#!/usr/bin/env python3
"""Apply explicit per-token decisions from the source cleanup review pack.

This complements the grouped decision queue. The queue can say that a source
has remaining ``ç`` or circumflex residue, while this review pack lets a human
approve exact word-level replacements such as one ambiguous ``cançe`` token
without replacing every cedilla in that source.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
REVIEW_PACK_PATH = Path("resources/source_cleanup_review_pack.tsv")
PROPOSALS_PATH = Path("resources/source_cleanup_review_pack_apply_proposals.tsv")
SUMMARY_PATH = Path("resources/source_cleanup_review_pack_apply_summary.json")
MARKER = "source_cleanup_review_pack_apply_2026_06_30"
QA_KEY = "qa_source_cleanup_review_pack_apply"

PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_BY_PUBLIC_FIELD = {
    "Traducción": "Traducción_raw_source_cleanup_review_pack",
    "Traducción (es)": "Traducción_es_raw_source_cleanup_review_pack",
    "Comentario": "Comentario_raw_source_cleanup_review_pack",
    "Comentario (es)": "Comentario_es_raw_source_cleanup_review_pack",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_source_cleanup_review_pack",
}
NOOP_DECISIONS = {"", "pending", "keep", "ignore", "hold", "disallow"}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


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


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def replacement_for(review_row: dict[str, str]) -> tuple[str, str] | None:
    decision = review_row.get("decision", "").strip()
    if decision in NOOP_DECISIONS:
        return None
    old = review_row.get("review_token", "")
    replacement = review_row.get("replacement", "")
    if decision == "accept_bracket":
        if not replacement and old.startswith("[") and old.endswith("]"):
            replacement = old[1:-1]
    elif decision != "replace":
        raise ValueError(f"unknown review-pack decision {decision!r} for {old!r}")
    if not old or not replacement:
        raise ValueError(f"decision {decision!r} requires review_token and replacement for {old!r}")
    if old == replacement:
        return None
    return old, replacement


def context_for(value: str, token: str, width: int = 140) -> str:
    index = value.find(token)
    if index < 0:
        return value[: width * 2].replace("\n", " ")
    left = max(0, index - width)
    right = min(len(value), index + len(token) + width)
    return value[left:right].replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--review-pack", type=Path, default=REVIEW_PACK_PATH)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    replacements_by_source: dict[str, list[tuple[dict[str, str], str, str]]] = {}
    counts: Counter[str] = Counter()
    for review_row in read_tsv(args.review_pack):
        counts["review_rows"] += 1
        replacement = replacement_for(review_row)
        if not replacement:
            counts["noop_decision_rows"] += 1
            continue
        old, new = replacement
        replacements_by_source.setdefault(review_row.get("source", ""), []).append((review_row, old, new))
        counts["active_decision_rows"] += 1

    rows = load_rows(args.data)
    proposals: list[dict[str, object]] = []
    for row in rows:
        source_replacements = replacements_by_source.get(row.get("Fuente", ""), [])
        if not source_replacements:
            continue
        row_changes: list[tuple[str, str, str, str]] = []
        raw_fields: list[str] = []
        previous_commentary = row.get("Comentario", "")
        for field in PUBLIC_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value = value
            for review_row, old, new in source_replacements:
                if old not in new_value:
                    continue
                count = new_value.count(old)
                new_value = new_value.replace(old, new)
                key = "|".join(
                    [
                        review_row.get("source", ""),
                        review_row.get("triage", ""),
                        review_row.get("pattern", ""),
                        review_row.get("queue_token", ""),
                        review_row.get("review_token", ""),
                    ]
                )
                row_changes.extend((field, old, new, key) for _ in range(count))
            if new_value == value:
                continue
            if args.apply:
                raw_field = RAW_FIELD_BY_PUBLIC_FIELD[field]
                if raw_field not in row:
                    row[raw_field] = value
                    raw_fields.append(raw_field)
                row[field] = new_value

        if not row_changes:
            continue
        counts["proposal_rows"] += 1
        counts["proposal_changes"] += len(row_changes)
        proposals.append(
            {
                "record_id": row.get("record_id", ""),
                "source": row.get("Fuente", ""),
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "review_keys": " | ".join(sorted({key for _, _, _, key in row_changes})),
                "old_tokens": " | ".join(f"{field}:{old}" for field, old, _, _ in row_changes),
                "new_tokens": " | ".join(f"{field}:{new}" for field, _, new, _ in row_changes),
                "context": context_for(str(row.get(row_changes[0][0], "")), row_changes[0][1]),
            }
        )

        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                QA_KEY: {
                    "action": "applied_explicit_source_cleanup_review_pack_entries",
                    "marker": MARKER,
                    "review_keys": sorted({key for _, _, _, key in row_changes}),
                    "raw_fields": raw_fields,
                    "raw_preserved": True,
                    "changed_token_count": len(row_changes),
                    "previous_commentary_sha1": hashlib.sha1(str(previous_commentary).encode("utf-8")).hexdigest(),
                },
            }
            row["Sentence_Source_JSON"] = qa

    write_tsv(
        args.proposals,
        proposals,
        ["record_id", "source", "original", "editado", "review_keys", "old_tokens", "new_tokens", "context"],
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
