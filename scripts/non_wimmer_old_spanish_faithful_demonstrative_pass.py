#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
SOURCE_REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_qu_residual_report.jsonl"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_faithful_demonstrative_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇçÕõ"
WORD_RE = re.compile(rf"[{LETTER}]+")

DEMONSTRATIVES: dict[str, str] = {
    "aquesa": "esa",
    "aquese": "ese",
    "aqueso": "eso",
    "aqauesto": "esto",
    "aquesta": "esta",
    "aquestas": "estas",
    "aqueste": "este",
    "aquesto": "esto",
    "aquestos": "estos",
}

DISPLAY_FORM: dict[str, str] = {
    "aqauesto": "aquesto",
}


def words(value: str) -> list[re.Match[str]]:
    return list(WORD_RE.finditer(value or ""))


def display_old_form(old_token: str) -> str:
    lower = old_token.lower()
    display = DISPLAY_FORM.get(lower, old_token)
    if old_token[:1].isupper():
        return display[:1].upper() + display[1:]
    return display


def annotated_old_form(old_token: str) -> str:
    lower = old_token.lower()
    modern = DEMONSTRATIVES[lower]
    return f"{display_old_form(old_token)} (arcaico: {modern})"


def restore_from_report(current: str, old_report: str, new_report: str) -> tuple[str, list[dict[str, object]], str | None]:
    if "(arcaico:" in (current or ""):
        return current, [], "already_annotated"

    old_words = words(old_report)
    new_words = words(new_report)
    current_words = words(current)

    if len(old_words) != len(new_words) or len(new_words) != len(current_words):
        return current, [], "word_count_mismatch"

    replacements: list[dict[str, object]] = []
    for index, old_match in enumerate(old_words):
        old_token = old_match.group(0)
        lower = old_token.lower()
        if lower not in DEMONSTRATIVES:
            continue

        expected_modern = DEMONSTRATIVES[lower]
        report_modern = new_words[index].group(0).lower()
        current_token = current_words[index].group(0)
        current_lower = current_token.lower()
        if report_modern != expected_modern or current_lower != expected_modern:
            return current, [], "alignment_mismatch"

        replacements.append(
            {
                "index": index,
                "old_token": old_token,
                "current_token": current_token,
                "modern": expected_modern,
                "start": current_words[index].start(),
                "end": current_words[index].end(),
                "replacement": annotated_old_form(old_token),
            }
        )

    if not replacements:
        return current, [], "no_demonstratives"

    updated = current
    for item in reversed(replacements):
        start = int(item["start"])
        end = int(item["end"])
        updated = updated[:start] + str(item["replacement"]) + updated[end:]

    return updated, replacements, None


def main() -> None:
    report_inputs = {}
    with SOURCE_REPORT_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            report_inputs[item["record_id"]] = item

    rows = []
    report = []
    skipped = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            record_id = row.get("record_id") or ""
            source_item = report_inputs.get(record_id)
            if source_item:
                old = row.get("Traducción") or ""
                new, replacements, skip_reason = restore_from_report(
                    old,
                    source_item.get("old_translation") or "",
                    source_item.get("new_translation") or "",
                )
                if new != old:
                    row["Traducción"] = new
                    report.append(
                        {
                            "record_id": record_id,
                            "source": row.get("Fuente"),
                            "lemma": row.get("Texto estandarizado"),
                            "old_translation": old,
                            "new_translation": new,
                            "replacements": [
                                {
                                    "index": item["index"],
                                    "old_token": item["old_token"],
                                    "current_token": item["current_token"],
                                    "modern": item["modern"],
                                    "replacement": item["replacement"],
                                }
                                for item in replacements
                            ],
                        }
                    )
                elif skip_reason and skip_reason != "already_annotated":
                    skipped.append(
                        {
                            "record_id": record_id,
                            "source": row.get("Fuente"),
                            "lemma": row.get("Texto estandarizado"),
                            "reason": skip_reason,
                            "current_translation": old,
                            "report_old_translation": source_item.get("old_translation"),
                            "report_new_translation": source_item.get("new_translation"),
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

        skipped_path = REPORT_PATH.with_name(REPORT_PATH.stem + "_skipped.jsonl")
        with skipped_path.open("w", encoding="utf-8") as fh:
            for item in skipped:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(report)}")
    print(f"skipped_rows={len(skipped)}")
    print(f"report={REPORT_PATH if not DRY_RUN else '(dry-run)'}")


if __name__ == "__main__":
    main()
