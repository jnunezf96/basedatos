#!/usr/bin/env python3
"""Normalize Wimmer Nahuatl-token macrons/circumflexes in public fields."""

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
PROPOSALS_PATH = Path("resources/wimmer_nahuatl_diacritics_public_proposals.tsv")
SUMMARY_PATH = Path("resources/wimmer_nahuatl_diacritics_public_summary.json")
MARKER = "visible_wimmer_nahuatl_diacritics_public_2026_06_30_v3"
QA_KEY = "qa_wimmer_nahuatl_diacritics_public"

TARGET_SOURCE = "2021 Wimmer"
PUBLIC_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
RAW_FIELD_SUFFIX = "_raw_wimmer_nahuatl_diacritics_public"

BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
WORD_RE = re.compile(r"[A-Za-zĀĒĪŌŪāēīōūÂÊÎÔÛâêîôûÀÈÌÒÙàèìòùÁÉÍÓÚÜÑáéíóúüñÄËÏÖÜäëïöüÇç'-]+")
MACRON_RE = re.compile("[ĀĒĪŌŪāēīōū]")
CIRCUMFLEX_RE = re.compile("[ÂÊÎÔÛâêîôû]")
TARGET_RE = re.compile("[ĀĒĪŌŪāēīōūÂÊÎÔÛâêîôû]")
SCAN_RE = re.compile("[ĀĒĪŌŪāēīōūÂÊÎÔÛâêîôûÁÉÍÓÚáéíóú]")
FOREIGN_ACCENT_RE = re.compile("[ÀÈÌÒÙàèìòùÁÉÍÓÚÜÑáéíóúüñÄËÏÖÜäëïöüÇç]")
ACUTE_RE = re.compile("[ÁÉÍÓÚáéíóú]")
OTHER_FOREIGN_ACCENT_RE = re.compile("[ÀÈÌÒÙàèìòùÜÑüñÄËÏÖÜäëïöüÇç]")
NAHUATL_CLUSTER_RE = re.compile(r"(tl|tz|hu|uh|cu)", re.I)
STRONG_NAHUATL_ACUTE_RE = re.compile(r"(tl|tz|hu|uh|cu|xoch|cihua|nahua|teuc|teo|tzin|lli|otl|atl)", re.I)
GLUED_FOREIGN_PREFIX_RE = re.compile(r"^(?:ahabia|aaqui|pajaro|cocinado|decrit|peut-etre)", re.I)
VOCATIVE_CONTEXT_RE = re.compile(r"vocati[fv]|vocativo|vocative", re.I)
VOCATIVE_FINAL_ACUTE_RE = re.compile(r"é$", re.I)
VOCATIVE_NAHUATL_SIGNAL_RE = re.compile(
    r"(tl|tz|uh|cu|xoch|cihua|nahua|teuc|teo|tzin|otl|atl|hua|queh|yahc|xihui|coco|pil|xol)",
    re.I,
)
BOLD_FINAL_ACUTE_NAHUATL_SIGNAL_RE = re.compile(
    r"(tl|tz|xoch|cihua|nahua|teuc|teo|tzin|otl|atl|queh|yahc|xihui|coco|xol|cauh|huan|huah|huitl|hue|hui|ahua)",
    re.I,
)
SAFE_FINAL_ACUTE_NAHUATL = {
    "ilhuicé",
    "nopiltzé",
    "nopiltziné",
    "otomitlé",
}
MORPH_INCORP_RE = re.compile(r"(?:morph\.incorp|morf\.\s*incorp)", re.I)
FORM_LABEL_RE = re.compile(r"(?:Form|Forma):", re.I)
MORPH_TOKEN_TRIGGER_RE = re.compile(
    r"(?:\b(?:sur|sobre|en|de|from|cf)\b|morph\.incorp\.?|morf\.\s*incorp\.?)\s*(?:[(*'\"]\s*)?$",
    re.I,
)
FOREIGN_METADATA_DENY = {
    "appats",
    "bruler",
    "croute",
    "etre",
    "flute",
    "meme",
    "peut-etre",
    "tete",
}
NAHUATL_ENDING_RE = re.compile(
    r"(tl|tli|lli|li|qui|hua|huia|tia|ia|ca|can|yan|pan|tlan|meh|queh|tin|tzin|yotl|otl|atl|ehuia|oa|ohua|ilia|lli)$",
    re.I,
)
SHORT_NAHUATL = {
    "â",
    "ê",
    "î",
    "ô",
    "mâ",
    "nô",
    "tê",
    "teô",
    "nên",
    "nâm",
    "yôcoya",
}
DIACRITIC_MAP = str.maketrans({
    "Ā": "A",
    "Ē": "E",
    "Ī": "I",
    "Ō": "O",
    "Ū": "U",
    "ā": "a",
    "ē": "e",
    "ī": "i",
    "ō": "o",
    "ū": "u",
    "Â": "A",
    "Ê": "E",
    "Î": "I",
    "Ô": "O",
    "Û": "U",
    "â": "a",
    "ê": "e",
    "î": "i",
    "ô": "o",
    "û": "u",
    "Á": "A",
    "É": "E",
    "Í": "I",
    "Ó": "O",
    "Ú": "U",
    "á": "a",
    "é": "e",
    "í": "i",
    "ó": "o",
    "ú": "u",
})


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: object, token: str, width: int = 150) -> str:
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


