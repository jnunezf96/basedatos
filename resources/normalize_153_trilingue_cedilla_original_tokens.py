#!/usr/bin/env python3
"""Normalize Trilingue cedilla tokens already aligned to each row Original.

This is intentionally narrower than a source-wide cedilla pass. It only changes
cedilla-bearing tokens in public display fields when the same token appears in
the row's Original and the row has an Editado value. Raw commentary is preserved.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/trilingue_153_cedilla_original_token_proposals.tsv")
SUMMARY_PATH = Path("resources/trilingue_153_cedilla_original_token_summary.json")
SOURCE = "153? Trilingüe"
RAW_FIELD = "Comentario_raw_153_trilingue_cedilla_original_tokens"
MARKER = "visible_153_trilingue_cedilla_original_token_oldwriting_2026_06_29"
QA_KEY = "qa_153_trilingue_cedilla_original_tokens"

PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
FRONT_VOWELS = set("eéiíêîEÉIÍÊÎ")
TOKEN_RE = re.compile(
    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç^]*"
    r"[Çç]"
    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç^]*"
)
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)


def clean_html(value: object) -> str:
    text = str(value or "")
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_key(token: str) -> str:
    return token.lower().strip("^")


def original_cedilla_tokens(row: dict) -> set[str]:
    return {token_key(match.group(0)) for match in TOKEN_RE.finditer(str(row.get("Original", "")))}


def normalize_cedilla_token(token: str) -> str:
    out: list[str] = []
    for index, char in enumerate(token):
        if char not in "çÇ":
            out.append(char)
            continue
        next_char = token[index + 1] if index + 1 < len(token) else ""
        replacement = "c" if next_char in FRONT_VOWELS else "z"
        out.append(replacement.upper() if char == "Ç" else replacement)
    return "".join(out)


def normalize_value(value: object, allowed_tokens: set[str]) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        old = match.group(0)
        if token_key(old) not in allowed_tokens:
            return old
        new = normalize_cedilla_token(old)
        if new == old:
            return old
        changes.append((old, new))
        return new

    return TOKEN_RE.sub(repl, text), changes


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
        if not str(row.get("Editado", "")).strip():
            continue
        allowed_tokens = original_cedilla_tokens(row)
        if not allowed_tokens:
            continue

        previous_commentary = row.get("Comentario", "")
        row_changes: list[tuple[str, str, str]] = []
        for field in PUBLIC_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_value(value, allowed_tokens)
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
                    "action": "normalized_trilingue_cedilla_tokens_aligned_to_original",
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
