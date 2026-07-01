#!/usr/bin/env python3
"""Normalize selected old-writing residue in 1598 Tezozomoc commentary."""

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
PROPOSALS_PATH = Path("resources/tezozomoc_1598_oldwriting_proposals.tsv")
SUMMARY_PATH = Path("resources/tezozomoc_1598_oldwriting_summary.json")
SOURCE = "1598 Tezozomoc"
RAW_FIELD = "Comentario_raw_1598_tezozomoc_oldwriting"
MARKER = "visible_1598_tezozomoc_oldwriting_2026_06_29"
QA_KEY = "qa_1598_tezozomoc_oldwriting"

DISPLAY_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_BY_FIELD = {
    "Traducción": "Traduccion_raw_1598_tezozomoc_oldwriting",
    "Traducción (es)": "Traduccion_es_raw_1598_tezozomoc_oldwriting",
    "Comentario": RAW_FIELD,
    "Comentario (es)": "Comentario_es_raw_1598_tezozomoc_oldwriting",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_1598_tezozomoc_oldwriting",
}
BOLD_RE = re.compile(r"(<b\b[^>]*>.*?</b>)", re.I | re.S)
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
TOKEN_CHARS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç"

EXACT_REPLACEMENTS: dict[str, str] = {
    "ques": "que es",
    "Acahualçinco": "Acahualcinco",
    "acaçintles": "acacintles",
    "Acaçitli": "Acacitli",
    "acoçile": "acocile",
    "acoçilin": "acocilin",
    "acoçillin": "acocillin",
    "adereçan": "aderezan",
    "atlacueçonan": "atlacuezonan",
    "Ayauhçihuatl": "Ayauhcihuatl",
    "Ayauhçihuatzin": "Ayauhcihuatzin",
    "Ayoçinco": "Ayocinco",
    "açiçicuilotes": "acicicuilotes",
    "caçica": "cacica",
    "comiençe": "comience",
    "començá": "comenzá",
    "conmemoriaçión": "conmemoración",
    "enpanada": "empanada",
    "Huixtoçihuatl": "Huixtocihuatl",
    "Huexoçinço": "Huexotzinco",
    "hazeros": "haceros",
    "hazerlos": "hacerlos",
    "haziendas": "haciendas",
    "maaçehualiztli": "macehualiztli",
    "matalçingas": "matalcingas",
    "Matalçingo": "Matalcingo",
    "Matalçitigo": "Matalcitigo",
    "matlaçingas": "matlacingas",
    "maçatecas": "mazatecas",
    "Maçatlam": "Mazatlam",
    "maçehual": "macehual",
    "maçehualiztli": "macehualiztli",
    "maçehualli": "macehualli",
    "Maçeuhcatzin": "Maceuhcatzin",
    "Micteccaçihuatl": "Micteccacihuatl",
    "Neçahualcoyotzim": "Nezahualcoyotzim",
    "Neçahualcuyutzin": "Nezahualcuyutzin",
    "Neçahualeoyotl": "Nezahualeoyotl",
    "Neçehualpilli": "Nezahualpilli",
    "Oçeloapan": "Oceloapan",
    "oçelotl": "ocelotl",
    "oçelotzitzimitl": "ocelotzitzimitl",
    "pescueçolera": "pescuezolera",
    "prençipalas": "principales",
    "queçaltepecas": "quezaltepecas",
    "Tecçistlan": "Teccistlan",
    "tecçiztentetl": "tecciztentetl",
    "Tecçiztlan": "Tecciztlan",
    "tecçiztli": "tecciztli",
    "Teçihuanitzin": "Tecihuanitzin",
    "teçontle": "tezontle",
    "Tialcoçauhtitlan": "Tialcozauhtitlan",
    "Ticoçic": "Ticocic",
    "tiçatl": "tizatl",
    "Tiçocnahuacatl": "Tizocnahuacatl",
    "Tlaatolçaca": "Tlaatolzaca",
    "Tlacochçalca": "Tlacochcalca",
    "Tlaçimaloyan": "Tlacimaloyan",
    "Tlaçolteutl": "Tlazolteutl",
    "Tonçi": "Tonci",
    "Tozcatoçi": "Tozcatoci",
    "toçicuahuitl": "tocicuahuitl",
    "Toçititlam": "Tocititlam",
    "tuçapanecas": "tuzapanecas",
    "Tzontemoç": "Tzontemoz",
    "yopiçingas": "yopicingas",
    "yupiçingas": "yupicingas",
    "Yupiçingo": "Yupicingo",
    "Çacatlam": "Zacatlam",
    "çacuan": "zacuan",
    "çani": "zani",
    "çaquan": "zacuan",
    "çecuan": "zacuan",
    "Çemanahuac": "Cemanahuac",
    "Çempoalan": "Cempoalan",
    "Çenpoala": "Cenpoala",
    "çenpoaltecas": "cenpoaltecas",
    "çenteycxiques": "centeycxiques",
    "çentzon": "centzon",
    "çentzontlacualli": "centzontlacualli",
    "çençiacatl": "cenciacatl",
    "Çeçepatic": "Cecepatic",
    "Çhalchiuhtonac": "Chalchiuhtonac",
    "Çicozcatlan": "Cicozcatlan",
    "çicuilli": "cicuilli",
    "çihuacalli": "cihuacalli",
    "Çihuacoaltzin": "Cihuacoaltzin",
    "Çihuacoatle": "Cihuacoatle",
    "Çihuacoatli": "Cihuacoatli",
    "Çihuacotlaylotlateuctli": "Cihuacotlaylotlateuctli",
    "çihuatecpan": "cihuatecpan",
    "Çihuatecpan": "Cihuatecpan",
    "Çihuatecpaneca": "Cihuatecpaneca",
    "Çihuateopan": "Cihuateopan",
    "Çihuatl": "Cihuatl",
    "Çihuatlailotlteuctli": "Cihuatlailotlteuctli",
    "çihuatotolin": "cihuatotolin",
    "Çiahuacoatl": "Cihuacoatl",
    "Çincalco": "Cincalco",
    "Çintla": "Cintla",
    "Suchimilço": "Xochimilco",
    "çitamos": "citamos",
    "Çitlallachtli": "Citlallachtli",
    "çoltecas": "zoltecas",
    "Çoçola": "Zozola",
    "çoçoltecas": "zozoltecas",
    "Çíhuacoatl": "Cíhuacoatl",
    "Azcapuçcalco": "Azcapotzalco",
    "questa": "que esta",
    "quarta": "cuarta",
}


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


