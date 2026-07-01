#!/usr/bin/env python3
"""Normalize visible old-Spanish word forms in 2021 Wimmer public text."""

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
PROPOSALS_PATH = Path("resources/wimmer_2021_oldspanish_word_proposals.tsv")
SUMMARY_PATH = Path("resources/wimmer_2021_oldspanish_word_summary.json")
SOURCE = "2021 Wimmer"
MARKER = "visible_spanish_2021_wimmer_oldword_cleanup_2026_06_29"
QA_KEY = "qa_2021_wimmer_oldspanish_word_cleanup"

PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_SUFFIX = "_raw_2021_wimmer_oldspanish_words"
BOLD_RE = re.compile(r"(<b\b[^>]*>.*?</b>)", re.I | re.S)
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
ALPHA_CLASS = "A-Za-zÀ-ÖØ-öø-ÿĀ-ž"

WORD_REPLACEMENTS = [
    ("auerestudiado", "haber estudiado"),
    ("desuergonçado", "desvergonzado"),
    ("deceruigado", "descervigado"),
    ("descabeçado", "descabezado"),
    ("esforçarse", "esforzarse"),
    ("ponçoñosa", "ponzoñosa"),
    ("çalçamora", "zarzamora"),
    ("çarçamora", "zarzamora"),
    ("beçoleras", "bezoleras"),
    ("cabeçudo", "cabezudo"),
    ("calabaça", "calabaza"),
    ("maçorcas", "mazorcas"),
    ("comienço", "comienzo"),
    ("començar", "comenzar"),
    ("verguença", "vergüenza"),
    ("ymagines", "imágenes"),
    ("adereçar", "aderezar"),
    ("quajados", "cuajados"),
    ("tardança", "tardanza"),
    ("marçorca", "mazorca"),
    ("pescueço", "pescuezo"),
    ("cabeças", "cabezas"),
    ("çapatero", "zapatero"),
    ("alcançar", "alcanzar"),
    ("maçorca", "mazorca"),
    ("lienço", "lienzo"),
    ("cabeça", "cabeza"),
    ("coraçon", "corazón"),
    ("ponçoña", "ponzoña"),
    ("çapatos", "zapatos"),
    ("cedaço", "cedazo"),
    ("çarcillo", "zarcillo"),
    ("çatico", "zatico"),
    ("pedaço", "pedazo"),
    ("fuerças", "fuerzas"),
    ("fuerça", "fuerza"),
    ("braços", "brazos"),
    ("pieça", "pieza"),
    ("çufre", "azufre"),
    ("biuoras", "víboras"),
    ("biuora", "víbora"),
    ("traviesso", "travieso"),
    ("enuarado", "envarado"),
    ("abaxo", "abajo"),
    ("beços", "bezos"),
    ("beuer", "beber"),
    ("boçal", "bozal"),
    ("cozer", "cocer"),
    ("baxo", "bajo"),
    ("braço", "brazo"),
    ("braça", "braza"),
    ("berdes", "verdes"),
    ("moço", "mozo"),
    ("çanja", "zanja"),
    ("loça", "loza"),
    ("caçar", "cazar"),
    ("caça", "caza"),
    ("aues", "aves"),
    ("auer", "haber"),
    ("faxa", "faja"),
    ("hazerse me", "hacérseme"),
    ("hazerse", "hacerse"),
    ("hazerlo", "hacerlo"),
    ("hazerle", "hacerle"),
    ("hazerme", "hacerme"),
    ("reyrse", "reírse"),
    ("reyr", "reír"),
    ("bexigas", "vejigas"),
    ("pedaços", "pedazos"),
    ("mugeres", "mujeres"),
    ("dezmenuzada", "desmenuzada"),
    ("dezian", "decían"),
    ("dezidor", "decidor"),
    ("dezirle", "decirle"),
    ("paraque", "para que"),
    ("enlas", "en las"),
    ("enlos", "en los"),
    ("enla", "en la"),
    ("enel", "en el"),
    ("yglesias", "iglesias"),
    ("yglesia", "iglesia"),
    ("quando", "cuando"),
    ("quales", "cuales"),
    ("qual", "cual"),
    ("dizen", "dicen"),
    ("dize", "dice"),
    ("dezir", "decir"),
    ("haziendo", "haciendo"),
    ("hazen", "hacen"),
    ("hazer", "hacer"),
    ("haze", "hace"),
    ("hazia", "hacia"),
    ("hizieron", "hicieron"),
    ("hiziere", "hiciere"),
    ("dixo", "dijo"),
    ("agora", "ahora"),
    ("ansi", "así"),
    ("assi", "así"),
    ("haver", "haber"),
    ("vnas", "unas"),
    ("vnos", "unos"),
    ("vna", "una"),
    ("vno", "uno"),
    ("vn", "un"),
    ("destas", "de estas"),
    ("destos", "de estos"),
    ("desta", "de esta"),
    ("deste", "de este"),
    ("dellas", "de ellas"),
    ("dellos", "de ellos"),
    ("della", "de ella"),
    ("delas", "de las"),
    ("delos", "de los"),
    ("dela", "de la"),
]

