#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_cedilla_report.jsonl"


EXCLUDED_SOURCES = {
    "1645 Carochi",
    "1992 Karttunen",
}

LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
CEDILLA_WORD_RE = re.compile(rf"[{LETTER}]*ç[{LETTER}]*")
BRACKET_BEFORE_CEDILLA_RE = re.compile(
    rf"(?<=[{LETTER}])\[([A-Za-z]{{1,8}})\s*\](?=ç)"
)
EMPTY_BRACKET_BEFORE_CEDILLA_RE = re.compile(rf"(?<=[{LETTER}])\[\](?=ç)")
INLINE_LETTER_BRACKET_RE = re.compile(
    rf"(?<=[{LETTER}])\[([A-Za-z]{{1,8}})\s*\](?=[{LETTER}]|\W|$)"
)
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


SPANISH_HINTS = (
    "cabeç",
    "coraç",
    "fuerç",
    "esfuerç",
    "caç",
    "alcanç",
    "maçorc",
    "moç",
    "lienç",
    "verguenç",
    "vergüenç",
    "vergonç",
    "uergonç",
    "pedaç",
    "despedaç",
    "braç",
    "lanç",
    "çanj",
    "çatic",
    "çapat",
    "calabaç",
    "ponçoñ",
    "adereç",
    "endereç",
    "començ",
    "comienç",
    "confianç",
    "ordenanç",
    "pescueç",
    "beç",
    "çanahor",
    "templanç",
    "calç",
    "descalç",
    "çum",
    "çarç",
    "açacan",
    "maciç",
    "sacrifiç",
    "preçi",
    "çiel",
    "çerr",
    "açip",
    "paresç",
    "pareç",
    "ynçens",
    "ençens",
    "espeçi",
    "tranç",
    "çelebr",
    "palaç",
    "çiudad",
    "çapot",
    "ençiend",
    "fraçad",
    "çerc",
    "çeb",
    "çib",
    "çint",
    "cárç",
    "bergüenç",
    "esparç",
    "creç",
    "bendeç",
    "açech",
    "reçum",
    "punç",
    "coç",
    "enmudeç",
    "adelgaç",
    "atiç",
    "çern",
    "regoç",
    "feneç",
    "açes",
    "poluç",
    "hechiç",
    "desagradeç",
    "conoç",
    "çieg",
    "açot",
    "acreç",
    "çabull",
    "raçon",
    "vsanç",
    "usanç",
    "escaramuç",
    "endulç",
    "roç",
    "oç",
    "garç",
    "çahum",
    "manç",
    "reçong",
    "altoç",
    "peç",
    "plaç",
    "bebediç",
    "veç",
    "esforç",
    "alç",
    "alabanç",
    "bonanç",
    "crianç",
    "danç",
    "tardanç",
    "bienauenturanç",
    "bienaventuranç",
    "traç",
    "semejanç",
    "cedaç",
    "açuel",
    "trenç",
    "maç",
    "baç",
    "çop",
    "forç",
    "granç",
    "embaraç",
    "assechanç",
    "asechanz",
    "esperanç",
    "çufr",
    "çancad",
    "çuruj",
    "çaher",
    "sustanç",
    "çerez",
    "çierb",
    "resistenç",
    "rresistenç",
    "çacat",
    "çim",
    "meçed",
    "çep",
    "parçial",
    "penitenç",
    "carniç",
    "ençend",
    "çinc",
    "regaç",
    "nariç",
    "satisfaç",
    "amarilleç",
    "encaneç",
    "humedeç",
    "dulç",
    "tiçon",
    "descorteç",
    "aborreç",
    "amaneç",
    "enseñanç",
)

EXACT_REPLACEMENTS = {
    "çahumerio": "sahumerio",
    "çahumerios": "sahumerios",
    "çabullirse": "zambullirse",
    "çebil": "civil",
    "çibil": "civil",
    "prençipal": "principal",
    "prençipales": "principales",
    "ynçensario": "incensario",
    "ynçensarios": "incensarios",
    "açeso": "acceso",
    "açesos": "accesos",
    "haçe": "hace",
    "diçe": "dice",
    "veçes": "veces",
    "saçerdote": "sacerdote",
    "saçerdotes": "sacerdotes",
    "quiça": "quizá",
    "çufre": "azufre",
    "çurujano": "cirujano",
    "çurujanos": "cirujanos",
    "çaheria": "zahería",
    "çaherir": "zaherir",
    "çaherido": "zaherido",
    "çaheridos": "zaheridos",
    "çaherimiento": "zaherimiento",
    "çancadilla": "zancadilla",
    "çancadillas": "zancadillas",
    "yeruaçal": "yerbazal",
    "yeruaçales": "yerbazales",
    "desuerguença": "desverguenza",
    "desuergonçado": "desvergonzado",
    "desuergonçada": "desvergonzada",
    "desuergonçados": "desvergonzados",
    "desuergonçadas": "desvergonzadas",
    "enpereçar": "emperezar",
    "enpereçado": "emperezado",
    "enpereçada": "emperezada",
    "çerar": "cerrar",
}

POST_REPLACEMENTS = {
    "lánza": "lanza",
    "lanzá": "lanza",
    "coménzar": "comenzar",
    "coménzada": "comenzada",
    "coménzado": "comenzado",
}


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


def is_in_cited_form_span(text: str, start: int) -> bool:
    left = text[max(0, start - 55) : start].lower()
    return bool(
        re.search(
            r"(?:\bpt\.|\bpt:|\bpret:|\bprete:|\bpreterito:|\bpret[eé]rito:|\bpre:|\bp:|\bca\.|\brec\.|\bpri\.|"
            r"\bprimitivo\.|\b(?:m|s|c)\s+for\s+)[^/;]*$",
            left,
        )
    )


def is_probably_spanish(token: str) -> bool:
    lower = token.lower()
    if lower in EXACT_REPLACEMENTS:
        return True
    return any(hint in lower for hint in SPANISH_HINTS)


def modernize_cedilla(token: str) -> str:
    lower = token.lower()
    replacement = EXACT_REPLACEMENTS.get(lower)
    if replacement is None:
        replacement = re.sub(r"ç(?=[eéií])", "c", lower)
        replacement = replacement.replace("ç", "z")
        replacement = POST_REPLACEMENTS.get(replacement, replacement)
    return preserve_case(token, replacement)


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    reasons: list[str] = []

    if source in EXCLUDED_SOURCES:
        return text, reasons

    new = BRACKET_BEFORE_CEDILLA_RE.sub(lambda match: match.group(1).lower(), text)
    if new != text:
        reasons.append("bracket_before_cedilla")

    cleaned = EMPTY_BRACKET_BEFORE_CEDILLA_RE.sub("", new)
    if cleaned != new:
        new = cleaned
        reasons.append("empty_bracket_before_cedilla")

    replacements = 0

    def replace_match(match: re.Match[str]) -> str:
        nonlocal replacements
        token = match.group(0)
        if is_inside_square(new, match.start()):
            return token
        if is_in_cited_form_span(new, match.start()):
            return token
        if not is_probably_spanish(token):
            return token
        replacement = modernize_cedilla(token)
        if replacement != token:
            replacements += 1
        return replacement

    cleaned = CEDILLA_WORD_RE.sub(replace_match, new)
    if cleaned != new:
        new = cleaned
        reasons.append("cedilla_spanish_token")

    cleaned = INLINE_LETTER_BRACKET_RE.sub(lambda match: match.group(1).lower(), new)
    if cleaned != new:
        new = cleaned
        reasons.append("inline_letter_bracket")

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
