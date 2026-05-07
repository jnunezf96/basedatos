#!/usr/bin/env python3
from __future__ import annotations

import gzip
import html
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "wimmer_translation_es_normalize_report.jsonl"


CIRCUMFLEX_TO_MACRON = str.maketrans(
    {
        "â": "ā",
        "ê": "ē",
        "î": "ī",
        "ô": "ō",
        "û": "ū",
        "Â": "Ā",
        "Ê": "Ē",
        "Î": "Ī",
        "Ô": "Ō",
        "Û": "Ū",
    }
)

DANGLING_OPEN_PAREN_RE = re.compile(r"\s*\((?:[.,;:])?\s*$")
BROKEN_OPEN_PAREN_RE = re.compile(r"\s*\(\s*([,.;:])\s*")
OPEN_SOURCE_PAREN_RE = re.compile(r"\s*\((?:Hern|Molina|Sah|SIS|ECN|Acad\s+Hist|Launey)[^)]*$", re.I)
PAREN_SOURCE_RE = re.compile(
    r"\s*\((?:Hern\.?|Molina[^)]*|Sah[^)]*|SIS[^)]*|ECN[^)]*|Acad\s+Hist[^)]*|Launey[^)]*)\)",
    re.I,
)
SIM_RE = re.compile(r"\s*R\.?\s*Sim[eé]on\b[^./]*(?:\([^)]*\))?\.?", re.I)
MOLINA_RE = re.compile(r"\s*Molina\s+[IVXLCDM]+\s+\d+[rv]?\.?", re.I)
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:])")
MULTISPACE_RE = re.compile(r"\s+")


REPLACEMENTS = [
    ("v. inanimado,", "v.inanim.,"),
    ("v. inanimado.", "v.inanim."),
    ("v. inanimados,", "v.inanim.,"),
    ("v. inanimados.", "v.inanim."),
    ("v.inanimado,", "v.inanim.,"),
    ("v.inanimado.", "v.inanim."),
    ("vi.i.,", "v.i.,"),
    ("vi,", "v.i.,"),
    ("v.passif.,", "pasivo,"),
    ("v.passif.", "pasivo."),
    ("v.pasivo-impers.,", "v.impers.,"),
    ("v.pasivo-impers.", "v.impers."),
    ("v. recipr.,", "v.recipr.,"),
    ("v.t. head-.,", "v.t. tē-.,"),
    ("v.t., head-.,", "v.t. tē-.,"),
    ("v.refl. con significado pasivo.,", "v.refl. con significado pasivo,"),
    ("v.refl. en sentido pasivo.,", "v.refl. en sentido pasivo,"),
    ("metáfora.,", "metáfora:"),
]


