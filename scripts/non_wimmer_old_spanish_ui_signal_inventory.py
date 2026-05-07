#!/usr/bin/env python3
from __future__ import annotations

import collections
import gzip
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_ui_signal_inventory.jsonl"
SUMMARY_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_ui_signal_inventory_summary.txt"


TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")


def normalize_old_spanish_like_ui(value: str) -> str:
    return (
        value.replace("ph", "f")
        .replace("th", "t")
        .replace("qu", "c")
        .replace("nn", "n")
        .replace("ss", "s")
        .replace("v", "b")
    )


def signal_reasons(token: str) -> list[str]:
    low = token.lower()
    reasons = []
    if "ph" in low:
        reasons.append("ph_to_f")
    if "th" in low:
        reasons.append("th_to_t")
    if "qu" in low:
        reasons.append("qu_to_c")
    if "nn" in low:
        reasons.append("nn_to_n")
    if "ss" in low:
        reasons.append("ss_to_s")
    if "v" in low:
        reasons.append("v_to_b")
    return reasons


def main() -> None:
    token_counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    source_counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    samples: dict[str, dict[str, object]] = {}

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            source = row.get("Fuente") or ""
            if source == "2021 Wimmer":
                continue
            text = row.get("Traducción") or ""
            for match in TOKEN_RE.finditer(text):
                token = match.group(0)
                low = token.lower()
                normalized = normalize_old_spanish_like_ui(low)
                if normalized == low:
                    continue
                reasons = signal_reasons(low)
                for reason in reasons:
                    token_counts[reason][low] += 1
                    source_counts[reason][source] += 1
                samples.setdefault(
                    low,
                    {
                        "token": low,
                        "ui_old_spanish": normalized,
                        "reasons": reasons,
                        "record_id": row.get("record_id"),
                        "source": source,
                        "lemma": row.get("Texto estandarizado"),
                        "translation": text,
                    },
                )

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for token, sample in sorted(samples.items()):
            sample = dict(sample)
            sample["count"] = sum(token_counts[reason][token] for reason in sample["reasons"])
            fh.write(json.dumps(sample, ensure_ascii=False) + "\n")

    with SUMMARY_PATH.open("w", encoding="utf-8") as fh:
        fh.write("Non-Wimmer old-Spanish UI-signal inventory for Traducción\n\n")
        for reason, counter in sorted(token_counts.items()):
            fh.write(f"## {reason}\n")
            fh.write(f"unique={len(counter)} total={sum(counter.values())}\n")
            fh.write("sources=" + json.dumps(source_counts[reason].most_common(12), ensure_ascii=False) + "\n")
            for token, count in counter.most_common(80):
                fh.write(f"{token}\t{count}\n")
            fh.write("\n")

    print(f"report={REPORT_PATH}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
