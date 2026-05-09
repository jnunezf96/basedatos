#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
RAW_PATH = ROOT / "data" / "data.jsonl.bak1.gz"
REPORT_PATH = ROOT / "scripts" / "sahagun_escolios_translation_grammar_report.jsonl"
SOURCE = "1565 Sahagún Escolios"

NAHUATL_FORM_CHARS = (
    r"A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
    r"āēīōūĀĒĪŌŪâêîôûÂÊÎÔÛçÇ{}\[\]"
)

MARKER_WORDS = r"primitivo|preterito|pres|pret|pti|pt|pri|prim|pre"

SHORT_CITATION_RE = re.compile(r"\s*\((?:\d+[+\-*]?|[a-z]\d?|[a-z]{1,3})\)", re.I)
GRAM_PAREN_RE = re.compile(
    rf"\s*\((?=[^)]*\b(?:{MARKER_WORDS})\.?\b)[^)]*\)",
    re.I,
)
CA_PAREN_RE = re.compile(
    rf"\s*\(ca\.?,?\s*[{NAHUATL_FORM_CHARS}]+\.?\)",
    re.I,
)
CA_FORM_RE = re.compile(
    rf"(?i)(?:,\s*|\s+)ca\.?,?\s*[{NAHUATL_FORM_CHARS}]+\.?"
)
STANDALONE_CA_RE = re.compile(r"(?i)(?:,\s*|\s+)ca\.\s*$")
MARKER_RE = re.compile(rf"(?i)(?:^|[\s,;])(?:{MARKER_WORDS})\.\s*")
START_MARKER_CLAUSE_RE = re.compile(
    rf"(?is)^\s*(?:{MARKER_WORDS})\.\s*[^.]*\.\s*"
)
MULTISPACE_RE = re.compile(r"\s{2,}")
EXPLICIT_MARKER_RE = re.compile(rf"(?i)\b(?:{MARKER_WORDS})\.\s*")
GRAMMAR_RESIDUE_RE = re.compile(
    rf"(?is)^(?:{MARKER_WORDS})\.\s*(?:[{NAHUATL_FORM_CHARS}]+\.?\s*)*$"
)
NAHUATL_FORM_TOKEN_RE = re.compile(rf"^[{NAHUATL_FORM_CHARS}]+$")
NAHUATL_FORM_PREFIXES = (
    "ni",
    "nic",
    "nino",
    "nite",
    "nitla",
    "no",
    "notla",
    "mo",
    "om",
    "oni",
    "oti",
    "oc",
    "ocal",
    "onac",
)

KEEP_TERMINAL_ABBREVS = {
    "ca",
    "etc",
    "lit",
    "p.e",
    "pres",
    "pret",
    "pri",
    "pt",
    "ss",
    "v",
    "vd",
    "vi",
    "vr",
    "vt",
}


def strip_terminal_period(text: str) -> str:
    text = text.rstrip()
    if not text.endswith("."):
        return text
    match = re.search(r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)\.$", text)
    if match and match.group(1).lower() in KEEP_TERMINAL_ABBREVS:
        return text
    return text[:-1].rstrip()


def final_tidy(text: str) -> str:
    old = None
    while old != text:
        old = text
        text = SHORT_CITATION_RE.sub("", text).strip()
        text = GRAM_PAREN_RE.sub("", text).strip()
        text = CA_PAREN_RE.sub("", text).strip()
        text = CA_FORM_RE.sub("", text).strip()
        text = STANDALONE_CA_RE.sub("", text).strip()

    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r",\s*$", "", text).strip()
    text = strip_terminal_period(text)
    return MULTISPACE_RE.sub(" ", text).strip()


def is_grammar_intro(text: str) -> bool:
    candidate = text.strip(" ,;")
    if not candidate:
        return False
    if GRAMMAR_RESIDUE_RE.fullmatch(candidate):
        return True
    tokens = [token.strip(".") for token in candidate.split()]
    if not tokens or len(tokens) > 5:
        return False
    for token in tokens:
        lowered = token.lower()
        if not token or not NAHUATL_FORM_TOKEN_RE.fullmatch(token):
            return False
        if not lowered.startswith(NAHUATL_FORM_PREFIXES):
            return False
    return True


def clean_segment(segment: str) -> str:
    text = final_tidy(segment.strip())
    if not text:
        return ""

    marker = MARKER_RE.search(text)
    if marker:
        before = text[: marker.start()].strip(" ,;")
        if before and not is_grammar_intro(before):
            text = before
        else:
            if before and is_grammar_intro(before):
                text = text[marker.start() :].strip(" ,;")
            changed = True
            while changed:
                changed = False
                for regex in (START_MARKER_CLAUSE_RE,):
                    cleaned = regex.sub("", text, 1).strip()
                    if cleaned != text.strip():
                        text = cleaned
                        changed = True
                        break
            text = text.strip(" ,;")

    return final_tidy(text)


def clean_translation(value: str) -> str:
    text = value or ""
    for _ in range(8):
        old = text
        segments = re.split(r"\s*/\s*", text)
        cleaned = [clean_segment(segment) for segment in segments]
        text = " / ".join(segment for segment in cleaned if segment)
        if old == text:
            return text
    return text


def iter_rows() -> list[dict]:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def load_raw_rows(record_ids: set[str]) -> dict[str, str]:
    raw_by_id: dict[str, str] = {}
    if not record_ids or not RAW_PATH.exists():
        return raw_by_id
    with gzip.open(RAW_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            record_id = row.get("record_id") or ""
            if record_id in record_ids:
                raw_by_id[record_id] = row.get("Traducción") or ""
                if len(raw_by_id) == len(record_ids):
                    break
    return raw_by_id


def normalize_raw_recovery(text: str) -> str:
    replacements = {
        "hazer": "hacer",
        "Hazer": "Hacer",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def should_use_raw_recovery(current_old: str, cleaned: str) -> bool:
    if not EXPLICIT_MARKER_RE.search(current_old):
        return False
    if not cleaned:
        return True
    return GRAMMAR_RESIDUE_RE.fullmatch(cleaned.strip()) is not None


def write_rows(rows: list[dict]) -> None:
    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes to data/data.jsonl.gz")
    args = parser.parse_args()

    rows = iter_rows()
    preliminary: list[tuple[dict, str, str]] = []
    raw_needed: set[str] = set()

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        old = row.get("Traducción") or ""
        new = clean_translation(old)
        if should_use_raw_recovery(old, new):
            raw_needed.add(row.get("record_id") or "")
        preliminary.append((row, old, new))

    raw_by_id = load_raw_rows(raw_needed)
    report = []

    for row, old, new in preliminary:
        raw = raw_by_id.get(row.get("record_id") or "")
        if raw and should_use_raw_recovery(old, new):
            raw_clean = normalize_raw_recovery(clean_translation(raw))
            if raw_clean and not GRAMMAR_RESIDUE_RE.fullmatch(raw_clean.strip()):
                new = raw_clean
        if new == old:
            continue
        report.append(
            {
                "record_id": row.get("record_id"),
                "lemma": row.get("Texto estandarizado"),
                "old_translation": old,
                "new_translation": new,
            }
        )
        if args.apply:
            row["Traducción"] = new

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    if args.apply:
        write_rows(rows)

    print(f"changed_rows={len(report)}")
    print(f"applied={args.apply}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
