#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_y_residual_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")
SKIP_SOURCES = {"1992 Karttunen"}


REPLACEMENTS: dict[str, tuple[str, str]] = {
    "ydem": ("ídem", "old_y_i_spelling"),
    "yden": ("ídem", "old_y_i_spelling"),
    "yda": ("ida", "old_y_i_spelling"),
    "yde": ("y de", "fused_y_conjunction"),
    "yderretir": ("y derretir", "fused_y_conjunction"),
    "ydesabrido": ("y desabrido", "fused_y_conjunction"),
    "ydescuidado": ("y descuidado", "fused_y_conjunction"),
    "ydespoblada": ("y despoblada", "fused_y_conjunction"),
    "ydiziendo": ("y diciendo", "fused_y_conjunction"),
    "ydifficultad": ("dificultad", "old_y_i_spelling"),
    "ydo": ("ido", "old_y_i_spelling"),
    "ydolatra": ("idólatra", "old_y_i_spelling"),
    "ydolatras": ("idólatras", "old_y_i_spelling"),
    "ydolatrar": ("idolatrar", "old_y_i_spelling"),
    "ydolatria": ("idolatría", "old_y_i_spelling"),
    "ydolatría": ("idolatría", "old_y_i_spelling"),
    "ydropesia": ("hidropesía", "old_y_i_spelling"),
    "ydropecia": ("hidropesía", "old_y_i_spelling"),
    "ydropico": ("hidrópico", "old_y_i_spelling"),
    "ygnorancia": ("ignorancia", "old_y_i_spelling"),
    "ygnorante": ("ignorante", "old_y_i_spelling"),
    "ygnorantemente": ("ignorantemente", "old_y_i_spelling"),
    "yglecia": ("iglesia", "old_y_i_spelling"),
    "yglesia": ("iglesia", "old_y_i_spelling"),
    "yglesias": ("iglesias", "old_y_i_spelling"),
    "ygnorancia": ("ignorancia", "old_y_i_spelling"),
    "ygual": ("igual", "old_y_i_spelling"),
    "yguala": ("iguala", "old_y_i_spelling"),
    "ygualada": ("igualada", "old_y_i_spelling"),
    "ygualadas": ("igualadas", "old_y_i_spelling"),
    "ygualado": ("igualado", "old_y_i_spelling"),
    "ygualador": ("igualador", "old_y_i_spelling"),
    "ygualar": ("igualar", "old_y_i_spelling"),
    "ygualarse": ("igualarse", "old_y_i_spelling"),
    "ygualdad": ("igualdad", "old_y_i_spelling"),
    "yguale": ("iguale", "old_y_i_spelling"),
    "yguales": ("iguales", "old_y_i_spelling"),
    "ygualmente": ("igualmente", "old_y_i_spelling"),
    "yguallar": ("igualar", "old_y_i_spelling"),
    "yjada": ("ijada", "old_y_i_spelling"),
    "yjadear": ("ijadear", "old_y_i_spelling"),
    "yjares": ("ijares", "old_y_i_spelling"),
    "yjusta": ("y justa", "fused_y_conjunction"),
    "ylabrada": ("y labrada", "fused_y_conjunction"),
    "yle": ("y le", "fused_y_conjunction"),
    "yles": ("y les", "fused_y_conjunction"),
    "ylicita": ("ilícita", "old_y_i_spelling"),
    "ylicito": ("ilícito", "old_y_i_spelling"),
    "ylos": ("y los", "fused_y_conjunction"),
    "ylexitimo": ("ilegítimo", "old_y_i_spelling"),
    "yllegitima": ("ilegítima", "old_y_i_spelling"),
    "yllisita": ("ilícita", "old_y_i_spelling"),
    "yllustre": ("ilustre", "old_y_i_spelling"),
    "yluminador": ("iluminador", "old_y_i_spelling"),
    "yluminados": ("iluminados", "old_y_i_spelling"),
    "yluminar": ("iluminar", "old_y_i_spelling"),
    "ylustre": ("ilustre", "old_y_i_spelling"),
    "ymagen": ("imagen", "old_y_i_spelling"),
    "ymaginar": ("imaginar", "old_y_i_spelling"),
    "ymaginada": ("imaginada", "old_y_i_spelling"),
    "ymagines": ("imágenes", "old_y_i_spelling"),
    "ymaluado": ("y malvado", "fused_y_conjunction"),
    "ymansa": ("y mansa", "fused_y_conjunction"),
    "ymarauilloso": ("y maravilloso", "fused_y_conjunction"),
    "ymatauan": ("y mataban", "fused_y_conjunction"),
    "ymalas": ("y malas", "fused_y_conjunction"),
    "yman": ("imán", "old_y_i_spelling"),
    "ymfierno": ("infierno", "old_y_i_spelling"),
    "ymitador": ("imitador", "old_y_i_spelling"),
    "ymitar": ("imitar", "old_y_i_spelling"),
    "ymmudable": ("inmutable", "old_y_i_spelling"),
    "ymmundicia": ("inmundicia", "old_y_i_spelling"),
    "ymmortal": ("inmortal", "old_y_i_spelling"),
    "ymmortalidad": ("inmortalidad", "old_y_i_spelling"),
    "ymmortalmente": ("inmortalmente", "old_y_i_spelling"),
    "ympaciencia": ("impaciencia", "old_y_i_spelling"),
    "ympaciente": ("impaciente", "old_y_i_spelling"),
    "ympacientemente": ("impacientemente", "old_y_i_spelling"),
    "ympedimento": ("impedimento", "old_y_i_spelling"),
    "ympedimiento": ("impedimiento", "old_y_i_spelling"),
    "ympedido": ("impedido", "old_y_i_spelling"),
    "ympedir": ("impedir", "old_y_i_spelling"),
    "ympedtrar": ("impetrar", "old_y_i_spelling"),
    "ymperial": ("imperial", "old_y_i_spelling"),
    "ymperio": ("imperio", "old_y_i_spelling"),
    "ympetrado": ("impetrado", "old_y_i_spelling"),
    "ympetrando": ("impetrando", "old_y_i_spelling"),
    "ympetrar": ("impetrar", "old_y_i_spelling"),
    "ympetu": ("ímpetu", "old_y_i_spelling"),
    "ympide": ("impide", "old_y_i_spelling"),
    "ymponedor": ("imponedor", "old_y_i_spelling"),
    "ymponer": ("imponer", "old_y_i_spelling"),
    "ympontencia": ("impotencia", "old_y_i_spelling"),
    "ymposibilidad": ("imposibilidad", "old_y_i_spelling"),
    "ymposible": ("imposible", "old_y_i_spelling"),
    "ympotencia": ("impotencia", "old_y_i_spelling"),
    "ympoténcia": ("impotencia", "old_y_i_spelling"),
    "ympotente": ("impotente", "old_y_i_spelling"),
    "ymprimir": ("imprimir", "old_y_i_spelling"),
    "ymprenta": ("imprenta", "old_y_i_spelling"),
    "ympresa": ("impresa", "old_y_i_spelling"),
    "ympuesto": ("impuesto", "old_y_i_spelling"),
    "ymportunamente": ("importunamente", "old_y_i_spelling"),
    "ymportunidad": ("importunidad", "old_y_i_spelling"),
    "ymportuno": ("importuno", "old_y_i_spelling"),
    "ymportuna": ("importuna", "old_y_i_spelling"),
    "ymportuná": ("importuna", "old_y_i_spelling"),
    "ymos": ("vamos", "old_y_i_spelling"),
    "ymuy": ("y muy", "fused_y_conjunction"),
    "ymudable": ("y mudable", "fused_y_conjunction"),
    "ynabil": ("inhábil", "old_y_i_spelling"),
    "ynabilidad": ("inhabilidad", "old_y_i_spelling"),
    "ynaduertencia": ("inadvertencia", "old_y_i_spelling"),
    "ynanimadas": ("inanimadas", "old_y_i_spelling"),
    "ynbierno": ("invierno", "old_y_i_spelling"),
    "ynchado": ("hinchado", "old_y_i_spelling"),
    "yncienso": ("incienso", "old_y_i_spelling"),
    "yncitado": ("incitado", "old_y_i_spelling"),
    "yncitador": ("incitador", "old_y_i_spelling"),
    "yncitar": ("incitar", "old_y_i_spelling"),
    "ynclina": ("inclina", "old_y_i_spelling"),
    "ynclinación": ("inclinación", "old_y_i_spelling"),
    "ynclinado": ("inclinado", "old_y_i_spelling"),
    "ynclinar": ("inclinar", "old_y_i_spelling"),
    "ynclinarse": ("inclinarse", "old_y_i_spelling"),
    "yncomportable": ("incomportable", "old_y_i_spelling"),
    "ynconcideradam": ("inconsideradam", "old_y_i_spelling"),
    "ynconcideradamene": ("inconsideradamente", "old_y_i_spelling"),
    "ynconcideradamente": ("inconsideradamente", "old_y_i_spelling"),
    "yncónsideradamente": ("inconsideradamente", "old_y_i_spelling"),
    "ynconsideradamene": ("inconsideradamente", "old_y_i_spelling"),
    "ynconsideradamente": ("inconsideradamente", "old_y_i_spelling"),
    "ynconstancia": ("inconstancia", "old_y_i_spelling"),
    "ynconstante": ("inconstante", "old_y_i_spelling"),
    "ynconstantemente": ("inconstantemente", "old_y_i_spelling"),
    "yncontinencia": ("incontinencia", "old_y_i_spelling"),
    "yncontinente": ("incontinente", "old_y_i_spelling"),
    "ynconueniente": ("inconveniente", "old_y_i_spelling"),
    "yncurrir": ("incurrir", "old_y_i_spelling"),
    "yndia": ("india", "old_y_i_spelling"),
    "yndias": ("Indias", "old_y_i_spelling"),
    "yndigestion": ("indigestión", "old_y_i_spelling"),
    "yndigesto": ("indigesto", "old_y_i_spelling"),
    "yndigno": ("indigno", "old_y_i_spelling"),
    "yndio": ("indio", "old_y_i_spelling"),
    "yndios": ("indios", "old_y_i_spelling"),
    "ynducido": ("inducido", "old_y_i_spelling"),
    "ynducimiento": ("inducimiento", "old_y_i_spelling"),
    "ynducir": ("inducir", "old_y_i_spelling"),
    "yndulugencia": ("indulgencia", "old_y_i_spelling"),
    "yndulgencia": ("indulgencia", "old_y_i_spelling"),
    "yndustria": ("industria", "old_y_i_spelling"),
    "yndustrioso": ("industrioso", "old_y_i_spelling"),
    "ynduzido": ("inducido", "old_y_i_spelling"),
    "ynduzidor": ("inducidor", "old_y_i_spelling"),
    "ynduzidora": ("inducidora", "old_y_i_spelling"),
    "ynduzimiento": ("inducimiento", "old_y_i_spelling"),
    "ynduzir": ("inducir", "old_y_i_spelling"),
    "ynfamado": ("infamado", "old_y_i_spelling"),
    "ynfamador": ("infamador", "old_y_i_spelling"),
    "ynfamar": ("infamar", "old_y_i_spelling"),
    "ynfamarse": ("infamarse", "old_y_i_spelling"),
    "ynfamia": ("infamia", "old_y_i_spelling"),
    "ynferior": ("inferior", "old_y_i_spelling"),
    "ynfernal": ("infernal", "old_y_i_spelling"),
    "ynfidelidad": ("infidelidad", "old_y_i_spelling"),
    "ynfiel": ("infiel", "old_y_i_spelling"),
    "ynfiermo": ("infierno", "old_y_i_spelling"),
    "ynfierno": ("infierno", "old_y_i_spelling"),
    "ynficionado": ("inficionado", "old_y_i_spelling"),
    "ynficionador": ("inficionador", "old_y_i_spelling"),
    "ynficionamiento": ("inficionamiento", "old_y_i_spelling"),
    "ynficionar": ("inficionar", "old_y_i_spelling"),
    "ynfinidad": ("infinidad", "old_y_i_spelling"),
    "ynfinito": ("infinito", "old_y_i_spelling"),
    "ynfinitamente": ("infinitamente", "old_y_i_spelling"),
    "ynflamarse": ("inflamarse", "old_y_i_spelling"),
    "ynformado": ("informado", "old_y_i_spelling"),
    "ynformador": ("informador", "old_y_i_spelling"),
    "ynforma": ("informa", "old_y_i_spelling"),
    "ynformar": ("informar", "old_y_i_spelling"),
    "ynfuriado": ("infuriado", "old_y_i_spelling"),
    "ynfuriar": ("infuriar", "old_y_i_spelling"),
    "yngenio": ("ingenio", "old_y_i_spelling"),
    "yngeniosamente": ("ingeniosamente", "old_y_i_spelling"),
    "yngenioso": ("ingenioso", "old_y_i_spelling"),
    "yngle": ("ingle", "old_y_i_spelling"),
    "yngrato": ("ingrato", "old_y_i_spelling"),
    "ynhumano": ("inhumano", "old_y_i_spelling"),
    "ynhumanidad": ("inhumanidad", "old_y_i_spelling"),
    "ynjuriado": ("injuriado", "old_y_i_spelling"),
    "ynjuriador": ("injuriador", "old_y_i_spelling"),
    "ynjuriar": ("injuriar", "old_y_i_spelling"),
    "ynjuria": ("injuria", "old_y_i_spelling"),
    "ynjusta": ("injusta", "old_y_i_spelling"),
    "ynjustamente": ("injustamente", "old_y_i_spelling"),
    "ynjusticia": ("injusticia", "old_y_i_spelling"),
    "ynoportuno": ("inoportuno", "old_y_i_spelling"),
    "ynocencia": ("inocencia", "old_y_i_spelling"),
    "ynocent": ("inocente", "old_y_i_spelling"),
    "ynocente": ("inocente", "old_y_i_spelling"),
    "ynocentes": ("inocentes", "old_y_i_spelling"),
    "ynocentemente": ("inocentemente", "old_y_i_spelling"),
    "ynobediente": ("inobediente", "old_y_i_spelling"),
    "ynopia": ("inopia", "old_y_i_spelling"),
    "ynorancia": ("ignorancia", "old_y_i_spelling"),
    "ynorante": ("ignorante", "old_y_i_spelling"),
    "ynpedido": ("impedido", "old_y_i_spelling"),
    "ynquirir": ("inquirir", "old_y_i_spelling"),
    "ynquisidor": ("inquisidor", "old_y_i_spelling"),
    "ymquisidor": ("inquisidor", "old_y_i_spelling"),
    "ynquieta": ("inquieta", "old_y_i_spelling"),
    "ynquietado": ("inquietado", "old_y_i_spelling"),
    "ynquietar": ("inquietar", "old_y_i_spelling"),
    "ynquietud": ("inquietud", "old_y_i_spelling"),
    "ynsinias": ("insignias", "old_y_i_spelling"),
    "ynsignias": ("insignias", "old_y_i_spelling"),
    "ynspirar": ("inspirar", "old_y_i_spelling"),
    "ynstancia": ("instancia", "old_y_i_spelling"),
    "ynstincto": ("instinto", "old_y_i_spelling"),
    "ynstinto": ("instinto", "old_y_i_spelling"),
    "ynstrar": ("instar", "old_y_i_spelling"),
    "ynstrumento": ("instrumento", "old_y_i_spelling"),
    "ynstruyendo": ("instruyendo", "old_y_i_spelling"),
    "ynsuficiente": ("insuficiente", "old_y_i_spelling"),
    "yntentando": ("intentando", "old_y_i_spelling"),
    "yntento": ("intento", "old_y_i_spelling"),
    "ynterjection": ("interjección", "old_y_i_spelling"),
    "ynterprete": ("intérprete", "old_y_i_spelling"),
    "ynterpretada": ("interpretada", "old_y_i_spelling"),
    "ynterpretar": ("interpretar", "old_y_i_spelling"),
    "yntolerable": ("intolerable", "old_y_i_spelling"),
    "yntroducir": ("introducir", "old_y_i_spelling"),
    "yntroduzir": ("introducir", "old_y_i_spelling"),
    "ynuentada": ("inventada", "old_y_i_spelling"),
    "ynuentar": ("inventar", "old_y_i_spelling"),
    "ynuentario": ("inventario", "old_y_i_spelling"),
    "ynueuevno": ("y nueve uno", "fused_y_conjunction"),
    "ynuernal": ("invernal", "old_y_i_spelling"),
    "ynuernar": ("invernar", "old_y_i_spelling"),
    "ynuierno": ("invierno", "old_y_i_spelling"),
    "ynvierno": ("invierno", "old_y_i_spelling"),
    "ynvernal": ("invernal", "old_y_i_spelling"),
    "ynventada": ("inventada", "old_y_i_spelling"),
    "ynventar": ("inventar", "old_y_i_spelling"),
    "ynventario": ("inventario", "old_y_i_spelling"),
    "ypacifica": ("y pacífica", "fused_y_conjunction"),
    "ypasados": ("y pasados", "fused_y_conjunction"),
    "ypereza": ("y pereza", "fused_y_conjunction"),
    "yperezca": ("y perezca", "fused_y_conjunction"),
    "yperuersa": ("y perversa", "fused_y_conjunction"),
    "ypobreza": ("y pobreza", "fused_y_conjunction"),
    "ypocresia": ("hipocresía", "old_y_i_spelling"),
    "ypocrecia": ("hipocresía", "old_y_i_spelling"),
    "ypochresia": ("hipocresía", "old_y_i_spelling"),
    "ypochrita": ("hipócrita", "old_y_i_spelling"),
    "ypocrita": ("hipócrita", "old_y_i_spelling"),
    "ypocrito": ("hipócrito", "old_y_i_spelling"),
    "ypor": ("y por", "fused_y_conjunction"),
    "yportanto": ("y por tanto", "fused_y_conjunction"),
    "yquitar": ("y quitar", "fused_y_conjunction"),
    "yque": ("y que", "fused_y_conjunction"),
    "yra": ("ira", "old_y_i_spelling"),
    "yracundo": ("iracundo", "old_y_i_spelling"),
    "yrado": ("irado", "old_y_i_spelling"),
    "yrarse": ("airarse", "old_y_i_spelling"),
    "yras": ("irás", "old_y_i_spelling"),
    "yrazonable": ("y razonable", "fused_y_conjunction"),
    "yre": ("iré", "old_y_i_spelling"),
    "yremos": ("iremos", "old_y_i_spelling"),
    "yrijen": ("y rigen", "fused_y_conjunction"),
    "yrle": ("irle", "old_y_i_spelling"),
    "yrlas": ("irlas", "old_y_i_spelling"),
    "yrracionales": ("irracionales", "old_y_i_spelling"),
    "yrreprehensible": ("irreprehensible", "old_y_i_spelling"),
    "yrregular": ("irregular", "old_y_i_spelling"),
    "yrregularidad": ("irregularidad", "old_y_i_spelling"),
    "yrregularmente": ("irregularmente", "old_y_i_spelling"),
    "yrse": ("irse", "old_y_i_spelling"),
    "ysaben": ("y saben", "fused_y_conjunction"),
    "ysazon": ("y sazón", "fused_y_conjunction"),
    "yseco": ("y seco", "fused_y_conjunction"),
    "ysed": ("y sed", "fused_y_conjunction"),
    "yselo": ("y se lo", "fused_y_conjunction"),
    "ysesenta": ("y sesenta", "fused_y_conjunction"),
    "ysi": ("y si", "fused_y_conjunction"),
    "ysin": ("y sin", "fused_y_conjunction"),
    "ysino": ("y si no", "fused_y_conjunction"),
    "ysquierda": ("izquierda", "old_y_i_spelling"),
    "ysla": ("isla", "old_y_i_spelling"),
    "ysopo": ("hisopo", "old_y_i_spelling"),
    "ystoria": ("historia", "old_y_i_spelling"),
    "ystoriador": ("historiador", "old_y_i_spelling"),
    "ystorial": ("historial", "old_y_i_spelling"),
    "ytambien": ("y también", "fused_y_conjunction"),
    "yten": ("ítem", "old_y_i_spelling"),
    "ytenebroso": ("y tenebroso", "fused_y_conjunction"),
    "yheroycas": ("y heroicas", "fused_y_conjunction"),
    "ytoca": ("y toca", "fused_y_conjunction"),
    "yusticiado": ("justiciado", "old_y_i_spelling"),
    "yuglar": ("juglar", "old_y_i_spelling"),
    "yzquierda": ("izquierda", "old_y_i_spelling"),
    "yzquierdas": ("izquierdas", "old_y_i_spelling"),
    "yzquierdo": ("izquierdo", "old_y_i_spelling"),
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
