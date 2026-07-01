#!/usr/bin/env python3
"""Repair Sahagun Escolios target numbers when bold evidence is stronger."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import repair_sahagun_internal_coherence as coherence


DATA_PATH = Path("data/data.jsonl.gz")
AUDIT_PATH = Path("resources/sahagun_internal_coherence_audit.tsv")
PROPOSALS_PATH = Path("resources/sahagun_target_number_from_bold_proposals.tsv")
SUMMARY_PATH = Path("resources/sahagun_target_number_from_bold_summary.json")
MARKER = "sahagun_target_number_from_bold_repair_2026_06_29"


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


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_marker(value: object, marker: str) -> list[str]:
    if isinstance(value, list):
        items = [str(item) for item in value]
    elif value:
        items = [str(value)]
    else:
        items = []
    if marker not in items:
        items.append(marker)
    return items


def bold_mismatch_ids(audit_path: Path) -> set[str]:
    ids: set[str] = set()
    with audit_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("issue_type") == "bold_nearest_number_mismatch":
                ids.add(row.get("record_id", ""))
    return ids


def proposal_for_row(row: dict) -> dict[str, str] | None:
    old_number = coherence.target_number(row)
    if old_number is None:
        return None
    nearests = coherence.bold_nearest_numbers(row)
    if len(nearests) != 1:
        return None
    bold_text, new_number = nearests[0]
    if new_number is None or new_number == old_number:
        return None
    if coherence.form_similarity(coherence.target_forms(row), bold_text) < 0.82:
        return None

    old_gloss = coherence.public_gloss_text_for_number(row, old_number)
    new_gloss = coherence.public_gloss_text_for_number(row, new_number)
    old_overlap = coherence.text_words(row.get("Traducción", "")) & coherence.text_words(old_gloss)
    new_overlap = coherence.text_words(row.get("Traducción", "")) & coherence.text_words(new_gloss)
    if old_overlap or not new_overlap:
        return None

    return {
        "record_id": row.get("record_id", ""),
        "original": row.get("Original", ""),
        "editado": row.get("Editado", ""),
        "old_target_number": str(old_number),
        "new_target_number": str(new_number),
        "bold_text": bold_text,
        "new_gloss_overlap": ",".join(sorted(new_overlap)),
        "old_target_gloss": old_gloss,
        "new_target_gloss": new_gloss,
        "translation": row.get("Traducción", ""),
    }


def apply_proposal(row: dict, proposal: dict[str, str]) -> None:
    old_number = int(proposal["old_target_number"])
    new_number = int(proposal["new_target_number"])
    metadata = row.get("Sahagun_Escolios_JSON") if isinstance(row.get("Sahagun_Escolios_JSON"), dict) else {}
    old_raw = metadata.get("target_number_raw") or str(old_number)
    previous_alignment = metadata.get("target_alignment_v34_1") if isinstance(metadata.get("target_alignment_v34_1"), dict) else {}

    metadata["target_number_base"] = new_number
    metadata["target_number_raw"] = str(new_number)
    alignment = metadata.setdefault("target_alignment_v34_1", {})
    alignment["number_base"] = new_number
    alignment["number_raw"] = str(new_number)
    alignment["repair_policy"] = MARKER

    display = metadata.get("display") if isinstance(metadata.get("display"), dict) else {}
    if display:
        display["issues"] = append_marker(display.get("issues"), MARKER)
        metadata["display"] = display

    metadata["qa_target_number_from_bold_repair_2026_06_29"] = {
        "action": "changed_target_number_to_existing_bold_nearest_number",
        "marker": MARKER,
        "old_target_number_base": old_number,
        "old_target_number_raw": old_raw,
        "new_target_number_base": new_number,
        "new_target_number_raw": str(new_number),
        "bold_text": proposal["bold_text"],
        "new_gloss_overlap": proposal["new_gloss_overlap"].split(",") if proposal["new_gloss_overlap"] else [],
        "old_target_gloss": proposal["old_target_gloss"],
        "new_target_gloss": proposal["new_target_gloss"],
        "previous_alignment_sha1": hashlib.sha1(
            json.dumps(previous_alignment, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }
    row["Sahagun_Escolios_JSON"] = metadata
    row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--audit", type=Path, default=AUDIT_PATH)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    ids = bold_mismatch_ids(args.audit)
    proposals: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in rows:
        if row.get("Fuente") != coherence.SOURCE or row.get("record_id", "") not in ids:
            continue
        proposal = proposal_for_row(row)
        if not proposal:
            continue
        proposals.append(proposal)
        counts["proposal_rows"] += 1
        if args.apply:
            apply_proposal(row, proposal)
            counts["applied_rows"] += 1

    write_tsv(
        args.proposals,
        proposals,
        [
            "record_id",
            "original",
            "editado",
            "old_target_number",
            "new_target_number",
            "bold_text",
            "new_gloss_overlap",
            "old_target_gloss",
            "new_target_gloss",
            "translation",
        ],
    )
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.apply and proposals:
        write_rows(args.data, rows)

    print("summary", dict(counts))
    print("proposals", args.proposals)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
