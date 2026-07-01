#!/usr/bin/env python3
"""Normalize old-source Comentario j used as vowel i."""

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
from pathlib import Path
from typing import Any


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/commentary_j_vowel_i_proposals.tsv")
SUMMARY_PATH = Path("resources/commentary_j_vowel_i_summary.json")
MARKER = "visible_commentary_j_vowel_i_2026_06_30"
QA_KEY = "qa_commentary_j_vowel_i"

DISPLAY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_BY_FIELD = {
    "Comentario": "Comentario_public_raw_j_vowel_i",
    "Comentario (es)": "Comentario_es_raw_j_vowel_i",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_j_vowel_i",
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
    "1645 Carochi",
    "1692 Guerra",
    "1759 Paredes",
    "1780 ? Bnf_361",
    "1780 Clavijero",
    "17?? Bnf_362",
    "17?? Bnf_362bis",
}

WORD_RE = re.compile(
    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñÂÊÎÔÛâêîôûĀĒĪŌŪāēīōūÀÈÌÒÙàèìòùÄËÏÖÜäëïöüÃÕãõÇç]+"
)
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
FALSE_WORDS = {
    "ij",
    "je",
    "conj",
    "conj.",
    "ajo",
    "jaca",
    "ja",
    "juan",
    "juana",
}
SHORT_NAHUATL_SOURCE_WORDS = {"jc", "jn", "juh"}
MAYNEZ_SOURCE = "1580 Sahagún/Máynez"
MAYNEZ_EXACT_REPLACEMENTS = {
    "chalchiujtes": "chalchihuites",
    "cujtlacoch": "cuitlacoch",
    "cujtlacococh": "cuitlacococh",
    "cujtlachueue": "cuitlachhuehue",
    "cujtltaoac": "cuitlahuac",
    "exprimjr": "exprimir",
    "famjlias": "familias",
    "hormjga": "hormiga",
    "macujlsuchitl": "macuilxochitl",
    "mimjscoa": "mimixcoa",
    "mjctlantecutli": "mictlantecutli",
    "mjltomate": "miltomate",
    "mjltomates": "miltomates",
    "mjxtecas": "mixtecas",
    "pardjllo": "pardillo",
    "quijpiiac": "quipiyac",
    "rujdo": "ruido",
    "tiangujz": "tianguiz",
    "totolcujtlatzaputl": "totolcuitlatzapotl",
    "totolcujtltzapocuahuitl": "totolcuitlatzapocuahuitl",
    "uitzocujtlapilxiujtl": "huitzocuitlapilxihuitl",
    "xoxoujc": "xoxohuic",
    "ylhujcoatl": "ilhuicoatl",
    "yztaquijlitl": "iztaquilitl",
}
FALSE_PREFIXES = (
    "jur",
    "jus",
    "jue",
    "juz",
)
FALSE_SUBSTRINGS = (
    "justicia",
    "juramento",
    "jurament",
)

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


def build_editado_lexicon(rows: list[dict[str, Any]]) -> dict[str, Counter[str]]:
    lexicon: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        for word in WORD_RE.findall(str(row.get("Editado") or "")):
            lexicon[fold(word)][word] += 1
    return dict(lexicon)


def looks_like_false_positive(word: str) -> bool:
    folded = fold(word)
    if len(folded) < 2:
        return True
    if folded in FALSE_WORDS:
        return True
    if folded.startswith(FALSE_PREFIXES):
        return True
    if any(part in folded for part in FALSE_SUBSTRINGS):
        return True
    return False


