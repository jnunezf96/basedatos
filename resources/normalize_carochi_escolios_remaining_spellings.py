#!/usr/bin/env python3
"""Apply exact remaining Carochi/Escolios visible spelling repairs."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import os
import re
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/carochi_escolios_remaining_spellings_proposals.tsv")
SUMMARY_PATH = Path("resources/carochi_escolios_remaining_spellings_summary.json")
COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
BOLD_RE = re.compile(r"(<b\b[^>]*>)(.*?)(</b>)", re.I | re.S)
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
TOKEN_BOUNDARY_CHARS = r"\wÀ-ÖØ-öø-ÿĀ-ž"

CONFIG = {
    "1645 Carochi": {
        "raw_field": "Comentario_raw_1645_carochi",
        "marker": "visible_bold_nahuatl_1645_carochi_remaining_exact_2026_06_29",
        "qa_key": "qa_1645_carochi_remaining_exact_spellings",
        "replacements": {
            "Cvel": "Cuel",
            "Hvècauh": "Huècauh",
            "Qventēl": "Quentēl",
            "Qvēn": "Quēn",
            "ivh": "iuh",
            "techquixtizq[u]è": "techquixtizque",
            "tlalhviz": "tlalhuiz",
            "vēuētl": "huēhuētl",
        },
        "token_replacements": {
            "Yyo": "Iyo",
            "ytechtzinco": "itechtzinco",
            "yn": "in",
        },
    },
    "1565 Sahagún Escolios": {
        "raw_field": "Comentario_raw_1565_sahagun_escolios",
        "marker": "visible_bold_nahuatl_1565_escolios_remaining_exact_2026_06_29",
        "qa_key": "qa_1565_escolios_remaining_exact_spellings",
        "replacements": {
            "aq[hue]quelli": "aquequelli",
            "aquetzq[hui]": "aquetzqui",
            "cemoq[hui]chtli": "cemoquichtli",
            "civatlampa": "cihuatlampa",
            "cualloq[hui]chtli": "cualloquichtli",
            "ixvacalihuizque": "ixhuacalihuizque",
            "movapaua": "mohuapahua",
            "quivalcentlami": "quihualcentlami",
            "quivallāncua": "quihuallāncua",
            "teahuilq[hui]xtia": "teahuilquixtia",
            "tecenvihuilanani": "tecenhuihuilanani",
            "tlanavalchiua": "tlanahualchihua",
            "tlaoq[hui]chuiani": "tlaoquichuiani",
            "tlapiq[hui]": "tlapiqui",
            "tlateq[hui]panoa": "tlatequipanoa",
            "yxquatolpopozauac": "ixcuatolpopozahuac",
        },
    },
}


def token_pattern(token: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![{TOKEN_BOUNDARY_CHARS}]){re.escape(token)}(?![{TOKEN_BOUNDARY_CHARS}])")


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: str, token: str, width: int = 140) -> str:
    text = clean_html(value)
    index = text.lower().find(token.lower())
    if index < 0:
        return text[: width * 2].strip()
    left = max(0, index - width)
    right = min(len(text), index + len(token) + width)
    return text[left:right].strip()


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def normalize_bold(
    value: object,
    replacements: dict[str, str],
    token_replacements: dict[str, str],
) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner = match.group(2)
        for old, new in replacements.items():
            count = inner.count(old)
            if count:
                changes.extend((old, new) for _ in range(count))
                inner = inner.replace(old, new)
        for old, new in token_replacements.items():
            inner, count = token_pattern(old).subn(new, inner)
            if count:
                changes.extend((old, new) for _ in range(count))
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), changes


def load_rows(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_rows(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as handle:
        for row in rows:
            json.dump(row, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
    os.replace(tmp, path)


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    proposals: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in rows:
        source = row.get("Fuente")
        config = CONFIG.get(source)
        if not config:
            continue
        counts[f"{source}:source_rows"] += 1
        raw_field = config["raw_field"]
        if args.apply and raw_field not in row:
            row[raw_field] = row.get("Comentario", "")
            counts[f"{source}:raw_preserved_rows"] += 1

        row_changes: list[tuple[str, str, str]] = []
        for field in COMMENTARY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_bold(
                value,
                config["replacements"],
                config.get("token_replacements", {}),
            )
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if args.apply:
                row[field] = new_value

        if not row_changes:
            continue

        marker = config["marker"]
        counts[f"{source}:proposal_rows"] += 1
        counts[f"{source}:proposal_changes"] += len(row_changes)
        proposals.append(
            {
                "source": source,
                "record_id": row.get("record_id", ""),
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "marker": marker,
                "old_tokens": " | ".join(f"{field}:{old}" for field, old, _ in row_changes),
                "new_tokens": " | ".join(f"{field}:{new}" for field, _, new in row_changes),
                "context": token_context(row.get("Comentario", ""), row_changes[0][1]),
            }
        )
        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), marker)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), marker)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                config["qa_key"]: {
                    "action": "normalized_remaining_exact_visible_spellings_inside_bold_examples",
                    "marker": marker,
                    "raw_field": raw_field,
                    "raw_preserved": True,
                    "changed_token_count": len(row_changes),
                    "previous_commentary_sha1": hashlib.sha1(str(row.get(raw_field, "")).encode("utf-8")).hexdigest(),
                },
            }
            row["Sentence_Source_JSON"] = qa

    write_tsv(
        args.proposals,
        proposals,
        ["source", "record_id", "original", "editado", "marker", "old_tokens", "new_tokens", "context"],
    )
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.apply and proposals:
        write_rows(args.data, rows)
        counts["applied_rows"] = len(proposals)
        args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"summary {dict(counts)}")
    print(f"proposals {args.proposals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
