#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "definition_punctuation_marks_report.jsonl"
FIELDS = ("Traducción", "Traducción (es)")

QUESTION_PERIOD_RE = re.compile(r"\?\.+")
BANG_PERIOD_RE = re.compile(r"!\.+")
COMMA_PERIOD_BEFORE_SPACE_RE = re.compile(r",\.+(?=\s)")
COMMA_PERIOD_END_RE = re.compile(r",\.+$")


def clean(value: str) -> tuple[str, list[str]]:
    text = value or ""
    reasons: list[str] = []

    new = QUESTION_PERIOD_RE.sub("?", text)
    if new != text:
        text = new
        reasons.append("question_period")

    new = BANG_PERIOD_RE.sub("!", text)
    if new != text:
        text = new
        reasons.append("bang_period")

    new = COMMA_PERIOD_BEFORE_SPACE_RE.sub(",", text)
    if new != text:
        text = new
        reasons.append("comma_period_before_space")

    new = COMMA_PERIOD_END_RE.sub("", text)
    if new != text:
        text = new
        reasons.append("comma_period_end")

    return text, reasons


def iter_rows() -> list[dict]:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def write_rows(rows: list[dict]) -> None:
    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes to data/data.jsonl.gz")
    args = parser.parse_args()

    rows = iter_rows()
    report = []

    for row in rows:
        for field in FIELDS:
            old = row.get(field)
            if not isinstance(old, str) or not old:
                continue
            new, reasons = clean(old)
            if new == old:
                continue
            report.append(
                {
                    "record_id": row.get("record_id"),
                    "source": row.get("Fuente"),
                    "lemma": row.get("Texto estandarizado"),
                    "field": field,
                    "reasons": reasons,
                    "old_translation": old,
                    "new_translation": new,
                }
            )
            if args.apply:
                row[field] = new

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    if args.apply:
        write_rows(rows)

    print(f"changed_fields={len(report)}")
    print(f"applied={args.apply}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
