#!/usr/bin/env python3
"""Run one cleanup normalizer through the standard stage workflow.

The default mode is dry-run only. With --apply, this runs the normalizer,
checks idempotence using temporary proposal files, rebuilds bootstrap/cache,
runs the standard verifier, and refreshes the cleanup dashboard.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


VERIFY_SCRIPT = Path("resources/verify_cleanup_stage.py")
DASHBOARD_SCRIPT = Path("resources/source_cleanup_dashboard.py")
JOURNAL_PATH = Path("resources/cleanup_stage_journal.tsv")
PREVIEW_COLUMNS = ["record_id", "original", "editado", "old_tokens", "new_tokens", "context"]
JOURNAL_COLUMNS = [
    "timestamp_utc",
    "script",
    "proposal_rows",
    "proposal_changes",
    "targets",
    "bootstrap_tag",
    "cache_version",
]


def run(cmd: list[str], *, label: str) -> str:
    print(f"\n== {label} ==")
    print("$ " + " ".join(cmd))
    result = subprocess.run(cmd, text=True, capture_output=True)
    output = (result.stdout + result.stderr).strip()
    if output:
        print(output)
    if result.returncode:
        raise SystemExit(result.returncode)
    return output


def normalizer_cmd(script: Path, *, apply: bool, proposals: Path | None, summary: Path | None) -> list[str]:
    cmd = [sys.executable, str(script)]
    if apply:
        cmd.append("--apply")
    if proposals:
        cmd.extend(["--proposals", str(proposals)])
    if summary:
        cmd.extend(["--summary", str(summary)])
    return cmd


def extract_proposals_path(output: str) -> Path | None:
    for line in output.splitlines():
        if line.startswith("proposals "):
            return Path(line.split(" ", 1)[1].strip())
    return None


def infer_summary_path(proposals: Path | None) -> Path | None:
    if proposals is None:
        return None
    stem = proposals.stem
    if stem.endswith("_proposals"):
        return proposals.with_name(stem[: -len("_proposals")] + "_summary.json")
    return proposals.with_suffix(".summary.json")


def read_summary(path: Path | None) -> dict[str, object]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8") or "{}")


def proposal_rows(summary: dict[str, object]) -> tuple[int | None, int | None]:
    rows = summary.get("proposal_rows")
    changes = summary.get("proposal_changes")
    return (
        int(rows) if isinstance(rows, int) else 0,
        int(changes) if isinstance(changes, int) else 0,
    )


def check_expectations(summary: dict[str, object], *, expect_rows: int | None, expect_changes: int | None) -> None:
    rows, changes = proposal_rows(summary)
    failures: list[str] = []
    if expect_rows is not None and rows != expect_rows:
        failures.append(f"expected proposal_rows={expect_rows}, saw {rows}")
    if expect_changes is not None and changes != expect_changes:
        failures.append(f"expected proposal_changes={expect_changes}, saw {changes}")
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        raise SystemExit(1)


def preview_indices(total: int, limit: int, mode: str) -> list[int]:
    if total <= 0 or limit <= 0:
        return []
    if mode == "head" or total <= limit:
        return list(range(min(total, limit)))
    if limit == 1:
        return [0]
    last = total - 1
    indexes = {round(index * last / (limit - 1)) for index in range(limit)}
    return sorted(indexes)


def preview_proposals(path: Path | None, limit: int, mode: str) -> None:
    if path is None or not path.exists() or limit <= 0:
        return
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    print(f"\nproposal preview {path} rows={len(rows)} mode={mode}")
    if not rows:
        return
    columns = [column for column in PREVIEW_COLUMNS if column in rows[0]]
    print("\t".join(columns))
    for index in preview_indices(len(rows), limit, mode):
        row = rows[index]
        print("\t".join(clip(row.get(column, "")) for column in columns))


def clip(value: object, limit: int = 140) -> str:
    text = str(value).replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def temporary_paths(script: Path) -> tuple[Path, Path]:
    safe_name = script.stem.replace("/", "_")
    return (
        Path("/tmp") / f"{safe_name}_idempotence_proposals.tsv",
        Path("/tmp") / f"{safe_name}_idempotence_summary.json",
    )


def verify_cmd(script: Path, targets: Iterable[str], *, skip_audit: bool, skip_spellcheck: bool) -> list[str]:
    cmd = [
        sys.executable,
        str(VERIFY_SCRIPT),
        "--rebuild-bootstrap",
        "--bump-cache",
        "--script",
        str(script),
        "--script",
        str(DASHBOARD_SCRIPT),
        "--script",
        str(VERIFY_SCRIPT),
    ]
    if skip_audit:
        cmd.append("--skip-audit")
    if skip_spellcheck:
        cmd.append("--skip-spellcheck")
    for target in targets:
        cmd.extend(["--target", target])
    return cmd


def dashboard_cmd(top: int) -> list[str]:
    return [sys.executable, str(DASHBOARD_SCRIPT), "--top", str(top)]


def current_tags() -> tuple[str, str]:
    index_text = Path("index.html").read_text(encoding="utf-8")
    sw_text = Path("sw.js").read_text(encoding="utf-8")
    bootstrap_tag = "missing-bootstrap-tag"
    cache_version = "missing-cache-version"
    for marker in index_text.split("data/bootstrap.js?v=")[1:2]:
        bootstrap_tag = marker.split('"', 1)[0].split("'", 1)[0]
    for marker in sw_text.split('CACHE_VERSION = "')[1:2]:
        cache_version = marker.split('"', 1)[0]
    return bootstrap_tag, cache_version


def append_journal(path: Path, *, script: Path, summary: dict[str, object], targets: list[str]) -> None:
    rows, changes = proposal_rows(summary)
    bootstrap_tag, cache_version = current_tags()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=JOURNAL_COLUMNS, lineterminator="\n")
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "script": str(script),
                "proposal_rows": rows,
                "proposal_changes": changes,
                "targets": " | ".join(targets),
                "bootstrap_tag": bootstrap_tag,
                "cache_version": cache_version,
            }
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True, type=Path, help="Normalizer script to run.")
    parser.add_argument("--apply", action="store_true", help="Write data, verify idempotence, and refresh browser payload.")
    parser.add_argument("--proposals", type=Path, help="Override the normalizer proposal TSV path.")
    parser.add_argument("--summary", type=Path, help="Override the normalizer summary JSON path.")
    parser.add_argument("--expect-rows", type=int, help="Fail if dry-run proposal_rows differs.")
    parser.add_argument("--expect-changes", type=int, help="Fail if dry-run proposal_changes differs.")
    parser.add_argument("--target", action="append", default=[], help="Verifier residue target, optionally Source::regex.")
    parser.add_argument("--preview", type=int, default=12, help="Proposal rows to print.")
    parser.add_argument("--preview-mode", choices=["spread", "head"], default="spread", help="How to sample proposal preview rows.")
    parser.add_argument("--journal", type=Path, default=JOURNAL_PATH, help="Append a successful apply-stage record to this TSV.")
    parser.add_argument("--no-journal", action="store_true", help="Do not append a successful apply-stage record.")
    parser.add_argument("--dashboard-top", type=int, default=20)
    parser.add_argument("--skip-audit", action="store_true")
    parser.add_argument("--skip-spellcheck", action="store_true")
    args = parser.parse_args()

    dry_output = run(
        normalizer_cmd(args.script, apply=False, proposals=args.proposals, summary=args.summary),
        label="dry run",
    )
    proposals_path = args.proposals or extract_proposals_path(dry_output)
    summary_path = args.summary or infer_summary_path(proposals_path)
    summary = read_summary(summary_path)
    print(f"\nsummary {summary_path}: {json.dumps(summary, ensure_ascii=False, sort_keys=True)}")
    check_expectations(summary, expect_rows=args.expect_rows, expect_changes=args.expect_changes)
    preview_proposals(proposals_path, args.preview, args.preview_mode)

    rows, _ = proposal_rows(summary)
    if not args.apply:
        print("\ndry-run only; pass --apply after reviewing proposals.")
        return 0
    if not rows:
        print("\nno proposals; skipped apply and verification.")
        return 0

    run(
        normalizer_cmd(args.script, apply=True, proposals=args.proposals, summary=args.summary),
        label="apply",
    )

    temp_proposals, temp_summary = temporary_paths(args.script)
    run(
        normalizer_cmd(args.script, apply=False, proposals=temp_proposals, summary=temp_summary),
        label="idempotence dry run",
    )
    idempotence_summary = read_summary(temp_summary)
    print(f"\nidempotence summary {temp_summary}: {json.dumps(idempotence_summary, ensure_ascii=False, sort_keys=True)}")
    check_expectations(idempotence_summary, expect_rows=0, expect_changes=0)

    run(
        verify_cmd(args.script, args.target, skip_audit=args.skip_audit, skip_spellcheck=args.skip_spellcheck),
        label="verify and refresh cache",
    )
    run(dashboard_cmd(args.dashboard_top), label="dashboard refresh")
    if not args.no_journal:
        append_journal(args.journal, script=args.script, summary=summary, targets=args.target)
        print(f"\nappended stage journal {args.journal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
