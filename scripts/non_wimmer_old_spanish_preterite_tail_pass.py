#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_preterite_tail_report.jsonl"


MOLINA_PRETERITE_TAIL_RE = re.compile(
    r"(?:(?<=\.)\s*|(?<=\s))\b(?:pre|pret|prete|preterito|pret[eé]rito|p)\s*:\s*.*$",
    re.I,
)
MECAYAPAN_CONJ_BRACKET_RE = re.compile(
    r"\s*\[(?:pret|preterito|pret[eé]rito)\s*:?[^\]]*\]",
    re.I,
)
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


def clean_terminal_punct(text: str) -> str:
    text = MULTISPACE_RE.sub(" ", text).strip()
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"[,;:]\s*$", "", text).strip()
    return text


def clean(row: dict[str, object]) -> tuple[str, list[str]]:
    source = row.get("Fuente") or ""
    old = str(row.get("Traducción") or "")
    new = old
    reasons: list[str] = []

    if source == "1571 Molina 2":
        updated = MOLINA_PRETERITE_TAIL_RE.sub("", new)
        if updated != new:
            new = updated
            reasons.append("molina_preterite_tail")

    if source == "2002 Mecayapan":
        updated = MECAYAPAN_CONJ_BRACKET_RE.sub("", new)
        if updated != new:
            new = updated
            reasons.append("mecayapan_conjugation_bracket")

    if reasons:
        cleaned = clean_terminal_punct(new)
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
                new, reasons = clean(row)
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
