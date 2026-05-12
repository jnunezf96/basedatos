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
REPORT_PATH = ROOT / "scripts" / "translation_quotes_terminal_period_report.jsonl"

QUOTE_SOURCE = "1580 Sahagún/Máynez"
TRANSLATION_FIELDS = ("Traducción", "Traducción (es)")
FIELDS = ("Traducción", "Traducción (es)", "Comentario", "Comentario (es)")
TERMINAL_PERIOD_SKIP_SOURCES = {"1992 Karttunen"}

PROTECTED_FINAL_ABBREVIATIONS = {
    "a.c.",
    "etc.",
    "p.e.",
    "ss.",
    "sr.",
    "sra.",
    "srta.",
    "ud.",
    "uds.",
    "v.",
    "vs.",
}

INTRAWARD_QUOTE_REPLACEMENTS = (
    ('"En el templo de las mujer"es', '"En el templo de las mujeres"'),
    ('mujer"es', "mujeres"),
    ('d"une', "d'une"),
    ("d&quot;une", "d'une"),
    ("le&quot;y&quot;", 'le "y"'),
    ("de&quot;camohpâltic&quot;", 'de "camohpâltic"'),
)


def remove_terminal_period(value: str) -> tuple[str, bool]:
    if not value:
        return value, False

    end = len(value)
    while end > 0 and value[end - 1].isspace():
        end -= 1
    if end == 0 or value[end - 1] != ".":
        return value, False

    stripped = value[:end]
    if stripped.endswith("..."):
        return value, False

    period_start = end
    while period_start > 0 and value[period_start - 1] == ".":
        period_start -= 1

    token_match = re.search(r"([^\s()\"'“”]+)$", stripped)
    final_token = token_match.group(1).lower() if token_match else ""
    if final_token in PROTECTED_FINAL_ABBREVIATIONS:
        return value, False

    return value[:period_start] + value[end:], True


def remove_outer_quotes(value: str) -> tuple[str, bool]:
    if not value:
        return value, False

    start = 0
    end = len(value)
    while start < end and value[start].isspace():
        start += 1
    while end > start and value[end - 1].isspace():
        end -= 1

    if end - start < 2:
        return value, False
    if value[start] != '"' or value[end - 1] != '"':
        return value, False

    return value[:start] + value[start + 1 : end - 1] + value[end:], True


def repair_intraword_quotes(value: str) -> tuple[str, bool]:
    if not value:
        return value, False

    text = value
    for old, new in INTRAWARD_QUOTE_REPLACEMENTS:
        text = text.replace(old, new)

    return text, text != value


def clean(row: dict, field: str, *, only_intraword_quotes: bool = False) -> tuple[str, list[str]]:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        return value or "", []

    reasons: list[str] = []
    text = value
    text, changed = repair_intraword_quotes(text)
    if changed:
        reasons.append("intraword_quote")

    if only_intraword_quotes:
        return text, reasons

    if field in TRANSLATION_FIELDS and row.get("Fuente") not in TERMINAL_PERIOD_SKIP_SOURCES:
        text, changed = remove_terminal_period(text)
        if changed:
            reasons.append("terminal_period")

    if row.get("Fuente") == QUOTE_SOURCE and field == "Traducción":
        text2, changed = remove_outer_quotes(text)
        if changed:
            text = text2
            reasons.append("outer_quotes")

    stripped = text.strip()
    if stripped != text:
        text = stripped
        reasons.append("edge_whitespace")

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
    parser.add_argument(
        "--only-intraword-quotes",
        action="store_true",
        help="repair quote marks embedded in words without running terminal punctuation cleanup",
    )
    args = parser.parse_args()

    rows = iter_rows()
    report = []

    for row in rows:
        for field in FIELDS:
            old = row.get(field)
            if not isinstance(old, str) or not old:
                continue
            new, reasons = clean(row, field, only_intraword_quotes=args.only_intraword_quotes)
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
