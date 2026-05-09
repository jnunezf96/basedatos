#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import re
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
REPORT_PATH = Path("scripts/spanish_languagetool_context_report.jsonl")


TOKEN_REPLACEMENTS = {
    # User-reviewed LanguageTool candidates.
    "alimpiada": "limpiada",
    "alimpiadas": "limpiadas",
    "alímpiada": "limpiada",
    "alimpiado": "limpiado",
    "alimpiados": "limpiados",
    "alimpiaduras": "limpiaduras",
    "alimpiador": "limpiador",
    "alimpiadero": "limpiadero",
    "mollidura": "mullidura",
    "frisol": "frijol",
    "frisoles": "frijoles",
    "frisolar": "frijolar",
    "asementado": "sementado",
    "asemillado": "semillado",
    "estropiezo": "tropiezo",
    "comprehendedor": "comprendedor",
    "comprehendida": "comprendida",
    "comprehenderla": "comprenderla",
    "ados": "a dos",
    "animalias": "animalías",
    "acevilarse": "acivilarse",
    "acevilado": "acivilado",
    "acevilizarse": "acivilizarse",
    # Current visible LanguageTool cluster, checked against parallel rows.
    "risar": "rifar",
    "estrañarse": "extrañarse",
    "enerisarse": "enerizarse",
    "desuelado": "desvelado",
    "frequentadamente": "frecuentemente",
    "frequentadas": "frecuentadas",
    "pocoa": "poco ha",
    "hínchir": "henchir",
    "hinchir": "henchir",
    "hechir": "henchir",
    "hencher": "henchir",
    "sunto": "sumo",
    # Same reviewed clusters.
    "guedeia": "guedeja",
    "emmarañada": "enmarañada",
    "descerrugado": "descervigado",
    "énuarado": "envarado",
    # Fused forms whose root is valid Spanish dolar 'desbastar/labrar'.
    "dolaralgo": "dolar algo",
    # Next visible cluster: direct spelling and fused-form fixes.
    "alogro": "a logro",
    "desgusto": "disgusto",
    "desto": "de esto",
    "desuario": "desvarío",
    "elar": "helar",
    "herviente": "hirviente",
    "pecilgo": "pellizco",
    "pixa": "pija",
    "quele": "que le",
    "soberbecerse": "ensoberbecerse",
    "agorear": "agorar",
    "apezgar": "apesgar",
    "endar": "en dar",
    "enquatro": "en cuatro",
    "dequatro": "de cuatro",
    "niygual": "ni igual",
    # Next visible cluster: mostly old orthography with clear modern forms.
    "acucharrada": "acucharada",
    "arojar": "arrojar",
    "atericiado": "ictericiado",
    "avna": "a una",
    "corua": "corva",
    "encensado": "incensado",
    "exear": "oxear",
    "eñel": "en el",
    "falza": "falsa",
    "haragania": "haraganería",
    "hechan": "echan",
    "hechando": "echando",
    "inabil": "inhábil",
    "javali": "jabalí",
    "magánta": "maganta",
    "mazoral": "mazorral",
    "meloxa": "meloja",
    "mescla": "mezcla",
    "mesclada": "mezclada",
    "micericordia": "misericordia",
    "mollida": "mullida",
    "moxca": "mosca",
    "moxcas": "moscas",
    "moxcada": "moscada",
    "negosio": "negocio",
    "nequén": "henequén",
    "nieblina": "neblina",
    "ocidental": "occidental",
    "oluidado": "olvidado",
    "padese": "padece",
    "pleveya": "plebeya",
    "poluos": "polvos",
    "proverse": "proveerse",
    "rosiar": "rociar",
    "sugeto": "sujeto",
    "tiguere": "tigre",
    "trahe": "trae",
    "vañar": "bañar",
    "vaño": "baño",
    "xabonar": "jabonar",
    "xeme": "jeme",
    "xicara": "jícara",
    "xicaras": "jícaras",
    # Next visible 5-count cluster: direct modern spellings and fused forms.
    "acorrucandose": "acurrucándose",
    "anocher": "anochecer",
    "apechos": "a pecho",
    "aqual": "a cuál",
    "atodas": "a todas",
    "atratar": "a tratar",
    "aucente": "ausente",
    "caruonero": "carbonero",
    "caxcar": "cascar",
    "cenogil": "cenojil",
    "cheremia": "chirimía",
    "chiminea": "chimenea",
    "cieruo": "ciervo",
    "cobdicioso": "codicioso",
    "concentir": "consentir",
    "corcoba": "corcova",
    "coxcorron": "coscorrón",
    "debuxada": "dibujada",
    "dende": "desde",
    "desapercebido": "desapercibido",
    "desempedagor": "desempedrador",
    "desonestas": "deshonestas",
    "desotra": "de esa otra",
    "desuanecer": "desvanecer",
    "desuelarse": "desvelarse",
    "desvaratada": "desbaratada",
    "differente": "diferente",
    "disfrasado": "disfrazado",
    "ditado": "dictado",
    "divinación": "adivinación",
    "eclipsi": "eclipse",
    "emmudecer": "enmudecer",
    "emméndada": "enmendada",
    "encensar": "incensar",
    "encoruar": "encorvar",
    "eneste": "en este",
    "entresi": "entre sí",
    "entretexida": "entretejida",
    "entretexido": "entretejido",
    "entricada": "intrincada",
    "envegecer": "envejecer",
    "enxalzar": "ensalzar",
    "esaminada": "examinada",
    "escojer": "escoger",
    "escopir": "escupir",
    "escusandose": "excusándose",
    "espendiendo": "expendiendo",
    "espremida": "exprimida",
    "espremido": "exprimido",
    "estorvo": "estorbo",
    "estremada": "extremada",
    "executar": "ejecutar",
    "fortunado": "afortunado",
    "friscal": "fiscal",
    "fructa": "fruta",
    "garvanzos": "garbanzos",
    "geme": "jeme",
    "ginetear": "jinetear",
    "hade": "ha de",
    "hagome": "me hago",
    "haser": "hacer",
    "herege": "hereje",
    "hidionda": "hedionda",
    "hortiga": "ortiga",
    "libiana": "liviana",
    "madexa": "madeja",
    "magestuosa": "majestuosa",
    "mancedumbre": "mansedumbre",
    "masorca": "mazorca",
    "mestruo": "menstruo",
    "mollido": "mullido",
    "mordificar": "mordiscar",
    "moxcatel": "moscatel",
    "muchacherria": "muchachería",
    "muger": "mujer",
    "nuve": "nube",
    "omenaje": "homenaje",
    "onesta": "honesta",
    "pecilgar": "pellizcar",
    "pluvia": "lluvia",
    "porlo": "por lo",
    "portatile": "portátil",
    "provada": "probada",
    "ranaquajo": "renacuajo",
    "rebatada": "arrebatada",
    "rebenton": "reventón",
    "recompenzar": "recompensar",
    "recoxer": "recoger",
    "redondes": "redondez",
    "regazado": "arregazado",
    "remanzo": "remanso",
    # Next visible 5-count cluster.
    "resurrection": "resurrección",
    "rompida": "rota",
    "rovar": "robar",
    "rreal": "real",
    "saluo": "salvo",
    "sepulchro": "sepulcro",
    "seruido": "servido",
    "sincel": "cincel",
    "sincelar": "cincelar",
    "soberuiamente": "soberbiamente",
    "suabe": "suave",
    "torondon": "tolondrón",
    "torondones": "tolondrones",
    "torondrones": "tolondrones",
    "troupiale": "trupial",
    "tverto": "tuerto",
    "valet": "ayuda de cámara",
    "vandear": "bandear",
    "varandas": "barandas",
    "verguensa": "vergüenza",
    "vidro": "vidrio",
    "visage": "visaje",
    "xaguei": "jagüey",
    "xicalas": "jícaras",
    "yezo": "yeso",
    # Next visible 4-count cluster: direct spelling/fused-form fixes,
    # excluding source/Nahuatl/proper-domain tokens and context-only cases.
    "aalgun": "a algún",
    "aalguno": "a alguno",
    "aciprés": "ciprés",
    "aconocer": "a conocer",
    "adellantada": "adentellada",
    "aderechas": "a derechas",
    "aderesarse": "aderezarse",
    "aduersidades": "adversidades",
    "advervio": "adverbio",
    "afliction": "aflicción",
    "aflijido": "afligido",
    "afloxandoles": "aflojándoles",
    "alagueño": "halagüeño",
    "alagueños": "halagüeños",
    "halagueñas": "halagüeñas",
    "alajas": "alhajas",
    "alanzada": "lanzada",
    "alholi": "alfolí",
    "alinpiar": "limpiar",
    "aluanega": "albanega",
    "aluergarse": "albergarse",
    "alvergarse": "albergarse",
    "amanese": "amanece",
    "amanesido": "amanecido",
    "anelar": "anhelar",
    "anzar": "ánsar",
    "apercivido": "apercibido",
    "aperder": "a perder",
    "arrazar": "arrasar",
    "arrodelado": "arrodalado",
    "asaber": "a saber",
    "atiempos": "a tiempos",
    "atraher": "atraer",
    "atravillados": "atraillados",
    "avdiencia": "audiencia",
    "avergonsarse": "avergonzarse",
    "axuar": "ajuar",
    "cabezcaido": "cabizcaído",
    "cadavno": "cada uno",
    "caluniado": "calumniado",
    "captivado": "cautivado",
    "caver": "caber",
    "cavesa": "cabeza",
    "caxcajo": "cascajo",
    "christalina": "cristalina",
    "codisiada": "codiciada",
    "concegil": "concejil",
    "concideración": "consideración",
    "condecender": "condescender",
    "congosa": "congoja",
    "conjunctiones": "conjunciones",
    "conserua": "conserva",
    "convatir": "combatir",
    "covardia": "cobardía",
    "debatalla": "de batalla",
    "delexos": "de lejos",
    "depunta": "de punta",
    "desapercivido": "desapercibido",
    "desboronada": "desmoronada",
    "desembolberse": "desenvolverse",
    "deseredado": "desheredado",
    "desmenusar": "desmenuzar",
    "desonrarse": "deshonrarse",
    "despedasando": "despedazando",
    "desuariadamente": "desvariadamente",
    "devia": "debía",
    "difficultad": "dificultad",
    "diligeute": "diligente",
    "dvda": "duda",
    "elbocado": "el bocado",
    "election": "elección",
    "eloquente": "elocuente",
    "emmallar": "enmallar",
    "emmohecerse": "enmohecerse",
    "emos": "hemos",
    "empuxones": "empujones",
    "encaxar": "encajar",
    "enhadarme": "enfadarme",
    "enmi": "en mi",
    "ensobervecerse": "ensoberbecerse",
    "ensusiada": "ensuciada",
    "entibiamento": "entibiamiento",
    "entiviado": "entibiado",
    "entiviarse": "entibiarse",
    "enuasar": "envasar",
    "envegaserse": "envejecerse",
    "enxabonamiento": "enjabonamiento",
    "enxabonamiénto": "enjabonamiento",
    "enxaluegado": "enjalbegado",
    "enxambre": "enjambre",
    "enxugado": "enjugado",
    "enxundia": "enjundia",
    "enxuta": "enjuta",
    "erbolario": "herbolario",
    "eregia": "herejía",
    "esamen": "examen",
    "esaminar": "examinar",
    "escova": "escoba",
    "escrivania": "escribanía",
    "esecutar": "ejecutar",
    "esforcar": "esforzar",
    "esparse": "esparce",
    "espedir": "expedir",
    "espexo": "espejo",
    "estenderme": "extenderme",
    "estremidades": "extremidades",
    "facilcosa": "fácil cosa",
    "feros": "feroz",
    "floreton": "floretón",
    "frecha": "flecha",
    "garavato": "garabato",
    "gentilizmo": "gentilismo",
    "geringa": "jeringa",
    "gomitada": "vomitada",
    "graza": "grasa",
    "guedijudo": "guedejudo",
    "haverselo": "habérselo",
    "honrrosamente": "honrosamente",
    "inobidiente": "inobediente",
    "insufficiente": "insuficiente",
    "iten": "ítem",
    "lenterna": "linterna",
    # Next visible cluster: direct modern spellings.
    "deservado": "desyerbado",
    "lienso": "lienzo",
    "luxuriosamente": "lujuriosamente",
    "martilogio": "martirologio",
    "mensagero": "mensajero",
    "morcielago": "murciélago",
    "mostruo": "monstruo",
    "mucico": "músico",
    "oaya": "o aya",
    "ocidente": "occidente",
    "ocosas": "o cosas",
    "oluido": "olvido",
    "omierda": "o mierda",
    "ortelano": "hortelano",
    "ospedarse": "hospedarse",
    "ostinarse": "obstinarse",
    "parentezco": "parentesco",
    "pasagero": "pasajero",
    "pavellon": "pabellón",
    "peruerso": "perverso",
    "picina": "piscina",
    "pizon": "pisón",
    "prover": "proveer",
    "quexandose": "quejándose",
    "recebidos": "recibidos",
    "redemptor": "redentor",
    "restrañar": "restañar",
    "resusitar": "resucitar",
    "revosar": "rebosar",
    "rofian": "rufián",
    "ronqueria": "ronquera",
    "sanja": "zanja",
    "satisfecer": "satisfacer",
    "sobervio": "soberbio",
    "solibiar": "soliviar",
    "sulco": "surco",
    "tectorica": "retórica",
    "tenebregoso": "tenebroso",
    "tericia": "tiricia",
}

