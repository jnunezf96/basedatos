#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_ss_residual_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")
SKIP_SOURCES = {"1992 Karttunen"}


REPLACEMENTS: dict[str, tuple[str, str]] = {
    "acossado": ("acosado", "old_ss_spelling"),
    "acossar": ("acosar", "old_ss_spelling"),
    "amassadera": ("amasadera", "old_ss_spelling"),
    "amassar": ("amasar", "old_ss_spelling"),
    "amissa": ("a misa", "fused_old_ss_spelling"),
    "antecessor": ("antecesor", "old_ss_spelling"),
    "apriessa": ("aprisa", "old_ss_spelling"),
    "aquesso": ("aqueso", "old_ss_spelling"),
    "argamassa": ("argamasa", "old_ss_spelling"),
    "assada": ("asada", "old_ss_spelling"),
    "assar": ("asar", "old_ss_spelling"),
    "assechador": ("acechador", "old_ss_spelling"),
    "assechanza": ("acechanza", "old_ss_spelling"),
    "assechar": ("acechar", "old_ss_spelling"),
    "asseguradamente": ("aseguradamente", "old_ss_spelling"),
    "assegurado": ("asegurado", "old_ss_spelling"),
    "assegurador": ("asegurador", "old_ss_spelling"),
    "assegurar": ("asegurar", "old_ss_spelling"),
    "asserradas": ("aserradas", "old_ss_spelling"),
    "asserrado": ("aserrado", "old_ss_spelling"),
    "asserrador": ("aserrador", "old_ss_spelling"),
    "asserradura": ("aserradura", "old_ss_spelling"),
    "asserraduras": ("aserraduras", "old_ss_spelling"),
    "asserrar": ("aserrar", "old_ss_spelling"),
    "assentadas": ("asentadas", "old_ss_spelling"),
    "assentadero": ("asentadero", "old_ss_spelling"),
    "assentado": ("asentado", "old_ss_spelling"),
    "assentados": ("asentados", "old_ss_spelling"),
    "assentar": ("asentar", "old_ss_spelling"),
    "assentarse": ("asentarse", "old_ss_spelling"),
    "assiento": ("asiento", "old_ss_spelling"),
    "assenssios": ("ajenjos", "old_ss_spelling"),
    "assessor": ("asesor", "old_ss_spelling"),
    "assiste": ("asiste", "old_ss_spelling"),
    "assolar": ("asolar", "old_ss_spelling"),
    "assolado": ("asolado", "old_ss_spelling"),
    "assolador": ("asolador", "old_ss_spelling"),
    "assolamiento": ("asolamiento", "old_ss_spelling"),
    "assolear": ("asolear", "old_ss_spelling"),
    "assoleada": ("asoleada", "old_ss_spelling"),
    "assoluer": ("absolver", "old_ss_spelling"),
    "assombrado": ("asombrado", "old_ss_spelling"),
    "assombrar": ("asombrar", "old_ss_spelling"),
    "assosegarse": ("sosegarse", "old_ss_spelling"),
    "assaetear": ("asaetear", "old_ss_spelling"),
    "cassa": ("casa", "old_ss_spelling"),
    "cessar": ("cesar", "old_ss_spelling"),
    "colicapassio": ("cólica pasión", "old_ss_spelling"),
    "compassion": ("compasión", "old_ss_spelling"),
    "compassiuo": ("compasivo", "old_ss_spelling"),
    "confessado": ("confesado", "old_ss_spelling"),
    "confessor": ("confesor", "old_ss_spelling"),
    "cossario": ("corsario", "old_ss_spelling"),
    "defenssion": ("defensa", "old_ss_spelling"),
    "defenssor": ("defensor", "old_ss_spelling"),
    "depriessa": ("deprisa", "old_ss_spelling"),
    "despenssa": ("despensa", "old_ss_spelling"),
    "desasossegada": ("desasosegada", "old_ss_spelling"),
    "desasossegado": ("desasosegado", "old_ss_spelling"),
    "desasossegar": ("desasosegar", "old_ss_spelling"),
    "desasossegarse": ("desasosegarse", "old_ss_spelling"),
    "desasossiego": ("desasosiego", "old_ss_spelling"),
    "desossado": ("desosado", "old_ss_spelling"),
    "desossador": ("desosador", "old_ss_spelling"),
    "desossadura": ("desosadura", "old_ss_spelling"),
    "desossar": ("desosar", "old_ss_spelling"),
    "desposseido": ("desposeído", "old_ss_spelling"),
    "dessa": ("de esa", "fused_old_ss_spelling"),
    "dessabrir": ("desabrir", "old_ss_spelling"),
    "dessabrido": ("desabrido", "old_ss_spelling"),
    "dessabrirse": ("desabrirse", "old_ss_spelling"),
    "desseable": ("deseable", "old_ss_spelling"),
    "desseado": ("deseado", "old_ss_spelling"),
    "dessear": ("desear", "old_ss_spelling"),
    "desseo": ("deseo", "old_ss_spelling"),
    "desseoso": ("deseoso", "old_ss_spelling"),
    "dessollado": ("desollado", "old_ss_spelling"),
    "dessollador": ("desollador", "old_ss_spelling"),
    "dessolladura": ("desolladura", "old_ss_spelling"),
    "dessollar": ("desollar", "old_ss_spelling"),
    "dessollarse": ("desollarse", "old_ss_spelling"),
    "diligentissimo": ("diligentísimo", "old_ss_spelling"),
    "dissimular": ("disimular", "old_ss_spelling"),
    "dissoluta": ("disoluta", "old_ss_spelling"),
    "escassa": ("escasa", "old_ss_spelling"),
    "escassamente": ("escasamente", "old_ss_spelling"),
    "escasseza": ("escasez", "old_ss_spelling"),
    "escasso": ("escaso", "old_ss_spelling"),
    "espessar": ("espesar", "old_ss_spelling"),
    "espessa": ("espesa", "old_ss_spelling"),
    "espesso": ("espeso", "old_ss_spelling"),
    "espessura": ("espesura", "old_ss_spelling"),
    "essa": ("esa", "old_ss_spelling"),
    "esse": ("ese", "old_ss_spelling"),
    "esso": ("eso", "old_ss_spelling"),
    "essos": ("esos", "old_ss_spelling"),
    "essotro": ("ese otro", "old_ss_spelling"),
    "grassa": ("grasa", "old_ss_spelling"),
    "grossura": ("grosura", "old_ss_spelling"),
    "gruessa": ("gruesa", "old_ss_spelling"),
    "gruesso": ("grueso", "old_ss_spelling"),
    "gruessos": ("gruesos", "old_ss_spelling"),
    "huesso": ("hueso", "old_ss_spelling"),
    "huessos": ("huesos", "old_ss_spelling"),
    "hyssopo": ("hisopo", "old_ss_spelling"),
    "impossible": ("imposible", "old_ss_spelling"),
    "loss": ("los", "old_ss_spelling"),
    "massa": ("masa", "old_ss_spelling"),
    "messado": ("mesado", "old_ss_spelling"),
    "messador": ("mesador", "old_ss_spelling"),
    "messadura": ("mesadura", "old_ss_spelling"),
    "messar": ("mesar", "old_ss_spelling"),
    "miesses": ("mieses", "old_ss_spelling"),
    "missa": ("misa", "old_ss_spelling"),
    "nassa": ("nasa", "old_ss_spelling"),
    "necessario": ("necesario", "old_ss_spelling"),
    "necessaria": ("necesaria", "old_ss_spelling"),
    "necessarias": ("necesarias", "old_ss_spelling"),
    "necessarios": ("necesarios", "old_ss_spelling"),
    "necessidad": ("necesidad", "old_ss_spelling"),
    "necessidades": ("necesidades", "old_ss_spelling"),
    "necessitado": ("necesitado", "old_ss_spelling"),
    "negligéntissimo": ("negligentísimo", "old_ss_spelling"),
    "ofenssa": ("ofensa", "old_ss_spelling"),
    "osso": ("oso", "old_ss_spelling"),
    "ossario": ("osario", "old_ss_spelling"),
    "ouiesse": ("hubiese", "old_ss_spelling"),
    "passa": ("pasa", "old_ss_spelling"),
    "passada": ("pasada", "old_ss_spelling"),
    "passado": ("pasado", "old_ss_spelling"),
    "passados": ("pasados", "old_ss_spelling"),
    "passador": ("pasador", "old_ss_spelling"),
    "passadero": ("pasadero", "old_ss_spelling"),
    "passaje": ("pasaje", "old_ss_spelling"),
    "passajero": ("pasajero", "old_ss_spelling"),
    "passamiento": ("pasamiento", "old_ss_spelling"),
    "passando": ("pasando", "old_ss_spelling"),
    "passar": ("pasar", "old_ss_spelling"),
    "passarse": ("pasarse", "old_ss_spelling"),
    "passatiempo": ("pasatiempo", "old_ss_spelling"),
    "passatiémpo": ("pasatiempo", "old_ss_spelling"),
    "passion": ("pasión", "old_ss_spelling"),
    "passo": ("paso", "old_ss_spelling"),
    "passos": ("pasos", "old_ss_spelling"),
    "passeadero": ("paseadero", "old_ss_spelling"),
    "passearse": ("pasearse", "old_ss_spelling"),
    "permission": ("permisión", "old_ss_spelling"),
    "posession": ("posesión", "old_ss_spelling"),
    "posseedor": ("poseedor", "old_ss_spelling"),
    "posseer": ("poseer", "old_ss_spelling"),
    "possible": ("posible", "old_ss_spelling"),
    "possession": ("posesión", "old_ss_spelling"),
    "procession": ("procesión", "old_ss_spelling"),
    "processo": ("proceso", "old_ss_spelling"),
    "profession": ("profesión", "old_ss_spelling"),
    "professo": ("profeso", "old_ss_spelling"),
    "promessa": ("promesa", "old_ss_spelling"),
    "priessa": ("prisa", "old_ss_spelling"),
    "rebossadura": ("rebosadura", "old_ss_spelling"),
    "rebossar": ("rebosar", "old_ss_spelling"),
    "remission": ("remisión", "old_ss_spelling"),
    "ressollando": ("resollando", "old_ss_spelling"),
    "salssa": ("salsa", "old_ss_spelling"),
    "sanctissimo": ("santísimo", "old_ss_spelling"),
    "siesso": ("sieso", "old_ss_spelling"),
    "tassa": ("tasa", "old_ss_spelling"),
    "tassada": ("tasada", "old_ss_spelling"),
    "tassador": ("tasador", "old_ss_spelling"),
    "tassar": ("tasar", "old_ss_spelling"),
    "tosse": ("tos", "old_ss_spelling"),
    "traspassar": ("traspasar", "old_ss_spelling"),
    "trauessura": ("travesura", "old_ss_spelling"),
    "trauiesso": ("travieso", "old_ss_spelling"),
    "yesso": ("yeso", "old_ss_spelling"),
    "acaeciesse": ("acaeciese", "old_ss_spelling"),
    "aessotra": ("a esa otra", "fused_old_ss_spelling"),
    "amassador": ("amasador", "old_ss_spelling"),
    "amassadura": ("amasadura", "old_ss_spelling"),
    "apassionado": ("apasionado", "old_ss_spelling"),
    "aprissa": ("aprisa", "old_ss_spelling"),
    "asessor": ("asesor", "old_ss_spelling"),
    "asossegarse": ("sosegarse", "old_ss_spelling"),
    "assadura": ("asadura", "old_ss_spelling"),
    "assaeteado": ("asaeteado", "old_ss_spelling"),
    "assaeteador": ("asaeteador", "old_ss_spelling"),
    "assaeteamiento": ("asaeteamiento", "old_ss_spelling"),
    "assamiento": ("asamiento", "old_ss_spelling"),
    "assador": ("asador", "old_ss_spelling"),
    "assentador": ("asentador", "old_ss_spelling"),
    "assentamiento": ("asentamiento", "old_ss_spelling"),
    "asserrar": ("aserrar", "old_ss_spelling"),
    "asserrarla": ("aserrarla", "old_ss_spelling"),
    "asserrarse": ("aserrarse", "old_ss_spelling"),
    "assientos": ("asientos", "old_ss_spelling"),
    "assientan": ("asientan", "old_ss_spelling"),
    "assir": ("asir", "old_ss_spelling"),
    "assimismo": ("asimismo", "old_ss_spelling"),
    "assomado": ("asomado", "old_ss_spelling"),
    "assomadura": ("asomadura", "old_ss_spelling"),
    "assomar": ("asomar", "old_ss_spelling"),
    "assombrador": ("asombrador", "old_ss_spelling"),
    "assombramiento": ("asombramiento", "old_ss_spelling"),
    "assómbrarse": ("asombrarse", "old_ss_spelling"),
    "assuelto": ("absuelto", "old_ss_spelling"),
    "cessando": ("cesando", "old_ss_spelling"),
    "compassar": ("compasar", "old_ss_spelling"),
    "compassada": ("compasada", "old_ss_spelling"),
    "comprehenssion": ("comprensión", "old_ss_spelling"),
    "concession": ("concesión", "old_ss_spelling"),
    "confiessa": ("confiesa", "old_ss_spelling"),
    "cónfessador": ("confesador", "old_ss_spelling"),
    "confusoassi": ("confuso así", "fused_old_ss_spelling"),
    "confussion": ("confusión", "old_ss_spelling"),
    "cosso": ("coso", "old_ss_spelling"),
    "cuesso": ("cuezo", "old_ss_spelling"),
    "delgadissima": ("delgadísima", "old_ss_spelling"),
    "desapassionado": ("desapasionado", "old_ss_spelling"),
    "desapassionar": ("desapasionar", "old_ss_spelling"),
    "desassosiego": ("desasosiego", "old_ss_spelling"),
    "desossada": ("desosada", "old_ss_spelling"),
    "dessabrida": ("desabrida", "old_ss_spelling"),
    "dessabridamente": ("desabridamente", "old_ss_spelling"),
    "dessabrimiento": ("desabrimiento", "old_ss_spelling"),
    "dessea": ("desea", "old_ss_spelling"),
    "desseada": ("deseada", "old_ss_spelling"),
    "dessemejante": ("desemejante", "old_ss_spelling"),
    "dessemejantemente": ("desemejantemente", "old_ss_spelling"),
    "dessemejar": ("desemejar", "old_ss_spelling"),
    "dessollada": ("desollada", "old_ss_spelling"),
    "dessossar": ("desosar", "old_ss_spelling"),
    "desso": ("de eso", "fused_old_ss_spelling"),
    "dissoluto": ("disoluto", "old_ss_spelling"),
    "engrossar": ("engrosar", "old_ss_spelling"),
    "esnecessario": ("es necesario", "fused_old_ss_spelling"),
    "espessada": ("espesada", "old_ss_spelling"),
    "espessarse": ("espesarse", "old_ss_spelling"),
    "essencia": ("esencia", "old_ss_spelling"),
    "essotra": ("esa otra", "old_ss_spelling"),
    "expressar": ("expresar", "old_ss_spelling"),
    "finissimo": ("finísimo", "old_ss_spelling"),
    "fuesse": ("fuese", "old_ss_spelling"),
    "fuessen": ("fuesen", "old_ss_spelling"),
    "grassiento": ("grasiento", "old_ss_spelling"),
    "grossera": ("grosera", "old_ss_spelling"),
    "gruessas": ("gruesas", "old_ss_spelling"),
    "impassibilidad": ("impasibilidad", "old_ss_spelling"),
    "ingratissimo": ("ingratísimo", "old_ss_spelling"),
    "intercessor": ("intercesor", "old_ss_spelling"),
    "jassando": ("sajando", "old_ss_spelling"),
    "jassadura": ("sajadura", "old_ss_spelling"),
    "jassar": ("sajar", "old_ss_spelling"),
    "manssa": ("mansa", "old_ss_spelling"),
    "messandose": ("mesándose", "old_ss_spelling"),
    "messurado": ("mesurado", "old_ss_spelling"),
    "messuradamente": ("mesuradamente", "old_ss_spelling"),
    "messurarse": ("mesurarse", "old_ss_spelling"),
    "missal": ("misal", "old_ss_spelling"),
    "necessariamente": ("necesariamente", "old_ss_spelling"),
    "necessitada": ("necesitada", "old_ss_spelling"),
    "omission": ("omisión", "old_ss_spelling"),
    "ossero": ("osero", "old_ss_spelling"),
    "ossorio": ("osorio", "old_ss_spelling"),
    "passagero": ("pasajero", "old_ss_spelling"),
    "passan": ("pasan", "old_ss_spelling"),
    "passea": ("pasea", "old_ss_spelling"),
    "penssar": ("pensar", "old_ss_spelling"),
    "possee": ("posee", "old_ss_spelling"),
    "possiblemente": ("posiblemente", "old_ss_spelling"),
    "pressa": ("prisa", "old_ss_spelling"),
    "reprehenssion": ("reprehensión", "old_ss_spelling"),
    "sesso": ("seso", "old_ss_spelling"),
    "sucessiua": ("sucesiva", "old_ss_spelling"),
    "sucessiva": ("sucesiva", "old_ss_spelling"),
    "sucessor": ("sucesor", "old_ss_spelling"),
    "sucessores": ("sucesores", "old_ss_spelling"),
    "successor": ("sucesor", "old_ss_spelling"),
    "tosser": ("toser", "old_ss_spelling"),
    "tuuiessemos": ("tuviésemos", "old_ss_spelling"),
    "vassijas": ("vasijas", "old_ss_spelling"),
    "vassos": ("vasos", "old_ss_spelling"),
    "ympassibilidad": ("impasibilidad", "old_ss_spelling"),
    "ympression": ("impresión", "old_ss_spelling"),
    "yngratissimo": ("ingratísimo", "old_ss_spelling"),
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
