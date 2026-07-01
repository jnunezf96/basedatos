#!/usr/bin/env python3
"""Normalize Trilingue cedilla tokens that are paired with modern text.

For a public text fragment like "Alicaçe o zanja. > Alicaze o zanja.", this
uses the token printed after the arrow as the replacement. That avoids applying
a single c/z rule across Spanish, Latin, and Nahuatl contexts.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import itertools
import json
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/trilingue_153_paired_cedilla_proposals.tsv")
SUMMARY_PATH = Path("resources/trilingue_153_paired_cedilla_summary.json")
SOURCE = "153? Trilingüe"
RAW_FIELD = "Comentario_raw_153_trilingue_paired_cedilla"
MARKER = "visible_153_trilingue_paired_cedilla_oldwriting_2026_06_29"
QA_KEY = "qa_153_trilingue_paired_cedilla"

PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç]+")
CEDILLA_TOKEN_RE = re.compile(
    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç]*"
    r"[Çç]"
    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç]*"
)


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_marks(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", value.lower())
        if unicodedata.category(char) != "Mn"
    )


def cedilla_variants(token: str) -> list[str]:
    positions = [index for index, char in enumerate(token) if char in "çÇ"]
    if len(positions) > 3:
        return []
    variants: list[str] = []
    for replacements in itertools.product("cz", repeat=len(positions)):
        chars = list(token)
        for position, replacement in zip(positions, replacements):
            chars[position] = replacement.upper() if token[position] == "Ç" else replacement
        variants.append("".join(chars))
    return variants


def paired_replacements(value: object) -> dict[str, str]:
    text = clean_html(value)
    replacements: dict[str, str] = {}
    conflicts: set[str] = set()
    for match in CEDILLA_TOKEN_RE.finditer(text):
        old = match.group(0)
        tail = text[match.end() :]
        if ">" not in tail:
            continue
        paired_phrase = tail.split(">", 1)[1].split(">", 1)[0]
        modern_tokens = TOKEN_RE.findall(paired_phrase)
        modern_by_key = {strip_marks(token): token for token in modern_tokens}
        matches: list[str] = []
        for variant in cedilla_variants(old):
            modern = modern_by_key.get(strip_marks(variant))
            if modern and modern not in matches:
                matches.append(modern)
        if len(matches) != 1 or matches[0] == old:
            continue
        if old in replacements and replacements[old] != matches[0]:
            conflicts.add(old)
            continue
        replacements[old] = matches[0]
    for old in conflicts:
        replacements.pop(old, None)
    return replacements


def normalize_value(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    replacements = paired_replacements(text)
    if not replacements:
        return text, []
    changes: list[tuple[str, str]] = []
    pattern = re.compile(
        r"(?<![\w-])("
        + "|".join(re.escape(token) for token in sorted(replacements, key=len, reverse=True))
        + r")(?![\w-])"
    )

    def repl(match: re.Match[str]) -> str:
        old = match.group(0)
        new = replacements[old]
        changes.append((old, new))
        return new

    return pattern.sub(repl, text), changes


def token_context(value: object, token: str, width: int = 140) -> str:
    text = clean_html(value)
    match = re.search(re.escape(token), text, re.I)
    if not match:
        return text[: width * 2].strip()
    left = max(0, match.start() - width)
    right = min(len(text), match.end() + width)
    return text[left:right].strip()


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


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
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    proposals: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        counts["source_rows"] += 1
        previous_commentary = row.get("Comentario", "")
        row_changes: list[tuple[str, str, str]] = []
        for field in PUBLIC_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value or "ç" not in value and "Ç" not in value:
                continue
            new_value, changes = normalize_value(value)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if args.apply:
                row[field] = new_value

        if not row_changes:
            continue

        counts["proposal_rows"] += 1
        counts["proposal_changes"] += len(row_changes)
        proposals.append(
            {
                "record_id": row.get("record_id", ""),
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "marker": MARKER,
                "old_tokens": " | ".join(f"{field}:{old}" for field, old, _ in row_changes),
                "new_tokens": " | ".join(f"{field}:{new}" for field, _, new in row_changes),
                "context": token_context(row.get(row_changes[0][0], row.get("Comentario", "")), row_changes[0][1]),
            }
        )

        if args.apply:
            if RAW_FIELD not in row:
                row[RAW_FIELD] = previous_commentary
                counts["raw_preserved_rows"] += 1
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                QA_KEY: {
                    "action": "normalized_trilingue_cedilla_tokens_from_printed_modern_pair",
                    "marker": MARKER,
                    "raw_field": RAW_FIELD,
                    "raw_preserved": True,
                    "changed_token_count": len(row_changes),
                    "previous_commentary_sha1": hashlib.sha1(str(row.get(RAW_FIELD, "")).encode("utf-8")).hexdigest(),
                },
            }
            row["Sentence_Source_JSON"] = qa

    write_tsv(
        args.proposals,
        proposals,
        ["record_id", "original", "editado", "marker", "old_tokens", "new_tokens", "context"],
    )
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.apply and proposals:
        write_rows(args.data, rows)
        counts["applied_rows"] = len(proposals)
        args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"summary {dict(counts)}")
    print(f"proposals {args.proposals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
