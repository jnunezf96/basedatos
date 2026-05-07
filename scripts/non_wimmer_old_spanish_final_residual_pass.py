#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_final_residual_report.jsonl"


MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


EXACT_SUBSTRINGS = (
    ("B[aço]", "Bazo", "bracketed_spanish_cedilla"),
    ("ma[ciç]a", "maciza", "bracketed_spanish_cedilla"),
    ("bra[ç]alete", "brazalete", "bracketed_spanish_cedilla"),
    ("Bra[ç]elete", "Brazalete", "bracketed_spanish_cedilla"),
    ("ha[ç]er", "hacer", "bracketed_spanish_cedilla"),
    ("mo[ç]edad", "mocedad", "bracketed_spanish_cedilla"),
    ("caer En poluçion", "caer en polución", "bracketed_spanish_cedilla"),
)


EXACT_TOKEN_REPLACEMENTS = {
    "hize": ("hice", "hize"),
    "hà": ("ha", "spanish_grave_or_circumflex"),
    "cô": ("con", "spanish_grave_or_circumflex"),
    "llegò": ("llegó", "spanish_grave_or_circumflex"),
    "recibìr": ("recibir", "spanish_grave_or_circumflex"),
    "serà": ("será", "spanish_grave_or_circumflex"),
    "tambièn": ("también", "spanish_grave_or_circumflex"),
    "principìo": ("principio", "spanish_grave_or_circumflex"),
    "pìpa": ("pipa", "spanish_grave_or_circumflex"),
    "Inspìrar": ("Inspirar", "spanish_grave_or_circumflex"),
    "algûa": ("alguna", "spanish_grave_or_circumflex"),
    "Môtaña": ("Montaña", "spanish_grave_or_circumflex"),
    "unâ": ("una", "spanish_grave_or_circumflex"),
    "apenàs": ("apenas", "spanish_grave_or_circumflex"),
    "salteâdo": ("salteado", "spanish_grave_or_circumflex"),
    "màs": ("más", "spanish_grave_or_circumflex"),
}


TOKEN_RE = re.compile(
    r"\b("
    + "|".join(re.escape(token) for token in sorted(EXACT_TOKEN_REPLACEMENTS, key=len, reverse=True))
    + r")\b"
)


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    if source == "2021 Wimmer":
        return text, []

    reasons: list[str] = []
    new = text

    for old, replacement, reason in EXACT_SUBSTRINGS:
        if old in new:
            new = new.replace(old, replacement)
            reasons.append(reason)

    def replace_token(match: re.Match[str]) -> str:
        replacement, reason = EXACT_TOKEN_REPLACEMENTS[match.group(0)]
        reasons.append(reason)
        return replacement

    new = TOKEN_RE.sub(replace_token, new)

    cleaned = MULTISPACE_RE.sub(" ", new).strip()
    if cleaned != new:
        new = cleaned
        reasons.append("multispace")

    return new, sorted(set(reasons))


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
