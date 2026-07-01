#!/usr/bin/env python3
"""Estimate source/field probabilities that major languages are absent.

This is a read-only planning aid for source-specific cleanup. It does not try
to assign one language to a whole cell: dictionary comments are often mixed.
Instead it estimates independent presence probabilities for each language, then
stores the inverse probability so future normalization scripts can avoid
applying Spanish, Nahuatl, French, Latin, English, or Greek rules where that
language is unlikely to be present.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


DATA_PATH = Path("data/data.jsonl.gz")
JSON_PATH = Path("resources/source_language_absence_profiles.json")
SUMMARY_PATH = Path("resources/source_language_absence_profile_summary.tsv")

FIELDS = [
    "Original",
    "Editado",
    "Traducción",
    "Traducción (es)",
    "Comentario",
    "Comentario (es)",
    "Comentario_wimmer_plus_html",
]
PUBLIC_TEXT_FIELDS = [
    "Traducción",
    "Traducción (es)",
    "Comentario",
    "Comentario (es)",
    "Comentario_wimmer_plus_html",
]
LANGUAGES = ["nahuatl", "spanish", "french", "latin", "english", "greek"]
DEFAULT_MAX_CHARS_PER_CELL = 6000
SUMMARY_FIELDS = [
    "source",
    "field",
    "rows",
    "filled_rows",
    "coverage",
    "likely_present",
    "likely_absent",
    "p_present_nahuatl",
    "p_not_nahuatl",
    "p_present_spanish",
    "p_not_spanish",
    "p_present_french",
    "p_not_french",
    "p_present_latin",
    "p_not_latin",
    "p_present_english",
    "p_not_english",
    "p_present_greek",
    "p_not_greek",
    "top_evidence",
]

BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
BOLD_RE = re.compile(r"<b\b[^>]*>(.*?)</b>", re.I | re.S)
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿĀĒĪŌŪȲāēīōūȳÂÊÎÔÛâêîôûĀ́ā́ḖḗĪ́ī́ṒṓŪ́ū́']+")
GREEK_RE = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")
LATIN_ENDING_RE = re.compile(
    r".{5,}(?:abilis|ibilis|ensis|ibus|orum|arum|atum|itas|tatis|tionis|ium|ius|um|us|is|ae|am|em|e)$"
)


def fold_token(value: str) -> str:
    value = value.replace("ꞌ", "'").replace("’", "'").strip().lower()
    decomposed = unicodedata.normalize("NFKD", value)
    folded = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z']", "", folded)


def normalize_set(words: Iterable[str]) -> set[str]:
    return {fold_token(word) for word in words}


NAHUATL_STRONG = normalize_set(
    """
    achto amo anca auh ca cenca huel huan ihuan in inic ipan itech itic
    itoca izca ma macamo moch mochipa niman no oc oncan quen quenin quin
    quim zan ye yeh yhuan yn
    """.split()
)
SPANISH_STRONG = normalize_set(
    """
    acerca adelante adelgazar ahora algo alguien alguna alguno ante antes
    aquel aquella aquello aqui arriba asi aunque cada camino ciudad como
    cosa cuando cuerpo debajo decir delgado despues dios donde efecto el
    entre era eran esta estaba estan estar este estos fiesta gloria gran
    hacer hacia hijo hombre iglesia luego madre manera menos mujer ninguno
    nombre otro padre para parte persona poco porque pueblo que quiere real
    sacramento santa santo senor ser si sobre son suele tierra todo todos
    traducido viejo
    """.split()
)
SPANISH_WEAK = normalize_set(
    """
    al de del el ella en es la las le les lo los ni no o por se su sus un
    una unas unos y
    """.split()
)
FRENCH_STRONG = normalize_set(
    """
    ajoute ancien aussi avec comme dans dire dit etre fait forme homme lequel
    laquelle lequel leurs meme mince objet parce personne
    peut plume plumes pour quelque quelqu repousser rejeter sur tertre vieux
    voir
    """.split()
)
FRENCH_WEAK = normalize_set(
    """
    au aux ce ces de des du en et la le les ou par que qui se son un une
    """.split()
)
ENGLISH_STRONG = normalize_set(
    """
    according artificial ball balls be become called cloth enter feather
    feathers fine form hillock made mound old one shape soaked strips the
    thin turkey water who with
    """.split()
)
ENGLISH_WEAK = normalize_set(
    """
    a an and as by for from in into is it of on or that this to
    """.split()
)
LATIN_STRONG = normalize_set(
    """
    abominabilis accusativus dativus genitivus gracilis indicativus linteolum
    linteum mantile nominativus onis orarium participium pluralis scil
    singularis subtilis talio tenuis vel
    """.split()
)
LATIN_WEAK = normalize_set(
    """
    cum et hoc id ille ipsa ipse per qui quae quod quo
    """.split()
)
GREEK_STRONG = normalize_set(
    """
    griego griega grec greek
    """.split()
)

NAHUATL_DENY = normalize_set(
    """
    adelgazar algo alguien alguna alguno como cosa cuando decir delgado dios
    donde hecho hombre madre manera mujer padre para parte persona porque
    pueblo quiere senor viejo
    """.split()
)
NAHUATL_HINT_FRAGMENTS = (
    "tl",
    "tz",
    "hu",
    "auh",
    "ihua",
    "yhua",
    "tzin",
    "xoch",
    "cuauh",
    "quauh",
    "nahu",
    "mexi",
    "tenoch",
    "atl",
    "yotl",
    "tepec",
    "tlan",
    "coatl",
    "chih",
    "calli",
    "tocht",
    "cuitl",
    "yoll",
)

LANGUAGE_STRONG_WORDS = {
    "nahuatl": NAHUATL_STRONG,
    "spanish": SPANISH_STRONG,
    "french": FRENCH_STRONG,
    "latin": LATIN_STRONG,
    "english": ENGLISH_STRONG,
    "greek": GREEK_STRONG,
}
LANGUAGE_WEAK_WORDS = {
    "spanish": SPANISH_WEAK,
}

# Schema/source priors are intentionally modest except for Original/Editado:
# those two fields are Nahuatl lexeme fields and many values are too short for
# lexical detection. Translation/comment priors only encode known field layout.
FIELD_PRIORS: dict[str, dict[str, float]] = {
    "Original": {"nahuatl": 12.0},
    "Editado": {"nahuatl": 12.0},
    "Traducción (es)": {"spanish": 6.0},
    "Comentario (es)": {"spanish": 3.0},
}
SOURCE_FIELD_PRIORS: dict[tuple[str, str], dict[str, float]] = {
    ("1992 Karttunen", "Traducción"): {"english": 8.0, "spanish": -2.0},
    ("1992 Karttunen", "Comentario"): {"english": 5.0, "nahuatl": 1.2, "spanish": -2.0},
    ("2021 Wimmer", "Traducción"): {"french": 8.0, "spanish": -2.0},
    ("2021 Wimmer", "Comentario"): {"french": 5.0, "nahuatl": 1.2, "english": 0.5, "spanish": -1.5},
    ("2021 Wimmer", "Traducción (es)"): {"spanish": 8.0, "french": -1.5},
    ("2021 Wimmer", "Comentario (es)"): {"spanish": 5.0, "nahuatl": 1.2, "english": 0.5, "french": -1.5},
    ("153? Trilingüe", "Comentario"): {"nahuatl": 1.5, "spanish": 1.5, "latin": 2.0},
    ("1580 CF Index", "Traducción"): {"nahuatl": -1.0, "spanish": -1.0, "french": -1.0, "latin": -1.0, "english": -1.0},
}
DEFAULT_TRANSLATION_PRIOR = {"spanish": 6.0}
DEFAULT_COMMENT_PRIOR = {"spanish": 2.5}


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub("\n", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def sample_for_detection(raw: str, max_chars: int) -> str:
    if len(raw) <= max_chars:
        return raw
    head = max_chars * 3 // 4
    tail = max_chars - head
    return f"{raw[:head]} {raw[-tail:]}"


def tokens(value: str) -> list[str]:
    folded = [fold_token(token) for token in TOKEN_RE.findall(value)]
    return [token for token in folded if token]


def looks_nahuatl(token: str) -> bool:
    if len(token) < 3 or token in NAHUATL_DENY:
        return False
    if token in NAHUATL_STRONG:
        return True
    return any(fragment in token for fragment in NAHUATL_HINT_FRAGMENTS)


def has_language_diacritic(language: str, raw_token: str) -> bool:
    if language == "spanish":
        return bool(re.search(r"[áéíóúñüÁÉÍÓÚÑÜ]", raw_token))
    if language == "french":
        return bool(re.search(r"[àâçéèêëîïôùûüÿœÀÂÇÉÈÊËÎÏÔÙÛÜŸŒ]", raw_token))
    return False


def add_score(
    scores: defaultdict[str, float],
    evidence: dict[str, Counter[str]],
    language: str,
    amount: float,
    marker: str,
) -> None:
    scores[language] += amount
    if amount > 0:
        evidence[language][marker] += 1


def apply_priors(source: str, field: str, scores: defaultdict[str, float], evidence: dict[str, Counter[str]]) -> None:
    priors: dict[str, float] = {}
    if field == "Traducción":
        priors.update(DEFAULT_TRANSLATION_PRIOR)
    elif field == "Comentario":
        priors.update(DEFAULT_COMMENT_PRIOR)
    priors.update(FIELD_PRIORS.get(field, {}))
    priors.update(SOURCE_FIELD_PRIORS.get((source, field), {}))
    for language, amount in priors.items():
        scores[language] += amount
        if amount > 0:
            evidence[language][f"prior:{field}"] += 1


def score_cell(
    source: str,
    field: str,
    value: object,
    *,
    max_chars: int,
) -> tuple[dict[str, float], dict[str, Counter[str]], int]:
    raw = str(value or "")
    if not raw.strip():
        return {language: 0.0 for language in LANGUAGES}, {language: Counter() for language in LANGUAGES}, 0
    raw = sample_for_detection(raw, max_chars)
    text = clean_html(raw)
    if not text:
        return {language: 0.0 for language in LANGUAGES}, {language: Counter() for language in LANGUAGES}, 0

    scores: defaultdict[str, float] = defaultdict(float)
    evidence: dict[str, Counter[str]] = {language: Counter() for language in LANGUAGES}
    apply_priors(source, field, scores, evidence)

    raw_tokens = TOKEN_RE.findall(html.unescape(raw))
    folded_tokens = [fold_token(token) for token in raw_tokens]
    folded_tokens = [token for token in folded_tokens if token]

    if GREEK_RE.search(raw):
        add_score(scores, evidence, "greek", 5.0, "greek-script")

    lexical_languages = {"nahuatl"} if field in {"Original", "Editado"} else set(LANGUAGES)

    bold_text = " ".join(clean_html(match.group(1)) for match in BOLD_RE.finditer(raw))
    if field.startswith("Comentario") and bold_text:
        for token in tokens(bold_text):
            if looks_nahuatl(token):
                add_score(scores, evidence, "nahuatl", 0.9, token)

    for raw_token, token in zip(raw_tokens, folded_tokens):
        if len(token) < 2:
            continue
        if "nahuatl" in lexical_languages and looks_nahuatl(token):
            add_score(scores, evidence, "nahuatl", 0.65, token)
        for language, words in LANGUAGE_STRONG_WORDS.items():
            if language not in lexical_languages:
                continue
            if token in words:
                add_score(scores, evidence, language, 0.75, token)
        for language, words in LANGUAGE_WEAK_WORDS.items():
            if language not in lexical_languages:
                continue
            if token in words:
                add_score(scores, evidence, language, 0.28, token)
        if "spanish" in lexical_languages and has_language_diacritic("spanish", raw_token):
            add_score(scores, evidence, "spanish", 0.35, token)
        if "french" in lexical_languages and has_language_diacritic("french", raw_token):
            add_score(scores, evidence, "french", 0.35, token)
        if field == "Comentario" and source == "153? Trilingüe" and LATIN_ENDING_RE.match(token):
            add_score(scores, evidence, "latin", 0.4, token)

    probabilities = {
        language: round(max(0.0, min(0.995, 1.0 - math.exp(-max(0.0, scores[language]) / 4.0))), 4)
        for language in LANGUAGES
    }
    return probabilities, evidence, len(folded_tokens)


def iter_rows(path: Path) -> Iterable[dict[str, object]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def format_probability(value: float) -> str:
    return f"{value:.4f}"


def top_evidence(evidence: dict[str, Counter[str]], limit: int = 3) -> str:
    parts = []
    for language in LANGUAGES:
        tokens_for_language = [
            f"{token}={count}" for token, count in evidence[language].most_common(limit) if not token.startswith("prior:")
        ]
        if tokens_for_language:
            parts.append(f"{language}:{'|'.join(tokens_for_language)}")
    return "; ".join(parts)


def summarize_group(stats: dict[str, object]) -> dict[str, object]:
    row_count = int(stats["rows"])
    filled_count = int(stats["filled_rows"])
    presence_sum: Counter[str] = stats["presence_sum"]  # type: ignore[assignment]
    evidence: dict[str, Counter[str]] = stats["evidence"]  # type: ignore[assignment]
    if filled_count:
        present = {language: round(presence_sum[language] / filled_count, 4) for language in LANGUAGES}
    else:
        present = {language: 0.0 for language in LANGUAGES}
    absent_filled = {language: round(1.0 - present[language], 4) for language in LANGUAGES}
    absent_all = {
        language: round(1.0 - (presence_sum[language] / row_count if row_count else 0.0), 4) for language in LANGUAGES
    }
    likely_present = [language for language in LANGUAGES if present[language] >= 0.35]
    likely_absent = [language for language in LANGUAGES if absent_filled[language] >= 0.95]
    return {
        "rows": row_count,
        "filled_rows": filled_count,
        "coverage": round(filled_count / row_count, 4) if row_count else 0.0,
        "token_count": int(stats["token_count"]),
        "presence_probability": present,
        "absence_probability_filled": absent_filled,
        "absence_probability_all_rows": absent_all,
        "likely_present": likely_present,
        "likely_absent": likely_absent,
        "evidence": {
            language: {
                "top_tokens": evidence[language].most_common(12),
                "token_hits": sum(evidence[language].values()),
            }
            for language in LANGUAGES
        },
    }


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=SUMMARY_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in SUMMARY_FIELDS})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--json", type=Path, default=JSON_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument(
        "--max-chars-per-cell",
        type=int,
        default=DEFAULT_MAX_CHARS_PER_CELL,
        help="Sample this many characters from each cell for scoring; long cells use head+tail.",
    )
    args = parser.parse_args()

    groups: defaultdict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {
            "rows": 0,
            "filled_rows": 0,
            "token_count": 0,
            "presence_sum": Counter(),
            "evidence": {language: Counter() for language in LANGUAGES},
        }
    )
    source_rows: Counter[str] = Counter()

    for row in iter_rows(args.data):
        source = str(row.get("Fuente", ""))
        source_rows[source] += 1
        row_public_absence_product = {language: 1.0 for language in LANGUAGES}
        row_public_evidence = {language: Counter() for language in LANGUAGES}
        row_public_token_count = 0
        row_public_filled = False
        for field in FIELDS:
            group = groups[(source, field)]
            group["rows"] = int(group["rows"]) + 1
            value = row.get(field, "")
            probabilities, evidence, token_count = score_cell(source, field, value, max_chars=args.max_chars_per_cell)
            if str(value or "").strip():
                group["filled_rows"] = int(group["filled_rows"]) + 1
                group["token_count"] = int(group["token_count"]) + token_count
                presence_sum: Counter[str] = group["presence_sum"]  # type: ignore[assignment]
                group_evidence: dict[str, Counter[str]] = group["evidence"]  # type: ignore[assignment]
                for language in LANGUAGES:
                    presence_sum[language] += probabilities[language]
                    group_evidence[language].update(evidence[language])
                if field in PUBLIC_TEXT_FIELDS:
                    row_public_filled = True
                    row_public_token_count += token_count
                    for language in LANGUAGES:
                        row_public_absence_product[language] *= 1.0 - probabilities[language]
                        row_public_evidence[language].update(evidence[language])

        group = groups[(source, "all_public_text")]
        group["rows"] = int(group["rows"]) + 1
        if row_public_filled:
            group["filled_rows"] = int(group["filled_rows"]) + 1
            group["token_count"] = int(group["token_count"]) + row_public_token_count
            presence_sum = group["presence_sum"]  # type: ignore[assignment]
            group_evidence = group["evidence"]  # type: ignore[assignment]
            for language in LANGUAGES:
                presence_sum[language] += round(1.0 - row_public_absence_product[language], 4)
                group_evidence[language].update(row_public_evidence[language])

    sources: dict[str, object] = {}
    summary_rows: list[dict[str, object]] = []
    for source in sorted(source_rows):
        source_fields: dict[str, object] = {}
        for field in [*FIELDS, "all_public_text"]:
            summary = summarize_group(groups[(source, field)])
            source_fields[field] = summary
            row = {
                "source": source,
                "field": field,
                "rows": summary["rows"],
                "filled_rows": summary["filled_rows"],
                "coverage": format_probability(float(summary["coverage"])),
                "likely_present": ",".join(summary["likely_present"]),
                "likely_absent": ",".join(summary["likely_absent"]),
                "top_evidence": top_evidence(groups[(source, field)]["evidence"]),  # type: ignore[index]
            }
            for language in LANGUAGES:
                present = summary["presence_probability"][language]  # type: ignore[index]
                absent = summary["absence_probability_filled"][language]  # type: ignore[index]
                row[f"p_present_{language}"] = format_probability(float(present))
                row[f"p_not_{language}"] = format_probability(float(absent))
            summary_rows.append(row)
        sources[source] = {"rows": source_rows[source], "fields": source_fields}

    payload = {
        "metadata": {
            "data_path": str(args.data),
            "row_count": sum(source_rows.values()),
            "source_count": len(source_rows),
            "fields": FIELDS,
            "aggregate_field": "all_public_text",
            "languages": LANGUAGES,
            "max_chars_per_cell": args.max_chars_per_cell,
            "probability_note": (
                "Presence probabilities are independent per language and can both be high in mixed cells. "
                "absence_probability_filled is 1 - mean presence over filled cells; "
                "absence_probability_all_rows also counts blank cells as absent."
            ),
            "method": {
                "field_priors": FIELD_PRIORS,
                "source_field_priors": {f"{source}::{field}": priors for (source, field), priors in SOURCE_FIELD_PRIORS.items()},
                "default_translation_prior": DEFAULT_TRANSLATION_PRIOR,
                "default_comment_prior": DEFAULT_COMMENT_PRIOR,
                "lexical_detection": "weighted word lists, Nahuatl orthographic fragments, Greek script, and Trilingüe Latin endings",
            },
        },
        "sources": sources,
    }

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_tsv(args.summary, summary_rows)

    print(f"json {args.json}")
    print(f"summary {args.summary} rows={len(summary_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
