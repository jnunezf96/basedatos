#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_cion_singular_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


EXPLICIT_REPLACEMENTS: dict[str, tuple[str, str]] = {
    "abituacion": ("habituación", "old_spelling_cion"),
    "abucion": ("abusión", "old_spelling_cion"),
    "acceptacion": ("aceptación", "old_spelling_cion"),
    "acolacion": ("a colación", "fused_cion"),
    "adivinacion": ("adivinación", "cion_accent"),
    "afliccion": ("aflicción", "cion_accent"),
    "affirmacion": ("afirmación", "old_spelling_cion"),
    "alficion": ("aflicción", "old_spelling_cion"),
    "aprouacion": ("aprobación", "old_spelling_cion"),
    "aprovacion": ("aprobación", "old_spelling_cion"),
    "asolacion": ("asolación", "cion_accent"),
    "assolucion": ("absolución", "old_spelling_cion"),
    "assignacion": ("asignación", "old_spelling_cion"),
    "aueriguacion": ("averiguación", "old_spelling_cion"),
    "avitacion": ("habitación", "old_spelling_cion"),
    "cóndicion": ("condición", "old_accent_cion"),
    "cóndenacion": ("condenación", "old_accent_cion"),
    "cónstellacion": ("constelación", "old_accent_cion"),
    "cónsumacion": ("consumación", "old_accent_cion"),
    "cóntemplacion": ("contemplación", "old_accent_cion"),
    "cómparacion": ("comparación", "old_accent_cion"),
    "canonizacion": ("canonización", "cion_accent"),
    "cessacion": ("cesación", "old_spelling_cion"),
    "circuncicion": ("circuncisión", "old_spelling_cion"),
    "codicion": ("codicia", "old_spelling_cion"),
    "collacion": ("colación", "old_spelling_cion"),
    "compacion": ("compasión", "old_spelling_cion"),
    "comprehencion": ("comprensión", "old_spelling_cion"),
    "compreencion": ("comprensión", "old_spelling_cion"),
    "comiuncion": ("conjunción", "old_spelling_cion"),
    "confuncion": ("confusión", "old_spelling_cion"),
    "conlcucion": ("conclusión", "old_spelling_cion"),
    "conpresuncion": ("con presunción", "fused_cion"),
    "conpresumpcion": ("con presunción", "fused_cion"),
    "consecuçion": ("consecución", "old_spelling_cion"),
    "constellacion": ("constelación", "old_spelling_cion"),
    "constuccion": ("construcción", "old_spelling_cion"),
    "contraicion": ("traición", "old_spelling_cion"),
    "correcion": ("corrección", "old_spelling_cion"),
    "criacion": ("creación", "old_spelling_cion"),
    "darlebendicion": ("darle bendición", "fused_cion"),
    "denunciancion": ("denunciación", "old_spelling_cion"),
    "descricion": ("descripción", "old_spelling_cion"),
    "deuocion": ("devoción", "old_spelling_cion"),
    "devocion": ("devoción", "cion_accent"),
    "dissolucion": ("disolución", "old_spelling_cion"),
    "divicion": ("división", "old_spelling_cion"),
    "dradacion": ("gradación", "old_spelling_cion"),
    "edificcacion": ("edificación", "old_spelling_cion"),
    "encuardernacion": ("encuadernación", "old_spelling_cion"),
    "enquadernacion": ("encuadernación", "old_spelling_cion"),
    "entoancion": ("entonación", "old_spelling_cion"),
    "esaminacion": ("examinación", "old_spelling_cion"),
    "espedicion": ("expedición", "old_spelling_cion"),
    "exalacion": ("exhalación", "old_spelling_cion"),
    "exortacion": ("exhortación", "old_spelling_cion"),
    "facinacion": ("fascinación", "old_spelling_cion"),
    "ficion": ("ficción", "old_spelling_cion"),
    "governacion": ("gobernación", "old_spelling_cion"),
    "icion": ("ición", "cion_accent"),
    "illuminacion": ("iluminación", "old_spelling_cion"),
    "impotracion": ("impetración", "old_spelling_cion"),
    "inténcion": ("intención", "old_accent_cion"),
    "interiecion": ("interjección", "old_spelling_cion"),
    "interieccion": ("interjección", "old_spelling_cion"),
    "juridicion": ("jurisdicción", "old_spelling_cion"),
    "jurisdicion": ("jurisdicción", "old_spelling_cion"),
    "jurisdiccion": ("jurisdicción", "cion_accent"),
    "leccion": ("lección", "cion_accent"),
    "licion": ("lección", "old_spelling_cion"),
    "manifesacion": ("manifestación", "old_spelling_cion"),
    "nauegacion": ("navegación", "old_spelling_cion"),
    "negosiacion": ("negociación", "old_spelling_cion"),
    "oancion": ("canción", "old_spelling_cion"),
    "ocollacion": ("o colación", "fused_cion"),
    "oradacion": ("horadación", "old_spelling_cion"),
    "ostinacion": ("obstinación", "old_spelling_cion"),
    "ovisitacion": ("o visitación", "fused_cion"),
    "pacion": ("pasión", "old_spelling_cion"),
    "percecucion": ("persecución", "old_spelling_cion"),
    "permicion": ("permisión", "old_spelling_cion"),
    "pencion": ("pensión", "old_spelling_cion"),
    "polucion": ("polución", "cion_accent"),
    "posecion": ("posesión", "old_spelling_cion"),
    "prepocicion": ("preposición", "old_spelling_cion"),
    "prepossicion": ("preposición", "old_spelling_cion"),
    "pricion": ("prisión", "old_spelling_cion"),
    "priuacion": ("privación", "old_spelling_cion"),
    "procecion": ("procesión", "old_spelling_cion"),
    "prosecion": ("procesión", "old_spelling_cion"),
    "provicion": ("provisión", "old_spelling_cion"),
    "redempcion": ("redención", "old_spelling_cion"),
    "renouacion": ("renovación", "old_spelling_cion"),
    "reprehencion": ("reprehensión", "old_spelling_cion"),
    "resurecion": ("resurrección", "old_spelling_cion"),
    "resurreccion": ("resurrección", "cion_accent"),
    "reuelacion": ("revelación", "old_spelling_cion"),
    "saluacion": ("salvación", "old_spelling_cion"),
    "sanctificacion": ("santificación", "old_spelling_cion"),
    "secertacion": ("secuestración", "old_spelling_cion"),
    "secrestacion": ("secuestración", "old_spelling_cion"),
    "suportacion": ("soportación", "old_spelling_cion"),
    "tassacion": ("tasación", "old_spelling_cion"),
    "tlaslacion": ("traslación", "old_spelling_cion"),
    "traducion": ("traducción", "old_spelling_cion"),
    "tribualcion": ("tribulación", "old_spelling_cion"),
    "yncitacion": ("incitación", "old_spelling_cion"),
    "ynformacion": ("información", "old_spelling_cion"),
    "ynquisicion": ("inquisición", "old_spelling_cion"),
    "ynterjeccion": ("interjección", "old_spelling_cion"),
    "ynterpretacion": ("interpretación", "old_spelling_cion"),
    "ynterseccion": ("intersección", "old_spelling_cion"),
    "yntencion": ("intención", "old_spelling_cion"),
    "yntroduccion": ("introducción", "old_spelling_cion"),
    "yntroducion": ("introducción", "old_spelling_cion"),
    "ynuencion": ("invención", "old_spelling_cion"),
    "ynvencion": ("invención", "old_spelling_cion"),
    "yluminacion": ("iluminación", "old_spelling_cion"),
    "ymitacion": ("imitación", "old_spelling_cion"),
    "ymposicion": ("imposición", "old_spelling_cion"),
    "yurisdicion": ("jurisdicción", "old_spelling_cion"),
}


