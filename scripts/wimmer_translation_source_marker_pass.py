#!/usr/bin/env python3
import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "wimmer_translation_source_marker_report.jsonl"


PAREN_SOURCE_BEFORE_PUNCT_RE = re.compile(r"\s*\((?:S|M|K|Par\.?)\)(?=[.,;:/]|$)", re.I)
PAREN_SOURCE_RE = re.compile(r"\s*\((?:S|M|K|Par\.?)\)\s*", re.I)
OPEN_SOURCE_RE = re.compile(r"\s*\((?:S|M|K)\.(?=\s*(?:/|$|[.;,]))", re.I)
BROKEN_EMPTY_PAREN_RE = re.compile(r"\s*\(\(\s*\.\s*")
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([.,;:])")
MULTISPACE_RE = re.compile(r"\s+")
GRAMMAR_SLASH_RE = re.compile(
    r"\b(tē|te|tla|motē|mote|motla|tētla|tetla|mo|tito)-\s*/\s*"
    r"(tē|te|tla|motē|mote|motla|tētla|tetla|mo|tito)-",
    re.I,
)


def clean(value: str) -> str:
    new = value
    new = OPEN_SOURCE_RE.sub("", new)
    new = PAREN_SOURCE_BEFORE_PUNCT_RE.sub("", new)
    new = PAREN_SOURCE_RE.sub(" ", new)
    new = BROKEN_EMPTY_PAREN_RE.sub(". ", new)
    new = GRAMMAR_SLASH_RE.sub(r"\1-/\2-", new)
    if new == value:
        return value
    new = SPACE_BEFORE_PUNCT_RE.sub(r"\1", new)
    new = re.sub(r"\.{2,}", ".", new)
    new = MULTISPACE_RE.sub(" ", new).strip()
    if new != value and new and new[-1] not in ".!?":
        new += "."
    return new


def main() -> None:
    rows = []
    report = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("Fuente") == "2021 Wimmer":
                old = row.get("Traducción (es)") or ""
                new = clean(old)
                if new != old:
                    row["Traducción (es)"] = new
                    report.append(
                        {
                            "record_id": row.get("record_id"),
                            "lemma": row.get("Texto estandarizado"),
                            "old_translation_es": old,
                            "new_translation_es": new,
                        }
                    )
            rows.append(row)

    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(report)}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
