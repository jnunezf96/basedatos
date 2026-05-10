#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import re
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
REPORT_PATH = Path("scripts/rendered_spanish_easy_spelling_report.jsonl")

LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
BOLD_SPAN_RE = re.compile(r"(<b\b[^>]*>.*?</b>)", re.I | re.S)


# Rendered Spanish fields only. These are old Spanish spellings that are not
# lexical archaisms; modernizing them does not change the source sense.
TOKEN_REPLACEMENTS = {
    "escribi": "escribí",
    "escribiras": "escribirás",
    "escrebir": "escribir",
    "escreuir": "escribir",
    "escreuirlo": "escribirlo",
    "escrevjr": "escribir",
    "escrevir": "escribir",
    "escreví": "escribí",
    "escripta": "escrita",
    "escripto": "escrito",
    "escriptor": "escritor",
    "escriptos": "escritos",
    "escriptura": "escritura",
    "escripturas": "escrituras",
    "escriuania": "escribanía",
    "escriuanias": "escribanías",
    "escriuano": "escribano",
    "escriuanos": "escribanos",
    "escriuen": "escriben",
    "escriue": "escribe",
    "escriuiendo": "escribiendo",
    "escriuiendose": "escribiéndose",
    "escriuir": "escribir",
    "escriuiras": "escribirás",
    "escriuo": "escribo",
    "escrivanias": "escribanías",
    "escrivania": "escribanía",
    "escrivano": "escribano",
    "escrivir": "escribir",
    "escrivjr": "escribir",
    "escrupulo": "escrúpulo",
    "escremento": "excremento",
    "escrudiñador": "escudriñador",
    "sobrescriuir": "sobrescribir",
}


TOKEN_RE = re.compile(
    rf"(?<![{LETTER}])("
    + "|".join(re.escape(token) for token in sorted(TOKEN_REPLACEMENTS, key=len, reverse=True))
    + rf")(?![{LETTER}])",
    re.I,
)


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def rendered_spanish_fields(source: str) -> tuple[str, ...]:
    if source == "2021 Wimmer":
        return ("Traducción", "Traducción (es)", "Comentario", "Comentario (es)")
    return ("Traducción", "Traducción (es)", "Comentario", "Comentario (es)")


def replace_segment(segment: str, changes: Counter[str]) -> str:
    def repl(match: re.Match[str]) -> str:
        old = match.group(0)
        new = preserve_case(old, TOKEN_REPLACEMENTS[old.casefold()])
        changes[f"{old}->{new}"] += 1
        return new

    return TOKEN_RE.sub(repl, segment)


def clean_value(value: str) -> tuple[str, Counter[str]]:
    changes: Counter[str] = Counter()
    parts = BOLD_SPAN_RE.split(value)
    for i, part in enumerate(parts):
        if not part or re.match(r"<b\b", part, re.I):
            continue
        parts[i] = replace_segment(part, changes)
    return "".join(parts), changes


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    rows: list[dict] = []
    reports: list[dict] = []
    changed_rows = 0
    replacement_counts: Counter[str] = Counter()

    for row in iter_rows(args.data):
        source = row.get("Fuente") or ""
        row_reports = []
        for field in rendered_spanish_fields(source):
            value = row.get(field)
            if not isinstance(value, str) or not value:
                continue
            new, changes = clean_value(value)
            if new != value:
                replacement_counts.update(changes)
                row_reports.append(
                    {
                        "field": field,
                        "changes": dict(changes),
                        "old": value,
                        "new": new,
                    }
                )
                if args.apply:
                    row[field] = new
        if row_reports:
            changed_rows += 1
            reports.append(
                {
                    "record_id": row.get("record_id"),
                    "Fuente": row.get("Fuente"),
                    "Lema": row.get("Texto estandarizado") or row.get("Lema"),
                    "fields": row_reports,
                }
            )
        rows.append(row)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as fh:
        for report in reports:
            fh.write(json.dumps(report, ensure_ascii=False) + "\n")

    print(f"mode={'apply' if args.apply else 'dry-run'}")
    print(f"changed_rows={changed_rows}")
    print(f"report={args.report}")
    print("top_replacements=")
    for key, count in replacement_counts.most_common(80):
        print(f"{key}\t{count}")

    if args.apply:
        write_rows(args.data, rows)


if __name__ == "__main__":
    main()