PHRASE_REPLACEMENTS = {
    r"\s*\*\s*a cheval sur deux pages\b": "",
    r"\bhenchir\s+lo\s+que\s+falta,?\s+o\s+henchir\b": "henchir lo que falta",
    r"\bhenchir\s*[,;]?\s*o\s+henchir\b": "henchir",
    r"\bfiscal\s*[,;]?\s*o\s+fiscal\b": "fiscal",
    r"\blluvia\s*[,;]?\s*o\s+lluvia\b": "lluvia",
    r"\bpellizcar\s*[,;]?\s*o\s+pellizcar\b": "pellizcar",
    r"\bplumas\s+trupial\b": "plumas de trupial",
    r"\bcañas\s+jícaras\b": "cañas, jícaras",
    r"\bse salvo\b": "se salvó",
    r"\btolondrón\s+tolondrón\b": "tolondrón",
    r"\btolondrón\.\s*tolon\b": "tolondrón",
    r"\bvidrio\s*[,;]?\s*o\s+vidrio\b": "vidrio",
    r"\bvidrio\s*;\s*vidrio\b": "vidrio",
    r"\bdesdel\s+un\b": "desde un",
    r"\bdesdel\b": "desde el",
    r"\bgeneralm\(en\(te\b": "generalmente",
    r"\bgeneralm\(en\)te\b": "generalmente",
    r"\bquan\s+(?=(?:buena|bueno|grande|justo)\b)": "cuán ",
    r"\bpellizco\s*[,;]?\s*o\s+pellizco\b": "pellizco",
    r"\bveinti\s+una\b": "veintiuna",
    r"\bveinti\s+dos\b": "veintidós",
    r"\bveinti\s+tres\b": "veintitrés",
    r"\bveinti\s+cuatro\b": "veinticuatro",
    r"\bveinti\s+cinco\b": "veinticinco",
    r"\bveinti\s+seis\b": "veintiséis",
    r"\bveinti\s+siete\b": "veintisiete",
    r"\bveinti\s+ocho\b": "veintiocho",
    r"\bveinti\s+nueve\b": "veintinueve",
    r"\bmescladam\(en\)te\b": "mezcladamente",
    r"\bmescladam\(en\(te\b": "mezcladamente",
    r"\bhalaga de halagüeño\b": "halago de halagüeño",
    r"\bhave \[hava\] legumbre\b": "haba [hava] legumbre",
    r"\bazacar agua\b": "azacar (arcaico: acarrear agua) agua",
    r"\bcabezpelado\b(?!\s*\(arcaico:)": "cabezpelado (arcaico: calvo o de pocos cabellos)",
    r"\bchanzcando\b(?!\s*\(arcaico:)": "chanzcando (arcaico: chanceando, con chanzas)",
    r"\bdemediado\b(?!\s*\(arcaico:)": "demediado (arcaico: reducido a la mitad)",
    r"\bderrabada ave\b(?!\s*\(arcaico:)": "derrabada (arcaico: desrabada o sin cola) ave",
    r"\bdesenseñado\b(?!\s*\(arcaico:)": "desenseñado (arcaico: que olvidó lo aprendido)",
    r"\bendemal\b(?!\s*\(arcaico:)": "ende mal (arcaico: gozo por el mal ajeno)",
    r"\bafrenta, baldón o enjabonamiento\b(?!\s*\(arcaico:)": "afrenta, baldón o enjabonamiento (arcaico: afrenta o baldón)",
    r"\bafrenta, baldón, o enjabonamiento\b(?!\s*\(arcaico:)": "afrenta, baldón, o enjabonamiento (arcaico: afrenta o baldón)",
    r"\benjabonamiento tal\b": "enjabonamiento (arcaico: afrenta o baldón) tal",
    r"\bfloretón\b(?!\s*\(arcaico:)": "floretón (arcaico: golpe con los dedos)",
    r"\bfornecimi[eé]nto\b(?!\s*\(arcaico:)": "fornecimiento (arcaico: fortificación)",
    r"\bgloriación\b(?!\s*\(arcaico:)": "gloriación (arcaico: glorificación)",
    r"\bhomiciano\b(?!\s*\(arcaico:)": "homiciano (arcaico: homicida)",
    r"\bomiciano\b": "homiciano (arcaico: homicida)",
    r"\braez cosa de hacer\b": "raez (arcaico: fácil) cosa de hacer",
}


