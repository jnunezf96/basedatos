#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
RLA_OLD_VERBS_PATH = (
    ROOT
    / "resources"
    / "dictionaries"
    / "rla-es-2.9"
    / "ortografia"
    / "palabras"
    / "RAE"
    / "VerbosAnticuadosDesusados.txt"
)
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_archaic_verb_report.jsonl"
REVIEW_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_archaic_verb_review.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


SKIP_SOURCES = {"2021 Wimmer", "1992 Karttunen"}
LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"


# Keep this list conservative. These are obsolete verb lexemes with a gloss that
# is either already established in the data or directly inferable from adjacent
# entries. Spelling-only variants stay out of this map.
CURATED_GLOSSES: dict[str, str] = {
    "abarrar": "embarrar",
    "aballar": "mover con dificultad",
    "abortear": "abortar",
    "aburar": "quemar",
    "acontar": "volver a contar",
    "ajenar": "enajenar",
    "albedriar": "juzgar por albedrío",
    "alimpiar": "limpiar",
    "amblar": "moverse con meneo",
    "alongar": "alargar",
    "antiguar": "quitar lo antiguo",
    "antevenir": "adelantarse o aventajar",
    "apercebir": "preparar o disponer",
    "aprovecer": "aprovechar",
    "apesgar": "apretar o hacer pesado",
    "aquedar": "aquietar o detener",
    "arronjar": "arrojar o lanzar",
    "arrempujar": "empujar",
    "asmar": "estimar o pensar",
    "asosegar": "sosegar",
    "atalar": "talar",
    "atapar": "tapar o cubrir",
    "aviltar": "envilecer o abatir",
    "azomar": "azuzar o incitar",
    "añublar": "nublar",
    "aziar": "sobornar o cohechar al juez",
    "barbar": "tener barba",
    "bermejecer": "enrojecer",
    "bermejecerse": "enrojecerse",
    "captivar": "capturar o hacer cautivo",
    "carlear": "jadear",
    "crismar": "confirmar o ungir con crisma",
    "cutir": "chocar o golpear",
    "descaecer": "decaer",
    "desatravesar": "quitar lo atravesado o poner en orden",
    "desboronar": "desmoronar",
    "desafuciar": "desahuciar o desesperar",
    "desañudar": "desanudar",
    "desavezar": "desacostumbrar",
    "delgazar": "adelgazar",
    "dentecer": "nacer los dientes",
    "desencasar": "desencajar",
    "desenhetrar": "desenredar",
    "desmoler": "digerir",
    "desnaturar": "desnaturalizar o desterrar",
    "desballestar": "disparar con ballesta",
    "despartir": "separar o apartar",
    "desperar": "desesperar",
    "despender": "gastar",
    "dehender": "hender",
    "embebecerse": "estar absorto",
    "embermejecer": "enrojecer",
    "embermejecerse": "enrojecerse",
    "embizmar": "poner bizma",
    "emprentar": "imprimir",
    "emprensar": "prensar",
    "encalvar": "dejar calvo",
    "enemigar": "hacer enemigos",
    "enertarse": "entumecerse o ponerse rígido",
    "enforrar": "forrar",
    "engastonar": "engastar",
    "enaspar": "poner en aspa",
    "engerir": "injertar",
    "enhadar": "hastiar o importunar",
    "enhetrar": "enmarañar o enredar",
    "enjerir": "injertar",
    "enmocecer": "hacerse mozo",
    "ensangostar": "hacer angosto o estrechar",
    "entrevenir": "intervenir o mediar",
    "envergonzar": "avergonzar",
    "escalentar": "calentar",
    "estrazar": "destrozar",
    "herbolecer": "crecer en hierba",
    "hereticar": "hacer hereje",
    "llantear": "llorar o lamentarse",
    "magrecer": "enflaquecer o adelgazar",
    "garzonear": "hacer vida de garzón",
    "hadar": "adivinar o pronosticar",
    "maderar": "enmaderar o techar",
    "maherir": "preparar o convocar",
    "membrar": "recordar",
    "mesturar": "mezclar",
    "mohatrar": "regatear o negociar",
    "mollir": "mullir",
    "mortajar": "amortajar",
    "noblecer": "ennoblecer",
    "pescudar": "preguntar o averiguar",
    "premir": "apretar u oprimir",
    "raigar": "arraigar",
    "rebatar": "arrebatar",
    "reguizcar": "hacer cosquillas o burlas",
    "rufianear": "hacer vida de rufián",
    "sangrentar": "ensangrentar",
    "secrestar": "poner en depósito",
    "segurar": "asegurar",
    "sermonar": "predicar o hacer sermón",
    "sollar": "soplar",
    "sosacar": "sonsacar",
    "testiguar": "atestiguar o testificar",
    "trafaguear": "regatear o negociar",
    "truhanear": "hacer burlas o gracias como truhán",
    "tormentar": "atormentar",
    "tropellar": "atropellar",
    "turar": "durar",
    "voltejar": "voltear",
}


