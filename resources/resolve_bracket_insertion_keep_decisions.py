#!/usr/bin/env python3
"""Mark bracketed insertion/gloss review rows as keep decisions."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


QUEUE_PATH = Path("resources/source_cleanup_decision_queue.tsv")
SUMMARY_PATH = Path("resources/bracket_insertion_keep_decision_summary.json")

KEEP_TOKENS: dict[tuple[str, str], str] = {
    ("1551-95 Documentos nahuas de la Ciudad de México", "[Topilaneuc]"): "contextual insertion after Anton, not a correction of the preceding spelling",
    ("1551-95 Documentos nahuas de la Ciudad de México", "[Mauitoca]"): "contextual insertion after Joseph, not a correction of the preceding spelling",
    ("1551-95 Documentos nahuas de la Ciudad de México", "[yahualtic]"): "supplied/contextual term inside the sentence, not an immediate spelling correction",
    ("1551-95 Documentos nahuas de la Ciudad de México", "[yematl]"): "supplied/contextual term inside a damaged bracketed span, not an immediate spelling correction",
    ("1551-95 Documentos nahuas de la Ciudad de México", "[noxhuiuh]"): "supplied kinship term in the sentence, not an immediate spelling correction",
    ("1629 Alarcón", "[MAGUEYES]"): "Spanish supplied subject in prose, not a correction of preceding spelling",
    ("1759 Paredes", "[tonaloyan]"): "contextual supplied/related form after necencuiltonoloyan, not an immediate spelling correction",
    ("2021 Wimmer", "[acanalada]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[agua]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[acuática]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[cobre]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[cruzadas]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[cuadrado]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[es]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[guerreros]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[maguey]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[mosaico]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[pieles]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[placa]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[quiquiztli]"): "Nahuatl term supplied inside Wimmer gloss prose, not source spelling correction",
    ("2021 Wimmer", "[resina]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[seca]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[tlacualli]"): "Nahuatl term supplied inside Wimmer gloss prose, not source spelling correction",
    ("2021 Wimmer", "[y]"): "Spanish supplied translation word, not source spelling correction",
    ("2021 Wimmer", "[águila]"): "Spanish supplied translation word, not source spelling correction",
}


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    fields, rows = read_tsv(QUEUE_PATH)
    counts: Counter[str] = Counter()
    for row in rows:
        counts["queue_rows"] += 1
        key = (row.get("source", ""), row.get("token", ""))
        note = KEEP_TOKENS.get(key)
        if not note:
            continue
        row["decision"] = "keep"
        row["replacement"] = ""
        row["decision_notes"] = f"bracket_insertion_keep: {note}"
        counts["marked_keep"] += 1
        counts[f"marked_keep:{key[0]}"] += 1

    write_tsv(QUEUE_PATH, fields, rows)
    SUMMARY_PATH.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"summary {dict(counts)}")
    print(f"queue {QUEUE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
