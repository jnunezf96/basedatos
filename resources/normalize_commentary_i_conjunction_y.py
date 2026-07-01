#!/usr/bin/env python3
"""Normalize old Spanish standalone i conjunctions to y in commentary."""

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
from typing import Any


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/commentary_i_conjunction_y_proposals.tsv")
SUMMARY_PATH = Path("resources/commentary_i_conjunction_y_summary.json")
MARKER = "visible_commentary_i_conjunction_y_2026_06_30"
QA_KEY = "qa_commentary_i_conjunction_y"

TARGET_SOURCE = "1580 Sahagún/Máynez"
DISPLAY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_BY_FIELD = {
    "Comentario": "Comentario_public_raw_i_conjunction_y",
    "Comentario (es)": "Comentario_es_raw_i_conjunction_y",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_i_conjunction_y",
}
TOKEN_RE = re.compile(r"(?<![A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌŪāēīōūÂÊÎÔÛâêîôûÇç])i(?![A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌŪāēīōūÂÊÎÔÛâêîôûÇç])")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")

NEXT_WORDS = {
    "también",
    "tambien",
    "ferocidad",
    "braveza",
    "en",
    "ihualli",
    "proveedor",
}

PROPOSAL_FIELDS = [
    "source",
    "record_id",
    "field",
    "original",
    "editado",
    "context",
]


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: object, index: int, width: int = 170) -> str:
    text = clean_html(value)
    left = max(0, index - width)
    right = min(len(text), index + width)
    return text[left:right].strip()


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def append_issue(value: object, marker: str) -> object:
    if isinstance(value, list):
        return value if marker in value else [*value, marker]
    return append_marker(value, marker)


def load_rows(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as handle:
        for row in rows:
            json.dump(row, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
    os.replace(tmp, path)


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=PROPOSAL_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in PROPOSAL_FIELDS})


def next_word(value: str, end: int) -> str:
    match = re.search(r"\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌŪāēīōūÂÊÎÔÛâêîôûÇç]+)", value[end:])
    return match.group(1).lower() if match else ""


def should_replace(value: str, match: re.Match[str]) -> bool:
    if next_word(value, match.end()) not in NEXT_WORDS:
        return False
    before = value[max(0, match.start() - 24):match.start()]
    if re.search(r"\(\s*$", before):
        return False
    return True


def apply_replacements(value: str) -> tuple[str, int, int]:
    replacements: list[tuple[int, int]] = []
    for match in TOKEN_RE.finditer(value):
        if should_replace(value, match):
            replacements.append((match.start(), match.end()))
    if not replacements:
        return value, 0, -1
    chunks: list[str] = []
    last = 0
    for start, end in replacements:
        chunks.append(value[last:start])
        chunks.append("y")
        last = end
    chunks.append(value[last:])
    return "".join(chunks), len(replacements), replacements[0][0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = load_rows(args.data)
    summary: Counter[str] = Counter()
    proposals: list[dict[str, object]] = []

    for row in rows:
        if row.get("Fuente") != TARGET_SOURCE:
            continue
        summary["target_source_rows"] += 1
        row_changes = 0
        raw_fields: set[str] = set()
        for field in DISPLAY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or " i " not in value:
                continue
            new_value, count, first_index = apply_replacements(value)
            if count == 0 or new_value == value:
                continue
            raw_field = RAW_FIELD_BY_FIELD[field]
            if args.apply and raw_field not in row:
                row[raw_field] = value
                summary["raw_preserved_fields"] += 1
            if args.apply:
                row[field] = new_value
            row_changes += count
            raw_fields.add(raw_field)
            proposals.append({
                "source": row.get("Fuente", ""),
                "record_id": row.get("record_id", ""),
                "field": field,
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "context": token_context(value, first_index),
            })

        if not row_changes:
            continue
        summary["proposal_rows"] += 1
        summary["proposal_changes"] += row_changes
        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_issue(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa[QA_KEY] = {
                "action": "normalized_old_spanish_i_conjunction_to_y_in_commentary",
                "marker": MARKER,
                "raw_fields_preserved": sorted(raw_fields),
                "changed_token_count": row_changes,
                "previous_commentary_sha1": hashlib.sha1(str(row.get("Comentario", "")).encode("utf-8")).hexdigest(),
            }
            row["Sentence_Source_JSON"] = qa
            summary["applied_rows"] += 1

    write_tsv(args.proposals, proposals)
    args.summary.write_text(
        json.dumps(dict(summary), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.apply and proposals:
        write_rows(args.data, rows)

    print(f"summary {dict(summary)}")
    print(f"proposals {args.proposals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
