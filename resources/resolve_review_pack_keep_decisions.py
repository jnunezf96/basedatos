#!/usr/bin/env python3
"""Mark review-pack ``keep`` recommendations in the decision queue.

This is a queue-only housekeeping pass. It does not modify dictionary data.
It records decisions where the review pack can safely say a residue is
intentional public apparatus rather than cleanup work.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


QUEUE_PATH = Path("resources/source_cleanup_decision_queue.tsv")
REVIEW_PACK_PATH = Path("resources/source_cleanup_review_pack.tsv")
SUMMARY_PATH = Path("resources/source_cleanup_keep_decision_summary.json")
KEEP_NOTE_PREFIX = "review_pack_keep"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def review_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("source", ""),
        row.get("triage", ""),
        row.get("pattern", ""),
        row.get("queue_token", ""),
    )


def queue_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("source", ""),
        row.get("triage", ""),
        row.get("pattern", ""),
        row.get("token", ""),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=QUEUE_PATH)
    parser.add_argument("--review-pack", type=Path, default=REVIEW_PACK_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    queue_rows = read_tsv(args.queue)
    review_rows = read_tsv(args.review_pack)
    keep_by_key = {
        review_key(row): row
        for row in review_rows
        if row.get("recommendation") == "keep"
    }
    counts: Counter[str] = Counter()

    for row in queue_rows:
        counts["queue_rows"] += 1
        review = keep_by_key.get(queue_key(row))
        if not review:
            continue
        if row.get("decision") == "keep":
            counts["already_keep"] += 1
            continue
        if row.get("decision") not in {"", "pending"}:
            counts["skipped_non_pending"] += 1
            continue
        row["decision"] = "keep"
        row["replacement"] = ""
        reason = review.get("reason", "")
        row["decision_notes"] = f"{KEEP_NOTE_PREFIX}: {reason}".strip()
        counts["marked_keep"] += 1

    write_tsv(args.queue, queue_rows, list(queue_rows[0].keys()))
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"summary {dict(counts)}")
    print(f"queue {args.queue}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
