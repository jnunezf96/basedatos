#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_spelling_residual_report.jsonl"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


REPLACEMENTS: dict[str, tuple[str, str]] = {
    # Fused particles/articles.
    "dela": ("de la", "fused_particle"),
    "delas": ("de las", "fused_particle"),
    "delo": ("de lo", "fused_particle"),
    "delos": ("de los", "fused_particle"),
    "della": ("de ella", "fused_particle"),
    "dellas": ("de ellas", "fused_particle"),
    "dello": ("de ello", "fused_particle"),
    "dellos": ("de ellos", "fused_particle"),
    "desta": ("de esta", "fused_particle"),
    "destas": ("de estas", "fused_particle"),
    "deste": ("de este", "fused_particle"),
    "destos": ("de estos", "fused_particle"),
    "enel": ("en el", "fused_particle"),
    "enla": ("en la", "fused_particle"),
    "enlas": ("en las", "fused_particle"),
    "enlo": ("en lo", "fused_particle"),
    "enlos": ("en los", "fused_particle"),
    "entiempo": ("en tiempo", "fused_particle"),
    "loque": ("lo que", "fused_particle"),
    "paraque": ("para que", "fused_particle"),
    "amenudo": ("a menudo", "fused_particle"),
    "sinoque": ("sino que", "fused_particle"),
    # Common old spellings.
    "mesma": ("misma", "old_spelling"),
    "mesmas": ("mismas", "old_spelling"),
    "mesmo": ("mismo", "old_spelling"),
    "mesmos": ("mismos", "old_spelling"),
    "quando": ("cuando", "old_spelling"),
    "quándo": ("cuando", "old_spelling"),
    "qual": ("cual", "old_spelling"),
    "quales": ("cuales", "old_spelling"),
    "qualidad": ("calidad", "old_spelling"),
    "qualquiera": ("cualquiera", "old_spelling"),
    "muger": ("mujer", "old_spelling"),
    "mugeres": ("mujeres", "old_spelling"),
    "verguença": ("vergüenza", "old_spelling"),
    "verguenza": ("vergüenza", "old_spelling"),
    "persibe": ("percibe", "old_spelling"),
    "esclaua": ("esclava", "old_spelling"),
    "esclauas": ("esclavas", "old_spelling"),
    "esclauo": ("esclavo", "old_spelling"),
    "esclauos": ("esclavos", "old_spelling"),
    "priuada": ("privada", "old_spelling"),
    "priuadas": ("privadas", "old_spelling"),
    "priuado": ("privado", "old_spelling"),
    "priuados": ("privados", "old_spelling"),
    "priuilegiada": ("privilegiada", "old_spelling"),
    "priuilegiadas": ("privilegiadas", "old_spelling"),
    "priuilegiado": ("privilegiado", "old_spelling"),
    "priuilegiados": ("privilegiados", "old_spelling"),
    "priuilegio": ("privilegio", "old_spelling"),
    "esenta": ("exenta", "old_spelling"),
    "esento": ("exento", "old_spelling"),
    "estrema": ("extrema", "old_spelling"),
    "estremas": ("extremas", "old_spelling"),
    "estremo": ("extremo", "old_spelling"),
    "estremos": ("extremos", "old_spelling"),
    "recivir": ("recibir", "old_spelling"),
    "aue": ("ave", "old_spelling"),
    "aues": ("aves", "old_spelling"),
    "caualgar": ("cabalgar", "old_spelling"),
    "caualgadura": ("cabalgadura", "old_spelling"),
    "cauallo": ("caballo", "old_spelling"),
    "cauallos": ("caballos", "old_spelling"),
    "yglesia": ("iglesia", "old_spelling"),
    "ysla": ("isla", "old_spelling"),
    "idolo": ("ídolo", "old_spelling"),
    "idolos": ("ídolos", "old_spelling"),
    "ydolo": ("ídolo", "old_spelling"),
    "ydolos": ("ídolos", "old_spelling"),
    "haver": ("haber", "old_spelling"),
    "necessaria": ("necesaria", "old_spelling"),
    "necessarias": ("necesarias", "old_spelling"),
    "necessario": ("necesario", "old_spelling"),
    "necessarios": ("necesarios", "old_spelling"),
    "aduertido": ("advertido", "old_spelling"),
    "auisado": ("avisado", "old_spelling"),
    "bolar": ("volar", "old_spelling"),
    "rebolar": ("revolar", "old_spelling"),
    "buelue": ("vuelve", "old_spelling"),
    "bueluo": ("vuelvo", "old_spelling"),
    "buelta": ("vuelta", "old_spelling"),
    "buelto": ("vuelto", "old_spelling"),
    "confessar": ("confesar", "old_spelling"),
    "confessarse": ("confesarse", "old_spelling"),
    "confessando": ("confesando", "old_spelling"),
    "confession": ("confesión", "old_spelling"),
    "confessiones": ("confesiones", "old_spelling"),
    "confiesse": ("confiese", "old_spelling"),
    "peccado": ("pecado", "old_spelling"),
    "peccados": ("pecados", "old_spelling"),
    "offensa": ("ofensa", "old_spelling"),
    "offensas": ("ofensas", "old_spelling"),
    "officio": ("oficio", "old_spelling"),
    "officios": ("oficios", "old_spelling"),
    "captiua": ("cautiva", "old_spelling"),
    "captiuas": ("cautivas", "old_spelling"),
    "captiuo": ("cautivo", "old_spelling"),
    "captiuos": ("cautivos", "old_spelling"),
    "catiuos": ("cautivos", "old_spelling"),
    "cautiuo": ("cautivo", "old_spelling"),
    "cautiuos": ("cautivos", "old_spelling"),
    "sauzedal": ("saucedal", "old_spelling"),
    "diuina": ("divina", "old_spelling"),
    "diuinas": ("divinas", "old_spelling"),
    "diuino": ("divino", "old_spelling"),
    "diuinos": ("divinos", "old_spelling"),
    "diuersa": ("diversa", "old_spelling"),
    "diuersas": ("diversas", "old_spelling"),
    "diuerso": ("diverso", "old_spelling"),
    "diuersos": ("diversos", "old_spelling"),
    "biuo": ("vivo", "old_spelling"),
    "biuos": ("vivos", "old_spelling"),
    "benado": ("venado", "old_spelling"),
    "rredonda": ("redonda", "old_spelling"),
    "lagrimas": ("lágrimas", "old_spelling"),
    "yr": ("ir", "old_spelling"),
}


PHRASE_REPLACEMENTS = (
    (re.compile(r"\bde leytable\b", re.I), "deleitable", "old_spelling"),
)


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
    if source == "2021 Wimmer":
        return text, []

    reasons: list[str] = []
    new = text

    for pattern, replacement, reason in PHRASE_REPLACEMENTS:
        cleaned = pattern.sub(lambda match: preserve_case(match.group(0), replacement), new)
        if cleaned != new:
            new = cleaned
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
