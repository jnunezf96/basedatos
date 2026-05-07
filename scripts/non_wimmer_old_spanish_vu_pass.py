#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_vu_report.jsonl"


REPLACEMENTS = {
    "vn": "un",
    "vna": "una",
    "vno": "uno",
    "vnos": "unos",
    "vnas": "unas",
    "vsar": "usar",
    "vso": "uso",
    "vsanza": "usanza",
    "vsança": "usanza",
    "vtil": "útil",
    "vtilidad": "utilidad",
    "vltimo": "último",
    "vniuersal": "universal",
    "vniuersalmente": "universalmente",
    "auer": "haber",
    "auiendo": "habiendo",
    "auia": "había",
    "auian": "habían",
    "lleuar": "llevar",
    "lleua": "lleva",
    "lleuan": "llevan",
    "lleuando": "llevando",
    "lleuado": "llevado",
    "lleuada": "llevada",
    "leuantar": "levantar",
    "leuanta": "levanta",
    "leuantado": "levantado",
    "leuantada": "levantada",
    "boluer": "volver",
    "boluerse": "volverse",
    "boluia": "volvía",
    "boluio": "volvió",
    "boluieron": "volvieron",
    "prouecho": "provecho",
    "prouar": "probar",
    "prouado": "probado",
    "prouada": "probada",
    "graue": "grave",
    "graues": "graves",
    "nueuo": "nuevo",
    "nueua": "nueva",
    "nueuos": "nuevos",
    "nueuas": "nuevas",
    "trauajo": "trabajo",
    "trauajar": "trabajar",
    "trauajoso": "trabajoso",
    "trauajosa": "trabajosa",
}

TOKEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(token) for token in sorted(REPLACEMENTS, key=len, reverse=True)) + r")\b",
    re.I,
)
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def is_inside_square(text: str, index: int) -> bool:
    last_open = text.rfind("[", 0, index)
    last_close = text.rfind("]", 0, index)
    return last_open > last_close


def clean(value: str) -> tuple[str, list[str]]:
    text = value or ""
    changed_tokens: list[str] = []

    def replace_match(match: re.Match[str]) -> str:
        token = match.group(0)
        if is_inside_square(text, match.start()):
            return token
        replacement = REPLACEMENTS[token.lower()]
        if replacement != token:
            changed_tokens.append(token.lower())
        return preserve_case(token, replacement)

    new = TOKEN_RE.sub(replace_match, text)
    reasons: list[str] = []
    if new != text:
        reasons.append("vu_token")

    cleaned = MULTISPACE_RE.sub(" ", new).strip()
    if cleaned != new:
        new = cleaned
        reasons.append("multispace")

    if changed_tokens:
        reasons.extend(f"token:{token}" for token in sorted(set(changed_tokens)))

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
