#!/usr/bin/env python3
from __future__ import annotations

import collections
import csv
import gzip
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
RLA_REVIEW_PATH = ROOT / "scripts" / "non_wimmer_rla_lexicon_review.tsv"
OUT_PATH = ROOT / "scripts" / "non_wimmer_context_required_spelling_review.jsonl"
SUMMARY_PATH = ROOT / "scripts" / "non_wimmer_context_required_spelling_review_summary.txt"


SKIP_SOURCES = {"2021 Wimmer", "1992 Karttunen", "V94 Diccionario Global SNP"}
CONTEXT_REVIEW_BUCKETS = {"old_spanish_review", "accent_review"}
WINDOW = 90
ANNOTATION_RE = re.compile(r"\((?:arcaico|latín):[^)]*\)", re.I)
TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+|/")


SAFE_ESTA_NEXT = {
    "manera",
    "misma",
    "mismo",
    "forma",
    "tierra",
    "hora",
    "condición",
    "especie",
    "es",
    "gota",
    "causa",
    "provincia",
    "particula",
    "partícula",
    "vestidura",
    "esponja",
    "sola",
    "tarde",
    "noche",
    "vida",
    "parte",
    "frase",
    "lengua",
    "oración",
    "mañana",
    "ciudad",
    "dolencia",
    "árbol",
    "arte",
    "cosa",
    "presente",
    "enfermedad",
    "énfermedad",
    "medida",
    "injuria",
    "esto",
    "postrer",
    "razón",
    "voz",
    "palabra",
    "significación",
    "preposición",
    "batalla",
    "ermita",
    "largura",
    "mesina",
    "armadura",
    "renta",
    "posición",
    "audiencia",
    "escritura",
    "cizaña",
    "hierba",
    "nueva",
    "naturaleza",
    "vez",
    "miel",
    "eso",
    "letra",
    "terminación",
    "expresión",
    "ligatura",
    "semana",
}


SAFE_ESTA_PREV = {
    "de",
    "en",
    "a",
    "por",
    "con",
    "para",
    "padece",
    "tiene",
    "toman",
    "hacer",
    "ha",
    "pagarseha",
    "este",
    "miel",
    "danza",
    "piedra",
    "mismo",
    "sola",
    "prolijidad",
    "paloma",
    "romance",
    "acusación",
    "araña",
    "anca",
    "aunque",
    "ponzoñosa",
    "máscara",
    "es",
    "da",
    "prepos",
    "preposición",
    "yohuatzinco",
    "teotlac",
    "yohualtica",
}


CONTEXT_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "fused_or_corrupt_phrase",
        re.compile(r"\bconhera\b", re.I),
        "possible fused/corrupt phrase; row context needed before changing",
    ),
    (
        "uncertain_old_lexeme",
        re.compile(r"\bcolcedra\b", re.I),
        "uncertain old lexeme or spelling error; compare row family before changing",
    ),
    (
        "fused_para_se",
        re.compile(r"\bparase\b", re.I),
        "could be para se/para + infinitive context; needs sentence-level reading",
    ),
    (
        "fused_reflexive_preposition",
        re.compile(r"\bacostarde\b", re.I),
        "likely fused reflexive/prepositional form, but needs row context",
    ),
    (
        "fused_de_possessive",
        re.compile(r"\bdesus?\b", re.I),
        "possible de su/de sus fusion; exact correction depends on following noun",
    ),
    (
        "fused_de_ser",
        re.compile(r"\bdeser\b", re.I),
        "possible de ser fusion; avoid touching unrelated deser- words",
    ),
    (
        "accent_or_demonstrative",
        re.compile(r"\besta\b", re.I),
        "could be verb está or demonstrative esta; row context decides",
    ),
    (
        "accent_adverb",
        re.compile(r"\b(?:aca|alla|alli|aqui)\b", re.I),
        "possible adverb needing accent; verify it is not a source form or name",
    ),
]


def snippet(text: str, start: int, end: int) -> str:
    left = max(0, start - WINDOW)
    right = min(len(text), end + WINDOW)
    return text[left:right].replace("\n", " ")


def annotation_spans(text: str) -> list[tuple[int, int]]:
    return [match.span() for match in ANNOTATION_RE.finditer(text)]


