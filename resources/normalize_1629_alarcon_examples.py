#!/usr/bin/env python3
"""Normalize safe visible Nahuatl example spelling in 1629 Alarcon.

Alarcon rows are mostly bold Nahuatl ritual/conjure texts followed by Spanish
explanation. This pass rewrites only the bold Nahuatl side:

* ``ç/Ç`` -> ``z/Z``
* ``qu-/Qu-`` before ``a/o`` -> ``cu-/Cu-``
* initial ``y/Y`` before a consonant -> ``i/I``

Initial ``h`` remains review-only because the source uses it in forms that need
more lexical context, except the source-attested bracketed spelling
``[c]hichimècatl`` -> ``chichimecatl``.
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
PROPOSALS_PATH = Path("resources/alarcon_1629_example_normalization_proposals.tsv")
REVIEW_PATH = Path("resources/alarcon_1629_example_normalization_review.tsv")
SUMMARY_PATH = Path("resources/alarcon_1629_example_normalization_summary.json")
SOURCE = "1629 Alarcón"
RAW_FIELD = "Comentario_raw_1629_alarcon"
CEDILLA_MARKER = "visible_bold_nahuatl_1629_cedilla_to_z_2026_06_29"
QU_MARKER = "visible_bold_nahuatl_1629_qu_before_ao_to_cu_2026_06_29"
INITIAL_Y_MARKER = "visible_bold_nahuatl_1629_initial_y_before_consonant_to_i_2026_06_29"
SOURCE_TERM_MAP_MARKER = "visible_bold_nahuatl_1629_source_term_map_2026_06_29"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]

BOLD_RE = re.compile(r"(<b\b[^>]*>)(.*?)(</b>)", re.I | re.S)
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TOKEN_CHARS = "A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùÇç\\[\\]"
WORD_RE = re.compile(rf"[{TOKEN_CHARS}]+")
QU_BEFORE_AO_RE = re.compile(r"[Qq][Uu](?=[aAoOāĀōŌáÁóÓâÂôÔàÀòÒ])")
CEDILLA_TOKEN_RE = re.compile(rf"[{TOKEN_CHARS}]*[Çç][{TOKEN_CHARS}]*")
INITIAL_Y_BEFORE_CONSONANT_RE = re.compile(r"^[Yy](?=[bcdfghjklmnpqrstvwxyzçÇ])")
DIACRITIC_TRANS = str.maketrans(
    "ÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùÇç",
    "AEIOUUNaeiouunAEIOaeioAEIOaeioAEIOUaeiouCc",
)
SPANISH_TOKEN_DENY = {
    "cuando",
    "cuanto",
    "cuantos",
    "cuatro",
    "quatro",
    "quarenta",
    "quarto",
    "quinientos",
    "quince",
}
NAHUATL_TOKEN_HINTS = (
    "tl",
    "tz",
    "hu",
    "auh",
    "hua",
    "tzin",
    "xoch",
    "atl",
    "tepec",
    "tlan",
    "cal",
    "cuauh",
    "quauh",
    "coatl",
    "cihua",
    "tlamacaz",
    "yoll",
    "tlaç",
    "coça",
    "çan",
    "maç",
    "qua",
    "iqua",
)

SOURCE_TERM_REPLACEMENTS = {
    "chalchicueve": "chalchicueye",
    "[c]hichimècatl": "chichimecatl",
    "chichimècatl": "chichimecatl",
    "tlejn": "tlein",
    "vn teteo tlamacazque": "in teteo tlamacazque",
    "vel": "huel",
}

REVIEW_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "cedilla",
        re.compile(r"[A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô]*[Çç][A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô]*"),
        "review cedilla not handled by the safe pass",
    ),
    (
        "qu_before_a_o",
        re.compile(r"\bqu[aoāōáóâô][A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô\[\]]*", re.I),
        "review qu before a/o not handled by the safe pass",
    ),
    (
        "initial_y_before_consonant",
        re.compile(r"\by[bcdfghjklmnpqrstvwxyzç][A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùç]*", re.I),
        "review old initial y used for i before consonant",
    ),
    (
        "initial_h_before_aeio",
        re.compile(
            r"(?<![A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù])h[aeioáéíóāēīōâêîôàèìò]"
            r"[A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù\[\]]*",
            re.I,
        ),
        "review initial h before a/e/i/o in Alarcon examples",
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


def token_key(token: str) -> str:
    return token.translate(DIACRITIC_TRANS).lower().replace("[", "").replace("]", "")


def looks_nahuatl_token(token: str) -> bool:
    key = token_key(token)
    if len(key) < 3 or key in {item.translate(DIACRITIC_TRANS).lower() for item in SPANISH_TOKEN_DENY}:
        return False
    if key.startswith(("qua", "quo")):
        return True
    return any(hint.translate(DIACRITIC_TRANS).lower() in key for hint in NAHUATL_TOKEN_HINTS)


def normalize_cedilla_in_text(value: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            new = old.replace("ç", "z").replace("Ç", "Z")
            if old != new:
                changes.append((old, new))
            return new

        return CEDILLA_TOKEN_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def qu_to_cu(token: str) -> str:
    def repl(match: re.Match[str]) -> str:
        old = match.group(0)
        if old == "QU":
            return "CU"
        if old == "Qu":
            return "Cu"
        return "cu"

    return QU_BEFORE_AO_RE.sub(repl, token)


def apply_case_pattern(old: str, new: str) -> str:
    if old.isupper():
        return new.upper()
    if old[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def normalize_source_terms_in_text(value: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []
    terms = sorted((re.escape(term) for term in SOURCE_TERM_REPLACEMENTS), key=len, reverse=True)
    pattern = re.compile(rf"(?<![{TOKEN_CHARS}])({'|'.join(terms)})(?![{TOKEN_CHARS}])", re.I)

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(1)
            replacement = SOURCE_TERM_REPLACEMENTS.get(old.lower())
            if not replacement:
                return old
            new = apply_case_pattern(old, replacement)
            if old != new:
                changes.append((old, new))
            return new

        return pattern.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_qu_before_ao_in_text(value: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            if "v" in old.lower() or not QU_BEFORE_AO_RE.search(old) or not looks_nahuatl_token(old):
                return old
            new = qu_to_cu(old)
            if old != new:
                changes.append((old, new))
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_initial_y_before_consonant_in_text(value: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            if not INITIAL_Y_BEFORE_CONSONANT_RE.search(old):
                return old
            new = ("I" if old[0].isupper() else "i") + old[1:]
            if old != new:
                changes.append((old, new))
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold(value: object) -> tuple[str, list[tuple[str, str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner, cedilla_changes = normalize_cedilla_in_text(match.group(2))
        inner, qu_changes = normalize_qu_before_ao_in_text(inner)
        inner, initial_y_changes = normalize_initial_y_before_consonant_in_text(inner)
        inner, source_term_changes = normalize_source_terms_in_text(inner)
        all_changes.extend((CEDILLA_MARKER, old, new) for old, new in cedilla_changes)
        all_changes.extend((QU_MARKER, old, new) for old, new in qu_changes)
        all_changes.extend((INITIAL_Y_MARKER, old, new) for old, new in initial_y_changes)
        all_changes.extend((SOURCE_TERM_MAP_MARKER, old, new) for old, new in source_term_changes)
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
                    if not looks_nahuatl_token(token):
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
            new_value, changes = normalize_bold(value)
            if new_value == value:
                continue
            for marker, old, new in changes:
                row_changes.append((field, marker, old, new))
            if args.apply:
                row[field] = new_value

        if row_changes:
            counts["proposal_rows"] += 1
            counts["proposal_changes"] += len(row_changes)
            counts["proposal_changes_cedilla"] += sum(1 for _, marker, _, _ in row_changes if marker == CEDILLA_MARKER)
            counts["proposal_changes_qu_before_ao"] += sum(1 for _, marker, _, _ in row_changes if marker == QU_MARKER)
            counts["proposal_changes_initial_y_before_consonant"] += sum(
                1 for _, marker, _, _ in row_changes if marker == INITIAL_Y_MARKER
            )
            counts["proposal_changes_source_term_map"] += sum(
                1 for _, marker, _, _ in row_changes if marker == SOURCE_TERM_MAP_MARKER
            )
            proposals.append(
                {
                    "record_id": row.get("record_id", ""),
                    "original": row.get("Original", ""),
                    "editado": row.get("Editado", ""),
                    "markers": ";".join(dict.fromkeys(marker for _, marker, _, _ in row_changes)),
                    "old_tokens": " | ".join(f"{field}:{old}" for field, _, old, _ in row_changes),
                    "new_tokens": " | ".join(f"{field}:{new}" for field, _, _, new in row_changes),
                    "context": token_context(row.get("Comentario", ""), row_changes[0][2]),
                }
            )
            if args.apply:
                for marker in dict.fromkeys(marker for _, marker, _, _ in row_changes):
                    row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), marker)
                    row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), marker)
                qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
                if any(marker == CEDILLA_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1629_alarcon_cedilla_to_z": {
                            "action": "normalized_cedilla_to_z_inside_bold_nahuatl_examples",
                            "marker": CEDILLA_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(1 for _, marker, _, _ in row_changes if marker == CEDILLA_MARKER),
                            "previous_commentary_sha1": hashlib.sha1(str(row.get(RAW_FIELD, "")).encode("utf-8")).hexdigest(),
                        },
                    }
                if any(marker == QU_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1629_alarcon_qu_before_ao_to_cu": {
                            "action": "normalized_qu_before_a_o_to_cu_inside_bold_nahuatl_examples",
                            "marker": QU_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(1 for _, marker, _, _ in row_changes if marker == QU_MARKER),
                            "previous_commentary_sha1": hashlib.sha1(str(row.get(RAW_FIELD, "")).encode("utf-8")).hexdigest(),
                        },
                    }
                if any(marker == INITIAL_Y_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1629_alarcon_initial_y_before_consonant_to_i": {
                            "action": "normalized_initial_y_before_consonant_to_i_inside_bold_nahuatl_examples",
                            "marker": INITIAL_Y_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == INITIAL_Y_MARKER
                            ),
                            "previous_commentary_sha1": hashlib.sha1(
                                str(row.get(RAW_FIELD, "")).encode("utf-8")
                            ).hexdigest(),
                        },
                    }
                if any(marker == SOURCE_TERM_MAP_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1629_alarcon_source_term_map": {
                            "action": "normalized_source_attested_bracketed_chichimecatl_spelling_inside_bold_examples",
                            "marker": SOURCE_TERM_MAP_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == SOURCE_TERM_MAP_MARKER
                            ),
                            "previous_commentary_sha1": hashlib.sha1(
                                str(row.get(RAW_FIELD, "")).encode("utf-8")
                            ).hexdigest(),
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