WORD_PATTERNS = [
    (re.compile(rf"(?<![{ALPHA_CLASS}]){old}(?![{ALPHA_CLASS}])", re.I), replacement)
    for old, replacement in WORD_REPLACEMENTS
]
BOLD_WORD_PATTERNS = [
    (re.compile(rf"(?<![{ALPHA_CLASS}]){old}(?![{ALPHA_CLASS}])", re.I), replacement)
    for old, replacement in [("yglesias", "iglesias"), ("yglesia", "iglesia")]
]
QD_RE = re.compile(rf"(?<![{ALPHA_CLASS}])q\s*\.\s*d\s*\.\s*", re.I)


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: object, token: str, width: int = 140) -> str:
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


def raw_field_for(field: str) -> str:
    normalized = (
        field.replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    return normalized + RAW_FIELD_SUFFIX


def match_case(replacement: str, old: str) -> str:
    if old.isupper():
        return replacement.upper()
    if old[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def normalize_piece(piece: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def qd_repl(match: re.Match[str]) -> str:
        old = match.group(0)
        replacement = match_case("quiere decir ", old)
        changes.append((old, replacement))
        return replacement

    piece = QD_RE.sub(qd_repl, piece)

    for pattern, replacement in WORD_PATTERNS:
        def word_repl(match: re.Match[str], replacement: str = replacement) -> str:
            old = match.group(0)
            new = match_case(replacement, old)
            changes.append((old, new))
            return new

        piece = pattern.sub(word_repl, piece)

    return piece, changes


def normalize_bold_piece(piece: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    for pattern, replacement in BOLD_WORD_PATTERNS:
        def word_repl(match: re.Match[str], replacement: str = replacement) -> str:
            old = match.group(0)
            new = match_case(replacement, old)
            changes.append((old, new))
            return new

        piece = pattern.sub(word_repl, piece)

    return piece, changes


def normalize_outside_bold(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    pieces: list[str] = []
    changes: list[tuple[str, str]] = []
    last = 0

    for match in BOLD_RE.finditer(text):
        piece, piece_changes = normalize_piece(text[last : match.start()])
        pieces.append(piece)
        bold_piece, bold_changes = normalize_bold_piece(match.group(0))
        pieces.append(bold_piece)
        changes.extend(piece_changes)
        changes.extend(bold_changes)
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
        raw_fields: list[str] = []

        for field in PUBLIC_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_outside_bold(value)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if args.apply:
                raw_field = raw_field_for(field)
                if raw_field not in row:
                    row[raw_field] = value
                    raw_fields.append(raw_field)
                    counts["raw_preserved_fields"] += 1
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
                    "action": "normalized_visible_old_spanish_word_forms_in_wimmer_public_text",
                    "marker": MARKER,
                    "raw_fields_preserved": raw_fields,
                    "changed_token_count": len(row_changes),
                    "previous_public_field_sha1": hashlib.sha1(
                        "||".join(str(row.get(raw_field, "")) for raw_field in raw_fields).encode("utf-8")
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
