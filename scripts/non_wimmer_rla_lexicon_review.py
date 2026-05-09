#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEXICON_ROOT = ROOT / "resources" / "dictionaries" / "rla-es-2.9" / "ortografia" / "palabras"
REVIEW_PATH = ROOT / "scripts" / "non_wimmer_spellcheck_suggestion_review.tsv"
OUT_PATH = ROOT / "scripts" / "non_wimmer_rla_lexicon_review.tsv"
SUMMARY_PATH = ROOT / "scripts" / "non_wimmer_rla_lexicon_review_summary.txt"
ACCOUNTING_PATH = ROOT / "scripts" / "non_wimmer_spellcheck_accounting.json"
STRICT = os.environ.get("STRICT") == "1"

LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"


KNOWN_DLE_VALID = {
    "bodegonero": "DLE: bodegonero, ra",
    "bodegonera": "DLE: bodegonero, ra",
    "oriniento": "DLE: oriniento, ta",
    "orinienta": "DLE: oriniento, ta",
    "baldrés": "DLE: baldrés",
}

KNOWN_HISTORICAL_VALID = {
    "bofetear": "DHLE: bofetear",
    "bular": "DLE: bular",
}

KNOWN_REGIONAL_OR_DOMAIN = {
    "balacear",
    "balacearse",
    "brilloso",
    "brillosa",
    "barbasco",
    "brasier",
    "chahuiztle",
    "cotaras",
    "cutaras",
    "deshierbar",
    "deshierbarle",
    "deshierbarlo",
    "ocozintle",
    "piciete",
    "tehuizote",
    "tzinacapense",
}

FORCE_SOURCE_TOKENS = {
    "achto",
    "adversus",
    "advo",
    "aocmo",
    "applic",
    "atolli",
    "axin",
    "bluteau",
    "calpolli",
    "calli",
    "catzin",
    "cauh",
    "cenca",
    "chilli",
    "chihc",
    "chim",
    "chinoa",
    "chtli",
    "chit",
    "cihu",
    "citl",
    "cuexco",
    "cuepa",
    "ctli",
    "echihchili",
    "ehcac",
    "generaliter",
    "hrer",
    "ahmo",
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
    "imman",
    "inver",
    "iquac",
    "itech",
    "itta",
    "ixpan",
    "iztac",
    "iuhqu",
    "iuiyotia",
    "iuan",
    "litt",
    "lloh",
    "ltia",
    "ltin",
    "macac",
    "mahm",
    "malinalli",
    "matl",
    "metaforam",
    "metap",
    "mauhc",
    "mauizopoloa",
    "mauizopololo",
    "mecapalli",
    "micc",
    "mictia",
    "mixc",
    "nanimado",
    "nalli",
    "natiuh",
    "neltilia",
    "nict",
    "nilia",
    "nemi",
    "nimis",
    "nite",
    "nopani",
    "ntli",
    "ntzinco",
    "oculis",
    "pfeffer",
    "pinolli",
    "plur",
    "patolli",
    "quod",
    "quemmach",
    "quecholli",
    "redupl",
    "sommer",
    "tech",
    "teht",
    "teitec",
    "temazcalli",
    "tepit",
    "tequiz",
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
    "toznene",
    "zcayoh",
    "ztli",
    "çolmiquiztli",
}

FORCE_PROPER_NAME_TOKENS = {
    "ayotzinapan",
    "bangladesh",
    "huitzilan",
    "teziutlan",
    "teziutlán",
    "tzinacapan",
    "tzicuilan",
}

FORCE_TAXONOMY_TOKENS = {
    "acuminata",
    "bixa",
    "bracteata",
    "geomys",
    "physalis",
    "zenaida",
}

