#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_cedilla_residual_report.jsonl"


EXCLUDED_SOURCES = {
    "1645 Carochi",
    "1992 Karttunen",
}

LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
CEDILLA_WORD_RE = re.compile(rf"[{LETTER}]*ç[{LETTER}]*")
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


EXACT_REPLACEMENTS = {
    "açada": "azada",
    "açacán": "azacán",
    "açadon": "azadon",
    "açedarse": "acedarse",
    "açeçar": "acezar",
    "açofar": "azofar",
    "açor": "azor",
    "açorado": "azorado",
    "açorarse": "azorarse",
    "açucena": "azucena",
    "açucar": "azucar",
    "agaçapado": "agazapado",
    "agaçapandose": "agazapandose",
    "agaçaparse": "agazaparse",
    "aguaçeros": "aguaceros",
    "aguaçarse": "aguazarse",
    "almohaça": "almohaza",
    "almohaçar": "almohazar",
    "amorteçerse": "amortecerse",
    "ançuelo": "anzuelo",
    "adoraçióm": "adoracion",
    "asechança": "asechanza",
    "asechanças": "asechanzas",
    "atemoriçar": "atemorizar",
    "atanborçillo": "tamborcillo",
    "balánça": "balanza",
    "baptiçar": "baptizar",
    "berça": "berza",
    "berguença": "verguenza",
    "bienauenturánça": "bienaventuranza",
    "biolençia": "violencia",
    "borguença": "verguenza",
    "bruças": "bruces",
    "capiçayo": "capisayo",
    "carçel": "carcel",
    "carduçar": "carduzar",
    "çeiba": "ceiba",
    "çahones": "zahones",
    "çahurda": "zahurda",
    "çamarreado": "zamarreado",
    "çamarreador": "zamarreador",
    "çamarreamiento": "zamarreamiento",
    "çamarrear": "zamarrear",
    "çamarro": "zamarro",
    "çanca": "zanca",
    "çancadilla": "zancadilla",
    "çáncadilla": "zancadilla",
    "çancajoso": "zancajoso",
    "çancudo": "zancudo",
    "çancos": "zancos",
    "çanqueador": "zanqueador",
    "çanquear": "zanquear",
    "çarcillo": "zarcillo",
    "çarandar": "zarandar",
    "çaranda": "zaranda",
    "çaratan": "zaratan",
    "çauana": "sabana",
    "çauanas": "sabanas",
    "çenirse": "ceñirse",
    "çongotrear": "zangotear",
    "çorarse": "azorarse",
    "çurrador": "zurrador",
    "çurrar": "zurrar",
    "çurron": "zurron",
    "çurugia": "cirugia",
    "cobdiçiar": "codiciar",
    "cobrança": "cobranza",
    "começon": "comezon",
    "coménçada": "comenzada",
    "coménçar": "comenzar",
    "comiénça": "comienza",
    "comiénço": "comienzo",
    "cónfiánça": "confianza",
    "cuerço": "cuerzo",
    "deverguénça": "de verguenza",
    "desbergonçarse": "desvergonzarse",
    "desémbaraço": "desembarazo",
    "descónfiança": "desconfianza",
    "desliçiarse": "deslizarse",
    "desuegonçada": "desvergonzada",
    "diborçio": "divorcio",
    "difiçile": "dificil",
    "disfraçarse": "disfrazarse",
    "empónçoñado": "emponzoñado",
    "empónçoñar": "emponzoñar",
    "enaguaçada": "enaguazada",
    "enaguaçar": "enaguazar",
    "enaguaçarse": "enaguazarse",
    "enblanqueçer": "emblanquecer",
    "ençamarrado": "enzamarrado",
    "enciençador": "incensador",
    "encrueleçerse": "encruelecerse",
    "engrandeçerse": "engrandecerse",
    "enheriçarse": "erizarse",
    "enriqueçer": "enriquecer",
    "enrriqueçer": "enriquecer",
    "ensoberueçerse": "ensoberbecerse",
    "ensordeçer": "ensordecer",
    "ensuçiar": "ensuciar",
    "entonaçerse": "entumecerse",
    "eriaço": "eriazo",
    "eruaçal": "yerbazal",
    "escuerço": "escuerzo",
    "estropieço": "estropiezo",
    "façil": "facil",
    "fiança": "fianza",
    "floreçer": "florecer",
    "gaçapillo": "gazapillo",
    "gaçapo": "gazapo",
    "gallinaça": "gallinaza",
    "garuanços": "garbanzos",
    "graniçar": "granizar",
    "gránças": "granzas",
    "heruaçal": "herbazal",
    "holgança": "holganza",
    "labrança": "labranza",
    "lánça": "lanza",
    "liçencia": "licencia",
    "liçençia": "licencia",
    "licençia": "licencia",
    "liénço": "lienzo",
    "lodaçal": "lodazal",
    "lodaçales": "lodazales",
    "marçal": "marzal",
    "março": "marzo",
    "mastuerço": "mastuerzo",
    "matança": "matanza",
    "meçer": "mecer",
    "naçer": "nacer",
    "nasçe": "nace",
    "neçesidad": "necesidad",
    "odesuerguença": "o desverguenza",
    "ofreçer": "ofrecer",
    "onça": "onza",
    "onças": "onzas",
    "orça": "orza",
    "orçuelo": "orzuelo",
    "overguénça": "o verguenza",
    "pança": "panza",
    "pançudo": "panzudo",
    "pieça": "pieza",
    "pobreça": "pobreza",
    "pónçoñosa": "ponzoñosa",
    "prouança": "probanza",
    "pujança": "pujanza",
    "raça": "raza",
    "reberdeçer": "reverdecer",
    "reçagada": "rezagada",
    "rechaçar": "rechazar",
    "rechaço": "rechazo",
    "reluçir": "relucir",
    "remembrança": "remembranza",
    "resuçitar": "resucitar",
    "retoneçer": "retoñecer",
    "semejánça": "semejanza",
    "ssessuerço": "esfuerzo",
    "taça": "taza",
    "terçero": "tercero",
    "torçal": "torzal",
    "torçer": "torcer",
    "torçida": "torcida",
    "torçón": "torzon",
    "torçon": "torzon",
    "torçonado": "torzonado",
    "trayçion": "traicion",
    "tropieço": "tropiezo",
    "tuça": "tuza",
    "tuçan": "tuzan",
    "varçiar": "vaciar",
    "vengança": "venganza",
    "vergenças": "verguenzas",
    "verguénça": "verguenza",
    "vergónçoso": "vergonzoso",
    "vergónçosas": "vergonzosas",
    "xunçia": "juncia",
}


SPECIAL_REPLACEMENTS = (
    (re.compile(r"\[a\]çorarse", re.I), "azorarse"),
    (re.compile(r"li\[\]enço", re.I), "lienzo"),
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


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    reasons: list[str] = []

    if source == "2021 Wimmer" or source in EXCLUDED_SOURCES:
        return text, reasons

    new = text
    for pattern, replacement in SPECIAL_REPLACEMENTS:
        cleaned = pattern.sub(lambda match: preserve_case(match.group(0), replacement), new)
        if cleaned != new:
            new = cleaned
            reasons.append("special_bracket_cedilla")

    replacements = 0

    def replace_match(match: re.Match[str]) -> str:
        nonlocal replacements
        token = match.group(0)
        if is_inside_square(new, match.start()):
            return token
        if is_in_cited_or_reference_span(new, match.start()):
            return token
        replacement = EXACT_REPLACEMENTS.get(token.lower())
        if replacement is None:
            return token
        replacements += 1
        return preserve_case(token, replacement)

    cleaned = CEDILLA_WORD_RE.sub(replace_match, new)
    if cleaned != new:
        new = cleaned
        reasons.append("cedilla_residual_exact")

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
