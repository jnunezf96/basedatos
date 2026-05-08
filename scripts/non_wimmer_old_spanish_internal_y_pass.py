#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_internal_y_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")
SKIP_SOURCES = {"1992 Karttunen"}


PHRASE_REPLACEMENTS: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(
            r"\b(?P<prefix>[Pp]ro(?:u|v)ocad[oa]s?(?: de otros)?|[Pp]ro(?:u|v)oca(?: a otros?| a otro| de otros)?|[Pp]ro(?:u|v)ocar(?: a otros?| a otro| de otros)?) ayra\b"
        ),
        r"\g<prefix> a ira",
        "old_internal_y_phrase",
    ),
    (
        re.compile(r"\[j\]uyzio", re.I),
        "juicio",
        "old_internal_y_phrase",
    ),
    (
        re.compile(r"\bestruydo \[estruendo\]", re.I),
        "estruendo",
        "old_internal_y_phrase",
    ),
    (
        re.compile(r"\bse ayra\b", re.I),
        "se aira",
        "old_internal_y_phrase",
    ),
]


REPLACEMENTS: dict[str, tuple[str, str]] = {
    "afeytador": ("afeitador", "old_internal_y_spelling"),
    "afeytar": ("afeitar", "old_internal_y_spelling"),
    "afeytarse": ("afeitarse", "old_internal_y_spelling"),
    "ahuyr": ("a huir", "old_internal_y_fused"),
    "alcayde": ("alcaide", "old_internal_y_spelling"),
    "arguyr": ("argüir", "old_internal_y_spelling"),
    "ayrada": ("airada", "old_internal_y_spelling"),
    "ayradamente": ("airadamente", "old_internal_y_spelling"),
    "ayrado": ("airado", "old_internal_y_spelling"),
    "ayrar": ("airar", "old_internal_y_spelling"),
    "ayrarse": ("airarse", "old_internal_y_spelling"),
    "ayre": ("aire", "old_internal_y_spelling"),
    "ayres": ("aires", "old_internal_y_spelling"),
    "azeyte": ("aceite", "old_internal_y_spelling"),
    "azeytera": ("aceitera", "old_internal_y_spelling"),
    "baylador": ("bailador", "old_internal_y_spelling"),
    "bayladora": ("bailadora", "old_internal_y_spelling"),
    "baylan": ("bailan", "old_internal_y_spelling"),
    "baylar": ("bailar", "old_internal_y_spelling"),
    "bayle": ("baile", "old_internal_y_spelling"),
    "cabezcaydo": ("cabizcaído", "old_internal_y_spelling"),
    "cayda": ("caída", "old_internal_y_spelling"),
    "caydas": ("caídas", "old_internal_y_spelling"),
    "caydo": ("caído", "old_internal_y_spelling"),
    "caydos": ("caídos", "old_internal_y_spelling"),
    "concluyda": ("concluida", "old_internal_y_spelling"),
    "concluyr": ("concluir", "old_internal_y_spelling"),
    "concluyrse": ("concluirse", "old_internal_y_spelling"),
    "cuydado": ("cuidado", "old_internal_y_spelling"),
    "deleytable": ("deleitable", "old_internal_y_spelling"),
    "deleytarse": ("deleitarse", "old_internal_y_spelling"),
    "deleyte": ("deleite", "old_internal_y_spelling"),
    "deleytes": ("deleites", "old_internal_y_spelling"),
    "deleytoso": ("deleitoso", "old_internal_y_spelling"),
    "demayz": ("de maíz", "old_internal_y_fused"),
    "derays": ("de raíz", "old_internal_y_fused"),
    "descuydado": ("descuidado", "old_internal_y_spelling"),
    "descuydo": ("descuido", "old_internal_y_spelling"),
    "destruydor": ("destruidor", "old_internal_y_spelling"),
    "destruyr": ("destruir", "old_internal_y_spelling"),
    "destruyrme": ("destruirme", "old_internal_y_spelling"),
    "destruyrse": ("destruirse", "old_internal_y_spelling"),
    "detraydo": ("detraído", "old_internal_y_spelling"),
    "deyr": ("de ir", "old_internal_y_fused"),
    "deziseys": ("dieciséis", "old_internal_y_spelling"),
    "donayre": ("donaire", "old_internal_y_spelling"),
    "donayres": ("donaires", "old_internal_y_spelling"),
    "empeyne": ("empeine", "old_internal_y_spelling"),
    "empeynes": ("empeines", "old_internal_y_spelling"),
    "enbaydor": ("embaidor", "old_internal_y_spelling"),
    "enseys": ("en seis", "old_internal_y_fused"),
    "estruydo": ("estruendo", "old_internal_y_spelling"),
    "estarya": ("estaría", "old_internal_y_spelling"),
    "estays": ("estáis", "old_internal_y_spelling"),
    "frayle": ("fraile", "old_internal_y_spelling"),
    "frayles": ("frailes", "old_internal_y_spelling"),
    "freyr": ("freír", "old_internal_y_spelling"),
    "fruyr": ("fruir", "old_internal_y_spelling"),
    "gayta": ("gaita", "old_internal_y_spelling"),
    "gaytero": ("gaitero", "old_internal_y_spelling"),
    "hazeys": ("hacéis", "old_internal_y_spelling"),
    "huyda": ("huida", "old_internal_y_spelling"),
    "huydizo": ("huidizo", "old_internal_y_spelling"),
    "huydo": ("huido", "old_internal_y_spelling"),
    "huydor": ("huidor", "old_internal_y_spelling"),
    "huyr": ("huir", "old_internal_y_spelling"),
    "instruyr": ("instruir", "old_internal_y_spelling"),
    "juyzio": ("juicio", "old_internal_y_spelling"),
    "leyda": ("leída", "old_internal_y_spelling"),
    "leydo": ("leído", "old_internal_y_spelling"),
    "martyr": ("mártir", "old_internal_y_spelling"),
    "martyrio": ("martirio", "old_internal_y_spelling"),
    "mays": ("maíz", "old_internal_y_spelling"),
    "mayz": ("maíz", "old_internal_y_spelling"),
    "mayzal": ("maizal", "old_internal_y_spelling"),
    "mayztostado": ("maíz tostado", "old_internal_y_fused"),
    "mosayca": ("mosaica", "old_internal_y_spelling"),
    "naypes": ("naipes", "old_internal_y_spelling"),
    "naypez": ("naipes", "old_internal_y_spelling"),
    "oyda": ("oída", "old_internal_y_spelling"),
    "oydo": ("oído", "old_internal_y_spelling"),
    "oydores": ("oidores", "old_internal_y_spelling"),
    "oydos": ("oídos", "old_internal_y_spelling"),
    "oydor": ("oidor", "old_internal_y_spelling"),
    "oyr": ("oír", "old_internal_y_spelling"),
    "oyrse": ("oírse", "old_internal_y_spelling"),
    "oys": ("oís", "old_internal_y_spelling"),
    "parayso": ("paraíso", "old_internal_y_spelling"),
    "penseys": ("penséis", "old_internal_y_spelling"),
    "perjuyzio": ("perjuicio", "old_internal_y_spelling"),
    "perteceys": ("pertenecéis", "old_internal_y_spelling"),
    "peynado": ("peinado", "old_internal_y_spelling"),
    "peynadura": ("peinadura", "old_internal_y_spelling"),
    "peynar": ("peinar", "old_internal_y_spelling"),
    "peynarse": ("peinarse", "old_internal_y_spelling"),
    "peyne": ("peine", "old_internal_y_spelling"),
    "peynes": ("peines", "old_internal_y_spelling"),
    "pleyteador": ("pleiteador", "old_internal_y_spelling"),
    "pleyteantes": ("pleiteantes", "old_internal_y_spelling"),
    "pleyteauan": ("pleiteaban", "old_internal_y_spelling"),
    "pleytomenaje": ("pleito homenaje", "old_internal_y_fused"),
    "pleyto": ("pleito", "old_internal_y_spelling"),
    "pleytos": ("pleitos", "old_internal_y_spelling"),
    "preceys": ("preciéis", "old_internal_y_spelling"),
    "proueyda": ("proveída", "old_internal_y_spelling"),
    "rayda": ("raída", "old_internal_y_spelling"),
    "rayz": ("raíz", "old_internal_y_spelling"),
    "rayzes": ("raíces", "old_internal_y_spelling"),
    "recibireys": ("recibiréis", "old_internal_y_spelling"),
    "retraydo": ("retraído", "old_internal_y_spelling"),
    "retraymiento": ("retraimiento", "old_internal_y_spelling"),
    "reyna": ("reina", "old_internal_y_spelling"),
    "reynado": ("reinado", "old_internal_y_spelling"),
    "reynar": ("reinar", "old_internal_y_spelling"),
    "reyno": ("reino", "old_internal_y_spelling"),
    "reynos": ("reinos", "old_internal_y_spelling"),
    "reyr": ("reír", "old_internal_y_spelling"),
    "reyrme": ("reírme", "old_internal_y_spelling"),
    "reyrse": ("reírse", "old_internal_y_spelling"),
    "royda": ("roída", "old_internal_y_spelling"),
    "rreyno": ("reino", "old_internal_y_spelling"),
    "ruydo": ("ruido", "old_internal_y_spelling"),
    "seays": ("seáis", "old_internal_y_spelling"),
    "seys": ("seis", "old_internal_y_spelling"),
    "sonreyrse": ("sonreírse", "old_internal_y_spelling"),
    "sostituyr": ("sustituir", "old_internal_y_spelling"),
    "soys": ("sois", "old_internal_y_spelling"),
    "trayda": ("traída", "old_internal_y_spelling"),
    "traydas": ("traídas", "old_internal_y_spelling"),
    "traydor": ("traidor", "old_internal_y_spelling"),
    "treynta": ("treinta", "old_internal_y_spelling"),
    "veynte": ("veinte", "old_internal_y_spelling"),
    "veys": ("veis", "old_internal_y_spelling"),
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
        replaced = pattern.sub(replacement, new)
        if replaced != new:
            new = replaced
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
