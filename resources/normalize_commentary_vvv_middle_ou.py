#!/usr/bin/env python3
"""Normalize source-commentary V-o/u-V spellings against the Editado lexicon."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/commentary_vvv_middle_ou_proposals.tsv")
SUMMARY_PATH = Path("resources/commentary_vvv_middle_ou_summary.json")
MARKER = "visible_commentary_vvv_middle_ou_2026_06_30"
QA_KEY = "qa_commentary_vvv_middle_ou"

DISPLAY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_BY_FIELD = {
    "Comentario": "Comentario_public_raw_vvv_middle_ou",
    "Comentario (es)": "Comentario_es_raw_vvv_middle_ou",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_vvv_middle_ou",
}
TARGET_SOURCES = {
    "153? Trilingüe",
    "1547 Olmos_G",
    "1551-95 Documentos nahuas de la Ciudad de México",
    "1565 Sahagún Escolios",
    "1571 Molina 2",
    "1579 Durán",
    "1580 Sahagún/Máynez",
    "1598 Tezozomoc",
    "1611 Arenas",
    "1629 Alarcón",
    "1759 Paredes",
    "1780 ? Bnf_361",
    "1780 Clavijero",
    "17?? Bnf_362",
    "17?? Bnf_362bis",
}

VOWELS = set("aeiouáéíóúâêîôûāēīōūàèìòùäëïöüãõ")
MIDDLE_VOWELS = {"o", "u"}
WORD_RE = re.compile(
    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñÂÊÎÔÛâêîôûĀĒĪŌŪāēīōūÀÈÌÒÙàèìòùÄËÏÖÜäëïöüÃÕãõÇç]+"
)
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
FALSE_SHORT_TOKENS = {
    "aui",
    "iui",
    "eui",
    "eua",
    "oui",
    "aua",
    "aue",
    "auo",
    "uui",
    "iuu",
    "ioo",
}
FALSE_WORDS = {
    "teteoe",
}
FALSE_PREFIXES = {
    "teo",
    "teō",
}

PROPOSAL_FIELDS = [
    "source",
    "record_id",
    "field",
    "original",
    "editado",
    "old_tokens",
    "new_tokens",
    "context",
]


def fold(value: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", value.lower())
        if unicodedata.category(ch) != "Mn"
    )


def has_target_triplet(word: str) -> bool:
    chars = list(word)
    for i, ch in enumerate(chars):
        if i == 0 or i == len(chars) - 1:
            continue
        if fold(ch) in MIDDLE_VOWELS and fold(chars[i - 1]) in VOWELS and fold(chars[i + 1]) in VOWELS:
            return True
    return False


def case_like(source: str, target: str) -> str:
    if source.isupper():
        return target.upper()
    if source[:1].isupper():
        return target[:1].upper() + target[1:]
    return target


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: object, token: str, width: int = 170) -> str:
    text = clean_html(value)
    index = fold(text).find(fold(token))
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


def append_issue(value: object, marker: str) -> object:
    if isinstance(value, list):
        return value if marker in value else [*value, marker]
    return append_marker(value, marker)


def build_editado_lexicon(rows: list[dict[str, Any]]) -> dict[str, Counter[str]]:
    lexicon: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        for word in WORD_RE.findall(str(row.get("Editado") or "")):
            lexicon[fold(word)][word] += 1
    return dict(lexicon)


def replacement_positions(word: str) -> list[int]:
    chars = list(word)
    positions: list[int] = []
    for i, ch in enumerate(chars):
        if i == 0 or i == len(chars) - 1:
            continue
        if fold(ch) in MIDDLE_VOWELS and fold(chars[i - 1]) in VOWELS and fold(chars[i + 1]) in VOWELS:
            positions.append(i)
    return positions


def transform_variants(word: str) -> set[str]:
    positions = replacement_positions(word)
    variants: set[str] = set()
    for count in range(1, min(len(positions), 3) + 1):
        for selected in combinations(positions, count):
            parts: list[str] = []
            for i, ch in enumerate(word):
                parts.append("hu" if i in selected else ch)
            base = "".join(parts)
            variants.add(base)
            variants.add(re.sub(r"(?i)qu(?=[aáâāàäãouóúôûōūòùöüõ])", "cu", base))
            variants.update(
                re.sub(r"(?i)^u(?=[aeiouáéíóúâêîôûāēīōūàèìòùäëïöüãõ])", "hu", item)
                for item in list(variants)
            )
    return variants


def choose_replacement(word: str, lexicon: dict[str, Counter[str]]) -> str | None:
    if len(fold(word)) < 4 or fold(word) in FALSE_SHORT_TOKENS:
        return None
    folded = fold(word)
    if folded in FALSE_WORDS:
        return None
    if any(folded.startswith(prefix) for prefix in FALSE_PREFIXES):
        return None
    candidates: list[tuple[int, int, str]] = []
    for variant in transform_variants(word):
        key = fold(variant)
        if key == fold(word) or key not in lexicon:
            continue
        normalized, count = lexicon[key].most_common(1)[0]
        score = count
        if not fold(normalized).startswith("qu"):
            score += 10
        if "hu" in fold(normalized):
            score += 5
        candidates.append((score, count, normalized))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return case_like(word, candidates[0][2])


def build_replacements(value: str, lexicon: dict[str, Counter[str]]) -> dict[str, str]:
    replacements: dict[str, str] = {}
    for match in WORD_RE.finditer(value):
        word = match.group(0)
        if not has_target_triplet(word):
            continue
        replacement = choose_replacement(word, lexicon)
        if replacement and replacement != word:
            replacements[word] = replacement
    return replacements


def apply_replacements(value: str, replacements: dict[str, str]) -> tuple[str, list[tuple[str, str]]]:
    if not replacements:
        return value, []
    changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        replacement = replacements.get(word)
        if not replacement:
            return word
        changes.append((word, replacement))
        return replacement

    return WORD_RE.sub(repl, value), changes


def load_rows(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as handle:
        for row in rows:
            json.dump(row, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
    os.replace(tmp, path)


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=PROPOSAL_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in PROPOSAL_FIELDS})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = load_rows(args.data)
    lexicon = build_editado_lexicon(rows)
    summary: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    pair_counts: Counter[str] = Counter()
    proposals: list[dict[str, object]] = []

    for row in rows:
        source = row.get("Fuente", "")
        if source not in TARGET_SOURCES:
            continue
        summary["target_source_rows"] += 1
        row_changes: list[tuple[str, str, str]] = []
        for field in DISPLAY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            replacements = build_replacements(value, lexicon)
            if not replacements:
                continue
            new_value, changes = apply_replacements(value, replacements)
            if not changes or new_value == value:
                continue
            raw_field = RAW_FIELD_BY_FIELD[field]
            if args.apply and raw_field not in row:
                row[raw_field] = value
                summary["raw_preserved_fields"] += 1
            if args.apply:
                row[field] = new_value
            row_changes.extend((field, old, new) for old, new in changes)
            for old, new in changes:
                pair_counts[f"{old}>{new}"] += 1
            proposals.append(
                {
                    "source": source,
                    "record_id": row.get("record_id", ""),
                    "field": field,
                    "original": row.get("Original", ""),
                    "editado": row.get("Editado", ""),
                    "old_tokens": " | ".join(old for old, _new in changes[:12]),
                    "new_tokens": " | ".join(new for _old, new in changes[:12]),
                    "context": token_context(value, changes[0][0]),
                }
            )

        if not row_changes:
            continue
        source_counts[source] += 1
        summary["proposal_rows"] += 1
        summary["proposal_changes"] += len(row_changes)
        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_issue(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa[QA_KEY] = {
                "action": "normalized_commentary_vowel_o_u_vowel_spellings_against_editado_lexicon",
                "marker": MARKER,
                "raw_fields_preserved": sorted({RAW_FIELD_BY_FIELD[field] for field, _old, _new in row_changes}),
                "changed_token_count": len(row_changes),
                "previous_commentary_sha1": hashlib.sha1(str(row.get("Comentario", "")).encode("utf-8")).hexdigest(),
            }
            row["Sentence_Source_JSON"] = qa
            summary["applied_rows"] += 1

    write_tsv(args.proposals, proposals)
    summary_payload = {
        **summary,
        "rows_by_source": dict(source_counts.most_common()),
        "top_replacements": dict(pair_counts.most_common(100)),
    }
    args.summary.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.apply and proposals:
        write_rows(args.data, rows)

    print(f"summary {dict(summary)}")
    print(f"proposals {args.proposals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
