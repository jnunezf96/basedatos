#!/usr/bin/env python3
"""Repair high-confidence Sahagun Escolios public target highlights."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import repair_sahagun_internal_coherence as coherence


DATA_PATH = Path("data/data.jsonl.gz")
AUDIT_PATH = Path("resources/sahagun_internal_coherence_audit.tsv")
PROPOSALS_PATH = Path("resources/sahagun_bold_highlight_repair_proposals.tsv")
REVIEW_PATH = Path("resources/sahagun_bold_highlight_repair_review.tsv")
SUMMARY_PATH = Path("resources/sahagun_bold_highlight_repair_summary.json")
MARKER = "sahagun_bold_highlight_repair_2026_06_29"
FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
TARGET_ISSUES = {
    "bold_nearest_number_mismatch",
    "bold_text_no_target_token_overlap",
    "no_bold_in_comentario",
}

BOLD_STRIP_RE = re.compile(r"</?b\b[^>]*>", re.I)


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


def target_issue_ids(audit_path: Path) -> dict[str, set[str]]:
    issue_ids: dict[str, set[str]] = defaultdict(set)
    with audit_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("issue_type") in TARGET_ISSUES:
                issue_ids[row.get("record_id", "")].add(row["issue_type"])
    return issue_ids


def public_gloss_text_for_number(row: dict, number: int) -> str:
    gloss_html = coherence.public_gloss_html(row)
    for match in coherence.PUBLIC_GLOSS_LINE_RE.finditer(gloss_html):
        if int(match.group(1)) == number:
            return coherence.clean_space(coherence.html_to_text(match.group(2)))
    return ""


def target_gloss_translation_overlap(row: dict, number: int) -> tuple[set[str], str]:
    gloss_text = public_gloss_text_for_number(row, number)
    overlap = coherence.text_words(row.get("Traducción", "")) & coherence.text_words(gloss_text)
    return overlap, gloss_text


def rehighlight_commentary(value: object, row: dict, number: int) -> str:
    text = str(value or "")
    marker = "Glosas relevantes del escolio:"
    if marker not in text:
        return text
    witness_html, gloss_html = text.split(marker, 1)
    unbolded_witness = BOLD_STRIP_RE.sub("", witness_html)
    highlighted_witness = coherence.bold_target(unbolded_witness, row, number)
    return highlighted_witness + marker + gloss_html


def bolds_in_public_witness(row: dict) -> list[str]:
    return [
        coherence.clean_space(coherence.html_to_text(match.group(1)))
        for match in coherence.BOLD_RE.finditer(coherence.public_witness_html(row))
    ]


def bold_key_length(value: str) -> int:
    return len(coherence.form_key(value))


def bolds_have_target_form_overlap(row: dict, bolds: list[str]) -> bool:
    forms = coherence.target_forms(row)
    return bool(forms) and any(coherence.form_similarity(forms, bold) >= 0.82 for bold in bolds)


def bolds_have_target_gloss_form_overlap(target_gloss: str, bolds: list[str]) -> bool:
    forms = {form for form in coherence.forms_from_value(target_gloss) if len(form) >= 4}
    return bool(forms) and any(coherence.form_similarity(forms, bold) >= 0.82 for bold in bolds)


def remaining_target_bold_issues(row: dict) -> list[str]:
    return [
        audit["issue_type"]
        for audit in coherence.audit_rows([row])
        if audit["issue_type"] in TARGET_ISSUES
    ]


def maybe_repair_row(row: dict, issues: set[str]) -> tuple[dict | None, dict[str, str] | None, dict[str, str] | None]:
    number = coherence.target_number(row)
    if number is None:
        return None, None, {
            "record_id": row.get("record_id", ""),
            "original": row.get("Original", ""),
            "editado": row.get("Editado", ""),
            "target_number": "",
            "issues": ";".join(sorted(issues)),
            "reason": "missing_target_number",
            "target_gloss": "",
            "translation": row.get("Traducción", ""),
        }

    if number not in coherence.public_witness_numbers(row) or number not in coherence.public_gloss_numbers(row):
        return None, None, {
            "record_id": row.get("record_id", ""),
            "original": row.get("Original", ""),
            "editado": row.get("Editado", ""),
            "target_number": str(number),
            "issues": ";".join(sorted(issues)),
            "reason": "target_number_missing_from_public_witness_or_gloss",
            "target_gloss": public_gloss_text_for_number(row, number),
            "translation": row.get("Traducción", ""),
        }

    overlap, target_gloss = target_gloss_translation_overlap(row, number)

    repaired = json.loads(json.dumps(row, ensure_ascii=False))
    changed_fields: list[str] = []
    previous_commentary = str(row.get("Comentario", ""))
    before_bolds = bolds_in_public_witness(row)

    for field in FIELDS:
        if not repaired.get(field):
            continue
        new_value = rehighlight_commentary(repaired[field], repaired, number)
        if new_value != repaired[field]:
            repaired[field] = new_value
            changed_fields.append(field)

    metadata = repaired.get("Sahagun_Escolios_JSON") if isinstance(repaired.get("Sahagun_Escolios_JSON"), dict) else {}
    display = metadata.get("display") if isinstance(metadata.get("display"), dict) else {}
    if display.get("html"):
        new_html = rehighlight_commentary(display["html"], repaired, number)
        if new_html != display["html"]:
            display["html"] = new_html
            changed_fields.append("Sahagun_Escolios_JSON.display.html")
        display["issues"] = append_marker(display.get("issues"), MARKER)
        metadata["display"] = display

    remaining = remaining_target_bold_issues(repaired)
    if remaining:
        return None, None, {
            "record_id": row.get("record_id", ""),
            "original": row.get("Original", ""),
            "editado": row.get("Editado", ""),
            "target_number": str(number),
            "issues": ";".join(sorted(issues)),
            "reason": "repair_did_not_clear_target_bold_issues:" + ";".join(remaining),
            "target_gloss": target_gloss,
            "translation": row.get("Traducción", ""),
        }

    if not changed_fields:
        return None, None, {
            "record_id": row.get("record_id", ""),
            "original": row.get("Original", ""),
            "editado": row.get("Editado", ""),
            "target_number": str(number),
            "issues": ";".join(sorted(issues)),
            "reason": "no_public_field_changed",
            "target_gloss": target_gloss,
            "translation": row.get("Traducción", ""),
        }

    after_bolds = bolds_in_public_witness(repaired)
    if not after_bolds or any(bold_key_length(bold) <= 2 for bold in after_bolds):
        return None, None, {
            "record_id": row.get("record_id", ""),
            "original": row.get("Original", ""),
            "editado": row.get("Editado", ""),
            "target_number": str(number),
            "issues": ";".join(sorted(issues)),
            "reason": "after_bold_span_too_short_for_high_confidence",
            "target_gloss": target_gloss,
            "translation": row.get("Traducción", ""),
        }

    target_form_supported = bolds_have_target_form_overlap(row, after_bolds)
    target_gloss_form_supported = bolds_have_target_gloss_form_overlap(target_gloss, after_bolds)
    if not (target_form_supported or target_gloss_form_supported):
        return None, None, {
            "record_id": row.get("record_id", ""),
            "original": row.get("Original", ""),
            "editado": row.get("Editado", ""),
            "target_number": str(number),
            "issues": ";".join(sorted(issues)),
            "reason": "after_bold_target_form_overlap_missing_for_data_repair",
            "target_gloss": target_gloss,
            "translation": row.get("Traducción", ""),
        }

    metadata["qa_bold_highlight_repair_2026_06_29"] = {
        "action": "repaired_public_target_highlight_in_existing_commentary",
        "marker": MARKER,
        "target_number_base": number,
        "issues": sorted(issues),
        "target_gloss_translation_overlap": sorted(overlap),
        "target_form_supported": target_form_supported,
        "target_gloss_form_supported": target_gloss_form_supported,
        "previous_commentary_sha1": hashlib.sha1(previous_commentary.encode("utf-8")).hexdigest(),
    }
    repaired["Sahagun_Escolios_JSON"] = metadata
    repaired["Comentario_display_issues"] = append_marker(repaired.get("Comentario_display_issues"), MARKER)

    proposal = {
        "record_id": row.get("record_id", ""),
        "original": row.get("Original", ""),
        "editado": row.get("Editado", ""),
        "target_number": str(number),
        "issues": ";".join(sorted(issues)),
        "gloss_overlap": ",".join(sorted(overlap)),
        "form_support": "target_form" if target_form_supported else "target_gloss_form",
        "changed_fields": ";".join(changed_fields),
        "before_bolds": "; ".join(before_bolds),
        "after_bolds": "; ".join(after_bolds),
        "target_gloss": target_gloss,
        "witness_after": coherence.clean_space(coherence.html_to_text(coherence.public_witness_html(repaired)))[:500],
    }
    return repaired, proposal, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--audit", type=Path, default=AUDIT_PATH)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--review", type=Path, default=REVIEW_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    issues_by_id = target_issue_ids(args.audit)
    proposals: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for index, row in enumerate(rows):
        if row.get("Fuente") != coherence.SOURCE:
            continue
        record_id = row.get("record_id", "")
        issues = issues_by_id.get(record_id)
        if not issues:
            continue
        repaired, proposal, review_row = maybe_repair_row(row, issues)
        if proposal:
            counts["proposal_rows"] += 1
            proposals.append(proposal)
            if args.apply and repaired:
                rows[index] = repaired
                counts["applied_rows"] += 1
        if review_row:
            counts["review_rows"] += 1
            review.append(review_row)

    write_tsv(
        args.proposals,
        proposals,
        [
            "record_id",
            "original",
            "editado",
            "target_number",
            "issues",
            "gloss_overlap",
            "form_support",
            "changed_fields",
            "before_bolds",
            "after_bolds",
            "target_gloss",
            "witness_after",
        ],
    )
    write_tsv(
        args.review,
        review,
        ["record_id", "original", "editado", "target_number", "issues", "reason", "target_gloss", "translation"],
    )
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.apply and proposals:
        write_rows(args.data, rows)

    print("summary", dict(counts))
    print("proposals", args.proposals)
    print("review", args.review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
