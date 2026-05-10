#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "translation_spelling_high_confidence_report.jsonl"
CANDIDATES_PATH = ROOT / "scripts" / "translation_spelling_open_candidates.tsv"

sys.path.insert(0, str(ROOT / "scripts"))
import non_wimmer_rla_lexicon_review as rla  # noqa: E402


SKIP_SOURCES = {"1992 Karttunen"}
TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñÇçĀĒĪŌŪāēīōūÂÊÎÔÛâêîôû]+")
LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇçĀĒĪŌŪāēīōūÂÊÎÔÛâêîôû"
MACRON_RE = re.compile(r"[āēīōūĀĒĪŌŪâêîôûÂÊÎÔÛ]")


# Exact, high-confidence spelling/orthography repairs in Spanish-facing
# translations. Lexical archaisms stay source-first with a short modern help.
MANUAL_REPLACEMENTS: dict[str, str] = {
    "acertándo": "acertando",
    "acompañandolos": "acompañándolos",
    "acrecéntada": "acrecentada",
    "acómpaña": "acompaña",
    "acómpañandolos": "acompañándolos",
    "acónsejando": "aconsejando",
    "adegalzar": "adelgazar",
    "adiestrándo": "adiestrando",
    "adormecerseme": "adormecérseme",
    "afréntosas": "afrentosas",
    "agonias": "agonías",
    "agonizándo": "agonizando",
    "alcarchofa": "alcachofa",
    "alhajeme": "alhájeme",
    "allegandole": "allegándole",
    "almastiga": "almástiga",
    "amontonandolo": "amontonándolo",
    "angustiandolos": "angustiándolos",
    "aparecera": "aparecerá",
    "arguméntos": "argumentos",
    "arremetiéndo": "arremetiendo",
    "arrepenti": "arrepentí",
    "arráncando": "arrancando",
    "aser": "hacer",
    "aserrandole": "aserrándole",
    "asementarse": "sementarse",
    "asomandose": "asomándose",
    "asolas": "a solas",
    "asus": "a sus",
    "atambor": "atambor (arcaico: tambor)",
    "atapa": "tapa",
    "atapada": "tapada",
    "atapado": "tapado",
    "atapador": "tapador",
    "atormentán": "atormentan",
    "atorméntado": "atormentado",
    "atraveso": "atravesó",
    "cabestrage": "cabestraje",
    "calándo": "calando",
    "carcax": "carcaj",
    "caseria": "casería",
    "ciertisimo": "ciertísimo",
    "cociendolas": "cociéndolas",
    "colerica": "colérica",
    "comence": "comencé",
    "comerselo": "comérselo",
    "comienzán": "comienzan",
    "companera": "compañera",
    "companeros": "compañeros",
    "componian": "componían",
    "comén": "comen",
    "confia": "confía",
    "confundiéndo": "confundiendo",
    "conocia": "conocía",
    "contenia": "contenía",
    "corrómpida": "corrompida",
    "creciéndo": "creciendo",
    "cámpana": "campana",
    "cámpanas": "campanas",
    "cénsos": "censos",
    "cómponian": "componían",
    "cóncede": "concede",
    "cóncertado": "concertado",
    "cónfundido": "confundido",
    "cónfutador": "confutador",
    "cónsagrada": "consagrada",
    "cónsultada": "consultada",
    "cóntienda": "contienda",
    "cóntrato": "contrato",
    "cóprofago": "coprófago",
    "desa": "de esa",
    "delgadisima": "delgadísima",
    "derramán": "derraman",
    "derramándo": "derramando",
    "desatavio": "desatavío",
    "descomedimiénto": "descomedimiento",
    "desempegado": "desempegado (arcaico: despegado)",
    "descomunión": "descomunión (arcaico: excomunión)",
    "descónfiado": "desconfiado",
    "desenterro": "desenterró",
    "desgañada": "desganada",
    "desmedrándo": "desmedrando",
    "desnudarselos": "desnudárselos",
    "desñudada": "desnudada",
    "dezmada": "diezmada",
    "diciendole": "diciéndole",
    "digán": "digan",
    "durmiéndo": "durmiendo",
    "echán": "echan",
    "encada": "en cada",
    "emperezandose": "emperezándose",
    "encanecerseme": "encanecérseme",
    "encoméndada": "encomendada",
    "enganos": "engaños",
    "enhastio": "enhastío",
    "envia": "envía",
    "escarnecienda": "escarneciendo",
    "esconderselo": "escondérselo",
    "escónde": "esconde",
    "escóndida": "escondida",
    "espectaculos": "espectáculos",
    "espiandolos": "espiándolos",
    "espántada": "espantada",
    "espántosas": "espantosas",
    "estanza": "estancia",
    "esteriles": "estériles",
    "examínado": "examinado",
    "falsada": "falseada",
    "fantastica": "fantástica",
    "fiandolo": "fiándolo",
    "fuertisima": "fuertísima",
    "girifalte": "gerifalte",
    "hazanosa": "hazañosa",
    "hebraismo": "hebraísmo",
    "heche": "eche",
    "henderseme": "hendérseme",
    "hendiendole": "hendiéndole",
    "hermosisima": "hermosísima",
    "hirio": "hirió",
    "hispañización": "hispanización",
    "hortigas": "ortigas",
    "hortigar": "ortigar",
    "húnde": "hunde",
    "húndidas": "hundidas",
    "impesonal": "impersonal",
    "imponian": "imponían",
    "imponén": "imponen",
    "importunandole": "importunándole",
    "indulgéncias": "indulgencias",
    "juntandolos": "juntándolos",
    "júntos": "juntos",
    "lanzándo": "lanzando",
    "legitimos": "legítimos",
    "mamiferos": "mamíferos",
    "manifesto": "manifiesto",
    "menstrua": "menstrúa",
    "merecia": "merecía",
    "metiéndo": "metiendo",
    "milaños": "mil años",
    "mastel": "mástil",
    "mormullo": "murmullo",
    "mostrandolos": "mostrándolos",
    "mostrarselo": "mostrárselo",
    "muchisima": "muchísima",
    "murmurán": "murmuran",
    "negándo": "negando",
    "ogaño": "hogaño",
    "ofrecio": "ofreció",
    "ostias": "ostras",
    "pajaros": "pájaros",
    "parecia": "parecía",
    "parpados": "párpados",
    "pequena": "pequeña",
    "porfias": "porfías",
    "prenada": "preñada",
    "principes": "príncipes",
    "procurándo": "procurando",
    "prohije": "prohíje",
    "rascuño": "rasguño",
    "rebite": "ribete",
    "reprehendiendolo": "reprehendiéndolo",
    "reprehensiones": "reprensiones",
    "rogarias": "rogarías",
    "rraíz": "raíz",
    "rrey": "rey",
    "rrosa": "rosa",
    "rrosal": "rosal",
    "rigorosamente": "rigurosamente",
    "sant": "san",
    "tamañicos": "tamañitos",
    "tirán": "tiran",
    "tiranicamente": "tiránicamente",
    "ánda": "anda",
    "ñublosa": "nublosa",
}