# These are intentionally not auto-annotated because they are too likely to be
# spelling-only forms or need context-specific modernization.
SPELLING_OR_UNCERTAIN = {
    "asconder",
    "callentar",
    "consejar",
    "delibrar",
    "desatapar",
    "descaecer",
    "desenhadar",
    "escurecer",
    "fornecer",
}

CONTEXT_REVIEW_VERBS = {
    "embasar",
}


REVIEW_FALSE_POSITIVES = {
    # RLA marks these, but the dictionary translations use them in valid modern
    # senses often enough that they add noise rather than useful review work.
    "ablandecer",
    "alcahuetar",
    "arrebatarse",
    "desfundar",
    "diluir",
    "frutificar",
    "traer",
    "vulgar",
}


PHRASE_ALREADY_ANNOTATED = [
    re.compile(r"\babortear\s+por\s+algún\s+desastre\s+y\s+sin\s+voluntad\b\s*\(arcaico:", re.I),
    re.compile(r"\bbaratar,?\s+o\s+trafaguear,?\s+o\s+mohatrar\b\s*\(arcaico:", re.I),
    re.compile(r"\bbermejecerse\s+el\s+rostro\s+de\s+enojo\b\s*\(arcaico:", re.I),
    re.compile(r"\bembebecerse\s+en\s+algo\b\s*\(arcaico:", re.I),
    re.compile(r"\bembebecerse\s+en\s+otra\s+cosa\b\s*\(arcaico:", re.I),
]


