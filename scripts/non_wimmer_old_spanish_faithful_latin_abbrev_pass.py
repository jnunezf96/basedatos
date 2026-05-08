#!/usr/bin/env python3
from __future__ import annotations

import difflib
import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
SOURCE_REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_latin_abbrev_report.jsonl"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_faithful_latin_abbrev_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
WORD_RE = re.compile(rf"[{LETTER}]+")


def words(value: str) -> list[re.Match[str]]:
    return list(WORD_RE.finditer(value or ""))


def lower_words(matches: list[re.Match[str]]) -> list[str]:
    return [match.group(0).lower() for match in matches]


def index_map(report_new_words: list[str], current_words: list[str]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    matcher = difflib.SequenceMatcher(None, report_new_words, current_words, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                mapping[i1 + offset] = j1 + offset
        elif tag == "replace" and (i2 - i1) == (j2 - j1):
            for offset in range(i2 - i1):
                mapping[i1 + offset] = j1 + offset
    return mapping


def mapped_span(
    current_matches: list[re.Match[str]],
    mapping: dict[int, int],
    report_start_index: int,
    report_word_count: int,
) -> tuple[int, int] | None:
    mapped = [mapping.get(index) for index in range(report_start_index, report_start_index + report_word_count)]
    if any(index is None for index in mapped):
        return None
    current_indexes = [int(index) for index in mapped]
    if current_indexes != list(range(current_indexes[0], current_indexes[0] + len(current_indexes))):
        return None
    return current_matches[current_indexes[0]].start(), current_matches[current_indexes[-1]].end()


def latin_case(old_token: str, value: str) -> str:
    if old_token[:1].isupper():
        return value[:1].upper() + value[1:]
    return value


def add_replacement(
    replacements: list[dict[str, object]],
    start: int,
    end: int,
    replacement: str,
    reason: str,
) -> None:
    replacements.append(
        {
            "start": start,
            "end": end,
            "replacement": replacement,
            "reason": reason,
        }
    )


def replace_terminal_period(current: str, replacement: str) -> tuple[str, list[dict[str, object]]]:
    stripped = current.rstrip()
    trailing = current[len(stripped) :]
    if stripped.endswith("."):
        start = len(stripped) - 1
        return (
            current[:start].rstrip() + replacement + "." + trailing,
            [{"start": start, "end": len(stripped), "replacement": replacement + ".", "reason": "trailing_vel"}],
        )
    return current.rstrip() + replacement + trailing, [
        {"start": len(stripped), "end": len(stripped), "replacement": replacement, "reason": "trailing_vel"}
    ]


def restore(current: str, old_report: str, new_report: str, reasons: list[str]) -> tuple[str, list[dict[str, object]], str | None]:
    if "(latín:" in (current or ""):
        return current, [], "already_annotated"

    old_matches = words(old_report)
    new_matches = words(new_report)
    current_matches = words(current)
    old_lowers = lower_words(old_matches)
    new_lowers = lower_words(new_matches)
    current_lowers = lower_words(current_matches)
    mapping = index_map(new_lowers, current_lowers)
    replacements: list[dict[str, object]] = []

    reason_set = set(reasons)

    if "vel_aut" in reason_set:
        old_lower = (old_report or "").lower()
        if old_lower.startswith("vel, aut") and current_lowers == ["o"]:
            return f"{latin_case(old_report.strip(), 'vel, aut')} (latín: o)", [
                {"start": 0, "end": len(current), "replacement": "Vel, aut (latín: o)", "reason": "vel_aut"}
            ], None
        if "conjuncion disjunctiva" in old_lower:
            if "vel, aut conjuncion" in old_lower:
                new = re.sub(
                    r"\bo,\s*(conjunci[oó]n disjunctiva)\b",
                    r"o, vel, aut (latín: o), \1",
                    current,
                    flags=re.I,
                )
            else:
                new = re.sub(
                    r"\bo,\s*(conjunci[oó]n disjunctiva)\b",
                    r"o, \1, vel, aut (latín: o)",
                    current,
                    flags=re.I,
                )
            if new != current:
                return new, [{"start": 0, "end": len(current), "replacement": new, "reason": "vel_aut"}], None
        if old_lower.startswith("o, latin. aut, vel") and current_lowers == ["o"]:
            return "o, latin. aut, vel (latín: o)", [
                {"start": 0, "end": len(current), "replacement": "o, latin. aut, vel (latín: o)", "reason": "vel_aut"}
            ], None
        if old_lower.startswith("o, vel, aut") and current_lowers == ["o"]:
            return "o, vel, aut (latín: o)", [
                {"start": 0, "end": len(current), "replacement": "o, vel, aut (latín: o)", "reason": "vel_aut"}
            ], None
        return current, [], "vel_aut_unhandled"

    if "trailing_vel" in reason_set:
        new, trailing_replacements = replace_terminal_period(current, "; vel (latín: o)")
        return new, trailing_replacements, None

    if "lo_mesmo_vel" in reason_set:
        try:
            old_index = old_lowers.index("vel")
        except ValueError:
            return current, [], "vel_not_found"
        next_old = old_lowers[old_index + 1] if old_index + 1 < len(old_lowers) else ""
        current_index = current_lowers.index(next_old) if next_old in current_lowers else None
        if current_index is None:
            return current, [], "lo_mesmo_target_not_found"
        start = current_matches[current_index].start()
        add_replacement(replacements, start, start, "vel (latín: o) ", "lo_mesmo_vel")

    if "o_vel_o" in reason_set:
        new = re.sub(r"^\s*o,\s*", "o, vel o (latín: o), ", current, flags=re.I)
        if new != current:
            return new, [{"start": 0, "end": len(current), "replacement": new, "reason": "o_vel_o"}], None
        return current, [], "o_vel_o_unhandled"

    if "guai_vel_o" in reason_set:
        new = re.sub(r"\bguai,\s*o\b", "guai, vel o (latín: o)", current, flags=re.I)
        if new != current:
            return new, [{"start": 0, "end": len(current), "replacement": new, "reason": "guai_vel_o"}], None
        return current, [], "guai_vel_o_unhandled"

    if "o_vel_quisas" in reason_set:
        new = re.sub(r"\bO\s+quisas\b", "O vel (latín: o) quisas", current)
        if new != current:
            return new, [{"start": 0, "end": len(current), "replacement": new, "reason": "o_vel_quisas"}], None
        return current, [], "o_vel_quisas_unhandled"

    for index, token in enumerate(old_lowers):
        if token == "scil":
            span = mapped_span(current_matches, mapping, index, 2)
            if not span or new_lowers[index : index + 2] != ["es", "decir"]:
                return current, [], "scil_alignment_mismatch"
            add_replacement(
                replacements,
                span[0],
                span[1],
                f"{latin_case(old_matches[index].group(0), 'scil.')} (latín: es decir)",
                "scil",
            )
        elif token == "vel":
            next_token = old_lowers[index + 1] if index + 1 < len(old_lowers) else ""
            if next_token == "ante":
                span = mapped_span(current_matches, mapping, index, 2)
                if not span or new_lowers[index : index + 2] != ["o", "antes"]:
                    return current, [], "vel_ante_alignment_mismatch"
                add_replacement(replacements, span[0], span[1], "vel ante (latín: o antes)", "vel_ante")
            elif next_token in {"simile", "similiter", "bimile"}:
                span = mapped_span(current_matches, mapping, index, 3)
                if not span or new_lowers[index : index + 3] != ["o", "cosa", "semejante"]:
                    return current, [], "vel_simile_alignment_mismatch"
                display = "vel similiter" if next_token == "similiter" else "vel simile"
                add_replacement(replacements, span[0], span[1], f"{display} (latín: o cosa semejante)", "vel_simile")
            elif next_token == "masque":
                span = mapped_span(current_matches, mapping, index, 3)
                if not span or new_lowers[index : index + 3] != ["o", "más", "que"]:
                    return current, [], "vel_masque_alignment_mismatch"
                add_replacement(replacements, span[0], span[1], "vel masque (latín: o más que)", "vel_masque")
            elif "vel" in reason_set or "spacing" in reason_set:
                span = mapped_span(current_matches, mapping, index, 1)
                if not span or new_lowers[index : index + 1] != ["o"]:
                    return current, [], "vel_alignment_mismatch"
                add_replacement(
                    replacements,
                    span[0],
                    span[1],
                    f"{latin_case(old_matches[index].group(0), 'vel')} (latín: o)",
                    "vel",
                )

    if not replacements:
        return current, [], "no_latin_marker"

    replacements.sort(key=lambda item: (int(item["start"]), int(item["end"])))
    last_end = -1
    for item in replacements:
        if int(item["start"]) < last_end:
            return current, [], "overlapping_replacements"
        last_end = int(item["end"])

    updated = current
    for item in reversed(replacements):
        start = int(item["start"])
        end = int(item["end"])
        updated = updated[:start] + str(item["replacement"]) + updated[end:]
    return updated, replacements, None


def main() -> None:
    report_inputs = {}
    with SOURCE_REPORT_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            report_inputs[item["record_id"]] = item

    rows = []
    report = []
    skipped = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            record_id = row.get("record_id") or ""
            source_item = report_inputs.get(record_id)
            if source_item:
                old = row.get("Traducción") or ""
                new, replacements, skip_reason = restore(
                    old,
                    source_item.get("old_translation") or "",
                    source_item.get("new_translation") or "",
                    source_item.get("reasons") or [],
                )
                if new != old:
                    row["Traducción"] = new
                    report.append(
                        {
                            "record_id": record_id,
                            "source": row.get("Fuente"),
                            "lemma": row.get("Texto estandarizado"),
                            "old_translation": old,
                            "new_translation": new,
                            "replacements": [
                                {
                                    "reason": item["reason"],
                                    "replacement": item["replacement"],
                                }
                                for item in replacements
                            ],
                        }
                    )
                elif skip_reason and skip_reason != "already_annotated":
                    skipped.append(
                        {
                            "record_id": record_id,
                            "source": row.get("Fuente"),
                            "lemma": row.get("Texto estandarizado"),
                            "reason": skip_reason,
                            "current_translation": old,
                            "report_old_translation": source_item.get("old_translation"),
                            "report_new_translation": source_item.get("new_translation"),
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

        skipped_path = REPORT_PATH.with_name(REPORT_PATH.stem + "_skipped.jsonl")
        with skipped_path.open("w", encoding="utf-8") as fh:
            for item in skipped:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(report)}")
    print(f"skipped_rows={len(skipped)}")
    print(f"report={REPORT_PATH if not DRY_RUN else '(dry-run)'}")


if __name__ == "__main__":
    main()
