#!/usr/bin/env python3
"""Rank remaining public-display cleanup residue by source.

This is a read-only planning aid. It scans public display fields, groups likely
residue by source and pattern, and writes a compact summary plus examples so a
cleanup stage can be chosen before writing any data.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DATA_PATH = Path("data/data.jsonl.gz")
SUMMARY_PATH = Path("resources/source_cleanup_dashboard_summary.tsv")
EXAMPLES_PATH = Path("resources/source_cleanup_dashboard_examples.tsv")

PUBLIC_FIELDS = [
    "Traducción",
    "Traducción (es)",
    "Comentario",
    "Comentario (es)",
    "Comentario_wimmer_plus_html",
]
SPANISH_SIDE_ONLY_SOURCES = {"2021 Wimmer"}
SPANISH_SIDE_FIELDS = ["Traducción (es)", "Comentario (es)"]

TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
ITALIC_RE = re.compile(r"<i\b[^>]*>.*?</i>", re.I | re.S)
SMALL_RE = re.compile(r"<small\b[^>]*>.*?</small>", re.I | re.S)
WORD_BOUNDARY = r"(?<![\w-])(?:{})(?![\w-])"
LETTER_CHARS = r"A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç"
LETTER_BRACKET_RE = re.compile(rf"\[[{LETTER_CHARS}]{{1,40}}\]")
PRECEDING_WORD_RE = re.compile(rf"([{LETTER_CHARS}]{{2,40}})\s*$")
CEDILLA_RE = re.compile(r"[çÇ]")
HAT_VOWEL_RE = re.compile(r"[âêîôÂÊÎÔ]")
SLASH_O_RE = re.compile(r"(?<![A-Za-zÀ-ÖØ-öø-ÿ])/o\b|\bo/(?=\S)", re.I)
LETTER_BRACKET_FALSE_POSITIVE_INNERS = {
    "auh",
    "ic",
    "roto",
    "rúbrica",
    "rubrica",
    "scilicet",
    "sic",
    "vel",
    "xii",
    "xvi",
}
HAT_VOWEL_FALSE_POSITIVE_WORDS = {
    "apparaît",
    "être",
    "même",
    "pâle",
}
HAT_VOWEL_FALSE_POSITIVE_RE = re.compile(
    r"(?<![\w-])(?:" + "|".join(re.escape(word) for word in HAT_VOWEL_FALSE_POSITIVE_WORDS) + r"|peut-être)(?![\w-])",
    re.I,
)

SPANISH_RESIDUE_TERMS = {
    "acanuel",
    "adereçan",
    "affirma",
    "affirman",
    "afflije",
    "afflijo",
    "anelar",
    "ansí",
    "assi",
    "assí",
    "azezando",
    "baptismo",
    "buelban",
    "buelben",
    "cabeça",
    "cabeças",
    "coraçon",
    "coraçones",
    "dezir",
    "dezima",
    "deziocheno",
    "dezuello",
    "differencia",
    "differencias",
    "dixo",
    "dixeron",
    "diziendo",
    "enpanada",
    "exenplo",
    "frios",
    "hazer",
    "hazeros",
    "hazerlos",
    "haziendas",
    "honrra",
    "honrrada",
    "honrrosas",
    "loz",
    "muger",
    "mugeres",
    "moço",
    "moços",
    "navaxa",
    "nuves",
    "officio",
    "officios",
    "offrendas",
    "passada",
    "perona",
    "qual",
    "quales",
    "quando",
    "quanto",
    "quarta",
    "quatro",
    "renouar",
    "rezio",
    "rezios",
    "salce",
    "salces",
    "tiêpo",
    "tienpo",
    "valde",
    "xicaras",
    "xicara",
    "ymgen",
}
SPANISH_RESIDUE_RE = re.compile(
    WORD_BOUNDARY.format("|".join(re.escape(term) for term in sorted(SPANISH_RESIDUE_TERMS, key=len, reverse=True))),
    re.I,
)

PATTERN_LABELS = {
    "known_spanish_residue": "known old-Spanish/OCR token",
    "slash_o": "slash-marked Spanish o alternative",
    "cedilla": "visible cedilla",
    "letter_brackets": "visible bracketed letters/words",
    "hat_vowels": "visible circumflex vowel",
}
PATTERN_WEIGHTS = {
    "known_spanish_residue": 5.0,
    "slash_o": 4.0,
    "cedilla": 2.0,
    "letter_brackets": 1.5,
    "hat_vowels": 0.5,
}
LOW_PRIORITY_SOURCES = {
    "1984 Tzinacapan",
    "1992 Karttunen",
    "2002 Mecayapan",
    "2021 Wimmer",
    "V94 Diccionario Global SNP",
}
SOURCE_PRIORITY_MULTIPLIER = {
    source: 0.15 for source in LOW_PRIORITY_SOURCES
}
TRIAGE_LABELS = {
    "batch_candidate": "likely exact cleanup candidate",
    "orthography_review": "source-specific orthography review",
    "source_orthography": "source/citation orthography, usually leave",
    "inline_restoration_review": "inline restoration or supplied letters",
    "preceding_correction_review": "bracketed correction of preceding spelling",
    "semantic_gloss": "semantic/editorial gloss, usually leave",
    "source_label": "source label or witness note, usually leave",
    "source_quote": "quoted source/citation residue, usually leave",
    "editorial_review": "bracket role review: correction, insertion, gloss, or note",
}
TRIAGE_PRIORITY_MULTIPLIER = {
    "batch_candidate": 1.0,
    "orthography_review": 0.45,
    "inline_restoration_review": 0.35,
    "preceding_correction_review": 0.65,
    "editorial_review": 0.25,
    "semantic_gloss": 0.03,
    "source_label": 0.03,
    "source_orthography": 0.02,
    "source_quote": 0.01,
}
SOURCE_QUOTE_CEDILLA_SOURCES = {
    "1780 ? Bnf_361",
    "1992 Karttunen",
    "2021 Wimmer",
}
SOURCE_ORTHOGRAPHY_HAT_SOURCES = {
    "153? Trilingüe",
    "1645 Carochi",
    "17?? Bnf_362bis",
    "1780 ? Bnf_361",
    "1780 Clavijero",
    "1759 Paredes",
}
SOURCE_LABEL_BRACKET_SOURCES = {
    "1565 Sahagún Escolios",
    "1580 Sahagún/Máynez",
}
KNOWN_BRACKET_INSERTION_TOKENS = {
    ("1551-95 Documentos nahuas de la Ciudad de México", "[Mauitoca]"),
    ("1551-95 Documentos nahuas de la Ciudad de México", "[Topilaneuc]"),
    ("1551-95 Documentos nahuas de la Ciudad de México", "[noxhuiuh]"),
    ("1551-95 Documentos nahuas de la Ciudad de México", "[yahualtic]"),
    ("1551-95 Documentos nahuas de la Ciudad de México", "[yematl]"),
    ("1629 Alarcón", "[MAGUEYES]"),
    ("1759 Paredes", "[tonaloyan]"),
    ("1645 Carochi", "[derogativo]"),
    ("1645 Carochi", "[nāmauh]"),
    ("1645 Carochi", "[niyauh]"),
    ("1645 Carochi", "[o]"),
    ("1645 Carochi", "[reverencial]"),
    ("1645 Carochi", "[ātlācatl]"),
    ("2021 Wimmer", "[acanalada]"),
    ("2021 Wimmer", "[agua]"),
    ("2021 Wimmer", "[acuática]"),
    ("2021 Wimmer", "[cobre]"),
    ("2021 Wimmer", "[copper]"),
    ("2021 Wimmer", "[crossed]"),
    ("2021 Wimmer", "[cruzadas]"),
    ("2021 Wimmer", "[cuadrado]"),
    ("2021 Wimmer", "[dried]"),
    ("2021 Wimmer", "[eagle]"),
    ("2021 Wimmer", "[es]"),
    ("2021 Wimmer", "[guerreros]"),
    ("2021 Wimmer", "[inlaid]"),
    ("2021 Wimmer", "[maguey]"),
    ("2021 Wimmer", "[mosaico]"),
    ("2021 Wimmer", "[mosaic]"),
    ("2021 Wimmer", "[pieles]"),
    ("2021 Wimmer", "[placa]"),
    ("2021 Wimmer", "[plate]"),
    ("2021 Wimmer", "[quiquiztli]"),
    ("2021 Wimmer", "[resina]"),
    ("2021 Wimmer", "[resin]"),
    ("2021 Wimmer", "[ribbed]"),
    ("2021 Wimmer", "[seca]"),
    ("2021 Wimmer", "[skins]"),
    ("2021 Wimmer", "[square]"),
    ("2021 Wimmer", "[teotenacochtli]"),
    ("2021 Wimmer", "[tlacualli]"),
    ("2021 Wimmer", "[water]"),
    ("2021 Wimmer", "[y]"),
    ("2021 Wimmer", "[águila]"),
}
KNOWN_INLINE_RESTORATION_SOURCE_TOKENS = {
    ("1645 Carochi", "[a]"),
    ("1645 Carochi", "[c]"),
    ("1645 Carochi", "[il]"),
    ("1645 Carochi", "[l]"),
    ("1645 Carochi", "[m]"),
    ("1645 Carochi", "[mo]"),
    ("1645 Carochi", "[n]"),
    ("1645 Carochi", "[ni]"),
    ("1645 Carochi", "[nic]"),
    ("1645 Carochi", "[nicno]"),
    ("1645 Carochi", "[nino]"),
    ("1645 Carochi", "[niqu]"),
    ("1645 Carochi", "[nitla]"),
    ("1645 Carochi", "[nitē]"),
    ("1645 Carochi", "[qu]"),
    ("1645 Carochi", "[qui]"),
    ("1645 Carochi", "[t]"),
    ("1645 Carochi", "[ticmo]"),
    ("1645 Carochi", "[tl]"),
    ("1645 Carochi", "[tla]"),
    ("1645 Carochi", "[tē]"),
    ("1645 Carochi", "[z]"),
    ("1645 Carochi", "[ā]"),
    ("1645 Carochi", "[āya]"),
    ("1645 Carochi", "[ī]"),
    ("1645 Carochi", "[ō]"),
    ("1645 Carochi", "[ōnino]"),
    ("1645 Carochi", "[ōtla]"),
    ("2021 Wimmer", "[m]"),
    ("2021 Wimmer", "[n]"),
}
KNOWN_PRECEDING_CORRECTION_PAIRS = {
    ("1547 Olmos_V ?", "jasar", "sajar"),
    ("1547 Olmos_V ?", "nondo", "nudo"),
    ("1547 Olmos_V ?", "valle", "balde"),
}
KNOWN_NOT_PRECEDING_CORRECTION_PAIRS = {
    ("1551-95 Documentos nahuas de la Ciudad de México", "entrada", "entrar"),
    ("1780 ? Bnf_361", "secta", "seta"),
    ("2021 Wimmer", "teonecochtli", "teotenacochtli"),
}
LATIN_OR_SOURCE_RESIDUE_TOKENS = {
    "quarta",
    "valde",
}


@dataclass(frozen=True)
class Hit:
    source: str
    pattern: str
    triage: str
    record_id: str
    field: str
    token: str
    context: str


def clean_text(value: str, *, include_italic: bool) -> str:
    text = html.unescape(value)
    if not include_italic:
        text = ITALIC_RE.sub(" ", text)
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def snippet(text: str, start: int, end: int, width: int = 110) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    return text[left:right].strip()


def iter_rows(path: Path) -> Iterable[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def fields_for_source(source: str, *, all_public_fields: bool) -> list[str]:
    if not all_public_fields and source in SPANISH_SIDE_ONLY_SOURCES:
        return list(SPANISH_SIDE_FIELDS)
    return list(PUBLIC_FIELDS)


def iter_field_hits(row: dict, *, include_italic: bool, all_public_fields: bool) -> Iterable[Hit]:
    source = str(row.get("Fuente", ""))
    record_id = str(row.get("record_id", ""))
    for field in fields_for_source(source, all_public_fields=all_public_fields):
        value = row.get(field, "")
        if not isinstance(value, str) or not value:
            continue
        text = clean_text(value, include_italic=include_italic)
        letter_text = (
            clean_text(SMALL_RE.sub(" ", value), include_italic=include_italic)
            if source in SOURCE_LABEL_BRACKET_SOURCES
            else text
        )
        scans = [
            ("known_spanish_residue", SPANISH_RESIDUE_RE),
            ("slash_o", SLASH_O_RE),
            ("cedilla", CEDILLA_RE),
            ("letter_brackets", LETTER_BRACKET_RE),
            ("hat_vowels", HAT_VOWEL_RE),
        ]
        for pattern, regex in scans:
            scan_text = letter_text if pattern == "letter_brackets" else text
            for match in regex.finditer(scan_text):
                if pattern == "hat_vowels" and is_hat_vowel_false_positive(scan_text, match.start(), match.end()):
                    continue
                if pattern == "letter_brackets" and is_letter_bracket_false_positive(match.group(0)):
                    continue
                token = match.group(0)
                triage = triage_hit(source, field, pattern, token, scan_text, match.start(), match.end())
                yield Hit(
                    source=source,
                    pattern=pattern,
                    triage=triage,
                    record_id=record_id,
                    field=field,
                    token=token,
                    context=snippet(scan_text, match.start(), match.end()),
                )


def is_hat_vowel_false_positive(text: str, start: int, end: int) -> bool:
    left = start
    right = end
    while left > 0 and re.match(r"[\w-]", text[left - 1], re.U):
        left -= 1
    while right < len(text) and re.match(r"[\w-]", text[right], re.U):
        right += 1
    token = text[left:right]
    return bool(HAT_VOWEL_FALSE_POSITIVE_RE.fullmatch(token))


def is_letter_bracket_false_positive(token: str) -> bool:
    inner = token.strip("[]").strip().lower()
    return inner in LETTER_BRACKET_FALSE_POSITIVE_INNERS


def edit_distance(a: str, b: str) -> int:
    a = a.lower()
    b = b.lower()
    row = list(range(len(b) + 1))
    for i, char_a in enumerate(a, 1):
        next_row = [i]
        for j, char_b in enumerate(b, 1):
            next_row.append(min(row[j] + 1, next_row[j - 1] + 1, row[j - 1] + (char_a != char_b)))
        row = next_row
    return row[-1]


def preceding_word(text: str, bracket_start: int) -> str:
    match = PRECEDING_WORD_RE.search(text[:bracket_start])
    return match.group(1) if match else ""


def is_preceding_correction(source: str, text: str, token: str, start: int) -> bool:
    inner = token.strip("[]")
    previous = preceding_word(text, start)
    if not previous:
        return False
    if (source, previous.lower(), inner.lower()) in KNOWN_NOT_PRECEDING_CORRECTION_PAIRS:
        return False
    if (source, previous.lower(), inner.lower()) in KNOWN_PRECEDING_CORRECTION_PAIRS:
        return True
    if previous.lower() == inner.lower():
        return True
    distance = edit_distance(previous, inner)
    return distance <= 3 and distance / max(len(previous), len(inner)) <= 0.35


def is_word_char_at(text: str, index: int) -> bool:
    return 0 <= index < len(text) and bool(re.match(r"[\w-]", text[index], re.U))


def has_word_neighbor(text: str, start: int, end: int) -> bool:
    return is_word_char_at(text, start - 1) or is_word_char_at(text, end)


def is_source_quote_residue(source: str, token: str, context: str) -> bool:
    normalized = token.lower()
    if source == "2021 Wimmer":
        return True
    if normalized in LATIN_OR_SOURCE_RESIDUE_TOKENS:
        citation_cues = ("vigilia", "latinos", "nimis", "admod", "hern.", "tertia", "quinta", "feria", "mercurii", "quadra")
        return any(cue in context.lower() for cue in citation_cues)
    return False


def triage_hit(source: str, field: str, pattern: str, token: str, text: str, start: int, end: int) -> str:
    context = snippet(text, start, end)
    if pattern in {"known_spanish_residue", "slash_o"}:
        if pattern == "known_spanish_residue" and is_source_quote_residue(source, token, context):
            return "source_quote"
        return "batch_candidate"
    if pattern == "cedilla":
        if source in SOURCE_QUOTE_CEDILLA_SOURCES:
            return "source_quote"
        if source == "1547 Olmos_G" and any(cue in context for cue in ("Molina", "Paredes", "Sim.")):
            return "source_quote"
        if source == "1759 Paredes" and "rever de" in context.lower():
            return "source_quote"
        if source == "153? Trilingüe":
            return "source_orthography"
        return "orthography_review"
    if pattern == "hat_vowels":
        if source in LOW_PRIORITY_SOURCES or source in SOURCE_ORTHOGRAPHY_HAT_SOURCES:
            return "source_orthography"
        return "orthography_review"
    if pattern == "letter_brackets":
        if is_preceding_correction(source, text, token, start):
            return "preceding_correction_review"
        if (source, token) in KNOWN_BRACKET_INSERTION_TOKENS:
            return "semantic_gloss"
        if (source, token) in KNOWN_INLINE_RESTORATION_SOURCE_TOKENS:
            return "source_quote"
        if has_word_neighbor(text, start, end):
            return "inline_restoration_review"
        if source == "1580 Sahagún/Máynez" and field.startswith("Traducción"):
            return "semantic_gloss"
        if source in SOURCE_LABEL_BRACKET_SOURCES:
            return "source_label"
        if field.startswith("Traducción"):
            return "semantic_gloss"
        return "editorial_review"
    return "editorial_review"


def priority_for(source: str, pattern: str, triage: str, count: int) -> float:
    weight = PATTERN_WEIGHTS.get(pattern, 1.0)
    multiplier = SOURCE_PRIORITY_MULTIPLIER.get(source, 1.0)
    if source in LOW_PRIORITY_SOURCES:
        if pattern == "hat_vowels":
            multiplier = 0.005
        elif pattern in {"known_spanish_residue", "cedilla"}:
            multiplier = 0.05
    if pattern == "hat_vowels" and source in {"153? Trilingüe", "1565 Sahagún Escolios", "1645 Carochi"}:
        multiplier *= 0.4
    multiplier *= TRIAGE_PRIORITY_MULTIPLIER.get(triage, 1.0)
    return count * weight * multiplier


def next_action(pattern: str, triage: str) -> str:
    if triage == "batch_candidate":
        return "safe/pattern candidate: inspect examples, then batch exact replacements"
    if triage == "source_quote":
        return "usually leave: quoted source/citation spelling unless source policy changes"
    if triage == "source_orthography":
        return "usually leave: source orthography or citation notation"
    if triage == "semantic_gloss":
        return "usually leave: bracketed semantic/editorial gloss"
    if triage == "source_label":
        return "usually leave: source label, witness note, or linked lemma marker"
    if triage == "inline_restoration_review":
        return "review exact token: supplied letters may be data correction or source apparatus"
    if triage == "preceding_correction_review":
        return "review as correction: usually replace previous word plus bracket with corrected word"
    if pattern == "cedilla":
        return "source-specific c/z decision: inspect token contexts before replacing"
    if pattern == "letter_brackets":
        return "review bracket role: correction of preceding spelling, insertion, gloss, citation, or public prose"
    if pattern == "hat_vowels":
        return "review only: may be long vowel, nasal expansion, reduplication, or source orthography"
    return "review"


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--source", action="append", help="Limit to a Fuente value. Repeatable.")
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--examples", type=Path, default=EXAMPLES_PATH)
    parser.add_argument("--top", type=int, default=40, help="Rows to print to stdout.")
    parser.add_argument("--examples-per-group", type=int, default=5)
    parser.add_argument("--include-italic", action="store_true")
    parser.add_argument("--all-public-fields", action="store_true")
    parser.add_argument("--min-priority", type=float, default=0.0)
    parser.add_argument("--triage", action="append", help="Limit to a triage class. Repeatable.")
    args = parser.parse_args()

    allowed_sources = set(args.source or [])
    allowed_triages = set(args.triage or [])
    source_pattern_counts: Counter[tuple[str, str, str]] = Counter()
    source_pattern_rows: defaultdict[tuple[str, str, str], set[str]] = defaultdict(set)
    source_pattern_tokens: defaultdict[tuple[str, str, str], Counter[str]] = defaultdict(Counter)
    example_hits: defaultdict[tuple[str, str, str], list[Hit]] = defaultdict(list)

    for row in iter_rows(args.data):
        source = row.get("Fuente", "")
        if allowed_sources and source not in allowed_sources:
            continue
        for hit in iter_field_hits(row, include_italic=args.include_italic, all_public_fields=args.all_public_fields):
            if allowed_triages and hit.triage not in allowed_triages:
                continue
            key = (hit.source, hit.pattern, hit.triage)
            source_pattern_counts[key] += 1
            source_pattern_rows[key].add(hit.record_id)
            source_pattern_tokens[key][hit.token] += 1
            if len(example_hits[key]) < args.examples_per_group:
                example_hits[key].append(hit)

    summary_rows: list[dict[str, object]] = []
    for (source, pattern, triage), count in source_pattern_counts.items():
        priority = priority_for(source, pattern, triage, count)
        if priority < args.min_priority:
            continue
        top_tokens = "; ".join(
            f"{token}={token_count}" for token, token_count in source_pattern_tokens[(source, pattern, triage)].most_common(8)
        )
        summary_rows.append(
            {
                "priority": f"{priority:.1f}",
                "source": source,
                "pattern": pattern,
                "triage": triage,
                "label": PATTERN_LABELS.get(pattern, pattern),
                "triage_label": TRIAGE_LABELS.get(triage, triage),
                "count": count,
                "row_count": len(source_pattern_rows[(source, pattern, triage)]),
                "top_tokens": top_tokens,
                "next_action": next_action(pattern, triage),
            }
        )
    summary_rows.sort(key=lambda row: (float(row["priority"]), int(row["count"])), reverse=True)

    example_rows: list[dict[str, object]] = []
    for row in summary_rows:
        key = (str(row["source"]), str(row["pattern"]), str(row["triage"]))
        for hit in example_hits[key]:
            example_rows.append(
                {
                    "source": hit.source,
                    "pattern": hit.pattern,
                    "triage": hit.triage,
                    "record_id": hit.record_id,
                    "field": hit.field,
                    "token": hit.token,
                    "context": hit.context,
                }
            )

    write_tsv(
        args.summary,
        summary_rows,
        ["priority", "source", "pattern", "triage", "label", "triage_label", "count", "row_count", "top_tokens", "next_action"],
    )
    write_tsv(args.examples, example_rows, ["source", "pattern", "triage", "record_id", "field", "token", "context"])

    print(f"summary {args.summary} rows={len(summary_rows)}")
    print(f"examples {args.examples} rows={len(example_rows)}")
    for row in summary_rows[: args.top]:
        print(
            "\t".join(
                [
                    str(row["priority"]),
                    str(row["count"]),
                    str(row["row_count"]),
                    str(row["pattern"]),
                    str(row["triage"]),
                    str(row["source"]),
                    str(row["top_tokens"]),
                ]
            )
        )

    if not summary_rows:
        print("No dashboard residue found.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
