#!/usr/bin/env python3
"""Normalize old Nahuatl `vel` while preserving Latin `vel`.

Rendered `Texto estandarizado` should use Nahuatl `huel`/related normalized
forms, but Latin separator `vel` ("or") should remain `vel`. This pass handles
both directions:

- old Nahuatl vel -> huel (or evidenced compound forms)
- mistakenly rendered Latin separator huel -> vel
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import unicodedata
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
REPORT_PATH = Path("scripts/edition_vel_huel_report.jsonl")


FIELD = "Texto estandarizado"

CURATED = {
    "1571-molina-1:009491": ("velipanyotl cualcan", "huelipanyotl cualcan", "attested huelipanyotl"),
    "1571-molina-1:010595": ("velica cuicatl", "huelica cuicatl", "attested huelica"),
    "1571-molina-2:009107": ("ocvel ichpochtli", "oc huel ichpochtli", "oc huel phrase"),
    "1571-molina-1:013756": ("tetechvelca in noyollo", "tetech huelca in noyollo", "attested tetech huelca"),
    "1571-molina-1:013757": ("tetechvelca in noyollo", "tetech huelca in noyollo", "attested tetech huelca"),
    "1571-molina-2:010124": ("macanvel ipan", "ma zan huel ipan", "ma zan + huel phrase"),
    "1571-molina-1:017747": ("temacvel miquiliztli", "temac huel miquiliztli", "temac + huel phrase"),
}

CURATED_CORRECTIONS = {
    "1571-molina-2:010124": ("mazan huel ipan", "ma zan huel ipan", "correct earlier ma zan spacing"),
    "1571-molina-1:017747": ("temacuel miquiliztli", "temac huel miquiliztli", "correct earlier temac huel split"),
}


def fold(text: str) -> str:
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower()


def is_latin_vel_separator(original: str, edition: str) -> bool:
    original_folded = fold(original)
    edition_folded = fold(edition)
    if "vide " in edition_folded or "vide " in original_folded:
        return True
    return bool(re.search(r",\s*vel\s*,|,\s*vel\s+", original_folded))


def restore_latin_vel(text: str) -> str:
    text = re.sub(r"/\s*huel\s*/", "/ vel/ ", text)
    text = re.sub(r",\s*huel\s+", ", vel ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def nahuatl_vel_to_huel(text: str) -> str:
    return re.sub(r"\bvel\b", "huel", text)


def read_rows() -> list[dict[str, object]]:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def write_rows(rows: list[dict[str, object]]) -> None:
    with gzip.open(DATA_PATH, "wt", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = read_rows()
    report_rows = []

    for row in rows:
        record_id = str(row.get("record_id") or "")
        original = str(row.get("Escritura original") or "")
        old = str(row.get(FIELD) or "")
        new = old
        reasons: list[str] = []

        if is_latin_vel_separator(original, old):
            restored = restore_latin_vel(new)
            if restored != new:
                new = restored
                reasons.append("latin_vel_separator")
            # Do not then convert Latin vel to Nahuatl huel.
        else:
            converted = nahuatl_vel_to_huel(new)
            if converted != new:
                new = converted
                reasons.append("nahuatl_vel_token")

        if record_id in CURATED:
            expected, replacement, reason = CURATED[record_id]
            if new == expected:
                new = replacement
                reasons.append(reason)
            elif old == expected:
                new = replacement
                reasons.append(reason)

        if record_id in CURATED_CORRECTIONS:
            expected, replacement, reason = CURATED_CORRECTIONS[record_id]
            if new == expected:
                new = replacement
                reasons.append(reason)
            elif old == expected:
                new = replacement
                reasons.append(reason)

        if new != old:
            report_rows.append(
                {
                    "record_id": record_id,
                    "source": row.get("Fuente"),
                    "original": original,
                    "old_edition": old,
                    "new_edition": new,
                    "translation": row.get("Traducción"),
                    "reasons": reasons,
                }
            )
            if args.apply:
                row[FIELD] = new

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        for report_row in report_rows:
            f.write(json.dumps(report_row, ensure_ascii=False, separators=(",", ":")) + "\n")

    if args.apply and report_rows:
        write_rows(rows)

    print(json.dumps({"apply": args.apply, "changed_rows": len(report_rows), "report": str(REPORT_PATH)}, indent=2))


if __name__ == "__main__":
    main()
