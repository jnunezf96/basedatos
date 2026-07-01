#!/usr/bin/env python3
"""Normalize exact Spanish display residue in 1992 Karttunen public fields.

This pass deliberately avoids Karttunen's quoted source spellings, where
cedillas and long-vowel notation are evidence rather than display residue.
"""

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
PROPOSALS_PATH = Path("resources/karttunen_1992_spanish_residue_proposals.tsv")
SUMMARY_PATH = Path("resources/karttunen_1992_spanish_residue_summary.json")
SOURCE = "1992 Karttunen"
MARKER = "visible_spanish_1992_karttunen_residue_cleanup_2026_06_30"
QA_KEY = "qa_1992_karttunen_spanish_residue_cleanup"

PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_SUFFIX = "_raw_1992_karttunen_spanish_residue"
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")

REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<![\w-])frios(?![\w-])", re.I), "fríos"),
    (re.compile(r"/ocho\b"), "/ ocho"),
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


def raw_field_for(field: str) -> str:
    normalized = (
        field.replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    return normalized + RAW_FIELD_SUFFIX


def normalize_text(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str]] = []
    for pattern, replacement in REPLACEMENTS:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            changes.append((old, replacement))
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
        raw_fields: list[str] = []

        for field in PUBLIC_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_text(value)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if args.apply:
                raw_field = raw_field_for(field)
                if raw_field not in row:
                    row[raw_field] = value
                    raw_fields.append(raw_field)
                    counts["raw_preserved_fields"] += 1
                row[field] = new_value

        if not row_changes:
            continue

        counts["proposal_rows"] += 1
        counts["proposal_changes"] += len(row_changes)
        for _, old, new in row_changes:
            counts[f"change:{old}->{new}"] += 1
        proposals.append(
            {
                "record_id": row.get("record_id", ""),
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
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
                    "action": "normalized_exact_spanish_residue_in_public_karttunen_fields",
                    "marker": MARKER,
                    "raw_fields_preserved": raw_fields,
                    "changed_token_count": len(row_changes),
                    "previous_public_field_sha1": hashlib.sha1(
                        "||".join(str(row.get(raw_field, "")) for raw_field in raw_fields).encode("utf-8")
                    ).hexdigest(),
                },
            }
            row["Sentence_Source_JSON"] = qa

    write_tsv(
        args.proposals,
        proposals,
        ["record_id", "original", "editado", "old_tokens", "new_tokens", "context"],
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
