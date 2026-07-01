#!/usr/bin/env python3
"""Normalize isolated old-Spanish residue in public display fields."""

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
PROPOSALS_PATH = Path("resources/oneoff_oldspanish_residue_proposals.tsv")
SUMMARY_PATH = Path("resources/oneoff_oldspanish_residue_summary.json")

DISPLAY_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
BOLD_RE = re.compile(r"(<b\b[^>]*>.*?</b>)", re.I | re.S)
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")

SOURCE_RULES = {
    "1692 Guerra": {
        "slug": "1692_guerra",
        "marker": "visible_spanish_1692_guerra_oldwriting_2026_06_29",
        "qa_key": "qa_1692_guerra_oldwriting",
        "replacements": {"dezuello": "desuello"},
    },
    "1780 ? Bnf_361": {
        "slug": "1780_bnf_361",
        "marker": "visible_spanish_1780_bnf_361_oldwriting_2026_06_29",
        "qa_key": "qa_1780_bnf_361_oldwriting",
        "replacements": {"haverla": "haberla"},
    },
    "1645 Carochi": {
        "slug": "1645_carochi",
        "marker": "visible_spanish_1645_carochi_oldwriting_2026_06_29",
        "qa_key": "qa_1645_carochi_oldwriting",
        "replacements": {
            "ESCALOFRIOS": "ESCALOFRÍOS",
            "affirman": "afirman",
            "affirma": "afirma",
            "afflije": "aflige",
            "afflijo": "aflijo",
            "deshazerse": "deshacerse",
            "diffieren": "difieren",
            "frios": "fríos",
            "Missa": "Misa",
            "missa": "misa",
            "nieue": "nieve",
            "offensa": "ofensa",
            "pretendia": "pretendía",
            "emprestado": "prestado",
            "vltima": "última",
            "vniuersal": "universal",
            ", ô purga": ", o purga",
        },
    },
    "1565 Sahagún Escolios": {
        "slug": "1565_sahagun_escolios",
        "marker": "visible_spanish_1565_sahagun_escolios_oldwriting_oneoff_2026_06_29",
        "qa_key": "qa_1565_sahagun_escolios_oldwriting_oneoff",
        "replacements": {
            "Differencias": "Diferencias",
            "dexa": "deja",
            "destaxo": "destajo",
            "differencias": "diferencias",
            "azezando": "acezando",
            "cortes": "cortés",
            "exemplo": "ejemplo",
            "exenplo": "ejemplo",
            "honrrada": "honrada",
            "honrra": "honra",
            "honrrosas": "honrosas",
            "perona": "persona",
            "renouar": "renovar",
            "tiêpo": "tiempo",
            "tienpo": "tiempo",
            "valde": "balde",
            "anelar": "anhelar",
        },
    },
    "1580 Sahagún/Máynez": {
        "slug": "1580_sahagun_maynez",
        "marker": "visible_spanish_1580_sahagun_maynez_oldwriting_oneoff_2026_06_29",
        "qa_key": "qa_1580_sahagun_maynez_oldwriting_oneoff",
        "replacements": {
            "contradezir": "contradecir",
            "hazecillos": "hacecillos",
            "hazecyllo": "hacecillo",
            "hazelo": "hacerlo",
            "hizieres": "hicieres",
            "rezios": "recios",
            "rezio": "recio",
        },
    },
    "1629 Alarcón": {
        "slug": "1629_alarcon",
        "marker": "visible_spanish_1629_alarcon_oldwriting_oneoff_2026_06_29",
        "qa_key": "qa_1629_alarcon_oldwriting_oneoff",
        "replacements": {
            "OFFICIOS": "OFICIOS",
            "OFFICIO": "OFICIO",
            "affirmaba": "afirmaba",
            "affirmando": "afirmando",
            "baptismo": "bautismo",
            "conffesase": "confesase",
            "differenciaban": "diferenciaban",
            "haziendole": "haciéndole",
            "honrrandolo": "honrándolo",
            "officio": "oficio",
            "offreciendole": "ofreciéndole",
            "offrecieron": "ofrecieron",
            "offrendas": "ofrendas",
            "vltima": "última",
        },
    },
    "17?? Bnf_362bis": {
        "slug": "17xx_bnf_362bis",
        "marker": "visible_spanish_17xx_bnf_362bis_oldwriting_2026_06_29",
        "qa_key": "qa_17xx_bnf_362bis_oldwriting",
        "replacements": {
            "buelban": "vuelvan",
            "dexe": "deje",
            "dexes": "dejes",
            "enquanto": "en cuanto",
            "exemplos": "ejemplos",
            "frios": "fríos",
            "huviera": "hubiera",
            "huvieras": "hubieras",
            "yelos": "hielos",
            "se aze": "se hace",
            "envalde": "en balde",
            "valde": "balde",
            " ó,": " o,",
            " ó ": " o ",
        },
    },
    "1598 Tezozomoc": {
        "slug": "1598_tezozomoc",
        "marker": "visible_spanish_1598_tezozomoc_oldwriting_oneoff_2026_06_29",
        "qa_key": "qa_1598_tezozomoc_oldwriting_oneoff",
        "replacements": {"buelben": "vuelven"},
    },
    "1547 Olmos_V ?": {
        "slug": "1547_olmos_v",
        "marker": "visible_spanish_1547_olmos_v_oldwriting_oneoff_2026_06_30",
        "qa_key": "qa_1547_olmos_v_oldwriting_oneoff",
        "replacements": {"enseãr": "enseñar"},
    },
    "1611 Arenas": {
        "slug": "1611_arenas",
        "marker": "visible_spanish_1611_arenas_oldwriting_oneoff_2026_06_29",
        "qa_key": "qa_1611_arenas_oldwriting_oneoff",
        "replacements": {
            "assigurar": "asegurar",
            "hazenme": "hácenme",
        },
    },
}


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: object, token: str, width: int = 150) -> str:
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