def looks_nahuatl_circumflex_token(token: str) -> bool:
    core = token.strip("'-").lower()
    if not core or FOREIGN_ACCENT_RE.search(core):
        return False
    if core in SHORT_NAHUATL:
        return True
    if NAHUATL_CLUSTER_RE.search(core):
        return True
    if NAHUATL_ENDING_RE.search(core):
        return True
    return False


def looks_nahuatl_acute_token(token: str) -> bool:
    core = token.strip("'-")
    if not core or OTHER_FOREIGN_ACCENT_RE.search(core):
        return False
    plain = core.translate(DIACRITIC_MAP).lower()
    if GLUED_FOREIGN_PREFIX_RE.search(plain):
        return False
    return bool(STRONG_NAHUATL_ACUTE_RE.search(plain))


def looks_vocative_final_acute_token(value: str, match: re.Match[str]) -> bool:
    token = match.group(0).strip("\"")
    core = token.strip("'-")
    if "'" in token or not VOCATIVE_FINAL_ACUTE_RE.search(core):
        return False
    if TARGET_RE.search(core) or OTHER_FOREIGN_ACCENT_RE.search(core):
        return False
    plain = core.translate(DIACRITIC_MAP)
    if core.lower() in SAFE_FINAL_ACUTE_NAHUATL:
        return True
    if is_inside_b_tag(value, match.start(), match.end()):
        return bool(BOLD_FINAL_ACUTE_NAHUATL_SIGNAL_RE.search(plain))
    if not VOCATIVE_NAHUATL_SIGNAL_RE.search(plain):
        return False
    left = max(0, match.start() - 220)
    right = min(len(value), match.end() + 220)
    return bool(VOCATIVE_CONTEXT_RE.search(clean_html(value[left:right])))


def is_inside_b_tag(value: str, start: int, end: int) -> bool:
    before = value[:start].lower()
    after = value[end:].lower()
    return before.rfind("<b>") > before.rfind("</b>") and after.find("</b>") != -1


