#!/usr/bin/env python3
"""Normalize narrow old-Spanish residue in 1611 Arenas public display."""

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
PROPOSALS_PATH = Path("resources/arenas_1611_oldspanish_proposals.tsv")
SUMMARY_PATH = Path("resources/arenas_1611_oldspanish_summary.json")
SOURCE = "1611 Arenas"
MARKER = "visible_spanish_1611_arenas_oldwriting_2026_06_29"
QA_KEY = "qa_1611_arenas_oldwriting"

PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELDS = {
    "Traducción": "Traducción_raw_1611_arenas_oldwriting",
    "Traducción (es)": "Traducción_es_raw_1611_arenas_oldwriting",
    "Comentario": "Comentario_raw_1611_arenas_oldwriting",
    "Comentario (es)": "Comentario_es_raw_1611_arenas_oldwriting",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_1611_arenas_oldwriting",
}

BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
TOKEN_CHARS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùÇç"
EXACT_REPLACEMENTS: dict[str, str] = {
    "aviendole": "habiéndole",
    "averse": "haberse",
    "azeyte": "aceite",
    "azia": "hacia",
    "baylar": "bailar",
    "cavallo": "caballo",
    "com?mente": "comúnmente",
    "deffectos": "defectos",
    "diffuntos": "difuntos",
    "devocion": "devoción",
    "emprestado": "prestado",
    "HAZIENDA": "HACIENDA",
    "mercaderias": "mercaderías",
    "Missa": "Misa",
    "missa": "misa",
    "Murmurã": "Murmuran",
    "officio": "oficio",
    "offrecen": "ofrecen",
    "offrecer": "ofrecer",
    "offrecimiento": "ofrecimiento",
    "official": "oficial",
    "oyr": "oír",
    "plazer": "placer",
    "priessa": "prisa",
    "quexandose": "quejándose",
    "rezio": "recio",
    "vella": "verla",
    "vozes": "voces",
}
REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(rf"(?<![{TOKEN_CHARS}])ô(?![{TOKEN_CHARS}])"), "o"),
    (re.compile(rf"(?<![{TOKEN_CHARS}])ó(?![{TOKEN_CHARS}])"), "o"),
    *[
        (re.compile(rf"(?<![{TOKEN_CHARS}]){re.escape(old)}(?![{TOKEN_CHARS}])", re.I), new)
        for old, new in sorted(EXACT_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True)
    ],
]


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: object, token: str, width: int = 140) -> str:
    text = clean_html(value)
    index = text.find(token)
    if index < 0:
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


def apply_case(old: str, new: str) -> str:
    letters = re.sub(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", "", old)
    if letters.isupper():
        return new.upper()
    if old[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def normalize_text(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str]] = []
    for pattern, replacement in REPLACEMENTS:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            new = apply_case(old, replacement)
            changes.append((old, new))
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
        if row.get("Fuente") != SOURCE:
            continue
        counts["source_rows"] += 1

        row_changes: list[tuple[str, str, str]] = []
        raw_preserved_fields: list[str] = []
        for field in PUBLIC_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_text(value)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if args.apply:
                raw_field = RAW_FIELDS[field]
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
                "record_id": row.get("record_id", ""),
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "marker": MARKER,
                "old_tokens": " | ".join(f"{field}:{old}" for field, old, _ in row_changes),
                "new_tokens": " | ".join(f"{field}:{new}" for field, _, new in row_changes),
                "context": token_context(row.get(row_changes[0][0], ""), row_changes[0][1]),
            }
        )

        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                QA_KEY: {
                    "action": "normalized_standalone_old_spanish_o_and_hazienda_in_public_display_fields",
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
        ["record_id", "original", "editado", "marker", "old_tokens", "new_tokens", "context"],
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
