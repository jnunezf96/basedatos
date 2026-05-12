#!/usr/bin/env python3
"""Normalize verbal cana to ana using translation context.

`cana` is the adverbial "somewhere" form in the rendered data. Rows where the
Spanish translation is verbal (tomar, desenvainar, entresacar, etc.) belong to
`ana`, including cases introduced by earlier attached-marker cleanup.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
REPORT_PATH = Path("scripts/edition_cana_ana_context_report.jsonl")

FIXES = {
    # Molina / BNF rows where the original had nicana but the translation is verbal.
    "1571-molina-1:036113": ("cana", "ana", "tomar"),
    "1571-molina-1:036114": ("cana", "ana", "malo estar mucho / agonizar context"),
    "1571-molina-1:036115": ("cana", "ana", "desenvainar"),
    "1571-molina-1:036124": ("nihio cana", "nihio ana", "alentar"),
    "1571-molina-1:036125": ("nihio cana", "nihio ana", "alentar / tomar huelgo"),
    "1571-molina-1:036126": ("tetech cana", "tetech ana", "edificarse tomando ejemplo"),
    "1571-molina-1:036127": ("tetech cana", "tetech ana", "seguir o imitar"),
    "1571-molina-1:036128": ("itlan cana", "itlan ana", "entresacar"),
    "1571-molina-1:036129": ("itzalan cana", "itzalan ana", "entresacar"),
    "1571-molina-2:024113": ("cana", "ana", "tomar / comenzar / agonizar"),
    "1571-molina-2:024119": ("itlan cana", "itlan ana", "entresacar"),
    "1571-molina-2:024120": ("tetech cana", "tetech ana", "tomar ejemplo"),
    "1780-bnf-361:015068": ("nihio cana", "nihio ana", "alentar / tomar huelgo"),
    "1780-bnf-361:021252": ("tetech cana", "tetech ana", "edificarse / seguir o imitar"),
    "1780-bnf-361:028096": ("cana", "ana", "tomar"),
    "17-bnf-362:005118": ("cana", "ana", "tomar"),
    # Cortés y Zedeño already has nearby `conana acaxto -> ana acachto`;
    # these phrase rows share the same verbal tomar context.
    "1765-cortes-y-zedeno:001236": ("cana acachto", "ana acachto", "tomar primero"),
    "1765-cortes-y-zedeno:004719": ("cana ica ganancia", "ana ica ganancia", "tomar a logro"),
    "1765-cortes-y-zedeno:004720": ("cana ica tlaniliztli", "ana ica tlaniliztli", "tomar a logro"),
    "1765-cortes-y-zedeno:004721": ("cana ipan icargo", "ana ipan icargo", "tomar a su cargo"),
    "1765-cortes-y-zedeno:004722": (
        "cana para temacaz tlapohualiztli",
        "ana para temacaz tlapohualiztli",
        "tomar algo para dar cuenta",
    ),
}


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
    report_rows: list[dict[str, object]] = []

    for row in rows:
        record_id = str(row.get("record_id") or "")
        if record_id not in FIXES:
            continue
        expected, replacement, reason = FIXES[record_id]
        old = str(row.get("Texto estandarizado") or "")
        if old != expected:
            continue
        report_rows.append(
            {
                "record_id": record_id,
                "source": row.get("Fuente"),
                "original": row.get("Escritura original"),
                "old_edition": old,
                "new_edition": replacement,
                "translation": row.get("Traducción"),
                "reason": reason,
            }
        )
        if args.apply:
            row["Texto estandarizado"] = replacement

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        for report_row in report_rows:
            f.write(json.dumps(report_row, ensure_ascii=False, separators=(",", ":")) + "\n")

    if args.apply and report_rows:
        write_rows(rows)

    print(json.dumps({"apply": args.apply, "changed_rows": len(report_rows), "report": str(REPORT_PATH)}, indent=2))


if __name__ == "__main__":
    main()
