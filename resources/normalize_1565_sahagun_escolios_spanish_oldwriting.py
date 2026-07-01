#!/usr/bin/env python3
"""Normalize narrow old-Spanish residue in 1565 Sahagun Escolios display."""

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
PROPOSALS_PATH = Path("resources/sahagun_escolios_spanish_oldwriting_proposals.tsv")
SUMMARY_PATH = Path("resources/sahagun_escolios_spanish_oldwriting_summary.json")
SOURCE = "1565 Sahagún Escolios"
MARKER = "visible_spanish_1565_escolios_oldwriting_2026_06_29"
QA_KEY = "qa_1565_escolios_spanish_oldwriting"

PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELDS = {
    "Traducción": "Traducción_raw_1565_sahagun_escolios_oldwriting",
    "Traducción (es)": "Traducción_es_raw_1565_sahagun_escolios_oldwriting",
    "Comentario": "Comentario_public_raw_1565_sahagun_escolios_oldwriting",
    "Comentario (es)": "Comentario_es_raw_1565_sahagun_escolios_oldwriting",
    "Comentario_wimmer_plus_html": "Comentario_wimmer_plus_html_raw_1565_sahagun_escolios_oldwriting",
}
JSON_DISPLAY_PATH = ("Sahagun_Escolios_JSON", "display", "html")

BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bq\.\s*d\.", re.I), "quiere decir"),
    (re.compile(r"(?<![A-Za-zÀ-ÖØ-öø-ÿĀ-ž])dizq\?(?![A-Za-zÀ-ÖØ-öø-ÿĀ-ž])", re.I), "dizque"),
    (re.compile(r"(?<![A-Za-zÀ-ÖØ-öø-ÿĀ-ž])q\?en(?![A-Za-zÀ-ÖØ-öø-ÿĀ-ž])", re.I), "quien"),
    (re.compile(r"(?<![A-Za-zÀ-ÖØ-öø-ÿĀ-ž])q\?(?![A-Za-zÀ-ÖØ-öø-ÿĀ-ž])"), "que"),
    (re.compile(r"(?<![\w-])abil(?![\w-])", re.I), "hábil"),
    (re.compile(r"(?<![\w-])arredondear(?![\w-])", re.I), "redondear"),
    (re.compile(r"(?<![\w-])bayladores(?![\w-])", re.I), "bailadores"),
    (re.compile(r"(?<![\w-])baylar(?![\w-])", re.I), "bailar"),
    (re.compile(r"(?<![\w-])bozear(?![\w-])", re.I), "vocear"),
    (re.compile(r"(?<![\w-])cozido(?![\w-])", re.I), "cocido"),
    (re.compile(r"(?<![\w-])demandâ(?![\w-])", re.I), "demandan"),
    (re.compile(r"(?<![\w-])demâdar(?![\w-])", re.I), "demandar"),
    (re.compile(r"(?<![\w-])dia(?![\w-])", re.I), "día"),
    (re.compile(r"(?<![\w-])dias(?![\w-])", re.I), "días"),
    (re.compile(r"(?<![\w-])delo(?![\w-])", re.I), "de lo"),
    (re.compile(r"(?<![\w-])dque(?![\w-])", re.I), "de que"),
    (re.compile(r"(?<![\w-])ê(?![\w-])", re.I), "en"),
    (re.compile(r"(?<![\w-])âtes(?![\w-])", re.I), "antes"),
    (re.compile(r"(?<![\w-])acôtecer(?![\w-])", re.I), "acontecer"),
    (re.compile(r"(?<![\w-])aparêcia(?![\w-])", re.I), "apariencia"),
    (re.compile(r"(?<![\w-])cômigo(?![\w-])", re.I), "conmigo"),
    (re.compile(r"(?<![\w-])diligête(?![\w-])", re.I), "diligente"),
    (re.compile(r"(?<![\w-])habitâ(?![\w-])", re.I), "habitan"),
    (re.compile(r"(?<![\w-])hîchar(?![\w-])", re.I), "hinchar"),
    (re.compile(r"(?<![\w-])nascê(?![\w-])", re.I), "nacen"),
    (re.compile(r"(?<![\w-])negligêcia(?![\w-])", re.I), "negligencia"),
    (re.compile(r"(?<![\w-])pnîa(?![\w-])", re.I), "ponían"),
    (re.compile(r"(?<![\w-])aûque(?![\w-])", re.I), "aunque"),
    (re.compile(r"(?<![\w-])algûas(?![\w-])", re.I), "algunas"),
    (re.compile(r"(?<![\w-])algûa(?![\w-])", re.I), "alguna"),
    (re.compile(r"(?<![\w-])nûca(?![\w-])", re.I), "nunca"),
    (re.compile(r"(?<![\w-])quâdo(?![\w-])", re.I), "cuando"),
    (re.compile(r"(?<![\w-])reziamête(?![\w-])", re.I), "reciamente"),
    (re.compile(r"(?<![\w-])reuêtar(?![\w-])", re.I), "reventar"),
    (re.compile(r"(?<![\w-])êtendida(?![\w-])", re.I), "entendida"),
    (re.compile(r"(?<![\w-])had(?![\w-])", re.I), "ha"),
    (re.compile(r"(?<![\w-])hazienda(?![\w-])", re.I), "hacienda"),
    (re.compile(r"(?<![\w-])maiz(?![\w-])", re.I), "maíz"),
    (re.compile(r"(?<![\w-])mayz(?![\w-])", re.I), "maíz"),
    (re.compile(r"(?<![\w-])prouincia(?![\w-])", re.I), "provincia"),
    (re.compile(r"(?<![\w-])tio(?![\w-])", re.I), "tío"),
    (re.compile(r"(?<![\w-])vnas(?![\w-])", re.I), "unas"),
    (re.compile(r"(?<![\w-])vnos(?![\w-])", re.I), "unos"),
    (re.compile(r"(?<![\w-])vna(?![\w-])", re.I), "una"),
    (re.compile(r"(?<![\w-])vno(?![\w-])", re.I), "uno"),
    (re.compile(r"(?<![\w-])vn(?![\w-])", re.I), "un"),
    (re.compile(r"(?<![\w-])dizen(?![\w-])", re.I), "dicen"),
    (re.compile(r"(?<![\w-])dize(?![\w-])", re.I), "dice"),
    (re.compile(r"(?<![\w-])dezirse(?![\w-])", re.I), "decirse"),
    (re.compile(r"(?<![\w-])dezir(?![\w-])", re.I), "decir"),
    (re.compile(r"(?<![\w-])hazen(?![\w-])", re.I), "hacen"),
    (re.compile(r"(?<![\w-])hazer(?![\w-])", re.I), "hacer"),
    (re.compile(r"(?<![\w-])haze(?![\w-])", re.I), "hace"),
    (re.compile(r"(?<![\w-])hazia(?![\w-])", re.I), "hacía"),
    (re.compile(r"(?<![\w-])ansi(?![\w-])", re.I), "así"),
    (re.compile(r"(?<![\w-])aquestas(?![\w-])", re.I), "estas"),
    (re.compile(r"(?<![\w-])dela(?![\w-])", re.I), "de la"),
    (re.compile(r"(?<![\w-])desta(?![\w-])", re.I), "de esta"),
    (re.compile(r"(?<![\w-])deste(?![\w-])", re.I), "de este"),
    (re.compile(r"(?<![\w-])destos(?![\w-])", re.I), "de estos"),
    (re.compile(r"(?<![\w-])destas(?![\w-])", re.I), "de estas"),
    (re.compile(r"(?<![\w-])delos(?![\w-])", re.I), "de los"),
    (re.compile(r"(?<![\w-])della(?![\w-])", re.I), "de ella"),
    (re.compile(r"(?<![\w-])dellos(?![\w-])", re.I), "de ellos"),
    (re.compile(r"(?<![\w-])dellas(?![\w-])", re.I), "de ellas"),
    (re.compile(r"(?<![\w-])dexar(?![\w-])", re.I), "dejar"),
    (re.compile(r"(?<![\w-])diziendo(?![\w-])", re.I), "diciendo"),
    (re.compile(r"(?<![\w-])frio(?![\w-])", re.I), "frío"),
    (re.compile(r"(?<![\w-])mesmo(?![\w-])", re.I), "mismo"),
    (re.compile(r"(?<![\w-])qualquiera(?![\w-])", re.I), "cualquiera"),
    (re.compile(r"(?<![\w-])qual(?![\w-])", re.I), "cual"),
    (re.compile(r"(?<![\w-])quinze(?![\w-])", re.I), "quince"),
    (re.compile(r"(?<![\w-])quarta(?![\w-])", re.I), "cuarta"),
    (re.compile(r"(?<![\w-])quando(?![\w-])", re.I), "cuando"),
]


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


