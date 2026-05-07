#!/usr/bin/env python3
from __future__ import annotations

import gzip
import html
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_translation_normalize_report.jsonl"


CF_INDEX_SOURCE = "1580 CF Index"
KARTTUNEN_SOURCE = "1992 Karttunen"

AMP_C_RE = re.compile(r"&c;", re.I)
LEADING_PUNCT_RE = re.compile(r"^\s*[:;,]\s*")
SPACE_BEFORE_BASIC_PUNCT_RE = re.compile(r"\s+([.,;:!])")
SPACE_BEFORE_NON_PERIOD_PUNCT_RE = re.compile(r"\s+([,;:!])")
SPACE_BEFORE_QUESTION_PUNCT_RE = re.compile(r"\s+\?(?=$|[\s,.;:!)\]])")
DOUBLE_PUNCT_RE = re.compile(r"([,;:])\1+")
DOUBLE_PERIOD_RE = re.compile(r"(?<!\.)\.\.(?!\.)")
KARTTUNEN_TWO_DOT_ELLIPSIS_RE = re.compile(r"(?<=\w)\.\.(?=\s)")
BROKEN_PERIOD_RE = re.compile(r"\.\s+(\.)")
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


def normalize_translation(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    reasons: list[str] = []

    new = text

    if "\xa0" in new:
        new = new.replace("\xa0", " ")
        reasons.append("nbsp")

    amp_c_new = AMP_C_RE.sub("etc.", new)
    if amp_c_new != new:
        new = amp_c_new
        reasons.append("amp_c")

    unescaped = html.unescape(new)
    if unescaped != new:
        new = unescaped
        reasons.append("html_entity")

    stripped = new.strip()
    if stripped != new:
        new = stripped
        reasons.append("trim")

    if source != CF_INDEX_SOURCE:
        cleaned = LEADING_PUNCT_RE.sub("", new)
        if cleaned != new:
            new = cleaned
            reasons.append("leading_punct")

        space_before_punct_re = (
            SPACE_BEFORE_NON_PERIOD_PUNCT_RE
            if source == KARTTUNEN_SOURCE
            else SPACE_BEFORE_BASIC_PUNCT_RE
        )
        cleaned = space_before_punct_re.sub(r"\1", new)
        if cleaned != new:
            new = cleaned
            reasons.append("space_before_punct")

        cleaned = SPACE_BEFORE_QUESTION_PUNCT_RE.sub("?", new)
        if cleaned != new:
            new = cleaned
            reasons.append("space_before_punct")

        cleaned = DOUBLE_PUNCT_RE.sub(r"\1", new)
        if cleaned != new:
            new = cleaned
            reasons.append("double_punct")

        cleaned = BROKEN_PERIOD_RE.sub(r"\1", new)
        if cleaned != new:
            new = cleaned
            reasons.append("broken_period")

        if source != KARTTUNEN_SOURCE:
            cleaned = DOUBLE_PERIOD_RE.sub(".", new)
            if cleaned != new:
                new = cleaned
                reasons.append("double_period")
        else:
            cleaned = KARTTUNEN_TWO_DOT_ELLIPSIS_RE.sub(" ...", new)
            if cleaned != new:
                new = cleaned
                reasons.append("two_dot_ellipsis")

    cleaned = MULTISPACE_RE.sub(" ", new)
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
                new, reasons = normalize_translation(old, source)
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
