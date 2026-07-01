#!/usr/bin/env python3
"""Clean visible inline bracket residue in 1579 Duran prose."""

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
PROPOSALS_PATH = Path("resources/duran_1579_inline_bracket_proposals.tsv")
SUMMARY_PATH = Path("resources/duran_1579_inline_bracket_summary.json")
SOURCE = "1579 Durán"
RAW_FIELD = "Comentario_raw_1579_duran"
MARKER = "visible_1579_duran_inline_bracket_cleanup_2026_06_29"
QA_KEY = "qa_1579_duran_inline_bracket_cleanup"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
PROTECTED_RE = re.compile(r"(<(?:b|small)\b[^>]*>.*?</(?:b|small)>)", re.I | re.S)
BRACKET_RE = re.compile(r"\[([^\[\]]+)\]")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
WORD_EDGE_RE = re.compile(r"[\wÁÉÍÓÚÜÑáéíóúüñ]", re.U)
CROSS_TAG_REPLACEMENTS = {
    "[Del cruel sacrificio que los tlaxcaltecas hicieron en la fiesta de la diosa <b>Toci</b>, y de cómo los huexotzincas enojados al saberlo, quemaron de noche el templo de aquella diosa]": (
        "Del cruel sacrificio que los tlaxcaltecas hicieron en la fiesta de la diosa <b>Toci</b>, "
        "y de cómo los huexotzincas enojados al saberlo, quemaron de noche el templo de aquella diosa"
    ),
}
CROSS_TAG_ITEMS = sorted(CROSS_TAG_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True)


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


def is_word_char(char: str) -> bool:
    return bool(char and WORD_EDGE_RE.fullmatch(char))


def replacement_for_match(piece: str, match: re.Match[str]) -> str:
    inner = match.group(1).strip()
    before = piece[match.start() - 1] if match.start() else ""
    after = piece[match.end()] if match.end() < len(piece) else ""
    compact_insert = " " not in inner and len(inner) <= 3 and (is_word_char(before) or is_word_char(after))

    prefix = ""
    suffix = ""
    if not compact_insert and is_word_char(before) and is_word_char(inner[:1]):
        prefix = " "
    if not compact_insert and is_word_char(after) and is_word_char(inner[-1:]):
        suffix = " "
    return f"{prefix}{inner}{suffix}"


def normalize_piece(piece: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        old = match.group(0)
        new = replacement_for_match(piece, match)
        changes.append((old, new))
        return new

    return BRACKET_RE.sub(repl, piece), changes


def normalize_visible_prose(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    pieces: list[str] = []
    changes: list[tuple[str, str]] = []

    for old, new in CROSS_TAG_ITEMS:
        count = text.count(old)
        if not count:
            continue
        text = text.replace(old, new)
        changes.extend((old, new) for _ in range(count))

    last = 0

    for match in PROTECTED_RE.finditer(text):
        piece, piece_changes = normalize_piece(text[last : match.start()])
        pieces.append(piece)
        pieces.append(match.group(0))
        changes.extend(piece_changes)
        last = match.end()
    piece, piece_changes = normalize_piece(text[last:])
    pieces.append(piece)
    changes.extend(piece_changes)
    return "".join(pieces), changes


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
        previous_commentary = row.get(RAW_FIELD, row.get("Comentario", ""))
        for field in COMMENTARY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_visible_prose(value)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if args.apply:
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
                "context": token_context(row.get("Comentario", ""), row_changes[0][1]),
            }
        )
        if args.apply:
            if RAW_FIELD not in row:
                row[RAW_FIELD] = previous_commentary
                counts["raw_preserved_rows"] += 1
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                QA_KEY: {
                    "action": "cleaned_visible_inline_brackets_outside_small_and_bold",
                    "marker": MARKER,
                    "raw_field": RAW_FIELD,
                    "raw_preserved": True,
                    "changed_token_count": len(row_changes),
                    "previous_commentary_sha1": hashlib.sha1(str(row.get(RAW_FIELD, "")).encode("utf-8")).hexdigest(),
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
