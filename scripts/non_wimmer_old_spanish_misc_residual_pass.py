#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_misc_residual_report.jsonl"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
CEDILLA_WORD_RE = re.compile(rf"[{LETTER}]*ç[{LETTER}]*")
ABBREV_MARK_RE = re.compile(r"([àèìòùâêîôû])\[([nm])\]", re.I)
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


CEDILLA_EXCLUDED_SOURCES = {
    "1645 Carochi",
    "1992 Karttunen",
}


ABBREV_MARKS = {
    "â": "a",
    "à": "a",
    "ê": "e",
    "è": "e",
    "î": "i",
    "ì": "i",
    "ô": "o",
    "ò": "o",
    "û": "u",
    "ù": "u",
}


EXACT_CEDILLA = {
    "açacar": "azacar",
    "açomar": "azomar",
    "açurdas": "a zurdas",
    "açutea": "azotea",
    "adegaçal": "adelgazar",
    "amenaça": "amenaza",
    "almorçar": "almorzar",
    "asechánça": "asechanza",
    "audiençia": "audiencia",
    "auergónçado": "avergonzado",
    "çafio": "zafio",
    "çaguan": "zaguan",
    "çaguero": "zaguero",
    "çania": "zanja",
    "çarco": "charco",
    "çarcos": "charcos",
    "çentellas": "centellas",
    "çiem": "cien",
    "çuecos": "zuecos",
    "cierço": "cierzo",
    "combleça": "combleza",
    "conçertarse": "concertarse",
    "contradeçir": "contradecir",
    "destemplánça": "destemplanza",
    "enmoeçerse": "enmohecerse",
    "entristeçerse": "entristecerse",
    "naçión": "nación",
    "nasçido": "nacido",
    "obedeçer": "obedecer",
    "ordenánça": "ordenanza",
    "ordenánças": "ordenanzas",
    "prençipio": "principio",
    "pronunçiar": "pronunciar",
    "reçagado": "rezagado",
    "taçon": "tazon",
    "uzança": "usanza",
}


SPECIAL_REPLACEMENTS = (
    (re.compile(r"azotea o açutea", re.I), "azotea"),
    (re.compile(r"garuan\[ç\]os", re.I), "garbanzos"),
    (re.compile(r"\[ç\]aguan", re.I), "zaguan"),
    (re.compile(r"\[punçar\]", re.I), "[punzar]"),
    (re.compile(r"\[regoçijar a otro\]", re.I), "[regocijar a otro]"),
    (re.compile(r"\[padeçer\]", re.I), "[padecer]"),
    (re.compile(r"\[poluçion\]", re.I), "[polucion]"),
    (re.compile(r"\[amançebarse\]", re.I), "[amancebarse]"),
)


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


def is_in_cited_or_reference_span(text: str, start: int) -> bool:
    left = text[max(0, start - 80) : start].lower()
    return bool(
        re.search(
            r"(?:\bpt\.|\bpt:|\bpret:|\bprete:|\bpreterito:|\bpret[eé]rito:|\bpre:|\bp:|"
            r"\bca\.|\brec\.|\bpri\.|\bprimitivo\.|\blo mesmo es que\b|\blo mismo es que\b|"
            r"\bvéase\b|\bvease\b|\bvide\b|\b(?:m|s|c)\s+for\s+)[^/;]*$",
            left,
        )
    )


def replace_abbrev_mark(match: re.Match[str]) -> str:
    base = ABBREV_MARKS[match.group(1).lower()]
    nasal = match.group(2).lower()
    if match.group(1).isupper():
        base = base.upper()
    return base + nasal


def replace_special(match: re.Match[str], replacement: str) -> str:
    original = match.group(0)
    if original.startswith("[") and replacement.startswith("[") and len(original) > 1:
        if original[1].isupper():
            return "[" + replacement[1:2].upper() + replacement[2:]
    return preserve_case(original, replacement)


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    reasons: list[str] = []

    if source == "2021 Wimmer":
        return text, reasons

    new = ABBREV_MARK_RE.sub(replace_abbrev_mark, text)
    if new != text:
        reasons.append("nasal_abbrev_mark")

    for pattern, replacement in SPECIAL_REPLACEMENTS:
        cleaned = pattern.sub(lambda match: replace_special(match, replacement), new)
        if cleaned != new:
            new = cleaned
            reasons.append("special_cedilla_form")

    if source not in CEDILLA_EXCLUDED_SOURCES:
        replacements = 0

        def replace_cedilla(match: re.Match[str]) -> str:
            nonlocal replacements
            token = match.group(0)
            if is_inside_square(new, match.start()):
                return token
            if is_in_cited_or_reference_span(new, match.start()):
                return token
            replacement = EXACT_CEDILLA.get(token.lower())
            if replacement is None:
                return token
            replacements += 1
            return preserve_case(token, replacement)

        cleaned = CEDILLA_WORD_RE.sub(replace_cedilla, new)
        if cleaned != new:
            new = cleaned
            reasons.append("cedilla_misc_exact")

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
