#!/usr/bin/env python3
"""Normalize selected Sahagún/Máynez qua/quah/quauh old-spelling forms."""

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
from typing import Any


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/commentary_maynez_qu_cu_proposals.tsv")
SUMMARY_PATH = Path("resources/commentary_maynez_qu_cu_summary.json")
MARKER = "visible_commentary_maynez_qu_cu_2026_06_30"
QA_KEY = "qa_commentary_maynez_qu_cu"

TARGET_SOURCE = "1580 Sahagún/Máynez"
DISPLAY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_BY_FIELD = {
    "Comentario": "Comentario_public_raw_maynez_qu_cu",
    "Comentario (es)": "Comentario_es_raw_maynez_qu_cu",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_maynez_qu_cu",
}

WORD_RE = re.compile(
    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌŪāēīōūÂÊÎÔÛâêîôûÀÈÌÒÙàèìòùÄËÏÖÜäëïöüÃÕãõÇç]+"
)
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")

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


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: object, token: str, width: int = 170) -> str:
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


def preserve_case_fragment(old: str, new: str) -> str:
    if old.isupper():
        return new.upper()
    if old[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def replace_quahuitl_variants(word: str) -> str:
    patterns = [
        (r"quahuitl", "cuahuitl"),
        (r"quavitl", "cuahuitl"),
        (r"quauitl", "cuahuitl"),
        (r"quaujtl", "cuahuitl"),
    ]
    output = word
    for pattern, replacement in patterns:
        output = re.sub(
            pattern,
            lambda match: preserve_case_fragment(match.group(0), replacement),
            output,
            flags=re.I,
        )
    return output


def replacement_for_word(word: str) -> str | None:
    if not re.search(r"qua|quá", word, re.I):
        return None
    output = replace_quahuitl_variants(word)
    output = re.sub(
        r"qua",
        lambda match: preserve_case_fragment(match.group(0), "cua"),
        output,
        flags=re.I,
    )
    output = re.sub(
        r"quá",
        lambda match: preserve_case_fragment(match.group(0), "cuá"),
        output,
        flags=re.I,
    )
    return output if output != word else None


def apply_replacements(value: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        replacement = replacement_for_word(word)
        if not replacement or replacement == word:
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
    summary: Counter[str] = Counter()
    pair_counts: Counter[str] = Counter()
    proposals: list[dict[str, object]] = []

    for row in rows:
        if row.get("Fuente") != TARGET_SOURCE:
            continue
        summary["target_source_rows"] += 1
        previous_commentary = row.get("Comentario", "")
        row_changes: list[tuple[str, str, str]] = []
        for field in DISPLAY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str):
                continue
            new_value, changes = apply_replacements(value)
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
            proposals.append({
                "source": row.get("Fuente", ""),
                "record_id": row.get("record_id", ""),
                "field": field,
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "old_tokens": " | ".join(old for old, _new in changes[:12]),
                "new_tokens": " | ".join(new for _old, new in changes[:12]),
                "context": token_context(value, changes[0][0]),
            })

        if not row_changes:
            continue
        summary["proposal_rows"] += 1
        summary["proposal_changes"] += len(row_changes)
        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_issue(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa[QA_KEY] = {
                "action": "normalized_maynez_qua_old_spelling_to_cua_in_commentary",
                "marker": MARKER,
                "raw_fields_preserved": sorted({RAW_FIELD_BY_FIELD[field] for field, _old, _new in row_changes}),
                "changed_token_count": len(row_changes),
                "previous_commentary_sha1": hashlib.sha1(str(previous_commentary).encode("utf-8")).hexdigest(),
            }
            row["Sentence_Source_JSON"] = qa
            summary["applied_rows"] += 1

    write_tsv(args.proposals, proposals)
    summary_payload = {
        **summary,
        "top_replacements": dict(pair_counts.most_common()),
    }
    args.summary.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.apply and proposals:
        write_rows(args.data, rows)

    print(f"summary {dict(summary)}")
    print(f"proposals {args.proposals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
