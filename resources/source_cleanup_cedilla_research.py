#!/usr/bin/env python3
"""Collect corpus evidence for unresolved cedilla review-pack decisions."""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
REVIEW_PACK_PATH = Path("resources/source_cleanup_review_pack.tsv")
OUTPUT_PATH = Path("resources/source_cleanup_cedilla_research.tsv")
SUMMARY_PATH = Path("resources/source_cleanup_cedilla_research_summary.json")

PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_RE = re.compile(r"(?:raw|Raw)")
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)

EXTRA_VARIANTS = {
    "adeçetar": ["adecetar", "adezetar", "acecetar", "acezetar", "acezar"],
    "espeçiba": ["especiba", "espeziba", "especiva", "expresiva"],
    "alabançan": ["alabanzan", "abalanzan"],
    "caçegas": ["cacegas", "cazegas", "cegas"],
}

FIELDS = [
    "source",
    "review_token",
    "candidate",
    "candidate_kind",
    "occurrences",
    "record_ids",
    "fields",
    "example_context",
]


def clean_text(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def context_for(text: str, token: str, width: int = 150) -> str:
    match = re.search(re.escape(token), text, re.I)
    if not match:
        return text[: width * 2].strip()
    left = max(0, match.start() - width)
    right = min(len(text), match.end() + width)
    return text[left:right].strip()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def iter_rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def mechanical_cedilla(token: str) -> str:
    out: list[str] = []
    for index, char in enumerate(token):
        if char not in "çÇ":
            out.append(char)
            continue
        next_char = token[index + 1 : index + 2].lower()
        replacement = "c" if next_char in {"e", "i"} else "z"
        out.append(replacement.upper() if char == "Ç" else replacement)
    return "".join(out)


def candidate_list(token: str, candidate_replacement: str) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for kind, candidate in [
        ("source_token", token),
        ("mechanical", candidate_replacement or mechanical_cedilla(token)),
    ]:
        if candidate and candidate.lower() not in seen:
            out.append((kind, candidate))
            seen.add(candidate.lower())
    for candidate in EXTRA_VARIANTS.get(token.lower(), []):
        if candidate.lower() not in seen:
            out.append(("plausible_variant", candidate))
            seen.add(candidate.lower())
    return out


def fields_for_row(row: dict) -> list[str]:
    fields = list(PUBLIC_FIELDS)
    fields.extend(key for key in row if RAW_FIELD_RE.search(key) and isinstance(row.get(key), str))
    return fields


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--review-pack", type=Path, default=REVIEW_PACK_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    review_rows = [
        row
        for row in read_tsv(args.review_pack)
        if row.get("pattern") == "cedilla" and row.get("recommendation") == "needs_user"
    ]
    candidates: dict[str, list[tuple[str, str]]] = {}
    allowed_sources: dict[str, str] = {}
    for row in review_rows:
        token = row.get("review_token", "")
        if not token:
            continue
        candidates[token] = candidate_list(token, row.get("candidate_replacement", ""))
        allowed_sources[token] = row.get("source", "")

    grouped: dict[tuple[str, str, str, str], dict[str, object]] = {}
    counts: Counter[str] = Counter()
    for row in iter_rows(args.data):
        source = row.get("Fuente", "")
        for review_token, token_candidates in candidates.items():
            if allowed_sources.get(review_token) and source != allowed_sources[review_token]:
                continue
            for kind, candidate in token_candidates:
                for field in fields_for_row(row):
                    value = row.get(field, "")
                    if not isinstance(value, str) or not value:
                        continue
                    text = clean_text(value)
                    found = len(re.findall(re.escape(candidate), text, re.I))
                    if not found:
                        continue
                    key = (source, review_token, candidate, kind)
                    item = grouped.setdefault(
                        key,
                        {
                            "source": source,
                            "review_token": review_token,
                            "candidate": candidate,
                            "candidate_kind": kind,
                            "occurrences": 0,
                            "record_ids": set(),
                            "fields": set(),
                            "example_context": "",
                        },
                    )
                    item["occurrences"] = int(item["occurrences"]) + found
                    item["record_ids"].add(row.get("record_id", ""))
                    item["fields"].add(field)
                    if not item["example_context"]:
                        item["example_context"] = context_for(text, candidate)

    for review_token, token_candidates in candidates.items():
        source = allowed_sources.get(review_token, "")
        for kind, candidate in token_candidates:
            key = (source, review_token, candidate, kind)
            grouped.setdefault(
                key,
                {
                    "source": source,
                    "review_token": review_token,
                    "candidate": candidate,
                    "candidate_kind": kind,
                    "occurrences": 0,
                    "record_ids": set(),
                    "fields": set(),
                    "example_context": "",
                },
            )

    rows_out: list[dict[str, object]] = []
    for item in grouped.values():
        rows_out.append(
            {
                **item,
                "record_ids": " | ".join(sorted(str(value) for value in item["record_ids"] if value)[:8]),
                "fields": " | ".join(sorted(str(value) for value in item["fields"])),
            }
        )
    rows_out.sort(
        key=lambda row: (
            str(row["source"]),
            str(row["review_token"]),
            0 if row["candidate_kind"] == "source_token" else 1,
            0 if int(row["occurrences"]) > 0 else 1,
            -int(row["occurrences"]),
            str(row["candidate"]),
        )
    )

    for row in rows_out:
        counts["rows"] += 1
        counts[f"review_token:{row['review_token']}"] += 1
        counts[f"candidate_kind:{row['candidate_kind']}"] += 1

    write_tsv(args.output, rows_out)
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"research {args.output} rows={len(rows_out)}")
    print(f"summary {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
