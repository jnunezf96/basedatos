#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_x_j_residual_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


REPLACEMENTS: dict[str, tuple[str, str]] = {
    "abaxar": ("bajar", "old_x_spelling"),
    "abaxada": ("bajada", "old_x_spelling"),
    "abaxarse": ("bajarse", "old_x_spelling"),
    "aempuxones": ("a empujones", "fused_old_x_spelling"),
    "afloxar": ("aflojar", "old_x_spelling"),
    "afloxarse": ("aflojarse", "old_x_spelling"),
    "alexos": ("a lejos", "fused_old_x_spelling"),
    "axi": ("ají", "old_x_spelling"),
    "baxa": ("baja", "old_x_spelling"),
    "baxar": ("bajar", "old_x_spelling"),
    "baxo": ("bajo", "old_x_spelling"),
    "bexiga": ("vejiga", "old_x_spelling"),
    "bexigas": ("vejigas", "old_x_spelling"),
    "biexo": ("viejo", "old_x_spelling"),
    "bocabaxo": ("boca abajo", "fused_old_x_spelling"),
    "bruxa": ("bruja", "old_x_spelling"),
    "bruxula": ("brújula", "old_x_spelling"),
    "caxa": ("caja", "old_x_spelling"),
    "caxas": ("cajas", "old_x_spelling"),
    "caxcara": ("cáscara", "old_x_spelling"),
    "caxcauel": ("cascabel", "old_x_spelling"),
    "caxco": ("casco", "old_x_spelling"),
    "congoxa": ("congoja", "old_x_spelling"),
    "congoxar": ("congojar", "old_x_spelling"),
    "congoxarse": ("congojarse", "old_x_spelling"),
    "coxear": ("cojear", "old_x_spelling"),
    "coxo": ("cojo", "old_x_spelling"),
    "coxquillas": ("cosquillas", "old_x_spelling"),
    "cruximiento": ("crujimiento", "old_x_spelling"),
    "cruxir": ("crujir", "old_x_spelling"),
    "debuxar": ("dibujar", "old_x_spelling"),
    "debuxo": ("dibujo", "old_x_spelling"),
    "descaxcar": ("descascar", "old_x_spelling"),
    "desquixarar": ("desquijarar", "old_x_spelling"),
    "dexarse": ("dejarse", "old_x_spelling"),
    "embaxador": ("embajador", "old_x_spelling"),
    "empuxado": ("empujado", "old_x_spelling"),
    "empuxando": ("empujando", "old_x_spelling"),
    "empuxar": ("empujar", "old_x_spelling"),
    "empuxon": ("empujón", "old_x_spelling"),
    "enxabonar": ("enjabonar", "old_x_spelling"),
    "enxabonado": ("enjabonado", "old_x_spelling"),
    "enxaguar": ("enjuagar", "old_x_spelling"),
    "enxugar": ("enjugar", "old_x_spelling"),
    "enxugarse": ("enjugarse", "old_x_spelling"),
    "enxuto": ("enjuto", "old_x_spelling"),
    "enrexada": ("enrejada", "old_x_spelling"),
    "enrexado": ("enrejado", "old_x_spelling"),
    "enrexar": ("enrejar", "old_x_spelling"),
    "entretexer": ("entretejer", "old_x_spelling"),
    "exémplo": ("ejemplo", "old_x_spelling"),
    "exemplo": ("ejemplo", "old_x_spelling"),
    "exemplificar": ("ejemplificar", "old_x_spelling"),
    "faxa": ("faja", "old_x_spelling"),
    "faxar": ("fajar", "old_x_spelling"),
    "floxedad": ("flojedad", "old_x_spelling"),
    "floxa": ("floja", "old_x_spelling"),
    "floxas": ("flojas", "old_x_spelling"),
    "floxo": ("flojo", "old_x_spelling"),
    "floxos": ("flojos", "old_x_spelling"),
    "frixol": ("frijol", "old_x_spelling"),
    "lexos": ("lejos", "old_x_spelling"),
    "luxuria": ("lujuria", "old_x_spelling"),
    "luxuriar": ("lujuriar", "old_x_spelling"),
    "luxuriosa": ("lujuriosa", "old_x_spelling"),
    "luxurioso": ("lujurioso", "old_x_spelling"),
    "maxcar": ("mascar", "old_x_spelling"),
    "maxcara": ("máscara", "old_x_spelling"),
    "mexilla": ("mejilla", "old_x_spelling"),
    "mexillas": ("mejillas", "old_x_spelling"),
    "oxala": ("ojalá", "old_x_spelling"),
    "paxaro": ("pájaro", "old_x_spelling"),
    "paxaros": ("pájaros", "old_x_spelling"),
    "páxaro": ("pájaro", "old_x_spelling"),
    "páxaros": ("pájaros", "old_x_spelling"),
    "proximo": ("prójimo", "old_x_spelling"),
    "proximos": ("prójimos", "old_x_spelling"),
    "puxo": ("pujo", "old_x_spelling"),
    "quexa": ("queja", "old_x_spelling"),
    "quexar": ("quejar", "old_x_spelling"),
    "quexarse": ("quejarse", "old_x_spelling"),
    "quixada": ("quijada", "old_x_spelling"),
    "quixar": ("quijar", "old_x_spelling"),
    "rexa": ("reja", "old_x_spelling"),
    "rexas": ("rejas", "old_x_spelling"),
    "rexada": ("rejada", "old_x_spelling"),
    "rexir": ("regir", "old_x_spelling"),
    "roxo": ("rojo", "old_x_spelling"),
    "orexas": ("orejas", "old_x_spelling"),
    "orexera": ("orejera", "old_x_spelling"),
    "perexil": ("perejil", "old_x_spelling"),
    "troxa": ("troja", "old_x_spelling"),
    "troxe": ("troje", "old_x_spelling"),
    "troxes": ("trojes", "old_x_spelling"),
    "xabon": ("jabón", "old_x_spelling"),
    "xaraue": ("jarabe", "old_x_spelling"),
    "xeringa": ("jeringa", "old_x_spelling"),
    "xugosa": ("jugosa", "old_x_spelling"),
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