def token_pattern(token: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![^\W\d_]){re.escape(token)}(?![^\W\d_])", re.I | re.UNICODE)


TOKEN_PATTERNS = [(token_pattern(src), src, dst) for src, dst in TOKEN_REPLACEMENTS.items()]
PHRASE_PATTERNS = [(re.compile(src, re.I), src, dst) for src, dst in PHRASE_REPLACEMENTS.items()]


def translation_field(row: dict) -> str | None:
    source = row.get("Fuente")
    if source == "1992 Karttunen":
        return None
    if source == "2021 Wimmer":
        return "Traducción (es)" if "Traducción (es)" in row else None
    return "Traducción" if "Traducción" in row else None


def apply_replacements(text: str) -> tuple[str, Counter[str]]:
    changes: Counter[str] = Counter()
    new = text

    for pattern, src, dst in TOKEN_PATTERNS:
        new, count = pattern.subn(dst, new)
        if count:
            changes[src] += count

    for pattern, src, dst in PHRASE_PATTERNS:
        new, count = pattern.subn(dst, new)
        if count:
            changes[src] += count

    if changes:
        cleaned = re.sub(r" {2,}", " ", new)
        cleaned = re.sub(r" +([,;:.])", r"\1", cleaned).strip()
        if cleaned != new:
            new = cleaned
            changes["spacing after context fix"] += 1

    return new, changes