MANUAL_REPLACEMENTS.update(
    {
        # Old Spanish u/v spellings surfaced by Trad. W ~+ "{V}u{V}".
        "acauar": "acabar",
        "adeuino": "adivino",
        "adiuina": "adivina",
        "aflictiua": "aflictiva",
        "affirmatiuo": "afirmativo",
        "alcauallo": "al caballo",
        "aplicatiuo": "aplicativo",
        "aprouando": "aprobando",
        "aprouecharme": "aprovecharme",
        "atreua": "atreva",
        "atauian": "atavían",
        "atrauesado": "atravesado",
        "atrauesarsele": "atravesársele",
        "atrauiesa": "atraviesa",
        "auejon": "abejón",
        "auarienta": "avarienta",
        "auarientos": "avarientos",
        "auentada": "aventada",
        "auerse": "haberse",
        "aueto": "abeto",
        "auillanado": "avillanado",
        "auéntajada": "aventajada",
        "aguabiua": "agua viva",
        "buuas": "bubas",
        "captiuan": "cautivan",
        "captiue": "cautive",
        "catiuerio": "cautiverio",
        "catiuidad": "cautividad",
        "caualletes": "caballetes",
        "cauallilo": "caballillo",
        "cauallero": "caballero",
        "cauernas": "cavernas",
        "cañaueralo": "cañaveral",
        "ceuamiento": "cebamiento",
        "chanbraua": "chambrana",
        "charitatiuo": "caritativo",
        "chiriuia": "chirivía",
        "concauidad": "concavidad",
        "conchaua": "conchaba",
        "conchauarlas": "conchabarlas",
        "copulatiua": "copulativa",
        "couardemente": "cobardemente",
        "criuo": "cribo",
        "curatiua": "curativa",
        "dadiuosa": "dadivosa",
        "deaue": "de ave",
        "desgouernarse": "desgobernarse",
        "deloqueamaua": "de lo que amaba",
        "deloquedudaua": "de lo que dudaba",
        "deseaua": "deseaba",
        "deuanada": "devanada",
        "deuanadura": "devanadura",
        "deuen": "deben",
        "deuio": "debió",
        "diuidise": "divídese",
        "diuisión": "división",
        "diuinales": "divinales",
        "dubdaua": "dudaba",
        "echaua": "echaba",
        "enclaua": "enclava",
        "enseuar": "ensebar",
        "entreuerada": "entreverada",
        "entreuerado": "entreverado",
        "equiuocamente": "equívocamente",
        "equiuocation": "equivocación",
        "esclauillo": "esclavillo",
        "eslauonada": "eslabonada",
        "esperaua": "esperaba",
        "estauán": "estaban",
        "esteua": "esteva",
        "eua": "eva",
        "fauorece": "favorece",
        "fauoreciendo": "favoreciendo",
        "fauoreciendolos": "favoreciéndolos",
        "fauorecerse": "favorecerse",
        "gallipauo": "gallipavo",
        "gouernados": "gobernados",
        "gouernando": "gobernando",
        "hablaua": "hablaba",
        "interrogatiue": "interrogativamente",
        "juuentud": "juventud",
        "laue": "lave",
        "lauarlos": "lavarlos",
        "lauarse": "lavarse",
        "laueme": "láveme",
        "lauo": "lavó",
        "leua": "lleva",
        "leuantar": "levantar",
        "leuantarle": "levantarle",
        "leuantandose": "levantándose",
        "leuantan": "levantan",
        "leuantados": "levantados",
        "leuantándo": "levantando",
        "leuánta": "levanta",
        "leuántamiento": "levantamiento",
        "leuar": "llevar",
        "liuianas": "livianas",
        "liuianamente": "livianamente",
        "llamaua": "llamaba",
        "llaues": "llaves",
        "lleuen": "lleven",
        "marauillamiento": "maravillamiento",
        "mouediza": "movediza",
        "niuela": "nivela",
        "niuelado": "nivelado",
        "oliuar": "olivar",
        "osuauidad": "o suavidad",
        "ouas": "ovas",
        "pasiue": "pasivamente",
        "pensatiua": "pensativa",
        "pensaua": "pensaba",
        "perseuerar": "perseverar",
        "preuilegiar": "privilegiar",
        "preuilegio": "privilegio",
        "priuacion": "privación",
        "priuarme": "privarme",
        "prouerbio": "proverbio",
        "prouablemente": "probablemente",
        "prouechosos": "provechosos",
        "proueen": "proveen",
        "proueymiento": "proveimiento",
        "prouidencia": "providencia",
        "prouocación": "provocación",
        "prouocandolo": "provocándolo",
        "rauia": "rabia",
        "rauiar": "rabiar",
        "rauioso": "rabioso",
        "remouer": "remover",
        "reuerenciada": "reverenciada",
        "reuerenciaque": "reverencia que",
        "reuerénciado": "reverenciado",
        "reuender": "revender",
        "reuiesa": "reviesa",
        "reuegido": "revejido",
        "reuocar": "revocar",
        "ropauegero": "ropavejero",
        "ruuios": "rubios",
        "sangrelluuia": "sangrelluvia",
        "serrauia": "serranía",
        "selauo": "se lavó",
        "souajadas": "sobajadas",
        "tiraua": "tiraba",
        "trastornaua": "trastornaba",
        "trauesura": "travesura",
        "trauesuras": "travesuras",
        "touajas": "toallas",
        "tuuiesen": "tuviesen",
        "tuuiesemos": "tuviésemos",
        "tuue": "tuve",
        "visauela": "bisabuela",
        "viuela": "vihuela",
        "émbeuida": "embebida",
    }
)