FORCE_VALID_SPANISH_TOKENS = {
    "acivilado",
    "acivilarse",
    "acivilizarse",
    "adentellada",
    "adentelladas",
    "adentellar",
    "aborrecedora",
    "agradecedor",
    "amollentada",
    "animalías",
    "asaeteado",
    "atestiguadores",
    "atraedor",
    "ayuntando",
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
    "bravísimamente",
    "cabizcaído",
    "calendárico",
    "comprendedor",
    "crismado",
    "descervigado",
    "desbarrancarse",
    "desenalbardada",
    "desenalbardadura",
    "desenalbardador",
    "desenalbardar",
    "deleznarse",
    "denunciación",
    "dolar",
    "encarbonar",
    "enerizado",
    "enhetrada",
    "enreciar",
    "enredadizo",
    "enriquecidamente",
    "ésta",
    "excusación",
    "frijolar",
    "hijada",
    "irado",
    "justiciado",
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
    "semillado",
    "sementado",
    "sobarcada",
    "tabernear",
    "tintor",
    "trogón",
    "tuzan",
}

FORCE_OLD_SPANISH_REVIEW_TOKENS = {
    "abuhamiento",
    "bulliciador",
    "cuzilla",
    "embizmador",
    "omezillo",
}

OPEN_REVIEW_BUCKETS = {
    "accent_review",
    "old_spanish_review",
}

TAXONOMY_WORD_RE = re.compile(
    r"\b("
    r"familia|subfamilia|género|genero|especie|planta|árbol|arbol|serpiente|"
    r"botánica|botanica|ornamental|medicinal|forraje|herbácea|herbacea|oruga"
    r")\b",
    re.I,
)
TAXONOMY_BINOMIAL_RE = re.compile(
    r"\([A-Z][a-z]+ (?!de\b|del\b|la\b|el\b|los\b|las\b)[a-z]+|"
    r"\b[A-Z][a-z]+ (?:sp|spp|L|DC|Benth|Bertol|Bonpl|Ruiz)\.?\b"
)
TAXONOMY_SUFFIXES = (
    "aceae",
    "áceas",
    "ácea",
    "eae",
    "oides",
    "ensis",
    "ifolia",
    "ifera",
    "aria",
    "ellia",
    "onia",
    "bium",
    "ops",
)
NAHUATL_TOKEN_RE = re.compile(r"(?:tz|tl|hu|auh|iuh|itz|quiz|tzin|qui|ç|xoch|cuauh|teo|tla)")
SOURCE_NOTE_RE = re.compile(r"\b(?:cf\.|véase|vease|vide|idem|pt\.|ca\.|lo mismo es que|lo mismo que|ver)\b", re.I)


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def key(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip().lower())


def plain_key(value: str) -> str:
    return strip_accents(key(value))


def lexicon_section(path: Path) -> str:
    rel = path.relative_to(LEXICON_ROOT)
    parts = rel.parts
    if parts[0] == "RAE":
        if "l10n" in parts:
            idx = parts.index("l10n")
            region = parts[idx + 1] if idx + 1 < len(parts) else "regional"
            return f"RAE/{region}"
        return "RAE"
    if parts[0] == "noRAE":
        if "l10n" in parts:
            idx = parts.index("l10n")
            region = parts[idx + 1] if idx + 1 < len(parts) else "regional"
            return f"noRAE/{region}"
        return "noRAE"
    return parts[0]


def load_lexicon() -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, set[str]]]:
    exact: dict[str, set[str]] = defaultdict(set)
    accentless: dict[str, set[str]] = defaultdict(set)
    files: dict[str, set[str]] = defaultdict(set)

    for path in sorted(LEXICON_ROOT.rglob("*.txt")):
        section = lexicon_section(path)
        category = path.stem
        label = f"{section}/{category}"
        for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            lemma = line.split("/", 1)[0].strip()
            if not lemma:
                continue
            lemma_key = key(lemma)
            exact[lemma_key].add(label)
            accentless[plain_key(lemma)].add(lemma_key)
            files[lemma_key].add(str(path.relative_to(ROOT)))

    return exact, accentless, files


