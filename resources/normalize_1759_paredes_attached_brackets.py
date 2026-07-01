#!/usr/bin/env python3
"""Remove attached one-letter square brackets in 1759 Paredes commentary."""

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
PROPOSALS_PATH = Path("resources/paredes_1759_attached_bracket_proposals.tsv")
SUMMARY_PATH = Path("resources/paredes_1759_attached_bracket_summary.json")
SOURCE = "1759 Paredes"
RAW_FIELD = "Comentario_raw_1759_paredes_attached_brackets"
MARKER = "visible_1759_paredes_attached_bracket_cleanup_2026_06_29"
QA_KEY = "qa_1759_paredes_attached_bracket_cleanup"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
BRACKET_RE = re.compile(r"\[([A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç])\]")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
WORD_EDGE_RE = re.compile(r"[\wÁÉÍÓÚÜÑáéíóúüñÀ-ÖØ-öø-ÿĀ-ž]", re.U)


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_word_char(char: str) -> bool:
    return bool(char and WORD_EDGE_RE.fullmatch(char))


def normalize_value(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        before = text[match.start() - 1] if match.start() else ""
        after = text[match.end()] if match.end() < len(text) else ""
        if not (is_word_char(before) or is_word_char(after)):
            return match.group(0)
        old = match.group(0)
        new = match.group(1)
        changes.append((old, new))
        return new

    return BRACKET_RE.sub(repl, text), changes


def token_context(value: object, token: str, width: int = 140) -> str:
    text = clean_html(value)
    index = text.find(token)
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

        for field in COMMENTARY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or "[" not in value:
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
                    "action": "removed_attached_one_letter_square_brackets_from_1759_paredes_commentary",
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
