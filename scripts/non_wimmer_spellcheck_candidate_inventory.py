#!/usr/bin/env python3
from __future__ import annotations

import collections
import gzip
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
TOKENS_PATH = ROOT / "scripts" / "non_wimmer_spellcheck_candidate_tokens.txt"
SAMPLES_PATH = ROOT / "scripts" / "non_wimmer_spellcheck_candidate_samples.jsonl"
SUMMARY_PATH = ROOT / "scripts" / "non_wimmer_spellcheck_candidate_summary.txt"


SKIP_SOURCES = {"2021 Wimmer", "1992 Karttunen", "1580 CF Index", "V94 Diccionario Global SNP"}
TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç]+")
ANNOTATION_RE = re.compile(r"\((?:arcaico|latín):[^)]*\)", re.I)
SPANISHISH_RE = re.compile(
    r"("
    r"z[eiéí]|"
    r"^v[^aeiouáéíóúü]|"
    r"^([aeo]?[mn]?b|conb|enb)|"
    r"^([aeo]?h?yer|[eo]mbr|[eo]nr|[eo]rm|[eo]red|[eo]ri)|"
    r"(bolu|uien|uier|uirt|uir|uiv|uiz|uad|uaz|silua|llub)|"
    r"(lebant|lleb|biud|serb|sirb|salb|perb|bax)|"
    r"^(ia|ie|iu|io)[a-záéíóúüñç]+"
    r")",
    re.I,
)


def is_candidate(token: str) -> bool:
    low = token.lower()
    if len(low) < 4:
        return False
    if low in {"vt", "vr", "vbo", "vb"}:
        return False
    if SPANISHISH_RE.search(low):
        return True
    return False


def annotation_spans(text: str) -> list[tuple[int, int]]:
    return [match.span() for match in ANNOTATION_RE.finditer(text)]


def is_intentional_annotation_token(text: str, start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    for span_start, span_end in spans:
        if span_start <= start < span_end:
            return True
        if end <= span_start:
            between = text[end:span_start]
            if not re.search(r"[.!?/]", between):
                return True
    return False


def main() -> None:
    counts: collections.Counter[str] = collections.Counter()
    samples: dict[str, dict[str, object]] = {}

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            source = row.get("Fuente") or ""
            if source in SKIP_SOURCES:
                continue
            translation = row.get("Traducción") or ""
            spans = annotation_spans(translation)
            for match in TOKEN_RE.finditer(translation):
                token = match.group(0)
                low = token.lower()
                if not is_candidate(token):
                    continue
                if is_intentional_annotation_token(translation, match.start(), match.end(), spans):
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
        fh.write(f"candidate_tokens={len(counts)}\n")
        fh.write(f"candidate_occurrences={sum(counts.values())}\n\n")
        for token, count in counts.most_common(300):
            sample = samples[token]
            fh.write(
                f"{token}\t{count}\t{sample['source']}\t"
                f"{sample['lemma']}\t{str(sample['translation'])[:160]}\n"
            )

    print(f"tokens={TOKENS_PATH}")
    print(f"samples={SAMPLES_PATH}")
    print(f"summary={SUMMARY_PATH}")
    print(f"candidate_tokens={len(counts)}")
    print(f"candidate_occurrences={sum(counts.values())}")


if __name__ == "__main__":
    main()
