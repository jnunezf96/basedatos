#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_ph_nn_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")
SKIP_SOURCES = {"1992 Karttunen"}


PHRASE_REPLACEMENTS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bEt\s+per\s+metaphor[aá]m\b"), "Y por metáfora", "metaphoram_marker"),
    (re.compile(r"\bet\s+per\s+metaphor[aá]m\b"), "y por metáfora", "metaphoram_marker"),
    (re.compile(r"\bEt\s+permetaphora[mn]\b"), "Y por metáfora", "metaphora_marker"),
    (re.compile(r"\bet\s+permetaphora[mn]\b"), "y por metáfora", "metaphora_marker"),
    (re.compile(r"\besperica\s+o\s+espherica\b", re.I), "esférica", "old_ph_spelling"),
    (re.compile(r"\besperica,?\s+o\s+esferica\b", re.I), "esférica", "old_ph_spelling"),
    (re.compile(r"\bper\s+metaphor[aá]m\b", re.I), "por metáfora", "metaphoram_marker"),
    (re.compile(r"\bper\s+metaphora\b", re.I), "por metáfora", "metaphora_marker"),
    (re.compile(r"\bpor\s+methaphora\b", re.I), "por metáfora", "metaphora_marker"),
    (re.compile(r"&\s*per\.?\s*metapho\.?", re.I), "y por metáfora", "metaphora_marker"),
]


REPLACEMENTS: dict[str, tuple[str, str]] = {
    "cacophonia": ("cacofonía", "old_ph_spelling"),
    "calunnia": ("calumnia", "old_nn_spelling"),
    "calunniado": ("calumniado", "old_nn_spelling"),
    "calunniador": ("calumniador", "old_nn_spelling"),
    "calunniar": ("calumniar", "old_nn_spelling"),
    "condennado": ("condenado", "old_nn_spelling"),
    "dannificado": ("damnificado", "old_nn_spelling"),
    "enningun": ("en ningún", "fused_old_nn_spelling"),
    "enninguna": ("en ninguna", "fused_old_nn_spelling"),
    "epitaphio": ("epitafio", "old_ph_spelling"),
    "espherica": ("esférica", "old_ph_spelling"),
    "esphericas": ("esféricas", "old_ph_spelling"),
    "esferica": ("esférica", "old_ph_spelling"),
    "esfericas": ("esféricas", "old_ph_spelling"),
    "esperica": ("esférica", "old_ph_spelling"),
    "filosophar": ("filosofar", "old_ph_spelling"),
    "filosophia": ("filosofía", "old_ph_spelling"),
    "filosopho": ("filósofo", "old_ph_spelling"),
    "metaph": ("metáfora", "metaphora_marker"),
    "metapho": ("metáfora", "metaphora_marker"),
    "metaphor": ("metáfora", "metaphora_marker"),
    "metaphora": ("metáfora", "metaphora_marker"),
    "metaphoram": ("metáfora", "metaphora_marker"),
    "metaphorám": ("metáfora", "metaphora_marker"),
    "metaphorice": ("metafóricamente", "metaphora_marker"),
    "metaphoricamente": ("metafóricamente", "metaphora_marker"),
    "methaphora": ("metáfora", "metaphora_marker"),
    "permetaphoran": ("por metáfora", "metaphora_marker"),
    "permetaphoram": ("por metáfora", "metaphora_marker"),
    "prophecia": ("profecía", "old_ph_spelling"),
    "propheta": ("profeta", "old_ph_spelling"),
    "prophetiza": ("profetiza", "old_ph_spelling"),
    "prophetizar": ("profetizar", "old_ph_spelling"),
    "saphiro": ("zafiro", "old_ph_spelling"),
    "sophisterias": ("sofisterías", "old_ph_spelling"),
    "spherica": ("esférica", "old_ph_spelling"),
    "spherico": ("esférico", "old_ph_spelling"),
    "ynnabil": ("inhábil", "old_y_nn_spelling"),
    "ynnumerable": ("innumerable", "old_y_nn_spelling"),
    "ynnumerables": ("innumerables", "old_y_nn_spelling"),
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
