#!/usr/bin/env python3
"""Normalize safe visible Nahuatl term spelling in 1598 Tezozomoc.

Tezozomoc commentary is Spanish chronicle prose with bold Nahuatl names and
terms. This pass rewrites only bold spans, preserving the public commentary in
a raw field before display changes.

The source's own Original/Editado pairs resolve many irregular old spellings,
so those exact single-token lexicon matches are preferred. Remaining safe
fallbacks are:

* ``ç/Ç`` -> ``c/C`` before e/i, otherwise ``z/Z``
* ``qu-/Qu-`` before a/o -> ``cu-/Cu-``
* initial ``y/Y`` before a consonant -> ``i/I``
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
PROPOSALS_PATH = Path("resources/tezozomoc_1598_term_normalization_proposals.tsv")
REVIEW_PATH = Path("resources/tezozomoc_1598_term_normalization_review.tsv")
SUMMARY_PATH = Path("resources/tezozomoc_1598_term_normalization_summary.json")
SOURCE = "1598 Tezozomoc"
RAW_FIELD = "Comentario_raw_1598_tezozomoc"
LEXICON_MARKER = "visible_bold_nahuatl_1598_lexicon_aligned_2026_06_29"
CEDILLA_MARKER = "visible_bold_nahuatl_1598_cedilla_to_cz_2026_06_29"
QU_MARKER = "visible_bold_nahuatl_1598_qu_before_ao_to_cu_2026_06_29"
INITIAL_Y_MARKER = "visible_bold_nahuatl_1598_initial_y_before_consonant_to_i_2026_06_29"
VISIBLE_LEXICON_MARKER = "visible_inline_nahuatl_1598_lexicon_aligned_2026_06_29"
VISIBLE_CEDILLA_MARKER = "visible_inline_nahuatl_1598_cedilla_to_cz_2026_06_29"
VISIBLE_QU_MARKER = "visible_inline_nahuatl_1598_qu_before_ao_to_cu_2026_06_29"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]

BOLD_RE = re.compile(r"(<b\b[^>]*>)(.*?)(</b>)", re.I | re.S)
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TOKEN_CHARS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç\\[\\]"
WORD_RE = re.compile(rf"[{TOKEN_CHARS}]+")
SINGLE_WORD_RE = re.compile(rf"^[{TOKEN_CHARS}]+$")
QU_BEFORE_AO_TOKEN_RE = re.compile(rf"^([Qq][Uu])([aAoOāĀōŌáÁóÓâÂôÔ][{TOKEN_CHARS}]*)$")
INITIAL_Y_BEFORE_CONSONANT_RE = re.compile(r"^[Yy](?=[bcdfghjklmnpqrstvwxyzçÇ])")
VISIBLE_LEXICON_SIGNAL_RE = re.compile(r"[ÇçÜü]|^[Yy](?=[bcdfghjklmnpqrstvwxyzçÇ])|^[Qq][Uu](?=[aAoO])")
INITIAL_Y_SKIP_KEYS = {"yhetocomatl"}
VISIBLE_SHORT_CEDILLA_KEYS = {"ca", "ce", "cem", "cen"}
DIACRITIC_TRANS = str.maketrans(
    "ÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç",
    "AEIOUUNaeiouunAEIOaeioAEIOaeioCc",
)
CEDILLA_EI = set("eéiíēīêîEÉIÍĒĪÊÎ")
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
    "que",
    "quedó",
    "quedo",
    "quedaron",
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
    "teo",
    "maç",
    "neç",
    "çan",
    "çom",
)

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
        re.compile(r"\by[bcdfghjklmnpqrstvwxyzç][A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôç]*", re.I),
        "review old initial y used for i before consonant",
    ),
    (
        "diaeresis",
        re.compile(r"\b[\wäëïöüÄËÏÖÜÿŸ]*[äëïöüÄËÏÖÜÿŸ][\wäëïöüÄËÏÖÜÿŸ]*\b"),
        "review remaining diaeresis convention",
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
    key = token.translate(DIACRITIC_TRANS).lower().replace("[", "").replace("]", "")
    return re.sub(r"[^a-z]", "", key)


def source_lexicon_key(token: str) -> str:
    return token_key(clean_html(token))


def looks_nahuatl_token(token: str) -> bool:
    key = token_key(token)
    if len(key) < 3 or key in {item.translate(DIACRITIC_TRANS).lower() for item in SPANISH_TOKEN_DENY}:
        return False
    if key.startswith(("qua", "quo")):
        return True
    return any(hint.translate(DIACRITIC_TRANS).lower() in key for hint in NAHUATL_TOKEN_HINTS)


def apply_case_pattern(old: str, new: str) -> str:
    if old.isupper():
        return new.upper()
    if old[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def qu_to_cu(token: str) -> str:
    match = QU_BEFORE_AO_TOKEN_RE.match(token)
    if not match:
        return token
    if token.startswith("QU"):
        return "CU" + token[2:]
    if token.startswith("Qu"):
        return "Cu" + token[2:]
    return "cu" + token[2:]


def cedilla_to_cz(token: str) -> str:
    chars = list(token)
    for index, char in enumerate(chars):
        if char not in {"ç", "Ç"}:
            continue
        next_char = chars[index + 1] if index + 1 < len(chars) else ""
        lower_replacement = "c" if next_char in CEDILLA_EI else "z"
        chars[index] = lower_replacement.upper() if char == "Ç" else lower_replacement
    return "".join(chars)


def build_source_lexicon(rows: list[dict]) -> tuple[dict[str, str], dict[str, set[str]]]:
    values: dict[str, set[str]] = {}
    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        original = clean_html(row.get("Original", ""))
        editado = clean_html(row.get("Editado", ""))
        if not SINGLE_WORD_RE.fullmatch(original) or not SINGLE_WORD_RE.fullmatch(editado):
            continue
        if not (
            re.search(r"[ÇçÜü]", original)
            or re.search(r"^qu[aoāōáóâô]", original, re.I)
            or re.search(r"^[Yy][bcdfghjklmnpqrstvwxyzçÇ]", original)
        ):
            continue
        original_key = source_lexicon_key(original)
        editado_key = source_lexicon_key(editado)
        if original_key.endswith("s") and not editado_key.endswith("s"):
            continue
        if original_key and original_key != editado_key:
            values.setdefault(original_key, set()).add(editado)

    values.setdefault("yanguitlam", set()).add("yanquitlan")
    values.setdefault("yanguitlan", set()).add("yanquitlan")
    values.setdefault("yanguitecas", set()).add("yanquitecas")
    values.setdefault("gueyabas", set()).add("guayabas")
    values.setdefault("hecacozcayo", set()).add("ehecacozcayo")
    values.setdefault("coazaqualco", set()).add("coatzacualco")
    values.setdefault("quixocoqualia", set()).add("xococualia")
    values.setdefault("zaquan", set()).add("zacuan")
    values.setdefault("ynichuihuiac", set()).add("inic huihuiac")
    values["yhetocomatl"] = {"yetecomatl"}

    lexicon: dict[str, str] = {}
    conflicts: dict[str, set[str]] = {}
    for key, edits in values.items():
        if len(edits) == 1:
            lexicon[key] = next(iter(edits))
        else:
            conflicts[key] = edits
    return lexicon, conflicts


def normalize_word(token: str, lexicon: dict[str, str]) -> tuple[str, list[tuple[str, str, str]]]:
    changes: list[tuple[str, str, str]] = []
    lexicon_match = lexicon.get(source_lexicon_key(token))
    if lexicon_match:
        new = apply_case_pattern(token, lexicon_match)
        if new != token:
            changes.append((LEXICON_MARKER, token, new))
            return new, changes

    new = cedilla_to_cz(token)
    if new != token:
        changes.append((CEDILLA_MARKER, token, new))

    after_qu = qu_to_cu(new)
    if after_qu != new and looks_nahuatl_token(new):
        changes.append((QU_MARKER, new, after_qu))
        new = after_qu

    if INITIAL_Y_BEFORE_CONSONANT_RE.search(new) and token_key(new) not in INITIAL_Y_SKIP_KEYS:
        after_y = ("I" if new[0].isupper() else "i") + new[1:]
        changes.append((INITIAL_Y_MARKER, new, after_y))
        new = after_y

    return new, changes


def normalize_text(value: str, lexicon: dict[str, str]) -> tuple[str, list[tuple[str, str, str]]]:
    changes: list[tuple[str, str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            new, token_changes = normalize_word(old, lexicon)
            changes.extend(token_changes)
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold(value: object, lexicon: dict[str, str]) -> tuple[str, list[tuple[str, str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_text(match.group(2), lexicon)
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def normalize_visible_word(token: str, lexicon: dict[str, str]) -> tuple[str, list[tuple[str, str, str]]]:
    changes: list[tuple[str, str, str]] = []
    lexicon_match = lexicon.get(source_lexicon_key(token))
    if lexicon_match and VISIBLE_LEXICON_SIGNAL_RE.search(token):
        new = apply_case_pattern(token, lexicon_match)
        if new != token:
            changes.append((VISIBLE_LEXICON_MARKER, token, new))
            return new, changes

    if ("ç" not in token and "Ç" not in token) or token_key(token) not in VISIBLE_SHORT_CEDILLA_KEYS:
        return token, changes

    new = cedilla_to_cz(token)
    if new != token:
        changes.append((VISIBLE_CEDILLA_MARKER, token, new))

    after_qu = qu_to_cu(new)
    if after_qu != new and looks_nahuatl_token(new):
        changes.append((VISIBLE_QU_MARKER, new, after_qu))
        new = after_qu

    return new, changes


def normalize_visible_segment(value: str, lexicon: dict[str, str]) -> tuple[str, list[tuple[str, str, str]]]:
    changes: list[tuple[str, str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            new, token_changes = normalize_visible_word(old, lexicon)
            changes.extend(token_changes)
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_visible_unbolded(value: object, lexicon: dict[str, str]) -> tuple[str, list[tuple[str, str, str]]]:
    text = str(value or "")
    pieces: list[str] = []
    all_changes: list[tuple[str, str, str]] = []
    last = 0

    for match in BOLD_RE.finditer(text):
        piece, changes = normalize_visible_segment(text[last : match.start()], lexicon)
        pieces.append(piece)
        pieces.append(match.group(0))
        all_changes.extend(changes)
        last = match.end()
    piece, changes = normalize_visible_segment(text[last:], lexicon)
    pieces.append(piece)
    all_changes.extend(changes)
    return "".join(pieces), all_changes


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
    lexicon, conflicts = build_source_lexicon(rows)
    proposals: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    counts: Counter[str] = Counter()
    counts["lexicon_entries"] = len(lexicon)
    counts["lexicon_conflicts"] = len(conflicts)

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
            new_value, field_changes = normalize_bold(value, lexicon)
            new_value, visible_field_changes = normalize_visible_unbolded(new_value, lexicon)
            field_changes.extend(visible_field_changes)
            if new_value == value:
                continue
            for marker, old, new in field_changes:
                row_changes.append((field, marker, old, new))
            if args.apply:
                row[field] = new_value

        if row_changes:
            counts["proposal_rows"] += 1
            counts["proposal_changes"] += len(row_changes)
            counts["proposal_changes_lexicon"] += sum(1 for _, marker, _, _ in row_changes if marker == LEXICON_MARKER)
            counts["proposal_changes_cedilla"] += sum(1 for _, marker, _, _ in row_changes if marker == CEDILLA_MARKER)
            counts["proposal_changes_qu_before_ao"] += sum(1 for _, marker, _, _ in row_changes if marker == QU_MARKER)
            counts["proposal_changes_initial_y_before_consonant"] += sum(
                1 for _, marker, _, _ in row_changes if marker == INITIAL_Y_MARKER
            )
            counts["proposal_changes_visible_lexicon"] += sum(
                1 for _, marker, _, _ in row_changes if marker == VISIBLE_LEXICON_MARKER
            )
            counts["proposal_changes_visible_cedilla"] += sum(
                1 for _, marker, _, _ in row_changes if marker == VISIBLE_CEDILLA_MARKER
            )
            counts["proposal_changes_visible_qu_before_ao"] += sum(
                1 for _, marker, _, _ in row_changes if marker == VISIBLE_QU_MARKER
            )
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
                bold_markers = {LEXICON_MARKER, CEDILLA_MARKER, QU_MARKER, INITIAL_Y_MARKER}
                inline_markers = {VISIBLE_LEXICON_MARKER, VISIBLE_CEDILLA_MARKER, VISIBLE_QU_MARKER}
                if any(marker in bold_markers for marker in changed_by_marker):
                    qa = {
                        **qa,
                        "qa_1598_tezozomoc_visible_bold_oldspell": {
                            "action": "normalized_old_spelling_inside_bold_nahuatl_terms",
                            "markers": [marker for marker in change_markers if marker in bold_markers],
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(changed_by_marker[marker] for marker in bold_markers),
                            "changed_by_marker": {
                                marker: changed_by_marker[marker] for marker in bold_markers if changed_by_marker[marker]
                            },
                            "previous_commentary_sha1": hashlib.sha1(str(row.get(RAW_FIELD, "")).encode("utf-8")).hexdigest(),
                        },
                    }
                if any(marker in inline_markers for marker in changed_by_marker):
                    qa = {
                        **qa,
                        "qa_1598_tezozomoc_visible_inline_oldspell": {
                            "action": "normalized_old_spelling_in_visible_inline_nahuatl_terms",
                            "markers": [marker for marker in change_markers if marker in inline_markers],
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(changed_by_marker[marker] for marker in inline_markers),
                            "changed_by_marker": {
                                marker: changed_by_marker[marker] for marker in inline_markers if changed_by_marker[marker]
                            },
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
