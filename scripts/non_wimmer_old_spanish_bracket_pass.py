#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_bracket_report.jsonl"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
INLINE_LETTER_BRACKET_RE = re.compile(
    rf"(?<=[{LETTER}])\[([A-Za-z]{{1,8}})\s*\](?=[{LETTER}]|\W|$)"
)
EN_ESTA_RE = re.compile(r"\be\[n\]\[e\]sta\b|\ben\[e\]sta\b", re.I)
AMP_C_RE = re.compile(r"&c[.;]?", re.I)
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:!?])")
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


def clean(value: str) -> tuple[str, list[str]]:
    text = value or ""
    reasons: list[str] = []

    new = AMP_C_RE.sub("etc.", text)
    if new != text:
        reasons.append("amp_c")

    cleaned = EN_ESTA_RE.sub("en esta", new)
    if cleaned != new:
        new = cleaned
        reasons.append("en_esta")

    cleaned = INLINE_LETTER_BRACKET_RE.sub(lambda match: match.group(1).lower(), new)
    if cleaned != new:
        new = cleaned
        reasons.append("inline_letter_bracket")

    cleaned = SPACE_BEFORE_PUNCT_RE.sub(r"\1", new)
    if cleaned != new:
        new = cleaned
        reasons.append("space_before_punct")

    cleaned = MULTISPACE_RE.sub(" ", new).strip()
    if cleaned != new:
        new = cleaned
        reasons.append("multispace")

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
