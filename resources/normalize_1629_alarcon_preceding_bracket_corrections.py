#!/usr/bin/env python3
"""Normalize 1629 Alarcon brackets that correct the immediately preceding word."""

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
PROPOSALS_PATH = Path("resources/alarcon_1629_preceding_bracket_corrections_proposals.tsv")
SUMMARY_PATH = Path("resources/alarcon_1629_preceding_bracket_corrections_summary.json")
SOURCE = "1629 Alarcón"
MARKER = "visible_1629_alarcon_preceding_bracket_corrections_2026_06_30"
QA_KEY = "qa_1629_alarcon_preceding_bracket_corrections"

DISPLAY_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_BY_FIELD = {
    "Traducción": "Traduccion_raw_1629_alarcon_preceding_bracket_corrections",
    "Traducción (es)": "Traduccion_es_raw_1629_alarcon_preceding_bracket_corrections",
    "Comentario": "Comentario_raw_1629_alarcon_preceding_bracket_corrections",
    "Comentario (es)": "Comentario_es_raw_1629_alarcon_preceding_bracket_corrections",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_1629_alarcon_preceding_bracket_corrections",
}

REPLACEMENTS = {
    "macuiltonelleque [macuiltonalleque]": "macuiltonalleque",
    "nonahualtzantecomatl [nonahualtzontecomatl]": "nonahualtzontecomatl",
    "chiucnaulimictlan [chicnauhmictlan]": "chicnauhmictlan",
    "chicnatitlatetzontli [chicnauhtlatetzontli]": "chicnauhtlatetzontli",
}

BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
PROPOSAL_FIELDS = ["source", "record_id", "original", "editado", "marker", "old_tokens", "new_tokens", "context"]


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def context_for(value: object, tokens: list[str], width: int = 170) -> str:
    text = clean_html(value)
    index = -1
    token = ""
    for candidate in tokens:
        index = text.lower().find(candidate.lower())
        token = candidate
        if index >= 0:
            break
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


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=PROPOSAL_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in PROPOSAL_FIELDS})


def replace_value(value: str) -> tuple[str, list[tuple[str, str, int]]]:
    changes: list[tuple[str, str, int]] = []
    new_value = value
    for old, new in REPLACEMENTS.items():
        count = new_value.count(old)
        if not count:
            continue
        new_value = new_value.replace(old, new)
        changes.append((old, new, count))
    return new_value, changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = load_rows(args.data)
    counts: Counter[str] = Counter()
    proposals: list[dict[str, object]] = []

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        counts["source_rows"] += 1
        row_changes: list[tuple[str, str, str, int]] = []
        first_field = ""
        old_context_tokens: list[str] = []
        for field in DISPLAY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str):
                continue
            new_value, changes = replace_value(value)
            if not changes:
                continue
            if args.apply:
                raw_field = RAW_FIELD_BY_FIELD[field]
                if raw_field not in row:
                    row[raw_field] = value
                    counts["raw_preserved_fields"] += 1
                row[field] = new_value
            if not first_field:
                first_field = field
            for old, new, count in changes:
                row_changes.append((field, old, new, count))
                old_context_tokens.append(old)

        if not row_changes:
            continue
        counts["proposal_rows"] += 1
        counts["proposal_changes"] += sum(count for _field, _old, _new, count in row_changes)
        if args.apply:
            row[QA_KEY] = append_marker(row.get(QA_KEY, ""), MARKER)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues", ""), MARKER)
            counts["applied_rows"] += 1
        proposals.append(
            {
                "source": SOURCE,
                "record_id": row.get("record_id", ""),
                "original": clean_html(row.get("Original", "")),
                "editado": clean_html(row.get("Editado", "")),
                "marker": MARKER,
                "old_tokens": " | ".join(f"{field}:{old}" for field, old, _new, _count in row_changes),
                "new_tokens": " | ".join(f"{field}:{new}" for field, _old, new, _count in row_changes),
                "context": context_for(row.get(first_field, ""), old_context_tokens),
            }
        )

    write_tsv(args.proposals, proposals)
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.apply and proposals:
        write_rows(args.data, rows)

    print(f"summary {dict(counts)}")
    print(f"proposals {args.proposals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
