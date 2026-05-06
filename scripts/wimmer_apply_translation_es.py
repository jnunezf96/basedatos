"""Apply conservative 2021 Wimmer `Traducción (es)` proposals.

The source text remains unchanged. This rewrites only the rendered
`Traducción (es)` field for 2021 Wimmer rows whose current Spanish translation
is contaminated by grammar/source/form material and whose comment-derived
proposal validates as Spanish-only.

Run without --write for a dry report. Run with --write to update data.jsonl.gz.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path

import wimmer_translation_pilot as pilot


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "data.jsonl.gz"
REPORT_JSONL = ROOT / "scripts" / "wimmer_translation_es_apply_report.jsonl"
REPORT_TXT = ROOT / "scripts" / "wimmer_translation_es_apply_report.txt"


APPLY_OLD_RE = re.compile(
    r"\b(?:v\.|tla-|t[ēêe]-|motla-|mot[ēêe]-|t[ēêe]tla-|"
    r"forma\s+pose[ií]da|plural\.?|met[aá]fora|bot[aá]nica|calendario|"
    r"ornitolog[ií]a|top[oó]nimo|Sah|SIS|Launey|Molina|Rammow|"
    r"algo:|persona:|reflexivo:|pasivo:|impersonal:|intransitivo:|"
    r"transitivo:|rec[ií]proco:|sujeto\s+inanimado:|bitransitivo:)\b",
    re.IGNORECASE,
)
COMPACT_LABEL_RE = re.compile(
    r"\b(?:algo|persona|persona/algo|persona\s+\+\s+algo|reflexivo|"
    r"reflexivo\s+\+\s+algo|reflexivo\s+\+\s+persona|pasivo|pasivo\s+impersonal|"
    r"impersonal|intransitivo|transitivo|rec[ií]proco|sujeto\s+inanimado|"
    r"bitransitivo)\s*:",
    re.IGNORECASE,
)
GRAMMAR_PREFIX_RE = re.compile(
    r"^\s*(?:/?\s*)?(?:"
    r"v\.[^,.;/]*|"
    r"plur(?:al)?\.?|"
    r"pasivo(?:\s+e\s+impers\.)?|"
    r"en\s+la\s+forma\s+pose[ií]da|"
    r"a\s+la\s+forma\s+pose[ií]da|"
    r"forma\s+pose[ií]da|"
    r"con\s+pref\.[^,.;/]*|"
    r"con\s+prefijo[^,.;/]*|"
    r"algo|persona(?:/algo)?|persona\s+\+\s+algo|reflexivo(?:\s+\+\s+(?:algo|persona))?|"
    r"pasivo(?:\s+impersonal)?|impersonal|intransitivo|transitivo|rec[ií]proco|"
    r"sujeto\s+inanimado|bitransitivo"
    r")\s*[,.;:]?\s*",
    re.IGNORECASE,
)


def load_previous_old_translations() -> dict[str, str]:
    if not REPORT_JSONL.exists():
        return {}
    old_by_id: dict[str, str] = {}
    try:
        with REPORT_JSONL.open("r", encoding="utf-8") as fin:
            for line in fin:
                if not line.strip():
                    continue
                row = json.loads(line)
                record_id = row.get("record_id")
                old = row.get("old_translation_es")
                if record_id and old:
                    old_by_id[record_id] = old
    except (OSError, json.JSONDecodeError):
        return {}
    return old_by_id


def load_wimmer_rows() -> list[dict]:
    rows: list[dict] = []
    with gzip.open(DATA, "rt", encoding="utf-8") as fin:
        for line in fin:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("Fuente") == "2021 Wimmer":
                rows.append(row)
    return rows


def old_meaning_text(old: str) -> str:
    parts: list[str] = []
    for segment in pilot.translation_segments(old):
        cleaned = segment
        previous = None
        while previous != cleaned:
            previous = cleaned
            cleaned = GRAMMAR_PREFIX_RE.sub("", cleaned)
        cleaned = re.sub(r"^[A-Z]\.\s*~\s*", "", cleaned)
        cleaned = re.sub(r"^~\s*[^,.;/]*[,.;]?\s*", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.;:")
        if not cleaned:
            continue
        if pilot.NAHUATL_MARK_RE.search(cleaned) and pilot.word_count(cleaned) <= 4:
            continue
        if pilot.is_bad_definition(cleaned) and pilot.word_count(cleaned) <= 4:
            continue
        parts.append(cleaned)
    return " / ".join(parts)


def semantically_close_to_old(row: dict, proposal: str) -> bool:
    old = row.get("Traducción (es)") or row.get("Traducción") or ""
    old_meaning = old_meaning_text(old)
    if pilot.word_count(old_meaning) < 2:
        return True
    score = pilot.overlap_score(proposal, old_meaning)
    if score >= 0.18:
        return True
    # If the current field was almost entirely metadata, the old text is not a
    # useful semantic anchor.
    if pilot.contamination_score(row) >= 10 and pilot.word_count(old_meaning) <= 3:
        return True
    return False


def should_apply(row: dict, proposal: str, errors: list[str]) -> bool:
    if errors:
        return False
    old = row.get("Traducción (es)") or row.get("Traducción") or ""
    if not pilot.changed(old, proposal):
        return False
    if not semantically_close_to_old(row, proposal):
        return False
    if pilot.contamination_score(row) > 0:
        return True
    return bool(APPLY_OLD_RE.search(old) or COMPACT_LABEL_RE.search(old))


def build_updates() -> tuple[list[dict], dict[str, str], int]:
    previous_old = load_previous_old_translations()
    source_rows = load_wimmer_rows()
    if previous_old:
        restored_rows: list[dict] = []
        for row in source_rows:
            old = previous_old.get(row.get("record_id", ""))
            if old is not None:
                row = row.copy()
                row["Traducción (es)"] = old
            restored_rows.append(row)
        source_rows = restored_rows
    model = pilot.build_corpus_model(source_rows)
    report_rows: list[dict] = []
    updates: dict[str, str] = dict(previous_old)
    for row in source_rows:
        proposal, snippets, reason = pilot.extract_corpus_proposal(row, model)
        errors = pilot.validate_proposal(row, proposal)
        if not should_apply(row, proposal, errors):
            continue
        record_id = row.get("record_id", "")
        old = row.get("Traducción (es)") or row.get("Traducción") or ""
        updates[record_id] = proposal
        report_rows.append(
            {
                "record_id": record_id,
                "eid": row.get("eid", ""),
                "lemma": row.get("Texto estandarizado", ""),
                "old_translation_es": old,
                "new_translation_es": proposal,
                "reason": reason,
                "old_word_count": pilot.word_count(old),
                "new_word_count": pilot.word_count(proposal),
                "contamination_score": pilot.contamination_score(row),
                "source_snippets": snippets,
            }
        )
    restored_count = max(0, len(previous_old) - len({row["record_id"] for row in report_rows}))
    return report_rows, updates, restored_count


def write_report(report_rows: list[dict], *, write_mode: bool) -> None:
    with REPORT_JSONL.open("w", encoding="utf-8") as fout:
        for row in report_rows:
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")

    lines = [
        "# 2021 Wimmer Traducción (es) Apply Report",
        f"# mode: {'write' if write_mode else 'dry-run'}",
        f"# rows: {len(report_rows)}",
        "",
    ]
    sep = "=" * 80
    for idx, row in enumerate(report_rows[:250], 1):
        lines.append(sep)
        lines.append(f"{idx:03d}. {row['lemma']} [{row['record_id']}]")
        lines.append(
            f"REASON: {row['reason']}  old_wc={row['old_word_count']}  "
            f"new_wc={row['new_word_count']}  risk={row['contamination_score']}"
        )
        lines.append(f"OLD   : {row['old_translation_es']}")
        lines.append(f"NEW   : {row['new_translation_es']}")
        for snippet in row["source_snippets"][:4]:
            lines.append(f"SOURCE: {snippet}")
        lines.append("")
    if len(report_rows) > 250:
        lines.append(sep)
        lines.append(f"... {len(report_rows) - 250} more rows in {REPORT_JSONL.name}")
    REPORT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_updates(updates: dict[str, str]) -> None:
    tmp = DATA.with_suffix(".jsonl.gz.tmp")
    with gzip.open(DATA, "rt", encoding="utf-8") as fin, gzip.open(tmp, "wt", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            row = json.loads(line)
            update = updates.get(row.get("record_id", ""))
            if update is not None:
                row["Traducción (es)"] = update
            fout.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    tmp.replace(DATA)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply 2021 Wimmer Spanish translation cleanup.")
    parser.add_argument("--write", action="store_true", help="rewrite data/data.jsonl.gz")
    parser.add_argument("--max-updates", type=int, help="abort if more rows would change")
    args = parser.parse_args()

    report_rows, updates, restored_count = build_updates()
    if args.max_updates is not None and len(updates) > args.max_updates:
        write_report(report_rows, write_mode=False)
        raise SystemExit(f"aborted: {len(updates)} updates exceeds --max-updates={args.max_updates}")
    if args.write:
        apply_updates(updates)
    write_report(report_rows, write_mode=args.write)
    print(f"updates={len(report_rows)} restores={restored_count} mode={'write' if args.write else 'dry-run'}")
    print(f"report={REPORT_TXT.relative_to(ROOT)}")
    print(f"jsonl={REPORT_JSONL.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
