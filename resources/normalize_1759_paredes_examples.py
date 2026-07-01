#!/usr/bin/env python3
"""Normalize safe visible Nahuatl example spelling in 1759 Paredes.

Paredes rows are mostly bold Nahuatl doctrinal examples with Spanish glosses in
parentheses. This pass is deliberately narrow: it rewrites only bold spans for
Nahuatl orthography, normalizes exact repeated old-Spanish citation-title and
religious loanword tokens, and preserves the original public commentary before
changing display text.

Safe source-specific rules:

* ``ç/Ç`` -> ``z/Z`` in bold Nahuatl-side examples.
* ``qu-/Qu-`` before ``a/o`` -> ``cu-/Cu-`` in likely Nahuatl tokens.
* repeated Spanish citation-title tokens such as ``Platica`` -> ``Plática``.
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
PROPOSALS_PATH = Path("resources/paredes_1759_example_normalization_proposals.tsv")
REVIEW_PATH = Path("resources/paredes_1759_example_normalization_review.tsv")
SUMMARY_PATH = Path("resources/paredes_1759_example_normalization_summary.json")
SOURCE = "1759 Paredes"
RAW_FIELD = "Comentario_raw_1759_paredes"
CEDILLA_MARKER = "visible_bold_nahuatl_1759_cedilla_to_z_2026_06_29"
QU_MARKER = "visible_bold_nahuatl_1759_qu_before_ao_to_cu_2026_06_29"
SPANISH_OLD_SPELLING_MARKER = "visible_spanish_1759_paredes_oldwriting_2026_06_29"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]

BOLD_RE = re.compile(r"(<b\b[^>]*>)(.*?)(</b>)", re.I | re.S)
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TOKEN_CHARS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùÇç\\[\\]"
WORD_RE = re.compile(rf"[{TOKEN_CHARS}]+")
QU_BEFORE_AO_RE = re.compile(r"[Qq][Uu](?=[aAoOāĀōŌáÁóÓâÂôÔàÀòÒ])")
CEDILLA_TOKEN_RE = re.compile(rf"[{TOKEN_CHARS}]*[Çç][{TOKEN_CHARS}]*")
DIACRITIC_TRANS = str.maketrans(
    "ÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùÇç",
    "AEIOUUNaeiouunAEIOaeioAEIOaeioAEIOUaeiouCc",
)
SPANISH_LATIN_TOKEN_DENY = {
    "quasi",
    "quando",
    "cuando",
    "quanto",
    "cuanto",
    "quantos",
    "cuantos",
    "quatro",
    "cuatro",
    "quarenta",
    "cuarenta",
    "quarto",
    "cuarto",
    "quintos",
    "quinientos",
    "quince",
    "qualis",
    "quod",
    "quabitur",
}
NAHUATL_TOKEN_HINTS = (
    "tl",
    "tz",
    "hu",
    "auh",
    "hua",
    "tzin",
    "xoch",
    "teo",
    "atl",
    "yotl",
    "pohu",
    "mict",
    "tepec",
    "tlan",
    "quetz",
    "coatl",
    "chih",
    "cal",
    "calli",
    "tocht",
    "cuitl",
    "olli",
    "matl",
    "yollo",
    "ix",
    "qual",
    "quah",
    "quauh",
    "qua",
    "iqua",
)
SPANISH_OLD_SPELLING_REPLACEMENTS = {
    "Angeles": "Ángeles",
    "Angel": "Ángel",
    "Baptismo": "Bautismo",
    "Catholica": "Católica",
    "Christina": "Cristiana",
    "Christiano": "Cristiano",
    "Christo": "Cristo",
    "Comunion": "Comunión",
    "comunion": "comunión",
    "Confirmacion": "Confirmación",
    "Contricion": "Contrición",
    "decimo": "décimo",
    "demas": "demás",
    "Encarnacion": "Encarnación",
    "Espiritu": "Espíritu",
    "Evangelicos": "Evangélicos",
    "Explicacion": "Explicación",
    "Invocacion": "Invocación",
    "Missa": "Misa",
    "Moderacion": "Moderación",
    "matarâs": "matarás",
    "Oyr": "Oír",
    "oyr": "oír",
    "Platica": "Plática",
    "Proximo": "Prójimo",
    "proximo": "prójimo",
    "Resurreccion": "Resurrección",
    "throno": "trono",
    "Uncion": "Unción",
    "bienauenturanza": "bienaventuranza",
}
SPANISH_OLD_SPELLING_RE = re.compile(
    r"(?<![A-Za-zÀ-ÖØ-öø-ÿĀ-ž])("
    + "|".join(re.escape(old) for old in sorted(SPANISH_OLD_SPELLING_REPLACEMENTS, key=len, reverse=True))
    + r")(?![A-Za-zÀ-ÖØ-öø-ÿĀ-ž])"
)

REVIEW_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "cedilla",
        CEDILLA_TOKEN_RE,
        "review cedilla not handled by the safe pass",
    ),
    (
        "qu_before_a_o",
        re.compile(
            r"\bqu[aoāōáóâôàò][A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòù\[\]]*",
            re.I,
        ),
        "review qu before a/o not handled by the safe pass",
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
    if len(key) < 3 or key in SPANISH_LATIN_TOKEN_DENY:
        return False
    if key.startswith(("qua", "quo")):
        return True
    return any(hint in key for hint in NAHUATL_TOKEN_HINTS)


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


def normalize_bold(value: object) -> tuple[str, list[tuple[str, str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner, cedilla_changes = normalize_cedilla_in_text(match.group(2))
        inner, qu_changes = normalize_qu_before_ao_in_text(inner)
        all_changes.extend((CEDILLA_MARKER, old, new) for old, new in cedilla_changes)
        all_changes.extend((QU_MARKER, old, new) for old, new in qu_changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def normalize_spanish_old_spellings_piece(piece: str) -> tuple[str, list[tuple[str, str, str]]]:
    changes: list[tuple[str, str, str]] = []

    def repl(match: re.Match[str]) -> str:
        old = match.group(1)
        new = SPANISH_OLD_SPELLING_REPLACEMENTS[old]
        if new != old:
            changes.append((SPANISH_OLD_SPELLING_MARKER, old, new))
        return new

    return SPANISH_OLD_SPELLING_RE.sub(repl, piece), changes


def normalize_spanish_old_spellings(value: object) -> tuple[str, list[tuple[str, str, str]]]:
    return normalize_spanish_old_spellings_piece(str(value or ""))


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
            new_value, spanish_changes = normalize_spanish_old_spellings(value)
            new_value, bold_changes = normalize_bold(new_value)
            changes = spanish_changes + bold_changes
            if new_value == value:
                continue
            for marker, old, new in changes:
                row_changes.append((field, marker, old, new))
            if args.apply:
                row[field] = new_value

        if row_changes:
            markers = list(dict.fromkeys(marker for _, marker, _, _ in row_changes))
            counts["proposal_rows"] += 1
            counts["proposal_changes"] += len(row_changes)
            counts["proposal_changes_cedilla"] += sum(1 for _, marker, _, _ in row_changes if marker == CEDILLA_MARKER)
            counts["proposal_changes_qu_before_ao"] += sum(1 for _, marker, _, _ in row_changes if marker == QU_MARKER)
            counts["proposal_changes_spanish_old_spelling"] += sum(
                1 for _, marker, _, _ in row_changes if marker == SPANISH_OLD_SPELLING_MARKER
            )
            proposals.append(
                {
                    "record_id": row.get("record_id", ""),
                    "original": row.get("Original", ""),
                    "editado": row.get("Editado", ""),
                    "markers": ";".join(markers),
                    "old_tokens": " | ".join(f"{field}:{old}" for field, _, old, _ in row_changes),
                    "new_tokens": " | ".join(f"{field}:{new}" for field, _, _, new in row_changes),
                    "context": token_context(row.get("Comentario", ""), row_changes[0][2]),
                }
            )
            if args.apply:
                for marker in markers:
                    row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), marker)
                    row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), marker)
                qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
                previous_commentary_sha1 = hashlib.sha1(str(row.get(RAW_FIELD, "")).encode("utf-8")).hexdigest()
                if any(marker == CEDILLA_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1759_paredes_cedilla_to_z": {
                            "action": "normalized_cedilla_to_z_inside_bold_nahuatl_examples",
                            "marker": CEDILLA_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == CEDILLA_MARKER
                            ),
                            "previous_commentary_sha1": previous_commentary_sha1,
                        },
                    }
                if any(marker == QU_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1759_paredes_qu_before_ao_to_cu": {
                            "action": "normalized_qu_before_a_o_to_cu_inside_bold_nahuatl_examples",
                            "marker": QU_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == QU_MARKER
                            ),
                            "previous_commentary_sha1": previous_commentary_sha1,
                        },
                    }
                if any(marker == SPANISH_OLD_SPELLING_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1759_paredes_spanish_old_spelling": {
                            "action": "normalized_exact_repeated_old_spanish_citation_and_loanword_tokens",
                            "marker": SPANISH_OLD_SPELLING_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == SPANISH_OLD_SPELLING_MARKER
                            ),
                            "previous_commentary_sha1": previous_commentary_sha1,
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
