#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import non_wimmer_rla_lexicon_review as rla


ROOT = Path(__file__).resolve().parents[1]
SAMPLES_PATH = ROOT / "scripts" / "spanish_general_spellcheck_samples.jsonl"
SUGGESTIONS_PATH = ROOT / "scripts" / "spanish_general_spellcheck_suggestions.jsonl"
OUT_PATH = ROOT / "scripts" / "spanish_general_spellcheck_review.tsv"
SUMMARY_PATH = ROOT / "scripts" / "spanish_general_spellcheck_review_summary.txt"


GRAMMAR_OR_ABBREV = {
    "adver",
    "adverb",
    "aplic",
    "bitrans",
    "caus",
    "conj",
    "clav",
    "pluri",
    "incl",
    "indef",
    "inanim",
    "impers",
    "nomen",
    "obj",
    "partic",
    "passif",
    "pers",
    "plur",
    "pref",
    "prepos",
    "recipr",
    "refl",
    "semipronombres",
    "trans",
    "vetativo",
}

FOREIGN_OR_SOURCE = {
    "advo",
    "adversus",
    "alijs",
    "cheval",
    "bluteau",
    "colonnes",
    "conjunction",
    "deux",
    "generaliter",
    "gilonne",
    "hrer",
    "imman",
    "inver",
    "litt",
    "metaforam",
    "metap",
    "michel",
    "nimis",
    "oculis",
    "pfeffer",
    "quod",
    "scilicet",
    "sing",
    "sommer",
    "vide",
}

KNOWN_VALID_OR_DOMAIN = {
    "acivilado",
    "acivilarse",
    "acivilizarse",
    "acuminata",
    "adentellada",
    "adentelladas",
    "adentellar",
    "afligidor",
    "agradecedor",
    "animalías",
    "arrojador",
    "asaeteado",
    "atapador",
    "atraedor",
    "ayuntando",
    "ayudador",
    "ayunta",
    "ayuntada",
    "ayuntadas",
    "ayuntado",
    "ayuntador",
    "ayuntadores",
    "ayuntados",
    "ayuntan",
    "ayuntar",
    "ayuntarse",
    "ayuntamiento",
    "ayuntamientos",
    "cabizcaído",
    "chilli",
    "comprendedor",
    "cotaras",
    "crismado",
    "cutaras",
    "calendárico",
    "descabullido",
    "descabullirse",
    "descervigado",
    "desbarrancarse",
    "desenalbardada",
    "desenalbardadura",
    "desenalbardador",
    "desenalbardar",
    "deshierbar",
    "deshierbarle",
    "deshierbarlo",
    "deleznarse",
    "denunciación",
    "dolar",
    "amollentada",
    "encarbonar",
    "enerizado",
    "enhetrada",
    "ésta",
    "excusación",
    "frijolar",
    "geomys",
    "hijada",
    "irado",
    "justiciado",
    "jonote",
    "labret",
    "ligatura",
    "limpiada",
    "limpiadas",
    "limpiado",
    "limpiador",
    "limpiadores",
    "limpiados",
    "limpiaduras",
    "limpiadero",
    "maganta",
    "mullidura",
    "marañada",
    "montosa",
    "negligentísimo",
    "physalis",
    "piciete",
    "piloncillo",
    "quitamiento",
    "sobarcada",
    "tabernear",
    "semillado",
    "sementado",
    "temascal",
    "tintor",
    "trogón",
    "tuzan",
}

