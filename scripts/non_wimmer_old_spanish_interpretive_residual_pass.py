#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_interpretive_residual_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")


TOKEN_REPLACEMENTS: dict[str, tuple[str, str]] = {
    "acasa": ("a casa", "fused_particle"),
    "aesta": ("a esta", "fused_particle"),
    "aestas": ("a estas", "fused_particle"),
    "aeste": ("a este", "fused_particle"),
    "aestos": ("a estos", "fused_particle"),
    "algúna": ("alguna", "accent_or_old_spelling"),
    "algúnas": ("algunas", "accent_or_old_spelling"),
    "algúno": ("alguno", "accent_or_old_spelling"),
    "algúnos": ("algunos", "accent_or_old_spelling"),
    "alcombite": ("al convite", "fused_particle"),
    "alcabo": ("al cabo", "fused_particle"),
    "alcriado": ("al criado", "fused_particle"),
    "alfin": ("al fin", "fused_particle"),
    "apardemi": ("a par de mí", "fused_particle"),
    "apoco": ("a poco", "fused_particle"),
    "apocos": ("a pocos", "fused_particle"),
    "cabemi": ("cabe mí", "fused_particle"),
    "cónque": ("con que", "fused_particle"),
    "conrazones": ("con razones", "fused_particle"),
    "dandome": ("dándome", "accent_or_old_spelling"),
    "poray": ("por ahí", "fused_particle"),
    "qualesquier": ("cualesquier", "old_spelling"),
    "qualquier": ("cualquier", "old_spelling"),
    "qualquiera": ("cualquiera", "old_spelling"),
    "selo": ("se lo", "fused_particle"),
    "sierua": ("sierva", "old_spelling"),
    "sieruas": ("siervas", "old_spelling"),
    "sieruo": ("siervo", "old_spelling"),
    "sieruos": ("siervos", "old_spelling"),
    "aflicion": ("aflicción", "accent_or_old_spelling"),
    "algun": ("algún", "accent_or_old_spelling"),
    "frio": ("frío", "accent_or_old_spelling"),
    "oracion": ("oración", "accent_or_old_spelling"),
    "razon": ("razón", "accent_or_old_spelling"),
}


TOKEN_RE = re.compile(
    rf"(?<![{LETTER}])("
    + "|".join(re.escape(token) for token in sorted(TOKEN_REPLACEMENTS, key=len, reverse=True))
    + rf")(?![{LETTER}])",
    re.I,
)

ADVERB_ABBREV_RE = re.compile(rf"(?<![{LETTER}])(aduer|adue)\.?(?![{LETTER}])", re.I)
AVER_RE = re.compile(rf"(?<![{LETTER}])aver(?![{LETTER}])", re.I)
UN_AVER_RE = re.compile(rf"(?<![{LETTER}])(un)(\s+)aver(?![{LETTER}])", re.I)
AMI_RE = re.compile(rf"(?<![{LETTER}])ami(?![{LETTER}])")
DEMI_RE = re.compile(rf"(?<![{LETTER}])demi(?![{LETTER}])")
PAR_DEMI_RE = re.compile(rf"(?<![{LETTER}])par\s+demi(?![{LETTER}])")

POSSESSIVE_MI_NEXT = {"cargo", "mano", "persona", "vando", "voluntad"}


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def replace_adverb_abbrev(match: re.Match[str]) -> str:
    return preserve_case(match.group(1), "adv.")


def replace_aver(text: str, source: str) -> tuple[str, bool]:
    changed = False

    def replace_un_aver(match: re.Match[str]) -> str:
        nonlocal changed
        changed = True
        return preserve_case(match.group(1), "un") + match.group(2) + "ave"

    if source == "V94 Diccionario Global SNP":
        text = UN_AVER_RE.sub(replace_un_aver, text)

    def replace_match(match: re.Match[str]) -> str:
        nonlocal changed
        start, end = match.span()
        left = text[max(0, start - 12) : start].lower()
        right = text[end : min(len(text), end + 12)].lower()
        changed = True
        if re.search(r"\bir\s+$", left):
            return preserve_case(match.group(0), "a ver")
        if re.match(r"\s+que\b", right):
            return preserve_case(match.group(0), "a ver")
        return preserve_case(match.group(0), "haber")

    return AVER_RE.sub(replace_match, text), changed


def replace_ami_demi(text: str) -> tuple[str, bool]:
    changed = False
    text = PAR_DEMI_RE.sub("a par de mí", text)
    if "a par de mí" in text:
        changed = True

    def next_word(start: int) -> str:
        match = re.match(rf"\W*([{LETTER}]+)", text[start:])
        return match.group(1).lower() if match else ""

    def replace_ami(match: re.Match[str]) -> str:
        nonlocal changed
        changed = True
        return "a mi" if next_word(match.end()) in {"cargo", "persona"} else "a mí"

    def replace_demi(match: re.Match[str]) -> str:
        nonlocal changed
        changed = True
        return "de mi" if next_word(match.end()) in POSSESSIVE_MI_NEXT else "de mí"

    text = AMI_RE.sub(replace_ami, text)
    text = DEMI_RE.sub(replace_demi, text)
    return text, changed


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    if source == "2021 Wimmer":
        return text, []

    reasons: list[str] = []
    new = text

    after_adverb = ADVERB_ABBREV_RE.sub(replace_adverb_abbrev, new)
    if after_adverb != new:
        new = after_adverb
        reasons.append("adverb_abbrev")

    after_aver, changed_aver = replace_aver(new, source)
    if changed_aver:
        new = after_aver
        reasons.append("aver_contextual")

    after_ami_demi, changed_ami_demi = replace_ami_demi(new)
    if changed_ami_demi:
        new = after_ami_demi
        reasons.append("ami_demi_contextual")

    def replace_token(match: re.Match[str]) -> str:
        replacement, reason = TOKEN_REPLACEMENTS[match.group(0).lower()]
        reasons.append(reason)
        return preserve_case(match.group(0), replacement)

    new = TOKEN_RE.sub(replace_token, new)

    # Finish the two known "aver que" examples as modern "a ver qué".
    finalized = re.sub(r"\ba ver que\b", "a ver qué", new, flags=re.I)
    if finalized != new:
        new = finalized
        reasons.append("a_ver_que")

    cleaned = MULTISPACE_RE.sub(" ", new).strip()
    if cleaned != new:
        new = cleaned
        reasons.append("multispace")

    return new, sorted(set(reasons))


def main() -> None:
    rows = []
    report = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            source = row.get("Fuente") or ""
            if source and source != "2021 Wimmer":
                old = row.get("Traducción") or ""
                new, reasons = clean(old, source)
                if new != old:
                    row["Traducción"] = new
                    report.append(
                        {
                            "record_id": row.get("record_id"),
                            "source": source,
                            "lemma": row.get("Texto estandarizado"),
                            "reasons": reasons,
                            "old_translation": old,
                            "new_translation": new,
                        }
                    )
            rows.append(row)

    if not DRY_RUN:
        tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        os.replace(tmp, DATA_PATH)

        with REPORT_PATH.open("w", encoding="utf-8") as fh:
            for item in report:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(report)}")
    print(f"report={REPORT_PATH if not DRY_RUN else '(dry-run)'}")


if __name__ == "__main__":
    main()
