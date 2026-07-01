#!/usr/bin/env python3
"""Apply exact public-field Spanish spellcheck review rows.

The review TSV is generated from public display fields only. This applier keeps
the edit intentionally mechanical: each record/field gets exact token
replacements from the current review file, with raw source fields untouched.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
REVIEW_PATH = Path("resources/spanish_spellcheck_review.tsv")
SUMMARY_PATH = Path("resources/spanish_spellcheck_apply_summary.json")
MARKER = "public_spanish_spellcheck_residue_2026_06_29"


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def word_pattern(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])")


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


def load_review(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    replacements: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            record_id = row.get("record_id", "")
            field = row.get("field", "")
            token = row.get("token", "")
            suggestion = row.get("suggestion", "")
            if record_id and field and token and suggestion and not suggestion.startswith("review"):
                replacements[(record_id, field)][token] = suggestion
    return replacements


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--review", type=Path, default=REVIEW_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    replacements = load_review(args.review)
    rows = load_rows(args.data)
    counts: Counter[str] = Counter()
    proposals: list[dict[str, str]] = []

    for row in rows:
        record_id = row.get("record_id", "")
        row_changes: list[tuple[str, str, str, int]] = []
        for (rid, field), token_map in replacements.items():
            if rid != record_id:
                continue
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value = value
            for old, new in token_map.items():
                new_value, n = word_pattern(old).subn(new, new_value)
                if n:
                    row_changes.append((field, old, new, n))
                    counts["changed_tokens"] += n
                    counts[f"changed_token:{old}->{new}"] += n
            if args.apply and new_value != value:
                row[field] = new_value

        if row_changes:
            counts["changed_rows"] += 1
            proposals.append(
                {
                    "record_id": record_id,
                    "source": row.get("Fuente", ""),
                    "original": row.get("Original", ""),
                    "changes": " | ".join(
                        f"{field}:{old}->{new}x{n}" for field, old, new, n in row_changes
                    ),
                }
            )
            if args.apply:
                row["Comentario_normalizado_version"] = append_marker(
                    row.get("Comentario_normalizado_version"), MARKER
                )
                row["Comentario_display_issues"] = append_marker(
                    row.get("Comentario_display_issues"), MARKER
                )
                qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
                qa = {
                    **qa,
                    "qa_public_spanish_spellcheck_residue_2026_06_29": {
                        "action": "normalized_exact_spanish_residue_in_public_display_fields",
                        "marker": MARKER,
                        "raw_fields_preserved": True,
                        "changed_token_count": sum(n for _, _, _, n in row_changes),
                    },
                }
                row["Sentence_Source_JSON"] = qa

    counts["review_replacement_pairs"] = sum(len(v) for v in replacements.values())
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.apply and proposals:
        write_rows(args.data, rows)
        counts["applied"] = True
        args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"summary {dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
