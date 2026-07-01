#!/usr/bin/env python3
"""Normalize context-supported residual cedilla forms in 1598 Tezozomoc."""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import os
import re
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/tezozomoc_1598_residual_cedilla_proposals.tsv")
SUMMARY_PATH = Path("resources/tezozomoc_1598_residual_cedilla_summary.json")
SOURCE = "1598 Tezozomoc"
MARKER = "visible_1598_tezozomoc_residual_cedilla_context_2026_06_30"
QA_KEY = "qa_1598_tezozomoc_residual_cedilla"

DISPLAY_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_BY_FIELD = {
    "Traducción": "Traduccion_raw_1598_tezozomoc_residual_cedilla",
    "Traducción (es)": "Traduccion_es_raw_1598_tezozomoc_residual_cedilla",
    "Comentario": "Comentario_raw_1598_tezozomoc_residual_cedilla",
    "Comentario (es)": "Comentario_es_raw_1598_tezozomoc_residual_cedilla",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_1598_tezozomoc_residual_cedilla",
}

BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")

REPLACEMENTS: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r"cesó el cançe de los mechuacanes"),
        "cesó el alcance de los mechuacanes",
        "cançe_contextual_alcance",
    ),
    (
        re.compile(r"entran\s*<small>\[106r=\]</small>\s*çado"),
        "entranzado",
        "page_split_entranzado",
    ),
]

PROPOSAL_FIELDS = ["source", "record_id", "original", "editado", "marker", "old_tokens", "new_tokens", "context"]


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def context_for(value: object, token: str, width: int = 170) -> str:
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


def normalize_value(value: object) -> tuple[str, list[tuple[str, str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str, str]] = []

    for pattern, replacement, label in REPLACEMENTS:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            changes.append((label, old, replacement))
            return replacement

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
    summary: Counter[str] = Counter()
    proposals: list[dict[str, object]] = []

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        summary["source_rows"] += 1
        row_changes: list[tuple[str, str, str, str]] = []
        for field in DISPLAY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            normalized, changes = normalize_value(value)
            if not changes:
                continue
            raw_field = RAW_FIELD_BY_FIELD[field]
            if raw_field not in row:
                row[raw_field] = value
                summary["raw_preserved_fields"] += 1
            row[field] = normalized
            row_changes.extend((field, label, old, new) for label, old, new in changes)

        if not row_changes:
            continue
        summary["proposal_rows"] += 1
        summary["proposal_changes"] += len(row_changes)
        if args.apply:
            row[QA_KEY] = append_marker(row.get(QA_KEY, ""), MARKER)
            summary["applied_rows"] += 1
        proposals.append(
            {
                "source": SOURCE,
                "record_id": row.get("record_id", ""),
                "original": clean_html(row.get("Original", "")),
                "editado": clean_html(row.get("Editado", "")),
                "marker": MARKER,
                "old_tokens": " | ".join(f"{field}:{old}" for field, _label, old, _new in row_changes),
                "new_tokens": " | ".join(f"{field}:{new}" for field, _label, _old, new in row_changes),
                "context": " || ".join(context_for(row.get(field, ""), new) for field, _label, _old, new in row_changes[:3]),
            }
        )

    write_tsv(args.proposals, proposals)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.apply and proposals:
        write_rows(args.data, rows)

    print(f"summary {dict(summary)}")
    print(f"proposals {args.proposals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