MANUAL_REPLACEMENTS.update(
    {
        # Old Spanish x spellings surfaced by Trad. W ~+ "{V}x{V}" and "?x?".
        "afloxo": "aflojo",
        "afloxamiento": "aflojamiento",
        "aguxerada": "agujerada",
        "aquexado": "aquejado",
        "aquexamiento": "aquejamiento",
        "axenxos": "ajenjos",
        "axenxios": "ajenjos",
        "axedréa": "ajedrea",
        "caxcabel": "cascabel",
        "caxcador": "cascador",
        "caxquezuelos": "casquezuelos",
        "caxquillo": "casquillo",
        "caxajo": "cascajo",
        "carcaxada": "carcajada",
        "cexas": "cejas",
        "coxcorrón": "coscorrón",
        "coxcuelo": "cojuelo",
        "coxeando": "cojeando",
        "coxqueando": "cojeando",
        "coxquilloso": "cosquilloso",
        "cruxen": "crujen",
        "debuxador": "dibujador",
        "debuxos": "dibujos",
        "deaxedrez": "de ajedrez",
        "desquixarado": "desquijarado",
        "desquixarador": "desquijarador",
        "desquixaramiento": "desquijaramiento",
        "detexer": "de tejer",
        "dexerga": "de jerga",
        "emmaxcararse": "enmascararse",
        "empuxada": "empujada",
        "empuxarlo": "empujarlo",
        "empuxones": "empujones",
        "émpuxones": "empujones",
        "encaxador": "encajador",
        "encaxes": "encajes",
        "enxalzador": "ensalzador",
        "enxalzamiento": "ensalzamiento",
        "enxalzarse": "ensalzarse",
        "enxaluegador": "enjalbegador",
        "enxaluegamiento": "enjalbegamiento",
        "enxaluegar": "enjalbegar",
        "enxabondandola": "enjabonándola",
        "enxabonandola": "enjabonándola",
        "enxabonadura": "enjabonadura",
        "enxabonamiénnto": "enjabonamiento",
        "enxeridor": "enjeridor (arcaico: injertador)",
        "enxerir": "enjerir (arcaico: injertar)",
        "enxertal": "enjertal",
        "enxertador": "enjertador",
        "enxertamiento": "enjertamiento",
        "enxertar": "enjertar",
        "enxugo": "enjugó",
        "exercito": "ejército",
        "exemplo": "ejemplo",
        "exparcir": "esparcir",
        "exparcido": "esparcido",
        "exparcirse": "esparcirse",
        "exeso": "exceso",
        "exageramente": "exageradamente",
        "faxarse": "fajarse",
        "fluxura": "flojura",
        "gruxir": "crujir",
        "luxuria": "lujuria",
        "luxuriar": "lujuriar",
        "luxuriosa": "lujuriosa",
        "luxuriosas": "lujuriosas",
        "luxurioso": "lujurioso",
        "matalotaxe": "matalotaje",
        "maxcada": "mascada",
        "maxcador": "mascador",
        "maxcadura": "mascadura",
        "maxcando": "mascando",
        "maxcarla": "mascarla",
        "mexillar": "mejilla",
        "moxcador": "moscador",
        "moxcas": "moscas",
        "amoxcarse": "amoscarse",
        "moxinete": "mojinete",
        "moxquito": "mosquito",
        "moxquitos": "mosquitos",
        "oxear": "ojear",
        "oxeada": "ojeada",
        "oxeadas": "ojeadas",
        "oxeados": "ojeados",
        "oxeando": "ojeando",
        "oxeo": "ojeo",
        "paraxe": "paraje",
        "paxairco": "pajarico",
        "paxarito": "pajarito",
        "paxaro": "pájaro",
        "paxaros": "pájaros",
        "perplexidad": "perplejidad",
        "perplexos": "perplejos",
        "quaxada": "cuajada",
        "quexarse": "quejarse",
        "quexura": "quejura",
        "raxada": "rajada",
        "raxo": "rajo",
        "roxos": "rojos",
        "sabandixa": "sabandija",
        "sabandixuela": "sabandijuela",
        "semaxca": "se masca",
        "sonaxera": "sonajera",
        "taxa": "tasa",
        "taxcar": "tascar",
        "texerla": "tejerla",
        "vaxilla": "vajilla",
        "xerga": "jerga",
        "xeta": "jeta",
        "xirguerito": "jilguerito",
        "xaquima": "jáquima",
        "xabonadura": "jabonadura",
        "énxaluegar": "enjalbegar",
        "entretexedura": "entretejedura",
        "replexion": "repleción",
    }
)