TARGETED_FIXES = {
    "2021-wimmer:000027": "Hondero, que tira piedras con una honda.",
    "2021-wimmer:000028": "Hondero, que tira piedras con una honda.",
    "2021-wimmer:000246": "Con mochila, que lleva una mochila.",
    "2021-wimmer:000383": "Hablador, el que responde y habla mucho. / El que piensa, sueña, está pensativo o preocupado.",
    "2021-wimmer:002034": "v.refl., caer en un hoyo. / impers., caer en agujeros. / impers., hacer caer a otro en un hoyo.",
    "2021-wimmer:006184": "v.t. tē-., golpear continuamente a alguien con lanza o pie.",
    "2021-wimmer:007528": "v.t. tla-., estar ocupado con una sola cosa; entender sólo eso.",
    "2021-wimmer:008482": "botánica: otro nombre para una planta llamada zacapolin.",
    "2021-wimmer:009297": "v.impers., nevar.",
    "2021-wimmer:009637": "Título divino relacionado con Chantico; cabeza de lobo.",
    "2021-wimmer:009700": "Tejido calado.",
    "2021-wimmer:009732": "v.t. tla-., creer con firmeza.",
    "2021-wimmer:010337": "Enchilada.",
    "2021-wimmer:011134": "Pava. / pavo asado. / plural: pavos.",
    "2021-wimmer:011610": "Placer, disfrute. / juguete.",
    "2021-wimmer:011921": "v.inanim., agacharse, voltearse o doblarse, hablando de pared. / v.i., encorvarse por la edad. / metáfora: castigar duramente.",
    "2021-wimmer:012481": "botánica: planta medicinal usada contra el reumatismo y enfermedades de la piel.",
    "2021-wimmer:013257": "Reptil de cabeza marrón, parecido al lagarto.",
    "2021-wimmer:013791": "zoología: ardilla de bosque.",
    "2021-wimmer:013885": "Remedio para dolencias laterales. / botánica: nombre de planta también llamada chiyantzotzoltōn.",
    "2021-wimmer:014427": "locativo: donde algo florece o brilla. / forma poseída. / topónimo.",
    "2021-wimmer:015077": "v.t. tla-., pelar la rabadilla del ave o quitarle la cola.",
    "2021-wimmer:016949": "v.t. tla-., hacer que una cosa vaya acompañada de otra. / v.bitrans. tētla-., hacer que alguien tome algo.",
    "2021-wimmer:017666": "v.i., preparar cacao u otra bebida. / v.i., adivinar en agua. / v.impers., tener agua en lebrillo o recipiente ancho.",
    "2021-wimmer:018603": "v.t. tla-., encontrar una cosa a tiempo o en sazón.",
    "2021-wimmer:019038": "botánica: nombre de una planta; especie de verdolaga.",
    "2021-wimmer:019264": "Cocido, hervido.",
    "2021-wimmer:004776": "v.t. tē-., examinar o indagar sobre algún asunto.",
    "2021-wimmer:021331": "Honor, estima, bien. / forma poseída: guardia, cubierta.",
    "2021-wimmer:021674": "v.t. tē-., golpear o herir a alguien con la mano. / v.t. tla-., frotar algo con la mano, aplicar ungüento. / v.refl., torcerse el pie al pisar una piedra. / metáfora: perdonar, mostrar misericordia o consolar.",
    "2021-wimmer:022246": "v.i., hacer cordeles.",
    "2021-wimmer:022570": "botánica: arbusto cuyas hojas se usan para curar heridas y llagas; también llamado ōmexōchitl.",
    "2021-wimmer:022748": "Desove; huevos de peces fertilizados.",
    "2021-wimmer:023625": "v.t. tla-., hacer espuma en el agua removiéndola. / v.t. tla-., dividir, compartir o desmenuzar una cosa.",
    "2021-wimmer:024624": "v.refl., engordar. / v.t. tē-., aburrir o preocupar a alguien; molestar.",
    "2021-wimmer:024460": "v.i., hacer o establecer leyes.",
    "2021-wimmer:025976": "Pato salvaje común en el lago de Tetzcoco.",
    "2021-wimmer:025342": "v.t. tē-., separar a personas que discuten; hacerlas divorciarse. / v.t. tla-., separar, despegar o distanciar una cosa de otra.",
    "2021-wimmer:026065": "v.t. tla-., golpear o herir una cosa con otra. / v.refl., chocar unas cosas con otras.",
    "2021-wimmer:026067": "v.t. tē-., levantar o excitar a personas unas contra otras. / v.t. tla-., golpear o herir una cosa con otra.",
    "2021-wimmer:026077": "v.t. tla-., golpear o herir una cosa con otra. / v.refl., chocar unas cosas con otras.",
    "2021-wimmer:026078": "v.t. tē-., levantar o excitar a personas unas contra otras. / v.t. tla-., golpear o herir una cosa con otra.",
    "2021-wimmer:026432": "v.t. tla-., hacer algo dulce y sabroso.",
    "2021-wimmer:027258": "botánica: nombre de una planta también llamada teocōxōchitl.",
    "2021-wimmer:027419": "botánica: planta medicinal que produce una goma llamada tzictli.",
    "2021-wimmer:027702": "v.i., cavar un hoyo, zanja o pozo.",
    "2021-wimmer:028894": "v.refl., estar encerrado en una caja. / metáfora: tener firmeza, soportar la desgracia.",
    "2021-wimmer:028326": "v.t. tla-. o nic-., preferir, amar o estimar una cosa más que otra.",
    "2021-wimmer:030097": "Cisne.",
    "2021-wimmer:031299": "Bocananga, cobija.",
    "2021-wimmer:031404": "v.i., hacer carbón.",
    "2021-wimmer:031457": "v.i., hacer carbón.",
    "2021-wimmer:031461": "v.i., hacer carbón.",
    "2021-wimmer:031465": "v.t. tla-., hacer carbón vegetal.",
    "2021-wimmer:034311": "v.t. tē-., calumniar, desmerecer o denigrar a alguien. / v.t. tla-., recriminar o calumniar.",
    "2021-wimmer:035130": "v.i., hacer cacao para beber.",
    "2021-wimmer:035289": "v.i., preparar cacao.",
    "2021-wimmer:031735": "Fiesta de los señores. / calendario: octava fiesta anual.",
    "2021-wimmer:035991": "Cirugía. / acción de aserrar piedras.",
    "2021-wimmer:038278": "Piedra blanca con manchas; usada como amuleto para favorecer la lactancia.",
    "2021-wimmer:039956": "Penitente, devoto, religioso. / plural: ancianos dedicados al ministerio de los sacrificios.",
    "2021-wimmer:040522": "v.impers., hacer tiempo claro y sereno.",
    "2021-wimmer:041731": "botánica: nombre de planta también llamada zacacamohtotōntin.",
    "2021-wimmer:041865": "v.t. tē-., hacer una cama a alguien.",
}


