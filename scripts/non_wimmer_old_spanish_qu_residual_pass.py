#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_qu_residual_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")
SKIP_SOURCES = {"1992 Karttunen"}


PHRASE_REPLACEMENTS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bcada\s+qualrecibira\b", re.I), "cada cual recibirá", "fused_old_qu_spelling"),
    (re.compile(r"\bdequalquier\b", re.I), "de cualquier", "fused_old_qu_spelling"),
    (re.compile(r"\bqualquieracosa\b", re.I), "cualquier cosa", "fused_old_qu_spelling"),
]


REPLACEMENTS: dict[str, tuple[str, str]] = {
    "quadrada": ("cuadrada", "old_qu_spelling"),
    "quadradas": ("cuadradas", "old_qu_spelling"),
    "quadrado": ("cuadrado", "old_qu_spelling"),
    "quadrados": ("cuadrados", "old_qu_spelling"),
    "quadrar": ("cuadrar", "old_qu_spelling"),
    "quadrarle": ("cuadrarle", "old_qu_spelling"),
    "quadril": ("cuadril", "old_qu_spelling"),
    "quadrilla": ("cuadrilla", "old_qu_spelling"),
    "quadra": ("cuadra", "old_qu_spelling"),
    "quaderno": ("cuaderno", "old_qu_spelling"),
    "quajada": ("cuajada", "old_qu_spelling"),
    "quajadas": ("cuajadas", "old_qu_spelling"),
    "quajado": ("cuajado", "old_qu_spelling"),
    "quajados": ("cuajados", "old_qu_spelling"),
    "quajar": ("cuajar", "old_qu_spelling"),
    "quaje": ("cuaje", "old_qu_spelling"),
    "quajo": ("cuajo", "old_qu_spelling"),
    "quales": ("cuales", "old_qu_spelling"),
    "qualesquiera": ("cualesquiera", "old_qu_spelling"),
    "qualesquier": ("cualesquier", "old_qu_spelling"),
    "qualidad": ("calidad", "old_qu_spelling"),
    "qualidades": ("calidades", "old_qu_spelling"),
    "qualquier": ("cualquier", "old_qu_spelling"),
    "qualquiera": ("cualquiera", "old_qu_spelling"),
    "qual": ("cual", "old_qu_spelling"),
    "quaci": ("casi", "old_qu_spelling"),
    "quasi": ("casi", "old_qu_spelling"),
    "quaderno": ("cuaderno", "old_qu_spelling"),
    "quando": ("cuando", "old_qu_spelling"),
    "quandoquiera": ("cuandoquiera", "old_qu_spelling"),
    "quantas": ("cuantas", "old_qu_spelling"),
    "quántas": ("cuántas", "old_qu_spelling"),
    "quanto": ("cuanto", "old_qu_spelling"),
    "quánto": ("cuánto", "old_qu_spelling"),
    "quantos": ("cuantos", "old_qu_spelling"),
    "quántos": ("cuántos", "old_qu_spelling"),
    "quarto": ("cuarto", "old_qu_spelling"),
    "quartos": ("cuartos", "old_qu_spelling"),
    "quarteron": ("cuarterón", "old_qu_spelling"),
    "quarto": ("cuarto", "old_qu_spelling"),
    "quatro": ("cuatro", "old_qu_spelling"),
    "quatrocientas": ("cuatrocientas", "old_qu_spelling"),
    "quatrocientos": ("cuatrocientos", "old_qu_spelling"),
    "quaresma": ("cuaresma", "old_qu_spelling"),
    "question": ("cuestión", "old_qu_spelling"),
    "quinze": ("quince", "old_qu_spelling"),
    "quínze": ("quince", "old_qu_spelling"),
    "quinzena": ("quincena", "old_qu_spelling"),
    "quinzeno": ("quinceno", "old_qu_spelling"),
}


TOKEN_RE = re.compile(
    rf"(?<![{LETTER}])("
    + "|".join(re.escape(token) for token in sorted(REPLACEMENTS, key=len, reverse=True))
    + rf")(?![{LETTER}])",
    re.I,
)


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    if source == "2021 Wimmer" or source in SKIP_SOURCES:
        return text, []

    reasons: list[str] = []
    new = text

    for pattern, replacement, reason in PHRASE_REPLACEMENTS:
        updated = pattern.sub(lambda match: preserve_case(match.group(0), replacement), new)
        if updated != new:
            new = updated
            reasons.append(reason)

    def replace_token(match: re.Match[str]) -> str:
        replacement, reason = REPLACEMENTS[match.group(0).lower()]
        reasons.append(reason)
        return preserve_case(match.group(0), replacement)

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

    if not DRY_RUN:
        tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        os.replace(tmp, DATA_PATH)

        with REPORT_PATH.open("w", encoding="utf-8") as fh:
            for item in report:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(report)}")
    print(f"report={REPORT_PATH if not DRY_RUN else '(dry-run)'}")


if __name__ == "__main__":
    main()
