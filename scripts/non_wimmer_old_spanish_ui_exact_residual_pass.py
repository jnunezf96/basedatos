#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_ui_exact_residual_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")
SKIP_SOURCES = {"1992 Karttunen"}


PHRASE_REPLACEMENTS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bel fuego\s+metph\b", re.I), "el fuego, metáfora", "metaphora_marker"),
]


REPLACEMENTS: dict[str, tuple[str, str]] = {
    "acossador": ("acosador", "old_ss_spelling"),
    "antepassados": ("antepasados", "old_ss_spelling"),
    "assegurarse": ("asegurarse", "old_ss_spelling"),
    "assepilladuras": ("acepilladuras", "old_ss_spelling"),
    "assestar": ("asestar", "old_ss_spelling"),
    "asside": ("así de", "fused_old_ss_spelling"),
    "assignar": ("asignar", "old_ss_spelling"),
    "assistente": ("asistente", "old_ss_spelling"),
    "assiénto": ("asiento", "old_ss_spelling"),
    "assoluedor": ("absolvedor", "old_ss_u_v_spelling"),
    "brauissimamente": ("bravísimamente", "old_ss_u_v_spelling"),
    "cathedra": ("cátedra", "old_th_spelling"),
    "cathedratico": ("catedrático", "old_th_spelling"),
    "confessionario": ("confesionario", "old_ss_spelling"),
    "confiessan": ("confiesan", "old_ss_spelling"),
    "cónfiessan": ("confiesan", "old_ss_spelling"),
    "cónfiesse": ("confiese", "old_ss_spelling"),
    "desasossegador": ("desasosegador", "old_ss_spelling"),
    "despenssero": ("despensero", "old_ss_spelling"),
    "jassador": ("sajador", "old_ss_spelling"),
    "metph": ("metáfora", "metaphora_marker"),
    "thema": ("tema", "old_th_spelling"),
}


TOKEN_RE = re.compile(
    rf"(?<![{LETTER}])("
    + "|".join(re.escape(token) for token in sorted(REPLACEMENTS, key=len, reverse=True))
    + rf")(?![{LETTER}])",
    re.I,
)


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    if source == "2021 Wimmer" or source in SKIP_SOURCES:
        return text, []

    reasons: list[str] = []

    new = text

    for pattern, replacement, reason in PHRASE_REPLACEMENTS:
        updated = pattern.sub(replacement, new)
        if updated != new:
            new = updated
            reasons.append(reason)

    def replace_token(match: re.Match[str]) -> str:
        replacement, reason = REPLACEMENTS[match.group(0).lower()]
        reasons.append(reason)
        return preserve_case(match.group(0), replacement)

    new = TOKEN_RE.sub(replace_token, new)

    cleaned = MULTISPACE_RE.sub(" ", new).strip()
    if cleaned != new:
        new = cleaned
        reasons.append("multispace")

    return new, sorted(set(reasons))


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

    if not DRY_RUN:
        tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        os.replace(tmp, DATA_PATH)

        with REPORT_PATH.open("w", encoding="utf-8") as fh:
            for item in report:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(report)}")
    print(f"report={REPORT_PATH if not DRY_RUN else '(dry-run)'}")


if __name__ == "__main__":
    main()
