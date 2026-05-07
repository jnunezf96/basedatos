#!/usr/bin/env python3
import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "wimmer_nonverb_data_cleanup_report.jsonl"


SOURCE_GARZA_RE = re.compile(r"\bgarza\.(?=\s*(?:[ivxlcdm]+|\d|\())", re.I)
TRANSLATION_HERN_RE = re.compile(
    r"\s+Hern\.\s*[IVXLCDMivxlcdm]+(?:\s+[IVXLCDMivxlcdm]+)?"
    r"(?:\s*\([^)]*\)|\s+\d+)*"
    r"(?:\s+Capítulo\s+\d+)?\.?",
    re.I,
)
EMPTY_PLURAL_RE = re.compile(r"\s*/\s*pl\.\s*,?\s*$", re.I)


TRANSLATION_FIXES = {
    "2021-wimmer:000241": "Lo que es de los Tlatepotzcah, los caracteriza o proviene de ellos.",
    "2021-wimmer:001037": "El que guarda o esconde algo; tendero, tesorero.",
    "2021-wimmer:001579": "Acción de sembrar o plantar.",
    "2021-wimmer:001675": "Portero.",
    "2021-wimmer:003042": "Que tiene o contiene fuego. / famoso, ilustre, renombrado.",
    "2021-wimmer:002611": "El que hace el mal, que comete impurezas.",
    "2021-wimmer:004041": "Hincharse; brotar, formar yemas.",
    "2021-wimmer:004237": "Alegre, regocijado. / animador público.",
    "2021-wimmer:005241": "Harapo, trapo pobre. / plural: pañales.",
    "2021-wimmer:005803": "Topónimo mítico: lugar de los sin carne; lugar de permanencia definitiva.",
    "2021-wimmer:005833": "El que corta.",
    "2021-wimmer:006927": "v.i., apresurarse. / v.inanimado, ponerse o situarse con locativo. / v.inanimado, oler mal, apestar.",
    "2021-wimmer:007600": "Calabaza.",
    "2021-wimmer:008297": "Animal, ser vivo. / cuadrúpedo. / presentador de embajadores en la corte.",
    "2021-wimmer:009586": "Nombre divino asociado a una deidad del agua que preside el bautismo del recién nacido. / nombre personal.",
    "2021-wimmer:009774": "Perro. / plural: perros. / metáfora: brutalidad, ferocidad. / v.i., amamantar. / v.t. tla-., mamar algo. / v.refl. en sentido pasivo, ser amamantado.",
    "2021-wimmer:010502": "Claro, limpio, puro.",
    "2021-wimmer:010504": "Correctamente. / sólo en la forma poseída.",
    "2021-wimmer:011272": "Término de parentesco: abuela, hermana del abuelo o hermana de la abuela. / zoología: liebre. / nombre personal.",
    "2021-wimmer:012795": "Forma poseída. / locativo.",
    "2021-wimmer:012977": "En forma poseída: bella apariencia, belleza de alguien.",
    "2021-wimmer:013237": "Tubo del águila o tubo del sol usado para recoger sangre sacrificial. / retórica: símbolo de ofrecer numerosas víctimas al Sol. / árbol delgado.",
    "2021-wimmer:013248": "Cola de la gran águila americana. / adorno, plumaje, penacho.",
    "2021-wimmer:014742": "Cantante o poeta.",
    "2021-wimmer:016085": "Ornitología: garza nocturna de corona negra. / halcón reidor. / nombre personal.",
    "2021-wimmer:016623": "Sólo en la forma poseída. / agradable, gentil; con sabor, agradablemente.",
    "2021-wimmer:016642": "Poder, habilidad.",
    "2021-wimmer:016698": "Calabaza alargada usada para extraer el jugo del agave.",
    "2021-wimmer:016891": "adjetivo: grande. / nombre personal o título. / v.inanimado, agrandarse, empeorar.",
    "2021-wimmer:017462": "Blusa de algodón. / peto acolchado de algodón.",
    "2021-wimmer:018054": "v.t. tē-., seguir a alguien en sus pasos. / v.t. tla-., buscar algo tanteando con los pies. / v.i., alargar el paso, caminar rápido.",
    "2021-wimmer:018421": "Anciana.",
    "2021-wimmer:019106": "Fríamente.",
    "2021-wimmer:020447": "Solo, separado de los demás.",
    "2021-wimmer:021000": "Palabra de enseñanza; enseñanza.",
    "2021-wimmer:021542": "Crecido, de edad avanzada. / desaparecido.",
    "2021-wimmer:022080": "Casa de los libros; biblioteca anexa al calmecac o al templo.",
    "2021-wimmer:022284": "Con asa. / forma poseída.",
    "2021-wimmer:022430": "botánica: euforbio. / v.inanimado, fluir por todos lados, hablando de un líquido; chorrear en diferentes lugares.",
    "2021-wimmer:023353": "Todo, todos.",
    "2021-wimmer:024584": "v.t. tē-., ordenar, dar prueba. / v.refl., despedirse.",
    "2021-wimmer:025413": "Acción de ir a defecar, descargar.",
    "2021-wimmer:025839": "Aconsejado. / quien lanza hechizos.",
    "2021-wimmer:026305": "Quema. / quemadura.",
    "2021-wimmer:026776": "¿Quiénes son?",
    "2021-wimmer:026821": "También. / interjección de dolor o aflicción: ¡ah!, ¡ay!, usada por mujeres.",
    "2021-wimmer:026893": "Calabaza redonda.",
    "2021-wimmer:027114": "Muro, muralla de guerreros.",
    "2021-wimmer:027654": "Inhumano, vicioso, monstruoso.",
    "2021-wimmer:027680": "Habitante de la laguna o de la ribera; marinero.",
    "2021-wimmer:027701": "Pozo, hoyo, acequia que tiene agua.",
    "2021-wimmer:027704": "Brocal, borde del pozo.",
    "2021-wimmer:027706": "Con un propulsor de dardos.",
    "2021-wimmer:027709": "Aguas residuales; sumidero de agua.",
    "2021-wimmer:028307": "Mojado, húmedo. / pálido, colorido.",
    "2021-wimmer:028590": "v.i., mejorarse, curarse, entrar en convalecencia. / v.t. tē-., tratar a alguien.",
    "2021-wimmer:028591": "v.inanimado, derretirse, licuarse, convertirse en agua, hablando de hielo; desmoronarse, caer en pedazos.",
    "2021-wimmer:029281": "v.aplicación sobre pitzoa. / v.aplicación sobre pītza.",
    "2021-wimmer:029083": "Hijo, niño. / noble. / cría de animal.",
    "2021-wimmer:029325": "Sucio, repulsivo, inmundo. / estrecho, apretado.",
    "2021-wimmer:032607": "Triple soporte de la vasija, formado por tres piedras en redondo. / por extensión: trillizos.",
    "2021-wimmer:032764": "Calabaza, melón.",
    "2021-wimmer:032875": "Calabaza.",
    "2021-wimmer:035010": "Piedra. / honorífico. / huevo. / semilla. / en compuestos puede designar una parte del cuerpo humano. / metáfora: castigo. / sufijo numeral para contar objetos redondos y gruesos.",
    "2021-wimmer:035109": "Mazorca o vaina de cacao.",
    "2021-wimmer:035030": "Perfecto de escuchar. / radical de verbos compuestos: estar vacío, desierto o abandonado.",
    "2021-wimmer:035486": "Espeso, apretado, denso, cuajado, coagulado. / intenso; también describe un olor.",
    "2021-wimmer:035781": "Como, similar a. / forma poseída: mi polvo. / forma poseída: mi piedra.",
    "2021-wimmer:035817": "Acolchado. / del color de las cerezas maduras.",
    "2021-wimmer:035840": "En las rocas. / en el horno.",
    "2021-wimmer:036006": "Harina de maíz molida. / cuñado.",
    "2021-wimmer:036209": "Piedra volcánica.",
    "2021-wimmer:036817": "Atrapado, cautivo, prisionero; dicho de personas y cosas.",
    "2021-wimmer:038202": "Piloto, marinero que sostiene el timón.",
    "2021-wimmer:038731": "Casa. / ornitología: cuervo. / calendario: signo o posición en el calendario ritual. / signo del calendario: tercer signo. / en composición: nombres de adornos.",
    "2021-wimmer:039414": "Calabaza silvestre.",
    "2021-wimmer:039484": "Sobre la tierra amarilla. / topónimo.",
    "2021-wimmer:040024": "Se les servía comida.",
    "2021-wimmer:040102": "Cargador, portador, tameme.",
    "2021-wimmer:040571": "El que sostiene o lleva un objeto en sus brazos. / plural: portadores.",
    "2021-wimmer:041831": "Intercambiados, trocados.",
    "2021-wimmer:042430": "Cortado, recogido. / colocado, apartado, trasladado.",
}