PHRASE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("defuera confingimiento", "de fuera con fingimiento"),
    ("por defuera", "por fuera"),
    ("Coxquear (arcaico: hacer cosquillas).", "cosquillear, hacer cosquillas"),
    ("coxquear (arcaico: cosquillar), hacer cosquillas", "cosquillear, hacer cosquillas"),
    ("cosquillar, hacer cosquillas", "cosquillear, hacer cosquillas"),
    ("Coxquear (arcaico: cojear) así.", "coxquear (arcaico: cojear) así."),
    ("reguizcar (arcaico: hacer cosquillas).", "reguizcar (arcaico: cosquillar)."),
    ("coxquar nombre", "cojera"),
    ("lexosel", "lejos el"),
    ("encada un ", "en cada "),
    ("v.i.rregular.,", "v.i. irregular,"),
    ("v.i.rreg.,", "v.i. irregular,"),
    ("v.i.rregular.", "v.i. irregular."),
    ("v.i.rreg.", "v.i. irregular."),
    ("impes.,", "impers.,"),
    ("ciuera casi cibdadria", "cibera, trigo, grano"),
    ("niello, broui, seco, hablando de fruta", "añublado, seco, hablando de fruta"),
    ("serrauia dieara montañesa", "serranía, tierra montañesa"),
)

