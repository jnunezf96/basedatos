#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_fused_vu_residual_report.jsonl"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
WORD = rf"[{LETTER}]+"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


TOKEN_REPLACEMENTS: dict[str, tuple[str, str]] = {
    # Fused preposition + article/pronoun.
    "alos": ("a los", "fused_a"),
    "alque": ("al que", "fused_a"),
    "alo": ("a lo", "fused_a"),
    "aotra": ("a otra", "fused_a"),
    "aotras": ("a otras", "fused_a"),
    "aotro": ("a otro", "fused_a"),
    "aotros": ("a otros", "fused_a"),
    "alquien": ("alguien", "typo_or_old_spelling"),
    "conla": ("con la", "fused_con"),
    "conlas": ("con las", "fused_con"),
    "conlo": ("con lo", "fused_con"),
    "conlos": ("con los", "fused_con"),
    "conque": ("con que", "fused_con"),
    # Old v/u and spelling residue.
    "aduerbio": ("adverbio", "old_vu_spelling"),
    "aduerbios": ("adverbios", "old_vu_spelling"),
    "algodon": ("algodón", "accent_or_old_spelling"),
    "atreuido": ("atrevido", "old_vu_spelling"),
    "beuida": ("bebida", "old_vu_spelling"),
    "beuidas": ("bebidas", "old_vu_spelling"),
    "beuido": ("bebido", "old_vu_spelling"),
    "beuidos": ("bebidos", "old_vu_spelling"),
    "beuer": ("beber", "old_vu_spelling"),
    "biuir": ("vivir", "old_vu_spelling"),
    "biuora": ("víbora", "old_vu_spelling"),
    "biuoras": ("víboras", "old_vu_spelling"),
    "bolver": ("volver", "old_vu_spelling"),
    "breue": ("breve", "old_vu_spelling"),
    "cauallero": ("caballero", "old_vu_spelling"),
    "caualleros": ("caballeros", "old_vu_spelling"),
    "comparatiuo": ("comparativo", "old_vu_spelling"),
    "conuertir": ("convertir", "old_vu_spelling"),
    "couarde": ("cobarde", "old_vu_spelling"),
    "couardes": ("cobardes", "old_vu_spelling"),
    "digestion": ("digestión", "accent_or_old_spelling"),
    "diuidir": ("dividir", "old_vu_spelling"),
    "escriptura": ("escritura", "old_vu_spelling"),
    "escripturas": ("escrituras", "old_vu_spelling"),
    "escreuir": ("escribir", "old_vu_spelling"),
    "escriue": ("escribe", "old_vu_spelling"),
    "escriuen": ("escriben", "old_vu_spelling"),
    "escriuano": ("escribano", "old_vu_spelling"),
    "escriuanos": ("escribanos", "old_vu_spelling"),
    "estomago": ("estómago", "accent_or_old_spelling"),
    "euangelio": ("evangelio", "old_vu_spelling"),
    "fauor": ("favor", "old_vu_spelling"),
    "fauorecer": ("favorecer", "old_vu_spelling"),
    "fauorecido": ("favorecido", "old_vu_spelling"),
    "fauorecida": ("favorecida", "old_vu_spelling"),
    "gouernar": ("gobernar", "old_vu_spelling"),
    "huerfano": ("huérfano", "accent_or_old_spelling"),
    "huerfanos": ("huérfanos", "accent_or_old_spelling"),
    "inuencion": ("invención", "old_vu_spelling"),
    "inuenciones": ("invenciones", "old_vu_spelling"),
    "inuentado": ("inventado", "old_vu_spelling"),
    "inuentada": ("inventada", "old_vu_spelling"),
    "inuentar": ("inventar", "old_vu_spelling"),
    "inuoca": ("invoca", "old_vu_spelling"),
    "inuocan": ("invocan", "old_vu_spelling"),
    "inuocar": ("invocar", "old_vu_spelling"),
    "lauar": ("lavar", "old_vu_spelling"),
    "llouer": ("llover", "old_vu_spelling"),
    "naue": ("nave", "old_vu_spelling"),
    "naues": ("naves", "old_vu_spelling"),
    "nauio": ("navío", "old_vu_spelling"),
    "nauios": ("navíos", "old_vu_spelling"),
    "nieue": ("nieve", "old_vu_spelling"),
    "predicacion": ("predicación", "accent_or_old_spelling"),
    "quarenta": ("cuarenta", "old_vu_spelling"),
    "reboluer": ("revolver", "old_vu_spelling"),
    "reuerencia": ("reverencia", "old_vu_spelling"),
    "suaue": ("suave", "old_vu_spelling"),
    "suaueza": ("suaveza", "old_vu_spelling"),
    "tribulacion": ("tribulación", "accent_or_old_spelling"),
    "nueue": ("nueve", "old_vu_spelling"),
}


TOKEN_RE = re.compile(
    rf"(?<![{LETTER}])("
    + "|".join(re.escape(token) for token in sorted(TOKEN_REPLACEMENTS, key=len, reverse=True))
    + rf")(?![{LETTER}])",
    re.I,
)

ALA_RE = re.compile(rf"(?<![{LETTER}])(ala)(\s+)({WORD})(?![{LETTER}])", re.I)
ALAS_RE = re.compile(rf"(?<![{LETTER}])(alas)(\s+)({WORD})(?![{LETTER}])", re.I)

ALA_EXCEPT_NEXT = {"con", "de", "deaue", "del", "para", "pequeña"}
ALAS_EXCEPT_NEXT = {
    "a",
    "amarillas",
    "brillan",
    "cuando",
    "de",
    "del",
    "el",
    "la",
    "pequeñas",
    "sin",
    "y",
}


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def replace_ala(match: re.Match[str]) -> str:
    next_word = match.group(3).lower()
    if next_word in ALA_EXCEPT_NEXT:
        return match.group(0)
    return preserve_case(match.group(1), "a la") + match.group(2) + match.group(3)


def replace_alas(match: re.Match[str]) -> str:
    next_word = match.group(3).lower()
    if next_word in ALAS_EXCEPT_NEXT:
        return match.group(0)
    return preserve_case(match.group(1), "a las") + match.group(2) + match.group(3)


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    if source == "2021 Wimmer":
        return text, []

    reasons: list[str] = []
    new = text

    after_ala = ALA_RE.sub(replace_ala, new)
    if after_ala != new:
        new = after_ala
        reasons.append("contextual_ala")

    after_alas = ALAS_RE.sub(replace_alas, new)
    if after_alas != new:
        new = after_alas
        reasons.append("contextual_alas")

    if "oalo" in new:
        new = new.replace("oalo", "o a lo").replace("Oalo", "O a lo")
        reasons.append("fused_a")

    def replace_token(match: re.Match[str]) -> str:
        replacement, reason = TOKEN_REPLACEMENTS[match.group(0).lower()]
        if reason != "noop":
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
