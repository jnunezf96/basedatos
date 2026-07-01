#!/usr/bin/env python3
"""Build a compact decision queue from the source cleanup dashboard.

This is a planning aid for the remaining source-by-source cleanup work. It does
not rewrite dictionary data. It refreshes the dashboard, then extracts only the
groups that still require an explicit cleanup decision.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


DASHBOARD_SCRIPT = Path("resources/source_cleanup_dashboard.py")
SUMMARY_PATH = Path("resources/source_cleanup_dashboard_summary.tsv")
EXAMPLES_PATH = Path("resources/source_cleanup_dashboard_examples.tsv")
QUEUE_PATH = Path("resources/source_cleanup_decision_queue.tsv")
QUEUE_SUMMARY_PATH = Path("resources/source_cleanup_decision_queue_summary.json")

DECISION_TRIAGES = {
    "batch_candidate",
    "orthography_review",
    "editorial_review",
    "inline_restoration_review",
    "preceding_correction_review",
}

DEFAULT_ACTIONS = {
    "batch_candidate": "apply after preview",
    "orthography_review": "hold for source-specific spelling decision",
    "editorial_review": "hold for bracket role decision: correction vs insertion/gloss/note",
    "inline_restoration_review": "hold for supplied-letter apparatus decision",
    "preceding_correction_review": "hold for bracketed preceding-spelling correction decision",
}

FIELDS = [
    "decision_id",
    "decision",
    "replacement",
    "decision_notes",
    "priority",
    "source",
    "triage",
    "pattern",
    "token",
    "token_count",
    "group_count",
    "group_row_count",
    "default_action",
    "example_record_ids",
    "example_fields",
    "example_context",
]

DECISION_FIELDS = ["decision", "replacement", "decision_notes"]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def existing_decisions(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    decisions: dict[str, dict[str, str]] = {}
    for row in read_tsv(path):
        decision_id = row.get("decision_id", "")
        if not decision_id:
            continue
        decisions[decision_id] = {field: row.get(field, "") for field in DECISION_FIELDS}
    return decisions


def parse_top_tokens(value: str) -> list[tuple[str, int]]:
    tokens: list[tuple[str, int]] = []
    for piece in value.split(";"):
        piece = piece.strip()
        if not piece or "=" not in piece:
            continue
        token, count = piece.rsplit("=", 1)
        try:
            tokens.append((token.strip(), int(count)))
        except ValueError:
            continue
    return tokens


def clip(value: str, limit: int = 260) -> str:
    value = " ".join(str(value).split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def decision_id_for(source: str, triage: str, pattern: str, token: str) -> str:
    payload = "\t".join([source, triage, pattern, token])
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]
    return f"dq-{digest}"


def refresh_dashboard(top: int, examples_per_group: int) -> None:
    subprocess.run(
        [
            sys.executable,
            str(DASHBOARD_SCRIPT),
            "--top",
            str(top),
            "--examples-per-group",
            str(examples_per_group),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def build_queue(
    summary_rows: list[dict[str, str]],
    example_rows: list[dict[str, str]],
    preserved_decisions: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    examples_by_key: defaultdict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    group_examples: defaultdict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for example in example_rows:
        group_key = (example["source"], example["pattern"], example["triage"])
        group_examples[group_key].append(example)
        examples_by_key[(*group_key, example["token"])].append(example)

    queue: list[dict[str, object]] = []
    for row in summary_rows:
        triage = row.get("triage", "")
        if triage not in DECISION_TRIAGES:
            continue
        group_key = (row.get("source", ""), row.get("pattern", ""), triage)
        top_tokens = parse_top_tokens(row.get("top_tokens", ""))
        if triage == "preceding_correction_review":
            correction_tokens: defaultdict[str, int] = defaultdict(int)
            for example in group_examples.get(group_key, []):
                token = example.get("token", "")
                if token:
                    correction_tokens[token] += 1
            if correction_tokens:
                top_tokens = sorted(correction_tokens.items(), key=lambda item: (-item[1], item[0]))
        if not top_tokens:
            top_tokens = [("(group)", int(row.get("count", "0") or 0))]

        for token, token_count in top_tokens:
            decision_id = decision_id_for(row.get("source", ""), triage, row.get("pattern", ""), token)
            preserved = preserved_decisions.get(decision_id, {})
            token_examples = examples_by_key.get((*group_key, token), [])
            missing_token_example = False
            if not token_examples:
                missing_token_example = True
                token_examples = group_examples.get(group_key, [])[:3]
            queue.append(
                {
                    "decision_id": decision_id,
                    "decision": preserved.get("decision", "pending"),
                    "replacement": preserved.get("replacement", ""),
                    "decision_notes": preserved.get("decision_notes", ""),
                    "priority": row.get("priority", ""),
                    "source": row.get("source", ""),
                    "triage": triage,
                    "pattern": row.get("pattern", ""),
                    "token": token,
                    "token_count": token_count,
                    "group_count": row.get("count", ""),
                    "group_row_count": row.get("row_count", ""),
                    "default_action": DEFAULT_ACTIONS.get(triage, "review"),
                    "example_record_ids": " | ".join(example.get("record_id", "") for example in token_examples[:3]),
                    "example_fields": " | ".join(example.get("field", "") for example in token_examples[:3]),
                    "example_context": (
                        "NO TOKEN-SPECIFIC EXAMPLE IN DASHBOARD SAMPLE"
                        if missing_token_example
                        else " || ".join(clip(example.get("context", "")) for example in token_examples[:3])
                    ),
                }
            )
    queue.sort(
        key=lambda item: (
            float(item.get("priority") or 0),
            int(item.get("token_count") or 0),
            str(item.get("source") or ""),
            str(item.get("token") or ""),
        ),
        reverse=True,
    )
    return queue


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--examples", type=Path, default=EXAMPLES_PATH)
    parser.add_argument("--output", type=Path, default=QUEUE_PATH)
    parser.add_argument("--queue-summary", type=Path, default=QUEUE_SUMMARY_PATH)
    parser.add_argument("--top", type=int, default=200)
    parser.add_argument("--examples-per-group", type=int, default=120)
    parser.add_argument("--no-refresh", action="store_true")
    parser.add_argument("--reset-decisions", action="store_true")
    args = parser.parse_args()

    if not args.no_refresh:
        refresh_dashboard(args.top, args.examples_per_group)

    preserved = {} if args.reset_decisions else existing_decisions(args.output)
    queue = build_queue(read_tsv(args.summary), read_tsv(args.examples), preserved)
    write_tsv(args.output, queue)
    counts: defaultdict[str, int] = defaultdict(int)
    source_counts: defaultdict[str, int] = defaultdict(int)
    decision_counts: defaultdict[str, int] = defaultdict(int)
    for row in queue:
        counts[str(row["triage"])] += 1
        source_counts[str(row["source"])] += 1
        decision_counts[str(row["decision"])] += 1
    payload = {
        "queue_rows": len(queue),
        "by_triage": dict(sorted(counts.items())),
        "by_source": dict(sorted(source_counts.items())),
        "by_decision": dict(sorted(decision_counts.items())),
        "output": str(args.output),
    }
    args.queue_summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"queue {args.output} rows={len(queue)}")
    print(f"summary {args.queue_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
