#!/usr/bin/env python3
"""Normalize exact bracketed root correction in 1629 Alarcon commentary."""

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
PROPOSALS_PATH = Path("resources/alarcon_1629_bracketed_root_correction_proposals.tsv")
SUMMARY_PATH = Path("resources/alarcon_1629_bracketed_root_correction_summary.json")
SOURCE = "1629 Alarcón"
MARKER = "visible_1629_alarcon_bracketed_root_correction_2026_06_30"
QA_KEY = "qa_1629_alarcon_bracketed_root_correction"

DISPLAY_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_BY_FIELD = {
    "Traducción": "Traduccion_raw_1629_alarcon_bracketed_root_correction",
    "Traducción (es)": "Traduccion_es_raw_1629_alarcon_bracketed_root_correction",
    "Comentario": "Comentario_raw_1629_alarcon_bracketed_root_correction",
    "Comentario (es)": "Comentario_es_raw_1629_alarcon_bracketed_root_correction",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_1629_alarcon_bracketed_root_correction",
}

OLD = "timòhuimolloz [huinelloz]"
NEW = "timohuinelloz"

BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
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
    counts: Counter[str] = Counter()
    proposals: list[dict[str, object]] = []

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        counts["source_rows"] += 1
        row_changes: list[tuple[str, int]] = []
        for field in DISPLAY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or OLD not in value:
                continue
            count = value.count(OLD)
            if args.apply:
                raw_field = RAW_FIELD_BY_FIELD[field]
                if raw_field not in row:
                    row[raw_field] = value
                    counts["raw_preserved_fields"] += 1
                row[field] = value.replace(OLD, NEW)
            row_changes.append((field, count))

        if not row_changes:
            continue
        counts["proposal_rows"] += 1
        counts["proposal_changes"] += sum(count for _field, count in row_changes)
        if args.apply:
            row[QA_KEY] = append_marker(row.get(QA_KEY, ""), MARKER)
            counts["applied_rows"] += 1
        proposals.append(
            {
                "source": SOURCE,
                "record_id": row.get("record_id", ""),
                "original": clean_html(row.get("Original", "")),
                "editado": clean_html(row.get("Editado", "")),
                "marker": MARKER,
                "old_tokens": " | ".join(f"{field}:{OLD}" for field, _count in row_changes),
                "new_tokens": " | ".join(f"{field}:{NEW}" for field, _count in row_changes),
                "context": context_for(row.get(row_changes[0][0], ""), NEW if args.apply else OLD),
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
