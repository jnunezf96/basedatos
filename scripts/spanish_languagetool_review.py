#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import non_wimmer_rla_lexicon_review as rla
import spanish_general_spellcheck_review as general_review


ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "scripts" / "spanish_languagetool_spellcheck.jsonl"
OUT_PATH = ROOT / "scripts" / "spanish_languagetool_review.tsv"
SUMMARY_PATH = ROOT / "scripts" / "spanish_languagetool_review_summary.txt"


def main() -> None:
    exact, accentless, _files = rla.load_lexicon()
    rows: list[dict[str, object]] = []

    with IN_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            token = str(item["token"])
            suggestions = [part.strip() for part in item.get("suggestions", []) if str(part).strip()]
            sample = {
                "count": item.get("count") or 0,
                "source": item.get("source") or "",
                "record_id": item.get("record_id") or "",
                "lemma": item.get("lemma") or "",
                "field": item.get("field") or "",
                "translation": item.get("translation") or "",
            }
            probe = {"token": token, "guesses": suggestions}
            guess = general_review.best_guess(probe)
            rel = general_review.relation(token, guess)
            bucket, reason = general_review.classify(probe, sample, exact, accentless)
            rows.append(
                {
                    "bucket": bucket,
                    "reason": reason,
                    "relation": rel,
                    "token": token,
                    "guess": guess,
                    "count": int(sample["count"]),
                    "source": sample["source"],
                    "record_id": sample["record_id"],
                    "lemma": sample["lemma"],
                    "field": sample["field"],
                    "translation": sample["translation"],
                    "guesses": ", ".join(suggestions[:12]),
                    "lt_rules": ", ".join(item.get("rules") or []),
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
            "lt_rules",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    bucket_counts = Counter(str(row["bucket"]) for row in rows)
    relation_counts = Counter(str(row["relation"]) for row in rows)
    with SUMMARY_PATH.open("w", encoding="utf-8") as fh:
        fh.write("LanguageTool review accounting\n")
        fh.write(f"rows={len(rows)}\n")
        fh.write(f"review={OUT_PATH}\n\n")
        fh.write("buckets\n")
        for key, value in bucket_counts.most_common():
            fh.write(f"{key}\t{value}\n")
        fh.write("\nrelations\n")
        for key, value in relation_counts.most_common():
            fh.write(f"{key}\t{value}\n")

    print(f"rows={len(rows)}")
    print(f"review={OUT_PATH}")
    print(f"summary={SUMMARY_PATH}")
    for key, value in bucket_counts.most_common():
        print(f"{key}\t{value}")


if __name__ == "__main__":
    main()
