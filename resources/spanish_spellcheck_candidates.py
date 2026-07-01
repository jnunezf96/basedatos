#!/usr/bin/env python3
"""Find Spanish spellcheck candidates in the Nahuatl database.

This audit is intentionally narrow. It flags likely Spanish/OCR residue
patterns in public display fields while avoiding raw preserved source fields by
default. Use --review-hats when you also want a broad, neutral review list of
remaining circumflex-bearing tokens.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


DEFAULT_DATA_PATH = Path("data/data.jsonl.gz")
PUBLIC_FIELDS = [
    "Traducción",
    "Traducción (es)",
    "Comentario",
    "Comentario (es)",
    "Comentario_wimmer_plus_html",
]
SPANISH_SIDE_ONLY_SOURCES = {"2021 Wimmer"}
SPANISH_SIDE_FIELDS = ["Traducción (es)", "Comentario (es)"]
RAW_FIELDS = ["Comentario_raw_1565_sahagun_escolios"]
APPARATUS_RESIDUE_SOURCES = {"153? Trilingüe"}

SPANISH_RESIDUE_FIXES = {
    "cô": "con",
    "cuâdo": "cuando",
    "mâchada": "manchada",
    "nîgun": "ningún",
    "delâte": "delante",
    "ordenadamête": "ordenadamente",
    "mâdar": "mandar",
    "êfermedad": "enfermedad",
    "ratô": "ratón",
    "nôbre": "nombre",
    "vâdea": "bandea",
    "câtaro": "cántaro",
}

CONTEXTUAL_RESIDUE_FIXES = [
    (
        "être",
        "entre",
        re.compile(r"\bconferir\s+être\s+si\b", re.I),
    ),
]

PHRASE_FIXES = {
    "vadea y favorece": "bandea y favorece",
}

FOREIGN_RESIDUES = {
    "être": "French form; review as foreign-language residue, not Spanish entre.",
}
HAT_REVIEW_HINT = "review: long vowel, reduplication, or n/m expansion"

TAG_RE = re.compile(r"<[^>]+>")
ITALIC_RE = re.compile(r"<i\b[^>]*>.*?</i>", re.I | re.S)
HAT_TOKEN_RE = re.compile(r"\b[\wâêîôÂÊÎÔ]*[âêîôÂÊÎÔ][\wâêîôÂÊÎÔ]*\b")


def clean_text(value: str, *, include_italic: bool) -> str:
    text = html.unescape(value)
    if not include_italic:
        text = ITALIC_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def context(text: str, start: int, end: int, width: int = 80) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    return text[left:right].strip()


def word_pattern(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])", re.I)


def iter_rows(path: Path) -> Iterable[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_candidates(
    row: dict,
    *,
    fields: list[str],
    include_italic: bool,
    include_review_only: bool,
    review_hats: bool,
) -> Iterable[dict[str, str]]:
    source = row.get("Fuente", "")
    record_id = row.get("record_id", "")
    original = row.get("Original", "")

    for field in fields:
        value = row.get(field, "")
        if not isinstance(value, str) or not value:
            continue
        text = clean_text(value, include_italic=include_italic)

        for term, suggestion in SPANISH_RESIDUE_FIXES.items():
            for match in word_pattern(term).finditer(text):
                if source in APPARATUS_RESIDUE_SOURCES:
                    if not include_review_only:
                        continue
                    yield {
                        "kind": "latin_or_source_apparatus_residue",
                        "source": source,
                        "record_id": record_id,
                        "field": field,
                        "original": original,
                        "token": match.group(0),
                        "suggestion": "review only: source/Latin apparatus",
                        "context": context(text, match.start(), match.end()),
                    }
                    continue
                yield {
                    "kind": "spanish_circumflex_residue",
                    "source": source,
                    "record_id": record_id,
                    "field": field,
                    "original": original,
                    "token": match.group(0),
                    "suggestion": suggestion,
                    "context": context(text, match.start(), match.end()),
                }

        for term, suggestion, context_re in CONTEXTUAL_RESIDUE_FIXES:
            for match in word_pattern(term).finditer(text):
                snippet = context(text, match.start(), match.end())
                if not context_re.search(snippet):
                    continue
                yield {
                    "kind": "spanish_contextual_residue",
                    "source": source,
                    "record_id": record_id,
                    "field": field,
                    "original": original,
                    "token": match.group(0),
                    "suggestion": suggestion,
                    "context": snippet,
                }

        for phrase, suggestion in PHRASE_FIXES.items():
            for match in re.finditer(re.escape(phrase), text, re.I):
                yield {
                    "kind": "spanish_phrase_sync",
                    "source": source,
                    "record_id": record_id,
                    "field": field,
                    "original": original,
                    "token": match.group(0),
                    "suggestion": suggestion,
                    "context": context(text, match.start(), match.end()),
                }

        for term, hint in FOREIGN_RESIDUES.items():
            for match in word_pattern(term).finditer(text):
                snippet = context(text, match.start(), match.end())
                if any(context_re.search(snippet) for _, _, context_re in CONTEXTUAL_RESIDUE_FIXES):
                    continue
                if not include_review_only:
                    continue
                yield {
                    "kind": "foreign_residue_in_spanish_spellcheck",
                    "source": source,
                    "record_id": record_id,
                    "field": field,
                    "original": original,
                    "token": match.group(0),
                    "suggestion": hint,
                    "context": snippet,
                }

        if review_hats:
            for match in HAT_TOKEN_RE.finditer(text):
                token = match.group(0)
                if token.lower() in SPANISH_RESIDUE_FIXES:
                    continue
                yield {
                    "kind": "review_circumflex_token",
                    "source": source,
                    "record_id": record_id,
                    "field": field,
                    "original": original,
                    "token": token,
                    "suggestion": HAT_REVIEW_HINT,
                    "context": context(text, match.start(), match.end()),
                }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--source", action="append", help="Limit to a Fuente value. Repeatable.")
    parser.add_argument("--include-raw", action="store_true", help="Also scan preserved raw fields.")
    parser.add_argument("--include-italic", action="store_true", help="Do not remove italic witness text before scanning.")
    parser.add_argument("--include-review-only", action="store_true", help="Also emit known non-actionable source-apparatus and foreign-language review rows.")
    parser.add_argument("--all-public-fields", action="store_true", help="Scan primary fields even for sources with separate Spanish-side fields.")
    parser.add_argument("--review-hats", action="store_true", help="Also output non-exact circumflex tokens for manual review.")
    parser.add_argument("--summary", action="store_true", help="Print counts to stderr.")
    parser.add_argument("--summary-only", action="store_true", help="Print counts without TSV rows.")
    parser.add_argument("--output", type=Path, help="Write TSV rows to this path instead of stdout.")
    args = parser.parse_args()

    allowed_sources = set(args.source or [])

    writer = None
    if not args.summary_only:
        output_handle = args.output.open("w", encoding="utf-8", newline="") if args.output else sys.stdout
        writer = csv.DictWriter(
            output_handle,
            fieldnames=["kind", "source", "record_id", "field", "original", "token", "suggestion", "context"],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()

    counts: Counter[str] = Counter()
    for row in iter_rows(args.data):
        if allowed_sources and row.get("Fuente") not in allowed_sources:
            continue
        if not args.all_public_fields and row.get("Fuente") in SPANISH_SIDE_ONLY_SOURCES:
            fields = list(SPANISH_SIDE_FIELDS)
        else:
            fields = list(PUBLIC_FIELDS)
        if args.include_raw:
            fields.extend(RAW_FIELDS)
        for candidate in iter_candidates(
            row,
            fields=fields,
            include_italic=args.include_italic,
            include_review_only=args.include_review_only,
            review_hats=args.review_hats,
        ):
            counts[candidate["kind"]] += 1
            if writer:
                writer.writerow(candidate)

    if args.summary or args.summary_only:
        for kind, count in counts.most_common():
            print(f"{kind}: {count}", file=sys.stderr)
        if not counts:
            print("No candidates found.", file=sys.stderr)
    if writer and args.output:
        output_handle.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