def append_marker(value: object, marker: str):
    if isinstance(value, list):
        return value if marker in value else [*value, marker]
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def apply_case(old: str, new: str) -> str:
    letters = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóú]", "", old)
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


def nested_get(row: dict, path: tuple[str, ...]) -> object:
    current: object = row
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def nested_set(row: dict, path: tuple[str, ...], value: object) -> None:
    current = row
    for key in path[:-1]:
        child = current.get(key)
        if not isinstance(child, dict):
            child = {}
            current[key] = child
        current = child
    current[path[-1]] = value


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
                    raw_preserved_fields.append(raw_field)
                    counts["raw_preserved_fields"] += 1
                row[field] = new_value

        json_value = nested_get(row, JSON_DISPLAY_PATH)
        if isinstance(json_value, str):
            new_value, changes = normalize_text(json_value)
            if new_value != json_value:
                row_changes.extend((".".join(JSON_DISPLAY_PATH), old, new) for old, new in changes)
                if args.apply:
                    raw_field = "Sahagun_Escolios_JSON_display_html_raw_oldwriting"
                    if raw_field not in row:
                        row[raw_field] = json_value
                        raw_preserved_fields.append(raw_field)
                        counts["raw_preserved_fields"] += 1
                    nested_set(row, JSON_DISPLAY_PATH, new_value)

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
                    "action": "normalized_exact_old_spanish_residue_in_public_display_fields",
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
