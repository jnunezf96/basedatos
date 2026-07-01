#!/usr/bin/env python3
"""Expand visible Spanish abbreviations in 1629 Alarcon public fields."""

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
PROPOSALS_PATH = Path("resources/alarcon_1629_spanish_abbreviation_proposals.tsv")
SUMMARY_PATH = Path("resources/alarcon_1629_spanish_abbreviation_summary.json")
SOURCE = "1629 Alarcón"
MARKER = "visible_spanish_1629_alarcon_abbreviation_expansion_2026_06_29"
QA_KEY = "qa_1629_alarcon_spanish_abbreviation_expansion"

PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELDS = {
    "Traducción": "Traducción_raw_1629_alarcon_spanish_abbreviations",
    "Traducción (es)": "Traducción_es_raw_1629_alarcon_spanish_abbreviations",
    "Comentario": "Comentario_raw_1629_alarcon_spanish_abbreviations",
    "Comentario (es)": "Comentario_es_raw_1629_alarcon_spanish_abbreviations",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_1629_alarcon_spanish_abbreviations",
}

BOLD_RE = re.compile(r"(<b\b[^>]*>.*?</b>)", re.I | re.S)
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
QD_RE = re.compile(r"\bq\.\s*d\.", re.I)
VGR_RE = re.compile(r"\bv\.\s*gr\.", re.I)
EXACT_REPLACEMENTS = {
    "DICEN OC HUETZTOC, Q. D. AUN ESTARA ACOSTADO": "DICEN OC HUETZTOC, QUIERE DECIR AUN ESTARA ACOSTADO",
}


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


def qd_replacement_for(old: str) -> str:
    letters = re.sub(r"[^A-Za-z]", "", old)
    if letters.isupper():
        return "QUIERE DECIR"
    if old[:1].isupper():
        return "Quiere decir"
    return "quiere decir"


def vgr_replacement_for(old: str) -> str:
    letters = re.sub(r"[^A-Za-z]", "", old)
    if letters.isupper():
        return "VERBIGRACIA"
    if old[:1].isupper():
        return "Verbigracia"
    return "verbigracia"


def normalize_piece(piece: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def qd_repl(match: re.Match[str]) -> str:
        old = match.group(0)
        new = qd_replacement_for(old)
        changes.append((old, new))
        return new

    def vgr_repl(match: re.Match[str]) -> str:
        old = match.group(0)
        new = vgr_replacement_for(old)
        changes.append((old, new))
        return new

    piece = QD_RE.sub(qd_repl, piece)
    piece = VGR_RE.sub(vgr_repl, piece)
    return piece, changes


def normalize_outside_bold(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    pieces: list[str] = []
    changes: list[tuple[str, str]] = []
    for old, new in EXACT_REPLACEMENTS.items():
        count = text.count(old)
        if not count:
            continue
        text = text.replace(old, new)
        changes.extend((old, new) for _ in range(count))
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
        row_changes: list[tuple[str, str, str]] = []
        raw_preserved_fields: list[str] = []

        for field in PUBLIC_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_outside_bold(value)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if args.apply:
                raw_field = RAW_FIELDS[field]
                if raw_field not in row:
                    row[raw_field] = value
                    raw_preserved_fields.append(raw_field)
                    counts["raw_preserved_fields"] += 1
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
                "context": token_context(row.get(row_changes[0][0], ""), row_changes[0][1]),
            }
        )

        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                QA_KEY: {
                    "action": "expanded_visible_spanish_q_d_abbreviation",
                    "marker": MARKER,
                    "raw_fields_preserved": raw_preserved_fields,
                    "changed_token_count": len(row_changes),
                    "previous_public_field_sha1": hashlib.sha1(
                        "||".join(str(row.get(raw_field, "")) for raw_field in raw_preserved_fields).encode("utf-8")
                    ).hexdigest(),
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
