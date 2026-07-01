#!/usr/bin/env python3
"""Render the per-token source cleanup review pack as Markdown."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


PACK_PATH = Path("resources/source_cleanup_review_pack.tsv")
RESEARCH_PATH = Path("resources/source_cleanup_cedilla_research.tsv")
REPORT_PATH = Path("resources/source_cleanup_review_report.md")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def clip(value: object, limit: int = 280) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def md_escape(value: object) -> str:
    text = str(value or "")
    return text.replace("\\", "\\\\").replace("|", "\\|")


def source_sort_key(item: tuple[str, list[dict[str, str]]]) -> tuple[int, str]:
    source, rows = item
    return (-len(rows), source)


def research_key(row: dict[str, str]) -> tuple[str, str]:
    return (row.get("source", ""), row.get("review_token", ""))


def evidence_text(research_rows: list[dict[str, str]]) -> str:
    if not research_rows:
        return ""
    positive_rows = [row for row in research_rows if int(row.get("occurrences") or 0) > 0]
    zero_rows = [row for row in research_rows if int(row.get("occurrences") or 0) == 0 and row.get("candidate_kind") != "source_token"]
    positive_rows.sort(key=lambda row: (-int(row.get("occurrences") or 0), row.get("candidate_kind", ""), row.get("candidate", "")))
    zero_rows.sort(key=lambda row: (row.get("candidate_kind", ""), row.get("candidate", "")))
    parts = []
    for row in positive_rows[:4]:
        parts.append(
            f"{row.get('candidate', '')} {row.get('candidate_kind', '')} x{row.get('occurrences', '')}"
        )
    if zero_rows:
        searched = ", ".join(row.get("candidate", "") for row in zero_rows[:5])
        parts.append(f"no local hits: {searched}")
    return "; ".join(parts)


def render(rows: list[dict[str, str]], research_rows: list[dict[str, str]]) -> str:
    by_source: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    research_by_key: defaultdict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    by_decision = Counter()
    by_triage = Counter()
    for row in rows:
        by_source[row["source"]].append(row)
        by_decision[row.get("decision") or "pending"] += 1
        by_triage[row["triage"]] += 1
    for row in research_rows:
        research_by_key[research_key(row)].append(row)

    lines = [
        "# Source Cleanup Review Report",
        "",
        "Generated from `resources/source_cleanup_review_pack.tsv`.",
        "",
        "Use this report to decide the remaining per-token cases. To apply a decision, edit the TSV columns `decision` and `replacement`, then run `python3 resources/apply_source_cleanup_review_pack_decisions.py --apply`.",
        "",
        "Allowed decisions:",
        "",
        "- `pending`: no-op; still needs review.",
        "- `keep`: intentional apparatus; no-op.",
        "- `accept_bracket`: replace `[token]` with `token`, unless `replacement` is filled.",
        "- `replace`: replace `review_token` with `replacement`.",
        "- `ignore` or `disallow`: no-op.",
        "",
        "## Summary",
        "",
        f"- Review rows: {len(rows)}",
        "- By decision: " + ", ".join(f"{key}={value}" for key, value in sorted(by_decision.items())),
        "- By triage: " + ", ".join(f"{key}={value}" for key, value in sorted(by_triage.items())),
        "",
        "## Source Groups",
        "",
    ]

    for source, source_rows in sorted(by_source.items(), key=source_sort_key):
        source_rows.sort(
            key=lambda row: (
                row.get("triage", ""),
                row.get("pattern", ""),
                -int(row.get("token_count") or 0),
                row.get("review_token", ""),
            )
        )
        lines.extend(
            [
                f"### {source}",
                "",
                "| decision | token | candidate | evidence | count | triage | confidence | reason | example |",
                "|---|---|---|---|---:|---|---|---|---|",
            ]
        )
        for row in source_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_escape(row.get("decision") or "pending"),
                        md_escape(row.get("review_token", "")),
                        md_escape(row.get("candidate_replacement", "")),
                        md_escape(evidence_text(research_by_key[research_key(row)])),
                        md_escape(row.get("token_count", "")),
                        md_escape(row.get("triage", "")),
                        md_escape(row.get("confidence", "")),
                        md_escape(row.get("reason", "")),
                        md_escape(clip(row.get("example_context", ""))),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=PACK_PATH)
    parser.add_argument("--research", type=Path, default=RESEARCH_PATH)
    parser.add_argument("--output", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    rows = read_tsv(args.pack)
    research_rows = read_tsv(args.research) if args.research.exists() else []
    args.output.write_text(render(rows, research_rows), encoding="utf-8")
    print(f"report {args.output} rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
