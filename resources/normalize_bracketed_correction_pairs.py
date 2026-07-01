#!/usr/bin/env python3
"""Normalize bracketed corrections that immediately follow the corrected form.

This pass intentionally handles only patterns like ``misspelling [correction]``.
It does not touch bracketed insertions, semantic glosses, supplied words, or
cases where the bracket does not correct the immediately preceding form.
"""

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
PROPOSALS_PATH = Path("resources/bracketed_correction_pair_proposals.tsv")
SUMMARY_PATH = Path("resources/bracketed_correction_pair_summary.json")
MARKER = "visible_bracketed_correction_pair_normalized_2026_06_30"
QA_KEY = "qa_bracketed_correction_pair_normalized"

PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_BY_PUBLIC_FIELD = {
    "Traducción": "Traducción_raw_bracketed_correction_pair",
    "Traducción (es)": "Traducción_es_raw_bracketed_correction_pair",
    "Comentario": "Comentario_raw_bracketed_correction_pair",
    "Comentario (es)": "Comentario_es_raw_bracketed_correction_pair",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_bracketed_correction_pair",
}

SOURCE_REPLACEMENTS: dict[str, dict[str, str]] = {
    "1629 Alarcón": {
        "tonatiulitzin [tonatiuhtzin]": "tonatiuhtzin",
        "onicnianato [oniquianato]": "oniquianato",
        "cihuatequiahuā [cihuatequihua]": "cihuatequihua",
        "tlatecapanilli [tlatecapauilli]": "tlatecapauilli",
        "BELCEBUT [BELZEBUTH]": "BELZEBUTH",
    },
    "1759 Paredes": {
        "manelhuayotia [monelhuayotia]": "monelhuayotia",
        "Ilhuani, [Ihuani]": "Ihuani",
        "icololiz [cocoliz]": "cocoliz",
        "Tlaxcaxinachtin [tlacaxinachtin]": "tlacaxinachtin",
    },
}

BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: object, token: str, width: int = 150) -> str:
    text = clean_html(value)
    index = text.find(token)
    if index < 0:
        return text[: width * 2].strip()
    left = max(0, index - width)
    right = min(len(text), index + len(token) + width)
    return text[left:right].strip()


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def normalize_value(value: object, replacements: dict[str, str]) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str]] = []
    for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        count = text.count(old)
        if not count:
            continue
        text = text.replace(old, new)
        changes.extend((old, new) for _ in range(count))
    return text, changes


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
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
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
        source = row.get("Fuente", "")
        replacements = SOURCE_REPLACEMENTS.get(source)
        if not replacements:
            continue
        counts[f"source_rows:{source}"] += 1
        row_changes: list[tuple[str, str, str]] = []
        raw_fields: list[str] = []
        first_context_field = ""
        first_old = ""

        for field in PUBLIC_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_value(value, replacements)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if not first_context_field:
                first_context_field = field
                first_old = changes[0][0]
            if args.apply:
                raw_field = RAW_FIELD_BY_PUBLIC_FIELD[field]
                if raw_field not in row:
                    row[raw_field] = value
                    raw_fields.append(raw_field)
                    counts["raw_preserved_fields"] += 1
                row[field] = new_value

        if not row_changes:
            continue

        counts["proposal_rows"] += 1
        counts["proposal_changes"] += len(row_changes)
        proposals.append(
            {
                "source": source,
                "record_id": row.get("record_id", ""),
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "marker": MARKER,
                "old_tokens": " | ".join(f"{field}:{old}" for field, old, _ in row_changes),
                "new_tokens": " | ".join(f"{field}:{new}" for field, _, new in row_changes),
                "context": token_context(row.get(first_context_field, ""), first_old),
            }
        )

        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                QA_KEY: {
                    "action": "normalized_immediate_bracketed_spelling_correction_pairs",
                    "marker": MARKER,
                    "raw_fields": raw_fields,
                    "raw_preserved": True,
                    "changed_token_count": len(row_changes),
                    "previous_public_field_sha1": hashlib.sha1(
                        "||".join(str(row.get(raw_field, "")) for raw_field in raw_fields).encode("utf-8")
                    ).hexdigest(),
                },
            }
            row["Sentence_Source_JSON"] = qa

    write_tsv(
        args.proposals,
        proposals,
        ["source", "record_id", "original", "editado", "marker", "old_tokens", "new_tokens", "context"],
    )
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.apply and proposals:
        write_rows(args.data, rows)
        counts["applied_rows"] = len(proposals)
        args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"summary {dict(counts)}")
    print(f"proposals {args.proposals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
