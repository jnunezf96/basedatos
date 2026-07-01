#!/usr/bin/env python3
"""Normalize narrow old-Spanish residue in 1551-95 Documentos display."""

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
PROPOSALS_PATH = Path("resources/documentos_1551_oldspanish_proposals.tsv")
SUMMARY_PATH = Path("resources/documentos_1551_oldspanish_summary.json")
SOURCE = "1551-95 Documentos nahuas de la Ciudad de México"
RAW_FIELD = "Comentario_raw_1551_documentos_nahuas"
MARKER = "visible_spanish_1551_documentos_oldwriting_2026_06_29"
QA_KEY = "qa_1551_documentos_oldspanish"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
BOLD_RE = re.compile(r"(<b\b[^>]*>.*?</b>)", re.I | re.S)
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")

REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<![\w-])Jhoachin(?![\w-])", re.I), "Joaquín"),
    (re.compile(r"(?<![\w-])Juachin(?![\w-])", re.I), "Joaquín"),
    (re.compile(r"(?<![\w-])Joachin(?![\w-])", re.I), "Joaquín"),
    (re.compile(r"(?<![\w-])Jhoana(?![\w-])", re.I), "Juana"),
    (re.compile(r"(?<![\w-])Joana(?![\w-])", re.I), "Juana"),
    (re.compile(r"(?<![\w-])Jhoan(?![\w-])", re.I), "Juan"),
    (re.compile(r"(?<![\w-])Joan(?![\w-])", re.I), "Juan"),
    (re.compile(r"(?<![\w-])Joarez(?![\w-])", re.I), "Juárez"),
    (re.compile(r"(?<![\w-])abló(?![\w-])", re.I), "habló"),
    (re.compile(r"(?<![\w-])ques(?![\w-])", re.I), "que es"),
    (re.compile(r"(?<![\w-])ylustre(?![\w-])", re.I), "ilustre"),
    (re.compile(r"(?<![\w-])yglesias(?![\w-])", re.I), "iglesias"),
    (re.compile(r"(?<![\w-])yglesia(?![\w-])", re.I), "iglesia"),
    (re.compile(r"(?<![\w-])quartas(?![\w-])", re.I), "cuartas"),
    (re.compile(r"(?<![\w-])quarta(?![\w-])", re.I), "cuarta"),
    (re.compile(r"(?<![\w-])otubre(?![\w-])", re.I), "octubre"),
    (re.compile(r"(?<![\w-])dies(?![\w-])", re.I), "diez"),
]
INLINE_SAFE_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<![\w-])otubre(?![\w-])", re.I), "octubre"),
    (re.compile(r"(?<![\w-])dies(?![\w-])", re.I), "diez"),
]


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


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


def apply_case(old: str, new: str) -> str:
    letters = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóú]", "", old)
    if letters.isupper():
        return new.upper()
    if old[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def normalize_piece(piece: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []
    for pattern, replacement in REPLACEMENTS:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            new = apply_case(old, replacement)
            changes.append((old, new))
            return new

        piece = pattern.sub(repl, piece)
    return piece, changes


def normalize_outside_bold(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    pieces: list[str] = []
    changes: list[tuple[str, str]] = []
    last = 0

    for match in BOLD_RE.finditer(text):
        piece, piece_changes = normalize_piece(text[last : match.start()])
        pieces.append(piece)
        pieces.append(match.group(0))
        changes.extend(piece_changes)
        last = match.end()
    piece, piece_changes = normalize_piece(text[last:])
    pieces.append(piece)
    changes.extend(piece_changes)
    return "".join(pieces), changes


def normalize_inline_safe(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str]] = []
    for pattern, replacement in INLINE_SAFE_REPLACEMENTS:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            new = apply_case(old, replacement)
            changes.append((old, new))
            return new

        text = pattern.sub(repl, text)
    return text, changes


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
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    proposals: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        counts["source_rows"] += 1
        if args.apply and RAW_FIELD not in row:
            row[RAW_FIELD] = row.get("Comentario", "")
            counts["raw_preserved_rows"] += 1

        row_changes: list[tuple[str, str, str]] = []
        for field in COMMENTARY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_outside_bold(value)
            new_value, inline_changes = normalize_inline_safe(new_value)
            changes.extend(inline_changes)
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
                "context": token_context(row.get("Comentario", ""), row_changes[0][1]),
            }
        )
        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                QA_KEY: {
                    "action": "normalized_narrow_old_spanish_forms_in_public_commentary",
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