def build_replacement_patterns() -> list[tuple[re.Pattern[str], str]]:
    items = sorted(EXACT_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True)
    return [
        (re.compile(rf"(?<![{TOKEN_CHARS}]){re.escape(old)}(?![{TOKEN_CHARS}])"), new)
        for old, new in items
    ]


REPLACEMENT_PATTERNS = build_replacement_patterns()


def normalize_piece(piece: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []
    for pattern, replacement in REPLACEMENT_PATTERNS:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            changes.append((old, replacement))
            return replacement

        piece = pattern.sub(repl, piece)
    return piece, changes


def normalize_outside_bold(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    pieces: list[str] = []
    changes: list[tuple[str, str]] = []
    last = 0

    for match in BOLD_RE.finditer(text):
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
        raw_preserved_fields: list[str] = []
        for field in DISPLAY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_outside_bold(value)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if args.apply:
                raw_field = RAW_FIELD_BY_FIELD.get(field)
                if raw_field and raw_field not in row:
                    row[raw_field] = value
                    raw_preserved_fields.append(raw_field)
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
                "context": token_context(row.get(row_changes[0][0], row.get("Comentario", "")), row_changes[0][1]),
            }
        )
        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                QA_KEY: {
                    "action": "normalized_selected_old_writing_outside_bold",
                    "marker": MARKER,
                    "raw_fields_preserved": raw_preserved_fields,
                    "raw_preserved": True,
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