EXPLICIT_RE = re.compile(
    rf"(?<![{LETTER}])("
    + "|".join(re.escape(token) for token in sorted(EXPLICIT_REPLACEMENTS, key=len, reverse=True))
    + rf")(?![{LETTER}])",
    re.I,
)

GENERIC_CION_RE = re.compile(rf"(?<![{LETTER}])([{LETTER}]*cion)(?![{LETTER}])", re.I)
GENERIC_SKIP_SOURCES = {"1992 Karttunen"}
GENERIC_SKIP_TOKENS = {"suspicion"}


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def accent_final_cion(token: str) -> str:
    suffix = "CIÓN" if token[-4:].isupper() else "ción"
    return token[:-4] + suffix


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    if source == "2021 Wimmer":
        return text, []

    reasons: list[str] = []

    def replace_explicit(match: re.Match[str]) -> str:
        replacement, reason = EXPLICIT_REPLACEMENTS[match.group(0).lower()]
        reasons.append(reason)
        return preserve_case(match.group(0), replacement)

    new = EXPLICIT_RE.sub(replace_explicit, text)

    if source not in GENERIC_SKIP_SOURCES:

        def replace_generic(match: re.Match[str]) -> str:
            token = match.group(1)
            if token.lower() in GENERIC_SKIP_TOKENS:
                return token
            reasons.append("cion_accent")
            return accent_final_cion(token)

        new = GENERIC_CION_RE.sub(replace_generic, new)

    # Avoid duplicate synonyms created when old and modern spellings were paired.
    new = re.sub(r"\bcreación\s+o\s+creación\b", "creación", new, flags=re.I)

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
