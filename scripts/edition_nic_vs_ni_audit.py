#!/usr/bin/env python3
"""Audit possible nic- forms that were cleaned as ni- + c...

Some expanded Molina-style rows contain first-person/object material attached to
the lexical head. The attached-marker cleanup strips person/object prefixes when
the prior + report makes the head clear. This audit looks for the ambiguous
shape:

    nic + V...  -> V...
    ni + cV...  -> cV...

and reports cases where data currently kept the c-initial head even though a
vowel-initial head is attested elsewhere.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATA_PATH = Path("data/data.jsonl.gz")
PLUS_REPORT_PATH = Path("scripts/edition_plus_decondense_report.jsonl")
REPORT_PATH = Path("scripts/edition_nic_vs_ni_audit_report.jsonl")

INDEX_SOURCES = {
    "1580 CF Index",
}

VOWELS = set("aeiou")

TRANSLATION_STOPWORDS = {
    "a",
    "al",
    "algo",
    "alguna",
    "alguno",
    "ante",
    "asi",
    "como",
    "con",
    "cosa",
    "de",
    "del",
    "el",
    "en",
    "es",
    "esta",
    "este",
    "la",
    "las",
    "le",
    "lo",
    "los",
    "me",
    "mi",
    "ni",
    "o",
    "otro",
    "para",
    "por",
    "que",
    "se",
    "ser",
    "su",
    "tal",
    "un",
    "una",
    "y",
    "yo",
}


def ascii_fold(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower()


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z]+", ascii_fold(text or ""))


def translation_terms(text: str) -> set[str]:
    return {tok for tok in tokens(text) if len(tok) > 2 and tok not in TRANSLATION_STOPWORDS}


def is_lexical_source(row: dict[str, Any]) -> bool:
    return row.get("Fuente") not in INDEX_SOURCES


def read_rows() -> list[dict[str, Any]]:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def read_plus_report() -> list[dict[str, Any]]:
    if not PLUS_REPORT_PATH.exists():
        return []
    with PLUS_REPORT_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def build_evidence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    token_counts: Counter[str] = Counter()
    lexical_exact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    lexical_token_counts: Counter[str] = Counter()

    for row in rows:
        edition = ascii_fold(str(row.get("Texto estandarizado") or "")).strip()
        edition = re.sub(r"\s+", " ", edition)
        if edition:
            exact[edition].append(row)
            if is_lexical_source(row):
                lexical_exact[edition].append(row)
        for token in tokens(str(row.get("Texto estandarizado") or "")):
            token_counts[token] += 1
            if is_lexical_source(row):
                lexical_token_counts[token] += 1

    return {
        "exact": exact,
        "token_counts": token_counts,
        "lexical_exact": lexical_exact,
        "lexical_token_counts": lexical_token_counts,
    }


def snippets(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, str]]:
    out = []
    for row in rows[:limit]:
        out.append(
            {
                "record_id": str(row.get("record_id") or ""),
                "source": str(row.get("Fuente") or ""),
                "edition": str(row.get("Texto estandarizado") or ""),
                "translation": str(row.get("Traducción") or ""),
            }
        )
    return out


def context_score(candidate_translation: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_terms = translation_terms(candidate_translation)
    best_score = 0
    best_overlap: list[str] = []
    best_example: dict[str, str] | None = None
    for row in rows:
        row_terms = translation_terms(str(row.get("Traducción") or ""))
        overlap = sorted(candidate_terms & row_terms)
        if len(overlap) > best_score:
            best_score = len(overlap)
            best_overlap = overlap
            best_example = {
                "record_id": str(row.get("record_id") or ""),
                "source": str(row.get("Fuente") or ""),
                "edition": str(row.get("Texto estandarizado") or ""),
                "translation": str(row.get("Traducción") or ""),
            }
    return {
        "score": best_score,
        "overlap": best_overlap,
        "example": best_example,
    }


def classify(c_head: str, v_head: str, evidence: dict[str, Any]) -> str:
    c_exact_lex = len(evidence["lexical_exact"].get(c_head, []))
    v_exact_lex = len(evidence["lexical_exact"].get(v_head, []))
    c_token_lex = evidence["lexical_token_counts"].get(c_head, 0)
    v_token_lex = evidence["lexical_token_counts"].get(v_head, 0)

    if v_exact_lex and not c_exact_lex:
        return "likely_vowel_head"
    if v_exact_lex and c_exact_lex:
        return "review_both_exact"
    if v_token_lex and not c_token_lex:
        return "review_vowel_token_only"
    if v_token_lex and c_token_lex:
        return "review_both_tokens"
    return "probably_c_or_unattested_vowel"


def candidate_from_c_head(record_id: str, row: dict[str, Any], c_head: str, context: str) -> dict[str, Any] | None:
    if not c_head.startswith("c") or len(c_head) < 4:
        return None
    v_head = c_head[1:]
    if not v_head or v_head[0] not in VOWELS:
        return None

    original_tokens = tokens(str(row.get("Escritura original") or ""))
    if not any(tok == "nic" + v_head or tok.startswith("nic" + v_head) for tok in original_tokens):
        # The plus report is already context; current-data scans need original
        # support so ordinary c-initial roots are not reported.
        if context != "plus_report":
            return None

    current_tokens = tokens(str(row.get("Texto estandarizado") or ""))
    status = "current_has_c_head" if c_head in current_tokens else "current_has_vowel_head" if v_head in current_tokens else "current_unclear"
    return {
        "record_id": row.get("record_id") or record_id,
        "source": row.get("Fuente"),
        "original": row.get("Escritura original"),
        "edition": row.get("Texto estandarizado"),
        "translation": row.get("Traducción"),
        "context": context,
        "c_head": c_head,
        "vowel_head": v_head,
        "status": status,
    }


def plus_report_candidates(plus_rows: list[dict[str, Any]], rows_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for report in plus_rows:
        record_id = str(report.get("record_id") or "")
        old_tokens = tokens(str(report.get("old_edition") or ""))
        if len(old_tokens) != 1:
            continue
        c_head = old_tokens[0]
        if not c_head.startswith("c") or len(c_head) < 4:
            continue
        v_head = c_head[1:]
        if not v_head or v_head[0] not in VOWELS:
            continue
        new_tokens = tokens(str(report.get("new_edition") or ""))
        if "nic" + v_head not in new_tokens:
            continue

        row = rows_by_id.get(record_id)
        if not row:
            row = {
                "record_id": record_id,
                "Fuente": report.get("source"),
                "Escritura original": report.get("original"),
                "Texto estandarizado": report.get("new_edition"),
                "Traducción": report.get("translation"),
            }
        candidate = candidate_from_c_head(record_id, row, c_head, "plus_report")
        if candidate:
            candidate["plus_old_edition"] = report.get("old_edition")
            candidate["plus_new_edition"] = report.get("new_edition")
            out.append(candidate)
    return out


def current_data_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for row in rows:
        original_tokens = tokens(str(row.get("Escritura original") or ""))
        edition_tokens = tokens(str(row.get("Texto estandarizado") or ""))
        for original_token in original_tokens:
            if not original_token.startswith("nic") or len(original_token) < 5:
                continue
            v_head = original_token[3:]
            if not v_head or v_head[0] not in VOWELS:
                continue
            c_head = "c" + v_head
            if c_head not in edition_tokens and v_head not in edition_tokens:
                continue
            key = (row.get("record_id"), c_head, v_head)
            if key in seen:
                continue
            seen.add(key)
            candidate = candidate_from_c_head(str(row.get("record_id") or ""), row, c_head, "current_data")
            if candidate:
                out.append(candidate)
    return out


def enrich(candidate: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    c_head = str(candidate["c_head"])
    v_head = str(candidate["vowel_head"])
    candidate["decision"] = classify(c_head, v_head, evidence)
    candidate["c_exact_lexical_count"] = len(evidence["lexical_exact"].get(c_head, []))
    candidate["vowel_exact_lexical_count"] = len(evidence["lexical_exact"].get(v_head, []))
    candidate["c_token_lexical_count"] = evidence["lexical_token_counts"].get(c_head, 0)
    candidate["vowel_token_lexical_count"] = evidence["lexical_token_counts"].get(v_head, 0)
    candidate["c_exact_examples"] = snippets(evidence["lexical_exact"].get(c_head, []))
    candidate["vowel_exact_examples"] = snippets(evidence["lexical_exact"].get(v_head, []))
    c_context = context_score(str(candidate.get("translation") or ""), evidence["lexical_exact"].get(c_head, []))
    vowel_context = context_score(str(candidate.get("translation") or ""), evidence["lexical_exact"].get(v_head, []))
    candidate["c_translation_score"] = c_context["score"]
    candidate["vowel_translation_score"] = vowel_context["score"]
    candidate["c_translation_overlap"] = c_context["overlap"]
    candidate["vowel_translation_overlap"] = vowel_context["overlap"]
    candidate["c_translation_example"] = c_context["example"]
    candidate["vowel_translation_example"] = vowel_context["example"]
    if vowel_context["score"] > c_context["score"]:
        candidate["translation_context"] = "vowel_head"
    elif c_context["score"] > vowel_context["score"]:
        candidate["translation_context"] = "c_head"
    else:
        candidate["translation_context"] = "tie_or_no_signal"
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", default="", help="Only print summary rows for this decision")
    args = parser.parse_args()

    rows = read_rows()
    rows_by_id = {str(row.get("record_id") or ""): row for row in rows}
    evidence = build_evidence(rows)

    all_candidates = []
    seen = set()
    for candidate in plus_report_candidates(read_plus_report(), rows_by_id) + current_data_candidates(rows):
        key = (candidate.get("record_id"), candidate.get("c_head"), candidate.get("vowel_head"))
        if key in seen:
            continue
        seen.add(key)
        all_candidates.append(enrich(candidate, evidence))

    all_candidates.sort(
        key=lambda c: (
            str(c.get("decision")),
            str(c.get("c_head")),
            str(c.get("record_id")),
        )
    )

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        for candidate in all_candidates:
            f.write(json.dumps(candidate, ensure_ascii=False, separators=(",", ":")) + "\n")

    counts = Counter(str(c.get("decision")) for c in all_candidates)
    status_counts = Counter(str(c.get("status")) for c in all_candidates)
    print(json.dumps({"candidates": len(all_candidates), "decisions": counts, "status": status_counts, "report": str(REPORT_PATH)}, ensure_ascii=False, indent=2))

    shown = 0
    for candidate in all_candidates:
        if args.decision and candidate.get("decision") != args.decision:
            continue
        if shown >= 80:
            break
        shown += 1
        print(
            f"{candidate['decision']} | {candidate['status']} | {candidate['record_id']} | "
            f"{candidate['c_head']} -> {candidate['vowel_head']} | "
            f"{candidate['edition']} | {candidate['translation']}"
        )


if __name__ == "__main__":
    main()
