#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_residual_spanish_orthography_report.jsonl"
FIELD = "Traducción"
SKIP_SOURCES = {"2021 Wimmer", "1992 Karttunen", "V94 Diccionario Global SNP"}


REGEX_REPLACEMENTS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bhacerlo ael\b"), "hacerlo a él", "hacerlo_ael_to_hacerlo_a_el"),
    (re.compile(r"\bparticularmente ael\b"), "particularmente a él", "particularmente_ael_to_particularmente_a_el"),
    (re.compile(r"\bael verbo\b"), "al verbo", "ael_verbo_to_al_verbo"),
    (re.compile(r"\btodo lo ael posible\b"), "todo lo posible", "todo_lo_ael_posible_to_todo_lo_posible"),
    (re.compile(r"\baella\b"), "a ella", "aella_to_a_ella"),
    (re.compile(r"\baello\b"), "a ello", "aello_to_a_ello"),
    (re.compile(r"\bqe\.\s*"), "que ", "qe_abbrev_to_que"),
    (re.compile(r"\bora del\b"), "hora del", "ora_del_to_hora_del"),
    (re.compile(r"\bora parte del\b"), "hora, parte del", "ora_parte_del_to_hora_parte_del"),
    (re.compile(r"\bque dia\b"), "qué día", "que_dia_to_que_dia_accent"),
    (re.compile(r"\bque mes\b"), "qué mes", "que_mes_to_que_mes_accent"),
    (re.compile(r"\bque año\b"), "qué año", "que_año_to_que_año_accent"),
    (re.compile(r"\bpor ledar priesa\b"), "por darle prisa", "por_ledar_priesa_to_por_darle_prisa"),
    (re.compile(r"\bpriesa dar\b"), "dar prisa", "priesa_dar_to_dar_prisa"),
    (re.compile(r"\bauisara\s+a\b"), "avisar a", "auisara_a_to_avisar_a"),
    (re.compile(r"\bauisados\b"), "avisados", "auisados_to_avisados"),
    (re.compile(r"\bauisandolo\b"), "avisándolo", "auisandolo_to_avisandolo"),
    (re.compile(r"\bauisos\b"), "avisos", "auisos_to_avisos"),
    (re.compile(r"\bauisa\b"), "avisa", "auisa_to_avisa"),
]

POST_REGEX_REPLACEMENTS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bser avisados prudentes y sabios\b"), "ser avisados, prudentes y sabios", "list_comma"),
    (re.compile(r"\bcorrer \[correr\]"), "correr", "drop_redundant_correr_bracket"),
]