def normalize(value: str, record_id: str) -> str:
    if record_id in TARGETED_FIXES:
        return TARGETED_FIXES[record_id]

    text = html.unescape(value or "").strip()
    text = text.translate(CIRCUMFLEX_TO_MACRON)

    for old, new in REPLACEMENTS:
        text = text.replace(old, new)

    text = PAREN_SOURCE_RE.sub("", text)
    text = OPEN_SOURCE_PAREN_RE.sub("", text)
    text = SIM_RE.sub("", text)
    text = MOLINA_RE.sub("", text)
    text = BROKEN_OPEN_PAREN_RE.sub(r" ", text)
    text = DANGLING_OPEN_PAREN_RE.sub("", text)

    text = re.sub(r",\s*/", " /", text)
    text = re.sub(r"/\s*,", "/", text)
    text = re.sub(r"(?<!-)\s*/\s*(?![a-zA-ZāēīōūĀĒĪŌŪ]+-)", " / ", text)
    text = re.sub(r"\b(v\.[^,./]+,\s*)/\s*", r"\1", text)
    text = re.sub(r"\s*/\s*/\s*", " / ", text)
    text = re.sub(r"\s+/\s+", " / ", text)

    text = SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)
    text = re.sub(r"([,;:])\1+", r"\1", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\b([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+),\s+\1\b", r"\1", text, flags=re.I)
    text = MULTISPACE_RE.sub(" ", text).strip(" ,;:")
    if text and text[-1] not in ".!?":
        text += "."
    return text


def main() -> None:
    rows = []
    report = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("Fuente") == "2021 Wimmer":
                old = row.get("Traducción (es)") or ""
                new = normalize(old, row.get("record_id", ""))
                if new != old:
                    row["Traducción (es)"] = new
                    report.append(
                        {
                            "record_id": row.get("record_id"),
                            "lemma": row.get("Texto estandarizado"),
                            "old_translation_es": old,
                            "new_translation_es": new,
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