def normalize_initial_qua(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.isupper():
            return "CUA"
        if token[:1].isupper():
            return "Cua"
        return "cua"

    return re.sub(r"^qua", repl, value, count=1, flags=re.I)


def source_specific_j_candidate(word: str, source: str) -> str | None:
    if source != MAYNEZ_SOURCE:
        return None
    exact = MAYNEZ_EXACT_REPLACEMENTS.get(fold(word))
    if exact:
        return case_like(word, exact)
    if "quj" not in fold(word):
        return None
    candidate = word.replace("j", "i").replace("J", "I")
    candidate = (
        candidate
        .replace("quii", "qui")
        .replace("Quii", "Qui")
        .replace("QUII", "QUI")
    )
    candidate = normalize_initial_qua(candidate)
    return candidate if candidate != word else None


def maynez_old_j_variants(word: str) -> set[str]:
    """Generate Maynez source-spelling variants for j used as i/h."""

    replacements = [
        (r"^suchimjlco$", "xochimilco"),
        (r"^suchmjlco$", "xochimilco"),
        (r"^sochimjlco$", "xochimilco"),
        (r"^sochmjlco$", "xochimilco"),
        (r"^xuchmjlco$", "xochimilco"),
        (r"^xochmjlco$", "xochimilco"),
        (r"aujtz", "ahuitz"),
        (r"hujtz", "huitz"),
        (r"ujtli", "uhtli"),
        (r"ujtl", "uhtl"),
        (r"iujtl", "ihuitl"),
        (r"ujtz", "uitz"),
        (r"cujtl", "cuitl"),
        (r"cujl", "cuil"),
        (r"mjs", "miz"),
        (r"mjx", "mix"),
        (r"mjl", "mil"),
        (r"huj", "hui"),
        (r"guj", "gui"),
        (r"ujz", "uiz"),
        (r"j", "i"),
        (r"j", "h"),
        (r"^ia", "ya"),
        (r"teu", "teo"),
        (r"aoa", "ahua"),
        (r"oaian$", "huayan"),
        (r"oaia$", "huaya"),
        (r"oac$", "huac"),
        (r"oa(?=[bcdfghklmnpqrstvwxyz])", "hua"),
    ]
    variants = {word}
    for _ in range(4):
        changed = False
        for current in list(variants):
            for pattern, replacement in replacements:
                candidate = re.sub(pattern, replacement, current, flags=re.I)
                if candidate != current and candidate not in variants:
                    variants.add(candidate)
                    changed = True
        if not changed:
            break
    variants.discard(word)
    return variants


def j_to_i_candidate(word: str, lexicon: dict[str, Counter[str]], source: str) -> str | None:
    if "j" not in word.lower() or looks_like_false_positive(word):
        return None
    source_candidate = source_specific_j_candidate(word, source)
    if source_candidate:
        return source_candidate
    folded = fold(word)
    if folded in SHORT_NAHUATL_SOURCE_WORDS:
        if source != "1565 Sahagún Escolios":
            return None
    elif len(folded) <= 3:
        return None
    candidate = word.replace("j", "i").replace("J", "I")
    if fold(candidate) == fold(word):
        return None
    key = fold(candidate)
    if key not in lexicon:
        if source != MAYNEZ_SOURCE:
            return None
        candidates: list[tuple[int, str]] = []
        for variant in maynez_old_j_variants(word):
            variant_key = fold(variant)
            if variant_key == fold(word) or variant_key not in lexicon:
                continue
            normalized, count = lexicon[variant_key].most_common(1)[0]
            candidates.append((count, normalized))
        if not candidates:
            return None
        normalized = sorted(candidates, key=lambda item: (-item[0], item[1]))[0][1]
        return case_like(word, normalized)
    normalized = lexicon[key].most_common(1)[0][0]
    return case_like(word, normalized)


def build_replacements(value: str, lexicon: dict[str, Counter[str]], source: str) -> dict[str, str]:
    replacements: dict[str, str] = {}
    for match in WORD_RE.finditer(value):
        word = match.group(0)
        replacement = j_to_i_candidate(word, lexicon, source)
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
            if not isinstance(value, str) or "j" not in value.lower():
                continue
            replacements = build_replacements(value, lexicon, source)
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
                "action": "normalized_commentary_j_used_as_vowel_i_against_editado_lexicon",
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