def classify_token(token: str, exact: dict[str, set[str]], accentless: dict[str, set[str]]) -> tuple[str, str]:
    token_key = key(token)
    if token_key in exact:
        labels = sorted(exact[token_key])
        if any("/VerbosAnticuadosDesusados" in label for label in labels):
            return "rla_exact_antiquated", "; ".join(labels[:8])
        if any(label.startswith("RAE/") or label == "RAE" for label in labels):
            return "rla_exact_rae", "; ".join(labels[:8])
        if any(label.startswith("noRAE") for label in labels):
            return "rla_exact_no_rae", "; ".join(labels[:8])
        return "rla_exact_other", "; ".join(labels[:8])

    if token_key.endswith("se"):
        base_key = token_key[:-2]
        if base_key in exact:
            labels = sorted(exact[base_key])
            if any(label.startswith("RAE/") or label == "RAE" for label in labels):
                return "rla_reflexive_rae", f"{base_key} :: {'; '.join(labels[:8])}"
            if any(label.startswith("noRAE") for label in labels):
                return "rla_reflexive_no_rae", f"{base_key} :: {'; '.join(labels[:8])}"
            return "rla_reflexive_other", f"{base_key} :: {'; '.join(labels[:8])}"

    plain = plain_key(token)
    if plain in accentless:
        matches = sorted(accentless[plain])
        sample_labels: list[str] = []
        for match in matches[:8]:
            sample_labels.extend(sorted(exact.get(match, []))[:2])
        return "rla_accent_variant", f"{', '.join(matches[:8])} :: {'; '.join(sample_labels[:8])}"

    return "not_in_rla", ""


def looks_taxonomy(row: dict[str, str]) -> bool:
    token = key(row["token"])
    translation = row["translation"]
    if token.endswith(TAXONOMY_SUFFIXES):
        return True
    if TAXONOMY_WORD_RE.search(translation) or TAXONOMY_BINOMIAL_RE.search(translation):
        return True
    return False


def looks_nahuatl_or_source(row: dict[str, str]) -> bool:
    token = key(row["token"])
    translation = row["translation"].lower()
    lemma = (row.get("lemma") or "").lower()
    if token and token in {part.strip(".,;:()[]{}+-") for part in lemma.split()}:
        return True
    if NAHUATL_TOKEN_RE.search(token) and re.search(rf"\b{re.escape(token)}\b", translation):
        return True
    if SOURCE_NOTE_RE.search(translation) and NAHUATL_TOKEN_RE.search(token):
        return True
    if re.search(rf"\b(?:cf\.|véase|vease|vide|idem|ver)\s+{re.escape(token)}\b", translation):
        return True
    if re.search(rf"\b(?:pt\.|ca\.)\s+[^\n/;]*\b{re.escape(token)}\b", translation):
        return True
    return False


def looks_annotated_archaic(row: dict[str, str]) -> bool:
    token = key(row["token"])
    translation = row["translation"].lower()
    return "(arcaico:" in translation and re.search(rf"\b{re.escape(token)}\b", translation) is not None


def looks_annotated_latin(row: dict[str, str]) -> bool:
    token = key(row["token"])
    translation = row["translation"].lower()
    return "(latín:" in translation and re.search(rf"\b{re.escape(token)}\b", translation) is not None


def looks_proper_name(row: dict[str, str]) -> bool:
    token = key(row["token"])
    translation = row["translation"]
    rla_match = row.get("rla_match") or ""
    if "toponimos/" in rla_match or "NombresPropiosSiglas" in rla_match:
        return True
    if token in {
        "huitzilopochtli",
        "huitzilopuchtli",
        "braulio",
        "bartolomé",
        "baco",
        "orizaba",
        "teziutlan",
        "teziutlán",
        "guadalupe",
        "quinatzin",
        "bangladesh",
    }:
        return True
    return False


def looks_diminutive_or_productive(row: dict[str, str]) -> bool:
    token = key(row["token"])
    return token.endswith(
        (
            "ito",
            "ita",
            "itos",
            "itas",
            "illo",
            "illa",
            "illos",
            "illas",
            "cillo",
            "cilla",
            "cillos",
            "cillas",
            "uelo",
            "uela",
            "uelos",
            "uelas",
            "ejo",
            "eja",
            "ejos",
            "ejas",
            "amiento",
            "imiento",
            "adura",
            "edura",
            "idor",
            "idora",
            "ador",
            "adora",
            "dero",
            "dera",
            "dad",
            "eza",
        )
    )


