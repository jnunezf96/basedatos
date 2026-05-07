#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_preterit_literal_report.jsonl"


PRETERIT_TAIL_RE = re.compile(
    r"(?:(?<=\.)\s*|(?<=\s))\bpreterit\s*:\s*.*$",
    re.I,
)
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    if source != "1571 Molina 2":
        return text, []

    new = PRETERIT_TAIL_RE.sub("", text)
    reasons: list[str] = []
    if new != text:
        reasons.append("molina_preterit_tail")
        cleaned = MULTISPACE_RE.sub(" ", new).strip()
        cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
        cleaned = re.sub(r"[,;:]\s*$", "", cleaned).strip()
        if cleaned and cleaned[-1] not in ".!?)]":
            cleaned += "."
        if cleaned != new:
            new = cleaned
            reasons.append("terminal_cleanup")

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
                new, reasons = clean(old, source)
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
