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
REPORT_PATH = ROOT / "scripts" / "v94_parenthetical_punctuation_report.jsonl"
SOURCE = "V94 Diccionario Global SNP"

FINAL_PE_PAREN_PERIOD_RE = re.compile(r"(\(p\.e\.[^)]*\))\.$")


def clean_translation(value: str) -> str:
    return FINAL_PE_PAREN_PERIOD_RE.sub(r"\1", value or "")


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
        if row.get("Fuente") != SOURCE:
            continue
        old = row.get("Traducción") or ""
        new = clean_translation(old)
        if new == old:
            continue
        report.append(
            {
                "record_id": row.get("record_id"),
                "lemma": row.get("Texto estandarizado"),
                "old_translation": old,
                "new_translation": new,
            }
        )
        if args.apply:
            row["Traducción"] = new

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    if args.apply:
        write_rows(rows)

    print(f"changed_rows={len(report)}")
    print(f"applied={args.apply}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