COMMENT_REPLACEMENTS = {
    "2021-wimmer:001675": [
        ("Portero, portero.", "Portero."),
    ],
    "2021-wimmer:004041": [
        ("swell (hablando de moverse).", "se hincha, hablando de brotes."),
        ("Brotan (sus flores). es el árbol capôlcuahuitl.", "Brotan sus flores. Se dice del árbol capōlcuahuitl."),
    ],
    "2021-wimmer:005241": [
        ("Pobre trapo o trapo.", "Harapo, trapo pobre."),
        ("les langes - los pañales.", "los pañales."),
    ],
    "2021-wimmer:005803": [
        (
            "Nach g.zimmermann ist das wort abzuleiten von dem verb. &#x27;ximoa&#x27; verweilen; daraus ergibt sich die bedeutung &#x27;ort des (endgültigen) verweilens&#x27; wie es auch bei bartholome de alua,",
            "Según G. Zimmermann, la palabra se deriva del verbo <b>ximoa</b>, permanecer; de ahí el sentido de lugar de permanencia definitiva, como también lo indica Bartolomé de Alva,",
        ),
        ("Ein name der unterwelt.", "Nombre del inframundo."),
        ("Ein in seiner bedeutung umstrippener begriff.", "Término de significado discutido."),
        ("Sga ii 759 (ximovaiano) muerte de vergessens.", "SGA II 759 (ximovaiano), muerte del olvido."),
    ],
    "2021-wimmer:008297": [
        ("les quadrupedes - los animales de cuatro patas", "los animales de cuatro patas"),
    ],
    "2021-wimmer:009586": [
        ("châlchihuitl îcue", "<b>Chālchihuitl īcue</b>"),
        ("Sah6, 175</small>", "Sah6, 175</small>"),
    ],
    "2021-wimmer:010254": [
        ("hicieron un estandarte de plumas<br>Garza. <small>W.Lehmann 1938, 67 párr. 48.</small>", "hicieron un estandarte de plumas de garza <small>W.Lehmann 1938, 67 párr. 48.</small>"),
    ],
    "2021-wimmer:010502": [
        ("les belles - las bellas", "las bellas"),
    ],
    "2021-wimmer:016698": [
        ("<b>allacatl</b>:.", "<b>allacatl</b>:"),
    ],
    "2021-wimmer:017462": [
        ("Les quitaron todo su equipo militar y su peto de algodón acolchado.", "Les quitaron todo su equipo militar y su peto acolchado de algodón."),
        ("Petalero acolchado de algodón.", "Peto acolchado de algodón."),
        ("Petalero de algodón acolchado.", "Peto de algodón acolchado."),
    ],
    "2021-wimmer:021000": [
        ("das unterweisende Wort", "la palabra de enseñanza"),
    ],
    "2021-wimmer:023236": [
        ("(Flor de Cod. Flor. es comestible <small>Sah11, 193</small>)", "Es comestible <small>Sah11, 193</small>"),
    ],
    "2021-wimmer:027680": [
        ("Alguien que vive sobre el agua, o a la orilla del agua. marinero, marinero.", "Alguien que vive sobre el agua o a la orilla del agua; marinero."),
    ],
    "2021-wimmer:027704": [
        ("Mingelle, borde de pozo.", "Brocal, borde de pozo."),
    ],
    "2021-wimmer:027706": [
        ("Con un propulsor de picadura", "Con un propulsor de dardos"),
    ],
    "2021-wimmer:036209": [
        ("Piedra volcánica. bacalao pa <small>ra xi 177v = ECN9, 208</small>", "Piedra volcánica. <small>Cod. Flor. XI 177v = ECN9, 208</small>"),
        ("Piedra volcánica. Cod. Flor. XI 177v = ECN9, 208</small>", "Piedra volcánica. <small>Cod. Flor. XI 177v = ECN9, 208</small>"),
    ],
    "2021-wimmer:038202": [
        ("Piloto, marinero, marinero que sostiene el timón.", "Piloto, marinero que sostiene el timón."),
    ],
    "2021-wimmer:039484": [
        ("Sur la terre jaune.", "Sobre la tierra amarilla."),
    ],
    "2021-wimmer:040102": [
        ("Portero, portero, tameme", "Cargador, portador, tameme"),
    ],
    "2021-wimmer:040571": [
        ("les porters - los portadores.", "los portadores."),
    ],
}