def is_inside_annotation(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(span_start <= start and end <= span_end for span_start, span_end in spans)


def is_annotated_candidate(text: str, start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    for span_start, _span_end in spans:
        if end <= span_start:
            between = text[end:span_start]
            if not re.search(r"[.!?;/]", between):
                return True
            return False
    return False


def neighboring_tokens(text: str, start: int, end: int) -> tuple[str, str]:
    prev = ""
    next_ = ""
    for match in TOKEN_RE.finditer(text):
        if match.end() <= start:
            prev = match.group(0).lower()
            continue
        if match.start() >= end:
            next_ = match.group(0).lower()
            break
    return prev, next_


def is_accounted_demonstrative_esta(text: str, start: int, end: int) -> bool:
    compact = re.sub(r"\s+", " ", text.strip().lower())
    local = text[max(0, start - 8) : min(len(text), end + 12)]
    if re.search(r"\bla\s+esta\s+cosa\b", local, re.I):
        return False
    if start > 0 and text[start - 1] == "[" and end < len(text) and text[end : end + 1] == "]":
        return True
    if compact in {"esta", "esta.", "este. esta. esto.", "esta, esta, esto"}:
        return True
    if re.search(r"\beste[,;]?\s+(?:o\s+)?esta(?:\(s\))?[,;]?\s+(?:o\s+)?esto", compact):
        return True
    if re.search(r"\beste,\s+esta\s*/|/\s+esta\s*/\s+este|^esta\s*/|/\s+esta\s*/", compact):
        return True

    prev, next_ = neighboring_tokens(text, start, end)
    if next_ in SAFE_ESTA_NEXT:
        return True
    if prev in SAFE_ESTA_PREV:
        return True
    return False


def direct_pattern_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    accounted_counts: collections.Counter[str] = collections.Counter()
    seen: set[tuple[str, str, int, int]] = set()
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            source = row.get("Fuente") or ""
            if source in SKIP_SOURCES:
                continue
            translation = row.get("Traducción") or ""
            spans = annotation_spans(translation)
            record_id = row.get("record_id") or ""
            for bucket, pattern, reason in CONTEXT_PATTERNS:
                for match in pattern.finditer(translation):
                    if is_inside_annotation(match.start(), match.end(), spans):
                        continue
                    if is_annotated_candidate(translation, match.start(), match.end(), spans):
                        continue
                    if (
                        bucket == "accent_or_demonstrative"
                        and match.group(0).lower() == "esta"
                        and is_accounted_demonstrative_esta(translation, match.start(), match.end())
                    ):
                        accounted_counts["demonstrative_esta"] += 1
                        continue
                    key = (record_id, bucket, match.start(), match.end())
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(
                        {
                            "origin": "direct_pattern",
                            "bucket": bucket,
                            "candidate": match.group(0),
                            "record_id": record_id,
                            "source": source,
                            "lemma": row.get("Texto estandarizado"),
                            "translation": translation,
                            "snippet": snippet(translation, match.start(), match.end()),
                            "reason": reason,
                        }
                    )
    direct_pattern_rows.accounted_counts = accounted_counts
    return rows


def rla_review_rows() -> list[dict[str, object]]:
    if not RLA_REVIEW_PATH.exists():
        return []

    rows: list[dict[str, object]] = []
    with RLA_REVIEW_PATH.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            bucket = row.get("review_bucket") or ""
            if bucket not in CONTEXT_REVIEW_BUCKETS:
                continue
            rows.append(
                {
                    "origin": "rla_spellcheck_review",
                    "bucket": bucket,
                    "candidate": row.get("token") or "",
                    "record_id": "",
                    "source": row.get("source") or "",
                    "lemma": row.get("lemma") or "",
                    "translation": row.get("translation") or "",
                    "snippet": row.get("translation") or "",
                    "reason": row.get("bucket_reason") or "requires contextual review",
                    "guess": row.get("guess") or "",
                    "relation": row.get("relation") or "",
                    "count": row.get("count") or "",
                }
            )
    return rows


def main() -> None:
    direct_rows = direct_pattern_rows()
    accounted_counts: collections.Counter[str] = getattr(
        direct_pattern_rows, "accounted_counts", collections.Counter()
    )
    rows = direct_rows + rla_review_rows()
    rows.sort(
        key=lambda row: (
            str(row["bucket"]),
            str(row["candidate"]).lower(),
            str(row["source"]),
            str(row["lemma"]),
        )
    )

    bucket_counts = collections.Counter(str(row["bucket"]) for row in rows)
    candidate_counts = collections.Counter(str(row["candidate"]).lower() for row in rows)

    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    with SUMMARY_PATH.open("w", encoding="utf-8") as fh:
        fh.write("Context-required spelling/grammar review ledger\n")
        fh.write("scope=Traducción, excluding 2021 Wimmer, 1992 Karttunen, V94 Diccionario Global SNP\n")
        fh.write(f"rows={len(rows)}\n")
        fh.write(f"buckets={dict(bucket_counts)}\n\n")
        fh.write(f"accounted={dict(accounted_counts)}\n\n")
        fh.write("top_candidates:\n")
        for candidate, count in candidate_counts.most_common(60):
            fh.write(f"{candidate}\t{count}\n")
        if rows:
            fh.write("\nsamples:\n")
            for row in rows[:80]:
                fh.write(
                    f"{row['bucket']}\t{row['candidate']}\t{row['source']}\t"
                    f"{row['lemma']}\t{str(row['snippet'])[:220]}\n"
                )

    print(f"rows={len(rows)}")
    print(f"review={OUT_PATH}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
