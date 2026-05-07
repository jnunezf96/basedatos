#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_consonant_report.jsonl"


REPLACEMENTS = {
    "hazer": "hacer",
    "hazerle": "hacerle",
    "hazerlo": "hacerlo",
    "hazerla": "hacerla",
    "hazerlos": "hacerlos",
    "hazerme": "hacerme",
    "hazerse": "hacerse",
    "hazerseme": "hacérseme",
    "haze": "hace",
    "hazen": "hacen",
    "hazén": "hacen",
    "hazes": "haces",
    "hazcer": "hacer",
    "hazerce": "hacerse",
    "hazezse": "hacerse",
    "haziendo": "haciendo",
    "haziéndo": "haciendo",
    "haziendole": "haciéndole",
    "haziéndole": "haciéndole",
    "haziendolo": "haciéndolo",
    "haziendola": "haciéndola",
    "haziendose": "haciéndose",
    "haziéndose": "haciéndose",
    "hazia": "hacia",
    "haziaca": "hacia acá",
    "haziami": "hacia mí",
    "haziabaxo": "hacia abajo",
    "haziatras": "hacia atrás",
    "haziarriba": "hacia arriba",
    "haziala": "hacia la",
    "hazienda": "hacienda",
    "haziénda": "hacienda",
    "hazedor": "hacedor",
    "hazedora": "hacedora",
    "hazedores": "hacedores",
    "hazedera": "hacedera",
    "contrahazer": "contrahacer",
    "contrahaze": "contrahace",
    "contrahazedor": "contrahacedor",
    "deshazer": "deshacer",
    "deshazerse": "deshacerse",
    "dehazer": "de hacer",
    "hizieron": "hicieron",
    "sehaze": "se hace",
    "yhaze": "y hace",
    "dezir": "decir",
    "deçir": "decir",
    "dezia": "decía",
    "dezian": "decían",
    "dize": "dice",
    "dizen": "dicen",
    "diziendo": "diciendo",
    "diziendole": "diciéndole",
    "diziendolo": "diciéndolo",
    "dixo": "dijo",
    "dixe": "dije",
    "dixeron": "dijeron",
    "dixese": "dijese",
    "dixesemos": "dijésemos",
    "dexar": "dejar",
    "dexa": "deja",
    "dexo": "dejo",
    "dexado": "dejado",
    "dexada": "dejada",
    "dexados": "dejados",
    "dexadas": "dejadas",
    "dexan": "dejan",
    "dexán": "dejan",
    "dexando": "dejando",
    "dexaron": "dejaron",
    "abaxo": "abajo",
    "debaxo": "debajo",
    "exemplo": "ejemplo",
    "exemplos": "ejemplos",
    "exercicio": "ejercicio",
    "exercicios": "ejercicios",
    "exercita": "ejercita",
    "exercitar": "ejercitar",
    "exercitarse": "ejercitarse",
    "exercitarme": "ejercitarme",
    "exercitarlo": "ejercitarlo",
    "exercitado": "ejercitado",
    "mexor": "mejor",
    "mexores": "mejores",
    "texer": "tejer",
    "texe": "teje",
    "texendo": "tejiendo",
    "texiendo": "tejiendo",
    "texedor": "tejedor",
    "texedera": "tejedera",
    "texedura": "tejedura",
    "texida": "tejida",
    "texido": "tejido",
    "texidos": "tejidos",
    "texa": "teja",
    "texas": "tejas",
    "texar": "tejar",
    "texado": "tejado",
    "texados": "tejados",
    "traxo": "trajo",
    "traxeron": "trajeron",
}

TOKEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(token) for token in sorted(REPLACEMENTS, key=len, reverse=True)) + r")\b",
    re.I,
)
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def clean(value: str) -> tuple[str, list[str]]:
    text = value or ""
    changed_tokens: list[str] = []

    def replace_match(match: re.Match[str]) -> str:
        token = match.group(0)
        replacement = REPLACEMENTS[token.lower()]
        if replacement != token:
            changed_tokens.append(token.lower())
        return preserve_case(token, replacement)

    new = TOKEN_RE.sub(replace_match, text)
    reasons: list[str] = []
    if new != text:
        reasons.append("consonant_token")
        reasons.extend(f"token:{token}" for token in sorted(set(changed_tokens)))

    cleaned = MULTISPACE_RE.sub(" ", new).strip()
    if cleaned != new:
        new = cleaned
        reasons.append("multispace")

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
                new, reasons = clean(old)
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