def clean_source_names(text: str, translation: bool) -> str:
    text = SOURCE_GARZA_RE.sub("Hern.", text)

    replacements = [
        (r"\b[Dd]escripción[Bb]acalao\s+Flor\b", "Descripción. Cod. Flor."),
        (r"\b[Bb]acalao\s*es\b", "Cod. Flor. es"),
        (r"\b[Gg]arza\.\s+historia\b", "Hern. Historia"),
        (r"\b[Gg]arza\.\s+yo\b", "Hern. I"),
        (r"\bGARZA\.\s+YO\b", "Hern. I"),
        (r"\b[Gg]arza\.\s+p\b", "Hern. p"),
        (r"\b[Ss]ah Bacalao florentino\b", "Sahagún, Cod. Florentino"),
        (r"\b[Bb]acalao\s+de\s+Madrid\b", "Cod. Matritense"),
        (r"\b[Bb]acalao\s+Matritense\b", "Cod. Matritense"),
        (r"\b[Bb]acalao\s+borbonicus\b", "Cod. Borbonicus"),
        (r"\b[Bb]acalao\s+mendocino\b", "Cod. Mendoza"),
        (r"\b[Bb]acalao\s+mendoza\b", "Cod. Mendoza"),
        (r"\b[Bb]acalao\s+vaticano\s+A\b", "Cod. Vat. A"),
        (r"\b[Bb]acalao\s+IVA\.?\s*A\b", "Cod. Vat. A"),
        (r"\b[Bb]acalao\s+FIor\b", "Cod. Flor."),
        (r"\b[Bb]acalao\s+Fior\b", "Cod. Flor."),
        (r"\b[Bb]acalao\s+Flor\b", "Cod. Flor."),
        (r"\b[Bb]acalao\s+Elor\b", "Cod. Flor."),
        (r"\b[Bb]acalao\s+For\b", "Cod. Flor."),
        (r"\b[Bb]acalao\s+Para\b", "Cod. Flor."),
        (r"\b[Bb]acalao\s+pa\s*<small>\s*ra\s+xi", "Cod. Flor. XI"),
        (r"\b[Ff]lor\s+[Dd]e;\s*[Bb]acalao\b", "Cod. Flor."),
        (r"\b[Ff]lor\s+[Dd]e\s*\([Bb]acalao\)", "Cod. Flor."),
        (r"\b[Ff]lor\s+de\s+\([Bb]acalao\)", "Cod. Flor."),
        (r"\b[Ff]lor\s+de\s+[Bb]acalao\b", "Cod. Flor."),
        (r"\(\s*[Ff]lor\s+[Dd]e\s*\([Bb]acalao\)\s*\)", "(Cod. Flor.)"),
        (r"\(\s*[Bb]acalao\s*\([Ff]lor\s*\)\s*\)", "(Cod. Flor.)"),
        (r"\b[Bb]acalao\s*\([Ff]lor\s*\)", "Cod. Flor."),
        (r"\b[Bb]acalao\s*\([Ff]lor\s+([^)]*)\)", r"Cod. Flor. \1"),
        (r"\b[Bb]acalao\s+Acad\b", "Cod. Acad."),
        (r"\b[Bb]acalao\s+Mat\s+Acad\b", "Cod. Mat. Acad."),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)

    text = re.sub(r"\b[Bb]acalao\b", "Cod.", text)

    if translation:
        text = TRANSLATION_HERN_RE.sub("", text)
        text = EMPTY_PLURAL_RE.sub("", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        text = re.sub(r"\s+/\s*$", "", text).strip()
    return text


def normalize_translation(text: str) -> str:
    text = clean_source_names(text, translation=True)
    text = text.replace(" / plural: Les langes.", " / plural: pañales.")
    text = text.replace(" / plural: Les quadrupedes.", " / plural: animales de cuatro patas.")
    text = text.replace(" / plural: Les belles.", "")
    text = text.replace(" / plural: Les porters.", " / plural: portadores.")
    text = EMPTY_PLURAL_RE.sub("", text)
    text = text.replace("Calabaza, calabaza", "Calabaza")
    return text.strip()


def normalize_comment(text: str, record_id: str) -> str:
    text = clean_source_names(text, translation=False)
    for old, new in COMMENT_REPLACEMENTS.get(record_id, []):
        text = text.replace(old, new)
    return text


def main() -> None:
    rows = []
    changes = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            old = dict(row)

            if row.get("Fuente") == "2021 Wimmer":
                rid = row.get("record_id")
                if "Traducción (es)" in row:
                    row["Traducción (es)"] = normalize_translation(row["Traducción (es)"] or "")
                    if rid in TRANSLATION_FIXES:
                        row["Traducción (es)"] = TRANSLATION_FIXES[rid]
                if "Comentario (es)" in row:
                    row["Comentario (es)"] = normalize_comment(row["Comentario (es)"] or "", rid)

            if row != old:
                diff = {}
                for key in ("Traducción (es)", "Comentario (es)"):
                    if row.get(key) != old.get(key):
                        diff[key] = {"old": old.get(key), "new": row.get(key)}
                changes.append(
                    {
                        "record_id": row.get("record_id"),
                        "lemma": row.get("Texto estandarizado"),
                        "changes": diff,
                    }
                )
            rows.append(row)

    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for change in changes:
            fh.write(json.dumps(change, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(changes)}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
