#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_cion_residual_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


REPLACEMENTS: dict[str, tuple[str, str]] = {
    "absolucion": ("absolución", "cion_accent_or_old_spelling"),
    "accion": ("acción", "cion_accent_or_old_spelling"),
    "acusacion": ("acusación", "cion_accent_or_old_spelling"),
    "acaecio": ("acaeció", "old_spelling"),
    "acaesido": ("acaecido", "old_spelling"),
    "adiuinacion": ("adivinación", "cion_accent_or_old_spelling"),
    "admiracion": ("admiración", "cion_accent_or_old_spelling"),
    "adoracion": ("adoración", "cion_accent_or_old_spelling"),
    "aficion": ("afición", "cion_accent_or_old_spelling"),
    "afirmacion": ("afirmación", "cion_accent_or_old_spelling"),
    "alteracion": ("alteración", "cion_accent_or_old_spelling"),
    "amonestacion": ("amonestación", "cion_accent_or_old_spelling"),
    "apelacion": ("apelación", "cion_accent_or_old_spelling"),
    "apropriacion": ("apropiación", "cion_accent_or_old_spelling"),
    "atencion": ("atención", "cion_accent_or_old_spelling"),
    "bendicion": ("bendición", "cion_accent_or_old_spelling"),
    "cancion": ("canción", "cion_accent_or_old_spelling"),
    "celebracion": ("celebración", "cion_accent_or_old_spelling"),
    "composicion": ("composición", "cion_accent_or_old_spelling"),
    "comparacion": ("comparación", "cion_accent_or_old_spelling"),
    "condicion": ("condición", "cion_accent_or_old_spelling"),
    "confederacion": ("confederación", "cion_accent_or_old_spelling"),
    "confirmacion": ("confirmación", "cion_accent_or_old_spelling"),
    "congregacion": ("congregación", "cion_accent_or_old_spelling"),
    "conjuncion": ("conjunción", "cion_accent_or_old_spelling"),
    "consolacion": ("consolación", "cion_accent_or_old_spelling"),
    "consideracion": ("consideración", "cion_accent_or_old_spelling"),
    "constitucion": ("constitución", "cion_accent_or_old_spelling"),
    "contencion": ("contención", "cion_accent_or_old_spelling"),
    "contemplacion": ("contemplación", "cion_accent_or_old_spelling"),
    "contradicion": ("contradicción", "cion_accent_or_old_spelling"),
    "conuersacion": ("conversación", "cion_accent_or_old_spelling"),
    "conversacion": ("conversación", "cion_accent_or_old_spelling"),
    "coronacion": ("coronación", "cion_accent_or_old_spelling"),
    "declaracion": ("declaración", "cion_accent_or_old_spelling"),
    "deliberacion": ("deliberación", "cion_accent_or_old_spelling"),
    "denunciacion": ("denunciación", "cion_accent_or_old_spelling"),
    "deposicion": ("deposición", "cion_accent_or_old_spelling"),
    "despoblacion": ("despoblación", "cion_accent_or_old_spelling"),
    "despues": ("después", "accent_or_old_spelling"),
    "destrucion": ("destrucción", "cion_accent_or_old_spelling"),
    "destruicion": ("destrucción", "cion_accent_or_old_spelling"),
    "determinacion": ("determinación", "cion_accent_or_old_spelling"),
    "dilacion": ("dilación", "cion_accent_or_old_spelling"),
    "discrecion": ("discreción", "cion_accent_or_old_spelling"),
    "disimulacion": ("disimulación", "cion_accent_or_old_spelling"),
    "dissimulacion": ("disimulación", "cion_accent_or_old_spelling"),
    "disposicion": ("disposición", "cion_accent_or_old_spelling"),
    "diuulgacion": ("divulgación", "cion_accent_or_old_spelling"),
    "donacion": ("donación", "cion_accent_or_old_spelling"),
    "duracion": ("duración", "cion_accent_or_old_spelling"),
    "edificacion": ("edificación", "cion_accent_or_old_spelling"),
    "elecion": ("elección", "cion_accent_or_old_spelling"),
    "entonacion": ("entonación", "cion_accent_or_old_spelling"),
    "escusacion": ("excusación", "cion_accent_or_old_spelling"),
    "esencion": ("exención", "cion_accent_or_old_spelling"),
    "estimacion": ("estimación", "cion_accent_or_old_spelling"),
    "exclamacion": ("exclamación", "cion_accent_or_old_spelling"),
    "fabricacion": ("fabricación", "cion_accent_or_old_spelling"),
    "generacion": ("generación", "cion_accent_or_old_spelling"),
    "glorificacion": ("glorificación", "cion_accent_or_old_spelling"),
    "gouernacion": ("gobernación", "cion_accent_or_old_spelling"),
    "humillacion": ("humillación", "cion_accent_or_old_spelling"),
    "importunacion": ("importunación", "cion_accent_or_old_spelling"),
    "inclinacion": ("inclinación", "cion_accent_or_old_spelling"),
    "incitacion": ("incitación", "cion_accent_or_old_spelling"),
    "indignacion": ("indignación", "cion_accent_or_old_spelling"),
    "inquisicion": ("inquisición", "cion_accent_or_old_spelling"),
    "intencion": ("intención", "cion_accent_or_old_spelling"),
    "interjecion": ("interjección", "cion_accent_or_old_spelling"),
    "lecion": ("lección", "cion_accent_or_old_spelling"),
    "maldicion": ("maldición", "cion_accent_or_old_spelling"),
    "manifestacion": ("manifestación", "cion_accent_or_old_spelling"),
    "meditacion": ("meditación", "cion_accent_or_old_spelling"),
    "multiplicacion": ("multiplicación", "cion_accent_or_old_spelling"),
    "murmuracion": ("murmuración", "cion_accent_or_old_spelling"),
    "nacion": ("nación", "cion_accent_or_old_spelling"),
    "negacion": ("negación", "cion_accent_or_old_spelling"),
    "notacion": ("notación", "cion_accent_or_old_spelling"),
    "obligacion": ("obligación", "cion_accent_or_old_spelling"),
    "obstinacion": ("obstinación", "cion_accent_or_old_spelling"),
    "ocacion": ("ocasión", "cion_accent_or_old_spelling"),
    "ocupacion": ("ocupación", "cion_accent_or_old_spelling"),
    "ordenacion": ("ordenación", "cion_accent_or_old_spelling"),
    "pacificacion": ("pacificación", "cion_accent_or_old_spelling"),
    "perfecion": ("perfección", "cion_accent_or_old_spelling"),
    "persecucion": ("persecución", "cion_accent_or_old_spelling"),
    "poblacion": ("población", "cion_accent_or_old_spelling"),
    "preposicion": ("preposición", "cion_accent_or_old_spelling"),
    "presumpcion": ("presunción", "cion_accent_or_old_spelling"),
    "presuncion": ("presunción", "cion_accent_or_old_spelling"),
    "procuracion": ("procuración", "cion_accent_or_old_spelling"),
    "pronunciacion": ("pronunciación", "cion_accent_or_old_spelling"),
    "provocacion": ("provocación", "cion_accent_or_old_spelling"),
    "prouocacion": ("provocación", "cion_accent_or_old_spelling"),
    "publicacion": ("publicación", "cion_accent_or_old_spelling"),
    "purgacion": ("purgación", "cion_accent_or_old_spelling"),
    "racion": ("ración", "cion_accent_or_old_spelling"),
    "reconciliacion": ("reconciliación", "cion_accent_or_old_spelling"),
    "recreacion": ("recreación", "cion_accent_or_old_spelling"),
    "relacion": ("relación", "cion_accent_or_old_spelling"),
    "representacion": ("representación", "cion_accent_or_old_spelling"),
    "restitucion": ("restitución", "cion_accent_or_old_spelling"),
    "retratacion": ("retractación", "cion_accent_or_old_spelling"),
    "satisfacion": ("satisfacción", "cion_accent_or_old_spelling"),
    "salutacion": ("salutación", "cion_accent_or_old_spelling"),
    "significacion": ("significación", "cion_accent_or_old_spelling"),
    "supplicacion": ("suplicación", "cion_accent_or_old_spelling"),
    "supplicar": ("suplicar", "old_spelling"),
    "supplicando": ("suplicando", "old_spelling"),
    "tentacion": ("tentación", "cion_accent_or_old_spelling"),
    "traicion": ("traición", "cion_accent_or_old_spelling"),
    "traycion": ("traición", "cion_accent_or_old_spelling"),
    "turbacion": ("turbación", "cion_accent_or_old_spelling"),
    "vncion": ("unción", "cion_accent_or_old_spelling"),
    "visitacion": ("visitación", "cion_accent_or_old_spelling"),
    "ymaginacion": ("imaginación", "cion_accent_or_old_spelling"),
    "ympetracion": ("impetración", "cion_accent_or_old_spelling"),
    "ynclinacion": ("inclinación", "cion_accent_or_old_spelling"),
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
    if source == "2021 Wimmer":
        return text, []

    reasons: list[str] = []

    def replace_token(match: re.Match[str]) -> str:
        replacement, reason = REPLACEMENTS[match.group(0).lower()]
        reasons.append(reason)
        return preserve_case(match.group(0), replacement)

    new = TOKEN_RE.sub(replace_token, text)

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
