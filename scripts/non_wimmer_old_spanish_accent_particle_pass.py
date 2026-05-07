#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_accent_particle_report.jsonl"


SOURCE_ALLOWLIST = {
    "1780 ? Bnf_361",
    "17?? Bnf_362",
    "1765 Cortés y Zedeño",
    "1692 Guerra",
    "1611 Arenas",
}

EXACT_REPLACEMENTS = {
    "àlos": "a los",
    "àla": "a la",
    "àl": "al",
    "àotro": "a otro",
    "âotro": "a otro",
    "àbaxo": "abajo",
    "àbajo": "abajo",
    "àfuera": "afuera",
    "àcosarlos": "acosarlos",
    "àunque": "aunque",
    "àun": "aun",
    "àcordarse": "acordarse",
    "àmenudo": "a menudo",
    "àriña": "a riña",
    "àcabar": "acabar",
    "àparejarse": "aparejarse",
    "àdos": "a dos",
    "àclarar": "aclarar",
    "âlgo": "algo",
    "âparte": "aparte",
    "està": "está",
    "estàs": "estás",
    "estâ": "está",
    "acà": "acá",
    "allà": "allá",
    "acullà": "acullá",
    "hà": "ha",
    "llegò": "llegó",
    "vè": "ve",
    "èl": "el",
    "înanimado": "inanimado",
    "sî": "sí",
}
EXACT_RE = re.compile(
    r"\b(" + "|".join(re.escape(token) for token in sorted(EXACT_REPLACEMENTS, key=len, reverse=True)) + r")\b",
    re.I,
)
PARTICLE_REPLACEMENTS = {
    "ô": "o",
    "ò": "o",
    "û": "u",
    "ù": "u",
    "à": "a",
    "â": "a",
    "ã": "a",
    "ê": "e",
}
PARTICLE_RE = re.compile(
    r"\b(" + "|".join(re.escape(token) for token in PARTICLE_REPLACEMENTS) + r")\b",
    re.I,
)
PUNCT_SPACE_RE = re.compile(r"([,;:])(?=\S)")
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def clean(value: str, source: str) -> tuple[str, list[str]]:
    if source not in SOURCE_ALLOWLIST:
        return value or "", []

    text = value or ""
    reasons: list[str] = []
    changed_exact: list[str] = []
    changed_particles: list[str] = []

    def replace_exact(match: re.Match[str]) -> str:
        token = match.group(0)
        replacement = EXACT_REPLACEMENTS[token.lower()]
        if replacement != token:
            changed_exact.append(token.lower())
        return preserve_case(token, replacement)

    def replace_particle(match: re.Match[str]) -> str:
        token = match.group(0)
        replacement = PARTICLE_REPLACEMENTS[token.lower()]
        if replacement != token:
            changed_particles.append(token.lower())
        return preserve_case(token, replacement)

    new = EXACT_RE.sub(replace_exact, text)
    new = PARTICLE_RE.sub(replace_particle, new)

    if changed_exact:
        reasons.append("accent_exact")
        reasons.extend(f"exact:{token}" for token in sorted(set(changed_exact)))
    if changed_particles:
        reasons.append("accent_particle")
        reasons.extend(f"particle:{token}" for token in sorted(set(changed_particles)))

    if reasons:
        spaced = PUNCT_SPACE_RE.sub(r"\1 ", new)
        spaced = MULTISPACE_RE.sub(" ", spaced).strip()
        if spaced != new:
            new = spaced
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
