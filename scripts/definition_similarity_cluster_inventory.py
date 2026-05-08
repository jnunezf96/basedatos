#!/usr/bin/env python3
from __future__ import annotations

import gzip
import html
import json
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
OUT_PATH = ROOT / "scripts" / "definition_similarity_cluster_review.jsonl"
SUMMARY_PATH = ROOT / "scripts" / "definition_similarity_cluster_summary.txt"
PROTECTED_SOURCES = {"2021 Wimmer", "1992 Karttunen", "V94 Diccionario Global SNP"}

LETTER_RE = re.compile(r"[a-záéíóúüñç]+", re.I)
HTML_RE = re.compile(r"<[^>]+>")

STOPWORDS = {
    "a",
    "al",
    "algo",
    "asi",
    "así",
    "como",
    "con",
    "cosa",
    "cosas",
    "de",
    "del",
    "el",
    "en",
    "es",
    "esta",
    "este",
    "la",
    "las",
    "lo",
    "los",
    "o",
    "por",
    "que",
    "se",
    "su",
    "tal",
    "un",
    "una",
    "y",
}

# Orthographic and very conservative concept aliases used only for review
# clustering, not for rewriting data.
TOKEN_ALIASES = {
    "medulla": "medula",
    "meollo": "medula",
    "ósea": "hueso",
    "osea": "hueso",
    "tutanos": "tuetano",
    "tutano": "tuetano",
    "tuétano": "tuetano",
    "tuetanos": "tuetano",
    "huesos": "hueso",
}

