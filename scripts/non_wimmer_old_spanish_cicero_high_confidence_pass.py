#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
PROPOSALS_PATH = ROOT / "scripts" / "agent_cicero_modern_help_proposals.jsonl"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_cicero_high_confidence_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"

ALLOWED_TOKENS = {
    "abrazamiento",
    "abundoso",
    "baldonar",
    "baptismo",
    "bruñeta",
    "enaguazar",
}

EXCLUDED_SOURCES = {"2021 Wimmer", "1992 Karttunen"}


def load_updates() -> dict[str, dict[str, str]]:
    updates: dict[str, dict[str, str]] = {}
    with PROPOSALS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            if item.get("confidence") != "high":
                continue
            if item.get("token") not in ALLOWED_TOKENS:
                continue
            record_id = item.get("record_id")
            if not record_id:
                continue
            updates[record_id] = {
                "old": item.get("old_translation") or "",
                "new": item.get("proposed_translation") or "",
                "token": item.get("token") or "",
            }
    return updates


def main() -> None:
    updates = load_updates()
    rows = []
    report = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            record_id = row.get("record_id") or ""
            update = updates.get(record_id)
            if update and row.get("Fuente") not in EXCLUDED_SOURCES:
                old = row.get("Traducción") or ""
                if old == update["old"] and old != update["new"]:
                    row["Traducción"] = update["new"]
                    report.append(
                        {
                            "record_id": record_id,
                            "source": row.get("Fuente"),
                            "lemma": row.get("Texto estandarizado"),
                            "token": update["token"],
                            "old": old,
                            "new": update["new"],
                        }
                    )
            rows.append(row)

    if not DRY_RUN:
        tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        os.replace(tmp, DATA_PATH)

        with REPORT_PATH.open("w", encoding="utf-8") as fh:
            for item in report:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"candidate_updates={len(updates)}")
    print(f"changed_rows={len(report)}")
    print(f"report={REPORT_PATH if not DRY_RUN else '(dry-run)'}")


if __name__ == "__main__":
    main()
