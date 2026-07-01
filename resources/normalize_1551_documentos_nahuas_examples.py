#!/usr/bin/env python3
"""Normalize safe visible Nahuatl example spelling in 1551-95 Documentos.

This source is made of paired documentary Nahuatl examples plus Spanish
translations. The automatic pass is intentionally narrow. It rewrites exact
single-token old-spelling forms whose normalized value is already established
by this source's own Original/Editado rows, exact high-frequency ``y``-for-``i``
Nahuatl function/relational forms, plus ``qu-/Qu-`` before ``a/o`` to ``cu-/Cu-``
inside bold Nahuatl example blocks. Other initial ``h`` and ``v/u`` patterns
remain review-only because the source uses them in several different ways.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import os
import re
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/documentos_1551_example_normalization_proposals.tsv")
REVIEW_PATH = Path("resources/documentos_1551_example_normalization_review.tsv")
SUMMARY_PATH = Path("resources/documentos_1551_example_normalization_summary.json")
SOURCE = "1551-95 Documentos nahuas de la Ciudad de México"
RAW_FIELD = "Comentario_raw_1551_documentos_nahuas"
QU_MARKER = "visible_bold_nahuatl_1551_qu_before_ao_to_cu_2026_06_29"
LEXICON_MARKER = "visible_bold_nahuatl_1551_lexicon_aligned_2026_06_29"
INITIAL_Y_MARKER = "visible_bold_nahuatl_1551_initial_y_function_tokens_2026_06_29"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]

BOLD_RE = re.compile(r"(<b\b[^>]*>)(.*?)(</b>)", re.I | re.S)
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TOKEN_CHARS = "A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôÇç\\[\\]"
WORD_RE = re.compile(rf"[{TOKEN_CHARS}]+")
SINGLE_WORD_RE = re.compile(rf"^[{TOKEN_CHARS}]+$")
QU_BEFORE_AO_RE = re.compile(r"[Qq][Uu](?=[aAoOāĀōŌáÁóÓâÂôÔ])")
DIACRITIC_TRANS = str.maketrans(
    "ÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç",
    "AEIOUUNaeiouunAEIOaeioAEIOaeioCc",
)
SPANISH_TOKEN_DENY = {
    "cuando",
    "cuanto",
    "cuantos",
    "cuatro",
    "quatro",
    "quarenta",
    "quarto",
    "quintos",
    "quinientos",
    "quince",
}
NAHUATL_TOKEN_HINTS = (
    "tl",
    "tz",
    "hu",
    "auh",
    "hua",
    "tzin",
    "xoch",
    "atl",
    "tepec",
    "tlan",
    "cal",
    "cuauh",
    "quauh",
    "acht",
    "icpat",
    "matl",
)

SOURCE_TERM_REPLACEMENTS = {
    "chiquace": "chicuace",
    "chiquacen": "chicuacen",
    "chiquacenpohualli": "chicuacenpohualli",
    "chiquacepohualli": "chicuacepohualli",
    "chiquacexiuitl": "chicuacexiuitl",
    "chiquacentetl": "chicuacentetl",
    "hahuelitiz": "ahuelitiz",
    "Hahuexotl": "Ahuexotl",
    "hehtlatetectli": "ehtlatetectli",
    "hehuatzin": "ehuatzin",
    "heltzaccayo": "eltzaccayo",
    "hetetl": "etetl",
    "heysihuitl": "eysihuitl",
    "Hezhuahua[ca]tzin": "Ezhuahua[ca]tzin",
    "haca": "aca",
    "hacatencoh": "acatencoh",
    "haquenca": "aquenca",
    "hicac": "icac",
    "hocatca": "ocatca",
    "hocatqui": "ocatqui",
    "hoccequintin": "occequintin",
    "hoalcallacohoa": "oalcallacohoa",
    "Hocelotl": "Ocelotl",
    "homochiuh": "omochiuh",
    "homomiquili": "omomiquili",
    "homiztlastlaui": "omiztlastlaui",
    "honmani": "onmani",
    "honpa": "onpa",
    "honcaxtolli": "oncaxtolli",
    "honmatlactli": "onmatlactli",
    "honpohualli": "onpohualli",
    "honpohualmatl": "onpohualmatl",
    "hontequiztoc": "ontequiztoc",
    "hontlatetectli": "ontlatetectli",
    "hoquimotlallili": "oquimotlallili",
    "hotihuallaque": "otihuallaque",
    "hotlica": "otlica",
    "inquac": "in icuac",
    "iquac": "icuac",
    "Viznauatl": "Uiznauatl",
    "ynquac": "in icuac",
    "yquac": "icuac",
}

INITIAL_Y_TOKEN_REPLACEMENTS = {
    "yc": "ic",
    "ycac": "icac",
    "ycaca": "icaca",
    "ycalaquiampa": "icalaquiampa",
    "ycalaquianpa": "icalaquianpa",
    "ycalaquianpahuic": "icalaquianpahuic",
    "ycalaquiyanpa": "icalaquiyanpa",
    "ycalaquiyampahuic": "icalaquiyampahuic",
    "ycalaquiyapa": "icalaquiyapa",
    "ycallaquianpa": "icallaquianpa",
    "ycallaquiyanpa": "icallaquiyanpa",
    "ycallaquiyanpahuic": "icallaquiyanpahuic",
    "ycal": "ical",
    "ycalnauac": "icalnauac",
    "ycaltech": "icaltech",
    "ycaltepotzco": "icaltepotzco",
    "ycaltitlan": "icaltitlan",
    "ycalnaoac": "icalnahuac",
    "ycalnemac": "icalnemac",
    "yca": "ica",
    "ycallaquiapa": "icallaquiapa",
    "ycallaquiyampa": "icallaquiyampa",
    "ycalaquiyancopa": "icalaquiyancopa",
    "ychan": "ichan",
    "ychcatl": "ichcatl",
    "ychcatzomitl": "ichcatzomitl",
    "ychpuchtli": "ichpochtli",
    "ychpochtli": "ichpochtli",
    "yciuhca": "iciuhca",
    "ycuiliuhtica": "icuiliuhtica",
    "yceltzin": "iceltzin",
    "ycnooquichtli": "icnooquichtli",
    "ycnohoquichtli": "icnooquichtli",
    "ycnotl": "icnotl",
    "ycnocihuatl": "icnocihuatl",
    "ycnozihuatiticatca": "icnozihuatiticatca",
    "ycnoxochitl": "icnoxochitl",
    "ycpac": "icpac",
    "ycpatl": "icpatl",
    "yconetzin": "iconetzin",
    "ycenmactzinco": "icenmactzinco",
    "ymac": "imac",
    "ymacal": "imacal",
    "ymachiz": "imachiz",
    "ymachiyo": "imachiyo",
    "ymactzinco": "imactzinco",
    "yfirmatzin": "ifirmatzin",
    "ymatica": "imatica",
    "ymatiantzinco": "imatiantzinco",
    "ymahuiztililonime": "imahuiztililonime",
    "ymahuiztililoni": "imahuiztililoni",
    "ymahuizcatzin": "imahuizcatzin",
    "ymixpan": "imixpan",
    "ymixpantzinco": "imixpantzinco",
    "ymixhuihuan": "imixhuihuan",
    "ymaxca": "imaxca",
    "ymaxcatzin": "imaxcatzin",
    "yn": "in",
    "ynyacamecatl": "inyacamecatl",
    "ynacaztlan": "inacaztlan",
    "ynacaztla": "inacaztla",
    "yncaltetzonco": "incaltetzonco",
    "yncal": "incal",
    "yncalaquian": "incalaquian",
    "ynemac": "inemac",
    "ynic": "inic",
    "ynicolihuin": "inicolihuin",
    "ynin": "inin",
    "yniquetetl": "iniquetetl",
    "yniquetlamantli": "iniquetlamantli",
    "yniquincemaxcauh": "iniquincemaxcauh",
    "yniquicohuazque": "iniquicohuazque",
    "yniquitlalpan": "iniquitlalpan",
    "yniquiualhuicaz": "iniquiualhuicaz",
    "ynocal": "inocal",
    "ynomatzinco": "inomatzinco",
    "yntech": "intech",
    "ynhuehuetlal": "inhuehuetlal",
    "ynauhcampaixti": "inauhcampaixti",
    "yntatzin": "intatzin",
    "yntatzacualconemac": "intatzacualconemac",
    "yntlal": "intlal",
    "yntlalcoual": "intlalcoual",
    "yntlalman": "intlalman",
    "yntlalnemac": "intlalnemac",
    "yntlalpan": "intlalpan",
    "yntlatuayan": "intlatuayan",
    "yntlatohuaya": "intlatohuaya",
    "yntlatohuayan": "intlatohuayan",
    "yntlatol": "intlatol",
    "yntlatoltica": "intlatoltica",
    "yntlaxillacalpan": "intlaxillacalpan",
    "yntlatqui": "intlatqui",
    "yntocatzin": "intocatzin",
    "yntoca": "intoca",
    "yntocan": "intocan",
    "yntotlatocatzin": "intotlatocatzin",
    "yntotolhuan": "intotolhuan",
    "ynpilhuan": "inpilhuan",
    "ypaltzinco": "ipaltzinco",
    "ypalehuiloca": "ipalehuiloca",
    "ypampa": "ipampa",
    "ypan": "ipan",
    "ypanpa": "ipanpa",
    "ypatiuh": "ipatiuh",
    "ypilhuan": "ipilhuan",
    "ypiltzin": "ipiltzin",
    "yquitlaocolizque": "iquitlaocolizque",
    "yquetetl": "iquetetl",
    "yquiyollotzin": "iquiyollotzin",
    "yquizaian": "iquizaian",
    "yquizayan": "iquizayan",
    "yquizayanpa": "iquizayanpa",
    "yquizayanpan": "iquizayanpan",
    "yquizayanpahuic": "iquizayanpahuic",
    "ytech": "itech",
    "ytechcopa": "itechcopa",
    "ytechcopatzinco": "itechcopatzinco",
    "ytechpa": "itechpa",
    "ytechtlacauili": "itechtlacauili",
    "ytechtzinco": "itechtzinco",
    "yteicauh": "iteicauh",
    "yteycauh": "iteicauh",
    "ytepotzco": "itepotzco",
    "ytepotz": "itepotz",
    "ytepantlatzacuillo": "itepantlatzacuillo",
    "yteixuihuan": "iteixuihuan",
    "ytecopatzinco": "itecopatzinco",
    "ytencopa": "itencopa",
    "ytencopatzinco": "itencopatzinco",
    "ytetzinco": "itetzinco",
    "ytla": "itla",
    "ytlacahuiz": "itlacahuiz",
    "ytlacauiz": "itlacauiz",
    "ytlal": "itlal",
    "ytlalcoual": "itlalcoual",
    "ytlalcoualtzin": "itlalcoualtzin",
    "ytlallo": "itlallo",
    "ytlalpantzinco": "itlalpantzinco",
    "ytlalmaio": "itlalmaio",
    "ytlalpan": "itlalpan",
    "ytlamatia": "itlamatia",
    "ytlamaquixtiltzin": "itlamaquixtiltzin",
    "ytlanauatiltica": "itlanauatiltica",
    "ytlanauatiltzin": "itlanauatiltzin",
    "ytlatol": "itlatol",
    "ytlatqui": "itlatqui",
    "ytlatzin": "itlatzin",
    "ytatzin": "itatzin",
    "ytlatuayan": "itlatuayan",
    "ytlachiualtzin": "itlachiualtzin",
    "ytlacual": "itlacual",
    "ytlatoltica": "itlatoltica",
    "ytlazacamol": "itlazacamol",
    "ytlaxilacaltia": "itlaxilacaltia",
    "ytlaxilacaltian": "itlaxilacaltian",
    "ytlaxlacaltian": "itlaxlacaltian",
    "ytlan": "itlan",
    "ytoca": "itoca",
    "ytocatzin": "itocatzin",
    "ytocatzintica": "itocatzintica",
    "ytomintzin": "itomintzin",
    "ytzticac": "itzticac",
    "ytztica": "itztica",
    "ytztitemi": "itztitemi",
    "ytztoc": "itztoc",
    "ytztimani": "itztimani",
    "ytzcuin": "itzcuin",
    "ytzcol": "itzcol",
    "ythoallo": "ithoallo",
    "ythoalo": "ithoalo",
    "ythuallo": "ithuallo",
    "ythualli": "ithualli",
    "ythualco": "ithualco",
    "ytic": "itic",
    "ycacahuaoh": "icacahuaoh",
    "ycohuatlayauhqui": "icohuatlayauhqui",
    "yhui": "ihui",
    "yhuihin": "ihuihin",
    "yhuiyan": "ihuiyan",
    "yhua": "ihuan",
    "yhueli": "ihueli",
    "yhuelli": "ihueli",
    "yhuehuetque": "ihuehuet[que]",
    "yhuelitilitzin": "ihuelitilitzin",
    "yhuitilmachiuhqui": "ihuitilmachiuhqui",
    "ylacatziuhqui": "ilacatziuhqui",
    "ylamatzin": "ilamatzin",
    "ylcahuiz": "ilcahuiz",
    "ylcahualoc": "ilcahualoc",
    "ylhuiloc": "ilhuiloc",
    "ylhuiloque": "ilhuiloque",
    "ylhuicamina": "ilhuicamina",
    "yllamatzin": "illamatzin",
    "ypalnemohuani": "ipalnemohuani",
    "yxiptlatzin": "ixiptlatzin",
    "yxamitl": "ixamitl",
    "yxnahuatilo": "ixnahuatilo",
    "yxpan": "ixpan",
    "yxquich": "ixquich",
    "yxquichin": "ixquichin",
    "yxtlahuiz": "ixtlahuiz",
    "yxtlamati": "ixtlamati",
    "yxhuiuh": "ixhuiuh",
    "yxacal": "ixacal",
    "yxpantzinco": "ixpantzinco",
    "yspantzinco": "ixpantzinco",
    "yzcatqui": "izcatqui",
    "yzcatquin": "izcatquin",
    "yzqui": "izqui",
    "yzquixoch": "izquixoch",
    "yzquipohual": "izquipohual",
    "yzcahuitlaxcoyan": "izcahuitlaxcoyan",
    "yzcahuitlacuhcxitilloyan": "izcahuitlacuhcxitilloyan",
    "yzuauacatzin": "izhuahuacatzin",
    "yztacalecan": "iztacalecan",
    "yztacallecan": "iztacalecan",
    "yztactecuihtli": "iztactecuihtli",
    "yztlacatiz": "iztlacatiz",
    "yzticac": "izticac",
    "yztoc": "iztoc",
    "yzhuatepec": "izhuatepec",
    "yzuatepec": "izhuatepec",
    "yjusticiatzin": "ijusticiatzin",
    "ycalcoual": "icalcohual",
    "yyacal": "iyacal",
    "yyascatzin": "iyaxcatzin",
    "yyomatzinco": "iyomatzinco",
    "yhuan": "ihuan",
    "yuan": "ihuan",
}

REVIEW_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "qu_before_a_o",
        re.compile(r"\bqu[aoāōáóâô][A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô\[\]]*", re.I),
        "review qu before a/o not handled by the safe pass",
    ),
    (
        "initial_h_before_aeio",
        re.compile(
            r"(?<![A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô])h[aeioáéíóāēīōâêîô]"
            r"[A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô\[\]]*",
            re.I,
        ),
        "review initial h before a/e/i/o in documentary examples",
    ),
    (
        "v_likely_u",
        re.compile(
            r"\b[vV][aeiouāēīōáéíóúâêîô]\w*|"
            r"\w*[aeiouāēīōáéíóúâêîô][vV][aeiouāēīōáéíóúâêîô]\w*|"
            r"\bq[vV]\w*"
        ),
        "review v/u historical spelling",
    ),
    (
        "initial_y_before_consonant_unmapped",
        re.compile(
            r"(?<![A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô])y[bcdfghjklmnpqrstvwxyz]"
            r"[A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô\[\]]*",
            re.I,
        ),
        "review initial y before consonant not covered by the exact-token pass",
    ),
]


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: str, token: str, width: int = 140) -> str:
    text = clean_html(value)
    index = text.lower().find(token.lower())
    if index < 0:
        return text[: width * 2].strip()
    left = max(0, index - width)
    right = min(len(text), index + len(token) + width)
    return text[left:right].strip()


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def token_key(token: str) -> str:
    key = token.translate(DIACRITIC_TRANS).lower().replace("[", "").replace("]", "")
    return re.sub(r"[^a-z]", "", key)


def apply_case_pattern(old: str, new: str) -> str:
    if old.isupper():
        return new.upper()
    if old[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def build_source_lexicon(rows: list[dict]) -> dict[str, str]:
    values: dict[str, set[str]] = {}
    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        original = clean_html(row.get("Original", ""))
        editado = clean_html(row.get("Editado", ""))
        if not SINGLE_WORD_RE.fullmatch(original) or not SINGLE_WORD_RE.fullmatch(editado):
            continue
        if not re.search(r"^h[aeioáéíóāēīōâêîô]|[Vv]", original):
            continue
        original_key = token_key(original)
        editado_key = token_key(editado)
        if original_key and original_key != editado_key:
            values.setdefault(original_key, set()).add(editado)

    lexicon: dict[str, str] = {}
    for key, edits in values.items():
        if len(edits) == 1:
            lexicon[key] = next(iter(edits))
    return lexicon


def looks_nahuatl_token(token: str) -> bool:
    key = token_key(token)
    if len(key) < 3 or key in {item.translate(DIACRITIC_TRANS).lower() for item in SPANISH_TOKEN_DENY}:
        return False
    if key.startswith(("qua", "quo")):
        return True
    return any(hint in key for hint in NAHUATL_TOKEN_HINTS)


def qu_to_cu(token: str) -> str:
    def repl(match: re.Match[str]) -> str:
        old = match.group(0)
        if old == "QU":
            return "CU"
        if old == "Qu":
            return "Cu"
        return "cu"

    return QU_BEFORE_AO_RE.sub(repl, token)


def normalize_qu_before_ao_in_text(value: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            if "v" in old.lower() or not QU_BEFORE_AO_RE.search(old) or not looks_nahuatl_token(old):
                return old
            new = qu_to_cu(old)
            if old != new:
                changes.append((old, new))
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold_qu_before_ao(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_qu_before_ao_in_text(match.group(2))
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def normalize_lexicon_in_text(value: str, lexicon: dict[str, str]) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []
    if not lexicon:
        return value, changes

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            replacement = lexicon.get(token_key(old))
            if not replacement:
                return old
            new = apply_case_pattern(old, replacement)
            if new != old:
                changes.append((old, new))
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold_lexicon(value: object, lexicon: dict[str, str]) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_lexicon_in_text(match.group(2), lexicon)
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def normalize_initial_y_tokens_in_text(value: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            replacement = INITIAL_Y_TOKEN_REPLACEMENTS.get(token_key(old))
            if not replacement:
                return old
            new = apply_case_pattern(old, replacement)
            if new != old:
                changes.append((old, new))
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold_initial_y_tokens(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_initial_y_tokens_in_text(match.group(2))
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def bold_texts(value: object) -> list[str]:
    return [clean_html(match.group(2)) for match in BOLD_RE.finditer(str(value or ""))]


def review_candidates(row: dict) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for field in COMMENTARY_FIELDS:
        value = row.get(field, "")
        if not isinstance(value, str) or not value:
            continue
        for bold in bold_texts(value):
            for kind, pattern, note in REVIEW_PATTERNS:
                for match in pattern.finditer(bold):
                    token = match.group(0)
                    if kind == "initial_y_before_consonant_unmapped" and token_key(token) in INITIAL_Y_TOKEN_REPLACEMENTS:
                        continue
                    if not looks_nahuatl_token(token):
                        continue
                    key = (field, kind, token)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(
                        {
                            "record_id": row.get("record_id", ""),
                            "original": row.get("Original", ""),
                            "editado": row.get("Editado", ""),
                            "field": field,
                            "candidate_kind": kind,
                            "token": token,
                            "note": note,
                            "bold_text": bold[:600],
                            "context": token_context(value, token),
                        }
                    )
    return out


def load_rows(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_rows(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as handle:
        for row in rows:
            json.dump(row, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
    os.replace(tmp, path)


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--review", type=Path, default=REVIEW_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    lexicon = build_source_lexicon(rows)
    lexicon.update({token_key(old): new for old, new in SOURCE_TERM_REPLACEMENTS.items()})
    proposals: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    counts: Counter[str] = Counter()
    counts["lexicon_entries"] = len(lexicon)

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        counts["source_rows"] += 1
        if args.apply and RAW_FIELD not in row:
            row[RAW_FIELD] = row.get("Comentario", "")
            counts["raw_preserved_rows"] += 1

        row_changes: list[tuple[str, str, str, str]] = []
        for field in COMMENTARY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, lexicon_changes = normalize_bold_lexicon(value, lexicon)
            new_value, initial_y_changes = normalize_bold_initial_y_tokens(new_value)
            new_value, qu_changes = normalize_bold_qu_before_ao(new_value)
            for old, new in lexicon_changes:
                row_changes.append((field, LEXICON_MARKER, old, new))
            for old, new in initial_y_changes:
                row_changes.append((field, INITIAL_Y_MARKER, old, new))
            for old, new in qu_changes:
                row_changes.append((field, QU_MARKER, old, new))
            if not row_changes or new_value == value:
                continue
            if args.apply:
                row[field] = new_value

        if row_changes:
            marker_counts = Counter(marker for _, marker, _, _ in row_changes)
            markers = list(dict.fromkeys(marker for _, marker, _, _ in row_changes))
            counts["proposal_rows"] += 1
            counts["proposal_changes"] += len(row_changes)
            counts["proposal_changes_lexicon"] += marker_counts[LEXICON_MARKER]
            counts["proposal_changes_initial_y_tokens"] += marker_counts[INITIAL_Y_MARKER]
            counts["proposal_changes_qu_before_ao"] += marker_counts[QU_MARKER]
            proposals.append(
                {
                    "record_id": row.get("record_id", ""),
                    "original": row.get("Original", ""),
                    "editado": row.get("Editado", ""),
                    "markers": ";".join(markers),
                    "old_tokens": " | ".join(f"{field}:{old}" for field, _, old, _ in row_changes),
                    "new_tokens": " | ".join(f"{field}:{new}" for field, _, _, new in row_changes),
                    "context": token_context(row.get("Comentario", ""), row_changes[0][2]),
                }
            )
            if args.apply:
                for marker in markers:
                    row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), marker)
                    row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), marker)
                qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
                previous_commentary_sha1 = hashlib.sha1(str(row.get(RAW_FIELD, "")).encode("utf-8")).hexdigest()
                if marker_counts[LEXICON_MARKER]:
                    qa = {
                        **qa,
                        "qa_1551_documentos_lexicon_aligned_oldspell": {
                            "action": "normalized_bold_old_spelling_to_matching_source_editado_form",
                            "marker": LEXICON_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": marker_counts[LEXICON_MARKER],
                            "previous_commentary_sha1": previous_commentary_sha1,
                        },
                    }
                if marker_counts[QU_MARKER]:
                    qa = {
                        **qa,
                        "qa_1551_documentos_qu_before_ao_to_cu": {
                            "action": "normalized_qu_before_a_o_to_cu_inside_bold_nahuatl_examples",
                            "marker": QU_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": marker_counts[QU_MARKER],
                            "previous_commentary_sha1": previous_commentary_sha1,
                        },
                    }
                if marker_counts[INITIAL_Y_MARKER]:
                    qa = {
                        **qa,
                        "qa_1551_documentos_initial_y_function_tokens": {
                            "action": "normalized_exact_high_frequency_initial_y_function_tokens_inside_bold_examples",
                            "marker": INITIAL_Y_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": marker_counts[INITIAL_Y_MARKER],
                            "previous_commentary_sha1": previous_commentary_sha1,
                        },
                    }
                row["Sentence_Source_JSON"] = qa

        review.extend(review_candidates(row))

    write_tsv(
        args.proposals,
        proposals,
        ["record_id", "original", "editado", "markers", "old_tokens", "new_tokens", "context"],
    )
    write_tsv(
        args.review,
        review,
        ["record_id", "original", "editado", "field", "candidate_kind", "token", "note", "bold_text", "context"],
    )
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.apply and proposals:
        write_rows(args.data, rows)
        counts["applied_rows"] = len(proposals)
        args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"summary {dict(counts)}")
    print(f"proposals {args.proposals}")
    print(f"review {args.review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