TOKEN_REPLACEMENTS: dict[str, str] = {
    "acóntecer": "acontecer",
    "acóntecio": "aconteció",
    "adéntelladas": "adentelladas",
    "adu": "adv.",
    "advbio": "adverbio",
    "afirmadaménte": "afirmadamente",
    "afligidaménte": "afligidamente",
    "amigableménte": "amigablemente",
    "apresuradaménte": "apresuradamente",
    "apartadaménte": "apartadamente",
    "apriesa": "aprisa",
    "almomento": "al momento",
    "ánte": "ante",
    "atreuidaménte": "atrevidamente",
    "atordidor": "aturdidor",
    "atordir": "aturdir",
    "cautelosaménte": "cautelosamente",
    "cónjúnctión": "conjunción",
    "comigo": "conmigo",
    "consciencia": "conciencia",
    "cónstante": "constante",
    "constánte": "constante",
    "cónstánte": "constante",
    "cónstituido": "constituido",
    "cónstituidor": "constituidor",
    "constreñidaménte": "constreñidamente",
    "cóntento": "contento",
    "corrigiendolo": "corrigiéndolo",
    "cúmpliendo": "cumpliendo",
    "cúmplirse": "cumplirse",
    "cúmplir": "cumplir",
    "corer": "correr",
    "dase": "darse",
    "dedia": "de día",
    "delánteros": "delanteros",
    "delicadaménte": "delicadamente",
    "déntellada": "dentellada",
    "devn": "de un",
    "devna": "de una",
    "dia": "día",
    "despúntada": "despuntada",
    "despúntador": "despuntador",
    "despúntar": "despuntar",
    "desaprouechadaménte": "desaprovechadamente",
    "depriesa": "deprisa",
    "determinadaménte": "determinadamente",
    "diferéntes": "diferentes",
    "diferenteménte": "diferentemente",
    "diligénte": "diligente",
    "dobladaménte": "dobladamente",
    "doliénte": "doliente",
    "dulceménte": "dulcemente",
    "éncontinénte": "encontinente",
    "engañosaménte": "engañosamente",
    "éntera": "entera",
    "enteraménte": "enteramente",
    "éntero": "entero",
    "énterrarse": "enterrarse",
    "éntresi": "entre sí",
    "esforzadaménte": "esforzadamente",
    "esteriorménte": "exteriormente",
    "excelénte": "excelente",
    "fingidaménte": "fingidamente",
    "gloriosaménte": "gloriosamente",
    "graciosaménte": "graciosamente",
    "halga": "haga",
    "inpaciénte": "impaciente",
    "ínterpretador": "interpretador",
    "juisio": "juicio",
    "júntera": "juntera",
    "júntamente": "juntamente",
    "largaménte": "largamente",
    "limpiaménte": "limpiamente",
    "llorosaménte": "llorosamente",
    "lugarteniénte": "lugarteniente",
    "maliciosaménte": "maliciosamente",
    "malqueréncia": "malquerencia",
    "mansaménte": "mansamente",
    "mántenimiénto": "mantenimiento",
    "mántenimiento": "mantenimiento",
    "medianaménte": "medianamente",
    "mónte": "monte",
    "múndo": "mundo",
    "mondadiéntes": "mondadientes",
    "móndadiéntes": "mondadientes",
    "mudableménte": "mudablemente",
    "opiadosaménte": "o piadosamente",
    "ordidura": "urdidura",
    "ordir": "urdir",
    "ordenadaménte": "ordenadamente",
    "paréntela": "parentela",
    "paréntesco": "parentesco",
    "permaneciénte": "permaneciente",
    "persoua": "persona",
    "poniendole": "poniéndole",
    "priesa": "prisa",
    "primeraménte": "primeramente",
    "presumptuosaménte": "presuntuosamente",
    "príncipal": "principal",
    "príncipalménte": "principalmente",
    "prudénte": "prudente",
    "prudéntemente": "prudentemente",
    "prudéntes": "prudentes",
    "puénte": "puente",
    "púnta": "punta",
    "qe": "que",
    "reléntecer": "relentecer",
    "resplandeciénte": "resplandeciente",
    "semblánte": "semblante",
    "sensualménte": "sensualmente",
    "solaménte": "solamente",
    "sosegadaménte": "sosegadamente",
    "supito": "súbito",
    "témplada": "templada",
    "tienén": "tienen",
    "trasparénte": "transparente",
    "travaxo": "trabajo",
    "turbadaménte": "turbadamente",
    "veínte": "veinte",
    "yaantigua": "ya antigua",
    "yvieja": "y vieja",
}

TOKEN_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(token) for token in sorted(TOKEN_REPLACEMENTS, key=len, reverse=True)) + r")\b"
)


def clean(text: str) -> tuple[str, list[str]]:
    reasons: list[str] = []
    new = text

    for pattern, replacement, reason in REGEX_REPLACEMENTS:
        cleaned, count = pattern.subn(replacement, new)
        if count:
            new = cleaned
            reasons.append(reason)

    seen_tokens: set[str] = set()

    def replace_token(match: re.Match[str]) -> str:
        token = match.group(0)
        seen_tokens.add(token)
        return TOKEN_REPLACEMENTS[token]

    cleaned = TOKEN_PATTERN.sub(replace_token, new)
    if cleaned != new:
        new = cleaned
        reasons.extend(f"{token}_to_{TOKEN_REPLACEMENTS[token]}" for token in sorted(seen_tokens))

    for pattern, replacement, reason in POST_REGEX_REPLACEMENTS:
        cleaned, count = pattern.subn(replacement, new)
        if count:
            new = cleaned
            reasons.append(reason)

    return new, reasons


def iter_rows() -> list[dict]:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def write_rows(rows: list[dict]) -> None:
    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes to data/data.jsonl.gz")
    args = parser.parse_args()

    rows = iter_rows()
    report = []

    for row in rows:
        if row.get("Fuente") in SKIP_SOURCES:
            continue
        old = row.get(FIELD)
        if not isinstance(old, str) or not old:
            continue
        new, reasons = clean(old)
        if new == old:
            continue
        report.append(
            {
                "record_id": row.get("record_id"),
                "source": row.get("Fuente"),
                "lemma": row.get("Texto estandarizado"),
                "reasons": reasons,
                "old_translation": old,
                "new_translation": new,
            }
        )
        if args.apply:
            row[FIELD] = new

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    if args.apply:
        write_rows(rows)

    print(f"changed_rows={len(report)}")
    print(f"applied={args.apply}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