MODERN_DISPLAY = {
    "medula": "médula",
    "tuetano": "tuétano",
    "hueso": "hueso",
}


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = HTML_RE.sub(" ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def lemma_key(value: str) -> str:
    value = strip_accents(value or "").lower()
    value = re.sub(r"\s*\+\s*$", "", value)
    value = re.sub(r"[^a-zñç]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def translation_for(row: dict[str, object]) -> str:
    if row.get("Fuente") == "2021 Wimmer" and row.get("Traducción (es)"):
        return str(row.get("Traducción (es)") or "")
    return str(row.get("Traducción") or row.get("Traducción (es)") or "")


def canonical_tokens(value: str) -> list[str]:
    raw_tokens = [strip_accents(t).lower() for t in LETTER_RE.findall(clean_text(value))]
    tokens = []
    for token in raw_tokens:
        token = TOKEN_ALIASES.get(token, token)
        if token not in STOPWORDS and len(token) > 1:
            tokens.append(token)
    return tokens


def canonical_string(tokens: list[str]) -> str:
    return " ".join(tokens)


def pair_score(left: list[str], right: list[str]) -> tuple[float, dict[str, float]]:
    if not left or not right:
        return 0.0, {"sequence": 0.0, "jaccard": 0.0, "containment": 0.0}
    lset, rset = set(left), set(right)
    shared = lset & rset
    sequence = SequenceMatcher(None, canonical_string(left), canonical_string(right)).ratio()
    jaccard = len(shared) / len(lset | rset)
    containment = len(shared) / min(len(lset), len(rset))
    score = max(sequence, jaccard, containment * 0.9)
    return score, {"sequence": sequence, "jaccard": jaccard, "containment": containment}


def should_link(left: list[str], right: list[str]) -> tuple[bool, str, float]:
    score, parts = pair_score(left, right)
    shared = set(left) & set(right)
    if score >= 0.72 and shared:
        return True, "high-similarity", score
    if parts["containment"] >= 0.62 and len(shared) >= 2:
        return True, "contained-definition", score
    if min(len(set(left)), len(set(right))) <= 2 and shared and score >= 0.48:
        return True, "short-shared-core", score
    return False, "", score


def components(items: list[dict[str, object]]) -> list[list[int]]:
    parent = list(range(len(items)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            ok, _reason, _score = should_link(items[i]["tokens"], items[j]["tokens"])  # type: ignore[arg-type]
            if ok:
                union(i, j)

    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(len(items)):
        groups[find(i)].append(i)
    return [group for group in groups.values() if len(group) >= 3]


def proposed_best(rows: list[dict[str, object]]) -> str:
    all_tokens: list[str] = []
    for row in rows:
        all_tokens.extend(row["tokens"])  # type: ignore[arg-type]
    counts = defaultdict(int)
    for token in all_tokens:
        counts[token] += 1

    core = [token for token, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])) if count >= 2]
    has_broad = any("gelatinosa" in row["translation"].lower() or "sustancia" in row["translation"].lower() for row in rows)  # type: ignore[index]
    has_grasa = any("grasa" in row["tokens"] for row in rows)  # type: ignore[operator]

    if {"medula", "tuetano", "hueso"} <= set(core):
        return (
            "Row-specific review: preserve meollo/Medulla with arcaico help, "
            "modernize tuétano/tuétanos spelling, and leave Wimmer/Karttunen/V94 untouched."
        )

    display = [MODERN_DISPLAY.get(token, token) for token in core[:6]]
    if not display:
        return ""
    return "; ".join(display) + "."


def row_proposal(row: dict[str, object]) -> str | None:
    if row.get("source") in PROTECTED_SOURCES:
        return None
    value = str(row.get("translation") or "")
    new = value
    new = re.sub(r"\btuetanos\b", "tuétanos", new, flags=re.I)
    new = re.sub(r"\btutanos\b", "tuétanos", new, flags=re.I)
    new = re.sub(r"\btuetano\b", "tuétano", new, flags=re.I)
    new = re.sub(r"\bMeollo\b(?!\s*\(arcaico:)", "Meollo (arcaico: médula)", new)
    new = re.sub(r"\bmeollo\b(?!\s*\(arcaico:)", "meollo (arcaico: médula)", new)
    new = re.sub(r"\bMedulla\b(?!\s*\(arcaico:)", "Medulla (arcaico: médula)", new)
    return new if new != value else None


def main() -> None:
    by_lemma: dict[str, list[dict[str, object]]] = defaultdict(list)
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            lemma = lemma_key(str(row.get("Texto estandarizado") or row.get("Lema") or ""))
            translation = clean_text(translation_for(row))
            tokens = canonical_tokens(translation)
            if not lemma or len(tokens) < 1 or not translation:
                continue
            by_lemma[lemma].append(
                {
                    "record_id": row.get("record_id"),
                    "source": row.get("Fuente"),
                    "lemma": row.get("Texto estandarizado") or row.get("Lema"),
                    "translation": translation,
                    "tokens": tokens,
                }
            )

    clusters = []
    for lemma, items in sorted(by_lemma.items()):
        if len(items) < 3:
            continue
        for group in components(items):
            rows = [items[i] for i in group]
            distinct = {row["translation"].lower().strip(". ") for row in rows}  # type: ignore[index]
            if len(distinct) < 2:
                continue
            max_pair = 0.0
            reasons = set()
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    ok, reason, score = should_link(rows[i]["tokens"], rows[j]["tokens"])  # type: ignore[arg-type]
                    max_pair = max(max_pair, score)
                    if ok:
                        reasons.add(reason)
            clusters.append(
                {
                    "cluster_key": lemma,
                    "row_count": len(rows),
                    "source_count": len({row["source"] for row in rows}),
                    "max_pair_score": round(max_pair, 3),
                    "reasons": sorted(reasons),
                    "proposed_best_spanish": proposed_best(rows),
                    "rows": [
                        {
                            "record_id": row["record_id"],
                            "source": row["source"],
                            "lemma": row["lemma"],
                            "translation": row["translation"],
                            "proposed_translation": row_proposal(row),
                        }
                        for row in rows
                    ],
                }
            )

    clusters.sort(key=lambda c: (-c["source_count"], -c["row_count"], c["cluster_key"]))

    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for cluster in clusters:
            fh.write(json.dumps(cluster, ensure_ascii=False) + "\n")

    lines = [
        f"clusters={len(clusters)}",
        f"output={OUT_PATH}",
        "",
        "top_clusters:",
    ]
    for cluster in clusters[:30]:
        sample = " | ".join(row["translation"] for row in cluster["rows"][:4])
        lines.append(
            f"{cluster['cluster_key']}\trows={cluster['row_count']}\tsources={cluster['source_count']}\t"
            f"score={cluster['max_pair_score']}\tbest={cluster['proposed_best_spanish']}\t{sample[:220]}"
        )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"clusters={len(clusters)}")
    print(f"review={OUT_PATH}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
