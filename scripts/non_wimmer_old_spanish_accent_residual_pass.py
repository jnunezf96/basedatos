#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_accent_residual_report.jsonl"


REPLACEMENTS = {
    "Bolverã otro": "Bolver a otro",
    "Paso ãpaso": "Paso a paso",
    "Tàblado": "Tablado",
    "è inquieta": "e inquieta",
    "Mas allâ": "Mas allá",
    "cãpanario": "campanario",
}


def clean(value: str) -> tuple[str, list[str]]:
    text = value or ""
    new = text
    reasons: list[str] = []
    for old, replacement in REPLACEMENTS.items():
        if old in new:
            new = new.replace(old, replacement)
            reasons.append(f"replace:{old}")
    return new, reasons


def main() -> None:
    rows = []
    report = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            source = row.get("Fuente") or ""
            if source and source != "2021 Wimmer":
                old = row.get("Traducción") or ""
                new, reasons = clean(old)
                if new != old:
                    row["Traducción"] = new
                    report.append(
                        {
                            "record_id": row.get("record_id"),
                            "source": source,
                            "lemma": row.get("Texto estandarizado"),
                            "reasons": reasons,
                            "old_translation": old,
                            "new_translation": new,
                        }
                    )
            rows.append(row)

    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(report)}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
