#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLES_PATH = ROOT / "scripts" / "non_wimmer_spellcheck_candidate_samples.jsonl"
SUGGESTIONS_PATH = ROOT / "scripts" / "non_wimmer_spellcheck_suggestions.jsonl"
REVIEW_PATH = ROOT / "scripts" / "non_wimmer_spellcheck_suggestion_review.tsv"


def fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def relation(token: str, guess: str) -> str:
    t = fold(token)
    g = fold(guess)
    compact_g = g.replace(" ", "")
    if t == g:
        return "accent-only"
    if t == compact_g and " " in g:
        return "spacing-only"
    if f"h{t}" == g:
        return "missing-initial-h"
    if t.replace("b", "v") == g or t.replace("v", "b") == g:
        return "b-v"
    if t.replace("u", "v") == g or t.replace("v", "u") == g:
        return "u-v"
    if t.replace("z", "c") == g or t.replace("z", "s") == g:
        return "z-c-s"
    if t.replace("qu", "cu") == g or t.replace("qua", "cua") == g:
        return "qu-cu"
    if re.sub(r"([aeiou])y", r"\1i", t) == g:
        return "y-i"
    return "other"


def main() -> None:
    samples: dict[str, dict[str, object]] = {}
    with SAMPLES_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            samples[item["token"]] = item

    rows: list[dict[str, object]] = []
    with SUGGESTIONS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            token = item["token"]
            guesses = item.get("guesses") or []
            guess = guesses[0] if guesses else ""
            sample = samples.get(token, {})
            rows.append(
                {
                    "token": token,
                    "guess": guess,
                    "relation": relation(token, guess) if guess else "no-guess",
                    "count": int(sample.get("count") or 0),
                    "source": sample.get("source") or "",
                    "lemma": sample.get("lemma") or "",
                    "translation": sample.get("translation") or "",
                    "guesses": ", ".join(guesses[:5]),
                }
            )

    priority = {
        "missing-initial-h": 0,
        "b-v": 1,
        "u-v": 2,
        "z-c-s": 3,
        "qu-cu": 4,
        "accent-only": 5,
        "spacing-only": 6,
        "y-i": 7,
        "other": 8,
        "no-guess": 9,
    }
    rows.sort(key=lambda r: (priority.get(str(r["relation"]), 99), -int(r["count"]), str(r["token"])))

    with REVIEW_PATH.open("w", encoding="utf-8") as fh:
        fh.write("relation\ttoken\tguess\tcount\tsource\tlemma\ttranslation\tguesses\n")
        for row in rows:
            values = [
                str(row["relation"]),
                str(row["token"]),
                str(row["guess"]),
                str(row["count"]),
                str(row["source"]),
                str(row["lemma"]),
                str(row["translation"]).replace("\t", " ").replace("\n", " ")[:260],
                str(row["guesses"]),
            ]
            fh.write("\t".join(values) + "\n")

    print(f"review={REVIEW_PATH}")
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
