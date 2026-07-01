#!/usr/bin/env python3
"""Repair Sahagun Escolios target numbers from displayed witness/gloss apparatus."""

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
PROPOSALS_PATH = Path("resources/sahagun_target_number_from_public_apparatus_proposals.tsv")
SUMMARY_PATH = Path("resources/sahagun_target_number_from_public_apparatus_summary.json")
MARKER = "sahagun_target_number_from_public_apparatus_repair_2026_06_29"


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


def target_missing_ids(audit_path: Path) -> set[str]:
    ids: set[str] = set()
    with audit_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("issue_type") == "target_number_missing_from_witness":
                ids.add(row.get("record_id", ""))
    return ids


def adjacent_text_for_number(row: dict, number: int) -> str:
    text = coherence.clean_space(coherence.html_to_text(coherence.public_witness_html(row)))
    span = coherence.target_number_adjacent_span(text, number)
    return text[span[0] : span[1]] if span else ""


def candidate_for_number(row: dict, number: int) -> dict[str, str] | None:
    adjacent_text = adjacent_text_for_number(row, number)
    if not adjacent_text:
        return None
    gloss = coherence.public_gloss_text_for_number(row, number)
    translation_overlap = coherence.text_words(row.get("Traducción", "")) & coherence.text_words(gloss)
    row_form_similarity = coherence.form_similarity(coherence.target_forms(row), adjacent_text)
    gloss_forms = {form for form in coherence.forms_from_value(gloss) if len(form) >= 4}
    gloss_form_similarity = coherence.form_similarity(gloss_forms, adjacent_text) if gloss_forms else 0.0

    evidence = ""
    if row_form_similarity >= 0.95:
        evidence = "adjacent_witness_form_matches_row_form"
    elif translation_overlap and gloss_form_similarity >= 0.95:
        evidence = "adjacent_witness_form_matches_target_gloss_form_and_translation"
    else:
        return None

    return {
        "new_target_number": str(number),
        "adjacent_text": adjacent_text,
        "row_form_similarity": f"{row_form_similarity:.3f}",
        "gloss_form_similarity": f"{gloss_form_similarity:.3f}",
        "translation_overlap": ",".join(sorted(translation_overlap)),
        "new_target_gloss": gloss,
        "evidence": evidence,
    }


def proposal_for_row(row: dict) -> dict[str, str] | None:
    old_number = coherence.target_number(row)
    if old_number is None:
        return None
    public_numbers = coherence.public_witness_numbers(row) & coherence.public_gloss_numbers(row)
    if old_number in public_numbers:
        return None
    candidates = [candidate for number in sorted(public_numbers) if (candidate := candidate_for_number(row, number))]
    if len(candidates) != 1:
        return None
    candidate = candidates[0]
    return {
        "record_id": row.get("record_id", ""),
        "original": row.get("Original", ""),
        "editado": row.get("Editado", ""),
        "old_target_number": str(old_number),
        "old_target_gloss": coherence.public_gloss_text_for_number(row, old_number),
        "translation": row.get("Traducción", ""),
        **candidate,
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

    metadata["qa_target_number_from_public_apparatus_repair_2026_06_29"] = {
        "action": "changed_target_number_to_displayed_witness_gloss_number",
        "marker": MARKER,
        "old_target_number_base": old_number,
        "old_target_number_raw": old_raw,
        "new_target_number_base": new_number,
        "new_target_number_raw": str(new_number),
        "adjacent_text": proposal["adjacent_text"],
        "evidence": proposal["evidence"],
        "translation_overlap": proposal["translation_overlap"].split(",") if proposal["translation_overlap"] else [],
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
    ids = target_missing_ids(args.audit)
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
            "adjacent_text",
            "evidence",
            "row_form_similarity",
            "gloss_form_similarity",
            "translation_overlap",
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
