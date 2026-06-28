#!/usr/bin/env python3
"""Normalize 1992 Karttunen Traduccion values.

The source strings generally follow:

    HEADWORD [grammar] English definition / Spanish definition (source)

Some rows also include copied "See ..." component entries and attestation
notes. This script keeps grammar/type and English/Spanish definitions, removes
headword labels, source sigla, and notes, and applies a small set of explicit
nodal fixes for records that do not fit the general pattern safely.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import re
import shutil
from collections import Counter
from pathlib import Path


SOURCE_NAME = "1992 Karttunen"
ORIGINAL_COMMENT_MARKER = "<b>1992 Karttunen original:</b>"
SOURCE_CODES = "A B C H I K M O R S T X Y Z V".split()
SOURCE_ALT = "(?:" + "|".join(SOURCE_CODES) + ")"
SOURCE_RE = rf"{SOURCE_ALT}(?:\s*[,/]\s*{SOURCE_ALT})*"

UPPER = "A-ZÁÉÍÓÚĀĒĪŌŪÜÑÇ"
LOWER = "a-záéíóúāēīōūüñç"
LETTER = UPPER + LOWER
HEAD_CHARS = UPPER + r"0-9\-\(\)\*'’\."
HEAD_TOKEN = rf"[*\-]?(?:\([A-Z]\))?[{UPPER}][{HEAD_CHARS}]*"
DEF_LOOKAHEAD = (
    r"(?:vrefl|vt\b|vi\b|vimpers|pret:|pl:|PL:|possessed|"
    r"necessarily possessed|inalienably possessed|compound|postposition|"
    r"locative|possessor|derivational|transitive|particle|place name|"
    r"personal name|expression|exclamation|interjection|salutation|"
    r"leavetaking|someone\b|something\b|a\b|an\b|the\b|to\b|for\b|"
    r"in\b|all\b|one\b|no\b|bean\b|reed\b|flower\b|base\b|dried\b|"
    r"illness\b|lame\b|however\b|group\b|son-in-law\b|at\b|near\b|"
    r"honorific\b|diminutive\b|swelling\b|garment\b|element\b)"
)

HEAD_RE = re.compile(rf"^({HEAD_TOKEN})(?:\s+|$)")
EMBED_HEAD_RE = re.compile(
    rf"(?P<prefix>[.]\s*|[.]['’]\s*)({HEAD_TOKEN})\s+(?={DEF_LOOKAHEAD})"
)
SOURCE_PAREN_RE = re.compile(
    rf"(?<![{LETTER}])\(\s*{SOURCE_RE}(?:\s+(?:for|por) [^)]*)?\s*\)(?![{LETTER}])"
)
ATTACHED_SOURCE_PAREN_RE = re.compile(
    rf"\(\s*{SOURCE_RE}(?:\s+(?:for|por) [^)]*)?\s*\)(?![{LETTER}])"
)
SOURCE_NOTE_RE = re.compile(
    rf"(?<![{LETTER}])\(\s*{SOURCE_RE}\b[^\])]*(?:\)|\])(?![{LETTER}])"
)
MALFORMED_SOURCE_TAIL_RE = re.compile(rf"\s*\(\s*{SOURCE_ALT}\d*\s*$")
SOURCE_BAR_RE = re.compile(rf"\s*[|/]\s*{SOURCE_RE}(?:\s+(?:for|por) [^)]*)?\)")
SOURCE_BEFORE_HEAD_RE = re.compile(
    rf"\s*(?:\(\s*{SOURCE_RE}(?:\s+(?:for|por) [^)]*)?\s*\)|"
    rf"[|/]\s*{SOURCE_RE}(?:\s+(?:for|por) [^)]*)?\))"
    rf"(?=\s*{HEAD_TOKEN}\s+{DEF_LOOKAHEAD})"
)
TRAIL_SEE_RE = re.compile(r"(?:^|\s+)See\s+[^.]+\.?\s*", re.I)
NOTE_AFTER_PERIOD_RE = re.compile(
    r"(?<=[.!?])\s+(?=(?:This|The|[A-Z]\s+(?:has|gives|attests|"
    r"combines|provides|consistently)|In\b|It\b|There\b|Both\b|Only\b|"
    r"By\b|Cf\.|Compare\b|Although\b|Since\b|When\b|Where\b|Of\b|As\b|"
    r"Personal\b|Aside\b|If\b|A\s+glottal\b|M\s+also\b|"
    r"Z\s+consistently\b)).*$"
)
NOTE_NO_PERIOD_RE = re.compile(
    r"\s+(?=(?:Although\b|This\s+(?:is\s+(?:also|implied|synonymous|"
    r"abundantly|commonly|found)|contrasts|suffix|reduplicated|nonactive|"
    r"compound)|It\s+(?:is|contrasts|appears|seems|may|can|has)|There\b|"
    r"In\s+general\b|The\s+(?:same|variant|common|expected|long|vowel)|"
    r"[A-Z]\s+(?:has|gives|attests|combines|provides|consistently)|"
    r"Personal\s+names\b|Aside\s+from\b|If\b)).*$"
)
DERIV_TAG = r"(?:nonact|applic|caus|redup|altern\. caus|altern\. applic|Redup)"
DERIV_REF_ONLY_RE = re.compile(rf"^(?P<tag>{DERIV_TAG})\.\s+{HEAD_TOKEN}\.?$")
BARE_DERIV_REF_ONLY_RE = re.compile(rf"^(?P<tag>nonact|applic|caus|redup)\s+{HEAD_TOKEN}\.?$")
LEADING_DERIV_REF_RE = re.compile(
    rf"^(?P<tag>{DERIV_TAG})\.\s+{HEAD_TOKEN}\s+"
    rf"(?={HEAD_TOKEN}\s+{DEF_LOOKAHEAD}|{DEF_LOOKAHEAD})"
)
POST_TAG_HEAD_RE = re.compile(
    rf"^((?:nonact|applic|caus|redup|altern\. caus|altern\. applic)\.)"
    rf"\s*;\s+{HEAD_TOKEN}\s+(?={DEF_LOOKAHEAD})"
)
TRAIL_DERIV_RE = re.compile(
    rf"(?:(?<=\.)\s*|^){DERIV_TAG}\.\s+{HEAD_TOKEN}\.?"
)
TAIL_DERIV_ANY_RE = re.compile(
    rf".*\b(?P<tag>nonact|applic|caus|redup|altern\. caus|"
    rf"altern\. applic|Redup)\.\s+{HEAD_TOKEN}\.?$",
    re.I,
)


# Nodal fixes are rows whose useful signal is not reachable by the general
# direct-gloss pattern without retaining attestation prose.
SPECIAL_NORMALIZATIONS = {
    "1992-karttunen:000095": "perhaps / por ventura, o quizá; that one / aquél",
    "1992-karttunen:000306": "person from Atlixco / natural de Atlixco",
    "1992-karttunen:000695": (
        "possessed reduplicated form; distributive, each to his own home"
    ),
    "1992-karttunen:000837": "applicative form",
    "1992-karttunen:000892": (
        "altern. caus.; applic.; nonact.; to weep, cry, howl, to utter "
        "one’s characteristic sound / llorar, balar la oveja, bramar el "
        "leon o el toro, cantar el buho o las otras aves"
    ),
    "1992-karttunen:002785": "particle which combines with negative particles",
    "1992-karttunen:002704": "compounding form; corpse, dead person; to die",
    "1992-karttunen:003275": "group of musicians / grupo de músicos",
    "1992-karttunen:003325": (
        "indicates movement toward or from a point and, with numerals, "
        "how many times"
    ),
    "1992-karttunen:003339": (
        "to be happy, to experience pleasure / alegrarse y tener placer"
    ),
    "1992-karttunen:003617": "element",
    "1992-karttunen:004376": (
        "to go to do something. A centrifugal purposive verbal compounding "
        "element"
    ),
    "1992-karttunen:004537": "nonactive form",
    "1992-karttunen:005694": "for children to be born; to chip or splinter off",
    "1992-karttunen:005093": "possessed form; one’s color, tint, hue",
    "1992-karttunen:005703": "honorific postposition",
    "1992-karttunen:005988": "element with the sense ‘green’ in many compounds",
    "1992-karttunen:006079": "variant: already",
    "1992-karttunen:006310": (
        "applic.; break ground, clear land, weed / abrir o labrar de nuevo "
        "la tierra, rozar la yerba"
    ),
}


def strip_leading_exact_original(value: str, original: str) -> str:
    if original and value.startswith(original + " "):
        rest = value[len(original) :].lstrip()
        if HEAD_RE.match(rest):
            return rest
    return value


def strip_leading_head(value: str) -> tuple[str, str | None]:
    match = HEAD_RE.match(value)
    if not match:
        return value, None
    head = match.group(1)
    if len(head) == 1 and head != "Ā":
        return value, None
    return value[match.end() :].strip(), head


def remove_source_markers(value: str) -> str:
    value = SOURCE_BAR_RE.sub("", value)
    value = SOURCE_NOTE_RE.sub("", value)
    value = SOURCE_PAREN_RE.sub("", value)
    value = ATTACHED_SOURCE_PAREN_RE.sub("", value)
    value = MALFORMED_SOURCE_TAIL_RE.sub("", value)
    return re.sub(r"\s*\(\s*;\s*for [^)]*\)", "", value)


def normalize_this_definition(value: str) -> str:
    transforms = [
        (
            r"^This is an? element meaning [‘']([^’']+)[’']\.?.*$",
            r"element meaning \1",
        ),
        (
            r"^This element is a constituent of many constructions having to do "
            r"with liquid;.*$",
            "element having to do with liquid",
        ),
        (
            r"^This is the second element of .*? and apparently means [‘']"
            r"([^’']+)[’']\.?.*$",
            r"element meaning \1",
        ),
        (
            r"^This element enters into many derivations with divergent meanings\. "
            r"The basic sense appears to be [‘']([^’']+)[’'].*$",
            r"element meaning \1",
        ),
        (
            r"^This is only attested in the constructions .*? both meaning [‘']"
            r"([^’']+)[’']\.?.*$",
            r"only attested in constructions meaning \1",
        ),
        (
            r"^This is an element in numerous compounds and derivations and "
            r"refers to (.*?)(?:\.\s+|$).*$",
            r"element referring to \1",
        ),
        (r"^This indicates (.*?)(?:\.\s+.*)?$", r"indicates \1"),
        (
            r"^This compounding element combines with kinship terms to convey "
            r"the sense of (.*?)(?:;|\.\s+|$).*$",
            r"compounding element conveying \1",
        ),
        (
            r"^This has two sources\. It is (.*?)(?:, and|\.\s+|$).*$",
            r"compounding form: \1",
        ),
        (
            r"^This is the initial element of (.*?)(?:\.\s+|$).*$",
            r"initial element of \1",
        ),
        (r"^This is a variant of (.*?)(?:\.\s+|$).*$", r"variant of \1"),
        (
            r"^This compound verb construction .*? meaning [‘']([^’']+)[’'].*$",
            r"compound verb construction meaning \1",
        ),
        (
            r"^This possessor derivation .*? whole phrase meaning [‘']([^’']+)"
            r"[’']\.?$",
            r"possessor derivation meaning \1",
        ),
    ]
    for pattern, replacement in transforms:
        if re.match(pattern, value):
            return re.sub(pattern, replacement, value)
    return value


INFLECTION_LABEL_RE = re.compile(
    r"\b(?:pret\.?\s*pl\.?|pret\.?|pr[eê]t|prep|prel|piet|pres|"
    r"sing\.?\s*pres|singular present|present singular|pl\.?|PL)"
    rf"(?![{LETTER}])\s*(?::|;|\.)?\s*",
    re.I,
)
FORM_TOKEN_RE = re.compile(
    r"(?:[~∼\-–]\s*){0,2}[A-ZĀĒĪŌŪÜÑÇ][A-ZĀĒĪŌŪÜÑÇ0-9()\-~∼]*"
)
FORM_SEQUENCE = rf"(?:[~∼\-–]*\s*{HEAD_TOKEN}\s*,?\s*)+"
PAREN_FORM_RE = re.compile(r"\(([^)]*)\)")
POSSESSED_FORM_LABEL = (
    r"possessed form|possesed form|posseseed form|prossessed form|"
    r"possessed fom"
)
DEF_START_WORDS = (
    r"vt|vi|vrefl|vimpers|to|for|a|an|the|someone|something|jaguar|stone|groin|jaw|mosquito|"
    r"head|protector|hard|love|six|eight|old|eye|eyelid|skin|jewel|wall|"
    r"clay|female|wooden|damp"
)
MIXED_CAP_FORM_TOKEN = rf"(?=[{LETTER}()]*[{UPPER}][{LETTER}()]*[{UPPER}])[{LETTER}()]+"
MIXED_FORM_TOKEN = (
    rf"(?:{HEAD_TOKEN}|p[ĪI]-?|{MIXED_CAP_FORM_TOKEN}|"
    rf"[{LETTER}()]+(?:[-:][\-{UPPER}()]+)+)"
)
LEADING_FORM_CHUNK_RE = re.compile(
    rf"^[>:~∼\s\-–]*(?:{MIXED_FORM_TOKEN})"
    rf"(?:\s*[~∼]\s*(?:{MIXED_FORM_TOKEN}))*"
    rf"\s+(?=(?:{DEF_START_WORDS})\b)",
)


def skip_inflection_forms(value: str, start: int) -> int:
    index = start
    while index < len(value):
        while index < len(value) and value[index].isspace():
            index += 1
        if index < len(value) and value[index] in ",~":
            index += 1
            continue

        paren = PAREN_FORM_RE.match(value, index)
        if paren:
            inner = paren.group(1).strip()
            if re.fullmatch(r"[A-Za-zĀĒĪŌŪāēīōūÜüÑñÇç-]+", inner) and inner.lower() not in {"one"}:
                index = paren.end()
                continue

        form = FORM_TOKEN_RE.match(value, index)
        if form:
            if form.end() < len(value) and re.match(rf"[{LOWER}]", value[form.end()]):
                break
            index = form.end()
            continue
        break

    while index < len(value) and value[index].isspace():
        index += 1
    if index < len(value) and value[index] == ",":
        index += 1
        while index < len(value) and value[index].isspace():
            index += 1
    return index


def remove_labelled_inflection_forms(value: str) -> str:
    output: list[str] = []
    position = 0
    for match in INFLECTION_LABEL_RE.finditer(value):
        if match.start() < position:
            continue
        output.append(value[position : match.start()])
        position = skip_inflection_forms(value, match.end())
    output.append(value[position:])
    return "".join(output)


def strip_inflection_info(value: str) -> str:
    value = remove_labelled_inflection_forms(value)
    value = re.sub(
        rf";\s*(?:the\s+)?(?:inalienably possessed form|inalienable possessed form|"
        rf"{POSSESSED_FORM_LABEL})\s*(?::|;|\.|–|-)?\s*{FORM_SEQUENCE}$",
        "",
        value,
    )
    value = re.sub(
        rf"\b(inalienably possessed form|inalienable possessed form)"
        rf"\s*(?::|;|\.|–|-)?\s*{FORM_SEQUENCE}"
        rf"(?=(?:to|for|a|an|the|someone|something)\b|[a-zāēīōūüñç]|/)",
        "inalienably possessed form; ",
        value,
    )
    value = re.sub(
        rf"\b(?:{POSSESSED_FORM_LABEL})\s*(?::|;|\.|–|-)?\s*{FORM_SEQUENCE}"
        rf"(?=(?:to|for|a|an|the|someone|something)\b|[a-zāēīōūüñç]|/)",
        "possessed form; ",
        value,
    )
    value = re.sub(
        rf"\b(inalienably possessed form|inalienable possessed form)"
        rf"\s*;\s*of\s+{HEAD_TOKEN}\s*;\s*",
        "inalienably possessed form; ",
        value,
    )
    value = re.sub(
        rf"\b(possessed form|prossessed form|inalienable possessed form|"
        rf"inalienably possessed form|compounding form):\s*{FORM_SEQUENCE}(?=(?:to|for|a|an|the|someone|"
        rf"something)\b|[a-zāēīōūüñç])",
        r"\1 ",
        value,
    )
    value = re.sub(
        rf"\b(possessed form|prossessed form|inalienable possessed form|inalienably possessed form)"
        rf"\s+of\s+{HEAD_TOKEN}\.?(?:\s+|$)",
        r"\1 ",
        value,
    )
    value = value.replace("prossessed form", "possessed form")
    value = re.sub(
        rf"\b(?:possesed form|posseseed form|possessed fom)\b",
        "possessed form",
        value,
        flags=re.I,
    )
    value = re.sub(
        rf"^in compounds:?\s+{FORM_SEQUENCE}(?=(?:{DEF_START_WORDS})\b)",
        "",
        value,
    )
    value = re.sub(
        rf"\bnegative form:\s*{FORM_SEQUENCE}(?=(?:let|may|such|as)\b)",
        "negative form; ",
        value,
    )
    value = re.sub(
        rf"\bnegated form of\s+{HEAD_TOKEN}\s+(?=(?:as|such)\b)",
        "negated form; ",
        value,
    )
    value = re.sub(
        rf"\b(vrefl,vt|vrefl|vimpers|vt|vi)\s*;\s*{FORM_SEQUENCE}"
        rf"(?=(?:to|for)\b)",
        r"\1 ",
        value,
    )
    value = re.sub(
        rf"^{FORM_SEQUENCE}(?=(?:to|for|a|an|the|someone|something|vt|vi|vrefl|"
        rf"nonact|applic|caus|break|particle|suppletive|irregular|compounding|"
        rf"possessed|inalienable)\b)",
        "",
        value,
    )
    value = re.sub(
        rf"^p[ĪI]-?\s+{FORM_SEQUENCE}(?=(?:mosquito|jaw)\b)",
        "",
        value,
    )
    value = LEADING_FORM_CHUNK_RE.sub("", value)
    value = re.sub(
        rf"\b(applic|nonact|caus|redup)\s+{FORM_SEQUENCE}\s*;\s*",
        lambda match: match.group(1).lower() + ".; ",
        value,
    )
    value = re.sub(rf"\s+{HEAD_TOKEN}\s+(?:applic|nonact|caus|redup)\..*$", "", value)
    value = re.sub(
        rf"\b(suppletive verb) with {HEAD_TOKEN}\s+(?=to\b)",
        r"\1 ",
        value,
    )
    value = re.sub(
        rf"\bparticle cluster used in place of simple {HEAD_TOKEN}\s+(?=to\b)",
        "particle cluster used ",
        value,
    )
    value = re.sub(r"\bno preterit form given\s+", "", value, flags=re.I)
    value = re.sub(r"\bpreterit-as-present verb\s*;\s*", "", value, flags=re.I)
    value = re.sub(rf"\bpreterit form of\s+{HEAD_TOKEN}\s+", "", value, flags=re.I)
    value = re.sub(
        r"\bsingular present and preterit only,\s*plus derivations\s+",
        "",
        value,
    )
    value = re.sub(
        r"^and preterit only,\s*plus derivations\s+",
        "",
        value,
        flags=re.I,
    )
    value = re.sub(
        r"\s+added directly to the preterit stem\b",
        "",
        value,
        flags=re.I,
    )
    value = re.sub(r"\bplural form of .*? nominalization\s+", "", value, flags=re.I)
    value = re.sub(r"\bplural form\s+", "", value, flags=re.I)
    value = re.sub(r"\bplural\s*;\s*", "", value, flags=re.I)
    value = re.sub(r"\s*\(plural\)", "", value, flags=re.I)
    value = re.sub(r"\byou\s+\(plural\)", "you", value, flags=re.I)
    value = re.sub(r"\bwho-plural\?", "who?", value, flags=re.I)
    value = re.sub(
        r"\b(first|second|third) pers\. plural possessed form\b",
        r"\1 pers. possessed form",
        value,
        flags=re.I,
    )
    value = re.sub(r"\b(vrefl,vt|vrefl|vimpers|vt|vi)\s*;\s+(?=(?:to|for)\b)", r"\1 ", value)
    value = re.sub(
        rf"\b(vrefl,vt|vrefl|vimpers|vt|vi)\s*;\s*{HEAD_TOKEN},?\s+(?=(?:to|for)\b)",
        r"\1 ",
        value,
    )
    value = re.sub(r"\b(vrefl,vt|vrefl|vimpers|vt|vi),\s+(?=(?:to|for)\b)", r"\1 ", value)
    value = re.sub(
        rf"\b(inalienably possessed form|inalienable possessed form)"
        rf"\s*;\s*of\s+{HEAD_TOKEN}\s*;\s*",
        "inalienably possessed form; ",
        value,
    )
    value = re.sub(
        r"\b(possessed form|inalienable possessed form|inalienably possessed form)"
        r"\s+(?=(?:to|for|a|an|the|someone|something)\b|[a-zāēīōūüñç])",
        r"\1; ",
        value,
    )
    value = re.sub(rf"\s+bound with\s+[–-]?{HEAD_TOKEN}", ";", value)
    value = re.sub(rf"\b(honorific form) of\s+{HEAD_TOKEN}\.?", r"\1", value)
    value = re.sub(
        rf";\s*vocative\s+[–-]?{FORM_SEQUENCE}(?:\([^)]*\))?",
        "",
        value,
    )
    value = re.sub(r";\s*;", ";", value)
    value = re.sub(r";\s*/", " /", value)
    value = re.sub(r"\s+([,;:])", r"\1", value)
    value = re.sub(r"(^|;\s*)[,;]\s*", r"\1", value)
    value = re.sub(r"\s+", " ", value).strip(" ;,")
    return value


def clean_piece(piece: str) -> str:
    value = piece.strip()
    value = TRAIL_SEE_RE.sub(" ", value).strip()
    value, _ = strip_leading_head(value)
    value = remove_source_markers(value)
    value = re.sub(r"\s*/\s*", " / ", value)
    value = re.sub(r"\s+,", ",", value)
    value = re.sub(r",\s*,", ",", value)
    value = re.sub(r"\s+([.;:])", r"\1", value)
    value = re.sub(r"\(\s+", "(", value)
    value = re.sub(r"\s+\)", ")", value)
    value = value.replace("(ser]", "ser")
    value = re.sub(r"\s+", " ", value).strip(" ;,")

    if " -- " in value:
        value = value.split(" -- ", 1)[0]

    tail = TAIL_DERIV_ANY_RE.match(value)
    if tail and not (
        " / " in value
        or re.match(
            r"^(?:vt|vi|vrefl|vimpers|to|for|someone|something|a |an |"
            r"the |pl:|pret:)",
            value,
        )
    ):
        return (tail.group("tag") + ".").replace("Redup.", "redup.")

    value = LEADING_DERIV_REF_RE.sub(lambda m: m.group("tag") + ".; ", value)
    value = POST_TAG_HEAD_RE.sub(r"\1; ", value)
    value = normalize_this_definition(value)

    if "; see " in value:
        value = value.split("; see ", 1)[0]
    if " Some examples " in value:
        value = value.split(" Some examples ", 1)[0]

    value = NOTE_AFTER_PERIOD_RE.sub("", value).strip()
    if " / " in value or re.search(
        r"\b(?:pl:|possessed form|suffix|compounding element|compound "
        r"postposition|postposition|particle|place name|personal name|"
        r"expression|exclamation|interjection|salutation|leavetaking|vt|vi|"
        r"vrefl|vimpers|to |for |someone|something)\b",
        value,
    ):
        value = NOTE_NO_PERIOD_RE.sub("", value).strip()

    value = TRAIL_SEE_RE.sub(" ", value).strip()
    deriv_only = DERIV_REF_ONLY_RE.match(value)
    if deriv_only:
        value = deriv_only.group("tag").replace("Redup", "redup") + "."
    else:
        bare_deriv_only = BARE_DERIV_REF_ONLY_RE.match(value)
        if bare_deriv_only:
            value = bare_deriv_only.group("tag").replace("Redup", "redup") + "."
        else:
            value = TRAIL_DERIV_RE.sub("", value).strip()

    value = re.sub(r"\b(applic|nonact|caus|redup)\.\s*;\s*", r"\1.; ", value)
    value = value.replace("applic;", "applic.;")
    value = value.replace("nonact;", "nonact.;")
    value = value.replace("caus;", "caus.;")
    value = value.replace("redup;", "redup.;")
    value = re.sub(r"\bpret:\s*;\s*", "pret: ", value)
    value = re.sub(r"\b(vrefl):\s+pret\s*;", r"\1; pret:", value)
    value = re.sub(r"\b(pret|pl|PL)\s*;\s*", r"\1: ", value)
    value = re.sub(r"\bpossessed form\s*;\s*", "possessed form: ", value)
    value = re.sub(r"^=\s*", "", value)
    value = re.sub(r"\bused in [A-Z]\b\s*", "used ", value)
    value = strip_inflection_info(value)

    value = value.strip(" ;,-")
    if value not in {
        "nonact.",
        "applic.",
        "caus.",
        "redup.",
        "altern. caus.",
        "altern. applic.",
    }:
        value = value.rstrip(".")
    if len(value) >= 2 and (value[0], value[-1]) in {("'", "'"), ("‘", "’")}:
        value = value[1:-1]
    return re.sub(r"\s+", " ", value).strip()


def looks_like_definition(value: str) -> bool:
    if not value:
        return False
    if " / " in value:
        return True
    if re.search(
        r"\b(?:vt|vi|vrefl|vimpers|pret:|pl:|PL:|nonact\.|applic\.|"
        r"caus\.|redup\.|altern\. caus\.|postposition|suffix|particle|"
        r"place name|personal name|expression|exclamation|interjection|"
        r"salutation|leavetaking phrase|possessed form|compounding element|"
        r"compound postposition|locative suffix|possessor suffix|derivational "
        r"suffix|transitive verb-forming suffix|applicative form|"
        r"nonactive form)\b",
        value,
    ):
        return True
    if re.match(
        r"^(?:to|for|a|an|the|someone|something|one|all|each|in|at|near|"
        r"however|given|since|element meaning|element having|element forming|"
        r"element referring|initial element|compounding form|compound verb|"
        r"variant of|indicates|mild|dried|lame|bean|reed|flower|base|group|"
        r"son-in-law|gully|swelling|garment|illness|boat|water vapor|"
        r"only attested|possessor derivation|plural|personal name|place name)\b",
        value,
        re.I,
    ):
        return True
    return len(value.split()) <= 8 and not re.match(
        r"^(?:This|The|T|Z|M|C|In|It|There|Both|Only|By|Although|Since|"
        r"attests|gives)\b",
        value,
    )


def normalize_karttunen_row(row: dict[str, str]) -> tuple[str, str]:
    record_id = row.get("record_id", "")
    if record_id in SPECIAL_NORMALIZATIONS:
        return SPECIAL_NORMALIZATIONS[record_id], "nodal-special"

    value = row.get("Traducción", "")
    value = value.replace("∕", "/").replace("“", "'").replace("”", "'")
    value = re.sub(r"\s+", " ", value).strip()
    value = strip_leading_exact_original(value, row.get("Original", ""))
    value, head = strip_leading_head(value)
    value = SOURCE_BEFORE_HEAD_RE.sub(". ", value)
    value = EMBED_HEAD_RE.sub(
        lambda match: match.group("prefix") + " || " + match.group(2) + " ",
        value,
    )

    parts: list[str] = []
    for piece in value.split("||"):
        cleaned = clean_piece(piece)
        if looks_like_definition(cleaned):
            parts.append(cleaned)

    if not parts:
        cleaned = clean_piece(value)
        if cleaned or head:
            parts = [cleaned]

    output: list[str] = []
    seen: set[str] = set()
    for part in parts:
        part = re.sub(r"\s*/\s*", " / ", part)
        part = re.sub(r"\s+", " ", part).strip(" ;,")
        if part and part not in seen:
            output.append(part)
            seen.add(part)

    route = "general"
    if "See " in row.get("Traducción", "") or len(output) > 1:
        route = "backpropagated-components"
    if not output:
        route = "empty-no-definition"
    return "; ".join(output).strip(), route


def strip_existing_original_comment(value: str) -> str:
    if ORIGINAL_COMMENT_MARKER not in value:
        return value.strip()
    prefix = value.split(ORIGINAL_COMMENT_MARKER, 1)[0].rstrip()
    return re.sub(r"(?:<br\s*/?>\s*)+$", "", prefix, flags=re.I).strip()


def merge_original_comment(existing: str, original_value: str) -> str:
    block = f"{ORIGINAL_COMMENT_MARKER} {html.escape(original_value, quote=False)}"
    prefix = strip_existing_original_comment(existing or "")
    if not prefix:
        return block
    return f"{prefix}<br><br>{block}"


def next_backup_path(data_path: Path) -> Path:
    existing = []
    for candidate in data_path.parent.glob("data.jsonl.bak*.gz"):
        match = re.fullmatch(r"data\.jsonl\.bak(\d+)\.gz", candidate.name)
        if match:
            existing.append(int(match.group(1)))
    return data_path.parent / f"data.jsonl.bak{(max(existing) if existing else 0) + 1}.gz"


def read_rows(data_path: Path) -> list[dict[str, str]]:
    with gzip.open(data_path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def write_rows(data_path: Path, rows: list[dict[str, str]]) -> None:
    tmp_path = data_path.with_suffix(data_path.suffix + ".tmp")
    with gzip.GzipFile(filename="", mode="wb", fileobj=tmp_path.open("wb"), mtime=0) as gz:
        for row in rows:
            line = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
            gz.write((line + "\n").encode("utf-8"))
    tmp_path.replace(data_path)


def write_audit(audit_path: Path, changes: list[dict[str, str]]) -> None:
    with audit_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "record_id",
                "route",
                "escritura_original",
                "texto_estandarizado",
                "source_traduccion",
                "old_traduccion",
                "new_traduccion",
                "old_comentario",
                "new_comentario",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(changes)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/data.jsonl.gz")
    parser.add_argument(
        "--original-data",
        help=(
            "Optional original JSONL.GZ to use as the source text for "
            "normalization and preserved comments."
        ),
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--audit",
        default="resources/karttunen_normalization_audit.tsv",
    )
    parser.add_argument(
        "--summary",
        default="resources/karttunen_normalization_summary.json",
    )
    args = parser.parse_args()

    data_path = Path(args.data)
    rows = read_rows(data_path)
    source_rows_by_id: dict[str, dict[str, str]] = {}
    if args.original_data:
        source_rows_by_id = {
            row.get("record_id", ""): row
            for row in read_rows(Path(args.original_data))
            if row.get("Fuente") == SOURCE_NAME and row.get("record_id")
        }

    route_counts: Counter[str] = Counter()
    changes: list[dict[str, str]] = []
    karttunen_rows = 0
    translation_changed = 0
    comment_changed = 0
    source_translation_changed = 0

    for row in rows:
        if row.get("Fuente") != SOURCE_NAME:
            continue
        karttunen_rows += 1
        source_row = source_rows_by_id.get(row.get("record_id", ""), row)
        source_value = source_row.get("Traducción", "")
        old_value = row.get("Traducción", "")
        old_comment = row.get("Comentario", "")
        new_value, route = normalize_karttunen_row(source_row)
        new_comment = old_comment
        if source_value != new_value:
            source_translation_changed += 1
        if source_value and source_value != new_value:
            new_comment = merge_original_comment(old_comment, source_value)

        changed_translation = new_value != old_value
        changed_comment = new_comment != old_comment
        if changed_translation or changed_comment:
            row["Traducción"] = new_value
            row["Comentario"] = new_comment
            changes.append(
                {
                    "record_id": row.get("record_id", ""),
                    "route": route,
                    "escritura_original": row.get("Original", ""),
                    "texto_estandarizado": row.get("Editado", ""),
                    "source_traduccion": source_value,
                    "old_traduccion": old_value,
                    "new_traduccion": new_value,
                    "old_comentario": old_comment,
                    "new_comentario": new_comment,
                }
            )
            route_counts[route] += 1
            if changed_translation:
                translation_changed += 1
            if changed_comment:
                comment_changed += 1

    unchanged = karttunen_rows - len(changes)
    summary = {
        "source": SOURCE_NAME,
        "totalRows": karttunen_rows,
        "changedRows": len(changes),
        "translationChangedRows": translation_changed,
        "commentChangedRows": comment_changed,
        "sourceTranslationChangedRows": source_translation_changed,
        "unchangedRows": unchanged,
        "emptyAfterNormalization": sum(1 for change in changes if not change["new_traduccion"]),
        "routeCounts": dict(sorted(route_counts.items())),
        "auditPath": args.audit,
        "applied": bool(args.apply),
    }
    if args.original_data:
        summary["originalDataPath"] = args.original_data

    if args.apply:
        backup = next_backup_path(data_path)
        shutil.copy2(data_path, backup)
        write_rows(data_path, rows)
        summary["backupPath"] = str(backup)

    write_audit(Path(args.audit), changes)
    Path(args.summary).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