KNOWN_NAHUATL_OR_SOURCE = {
    "achto",
    "aocmo",
    "applic",
    "ahmo",
    "atolli",
    "axin",
    "cauh",
    "calpolli",
    "calli",
    "cenca",
    "chit",
    "chihc",
    "chim",
    "chinoa",
    "chtli",
    "citl",
    "cuexco",
    "cuepa",
    "ctli",
    "cihu",
    "echihchili",
    "ehcac",
    "huac",
    "huahc",
    "huia",
    "huani",
    "huatl",
    "hualiztli",
    "huehp",
    "huihhu",
    "icpac",
    "inic",
    "iquac",
    "itech",
    "itta",
    "ixpan",
    "iztac",
    "lloh",
    "ltia",
    "ltin",
    "macac",
    "mahm",
    "malinalli",
    "mauhc",
    "matl",
    "mecapalli",
    "micc",
    "mictia",
    "mixc",
    "nemi",
    "nalli",
    "nanimado",
    "natiuh",
    "neltilia",
    "nict",
    "nilia",
    "nite",
    "nopani",
    "ntli",
    "patolli",
    "pinolli",
    "quemmach",
    "quecholli",
    "redupl",
    "tech",
    "teht",
    "teitec",
    "temazcalli",
    "tepit",
    "tlahchin",
    "tlahcalhu",
    "tlahtlap",
    "tlaloc",
    "tlatl",
    "tlam",
    "tlac",
    "tlahtl",
    "tomatl",
    "tzin",
    "uctli",
    "uhtli",
    "uhqui",
    "xical",
    "xiuht",
    "yopi",
    "ztli",
    "zcayoh",
    "toznene",
}

TAXONOMY_SUFFIXES = (
    "aceae",
    "oideae",
    "eae",
    "ensis",
    "ifolia",
    "ifera",
)
NAHUATLISH_RE = re.compile(r"(?:tl|tz|hu|auh|iuh|itz|quiz|tzin|catl|miqui|motla|piya|xoch|cuauh)")


def fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def best_guess(row: dict[str, object]) -> str:
    guesses = row.get("guesses") or []
    return str(guesses[0]) if guesses else ""


def relation(token: str, guess: str) -> str:
    if not guess:
        return "no_guess"
    token_lower = token.lower()
    guess_lower = guess.lower()
    if token_lower == guess_lower:
        return "capitalization_only"
    if fold(token_lower) == fold(guess_lower):
        return "accent_only"
    compact_guess = guess_lower.replace(" ", "")
    if fold(token_lower) == fold(compact_guess):
        return "spacing_only"
    return "other"


def looks_taxonomic(token: str, sample: dict[str, object]) -> bool:
    text = str(sample.get("translation") or "")
    low = token.lower()
    if low.endswith(TAXONOMY_SUFFIXES):
        return True
    return bool(re.search(r"\b(?:familia|subfamilia|género|genero|especie|botánica|botanica)\b", text, re.I))


def classify(row: dict[str, object], sample: dict[str, object], exact: dict[str, set[str]], accentless: dict[str, set[str]]) -> tuple[str, str]:
    token = str(row["token"])
    token_key = token.lower()
    guess = best_guess(row)
    rel = relation(token, guess)
    source = str(sample.get("source") or "")
    translation = str(sample.get("translation") or "")
    lemma = str(sample.get("lemma") or "")

    if rel == "capitalization_only":
        return "subtract_lowercase_policy", "spellchecker only wants capitalization"
    if token_key in GRAMMAR_OR_ABBREV:
        return "subtract_grammar_or_abbrev", "grammar marker or abbreviation"
    if token_key in FOREIGN_OR_SOURCE:
        return "subtract_foreign_or_source", "foreign/source note token"
    if token_key in KNOWN_NAHUATL_OR_SOURCE:
        return "subtract_nahuatl_or_source", "known Nahuatl/source-form token"
    if token_key in KNOWN_VALID_OR_DOMAIN:
        return "subtract_valid_or_domain", "known valid/domain vocabulary"
    if looks_taxonomic(token_key, sample):
        return "subtract_taxonomy_latin", "taxonomic/domain context"
    if token_key in {part.strip(".,;:()[]{}+-").lower() for part in lemma.split()}:
        return "subtract_nahuatl_or_source", "token appears in lemma/source form"
    if NAHUATLISH_RE.search(token_key) and re.search(rf"\b{re.escape(token_key)}\b", translation.lower()):
        return "subtract_nahuatl_or_source", "Nahuatl-shaped token in translation"

    rla_status, rla_match = rla.classify_token(token_key, exact, accentless)
    probe = {
        "token": token_key,
        "guess": guess,
        "relation": rel,
        "count": str(sample.get("count") or 0),
        "source": source,
        "lemma": lemma,
        "translation": translation,
        "guesses": ", ".join(str(g) for g in (row.get("guesses") or [])[:5]),
        "rla_status": rla_status,
        "rla_match": rla_match,
    }
    bucket, reason = rla.review_bucket(probe)
    if bucket.startswith("subtract_"):
        return bucket, reason

    if rel == "accent_only":
        return "candidate_accent", f"{token} -> {guess}"
    if rel == "spacing_only":
        return "candidate_spacing", f"{token} -> {guess}"
    if guess:
        return "candidate_spelling", f"{token} -> {guess}"
    return "review_no_guess", "spellchecker flags token without suggestion"


