#!/usr/bin/env python3
"""Clean person/object markers preserved by the + decondensation pass.

The + pass expanded entries such as "cochi +" with context from the original
phrase. In some rows that also preserved conjugation notation attached to the
head, yielding forms such as "tetlan nicochi" where the intended rendered head
is "tetlan cochi".

This pass only edits rendered data (`Texto estandarizado`). It uses the prior
plus report as evidence: if the old condensed head is a single token and the new
rendered form contains that same token with a known person/object marker
attached, replace the marked token with the old head.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
PLUS_REPORT_PATH = Path("scripts/edition_plus_decondense_report.jsonl")
REPORT_PATH = Path("scripts/edition_attached_marker_cleanup_report.jsonl")

TEXT_FIELD = "Texto estandarizado"
ID_FIELD = "record_id"

# Longest first so "nitlatla..." is not consumed as "ni...".
MARKER_PREFIXES = (
    "ninotla",
    "ninote",
    "nitlatla",
    "ninoc",
    "nino",
    "nitla",
    "nite",
    "nito",
    "nic",
    "nin",
    "ni",
    "n",
)

MIN_AUTO_HEAD_LENGTH = 4

# Duplicates/mirror rows that did not come through the current + report, plus
# rows where comma/spacing left a marker outside the evidence replacement.
CURATED_FIXES = {
    "1571-molina-1:007893": ("tetlan nactiuh", "tetlan actiuh", "curated bare n + actiuh"),
    "1571-molina-1:014540": ("itlan nicaana", "itlan aana", "curated attached nic + aana"),
    "1571-molina-1:014541": ("itlan nino quetzticac", "itlan quetzticac", "curated reflexive marker + quetzticac"),
    "1571-molina-1:014656": ("itzalan nicaana", "itzalan aana", "curated attached nic + aana"),
    "1571-molina-1:021365": ("itlan naqui", "itlan aqui", "curated bare n + aqui"),
    "1571-molina-1:021366": ("tetlan naqui", "tetlan aqui", "curated bare n + aqui"),
    "1571-molina-1:021368": ("itlan naqui", "itlan aqui", "curated bare n + aqui"),
    "1571-molina-1:021373": ("tetlan nicatiuh", "tetlan icatiuh", "curated attached ni + icatiuh"),
    "1571-molina-2:010342": ("itlan nicaana", "itlan aana", "curated attached nic + aana"),
    "1571-molina-2:010343": ("itlan ninoquetzticac", "itlan quetzticac", "curated reflexive marker + quetzticac"),
    "1571-molina-2:014945": ("itlan naqui", "itlan aqui", "curated bare n + aqui"),
    "1780-bnf-361:001805": ("tlatzintlan nica", "tlatzintlan ca", "mirror attached ni + ca"),
    "1780-bnf-361:005036": ("cemicac nica", "cemicac ca", "mirror attached ni + ca"),
    "1780-bnf-361:019673": ("achi tetlan, nica", "achi tetlan ca", "mirror attached ni + ca"),
    "1780-bnf-361:021831": ("tetlannicalactiuh", "tetlan calactiuh", "mirror fused tetlan + ni"),
    "1780-bnf-361:021776": ("tetlan nicatiuh", "tetlan icatiuh", "mirror attached ni + icatiuh"),
    "1780-bnf-361:021252": ("tetech nicana", "tetech ana", "mirror attached nic + ana"),
}

# Corrections for data already touched by an earlier version of this pass.
CURATED_CORRECTIONS = {
    "153-trilingue:009731": ("itzalan caana", "itzalan aana", "curated nicaána + aana"),
    "1571-molina-1:036114": ("cana", "ana", "translation context: verbal ana"),
    "1571-molina-1:036115": ("cana", "ana", "translation context: verbal ana"),
    "1571-molina-1:036124": ("nihio cana", "nihio ana", "translation context: verbal ana"),
    "1571-molina-1:036125": ("nihio cana", "nihio ana", "translation context: verbal ana"),
    "1571-molina-1:036126": ("tetech cana", "tetech ana", "translation context: verbal ana"),
    "1571-molina-1:036127": ("tetech cana", "tetech ana", "translation context: verbal ana"),
    "1571-molina-1:036128": ("itlan cana", "itlan ana", "translation context: verbal ana"),
    "1571-molina-1:036129": ("itzalan cana", "itzalan ana", "translation context: verbal ana"),
    "1571-molina-2:024113": ("cana", "ana", "translation context: verbal ana"),
    "1571-molina-2:024119": ("itlan cana", "itlan ana", "translation context: verbal ana"),
    "1571-molina-2:024120": ("tetech cana", "tetech ana", "translation context: verbal ana"),
    "1780-bnf-361:015068": ("nihio cana", "nihio ana", "translation context: verbal ana"),
    "1780-bnf-361:021252": ("tetech cana", "tetech ana", "translation context: verbal ana"),
    "1571-molina-1:014540": ("itlan caana", "itlan aana", "correct earlier nicaana target"),
    "1571-molina-1:014656": ("itzalan caana", "itzalan aana", "correct earlier nicaana target"),
    "1571-molina-2:010342": ("itlan caana", "itlan aana", "correct earlier nicaana target"),
}


def old_head_token(old_edition: str) -> str | None:
    """Return a single old condensed head token, or None if not simple."""

    text = old_edition.replace("+", " ").replace("=", " ")
    tokens = re.findall(r"[a-z]+", text.lower())
    if len(tokens) != 1:
        return None
    return tokens[0]


def marker_stripped_token(token: str, head: str) -> tuple[str, str] | None:
    lower = token.lower()
    for marker in MARKER_PREFIXES:
        if lower.startswith(marker) and lower[len(marker) :] == head:
            return head, marker
    return None


def safe_automatic_replacement(token: str, head: str) -> tuple[str, str] | None:
    """Return (replacement, marker) when an automatic replacement is safe.

    Bare n- before a vowel is a real phenomenon in the bad expansions, but it
    is also where false positives cluster (`namiqui`, `nehua`, etc.). Keep those
    for curated/contextual passes.
    """

    if token == "nica" and head == "ica":
        return "ca", "ni-ca"

    stripped = marker_stripped_token(token, head)
    if not stripped:
        return None
    _, marker = stripped
    if marker == "n":
        return None
    if len(head) < MIN_AUTO_HEAD_LENGTH:
        return None
    return head, marker


def replacement_plan_from_plus_report(
    path: Path,
) -> tuple[dict[str, dict[str, object]], dict[str, str]]:
    plans: dict[str, dict[str, object]] = {}
    mirror_replacements: dict[str, str] = {}
    if not path.exists():
        return plans, mirror_replacements

    with path.open(encoding="utf-8") as f:
        for line in f:
            report = json.loads(line)
            record_id = report.get("record_id")
            old_edition = report.get("old_edition") or ""
            new_edition = report.get("new_edition") or ""
            head = old_head_token(old_edition)
            if not record_id or not head:
                continue

            replacements: list[dict[str, str]] = []
            for match in re.finditer(r"\b[a-z]+\b", new_edition):
                token = match.group(0)
                replacement = safe_automatic_replacement(token, head)
                if replacement:
                    new_token, marker = replacement
                    replacements.append(
                        {
                            "token": token,
                            "replacement": new_token,
                            "marker": marker,
                        }
                    )

            if replacements:
                corrected = apply_replacements(new_edition, replacements)
                plans[record_id] = {
                    "head": head,
                    "old_edition": old_edition,
                    "plus_new_edition": new_edition,
                    "replacements": replacements,
                }
                if corrected != new_edition:
                    mirror_replacements[new_edition] = corrected
    return plans, mirror_replacements


def apply_replacements(text: str, replacements: list[dict[str, str]]) -> str:
    new_text = text
    for repl in replacements:
        token = repl["token"]
        replacement = repl["replacement"]
        new_text = re.sub(rf"\b{re.escape(token)}\b", replacement, new_text)
    new_text = new_text.replace(",", "")
    new_text = re.sub(r"\s+", " ", new_text).strip()
    return new_text


def load_rows(path: Path) -> list[dict[str, object]]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = load_rows(DATA_PATH)
    plans, mirror_replacements = replacement_plan_from_plus_report(PLUS_REPORT_PATH)
    report_rows: list[dict[str, object]] = []
    changed = 0

    for row in rows:
        record_id = str(row.get(ID_FIELD) or "")
        old_text = str(row.get(TEXT_FIELD) or "")
        new_text = old_text
        reasons: list[str] = []
        detail: dict[str, object] = {}

        if record_id in plans:
            plan = plans[record_id]
            replacements = plan["replacements"]  # type: ignore[index]
            assert isinstance(replacements, list)
            proposed = apply_replacements(old_text, replacements)  # type: ignore[arg-type]
            if proposed != old_text:
                new_text = proposed
                reasons.append("plus_report_attached_marker")
                detail["plus_plan"] = plan

        if (
            not reasons
            and str(row.get("Fuente") or "") == "1780 ? Bnf_361"
            and old_text in mirror_replacements
        ):
            new_text = mirror_replacements[old_text]
            reasons.append("mirror_exact_plus_attached_marker")

        if record_id in CURATED_FIXES:
            expected, replacement, reason = CURATED_FIXES[record_id]
            if new_text == expected:
                new_text = replacement
                reasons.append(reason)
            elif old_text == expected:
                new_text = replacement
                reasons.append(reason)
            elif expected in new_text:
                new_text = new_text.replace(expected, replacement)
                reasons.append(reason)
            detail["curated_expected"] = expected

        if record_id in CURATED_CORRECTIONS:
            expected, replacement, reason = CURATED_CORRECTIONS[record_id]
            if new_text == expected:
                new_text = replacement
                reasons.append(reason)
            elif old_text == expected:
                new_text = replacement
                reasons.append(reason)
            detail["curated_correction_expected"] = expected

        if new_text != old_text:
            changed += 1
            report_rows.append(
                {
                    "record_id": record_id,
                    "source": row.get("Fuente"),
                    "original": row.get("Escritura original"),
                    "old_edition": old_text,
                    "new_edition": new_text,
                    "translation": row.get("Traducción"),
                    "reasons": reasons,
                    **detail,
                }
            )
            if args.apply:
                row[TEXT_FIELD] = new_text

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        for report_row in report_rows:
            f.write(json.dumps(report_row, ensure_ascii=False, separators=(",", ":")) + "\n")

    if args.apply and changed:
        write_rows(DATA_PATH, rows)

    summary = {
        "apply": args.apply,
        "changed_rows": changed,
        "report": str(REPORT_PATH),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
