#!/usr/bin/env python3
from __future__ import annotations

import collections
import gzip
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
TOKENS_PATH = ROOT / "scripts" / "spanish_general_spellcheck_tokens.txt"
SAMPLES_PATH = ROOT / "scripts" / "spanish_general_spellcheck_samples.jsonl"
SUMMARY_PATH = ROOT / "scripts" / "spanish_general_spellcheck_summary.txt"


SKIP_SOURCES = {"1992 Karttunen"}
TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç]+")
ARCHAIC_MARK_RE = re.compile(r"\(\s*arcaico\s*:", re.I)
SKIP_TOKENS = {
    "arcaico",
    "latin",
    "latín",
    "cf",
    "cfr",
    "etc",
    "sah",
    "sa",
    "sis",
    "v",
    "vt",
    "vi",
    "vr",
    "refl",
    "impers",
    "pret",
    "pft",
    "pl",
    "sg",
}


def spanish_field(row: dict[str, object]) -> str:
    source = row.get("Fuente") or ""
    if source == "2021 Wimmer":
        return str(row.get("Traducción (es)") or "")
    return str(row.get("Traducción") or "")


def skip_archaic_headword(text: str, end: int) -> bool:
    after = text[end : end + 24]
    return ARCHAIC_MARK_RE.match(after.lstrip()) is not None


def is_token_candidate(token: str) -> bool:
    low = token.lower()
    if len(low) < 4:
        return False
    if low in SKIP_TOKENS:
        return False
    if low.isupper():
        return False
    if not re.search(r"[aeiouáéíóúü]", low):
        return False
    return True


def main() -> None:
    counts: collections.Counter[str] = collections.Counter()
    samples: dict[str, dict[str, object]] = {}
    scoped_rows = 0

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            source = row.get("Fuente") or ""
            if source in SKIP_SOURCES:
                continue
            translation = spanish_field(row)
            if not translation:
                continue
            scoped_rows += 1
            for match in TOKEN_RE.finditer(translation):
                token = match.group(0)
                low = token.lower()
                if not is_token_candidate(low):
                    continue
                if skip_archaic_headword(translation, match.end()):
                    continue
                counts[low] += 1
                samples.setdefault(
                    low,
                    {
                        "token": low,
                        "count": 0,
                        "record_id": row.get("record_id"),
                        "source": source,
                        "lemma": row.get("Texto estandarizado"),
                        "field": "Traducción (es)" if source == "2021 Wimmer" else "Traducción",
                        "translation": translation,
                    },
                )

    with TOKENS_PATH.open("w", encoding="utf-8") as fh:
        for token, _count in counts.most_common():
            fh.write(token + "\n")

    with SAMPLES_PATH.open("w", encoding="utf-8") as fh:
        for token, count in counts.most_common():
            item = dict(samples[token])
            item["count"] = count
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    with SUMMARY_PATH.open("w", encoding="utf-8") as fh:
        fh.write("Broad Spanish spellcheck inventory\n")
        fh.write("scope=Traducción for non-Wimmer, Traducción (es) for 2021 Wimmer, excluding 1992 Karttunen\n")
        fh.write(f"scoped_rows={scoped_rows}\n")
        fh.write(f"candidate_tokens={len(counts)}\n")
        fh.write(f"candidate_occurrences={sum(counts.values())}\n\n")
        for token, count in counts.most_common(500):
            sample = samples[token]
            fh.write(
                f"{token}\t{count}\t{sample['source']}\t{sample['lemma']}\t"
                f"{str(sample['translation'])[:180]}\n"
            )

    print(f"tokens={TOKENS_PATH}")
    print(f"samples={SAMPLES_PATH}")
    print(f"summary={SUMMARY_PATH}")
    print(f"scoped_rows={scoped_rows}")
    print(f"candidate_tokens={len(counts)}")
    print(f"candidate_occurrences={sum(counts.values())}")


if __name__ == "__main__":
    main()
