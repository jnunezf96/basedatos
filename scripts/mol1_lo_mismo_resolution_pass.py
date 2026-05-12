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
REPORT_PATH = ROOT / "scripts" / "mol1_lo_mismo_resolution_report.jsonl"

SOURCE = "1571 Molina 1"
PLACEHOLDER_RE = re.compile(r"^\s*lo\s+m[ie][§s]mo\s*(?:[.;]\s*|;\s*l\s*)?$", re.I)
SPLIT_HEAD_RE = re.compile(r"\s*[;,]\s*", re.I)
PAREN_NOTE_RE = re.compile(r"\s+\([^)]*\)\s*$")

NOTE = 'Original "lo mismo": Molina indica que la forma es la misma voz que la entrada española.'

DESCRIPTOR_TAILS = (
    r"\s+un d[ií]a de la semana$",
    r"\s+d[ií]a segundo de la semana$",
    r"\s+d[ií]a de la semana$",
    r"\s+mes (?:quinto|cuarto)$",
    r"\s+mes$",
    r"\s+fruta de este [aá]rbol$",
    r"\s+la fruta de este [aá]rbol$",
    r"\s+fruta conocida$",
    r"\s+la fruta$",
    r"\s+fruta del$",
    r"\s+fruta$",
    r"\s+hierba conocida$",
    r"\s+hierba$",
    r"\s+[aá]rbol conocido$",
    r"\s+[aá]rbol$",
    r"\s+animal conocida$",
    r"\s+animal conocido$",
    r"\s+animal$",
    r"\s+calzado$",
    r"\s+arma usada$",
    r"\s+sacramento$",
    r"\s+piedra preciosa$",
    r"\s+vino corrompido$",
    r"\s+candela$",
    r"\s+para trillar$",
    r"\s+para tornear$",
    r"\s+en las horas$",
    r"\s+de once onzas$",
)


def read_rows() -> list[dict]:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def write_rows(rows: list[dict]) -> None:
    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)


def is_placeholder(row: dict) -> bool:
    return row.get("Fuente") == SOURCE and bool(PLACEHOLDER_RE.fullmatch(row.get("Escritura original") or ""))


def derive_edition(translation: str) -> str:
    text = (translation or "").strip().strip(".")
    if not text:
        return ""

    head = SPLIT_HEAD_RE.split(text, maxsplit=1)[0].strip()
    head = PAREN_NOTE_RE.sub("", head).strip()
    head = head.replace("+", "")

    changed = True
    while changed:
        changed = False
        for tail in DESCRIPTOR_TAILS:
            updated = re.sub(tail, "", head, flags=re.I).strip()
            if updated and updated != head:
                head = updated
                changed = True

    return head


def with_note(comment: str) -> str:
    comment = (comment or "").strip()
    if NOTE in comment:
        return comment
    if not comment:
        return NOTE
    return f"{comment} {NOTE}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes to data/data.jsonl.gz")
    args = parser.parse_args()

    rows = read_rows()
    report = []

    for row in rows:
        if not is_placeholder(row):
            continue

        resolved = derive_edition(row.get("Traducción") or "")
        if not resolved:
            continue

        old_edition = row.get("Texto estandarizado") or ""
        old_comment = row.get("Comentario") or ""
        new_comment = with_note(old_comment)

        if old_edition == resolved and old_comment == new_comment:
            continue

        report.append(
            {
                "record_id": row.get("record_id"),
                "source": row.get("Fuente"),
                "original": row.get("Escritura original"),
                "translation": row.get("Traducción"),
                "old_edition": old_edition,
                "new_edition": resolved,
                "old_comment": old_comment,
                "new_comment": new_comment,
            }
        )

        if args.apply:
            row["Texto estandarizado"] = resolved
            row["Comentario"] = new_comment

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