POST_CLEANUPS: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r"\bTurar\s+\(arcaico:\s+durar\)\s+por\s+durar\.?"),
        "Turar (arcaico: durar).",
        "collapse_redundant_turar_gloss",
    ),
    (
        re.compile(r"\bturar\s+\(arcaico:\s+durar\)\s+por\s+durar\.?"),
        "turar (arcaico: durar).",
        "collapse_redundant_turar_gloss",
    ),
    (
        re.compile(r"\bEmprentar\s+\(arcaico:\s+imprimir\),?\s+o\s+imprimir\.?"),
        "Emprentar (arcaico: imprimir).",
        "collapse_redundant_emprentar_gloss",
    ),
    (
        re.compile(r"\bemprentar\s+\(arcaico:\s+imprimir\),?\s+o\s+imprimir\.?"),
        "emprentar (arcaico: imprimir).",
        "collapse_redundant_emprentar_gloss",
    ),
    (
        re.compile(r"\bEmprentar\s+\(arcaico:\s+imprimir\)\s+a\s+imprimir\.?"),
        "Emprentar (arcaico: imprimir).",
        "collapse_redundant_emprentar_gloss",
    ),
    (
        re.compile(r"\bDesmoler\s+\(arcaico:\s+digerir\)\s+la\s+comida\s+o\s+digerirla\.?"),
        "Desmoler (arcaico: digerir) la comida.",
        "collapse_redundant_desmoler_gloss",
    ),
    (
        re.compile(r"\bdesmoler\s+\(arcaico:\s+digerir\)\s+la\s+comida\s+o\s+digerirla\.?"),
        "desmoler (arcaico: digerir) la comida.",
        "collapse_redundant_desmoler_gloss",
    ),
    (
        re.compile(r"\bDespender\s+\(arcaico:\s+gastar\)\s+o\s+gastar\.?"),
        "Despender (arcaico: gastar).",
        "collapse_redundant_despender_gloss",
    ),
    (
        re.compile(r"\bdespender\s+\(arcaico:\s+gastar\)\s+o\s+gastar\.?"),
        "despender (arcaico: gastar).",
        "collapse_redundant_despender_gloss",
    ),
    (
        re.compile(r"\bPremir\s+\(arcaico:\s+apretar\s+u\s+oprimir\),?\s+o\s+apretar\.?"),
        "Premir (arcaico: apretar u oprimir).",
        "collapse_redundant_premir_gloss",
    ),
    (
        re.compile(r"\bpremir\s+\(arcaico:\s+apretar\s+u\s+oprimir\),?\s+o\s+apretar\.?"),
        "premir (arcaico: apretar u oprimir).",
        "collapse_redundant_premir_gloss",
    ),
    (
        re.compile(r"\bdespender\s+\(arcaico:\s+gastar\)\.;"),
        "despender (arcaico: gastar);",
        "fix_cleanup_punctuation",
    ),
    (
        re.compile(r"\bPremir\s+\(arcaico:\s+apretar\s+u\s+oprimir\)\.;"),
        "Premir (arcaico: apretar u oprimir);",
        "fix_cleanup_punctuation",
    ),
    (
        re.compile(r"\bDesperar\s+\(arcaico:\s+desesperar\)\s+o\s+desesperar\.?"),
        "Desperar (arcaico: desesperar).",
        "collapse_redundant_desperar_gloss",
    ),
    (
        re.compile(r"\bAlbedriar\s+\(arcaico:\s+juzgar\s+por\s+albedrío\)\s+juzgar\s+por\s+albedrio\.?"),
        "Albedriar (arcaico: juzgar por albedrío).",
        "collapse_redundant_albedriar_gloss",
    ),
    (
        re.compile(r"\bAntiguar\s+\(arcaico:\s+quitar\s+lo\s+antiguo\)\s+quitar\s+lo\s+antiguo\.?"),
        "Antiguar (arcaico: quitar lo antiguo).",
        "collapse_redundant_antiguar_gloss",
    ),
    (
        re.compile(r"\bAsmar\s+\(arcaico:\s+estimar\s+o\s+pensar\)\s+casi\s+estimar\s+o\s+pensar\.?"),
        "Asmar (arcaico: estimar o pensar).",
        "collapse_redundant_asmar_gloss",
    ),
    (
        re.compile(r"\bAtalar\s+\(arcaico:\s+talar\)\s+\[talar\]\s+el\s+fuego"),
        "Atalar (arcaico: talar) el fuego",
        "collapse_redundant_atalar_gloss",
    ),
    (
        re.compile(r"\bEnemigar\s+\(arcaico:\s+hacer\s+enemigos\)\s+hacer\s+enemigos\.?"),
        "Enemigar (arcaico: hacer enemigos).",
        "collapse_redundant_enemigar_gloss",
    ),
    (
        re.compile(r"\bHerbolecer\s+\(arcaico:\s+crecer\s+en\s+hierba\)\s+crecer\s+en\s+hierba\.?"),
        "Herbolecer (arcaico: crecer en hierba).",
        "collapse_redundant_herbolecer_gloss",
    ),
    (
        re.compile(
            r"\bEchar\s+aziar\s+\(arcaico:\s+sobornar\s+o\s+cohechar\s+al\s+juez\);\s+sobornar;\s+cohechar\s+al\s+juez\.?",
            re.I,
        ),
        "Echar aziar (arcaico: sobornar o cohechar al juez).",
        "collapse_redundant_aziar_gloss",
    ),
    (
        re.compile(r"\bpescudar\s+\(arcaico:\s+preguntar\s+o\s+averiguar\)\s+o\s+preguntar\.?"),
        "pescudar (arcaico: preguntar o averiguar).",
        "collapse_redundant_pescudar_gloss",
    ),
    (
        re.compile(r"\bPescudar\s+\(arcaico:\s+preguntar\s+o\s+averiguar\)\s+o\s+preguntar\.?"),
        "Pescudar (arcaico: preguntar o averiguar).",
        "collapse_redundant_pescudar_gloss",
    ),
    (
        re.compile(r"\bAballar\s+\(arcaico:\s+mover\s+con\s+dificultad\)\s+mover\s+con\s+dificultad\.?"),
        "Aballar (arcaico: mover con dificultad).",
        "collapse_redundant_aballar_gloss",
    ),
    (
        re.compile(r"\bAquedar\s+\(arcaico:\s+aquietar\s+o\s+detener\),\s+parar,\s+o\s+aquietar\s+el\s+ganado\.?"),
        "Aquedar (arcaico: parar, aquietar o detener) el ganado.",
        "collapse_redundant_aquedar_gloss",
    ),
    (
        re.compile(r"\baquedar\s+\(arcaico:\s+aquietar\s+o\s+detener\),\s+aquietar\s+lo\s+que\s+anda"),
        "aquedar (arcaico: aquietar o detener) lo que anda",
        "collapse_redundant_aquedar_gloss",
    ),
    (
        re.compile(r"\bAtapar\s+\(arcaico:\s+tapar\s+o\s+cubrir\),\s+o\s+tapar\.?"),
        "Atapar (arcaico: tapar o cubrir).",
        "collapse_redundant_atapar_gloss",
    ),
    (
        re.compile(r"\bechar\s+aziar\s+\(arcaico:\s+sobornar\),\s+o\s+cohechar\s+al\s+juez"),
        "echar aziar (arcaico: sobornar o cohechar al juez)",
        "collapse_redundant_aziar_gloss",
    ),
    (
        re.compile(r"\bechar\s+aziar\s+\(arcaico:\s+sobornar\),\s+o\s+sobornar\s+a\s+otro,\s+cubrir"),
        "echar aziar (arcaico: sobornar a otro), cubrir",
        "collapse_redundant_aziar_gloss",
    ),
    (
        re.compile(r"\bbarbar\s+\(arcaico:\s+tener\s+barba\),\s+comenzar\s+a\s+salir\s+la\s+barba\.?"),
        "barbar (arcaico: comenzar a salir la barba).",
        "collapse_redundant_barbar_gloss",
    ),
    (
        re.compile(r"\bBarbar\s+\(arcaico:\s+tener\s+barba\)\s+comenzar\s+a\s+tener\s+barbas\.?"),
        "Barbar (arcaico: comenzar a tener barbas).",
        "collapse_redundant_barbar_gloss",
    ),
    (
        re.compile(r"\bBarbar\s+\(arcaico:\s+tener\s+barba\),\s+comenzar\s+[aá]\s+salir\s+la\s+barba\.?"),
        "Barbar (arcaico: comenzar a salir la barba).",
        "collapse_redundant_barbar_gloss",
    ),
    (
        re.compile(r"\bDentecer\s+\(arcaico:\s+nacer\s+los\s+dientes\)\s+nacer\s+los\s+dientes\.?"),
        "Dentecer (arcaico: nacer los dientes).",
        "collapse_redundant_dentecer_gloss",
    ),
    (
        re.compile(r"\bdentecer\s+\(arcaico:\s+nacer\s+los\s+dientes\)\s+nacer\s+los\s+dientes\.?"),
        "dentecer (arcaico: nacer los dientes).",
        "collapse_redundant_dentecer_gloss",
    ),
]


