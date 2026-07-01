#!/usr/bin/env python3
"""Build a compact review pack for remaining source-cleanup decisions.

This is read-only. The queue is intentionally conservative, so this script
expands grouped residue such as "ç" into concrete word-level examples and
adds a recommendation note without modifying data.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
QUEUE_PATH = Path("resources/source_cleanup_decision_queue.tsv")
PACK_PATH = Path("resources/source_cleanup_review_pack.tsv")
SUMMARY_PATH = Path("resources/source_cleanup_review_pack_summary.json")

PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
WORD_WITH_CEDILLA_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç]*[Çç][A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç]*")
WORD_WITH_HAT_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîô]*[ÂÊÎÔâêîô][A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîô]*")

FIELDS = [
    "source",
    "triage",
    "pattern",
    "queue_token",
    "review_token",
    "decision",
    "replacement",
    "decision_notes",
    "candidate_replacement",
    "token_count",
    "record_ids",
    "fields",
    "recommendation",
    "confidence",
    "reason",
    "example_context",
]


def clean_text(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def context_for(value: object, token: str, width: int = 170) -> str:
    text = clean_text(value)
    match = re.search(re.escape(token), text, re.I)
    if not match:
        return text[: width * 2]
    left = max(0, match.start() - width)
    right = min(len(text), match.end() + width)
    return text[left:right]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def iter_rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def decision_key(row: dict[str, object]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("source", "")),
        str(row.get("triage", "")),
        str(row.get("pattern", "")),
        str(row.get("queue_token", "")),
        str(row.get("review_token", "")),
    )


def existing_decisions(path: Path) -> dict[tuple[str, str, str, str, str], dict[str, str]]:
    if not path.exists():
        return {}
    decisions: dict[tuple[str, str, str, str, str], dict[str, str]] = {}
    for row in read_tsv(path):
        decisions[decision_key(row)] = {
            "decision": row.get("decision", ""),
            "replacement": row.get("replacement", ""),
            "decision_notes": row.get("decision_notes", ""),
        }
    return decisions


def bracket_recommendation(row: dict[str, str]) -> tuple[str, str, str, str]:
    triage = row.get("triage", "")
    token = row.get("token", "")
    if triage == "preceding_correction_review" and token.startswith("[") and token.endswith("]"):
        return (
            "needs_user",
            "medium",
            "bracket appears to correct the preceding spelling; if accepted, replace the preceding word plus bracket with the corrected word",
            token[1:-1],
        )
    if triage == "inline_restoration_review":
        return "keep", "medium", "inline supplied-letter apparatus is meaningful unless the source policy changes", ""
    if token.startswith("[") and token.endswith("]"):
        return "needs_user", "low", "bracket may correct the preceding spelling, or may be an insertion, gloss, supplied text, or source note", token[1:-1]
    return "needs_user", "low", "group needs source-context review", ""


def mechanical_cedilla(token: str) -> str:
    out: list[str] = []
    for index, char in enumerate(token):
        if char not in "çÇ":
            out.append(char)
            continue
        next_char = token[index + 1 : index + 2].lower()
        replacement = "c" if next_char in {"e", "i"} else "z"
        out.append(replacement.upper() if char == "Ç" else replacement)
    return "".join(out)


def cedilla_recommendation(source: str, token: str) -> tuple[str, str, str, str]:
    mechanical = mechanical_cedilla(token)
    if source == "1547 Olmos_V ?":
        if token.lower() == "adeçetar":
            return (
                "needs_user",
                "low",
                "mechanical form would be adecetar; local Olmos has acezar elsewhere, but this entry is transitive with algo and the Nahuatl is tlachichina",
                mechanical,
            )
        return "needs_user", "low", f"mechanical form would be {mechanical}, but the Spanish lemma is uncertain", mechanical
    if source == "1598 Tezozomoc":
        if token.lower() == "cançe":
            return "needs_user", "low", "context suggests a possible OCR/source word like alcance, not a plain cedilla swap", mechanical
        if token.lower() == "amaneçese":
            return "needs_user", "medium", "could normalize cedilla, but the verbal form may be amaneciese", mechanical
        if token.lower() in {"espeçiba", "çado"}:
            return (
                "needs_user",
                "low",
                "mechanical form is not convincing; context suggests a possible expression/expressive reading, but no local corroboration was found",
                mechanical,
            )
    if source == "1629 Alarcón":
        if token.lower() == "alabançan":
            return (
                "needs_user",
                "low",
                "mechanical alabanzan is weak; context with 'a ellas' may point to abalanzan, but the source already marks uncertainty",
                mechanical,
            )
        if token.lower() == "caçegas":
            return (
                "needs_user",
                "low",
                "mechanical cacegas has no local corroboration and the Spanish word is unclear in context",
                mechanical,
            )
        return "needs_user", "low", f"mechanical form would be {mechanical}, but context points to possible OCR/source-word uncertainty", mechanical
    return "needs_user", "low", f"mechanical cedilla form would be {mechanical}; source-specific decision needed", mechanical


def hat_recommendation(token: str) -> tuple[str, str, str, str]:
    return (
        "needs_user",
        "low",
        "circumflex may mark long vowel, reduplication, or hidden n/m; this row is not safe to infer mechanically",
        "",
    )


def grouped_word_rows(queue_row: dict[str, str], rows_by_source: dict[str, list[dict]]) -> list[dict[str, object]]:
    source = queue_row["source"]
    pattern = queue_row["pattern"]
    regex = WORD_WITH_CEDILLA_RE if pattern == "cedilla" else WORD_WITH_HAT_RE
    grouped: dict[str, dict[str, object]] = {}
    for row in rows_by_source.get(source, []):
        for field in PUBLIC_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            for match in regex.finditer(clean_text(value)):
                token = match.group(0)
                if pattern == "hat_vowels" and not any(ch in token for ch in "âêîôÂÊÎÔ"):
                    continue
                item = grouped.setdefault(
                    token,
                    {
                        "source": source,
                        "triage": queue_row["triage"],
                        "pattern": pattern,
                        "queue_token": queue_row["token"],
                        "review_token": token,
                        "token_count": 0,
                        "record_ids": [],
                        "fields": [],
                        "example_context": "",
                    },
                )
                item["token_count"] = int(item["token_count"]) + 1
                if row.get("record_id") not in item["record_ids"]:
                    item["record_ids"].append(row.get("record_id", ""))
                if field not in item["fields"]:
                    item["fields"].append(field)
                if not item["example_context"]:
                    item["example_context"] = context_for(value, token)
    out: list[dict[str, object]] = []
    for token, item in sorted(grouped.items(), key=lambda entry: (-int(entry[1]["token_count"]), entry[0])):
        if pattern == "cedilla":
            recommendation, confidence, reason, candidate = cedilla_recommendation(source, token)
        else:
            recommendation, confidence, reason, candidate = hat_recommendation(token)
        item["record_ids"] = " | ".join(item["record_ids"][:5])
        item["fields"] = " | ".join(item["fields"])
        item["recommendation"] = recommendation
        item["confidence"] = confidence
        item["reason"] = reason
        item["candidate_replacement"] = candidate
        out.append(item)
    return out


def queue_rows(
    queue: list[dict[str, str]],
    rows_by_source: dict[str, list[dict]],
    preserved_decisions: dict[tuple[str, str, str, str, str], dict[str, str]],
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in queue:
        if row.get("decision") not in {"", "pending"}:
            continue
        if row.get("pattern") in {"cedilla", "hat_vowels"}:
            out.extend(grouped_word_rows(row, rows_by_source))
            continue
        recommendation, confidence, reason, candidate = bracket_recommendation(row)
        out.append(
            {
                "source": row.get("source", ""),
                "triage": row.get("triage", ""),
                "pattern": row.get("pattern", ""),
                "queue_token": row.get("token", ""),
                "review_token": row.get("token", ""),
                "candidate_replacement": candidate,
                "token_count": row.get("token_count", ""),
                "record_ids": row.get("example_record_ids", ""),
                "fields": row.get("example_fields", ""),
                "recommendation": recommendation,
                "confidence": confidence,
                "reason": reason,
                "example_context": row.get("example_context", ""),
            }
        )
    for row in out:
        preserved = preserved_decisions.get(decision_key(row), {})
        row["decision"] = preserved.get("decision", "pending")
        row["replacement"] = preserved.get("replacement", "")
        row["decision_notes"] = preserved.get("decision_notes", "")
    out.sort(key=lambda item: (item["recommendation"], item["source"], item["pattern"], item["review_token"]))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--queue", type=Path, default=QUEUE_PATH)
    parser.add_argument("--output", type=Path, default=PACK_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    queue = read_tsv(args.queue)
    sources = {row["source"] for row in queue}
    rows_by_source: dict[str, list[dict]] = defaultdict(list)
    for row in iter_rows(args.data):
        if row.get("Fuente") in sources:
            rows_by_source[row.get("Fuente", "")].append(row)

    preserved_decisions = existing_decisions(args.output)
    rows = queue_rows(queue, rows_by_source, preserved_decisions)
    write_tsv(args.output, rows)

    counts: Counter[str] = Counter()
    for row in rows:
        counts["review_rows"] += 1
        counts[f"recommendation:{row['recommendation']}"] += 1
        counts[f"triage:{row['triage']}"] += 1
        counts[f"source:{row['source']}"] += 1
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"review_pack {args.output} rows={len(rows)}")
    print(f"summary {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
