#!/usr/bin/env python3
"""Normalize safe visible old spelling in 1547 Olmos_G examples.

Olmos_G commentary is largely Spanish grammar explanation with bold Nahuatl
examples. This pass rewrites only exact, source-checked tokens inside bold
spans and preserves the public commentary in a raw field before display edits.
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
PROPOSALS_PATH = Path("resources/olmos_1547_example_normalization_proposals.tsv")
REVIEW_PATH = Path("resources/olmos_1547_example_normalization_review.tsv")
SUMMARY_PATH = Path("resources/olmos_1547_example_normalization_summary.json")
SOURCE = "1547 Olmos_G"
RAW_FIELD = "Comentario_raw_1547_olmos_g"
SOURCE_TERM_MAP_MARKER = "visible_bold_nahuatl_1547_olmos_g_oldspell_map_2026_06_29"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
REVIEW_TOKEN_DENY = {"varro", "verdaderamente"}

BOLD_RE = re.compile(r"(<b\b[^>]*>)(.*?)(</b>)", re.I | re.S)
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TOKEN_CHARS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùÇç\\[\\]"
WORD_RE = re.compile(rf"[{TOKEN_CHARS}]+")

SOURCE_TERM_REPLACEMENTS = {
    "aço": "azo",
    "auc": "aoc",
    "aucmo": "aocmo",
    "auelh": "ahuel",
    "çan": "zan",
    "çaço": "zazo",
    "yc": "ic",
    "ycipa": "icipa",
    "yn": "in",
    "ynic": "inic",
    "ypan": "ipan",
    "yquin": "iquin",
    "ytic": "itic",
    "neçaualiztli": "nezahualiztli",
    "nitequitlaqua": "nitequitlacua",
    "nitlaquataçi": "nitlacuataci",
    "nitzinquiça": "nitzinquiza",
    "mochiuaz": "mochihuaz",
    "ticcauhtiquiçaz": "ticcauhtiquizaz",
    "tlaquauh": "tlacuauh",
    "uel": "huel",
    "uelh": "huel",
    "uelipan": "huelipan",
    "vel": "huel",
    "xitlaqua": "xitlacua",
    "xiualauh": "xihualauh",
}

REVIEW_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "cedilla",
        re.compile(r"\b[\wÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù]*[çÇ][\wÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù]*\b"),
        "review cedilla in bold Nahuatl example",
    ),
    (
        "qu_before_a_o",
        re.compile(r"\bqu[aoāōáóàòâô][\wÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù\[\]]*", re.I),
        "review qu before a/o in bold Nahuatl example",
    ),
    (
        "initial_y_before_consonant",
        re.compile(r"\by[bcdfghjklmnpqrstvwxyzç][\wÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùç]*\b", re.I),
        "review old y used for i before consonant",
    ),
    (
        "huel_without_h",
        re.compile(r"\buelh?\w*", re.I),
        "review old uel/huel spelling",
    ),
    (
        "v_likely_u",
        re.compile(r"\b[vV][aeiouāēīōáéíóúàèìòùâêîô]\w*|\w*[aeiouāēīōáéíóúàèìòùâêîô][vV][aeiouāēīōáéíóúàèìòùâêîô]\w*"),
        "review v/u historical spelling in bold text",
    ),
]


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


def apply_case_pattern(old: str, new: str) -> str:
    if old.isupper():
        return new.upper()
    if old[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def normalize_word(token: str) -> tuple[str, list[tuple[str, str, str]]]:
    replacement = SOURCE_TERM_REPLACEMENTS.get(token.lower())
    if not replacement:
        return token, []
    new = apply_case_pattern(token, replacement)
    if new == token:
        return token, []
    return new, [(SOURCE_TERM_MAP_MARKER, token, new)]


def normalize_text(value: str) -> tuple[str, list[tuple[str, str, str]]]:
    changes: list[tuple[str, str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            new, token_changes = normalize_word(old)
            changes.extend(token_changes)
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold(value: object) -> tuple[str, list[tuple[str, str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_text(match.group(2))
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def bold_texts(value: object) -> list[str]:
    return [clean_html(match.group(2)) for match in BOLD_RE.finditer(str(value or ""))]


def review_candidates(row: dict) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for field in COMMENTARY_FIELDS:
        value = row.get(field, "")
        if not isinstance(value, str) or not value:
            continue
        for bold in bold_texts(value):
            for kind, pattern, note in REVIEW_PATTERNS:
                for match in pattern.finditer(bold):
                    token = match.group(0)
                    if token.lower() in REVIEW_TOKEN_DENY:
                        continue
                    key = (field, kind, token)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(
                        {
                            "record_id": row.get("record_id", ""),
                            "original": row.get("Original", ""),
                            "editado": row.get("Editado", ""),
                            "field": field,
                            "candidate_kind": kind,
                            "token": token,
                            "note": note,
                            "bold_text": bold[:700],
                            "context": token_context(value, token),
                        }
                    )
    return out


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
    parser.add_argument("--review", type=Path, default=REVIEW_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    proposals: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        counts["source_rows"] += 1
        if args.apply and RAW_FIELD not in row:
            row[RAW_FIELD] = row.get("Comentario", "")
            counts["raw_preserved_rows"] += 1
        row_changes: list[tuple[str, str, str, str]] = []

        for field in COMMENTARY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, field_changes = normalize_bold(value)
            if new_value == value:
                continue
            for marker, old, new in field_changes:
                row_changes.append((field, marker, old, new))
            if args.apply:
                row[field] = new_value

        if row_changes:
            counts["proposal_rows"] += 1
            counts["proposal_changes"] += len(row_changes)
            old_tokens = []
            new_tokens = []
            change_markers = []
            for field, marker, old, new in row_changes:
                old_tokens.append(f"{field}:{old}")
                new_tokens.append(f"{field}:{new}")
                if marker not in change_markers:
                    change_markers.append(marker)
            proposals.append(
                {
                    "record_id": row.get("record_id", ""),
                    "original": row.get("Original", ""),
                    "editado": row.get("Editado", ""),
                    "markers": ";".join(change_markers),
                    "old_tokens": " | ".join(old_tokens),
                    "new_tokens": " | ".join(new_tokens),
                    "context": token_context(row.get("Comentario", ""), row_changes[0][2]),
                }
            )
            if args.apply:
                for marker in change_markers:
                    row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), marker)
                    row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), marker)
                qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
                changed_by_marker = Counter(marker for _, marker, _, _ in row_changes)
                qa = {
                    **qa,
                    "qa_1547_olmos_g_visible_bold_oldspell": {
                        "action": "normalized_visible_old_spellings_inside_bold_nahuatl_examples",
                        "markers": change_markers,
                        "raw_field": RAW_FIELD,
                        "raw_preserved": True,
                        "changed_token_count": len(row_changes),
                        "changed_by_marker": dict(changed_by_marker),
                        "previous_commentary_sha1": hashlib.sha1(str(row.get(RAW_FIELD, "")).encode("utf-8")).hexdigest(),
                    },
                }
                row["Sentence_Source_JSON"] = qa

        review.extend(review_candidates(row))

    write_tsv(
        args.proposals,
        proposals,
        ["record_id", "original", "editado", "markers", "old_tokens", "new_tokens", "context"],
    )
    write_tsv(
        args.review,
        review,
        ["record_id", "original", "editado", "field", "candidate_kind", "token", "note", "bold_text", "context"],
    )
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.apply and proposals:
        write_rows(args.data, rows)
        counts["applied_rows"] = len(proposals)
        args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"summary {dict(counts)}")
    print(f"proposals {args.proposals}")
    print(f"review {args.review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
