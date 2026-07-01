#!/usr/bin/env python3
"""Sync minor Spanish orthography drift across Sahagun Escolios commentary mirrors."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import os
import re
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/sahagun_escolios_spanish_mirror_sync_proposals.tsv")
SUMMARY_PATH = Path("resources/sahagun_escolios_spanish_mirror_sync_summary.json")
SOURCE = "1565 Sahagún Escolios"
MARKER = "sahagun_escolios_spanish_mirror_sync_2026_06_29"
FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]

BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
WORD_REPLACEMENTS = {
    "auisos": "avisos",
    "baxa": "baja",
    "captivos": "cautivos",
    "cria": "cría",
    "estauan": "estaban",
    "hazes": "haces",
    "nueuas": "nuevas",
    "polido": "pulido",
    "aqui": "aquí",
}


def clean_text(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub("\n", text)
    text = TAG_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def html_skeleton(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"[A-Za-zÁÉÍÓÚÜÑÇáéíóúāēīōūüñç]+", "W", text)
    text = re.sub(r"\d+", "N", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_spanish_words(value: str) -> str:
    text = value
    for old, new in WORD_REPLACEMENTS.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)
        text = re.sub(rf"\b{re.escape(old.capitalize())}\b", new.capitalize(), text)
    return text


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def append_issue(value: object, marker: str) -> list[str]:
    if isinstance(value, list):
        issues = [str(item) for item in value]
    elif value:
        issues = [str(value)]
    else:
        issues = []
    if marker not in issues:
        issues.append(marker)
    return issues


def load_rows(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_rows(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as handle:
        for row in rows:
            json.dump(row, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
    os.replace(tmp, path)


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    proposals: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        values = {field: str(row.get(field, "")) for field in FIELDS}
        non_empty = [value for value in values.values() if value]
        if len(non_empty) < 2:
            continue
        normalized = {field: normalize_spanish_words(value) for field, value in values.items()}
        normalized_texts = {clean_text(value) for value in normalized.values() if value}
        if len(normalized_texts) != 1:
            continue
        if all(normalized[field] == values[field] for field in FIELDS):
            continue

        changed_fields = [field for field in FIELDS if normalized[field] != values[field]]
        counts["proposal_rows"] += 1
        counts["proposal_field_changes"] += len(changed_fields)
        proposals.append(
            {
                "record_id": row.get("record_id", ""),
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "changed_fields": ";".join(changed_fields),
                "before": " | ".join(f"{field}:{clean_text(values[field])[:180]}" for field in changed_fields),
                "after": " | ".join(f"{field}:{clean_text(normalized[field])[:180]}" for field in changed_fields),
            }
        )
        if args.apply:
            before = row.get("Comentario", "")
            for field in FIELDS:
                row[field] = normalized[field]
            metadata = row.get("Sahagun_Escolios_JSON") if isinstance(row.get("Sahagun_Escolios_JSON"), dict) else {}
            display = metadata.get("display") if isinstance(metadata.get("display"), dict) else {}
            if display.get("html"):
                display["html"] = normalize_spanish_words(str(display["html"]))
                display["issues"] = append_issue(display.get("issues"), MARKER)
            if display:
                metadata["display"] = display
            metadata["qa_spanish_mirror_sync_2026_06_29"] = {
                "action": "synced_minor_spanish_orthography_across_public_commentary_mirrors",
                "marker": MARKER,
                "changed_fields": changed_fields,
                "previous_commentary_sha1": hashlib.sha1(str(before).encode("utf-8")).hexdigest(),
            }
            row["Sahagun_Escolios_JSON"] = metadata
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)
            counts["applied_rows"] += 1

    write_tsv(
        args.proposals,
        proposals,
        ["record_id", "original", "editado", "changed_fields", "before", "after"],
    )
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.apply and proposals:
        write_rows(args.data, rows)

    print(f"summary {dict(counts)}")
    print(f"proposals {args.proposals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