def load_rla_old_verbs() -> set[str]:
    verbs: set[str] = set()
    if not RLA_OLD_VERBS_PATH.exists():
        return verbs
    for raw_line in RLA_OLD_VERBS_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        verbs.add(line.split("/", 1)[0].strip().lower())
    return verbs


def token_regex(tokens: set[str]) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![{LETTER}])("
        + "|".join(re.escape(token) for token in sorted(tokens, key=len, reverse=True))
        + rf")(?![{LETTER}])",
        re.I,
    )


def in_annotation(text: str, start: int) -> bool:
    open_index = text.rfind("(", 0, start)
    close_index = text.rfind(")", 0, start)
    if open_index <= close_index:
        return False
    marker = text[open_index : min(len(text), open_index + 24)].lower()
    return marker.startswith("(arcaico:") or marker.startswith("(latín:") or marker.startswith("(latin:")


def token_already_annotated(text: str, end: int) -> bool:
    return text[end:].lstrip().lower().startswith("(arcaico:")


def in_phrase_annotation(text: str, start: int, end: int) -> bool:
    for pattern in PHRASE_ALREADY_ANNOTATED:
        for match in pattern.finditer(text):
            if match.start() <= start and end <= match.end():
                return True
    return False


def preserve_case_annotation(token: str, gloss: str) -> str:
    return f"{token} (arcaico: {gloss})"


