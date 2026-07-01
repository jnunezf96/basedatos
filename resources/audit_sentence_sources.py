#!/usr/bin/env python3
"""Audit sentence-heavy colonial sources for example extraction and cleanup.

This implements the shared first pass for sources whose public commentary is
mostly running Spanish prose, phrasebook sentences, grammar examples, or
narrative contexts. It does not rewrite data. It records what can be extracted
as public example units and which visible Nahuatl-side tokens need source-aware
normalization review.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


DATA_PATH = Path("data/data.jsonl.gz")
SUMMARY_PATH = Path("resources/sentence_source_profile_summary.tsv")
UNITS_PATH = Path("resources/sentence_source_units_audit.tsv")
CANDIDATES_PATH = Path("resources/sentence_source_normalization_candidates.tsv")
PROFILES_PATH = Path("resources/sentence_source_profiles.json")

SENTENCE_SOURCE_PROFILES: dict[str, dict[str, str]] = {
    "1580 Sahagún/Máynez": {
        "tier": "strongest",
        "profile": "sahagun_narrative_terms",
        "treatment": "extract bold Nahuatl terms inside Spanish narrative; normalize embedded Nahuatl cautiously",
        "apply_policy": "review-first",
    },
    "1565 Sahagún Escolios": {
        "tier": "strongest",
        "profile": "numbered_witness_glosses",
        "treatment": "keep existing numbered witness/gloss apparatus; continue source-specific public display repairs",
        "apply_policy": "existing-escolios-pipeline",
    },
    "1629 Alarcón": {
        "tier": "strongest",
        "profile": "ritual_text_plus_spanish_explanation",
        "treatment": "split bold Nahuatl ritual text from Spanish explanation and citation",
        "apply_policy": "review-first",
    },
    "1598 Tezozomoc": {
        "tier": "strongest",
        "profile": "chronicle_narrative_terms",
        "treatment": "extract bold Nahuatl names/terms and preserve surrounding Spanish narrative context",
        "apply_policy": "review-first",
    },
    "1579 Durán": {
        "tier": "strongest",
        "profile": "chronicle_narrative_terms",
        "treatment": "extract Nahuatl terms inside Spanish narrative; avoid broad Spanish modernization",
        "apply_policy": "review-first",
    },
    "1645 Carochi": {
        "tier": "sentence-heavy",
        "profile": "grammar_examples",
        "treatment": "split italic/bold Nahuatl examples from Spanish glosses and grammar citations",
        "apply_policy": "review-first",
    },
    "1611 Arenas": {
        "tier": "sentence-heavy",
        "profile": "phrasebook_pairs",
        "treatment": "align Nahuatl phrasebook sentences with Spanish prompts/translations",
        "apply_policy": "review-first",
    },
    "1759 Paredes": {
        "tier": "sentence-heavy",
        "profile": "religious_sentence_examples",
        "treatment": "split doctrinal/confessional Nahuatl examples from Spanish parenthetical glosses",
        "apply_policy": "review-first",
    },
    "17?? Bnf_362bis": {
        "tier": "sentence-heavy",
        "profile": "grammar_notes_examples",
        "treatment": "align grammar examples with Spanish explanations",
        "apply_policy": "review-first",
    },
    "1551-95 Documentos nahuas de la Ciudad de México": {
        "tier": "sentence-heavy",
        "profile": "legal_document_sentences",
        "treatment": "preserve legal Spanish formulae while extracting embedded Nahuatl documentary sentences",
        "apply_policy": "review-first",
    },
}

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
DISPLAY_FIELDS = ["Traducción", "Traducción (es)", *COMMENTARY_FIELDS]

BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
BOLD_RE = re.compile(r"<b\b[^>]*>(.*?)</b>", re.I | re.S)
SMALL_RE = re.compile(r"<small\b[^>]*>(.*?)</small>", re.I | re.S)
ITALIC_RE = re.compile(r"<i\b[^>]*>(.*?)</i>", re.I | re.S)
WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùÇç\[\]]+")
SENTENCE_PUNCT_RE = re.compile(r"[.!?;:]")
DIACRITIC_TRANS = str.maketrans(
    "ÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùÇç",
    "AEIOUUNaeiouunAEIOaeioAEIOaeioAEIOUaeiouCc",
)

NAHUATL_HINT_WORDS = {
    "in",
    "inic",
    "auh",
    "amo",
    "zan",
    "ca",
    "ye",
    "oc",
    "niman",
    "ma",
    "ic",
    "ipan",
    "itech",
    "yhuan",
    "ihuan",
    "quim",
    "tla",
    "tlah",
}
SPANISH_HINT_WORDS = {
    "el",
    "la",
    "los",
    "las",
    "un",
    "una",
    "unos",
    "unas",
    "de",
    "del",
    "que",
    "se",
    "en",
    "con",
    "por",
    "para",
    "como",
    "no",
    "si",
    "su",
    "sus",
    "al",
    "le",
    "les",
    "lo",
    "cosa",
    "persona",
    "hombre",
    "mujer",
    "dios",
    "señor",
    "madre",
    "padre",
    "hijo",
    "todos",
    "todo",
    "otro",
    "otra",
    "donde",
    "cuando",
    "porque",
    "quien",
    "cual",
    "este",
    "esta",
    "hay",
    "es",
    "son",
    "era",
    "fue",
    "tiene",
    "hacer",
    "dice",
    "dijo",
    "llaman",
    "llamado",
}
SPANISH_TOKEN_DENY = {
    "vez",
    "veces",
    "vayame",
    "voy",
    "voime",
    "vio",
    "vieron",
    "ver",
    "vida",
    "viva",
    "vive",
    "viven",
    "vivir",
    "viviendo",
    "viene",
    "vienen",
    "vinieron",
    "vino",
    "venir",
    "verdad",
    "verdadero",
    "valer",
    "valen",
    "valemos",
    "volver",
    "vuelta",
    "vuestro",
    "vuestra",
    "vuestros",
    "vuestras",
    "veinte",
    "noventa",
    "varon",
    "varón",
    "viejo",
    "vieja",
    "hace",
    "hacer",
    "hacen",
    "haciendo",
    "hicieron",
    "hizo",
    "hombre",
    "hombres",
    "hernandotze",
    "hijo",
    "hijos",
    "hija",
    "hijas",
    "honra",
    "honrar",
    "hora",
    "hoy",
    "hecho",
    "hecha",
    "hechos",
    "hechas",
    "habia",
    "había",
    "habian",
    "habían",
    "habéis",
    "habeis",
    "hubiera",
    "hubiese",
    "hubo",
    "huviera",
    "huvo",
}
NAHUATL_TOKEN_HINTS = (
    "tl",
    "tz",
    "hu",
    "auh",
    "yhu",
    "ihua",
    "hua",
    "tzin",
    "xoch",
    "teo",
    "cuauh",
    "quauh",
    "nahu",
    "mexi",
    "tenuch",
    "atl",
    "yotl",
    "ayotl",
    "pohu",
    "mict",
    "tepec",
    "tlan",
    "quetz",
    "coatl",
    "chih",
    "cal",
    "calli",
    "tocht",
    "cuitl",
    "olli",
    "olli",
    "matl",
    "yollo",
    "yoll",
    "ix",
)

NORMALIZATION_PATTERNS: list[tuple[str, re.Pattern[str], str, str]] = [
    (
        "initial_h_before_aeio",
        re.compile(
            r"(?<![A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù])h[aeioáéíóāēīōâêîôàèìò]"
            r"[A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù\[\]]*",
            re.I,
        ),
        "delete initial h before a/e/i/o in Nahuatl-side examples",
        "candidate",
    ),
    (
        "cedilla",
        re.compile(r"[A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù]*[Çç][A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù]*"),
        "review ç -> z/c depending on source pattern",
        "review",
    ),
    (
        "q_bracket",
        re.compile(r"\b\w*q\[[^\]]+\]\w*", re.I),
        "review bracketed q expansion",
        "review",
    ),
    (
        "qu_before_a_o",
        re.compile(r"\bqu[aoāōáóâôàò][A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù\[\]]*", re.I),
        "review qu before a/o, often cu in normalized Nahuatl",
        "review",
    ),
    (
        "v_likely_u",
        re.compile(r"\b[vV][aeiouāēīōáéíóúâêîôàèìòù]\w*|\w*[aeiouāēīōáéíóúâêîôàèìòù][vV][aeiouāēīōáéíóúâêîôàèìòù]\w*|\bq[vV]\w*"),
        "review v/u historical spelling",
        "review",
    ),
    (
        "circumflex",
        re.compile(r"\b[\wâêîôÂÊÎÔ]*[âêîôÂÊÎÔ][\wâêîôÂÊÎÔ]*\b"),
        "review circumflex as long vowel, reduplication, or hidden n/m",
        "review",
    ),
    (
        "diaeresis",
        re.compile(r"\b[\wäëïöüÄËÏÖÜÿŸ]*[äëïöüÄËÏÖÜÿŸ][\wäëïöüÄËÏÖÜÿŸ]*\b"),
        "review diaeresis source convention",
        "review",
    ),
]


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub("\n", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def words(value: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(value)]


def language_hint(value: str) -> str:
    tokens = words(value)
    if not tokens:
        return "empty"
    spanish = sum(1 for token in tokens if token in SPANISH_HINT_WORDS)
    nahuatl = sum(1 for token in tokens if token in NAHUATL_HINT_WORDS or token.startswith(("tla", "te", "mo", "ni", "qui", "tl")))
    if nahuatl > spanish:
        return "nahuatl"
    if spanish > nahuatl:
        return "spanish"
    return "mixed"


def token_key(token: str) -> str:
    return token.translate(DIACRITIC_TRANS).lower().replace("[", "").replace("]", "")


def looks_nahuatl_token(token: str) -> bool:
    key = token_key(token)
    if len(key) < 3:
        return False
    if key in {word.translate(DIACRITIC_TRANS).lower() for word in SPANISH_TOKEN_DENY}:
        return False
    if key in NAHUATL_HINT_WORDS:
        return True
    return any(hint in key for hint in NAHUATL_TOKEN_HINTS)


def sentence_like(value: str) -> bool:
    tokens = words(value)
    return len(tokens) >= 6 and bool(SENTENCE_PUNCT_RE.search(value))


def extract_small(after_html: str) -> str:
    match = SMALL_RE.search(after_html)
    return clean_html(match.group(1)) if match else ""


def extract_spanish_after(after_html: str) -> tuple[str, str]:
    """Return a likely Spanish gloss/explanation after a bold example."""
    window = after_html[:900]
    if "=" in window:
        right = window.split("=", 1)[1]
        right = re.split(r"<br\s*/?>|<small\b|<b\b", right, maxsplit=1, flags=re.I | re.S)[0]
        text = clean_html(right)
        if text:
            return text, "equals"

    # Alarcon/Bnf style: bold Nahuatl line, then a Spanish line.
    parts = [clean_html(part) for part in BR_RE.split(window)]
    parts = [part for part in parts if part]
    for part in parts[:3]:
        if language_hint(part) == "spanish" or sentence_like(part):
            return part, "next-line"

    # Paredes style: Spanish parenthetical gloss between bold chunks.
    paren = re.search(r"\(([^()]{1,280})\)", clean_html(window))
    if paren:
        text = compact(paren.group(1))
        if text:
            return text, "parenthetical"

    return "", ""


def context_around(html_value: str, start: int, end: int, width: int = 180) -> str:
    left = max(0, start - width)
    right = min(len(html_value), end + width)
    return compact(clean_html(html_value[left:right]))


def iter_units(row: dict) -> Iterable[dict[str, str]]:
    commentary = str(row.get("Comentario", ""))
    profile = SENTENCE_SOURCE_PROFILES[row.get("Fuente", "")]
    profile_name = profile["profile"]

    for index, match in enumerate(BOLD_RE.finditer(commentary), start=1):
        bold_html = match.group(1)
        nahuatl_text = clean_html(bold_html)
        if not nahuatl_text:
            continue
        after_html = commentary[match.end() :]
        spanish_text, relation = extract_spanish_after(after_html)
        citation = extract_small(after_html[:600])
        language = language_hint(nahuatl_text)
        if profile_name in {"chronicle_narrative_terms", "sahagun_narrative_terms"}:
            unit_kind = "narrative_term_context"
        elif relation:
            unit_kind = "paired_example"
        elif language == "nahuatl" and len(words(nahuatl_text)) >= 4:
            unit_kind = "unpaired_nahuatl_example"
        else:
            unit_kind = "bold_term"

        yield {
            "source": row.get("Fuente", ""),
            "record_id": row.get("record_id", ""),
            "original": row.get("Original", ""),
            "editado": row.get("Editado", ""),
            "translation": row.get("Traducción", ""),
            "tier": profile["tier"],
            "profile": profile_name,
            "unit_kind": unit_kind,
            "unit_index": str(index),
            "relation": relation,
            "language_hint": language,
            "nahuatl_text": nahuatl_text,
            "spanish_text": spanish_text,
            "citation": citation,
            "context": context_around(commentary, match.start(), match.end()),
        }


def candidate_suggestion(kind: str, token: str) -> str:
    if kind == "initial_h_before_aeio":
        return re.sub(r"^h", "", token, flags=re.I)
    if kind == "cedilla":
        return token.replace("ç", "z").replace("Ç", "Z")
    if kind == "qu_before_a_o":
        return re.sub(r"^qu", "cu", token, flags=re.I)
    if kind == "v_likely_u":
        return token.replace("v", "u").replace("V", "U")
    return ""


def iter_candidates(unit: dict[str, str]) -> Iterable[dict[str, str]]:
    text = unit["nahuatl_text"]
    unit_language = unit["language_hint"]
    seen: set[tuple[str, str]] = set()
    for kind, pattern, note, confidence in NORMALIZATION_PATTERNS:
        for match in pattern.finditer(text):
            token = match.group(0)
            if unit_language == "spanish" or not looks_nahuatl_token(token):
                continue
            key = (kind, token)
            if key in seen:
                continue
            seen.add(key)
            yield {
                **{field: unit[field] for field in ["source", "record_id", "original", "editado", "tier", "profile", "unit_kind", "unit_index"]},
                "candidate_kind": kind,
                "confidence": confidence,
                "token": token,
                "suggestion": candidate_suggestion(kind, token),
                "note": note,
                "nahuatl_text": text,
                "spanish_text": unit["spanish_text"],
                "citation": unit["citation"],
            }


def iter_rows(path: Path, sources: set[str]) -> Iterable[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("Fuente") in sources:
                yield row


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--source", action="append", help="Limit to a source. Repeatable.")
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--units", type=Path, default=UNITS_PATH)
    parser.add_argument("--candidates", type=Path, default=CANDIDATES_PATH)
    parser.add_argument("--profiles", type=Path, default=PROFILES_PATH)
    parser.add_argument("--max-units-per-source", type=int, default=300)
    args = parser.parse_args()

    sources = set(args.source or SENTENCE_SOURCE_PROFILES)
    unknown = sources - set(SENTENCE_SOURCE_PROFILES)
    if unknown:
        raise SystemExit(f"unknown source(s): {', '.join(sorted(unknown))}")

    summary: dict[str, Counter[str]] = defaultdict(Counter)
    units_out: list[dict[str, str]] = []
    candidates_out: list[dict[str, str]] = []
    unit_samples_by_source: Counter[str] = Counter()

    for row in iter_rows(args.data, sources):
        source = row.get("Fuente", "")
        summary[source]["rows"] += 1
        if row.get("Comentario"):
            summary[source]["commentary_rows"] += 1
        row_units = list(iter_units(row))
        if row_units:
            summary[source]["rows_with_units"] += 1
        for unit in row_units:
            summary[source]["units"] += 1
            summary[source][f"unit_{unit['unit_kind']}"] += 1
            summary[source][f"language_{unit['language_hint']}"] += 1
            unit_candidates = list(iter_candidates(unit))
            if unit_candidates:
                summary[source]["units_with_candidates"] += 1
            for candidate in unit_candidates:
                summary[source]["candidates"] += 1
                summary[source][f"candidate_{candidate['candidate_kind']}"] += 1
                candidates_out.append(candidate)
            if unit_samples_by_source[source] < args.max_units_per_source:
                unit["candidate_count"] = str(len(unit_candidates))
                units_out.append(unit)
                unit_samples_by_source[source] += 1

    summary_rows: list[dict[str, str]] = []
    for source in sorted(sources, key=lambda item: (SENTENCE_SOURCE_PROFILES[item]["tier"], item)):
        profile = SENTENCE_SOURCE_PROFILES[source]
        counts = summary[source]
        candidate_counts = {
            key.replace("candidate_", ""): value
            for key, value in counts.items()
            if key.startswith("candidate_")
        }
        unit_counts = {
            key.replace("unit_", ""): value
            for key, value in counts.items()
            if key.startswith("unit_")
        }
        summary_rows.append(
            {
                "source": source,
                "tier": profile["tier"],
                "profile": profile["profile"],
                "rows": str(counts["rows"]),
                "commentary_rows": str(counts["commentary_rows"]),
                "rows_with_units": str(counts["rows_with_units"]),
                "units": str(counts["units"]),
                "paired_examples": str(counts["unit_paired_example"]),
                "narrative_contexts": str(counts["unit_narrative_term_context"]),
                "unpaired_examples": str(counts["unit_unpaired_nahuatl_example"]),
                "bold_terms": str(counts["unit_bold_term"]),
                "units_with_candidates": str(counts["units_with_candidates"]),
                "candidates": str(counts["candidates"]),
                "candidate_counts": json.dumps(candidate_counts, ensure_ascii=False, sort_keys=True),
                "unit_counts": json.dumps(unit_counts, ensure_ascii=False, sort_keys=True),
                "treatment": profile["treatment"],
                "apply_policy": profile["apply_policy"],
            }
        )

    write_tsv(
        args.summary,
        summary_rows,
        [
            "source",
            "tier",
            "profile",
            "rows",
            "commentary_rows",
            "rows_with_units",
            "units",
            "paired_examples",
            "narrative_contexts",
            "unpaired_examples",
            "bold_terms",
            "units_with_candidates",
            "candidates",
            "candidate_counts",
            "unit_counts",
            "treatment",
            "apply_policy",
        ],
    )
    write_tsv(
        args.units,
        units_out,
        [
            "source",
            "record_id",
            "original",
            "editado",
            "translation",
            "tier",
            "profile",
            "unit_kind",
            "unit_index",
            "relation",
            "language_hint",
            "candidate_count",
            "nahuatl_text",
            "spanish_text",
            "citation",
            "context",
        ],
    )
    write_tsv(
        args.candidates,
        candidates_out,
        [
            "source",
            "record_id",
            "original",
            "editado",
            "tier",
            "profile",
            "unit_kind",
            "unit_index",
            "candidate_kind",
            "confidence",
            "token",
            "suggestion",
            "note",
            "nahuatl_text",
            "spanish_text",
            "citation",
        ],
    )
    args.profiles.write_text(
        json.dumps(SENTENCE_SOURCE_PROFILES, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"summary {args.summary}")
    print(f"units {args.units} rows={len(units_out)}")
    print(f"candidates {args.candidates} rows={len(candidates_out)}")
    print(f"profiles {args.profiles}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