MANUAL_RE = re.compile(
    rf"(?<![{LETTER}])("
    + "|".join(re.escape(token) for token in sorted(MANUAL_REPLACEMENTS, key=len, reverse=True))
    + rf")(?![{LETTER}])",
    re.I,
)


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


def translation_field(row: dict) -> str | None:
    source = row.get("Fuente") or ""
    if source in SKIP_SOURCES:
        return None
    if source == "2021 Wimmer":
        return "Traducción (es)"
    return "Traducción"


def preserve_case(old: str, new: str) -> str:
    if old.isupper():
        return new.upper()
    if old[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def plain_key(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.strip().lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def build_accent_replacements(candidates_path: Path) -> dict[str, str]:
    exact, accentless, _files = rla.load_lexicon()
    replacements: dict[str, str] = {}
    if not candidates_path.exists():
        return replacements
    with candidates_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row.get("bucket") != "candidate_accent":
                continue
            token = row.get("token") or ""
            if not token or MACRON_RE.search(token):
                continue
            token_key = rla.key(token)
            if token_key in exact:
                continue
            matches = sorted(accentless.get(plain_key(token), set()))
            if len(matches) == 1 and matches[0] != token_key:
                replacements[token_key] = matches[0]
    return replacements


def apply_manual(value: str, changes: Counter[str]) -> str:
    def repl(match: re.Match[str]) -> str:
        old = match.group(0)
        after = match.string[match.end() : match.end() + 32]
        if re.match(r"\s*\(\s*arcaico\s*:", after, re.I):
            return old
        new = preserve_case(old, MANUAL_REPLACEMENTS[old.lower()])
        changes[f"{old}->{new}"] += 1
        return new

    return MANUAL_RE.sub(repl, value)


def apply_phrases(value: str, changes: Counter[str]) -> str:
    for old, new in PHRASE_REPLACEMENTS:
        if old in value:
            count = value.count(old)
            value = value.replace(old, new)
            changes[f"{old}->{new}"] += count
    return value


def apply_accents(value: str, accent_replacements: dict[str, str], changes: Counter[str]) -> str:
    def repl(match: re.Match[str]) -> str:
        old = match.group(0)
        if MACRON_RE.search(old):
            return old
        new = accent_replacements.get(rla.key(old))
        if not new:
            return old
        new = preserve_case(old, new)
        changes[f"{old}->{new}"] += 1
        return new

    return TOKEN_RE.sub(repl, value)


def clean_value(value: str, accent_replacements: dict[str, str]) -> tuple[str, Counter[str]]:
    changes: Counter[str] = Counter()
    value = apply_phrases(value, changes)
    value = apply_manual(value, changes)
    value = apply_accents(value, accent_replacements, changes)
    return value, changes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--candidates", type=Path, default=CANDIDATES_PATH)
    args = parser.parse_args()

    accent_replacements = build_accent_replacements(args.candidates)
    rows = []
    reports = []
    replacement_counts: Counter[str] = Counter()

    for row in iter_rows(args.data):
        field = translation_field(row)
        value = row.get(field) if field else None
        if isinstance(value, str) and value:
            new_value, changes = clean_value(value, accent_replacements)
            if new_value != value:
                replacement_counts.update(changes)
                reports.append(
                    {
                        "record_id": row.get("record_id"),
                        "Fuente": row.get("Fuente"),
                        "Lema": row.get("Texto estandarizado") or row.get("Lema"),
                        "field": field,
                        "changes": dict(changes),
                        "old": value,
                        "new": new_value,
                    }
                )
                if args.apply:
                    row[field] = new_value
        rows.append(row)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as fh:
        for report in reports:
            fh.write(json.dumps(report, ensure_ascii=False) + "\n")

    print(f"mode={'apply' if args.apply else 'dry-run'}")
    print(f"changed_rows={len(reports)}")
    print(f"report={args.report}")
    print("top_replacements=")
    for key, count in replacement_counts.most_common(120):
        print(f"{key}\t{count}")

    if args.apply:
        write_rows(args.data, rows)


if __name__ == "__main__":
    main()