def iter_rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)


def write_rows(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=9) as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    tmp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    rows = []
    reports = []
    changed_rows = 0
    replacement_counts: Counter[str] = Counter()

    for row in iter_rows(args.data):
        field = translation_field(row)
        if field and isinstance(row.get(field), str):
            old = row[field]
            new, changes = apply_replacements(old)
            if new != old:
                changed_rows += 1
                replacement_counts.update(changes)
                reports.append(
                    {
                        "record_id": row.get("record_id") or row.get("id") or row.get("ID"),
                        "Fuente": row.get("Fuente"),
                        "Lema": row.get("Texto estandarizado") or row.get("Lema"),
                        "field": field,
                        "changes": dict(changes),
                        "old": old,
                        "new": new,
                    }
                )
                if args.apply:
                    row[field] = new
        rows.append(row)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as fh:
        for report in reports:
            fh.write(json.dumps(report, ensure_ascii=False) + "\n")

    print(f"mode={'apply' if args.apply else 'dry-run'}")
    print(f"changed_rows={changed_rows}")
    print(f"report={args.report}")
    print("top_replacements=")
    for key, count in replacement_counts.most_common(80):
        replacement = TOKEN_REPLACEMENTS.get(key) or PHRASE_REPLACEMENTS.get(key) or "<regex>"
        print(f"{key}\t{count}\t->\t{replacement}")

    if args.apply:
        write_rows(args.data, rows)


if __name__ == "__main__":
    main()
