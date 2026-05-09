#!/usr/bin/env python3
from __future__ import annotations

import bisect
import csv
import json
import subprocess
import sys
import argparse
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "tools" / "jre" / "jdk-21.0.11+10-jre" / "Contents" / "Home" / "bin" / "java"
LT_JAR = ROOT / "tools" / "languagetool" / "LanguageTool-6.6" / "languagetool-commandline.jar"

TOKENS_PATH = ROOT / "scripts" / "spanish_general_spellcheck_tokens.txt"
SAMPLES_PATH = ROOT / "scripts" / "spanish_general_spellcheck_samples.jsonl"
OUT_JSONL = ROOT / "scripts" / "spanish_languagetool_spellcheck.jsonl"
OUT_TSV = ROOT / "scripts" / "spanish_languagetool_spellcheck.tsv"
SUMMARY_PATH = ROOT / "scripts" / "spanish_languagetool_spellcheck_summary.txt"


def load_tokens() -> list[str]:
    with TOKENS_PATH.open(encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def load_samples() -> dict[str, dict[str, object]]:
    samples: dict[str, dict[str, object]] = {}
    with SAMPLES_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            samples[str(item["token"])] = item
    return samples


def parse_json_stdout(stdout: str) -> dict[str, object]:
    start = stdout.find("{")
    if start == -1:
        raise RuntimeError("LanguageTool did not emit JSON")
    return json.loads(stdout[start:])


def build_text(tokens: list[str]) -> tuple[str, list[int]]:
    starts: list[int] = []
    chunks: list[str] = []
    offset = 0
    for token in tokens:
        starts.append(offset)
        chunks.append(token)
        offset += len(token) + 1
    return "\n".join(chunks) + "\n", starts


def token_for_match(tokens: list[str], starts: list[int], offset: int) -> str | None:
    index = bisect.bisect_right(starts, offset) - 1
    if index < 0 or index >= len(tokens):
        return None
    token = tokens[index]
    if offset >= starts[index] + len(token):
        return None
    return token


def run_languagetool(text: str) -> dict[str, object]:
    if not JAVA.exists():
        raise FileNotFoundError(f"Missing Java runtime: {JAVA}")
    if not LT_JAR.exists():
        raise FileNotFoundError(f"Missing LanguageTool jar: {LT_JAR}")
    command = [
        str(JAVA),
        "-Xmx2g",
        "-jar",
        str(LT_JAR),
        "--json",
        "-b",
        "-l",
        "es",
        "-e",
        "MORFOLOGIK_RULE_ES",
        "-eo",
    ]
    result = subprocess.run(
        command,
        input=text,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    if result.returncode:
        sys.stderr.write(result.stderr)
        raise RuntimeError(f"LanguageTool exited with {result.returncode}")
    return parse_json_stdout(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=5000)
    args = parser.parse_args()

    tokens = load_tokens()
    samples = load_samples()

    by_token: dict[str, dict[str, object]] = {}
    rule_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()

    for start_index in range(0, len(tokens), args.batch_size):
        batch = tokens[start_index : start_index + args.batch_size]
        text, starts = build_text(batch)
        print(
            f"checking {start_index + 1}-{start_index + len(batch)} / {len(tokens)}",
            file=sys.stderr,
            flush=True,
        )
        result = run_languagetool(text)

        for match in result.get("matches", []):
            if not isinstance(match, dict):
                continue
            token = token_for_match(batch, starts, int(match.get("offset") or 0))
            if not token:
                continue
            rule = match.get("rule") if isinstance(match.get("rule"), dict) else {}
            category = rule.get("category") if isinstance(rule.get("category"), dict) else {}
            rule_id = str(rule.get("id") or "")
            category_id = str(category.get("id") or "")
            issue_type = str(rule.get("issueType") or "")
            rule_counts[rule_id] += 1
            category_counts[category_id] += 1
            issue_counts[issue_type] += 1
            replacements = [
                str(item.get("value"))
                for item in match.get("replacements", [])
                if isinstance(item, dict) and item.get("value")
            ]
            current = by_token.setdefault(
                token,
                {
                    "token": token,
                    "count": int(samples.get(token, {}).get("count") or 0),
                    "record_id": samples.get(token, {}).get("record_id") or "",
                    "source": samples.get(token, {}).get("source") or "",
                    "lemma": samples.get(token, {}).get("lemma") or "",
                    "field": samples.get(token, {}).get("field") or "",
                    "translation": samples.get(token, {}).get("translation") or "",
                    "rules": [],
                    "messages": [],
                    "suggestions": [],
                },
            )
            current["rules"].append(rule_id)
            current["messages"].append(str(match.get("message") or ""))
            current["suggestions"].extend(replacements[:8])

    rows = sorted(by_token.values(), key=lambda row: (-int(row["count"]), str(row["token"])))

    with OUT_JSONL.open("w", encoding="utf-8") as fh:
        for row in rows:
            row = dict(row)
            row["rules"] = sorted(set(row["rules"]))
            row["messages"] = sorted(set(row["messages"]))
            row["suggestions"] = list(dict.fromkeys(row["suggestions"]))[:12]
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    with OUT_TSV.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = [
            "token",
            "count",
            "suggestions",
            "rules",
            "source",
            "record_id",
            "lemma",
            "field",
            "translation",
            "messages",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "token": row["token"],
                    "count": row["count"],
                    "suggestions": ", ".join(list(dict.fromkeys(row["suggestions"]))[:12]),
                    "rules": ", ".join(sorted(set(row["rules"]))),
                    "source": row["source"],
                    "record_id": row["record_id"],
                    "lemma": row["lemma"],
                    "field": row["field"],
                    "translation": row["translation"],
                    "messages": " | ".join(sorted(set(row["messages"]))),
                }
            )

    with SUMMARY_PATH.open("w", encoding="utf-8") as fh:
        fh.write("LanguageTool Spanish spellcheck\n")
        fh.write("mode=MORFOLOGIK_RULE_ES only\n")
        fh.write(f"tokens_checked={len(tokens)}\n")
        fh.write(f"flagged_tokens={len(rows)}\n")
        fh.write(f"matches={sum(rule_counts.values())}\n")
        fh.write(f"jsonl={OUT_JSONL}\n")
        fh.write(f"tsv={OUT_TSV}\n\n")
        fh.write("rules\n")
        for key, value in rule_counts.most_common(30):
            fh.write(f"{key}\t{value}\n")
        fh.write("\ncategories\n")
        for key, value in category_counts.most_common(30):
            fh.write(f"{key}\t{value}\n")
        fh.write("\nissue_types\n")
        for key, value in issue_counts.most_common(30):
            fh.write(f"{key}\t{value}\n")

    print(f"tokens_checked={len(tokens)}")
    print(f"flagged_tokens={len(rows)}")
    print(f"matches={sum(rule_counts.values())}")
    print(f"jsonl={OUT_JSONL}")
    print(f"tsv={OUT_TSV}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
