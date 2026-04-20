"""Phase 1 — build the gold (EO, TE) corpus for 153? Trilingüe.

Reads data/data.jsonl.gz, keeps rows whose Fuente is "153? Trilingüe" and whose
Texto estandarizado has no "+", classifies each pair as single_token / aligned /
mismatched, and writes scripts/trilingue/pairs.jsonl plus a short stats report.

Also splits out the "+" rows (partials we eventually need to complete) into
scripts/trilingue/partials.jsonl so phase 4 has a clean input file to work from.
"""
import gzip
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "data.jsonl.gz"
OUT_DIR = Path(__file__).resolve().parent
PAIRS = OUT_DIR / "pairs.jsonl"
PARTIALS = OUT_DIR / "partials.jsonl"
STATS = OUT_DIR / "phase1_stats.txt"

FUENTE = "153? Trilingüe"


def tokenize(s: str) -> list[str]:
    # Whitespace split after trimming; keep original accents/case for inspection.
    return [t for t in re.split(r"\s+", s.strip()) if t]


def strip_diacritics(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def classify(eo_tokens: list[str], te_tokens: list[str]) -> str:
    if len(eo_tokens) == 1 and len(te_tokens) == 1:
        return "single_token"
    if len(eo_tokens) == len(te_tokens) and len(eo_tokens) > 1:
        return "aligned_multi"
    return "mismatched"


def main():
    pairs = []
    partials = []
    total_tri = 0
    skipped_empty = 0

    with gzip.open(DATA, "rb") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("Fuente") != FUENTE:
                continue
            total_tri += 1
            eo = (row.get("Escritura original") or "").strip()
            te = (row.get("Texto estandarizado") or "").strip()
            if not eo or not te:
                skipped_empty += 1
                continue

            rid = row.get("record_id")
            if "+" in te:
                # Partial — the stub before the "+" is the head-word normalization.
                stub = te.replace("+", "").strip()
                partials.append({
                    "record_id": rid,
                    "eo": eo,
                    "te_stub": stub,
                    "traduccion": row.get("Traducción", ""),
                    "comentario": row.get("Comentario", ""),
                    "eo_tokens": tokenize(eo),
                })
                continue

            eo_tokens = tokenize(eo)
            te_tokens = tokenize(te)
            pairs.append({
                "record_id": rid,
                "eo": eo,
                "te": te,
                "eo_tokens": eo_tokens,
                "te_tokens": te_tokens,
                "category": classify(eo_tokens, te_tokens),
            })

    with PAIRS.open("w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with PARTIALS.open("w", encoding="utf-8") as f:
        for p in partials:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    cat_counts = Counter(p["category"] for p in pairs)
    single = [p for p in pairs if p["category"] == "single_token"]
    # How many single-token pairs are already identical modulo diacritics?
    identical_stripped = sum(
        1 for p in single if strip_diacritics(p["eo"].lower()) == p["te"].lower()
    )
    # Char-level edit signal: how many pairs need any change at all.
    needs_change = sum(1 for p in single if p["eo"] != p["te"])

    lines = [
        f"Fuente: {FUENTE}",
        f"total rows: {total_tri}",
        f"skipped (empty EO or TE): {skipped_empty}",
        f"partials (+): {len(partials)} → {PARTIALS.name}",
        f"gold pairs: {len(pairs)} → {PAIRS.name}",
        "  by category:",
    ]
    for cat, n in cat_counts.most_common():
        lines.append(f"    {cat}: {n}")
    lines += [
        "",
        f"single-token pairs: {len(single)}",
        f"  identical after NFD-strip + lowercase: {identical_stripped} "
        f"({identical_stripped/len(single):.1%})",
        f"  pairs where EO != TE: {needs_change} ({needs_change/len(single):.1%})",
    ]

    STATS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