def review_bucket(row: dict[str, str]) -> tuple[str, str]:
    token = key(row["token"])
    status = row["rla_status"]
    source = row.get("source") or ""

    if token in FORCE_SOURCE_TOKENS:
        return "subtract_nahuatl_or_source", "exact source-form token"
    if token in FORCE_PROPER_NAME_TOKENS:
        return "subtract_proper_name", "proper name or toponym"
    if token in FORCE_TAXONOMY_TOKENS:
        return "subtract_taxonomy_latin", "scientific/taxonomic token"
    if token in FORCE_VALID_SPANISH_TOKENS:
        return "subtract_valid_spanish", "valid Spanish form missed by review heuristics"
    if token in FORCE_OLD_SPANISH_REVIEW_TOKENS:
        if looks_annotated_archaic(row):
            return "subtract_annotated_archaic", "archaic form retained with modern help"
        return "old_spanish_review", "old-Spanish candidate forced out of broad derivative bucket"
    if looks_taxonomy(row):
        return "subtract_taxonomy_latin", "scientific/taxonomic context"
    if token in KNOWN_REGIONAL_OR_DOMAIN:
        return "subtract_regional_or_domain", "modern/regional/domain vocabulary"
    if looks_nahuatl_or_source(row):
        return "subtract_nahuatl_or_source", "Nahuatl form or cross-reference note"
    if looks_annotated_archaic(row):
        return "subtract_annotated_archaic", "archaic form retained with modern help"
    if looks_annotated_latin(row):
        return "subtract_annotated_latin", "Latin form retained with modern help"
    if looks_proper_name(row):
        return "subtract_proper_name", "proper name or toponym"
    if token in KNOWN_DLE_VALID:
        return "subtract_dle_valid", KNOWN_DLE_VALID[token]
    if token in KNOWN_HISTORICAL_VALID:
        return "subtract_historical_valid", KNOWN_HISTORICAL_VALID[token]
    if status in {
        "rla_exact_rae",
        "rla_exact_no_rae",
        "rla_exact_other",
        "rla_exact_antiquated",
        "rla_reflexive_rae",
        "rla_reflexive_no_rae",
        "rla_reflexive_other",
    }:
        return "subtract_rla_valid", status
    if source.startswith(("V94 ", "1984 ", "2002 ")):
        return "subtract_regional_or_domain", "modern/regional/domain vocabulary"
    if looks_diminutive_or_productive(row):
        return "subtract_productive_derivative", "productive diminutive or derivational form"
    if status == "rla_accent_variant":
        return "accent_review", row.get("rla_match") or "accent-only match"
    return "old_spanish_review", "not in RLA and not subtracted by heuristic"


def compact_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "token": row["token"],
        "count": int(row["count"]),
        "source": row["source"],
        "lemma": row["lemma"],
        "translation": row["translation"],
        "suggestion": row["guess"],
        "relation": row["relation"],
        "rla_status": row["rla_status"],
        "rla_match": row["rla_match"],
        "review_bucket": row["review_bucket"],
        "bucket_reason": row["bucket_reason"],
    }


