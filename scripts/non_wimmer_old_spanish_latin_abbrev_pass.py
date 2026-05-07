#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_latin_abbrev_report.jsonl"


AUT_VEL_PATTERNS = [
    (re.compile(r"\bo,\s*conjuncion disjunctiva,\s*vel,\s*aut,?", re.I), "o, conjuncion disjunctiva"),
    (re.compile(r"\bo,\s*vel,\s*aut\s+conjuncion disjunctiva", re.I), "o, conjuncion disjunctiva"),
    (re.compile(r"\bo,\s*vel,\s*aut\b", re.I), "o"),
    (re.compile(r"\bo,\s*latin\.\s*aut,\s*vel\b", re.I), "o"),
    (re.compile(r"\bvel,\s*aut\b", re.I), "o"),
]
VEL_SIMILE_RE = re.compile(
    r"\(?\bvel\b\s*[.;,]?\s*(?:simile|similiter|bimile\s*\[simile\])\)?",
    re.I,
)
LO_MESMO_ES_QUE_VEL_RE = re.compile(r"\blo mesmo es que\s+vel\s+", re.I)
VEL_ANTE_RE = re.compile(r"\bvel\s+ante\b", re.I)
VEL_MASQUE_RE = re.compile(r"\bvel\s+masque\b", re.I)
TRAILING_VEL_RE = re.compile(r"\s*[;,]\s*\bvel\b\.?\s*$", re.I)
O_VEL_O_RE = re.compile(r"\bo\.\s*vel\.?\s*o,", re.I)
GUAI_VEL_O_RE = re.compile(r"\bguai\.\s*vel\.\s*o\.", re.I)
O_VEL_QUISAS_RE = re.compile(r"\bO\s+vel\s+quisas\b")
SCIL_RE = re.compile(r"\bscil\b\.?,?", re.I)
VEL_RE = re.compile(r"\bvel\b\.?,?", re.I)
PUNCT_SPACE_RE = re.compile(r"([,;:])(?=\S)")
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


def clean(value: str, source: str) -> tuple[str, list[str]]:
    if source == "2021 Wimmer":
        return value or "", []

    old = value or ""
    new = old
    reasons: list[str] = []

    for pattern, replacement in AUT_VEL_PATTERNS:
        updated = pattern.sub(replacement, new)
        if updated != new:
            new = updated
            reasons.append("vel_aut")

    updated = VEL_SIMILE_RE.sub("o cosa semejante", new)
    if updated != new:
        new = updated
        reasons.append("vel_simile")

    updated = LO_MESMO_ES_QUE_VEL_RE.sub("lo mesmo es que ", new)
    if updated != new:
        new = updated
        reasons.append("lo_mesmo_vel")

    updated = VEL_ANTE_RE.sub("o antes", new)
    if updated != new:
        new = updated
        reasons.append("vel_ante")

    updated = VEL_MASQUE_RE.sub("o más que", new)
    if updated != new:
        new = updated
        reasons.append("vel_masque")

    updated = TRAILING_VEL_RE.sub(".", new)
    if updated != new:
        new = updated
        reasons.append("trailing_vel")

    updated = O_VEL_O_RE.sub("o,", new)
    if updated != new:
        new = updated
        reasons.append("o_vel_o")

    updated = GUAI_VEL_O_RE.sub("guai, o.", new)
    if updated != new:
        new = updated
        reasons.append("guai_vel_o")

    updated = O_VEL_QUISAS_RE.sub("O quisas", new)
    if updated != new:
        new = updated
        reasons.append("o_vel_quisas")

    updated = SCIL_RE.sub("es decir,", new)
    if updated != new:
        new = updated
        reasons.append("scil")

    updated = VEL_RE.sub("o", new)
    if updated != new:
        new = updated
        reasons.append("vel")

    if reasons:
        cleaned = PUNCT_SPACE_RE.sub(r"\1 ", new)
        cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
        cleaned = re.sub(r"\(\s+", "(", cleaned)
        cleaned = re.sub(r"\s+\)", ")", cleaned)
        cleaned = re.sub(r"\s+([?])", r"\1", cleaned)
        cleaned = MULTISPACE_RE.sub(" ", cleaned).strip()
        cleaned = re.sub(r",\s*o\b", ", o", cleaned)
        cleaned = re.sub(r";\s*o;\s*", "; o ", cleaned)
        if cleaned != new:
            new = cleaned
            reasons.append("spacing")

    return new, reasons


def main() -> None:
    rows = []
    report = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            source = row.get("Fuente") or ""
            if source and source != "2021 Wimmer":
                old = row.get("Traducción") or ""
                new, reasons = clean(old, source)
                if new != old:
                    row["Traducción"] = new
                    report.append(
                        {
                            "record_id": row.get("record_id"),
                            "source": source,
                            "lemma": row.get("Texto estandarizado"),
                            "reasons": reasons,
                            "old_translation": old,
                            "new_translation": new,
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