def main() -> None:
    samples: dict[str, dict[str, object]] = {}
    with SAMPLES_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            samples[str(item["token"])] = item

    exact, accentless, _files = rla.load_lexicon()
    rows: list[dict[str, object]] = []
    with SUGGESTIONS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            token = str(item["token"])
            sample = samples.get(token, {})
            guess = best_guess(item)
            rel = relation(token, guess)
            bucket, reason = classify(item, sample, exact, accentless)
            rows.append(
                {
                    "bucket": bucket,
                    "reason": reason,
                    "relation": rel,
                    "token": token,
                    "guess": guess,
                    "count": int(sample.get("count") or 0),
                    "source": sample.get("source") or "",
                    "record_id": sample.get("record_id") or "",
                    "lemma": sample.get("lemma") or "",
                    "field": sample.get("field") or "",
                    "translation": sample.get("translation") or "",
                    "guesses": ", ".join(str(g) for g in (item.get("guesses") or [])[:8]),
                }
            )

    priority = {
        "candidate_spelling": 0,
        "candidate_accent": 1,
        "candidate_spacing": 2,
        "review_no_guess": 3,
    }
    rows.sort(key=lambda row: (priority.get(str(row["bucket"]), 9), -int(row["count"]), str(row["token"])))

    with OUT_PATH.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = [
            "bucket",
            "reason",
            "relation",
            "token",
            "guess",
            "count",
            "source",
            "record_id",
            "lemma",
            "field",
            "translation",
            "guesses",
        ]
        writer = csv.DictWriter(fh, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    bucket_counts = Counter(str(row["bucket"]) for row in rows)
    occurrence_counts = Counter()
    examples: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        bucket = str(row["bucket"])
        occurrence_counts[bucket] += int(row["count"])
        if len(examples[bucket]) < 25:
            examples[bucket].append(
                {
                    "token": row["token"],
                    "guess": row["guess"],
                    "count": row["count"],
                    "source": row["source"],
                    "record_id": row["record_id"],
                    "lemma": row["lemma"],
                    "translation": str(row["translation"])[:180],
                    "reason": row["reason"],
                }
            )

    lines = [
        "Broad Spanish spellcheck review",
        "scope=Traducción for non-Wimmer, Traducción (es) for 2021 Wimmer, excluding 1992 Karttunen",
        f"raw_spellcheck_flags={len(rows)}",
        f"raw_spellcheck_occurrences={sum(int(row['count']) for row in rows)}",
        "",
        "buckets:",
    ]
    for bucket, count in bucket_counts.most_common():
        lines.append(f"{bucket}\trows={count}\toccurrences={occurrence_counts[bucket]}")
        for example in examples[bucket]:
            lines.append("  " + json.dumps(example, ensure_ascii=False))
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"review={OUT_PATH}")
    print(f"summary={SUMMARY_PATH}")
    print(f"raw_spellcheck_flags={len(rows)}")
    for bucket, count in bucket_counts.most_common():
        print(f"{bucket}\trows={count}\toccurrences={occurrence_counts[bucket]}")


if __name__ == "__main__":
    main()
