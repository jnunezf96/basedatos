#!/usr/bin/env python3
from __future__ import annotations

import collections
import gzip
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_inventory.jsonl"
SUMMARY_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_inventory_summary.txt"


PATTERNS = {
    "q_bracket": re.compile(r"q\[[^\]]+\]|q̃|q̄", re.I),
    "letter_bracket_in_word": re.compile(
        r"(?<=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])\[[a-z]{1,8}\](?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]|\W|$)"
    ),
    "cedilla": re.compile(r"ç"),
    "hazer_family": re.compile(
        r"\b(?:hazer|hazerse|haze|hazen|hazé|haziendo|hiz[oae]|hizieron)\b", re.I
    ),
    "dezir_family": re.compile(r"\b(?:dezir|dize|dizen|diziendo|dixo|dixe|dixer)\b", re.I),
    "assi_anssi": re.compile(r"\b(?:assi|anssi|assí|ansí)\b", re.I),
    "v_for_u_initial": re.compile(
        r"\b(?:vna|vno|vnos|vnas|vn|vsar|vso|vtil|vtilidad|vltimo|vniuersal|vniuersalmente)\b",
        re.I,
    ),
    "u_for_v": re.compile(
        r"\b(?:auer|auiendo|aui[aeo]|auia|auian|lleuar|leuantar|boluer|boluia|boluio|prouecho|prouar|graue|nueuo)\b",
        re.I,
    ),
    "x_for_j": re.compile(
        r"\b(?:dexar|dexa|dexo|traxo|texer|texido|texida|mexor|abaxo|debaxo|exemplo|exercicio)\b",
        re.I,
    ),
    "old_grave_or_circumflex": re.compile(r"[àèìòùâêîôû]"),
    "latin_vel": re.compile(r"\bvel\.?\b", re.I),
    "latin_scil": re.compile(r"\bscil\.?\b", re.I),
    "amp_c": re.compile(r"&c[.;]?", re.I),
    "preterite_abbrev": re.compile(r"\b(?:pre|pret|prete|preterito|pret[eé]rito|p)\s*:", re.I),
}


def main() -> None:
    source_counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    samples: list[dict[str, object]] = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            source = row.get("Fuente") or ""
            if source == "2021 Wimmer":
                continue
            text = row.get("Traducción") or ""
            hit_names = [name for name, pattern in PATTERNS.items() if pattern.search(text)]
            if not hit_names:
                continue
            for name in hit_names:
                source_counts[source][name] += 1
            samples.append(
                {
                    "record_id": row.get("record_id"),
                    "source": source,
                    "lemma": row.get("Texto estandarizado"),
                    "patterns": hit_names,
                    "translation": text,
                }
            )

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in samples:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    with SUMMARY_PATH.open("w", encoding="utf-8") as fh:
        fh.write("Non-Wimmer old-Spanish inventory for Traducción\n")
        fh.write(f"rows_with_hits={len(samples)}\n\n")
        for source, counter in sorted(
            source_counts.items(), key=lambda item: (-sum(item[1].values()), item[0])
        ):
            fh.write(f"{source}\t{sum(counter.values())}\t{dict(counter)}\n")

    print(f"rows_with_hits={len(samples)}")
    print(f"report={REPORT_PATH}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