def raw_field_name(field: str, slug: str) -> str:
    safe_field = (
        field.replace("Traducción", "Traduccion")
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
    )
    return f"{safe_field}_raw_{slug}_oldspanish"


def normalize_piece(piece: str, replacements: dict[str, str]) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []
    for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        count = piece.count(old)
        if not count:
            continue
        piece = piece.replace(old, new)
        changes.extend((old, new) for _ in range(count))
    return piece, changes


def normalize_outside_bold(value: object, replacements: dict[str, str]) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    pieces: list[str] = []
    changes: list[tuple[str, str]] = []
    last = 0

    for match in BOLD_RE.finditer(text):
        piece, piece_changes = normalize_piece(text[last : match.start()], replacements)
        pieces.append(piece)
        pieces.append(match.group(0))
        changes.extend(piece_changes)
        last = match.end()
    piece, piece_changes = normalize_piece(text[last:], replacements)
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
        rule = SOURCE_RULES.get(row.get("Fuente"))
        if not rule:
            continue
        counts[f"source_rows:{row.get('Fuente')}"] += 1
        replacements = rule["replacements"]
        marker = rule["marker"]
        slug = rule["slug"]

        row_changes: list[tuple[str, str, str]] = []
        raw_preserved_fields: list[str] = []
        for field in DISPLAY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_outside_bold(value, replacements)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if args.apply:
                raw_field = raw_field_name(field, slug)
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
                "source": row.get("Fuente", ""),
                "record_id": row.get("record_id", ""),
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "marker": marker,
                "old_tokens": " | ".join(f"{field}:{old}" for field, old, _ in row_changes),
                "new_tokens": " | ".join(f"{field}:{new}" for field, _, new in row_changes),
                "context": token_context(row.get(row_changes[0][0], row.get("Comentario", "")), row_changes[0][1]),
            }
        )
        if args.apply:
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), marker)
            row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), marker)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                rule["qa_key"]: {
                    "action": "normalized_isolated_old_spanish_residue_in_public_display_fields",
                    "marker": marker,
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
