#!/usr/bin/env python3
"""Render the source cleanup decision queue as a compact Markdown report."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


QUEUE_PATH = Path("resources/source_cleanup_decision_queue.tsv")
REPORT_PATH = Path("resources/source_cleanup_decision_report.md")


def read_queue(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def clip(value: str, limit: int = 360) -> str:
    value = " ".join(str(value).split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def md_escape(value: object) -> str:
    text = str(value)
    return text.replace("\\", "\\\\").replace("|", "\\|")


def source_sort_key(item: tuple[str, list[dict[str, str]]]) -> tuple[int, str]:
    source, rows = item
    return (-len(rows), source)


def render_report(rows: list[dict[str, str]]) -> str:
    by_source: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    triage_counts = Counter()
    decision_counts = Counter()
    for row in rows:
        by_source[row["source"]].append(row)
        triage_counts[row["triage"]] += 1
        decision_counts[row.get("decision", "") or "pending"] += 1

    lines: list[str] = [
        "# Source Cleanup Decision Report",
        "",
        "Generated from `resources/source_cleanup_decision_queue.tsv`.",
        "",
        "Allowed decisions:",
        "",
        "- `pending`: leave unresolved for review.",
        "- `keep` or `ignore`: intentionally no-op.",
        "- `accept_bracket`: replace `[token]` with `token`, unless `replacement` is filled.",
        "- `replace`: replace the exact token with `replacement`.",
        "",
        "## Summary",
        "",
        f"- Queue rows: {len(rows)}",
        "- By triage: "
        + ", ".join(f"{name}={count}" for name, count in sorted(triage_counts.items())),
        "- By decision: "
        + ", ".join(f"{name}={count}" for name, count in sorted(decision_counts.items())),
        "",
        "## Source Groups",
        "",
    ]

    for source, source_rows in sorted(by_source.items(), key=source_sort_key):
        lines.extend(
            [
                f"### {source}",
                "",
                "| decision_id | decision | token | count | triage | default action | example |",
                "|---|---|---:|---:|---|---|---|",
            ]
        )
        source_rows.sort(
            key=lambda row: (
                float(row.get("priority") or 0),
                int(row.get("token_count") or 0),
                row.get("token", ""),
            ),
            reverse=True,
        )
        for row in source_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_escape(row.get("decision_id", "")),
                        md_escape(row.get("decision", "") or "pending"),
                        md_escape(row.get("token", "")),
                        md_escape(row.get("token_count", "")),
                        md_escape(row.get("triage", "")),
                        md_escape(row.get("default_action", "")),
                        md_escape(clip(row.get("example_context", ""))),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=QUEUE_PATH)
    parser.add_argument("--output", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    rows = read_queue(args.queue)
    args.output.write_text(render_report(rows), encoding="utf-8")
    print(f"report {args.output} rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
