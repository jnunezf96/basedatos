#!/usr/bin/env python3
"""Normalize exact old-Spanish tokens that occur inside source bold spans.

Most cleanup passes avoid bold spans because they usually contain Nahuatl. This
pass is deliberately narrower: source-specific Spanish tokens only, with word
boundaries, in public display fields.
"""

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
PROPOSALS_PATH = Path("resources/sentence_heavy_bold_oldspanish_proposals.tsv")
SUMMARY_PATH = Path("resources/sentence_heavy_bold_oldspanish_summary.json")

DISPLAY_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
MARKER = "visible_spanish_sentence_heavy_bold_oldwriting_2026_06_30"
QA_KEY = "qa_sentence_heavy_bold_oldwriting"

SOURCE_REPLACEMENTS: dict[str, dict[str, str]] = {
    "1551-95 Documentos nahuas de la Ciudad de México": {
        "PROPRIO": "PROPIO",
        "huve": "hube",
    },
    "1565 Sahagún Escolios": {
        "aluedrio": "albedrío",
        "auisada": "avisada",
        "auisadamente": "avisadamente",
        "biua": "viva",
        "biuidora": "vividora",
        "biuir": "vivir",
        "grandissimo": "grandísimo",
        "parescer": "parecer",
        "proprio": "propio",
        "recattadamente": "recatadamente",
        "vellaco": "bellaco",
        "vieia": "vieja",
        "yerua": "yerba",
    },
    "1571 Molina 2": {
        "contradezir": "contradecir",
        "dexe": "deje",
    },
    "1611 Arenas": {
        "nieue": "nieve",
        "PROPRIO": "PROPIO",
    },
    "1629 Alarcón": {
        "aduiertase": "adviértase",
        "SILUESTRES": "SILVESTRES",
    },
    "1645 Carochi": {
        "aguardeme": "aguárdeme",
        "concluie": "concluye",
        "cuyde": "cuide",
        "demonstratiuo": "demonstrativo",
        "frequentatiuo": "frecuentativo",
        "Imperatiuo": "Imperativo",
        "indicatiuo": "indicativo",
        "motiuo": "motivo",
        "negatiuo": "negativo",
        "Optatiuo": "Optativo",
        "relatiuo": "relativo",
        "substantiuo": "substantivo",
        "superlatiuo": "superlativo",
        "transitiuo": "transitivo",
        "vetatiuo": "vetativo",
    },
    "17?? Bnf_362bis": {
        "aguardeme": "aguárdeme",
        "dexe": "deje",
        "dexes": "dejes",
        "enquanto": "en cuanto",
        "exemplos": "ejemplos",
        "huviera": "hubiera",
        "proprios": "propios",
        "recien": "recién",
    },
}


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: object, token: str, width: int = 150) -> str:
    text = clean_html(value)
    match = re.search(re.escape(token), text, re.I)
    if not match:
        return text[: width * 2].strip()
    left = max(0, match.start() - width)
    right = min(len(text), match.end() + width)
    return text[left:right].strip()


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def raw_field_name(field: str, source: str) -> str:
    safe_source = (
        source.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("?", "x")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )
    safe_field = (
        field.replace("Traducción", "Traduccion")
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
    )
    return f"{safe_field}_raw_{safe_source}_bold_oldspanish"


def token_re(old: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![\w-]){re.escape(old)}(?![\w-])")


def normalize_text(value: object, replacements: dict[str, str]) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str]] = []
    for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = token_re(old)

        def repl(match: re.Match[str]) -> str:
            changes.append((match.group(0), new))
            return new

        text = pattern.sub(repl, text)
    return text, changes


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
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
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
        source = str(row.get("Fuente", ""))
        replacements = SOURCE_REPLACEMENTS.get(source)
        if not replacements:
            continue
        counts[f"source_rows:{source}"] += 1
        row_changes: list[tuple[str, str, str]] = []
        raw_preserved_fields: list[str] = []
        first_context_field = ""
        first_context_token = ""

        for field in DISPLAY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_text(value, replacements)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if not first_context_field:
                first_context_field = field
                first_context_token = changes[0][0]
            if args.apply:
                raw_field = raw_field_name(field, source)
                if raw_field not in row:
                    row[raw_field] = value
                    counts["raw_preserved_fields"] += 1
                if raw_field not in raw_preserved_fields:
                    raw_preserved_fields.append(raw_field)
                row[field] = new_value

        if not row_changes:
            continue

        counts["proposal_rows"] += 1
        counts["proposal_changes"] += len(row_changes)
        proposals.append(
            {
                "source": source,
                "record_id": row.get("record_id", ""),
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "marker": MARKER,
                "old_tokens": " | ".join(f"{field}:{old}" for field, old, _ in row_changes),
                "new_tokens": " | ".join(f"{field}:{new}" for field, _, new in row_changes),
                "context": token_context(row.get(first_context_field, ""), first_context_token),
            }
        )

        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                QA_KEY: {
                    "action": "normalized_exact_old_spanish_tokens_in_source_bold_spans",
                    "marker": MARKER,
                    "raw_fields_preserved": raw_preserved_fields,
                    "changed_token_count": len(row_changes),
                    "previous_public_field_sha1": hashlib.sha1(
                        "||".join(str(row.get(raw_field, "")) for raw_field in raw_preserved_fields).encode("utf-8")
                    ).hexdigest(),
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
