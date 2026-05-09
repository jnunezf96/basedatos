#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
REPORT_PATH = Path("scripts/spanish_row_specific_context_report.jsonl")


REPLACEMENTS: dict[str, list[tuple[str, str, str]]] = {
    # "metalado" is not one correction globally. Parallel rows split it by lemma.
    "1571-molina-1:000938": [
        (
            "metalado.",
            "metalado (arcaico: mellado o resquebrajado).",
            "tlatlapanqui parallels: resquebrajado / cosa hecha pedazos",
        )
    ],
    "1780-bnf-361:000902": [
        (
            "metalado",
            "metalado (arcaico: mellado o resquebrajado)",
            "tlatlapanqui parallels: resquebrajado / cosa hecha pedazos",
        )
    ],
    "1571-molina-1:007735": [
        (
            "metalado.",
            "metalado (arcaico: ametalado, compuesto de diversos metales).",
            "chichictlapanqui parallels: ametalado / compuesto de diversos metales",
        )
    ],
    "1571-molina-1:007935": [
        (
            "metalado.",
            "metalado (arcaico: ametalado, compuesto de varias piezas).",
            "chictlapanqui parallels: ametalado / compuesto de varias piezas",
        )
    ],
    "153-trilingue:009466": [
        (
            "metalado cosa de metal.",
            "metalado (arcaico: metálico) cosa de metal.",
            "tepozo context says cosa de metal",
        )
    ],
    # "sequera" is an old/source adjective here, not "ceguera".
    "1571-molina-1:028057": [
        (
            "sequera cosa de sequero.",
            "sequera (arcaico: seca, de sequero) cosa de sequero.",
            "tepepammochihua dryland/sequero context",
        )
    ],
    "1780-bnf-361:020624": [
        (
            "sequera, cosa de sequera.",
            "sequera (arcaico: seca, de sequero).",
            "tepepammochihua dryland/sequero context",
        )
    ],
    "1571-molina-1:033729": [
        (
            "sequera cosa de sequero.",
            "sequera (arcaico: seca, de sequero) cosa de sequero.",
            "tlalhuaccapammochihua dryland/sequero context",
        )
    ],
    "1780-bnf-361:025699": [
        (
            "sequera cosa de vequero.",
            "sequera (arcaico: seca, de sequero) cosa de sequero.",
            "tlalhuaccapammochihua dryland/sequero context; vequero corrected to sequero",
        )
    ],
}


def iter_rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)


def write_rows(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=9) as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    tmp.replace(path)


def translation_field(row: dict) -> str | None:
    if row.get("Fuente") == "2021 Wimmer":
        return "Traducción (es)" if "Traducción (es)" in row else None
    return "Traducción" if "Traducción" in row else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    rows = []
    reports = []
    counts: Counter[str] = Counter()

    for row in iter_rows(args.data):
        record_id = row.get("record_id")
        field = translation_field(row)
        if record_id in REPLACEMENTS and field and isinstance(row.get(field), str):
            old_value = row[field]
            new_value = old_value
            row_reports = []
            for old, new, reason in REPLACEMENTS[record_id]:
                if new in new_value:
                    continue
                if old in new_value:
                    new_value = new_value.replace(old, new, 1)
                    counts[record_id] += 1
                    row_reports.append({"old_fragment": old, "new_fragment": new, "reason": reason})
            if new_value != old_value:
                reports.append(
                    {
                        "record_id": record_id,
                        "Fuente": row.get("Fuente"),
                        "Lema": row.get("Texto estandarizado") or row.get("Lema"),
                        "field": field,
                        "old": old_value,
                        "new": new_value,
                        "changes": row_reports,
                    }
                )
                if args.apply:
                    row[field] = new_value
        rows.append(row)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as fh:
        for report in reports:
            fh.write(json.dumps(report, ensure_ascii=False) + "\n")

    print(f"mode={'apply' if args.apply else 'dry-run'}")
    print(f"changed_rows={len(reports)}")
    print(f"report={args.report}")
    for record_id, count in counts.most_common():
        print(f"{record_id}\t{count}")

    if args.apply:
        write_rows(args.data, rows)


if __name__ == "__main__":
    main()