def write_accounting(
    rows: list[dict[str, str]],
    bucket_counts: Counter[str],
    bucket_occurrence_counts: Counter[str],
) -> list[dict[str, str]]:
    open_rows = [row for row in rows if row["review_bucket"] in OPEN_REVIEW_BUCKETS]
    accounted_rows = [row for row in rows if row["review_bucket"] not in OPEN_REVIEW_BUCKETS]
    accounting = {
        "scope": "Traducción, excluding 2021 Wimmer, 1992 Karttunen, V94 Diccionario Global SNP",
        "purpose": "Account for spellcheck/RLA flags after high-confidence orthography and context passes.",
        "open_review_buckets": sorted(OPEN_REVIEW_BUCKETS),
        "review_rows": len(rows),
        "review_occurrences": sum(int(row["count"]) for row in rows),
        "open_review_rows": len(open_rows),
        "open_review_occurrences": sum(int(row["count"]) for row in open_rows),
        "accounted_rows": len(accounted_rows),
        "accounted_occurrences": sum(int(row["count"]) for row in accounted_rows),
        "buckets": {
            bucket: {
                "rows": bucket_counts[bucket],
                "occurrences": bucket_occurrence_counts[bucket],
                "open": bucket in OPEN_REVIEW_BUCKETS,
            }
            for bucket in sorted(bucket_counts)
        },
        "tokens": [compact_row(row) for row in rows],
        "open_tokens": [compact_row(row) for row in open_rows],
    }
    ACCOUNTING_PATH.write_text(json.dumps(accounting, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return open_rows


def main() -> None:
    exact, accentless, _files = load_lexicon()

    rows = []
    with REVIEW_PATH.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            status, rla_match = classify_token(row["token"], exact, accentless)
            row["rla_status"] = status
            row["rla_match"] = rla_match
            bucket, bucket_reason = review_bucket(row)
            row["review_bucket"] = bucket
            row["bucket_reason"] = bucket_reason
            rows.append(row)

    with OUT_PATH.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = list(rows[0].keys()) if rows else [
            "relation",
            "token",
            "guess",
            "count",
            "source",
            "lemma",
            "translation",
            "guesses",
            "rla_status",
            "rla_match",
        ]
        writer = csv.DictWriter(fh, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    status_counts = Counter(row["rla_status"] for row in rows)
    bucket_counts = Counter(row["review_bucket"] for row in rows)
    occurrence_counts = Counter()
    bucket_occurrence_counts = Counter()
    examples: dict[str, list[dict[str, str]]] = defaultdict(list)
    bucket_examples: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        occurrence_counts[row["rla_status"]] += int(row["count"])
        bucket_occurrence_counts[row["review_bucket"]] += int(row["count"])
        if len(examples[row["rla_status"]]) < 12:
            examples[row["rla_status"]].append(
                {
                    "token": row["token"],
                    "count": row["count"],
                    "source": row["source"],
                    "lemma": row["lemma"],
                    "translation": row["translation"][:160],
                    "rla_match": row["rla_match"][:180],
                }
            )
        if len(bucket_examples[row["review_bucket"]]) < 16:
            bucket_examples[row["review_bucket"]].append(
                {
                    "token": row["token"],
                    "count": row["count"],
                    "source": row["source"],
                    "lemma": row["lemma"],
                    "translation": row["translation"][:160],
                    "reason": row["bucket_reason"][:180],
                }
            )

    lines = [
        f"lexicon_files={sum(1 for _ in LEXICON_ROOT.rglob('*.txt'))}",
        f"lexicon_exact_lemmas={len(exact)}",
        f"review_rows={len(rows)}",
        f"review_occurrences={sum(int(row['count']) for row in rows)}",
        "",
        "review_buckets:",
    ]
    for bucket, count in bucket_counts.most_common():
        lines.append(f"{bucket}\trows={count}\toccurrences={bucket_occurrence_counts[bucket]}")
        for example in bucket_examples[bucket]:
            lines.append("  " + json.dumps(example, ensure_ascii=False))
    lines.extend([
        "",
        "rla_statuses:",
    ]
    )
    for status, count in status_counts.most_common():
        lines.append(f"{status}\trows={count}\toccurrences={occurrence_counts[status]}")
        for example in examples[status]:
            lines.append("  " + json.dumps(example, ensure_ascii=False))
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    open_rows = write_accounting(rows, bucket_counts, bucket_occurrence_counts)

    print(f"review={OUT_PATH}")
    print(f"summary={SUMMARY_PATH}")
    print(f"accounting={ACCOUNTING_PATH}")
    print(f"review_rows={len(rows)}")
    print(f"open_review_rows={len(open_rows)}")
    if STRICT and open_rows:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
