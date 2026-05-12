#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "edition_punctuated_marker_cleanup_report.jsonl"

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÇç§ƺ\[\]_-]+|\d+|\?")
PUNCTUATED_MARKERS = {
    "am",
    "an",
    "n",
    "ni",
    "nic",
    "nictla",
    "nimitz",
    "nin",
    "nino",
    "ninote",
    "nite",
    "nitla",
    "nitlatla",
    "no",
    "ti",
    "tic",
    "tite",
    "titla",
    "to",
}

SKIP_RECORD_IDS = {
    # Here `ni` is lexical in the expression translated "ni uno ni otro", not
    # a separated Nahuatl subject/object marker.
    "1765-cortes-y-zedeno:000391",
}


def replace_legacy_chars(value: str) -> str:
    return (
        (value or "")
        .replace("Ç", "Z")
        .replace("ç", "z")
        .replace("ƺ", "z")
        .replace("§", "s")
    )


def strip_accents(value: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", replace_legacy_chars(value))
        if unicodedata.category(ch) != "Mn"
    )


def clean_token(value: str) -> str:
    text = strip_accents(value).lower()
    text = text.replace("[", "").replace("]", "").replace("_", "").replace("-", "")
    return re.sub(r"[^a-z0-9?]+", "", text)


def tokens_with_spans(value: str) -> list[tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in WORD_RE.finditer(value or "")]


def original_marker_tokens(original: str) -> list[str]:
    markers: list[str] = []
    for token, start, end in tokens_with_spans(original):
        cleaned = clean_token(token)
        if cleaned not in PUNCTUATED_MARKERS:
            continue
        before = original[max(0, start - 4) : start]
        after = original[end : min(len(original), end + 4)]
        if re.search(r"[,;/]\s*$", before) or re.search(r"^\s*[,;/]", after):
            markers.append(cleaned)
    return markers


def cleaned_edition_tokens(edition: str) -> list[str]:
    return [clean_token(token) for token, _start, _end in tokens_with_spans(edition)]


def remove_markers_from_edition(edition: str, markers: set[str]) -> str:
    kept = []
    for token, _start, _end in tokens_with_spans(edition):
        if clean_token(token) in markers:
            continue
        literal = token.replace("[", "").replace("]", "").replace("_", "").replace("-", "")
        if literal:
            kept.append(literal)
    return re.sub(r"\s+", " ", " ".join(kept)).strip()


def read_rows() -> list[dict]:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def write_rows(rows: list[dict]) -> None:
    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes to data/data.jsonl.gz")
    parser.add_argument(
        "--report-path",
        default=str(REPORT_PATH),
        help="write the JSONL report here; defaults to scripts/edition_punctuated_marker_cleanup_report.jsonl",
    )
    args = parser.parse_args()

    rows = read_rows()
    report = []

    for row in rows:
        record_id = row.get("record_id") or ""
        source = row.get("Fuente") or ""
        if record_id in SKIP_RECORD_IDS or source.startswith("V94"):
            continue

        original = row.get("Escritura original") or ""
        edition = row.get("Texto estandarizado") or ""
        markers = original_marker_tokens(original)
        if not markers:
            continue

        edition_tokens = cleaned_edition_tokens(edition)
        markers_in_edition = sorted({marker for marker in markers if marker in edition_tokens})
        if not markers_in_edition:
            continue

        new_edition = remove_markers_from_edition(edition, set(markers_in_edition))
        if not new_edition or new_edition == edition:
            continue

        report.append(
            {
                "record_id": record_id,
                "source": source,
                "original": original,
                "old_edition": edition,
                "new_edition": new_edition,
                "translation": row.get("Traducción"),
                "dropped_markers": markers_in_edition,
            }
        )
        if args.apply:
            row["Texto estandarizado"] = new_edition

    report_path = Path(args.report_path)
    with report_path.open("w", encoding="utf-8") as fh:
        for item in report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    if args.apply:
        write_rows(rows)

    marker_counts = Counter(marker for item in report for marker in item["dropped_markers"])
    print(f"changed_rows={len(report) if args.apply else 0}")
    print(f"proposed_rows={len(report)}")
    print(f"applied={args.apply}")
    print(f"marker_counts={dict(marker_counts)}")
    print(f"report={report_path}")


if __name__ == "__main__":
    main()