def looks_morph_incorp_metadata_token(value: str, match: re.Match[str]) -> bool:
    token = match.group(0).strip("'\"")
    core = token.strip("'-")
    if not core or FOREIGN_ACCENT_RE.search(core):
        return False
    plain = token.translate(DIACRITIC_MAP).strip("'-").lower()
    if plain in FOREIGN_METADATA_DENY:
        return False

    left = value[max(0, match.start() - 160) : match.start()]
    right = value[match.end() : min(len(value), match.end() + 100)]
    if not MORPH_INCORP_RE.search(left + token + right):
        return False
    form_matches = list(FORM_LABEL_RE.finditer(left))
    if not form_matches:
        return False
    clause = left[form_matches[-1].start() :]
    if re.search(r"(?:sens|meaning|significado)\s+de\s*$", clause, re.I):
        return False
    return bool(MORPH_TOKEN_TRIGGER_RE.search(clause))


def should_normalize_token(token: str, value: str, match: re.Match[str]) -> bool:
    if ACUTE_RE.search(token) and looks_vocative_final_acute_token(value, match):
        return True
    if MACRON_RE.search(token):
        return True
    if CIRCUMFLEX_RE.search(token) and ACUTE_RE.search(token) and looks_nahuatl_acute_token(token):
        return True
    if CIRCUMFLEX_RE.search(token) and looks_morph_incorp_metadata_token(value, match):
        return True
    if CIRCUMFLEX_RE.search(token) and looks_nahuatl_circumflex_token(token):
        return True
    return False


def normalize_text(value: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        if not SCAN_RE.search(token) or not should_normalize_token(token, value, match):
            return token
        new = token.translate(DIACRITIC_MAP)
        if new != token:
            changes.append((token, new))
        return new

    return WORD_RE.sub(repl, value), changes


def load_rows(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as handle:
        for row in rows:
            json.dump(row, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
    os.replace(tmp, path)


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
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
    counts: Counter[str] = Counter()
    pair_counts: Counter[str] = Counter()
    proposals: list[dict[str, object]] = []

    for row in rows:
        if row.get("Fuente") != TARGET_SOURCE:
            continue
        counts["target_source_rows"] += 1
        previous_public = "||".join(str(row.get(field, "")) for field in PUBLIC_FIELDS)
        row_changes: list[tuple[str, str, str]] = []
        raw_fields: list[str] = []

        for field in PUBLIC_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not SCAN_RE.search(value):
                continue
            new_value, changes = normalize_text(value)
            if new_value == value:
                continue
            row_changes.extend((field, old, new) for old, new in changes)
            for old, new in changes:
                pair_counts[f"{old}>{new}"] += 1
            if args.apply:
                raw_field = raw_field_for(field)
                if raw_field not in row:
                    row[raw_field] = value
                    counts["raw_preserved_fields"] += 1
                if raw_field not in raw_fields:
                    raw_fields.append(raw_field)
                row[field] = new_value

        if not row_changes:
            continue

        counts["proposal_rows"] += 1
        counts["proposal_changes"] += len(row_changes)
        proposals.append(
            {
                "source": row.get("Fuente", ""),
                "record_id": row.get("record_id", ""),
                "field": row_changes[0][0],
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "old_tokens": " | ".join(f"{field}:{old}" for field, old, _new in row_changes[:20]),
                "new_tokens": " | ".join(f"{field}:{new}" for field, _old, new in row_changes[:20]),
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
                    "action": "normalized_wimmer_nahuatl_token_macron_and_safe_circumflex_in_public_display_fields",
                    "marker": MARKER,
                    "raw_fields_preserved": raw_fields,
                    "changed_token_count": len(row_changes),
                    "previous_public_field_sha1": hashlib.sha1(previous_public.encode("utf-8")).hexdigest(),
                },
            }
            row["Sentence_Source_JSON"] = qa
            counts["applied_rows"] += 1

    fields = ["source", "record_id", "field", "original", "editado", "old_tokens", "new_tokens", "context"]
    write_tsv(args.proposals, proposals, fields)
    summary = {**counts, "top_replacements": dict(pair_counts.most_common())}
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.apply and proposals:
        write_rows(args.data, rows)

    print(f"summary {dict(counts)}")
    print(f"proposals {args.proposals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