def annotate_translation(text: str, pattern: re.Pattern[str]) -> tuple[str, list[dict[str, str]]]:
    replacements: list[dict[str, str | int]] = []
    for match in pattern.finditer(text):
        token = match.group(0)
        token_key = token.lower()
        if token_key not in CURATED_GLOSSES:
            continue
        if in_annotation(text, match.start()):
            continue
        if token_already_annotated(text, match.end()):
            continue
        if in_phrase_annotation(text, match.start(), match.end()):
            continue
        replacement = preserve_case_annotation(token, CURATED_GLOSSES[token_key])
        replacements.append(
            {
                "start": match.start(),
                "end": match.end(),
                "token": token,
                "replacement": replacement,
                "gloss": CURATED_GLOSSES[token_key],
            }
        )

    updated = text
    for item in reversed(replacements):
        start = int(item["start"])
        end = int(item["end"])
        updated = updated[:start] + str(item["replacement"]) + updated[end:]

    clean_replacements = [
        {
            "token": str(item["token"]),
            "replacement": str(item["replacement"]),
            "gloss": str(item["gloss"]),
        }
        for item in replacements
    ]
    for cleanup_pattern, cleanup_replacement, cleanup_reason in POST_CLEANUPS:
        cleaned = cleanup_pattern.sub(cleanup_replacement, updated)
        if cleaned != updated:
            updated = cleaned
            clean_replacements.append(
                {
                    "token": cleanup_reason,
                    "replacement": cleanup_replacement,
                    "gloss": "post-cleanup",
                }
            )

    if updated == text:
        return text, []

    return updated, clean_replacements


def review_candidates(
    text: str,
    source: str,
    rla_old_verbs: set[str],
    applied_tokens: set[str],
    candidate_pattern: re.Pattern[str],
) -> list[dict[str, str]]:
    review: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in candidate_pattern.finditer(text):
        token = match.group(0)
        token_key = token.lower()
        if token_key in seen:
            continue
        seen.add(token_key)
        if token_key in applied_tokens or token_key in CURATED_GLOSSES:
            continue
        if token_key in REVIEW_FALSE_POSITIVES:
            continue
        if in_annotation(text, match.start()) or token_already_annotated(text, match.end()):
            continue
        reason = "rla_antiquated_no_curated_gloss"
        if token_key in SPELLING_OR_UNCERTAIN:
            reason = "possible_spelling_variant_or_context_specific"
        elif token_key in CONTEXT_REVIEW_VERBS:
            reason = "context_derived_no_curated_gloss"
        review.append(
            {
                "candidate_verb": token,
                "reason": reason,
                "source": "RLA VerbosAnticuadosDesusados"
                if token_key in rla_old_verbs
                else "context-derived local match",
                "proposed_annotation": f"{token} (arcaico: [revisar])",
            }
        )
    return review


def main() -> None:
    rla_old_verbs = load_rla_old_verbs()
    curated_tokens = set(CURATED_GLOSSES)
    auto_pattern = token_regex(curated_tokens)
    review_pattern = token_regex(rla_old_verbs | curated_tokens | CONTEXT_REVIEW_VERBS)

    rows = []
    report = []
    review = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            source = row.get("Fuente") or ""
            old = row.get("Traducción") or ""
            applied_tokens: set[str] = set()

            if source and source not in SKIP_SOURCES:
                new, replacements = annotate_translation(old, auto_pattern)
                if new != old:
                    row["Traducción"] = new
                    applied_tokens = {item["token"].lower() for item in replacements}
                    report.append(
                        {
                            "record_id": row.get("record_id"),
                            "source": source,
                            "lemma": row.get("Texto estandarizado"),
                            "old_translation": old,
                            "new_translation": new,
                            "replacements": replacements,
                        }
                    )

                current = row.get("Traducción") or ""
                candidates = review_candidates(current, source, rla_old_verbs, applied_tokens, review_pattern)
                for candidate in candidates:
                    review.append(
                        {
                            "record_id": row.get("record_id"),
                            "source": source,
                            "lemma": row.get("Texto estandarizado"),
                            "translation": current,
                            **candidate,
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

        with REVIEW_PATH.open("w", encoding="utf-8") as fh:
            for item in review:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(report)}")
    print(f"review_rows={len(review)}")
    print(f"report={REPORT_PATH if not DRY_RUN else '(dry-run)'}")
    print(f"review={REVIEW_PATH if not DRY_RUN else '(dry-run)'}")


if __name__ == "__main__":
    main()
