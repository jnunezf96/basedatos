#!/usr/bin/env python3
"""Normalize remaining public bracket residues in 1565 Sahagun Escolios.

The public Escolios display still contains a small closed set of bracketed
Nahuatl witness spellings and Spanish gloss abbreviations outside the currently
bolded target spans. This pass applies exact reviewed replacements to public
commentary/display strings, while preserving the raw Escolios packet field.
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
from typing import Any


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/sahagun_escolios_bracketed_residue_proposals.tsv")
SUMMARY_PATH = Path("resources/sahagun_escolios_bracketed_residue_summary.json")
SOURCE = "1565 Sahagún Escolios"
RAW_FIELD = "Comentario_raw_1565_sahagun_escolios"
MARKER = "visible_1565_escolios_bracketed_residue_expansion_2026_06_29"
QA_KEY = "qa_1565_escolios_bracketed_residue_expansion"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
JSON_PUBLIC_PATHS = [
    ("Sahagun_Escolios_JSON", "display", "html"),
    ("Sahagun_Escolios_JSON", "display", "display_witness_line"),
    ("Sahagun_Escolios_JSON", "display", "display_gloss"),
    ("Sahagun_Escolios_JSON", "witness", "display_witness_line_v28"),
    ("Sahagun_Escolios_JSON", "witness", "display_gloss_v28"),
]

BOLD_RE = re.compile(r"(<b\b[^>]*>.*?</b>)", re.I | re.S)
BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")

REPLACEMENTS = {
    "P[reterito]": "Pretérito",
    "P[er]o": "Pero",
    "I[n]": "In",
    "a[ver]": "aver",
    "aq[hue]quelli": "aquequelli",
    "aquetzq[hui]": "aquetzqui",
    "aca[n]": "acan",
    "ahuilq[hui]zqui": "ahuilquizqui",
    "ao[n]monamic": "aonmonamic",
    "at[ra]ycion": "atraycion",
    "atlaqu[el]matini": "atlaquelmatini",
    "cemoq[hui]chtli": "cemoquichtli",
    "chiq[ui]llos": "chiquillos",
    "co[n]dicion": "condicion",
    "co[n]sejos": "consejos",
    "cualloq[hui]chtli": "cualloquichtli",
    "cuid[ado]": "cuidado",
    "ense[ña]": "enseña",
    "h[erman]o": "hermano",
    "i[n]": "in",
    "instrum[ento]": "instrumento",
    "ma[l]": "mal",
    "matratami[ent]o": "matratamiento",
    "menosp[re]cia": "menosprecia",
    "mis[mo]": "mismo",
    "m[edio]": "medio",
    "mu[erto]": "muerto",
    "n[in]guno": "ninguno",
    "n[uest]ra": "nuestra",
    "nau[sea]": "nausea",
    "nocalp[an]coneuh": "nocalpanconeuh",
    "notlaca[xo]lopi": "notlacaxolopi",
    "notlate[c]huacauh": "notlatechuacauh",
    "o[ni]eltic": "onieltic",
    "o[ni]heltic": "oniheltic",
    "ochichiliuhticmoma[n]": "ochichiliuhticmoman",
    "oninezticat[ca]": "oninezticatca",
    "oq[hui]chtli": "oquichtli",
    "p[er]zona": "persona",
    "per[sona]": "persona",
    "pa[ra]": "para",
    "pare[n]tesco": "parentesco",
    "pensamj[ento]": "pensamiento",
    "p[ar]a": "para",
    "p[art]o": "parto",
    "q[ua]lli": "cualli",
    "q[ue]": "que",
    "s[eñ]or": "señor",
    "s[anc]to": "sancto",
    "sa[n]gre": "sangre",
    "sp[irit]ual": "spiritual",
    "suc[cesor]es": "sucesores",
    "teahuilq[hui]xtia": "teahuilquixtia",
    "teq[hui]xti": "tequixti",
    "tlacaq[hui]ni": "tlacaquini",
    "tlaoq[hui]chuiani": "tlaoquichuiani",
    "tlapiq[hui]": "tlapiqui",
    "tlateq[hui]panoa": "tlatequipanoa",
    "tlateq[hui]panoani": "tlatequipanoani",
    "xocotonq[hui]": "xocotonqui",
    "y[n]": "in",
}
REPLACEMENT_ITEMS = sorted(REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True)


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


def append_issue(value: object, marker: str) -> object:
    if isinstance(value, list):
        return value if marker in value else [*value, marker]
    return append_marker(value, marker)


def normalize_piece(piece: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []
    for old, new in REPLACEMENT_ITEMS:
        count = piece.count(old)
        if not count:
            continue
        piece = piece.replace(old, new)
        changes.extend((old, new) for _ in range(count))
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


def path_get(root: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = root
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def path_set(root: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    target: Any = root
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


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
        if args.apply and RAW_FIELD not in row:
            row[RAW_FIELD] = row.get("Comentario", "")
            counts["raw_preserved_rows"] += 1

        row_changes: list[tuple[str, str, str]] = []

        for field in COMMENTARY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_outside_bold(value)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            if args.apply:
                row[field] = new_value

        for path in JSON_PUBLIC_PATHS:
            value = path_get(row, path)
            if not isinstance(value, str) or not value:
                continue
            new_value, changes = normalize_outside_bold(value)
            if new_value == value:
                continue
            field = ".".join(path)
            row_changes.extend((field, old, new) for old, new in changes)
            if args.apply:
                path_set(row, path, new_value)

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
            row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
            row["Comentario_display_issues"] = append_issue(row.get("Comentario_display_issues"), MARKER)
            qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
            qa = {
                **qa,
                QA_KEY: {
                    "action": "expanded_public_bracketed_residue_outside_bold_spans",
                    "marker": MARKER,
                    "raw_field": RAW_FIELD,
                    "raw_preserved": True,
                    "changed_token_count": len(row_changes),
                    "changed_public_fields": sorted({field for field, _, _ in row_changes}),
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
