#!/usr/bin/env python3
"""Normalize visible Nahuatl examples in 17?? Bnf_362bis.

This source mixes bold Nahuatl grammar examples with Spanish/Latin
explanation. The pass preserves the raw commentary, expands visible Spanish
abbreviations in public commentary, and rewrites only bold spans for Nahuatl
orthography. Known Spanish/Latin qu- tokens are denied before applying the old
Nahuatl qu-before-a/o convention:

* visible Spanish abbreviations such as ``q[ue]`` -> ``que``.
* ``qu/Qu`` before ``a/o`` -> ``cu/Cu`` inside likely Nahuatl tokens.
* source-attested exact forms such as ``quaquahuē`` -> ``cuacuahuē``.
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
PROPOSALS_PATH = Path("resources/bnf_362bis_example_normalization_proposals.tsv")
REVIEW_PATH = Path("resources/bnf_362bis_example_normalization_review.tsv")
SUMMARY_PATH = Path("resources/bnf_362bis_example_normalization_summary.json")
SOURCE = "17?? Bnf_362bis"
RAW_FIELD = "Comentario_raw_17xx_bnf_362bis"
QU_MARKER = "visible_bold_nahuatl_17xx_bnf_362bis_qu_before_ao_to_cu_2026_06_29"
SOURCE_TERM_MAP_MARKER = "visible_bold_nahuatl_17xx_bnf_362bis_source_term_map_2026_06_29"
SPANISH_ABBREVIATION_MARKER = "visible_spanish_17xx_bnf_362bis_abbreviation_expansion_2026_06_29"
SPANISH_OLD_SPELLING_MARKER = "visible_spanish_17xx_bnf_362bis_old_spelling_2026_06_29"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]

BOLD_RE = re.compile(r"(<b\b[^>]*>)(.*?)(</b>)", re.I | re.S)
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TOKEN_CHARS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùÇç\\[\\]"
WORD_RE = re.compile(rf"[{TOKEN_CHARS}]+")
QU_BEFORE_AO_RE = re.compile(r"[Qq][Uu](?=[aAoOāĀōŌáÁóÓâÂôÔàÀòÒ])")
DIACRITIC_TRANS = str.maketrans(
    "ÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùÇç",
    "AEIOUUNaeiouunAEIOaeioAEIOaeioAEIOUaeiouCc",
)

SPANISH_LATIN_TOKEN_DENY = {
    "aquo",
    "enquanto",
    "qual",
    "quando",
    "quantas",
    "quanto",
    "quarto",
    "quasi",
    "quatro",
    "quatrocientas",
    "quatros",
    "que",
    "quod",
}
SPANISH_LATIN_PREFIX_DENY = (
    "aqu",
    "enquant",
    "qualq",
    "quand",
    "quant",
    "quatr",
    "quo",
)

SOURCE_TERM_REPLACEMENTS = {
    "Helnandotzē": "Hernandotzē",
    "āqualli": "ācualli",
    "quauhti[c]pac": "cuauhticpac",
    "quaquahuē": "cuacuahuē",
    "quaquahuequē": "cuacuahuequē",
}

SPANISH_ABBREVIATION_REPLACEMENTS = {
    "V[erbi )g[racia]": "Verbigracia",
    "V[erbi]g[gracia]": "Verbigracia",
    "V[erbi]g[racia]": "Verbigracia",
    "v[erbi]g[racia]": "verbigracia",
    "V[uestra]M[ajestad]": "Vuestra Majestad",
    "V[uestra]M[ajesta]d": "Vuestra Majestad",
    "V[uestra]m[ajestad]": "Vuestra majestad",
    "V[uestra]m[ajesta]d": "Vuestra majestad",
    "V[uestras]m[ajesta]des": "Vuestras majestades",
    "aV[uestra]m[ajesta]d": "a Vuestra majestad",
    "V[ue]tros": "Vuestros",
    "v[ues]tra": "vuestra",
    "N[uest]ro": "Nuestro",
    "N[uest]ra": "Nuestra",
    "N[ues]tro": "Nuestro",
    "n[uest]ro": "nuestro",
    "n[ues]tro": "nuestro",
    "n[ues]tra": "nuestra",
    "n[ues]tros": "nuestros",
    "n[ues]tos": "nuestros",
    "den[ues]tro": "de nuestro",
    "den[ues]tros": "de nuestros",
    "ant[e nues]tro": "ante nuestro",
    "S[eñor]a": "Señora",
    "S[eño]r": "Señor",
    "S[eñ]or": "Señor",
    "S[eñor]": "Señor",
    "s[eñor]a": "señora",
    "s[eño]r": "señor",
    "S[an]ta": "Santa",
    "D[io]s": "Dios",
    "Sacram[en]to": "Sacramento",
    "pret[erit]o": "pretérito",
    "perf[ecto]": "perfecto",
    "imperf[ecto]": "imperfecto",
    "imper[fecto]": "imperfecto",
    "imperat[ivo]": "imperativo",
    "imperar[ivo]": "imperativo",
    "vetat[iv]o": "vetativo",
    "afirmat[iv]o": "afirmativo",
    "adv[erbi]o": "adverbio",
    "prepos[icion]": "preposición",
    "interrog[acio]n": "interrogación",
    "interrogã[cion]": "interrogación",
    "semipron[ombre]": "semipronombre",
    "usbstant[iv]o": "substantivo",
    "literalm[en]te": "literalmente",
    "ultimam[en]te": "últimamente",
    "infaliblem[en]te": "infaliblemente",
    "especialm[en]te": "especialmente",
    "inmediatam[en]te": "inmediatamente",
    "perezosam[en]te": "perezosamente",
    "etc[etera]": "etcétera",
    "t[iem]pos": "tiempos",
    "t[iem]ps": "tiempos",
    "t[iem]po": "tiempo",
    "t[iemp]o": "tiempo",
    "ning[un]a": "ninguna",
    "Alg[una]s": "Algunas",
    "fut[ur]o": "futuro",
    "desobed[ecen]te": "desobedecente",
    "ladro[n]": "ladrón",
    "pura[-]": "pura",
    "p[a]r[a]": "para",
    "p[ar]a": "para",
    "p[o]rq[ue]": "porque",
    "p[o]r": "por",
    "qualq[uie]ra": "cualquiera",
    "q[uand]o": "cuando",
    "q[uan]do": "cuando",
    "q[uan]to": "cuanto",
    "q[ue ]": "que",
    "q[ue]": "que",
    "porq[ue]": "porque",
    "Porq[ue]": "Porque",
    "aunq[ue]": "aunque",
    "Aunq[ue]": "Aunque",
    "enq[ue]": "en que",
    "deq[ue]": "de que",
    "Deq[ue]": "De que",
    "alq[ue]": "al que",
    "aloq[ue]": "a lo que",
    "elq[ue]": "el que",
    "Elq[ue]": "El que",
    "Delqu[ue]": "Del que",
    "deloq[ue]": "de lo que",
    "conloq[ue]": "con lo que",
    "enloq[ue]": "en lo que",
    "loq[ue]": "lo que",
    "Loq[ue]": "Lo que",
    "conq[ue]": "conque",
    "puesq[ue]": "pues que",
    "Puesq[ue]": "Pues que",
    "hastaq[ue]": "hasta que",
    "anteq[ue]": "ante que",
}
SPANISH_ABBREVIATION_REPLACEMENT_ITEMS = sorted(
    SPANISH_ABBREVIATION_REPLACEMENTS.items(),
    key=lambda item: len(item[0]),
    reverse=True,
)

SPANISH_OLD_SPELLING_REPLACEMENTS = {
    "Ala": "A la",
    "Dela": "De la",
    "Delas": "De las",
    "Dixo": "Dijo",
    "Quantas": "Cuántas",
    "dixo": "dijo",
    "dixeron": "dijeron",
    "dira": "dirá",
    "dies": "diez",
    "estan": "están",
    "estubieron": "estuvieron",
    "executará": "ejecutará",
    "agravo": "agravio",
    "carcel": "cárcel",
    "decian": "decían",
    "dia": "día",
    "dias": "días",
    "havia": "había",
    "Haviendo": "Habiendo",
    "haviendo": "habiendo",
    "haver": "haber",
    "havre": "habré",
    "hiceres": "hicieres",
    "huvo": "hubo",
    "mui": "muy",
    "muger": "mujer",
    "Tios": "Tíos",
    "Yanoviene": "Ya no viene",
    "aalguna": "a alguna",
    "aentender": "a entender",
    "ala": "a la",
    "dela": "de la",
    "delas": "de las",
    "alaletra": "a la letra",
    "alamar": "a la mar",
    "alguntiempo": "algún tiempo",
    "alrio": "al río",
    "alos": "a los",
    "amanera": "a manera",
    "asu": "a su",
    "atodo": "a todo",
    "atodos": "a todos",
    "atu": "a tu",
    "ami": "a mi",
    "añadio": "añadió",
    "aretraherme": "a retraerme",
    "dela": "de la",
    "delafe": "de la fe",
    "delos": "de los",
    "despues": "después",
    "desu": "de su",
    "deun": "de un",
    "deuna": "de una",
    "defiesta": "de fiesta",
    "dispertando": "despertando",
    "dispertaste": "despertaste",
    "espias": "espías",
    "estubiese": "estuviese",
    "forastreros": "forasteros",
    "govierno": "gobierno",
    "Governador": "Gobernador",
    "governador": "gobernador",
    "interrogacion": "interrogación",
    "nolo": "no lo",
    "oir": "oír",
    "oi": "oí",
    "pareciendole": "pareciéndole",
    "pedia": "pedía",
    "podre": "podré",
    "proximo": "próximo",
    "propriamente": "propiamente",
    "qualquiera": "cualquiera",
    "qual": "cual",
    "quexandose": "quejándose",
    "quarto": "cuarto",
    "quatros": "cuatro",
    "quatrocientas": "cuatrocientas",
    "quando": "cuando",
    "quantas": "cuantas",
    "quanto": "cuanto",
    "queria": "quería",
    "saldria": "saldría",
    "semanteras": "sementeras",
    "seras": "serás",
    "sinonimo": "sinónimo",
    "temia": "temía",
    "todavia": "todavía",
    "venis": "venís",
}
SPANISH_OLD_SPELLING_RE = re.compile(
    r"(?<![A-Za-zÀ-ÖØ-öø-ÿĀ-ž])("
    + "|".join(re.escape(old) for old in sorted(SPANISH_OLD_SPELLING_REPLACEMENTS, key=len, reverse=True))
    + r")(?![A-Za-zÀ-ÖØ-öø-ÿĀ-ž])"
)

REVIEW_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "qu_before_a_o_unhandled",
        re.compile(
            r"\b\w*qu[aoāōáóâôàò][A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù\[\]]*",
            re.I,
        ),
        "review qu before a/o not handled by the safe pass",
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


def is_denied_spanish_latin_token(token: str) -> bool:
    key = token_key(token)
    return key in SPANISH_LATIN_TOKEN_DENY or any(key.startswith(prefix) for prefix in SPANISH_LATIN_PREFIX_DENY)


def should_normalize_qu_token(token: str) -> bool:
    key = token_key(token)
    if len(key) < 3 or not re.search(r"qu[ao]", key):
        return False
    return not is_denied_spanish_latin_token(token)


def qu_to_cu(token: str) -> str:
    def repl(match: re.Match[str]) -> str:
        old = match.group(0)
        if old == "QU":
            return "CU"
        if old == "Qu":
            return "Cu"
        return "cu"

    return QU_BEFORE_AO_RE.sub(repl, token)


def source_term_replacement(token: str) -> str:
    replacement = SOURCE_TERM_REPLACEMENTS.get(token)
    if replacement:
        return replacement
    lower_replacement = SOURCE_TERM_REPLACEMENTS.get(token.lower())
    if lower_replacement and token[:1].isupper():
        return lower_replacement[:1].upper() + lower_replacement[1:]
    return lower_replacement or token


def normalize_word(token: str) -> tuple[str, list[tuple[str, str, str]]]:
    changes: list[tuple[str, str, str]] = []

    mapped = source_term_replacement(token)
    if mapped != token:
        changes.append((SOURCE_TERM_MAP_MARKER, token, mapped))
        token = mapped

    if should_normalize_qu_token(token):
        normalized = qu_to_cu(token)
        if normalized != token:
            changes.append((QU_MARKER, token, normalized))
            token = normalized

    return token, changes


def normalize_text(value: str) -> tuple[str, list[tuple[str, str, str]]]:
    changes: list[tuple[str, str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            new, token_changes = normalize_word(old)
            changes.extend(token_changes)
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold(value: object) -> tuple[str, list[tuple[str, str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_text(match.group(2))
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def normalize_spanish_abbreviations(value: object) -> tuple[str, list[tuple[str, str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str, str]] = []
    for old, new in SPANISH_ABBREVIATION_REPLACEMENT_ITEMS:
        count = text.count(old)
        if not count:
            continue
        text = text.replace(old, new)
        changes.extend((SPANISH_ABBREVIATION_MARKER, old, new) for _ in range(count))
    return text, changes


def normalize_spanish_old_spellings(value: object) -> tuple[str, list[tuple[str, str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str, str]] = []

    def repl(match: re.Match[str]) -> str:
        old = match.group(1)
        new = SPANISH_OLD_SPELLING_REPLACEMENTS[old]
        if new != old:
            changes.append((SPANISH_OLD_SPELLING_MARKER, old, new))
        return new

    return SPANISH_OLD_SPELLING_RE.sub(repl, text), changes


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
                    if kind == "qu_before_a_o_unhandled" and is_denied_spanish_latin_token(token):
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
                            "bold_text": bold[:700],
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
    proposals: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

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
            new_value, abbreviation_changes = normalize_spanish_abbreviations(value)
            new_value, spanish_old_spelling_changes = normalize_spanish_old_spellings(new_value)
            new_value, bold_changes = normalize_bold(new_value)
            changes = abbreviation_changes + spanish_old_spelling_changes + bold_changes
            if new_value == value:
                continue
            for marker, old, new in changes:
                row_changes.append((field, marker, old, new))
            if args.apply:
                row[field] = new_value

        if row_changes:
            markers = list(dict.fromkeys(marker for _, marker, _, _ in row_changes))
            counts["proposal_rows"] += 1
            counts["proposal_changes"] += len(row_changes)
            counts["proposal_changes_spanish_abbreviation"] += sum(
                1 for _, marker, _, _ in row_changes if marker == SPANISH_ABBREVIATION_MARKER
            )
            counts["proposal_changes_spanish_old_spelling"] += sum(
                1 for _, marker, _, _ in row_changes if marker == SPANISH_OLD_SPELLING_MARKER
            )
            counts["proposal_changes_qu_before_ao"] += sum(1 for _, marker, _, _ in row_changes if marker == QU_MARKER)
            counts["proposal_changes_source_map"] += sum(
                1 for _, marker, _, _ in row_changes if marker == SOURCE_TERM_MAP_MARKER
            )
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
                if any(marker == QU_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_17xx_bnf_362bis_qu_before_ao_to_cu": {
                            "action": "normalized_qu_before_a_o_to_cu_inside_bold_nahuatl_examples",
                            "marker": QU_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(1 for _, marker, _, _ in row_changes if marker == QU_MARKER),
                            "previous_commentary_sha1": previous_commentary_sha1,
                        },
                    }
                if any(marker == SPANISH_ABBREVIATION_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_17xx_bnf_362bis_spanish_abbreviation_expansion": {
                            "action": "expanded_visible_spanish_abbreviations_in_public_commentary",
                            "marker": SPANISH_ABBREVIATION_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == SPANISH_ABBREVIATION_MARKER
                            ),
                            "previous_commentary_sha1": previous_commentary_sha1,
                        },
                    }
                if any(marker == SPANISH_OLD_SPELLING_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_17xx_bnf_362bis_spanish_old_spelling": {
                            "action": "normalized_visible_spanish_old_spellings_in_public_commentary",
                            "marker": SPANISH_OLD_SPELLING_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == SPANISH_OLD_SPELLING_MARKER
                            ),
                            "previous_commentary_sha1": previous_commentary_sha1,
                        },
                    }
                if any(marker == SOURCE_TERM_MAP_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_17xx_bnf_362bis_source_term_map": {
                            "action": "normalized_source_attested_forms_inside_bold_examples",
                            "marker": SOURCE_TERM_MAP_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == SOURCE_TERM_MAP_MARKER
                            ),
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
