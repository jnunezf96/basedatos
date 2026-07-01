#!/usr/bin/env python3
"""Repair the Sahagun Escolios P_160v numbered-gloss cluster."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import repair_sahagun_internal_coherence as coherence


DATA_PATH = Path("data/data.jsonl.gz")
AUDIT_PATH = Path("resources/sahagun_internal_coherence_audit.tsv")
PROPOSALS_PATH = Path("resources/sahagun_p160v_cluster_repair_proposals.tsv")
SUMMARY_PATH = Path("resources/sahagun_p160v_cluster_repair_summary.json")
SOURCE = coherence.SOURCE
MARKER = "sahagun_p160v_cluster_repair_2026_06_29"
FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]


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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_marker(value: object, marker: str) -> list[str]:
    if isinstance(value, list):
        items = [str(item) for item in value]
    elif value:
        items = [str(value)]
    else:
        items = []
    if marker not in items:
        items.append(marker)
    return items


def target_missing_ids(audit_path: Path) -> set[str]:
    ids: set[str] = set()
    with audit_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("issue_type") == "target_number_missing_from_witness":
                ids.add(row.get("record_id", ""))
    return ids


def adjacent_text(unit: str, number: int) -> str:
    span = coherence.target_number_adjacent_span(unit, number)
    return unit[span[0] : span[1]] if span else ""


def unit_for_number(packet: coherence.Packet, number: int) -> str:
    for unit in coherence.split_occurrence_units(packet.witness):
        if number in coherence.numbers_in(unit):
            return unit
    return ""


def score_candidate(row: dict, packet: coherence.Packet, number: int, gloss: str) -> tuple[float, dict[str, str]]:
    unit = unit_for_number(packet, number)
    adjacent = adjacent_text(unit, number)
    forms = coherence.target_forms(row) | coherence.forms_from_value(packet.header)
    form_similarity = coherence.form_similarity(forms, adjacent)
    overlap = coherence.text_words(row.get("Traducción", "")) & coherence.text_words(gloss)
    header_overlap = coherence.text_words(packet.header) & coherence.text_words(gloss)

    score = 0.0
    score += 25 * len(overlap)
    score += 25 * len(header_overlap)
    score += 40 * form_similarity
    if number == coherence.target_number(row):
        score += 5
    return score, {
        "new_target_number": str(number),
        "occurrence_unit": unit,
        "adjacent_text": adjacent,
        "form_similarity": f"{form_similarity:.3f}",
        "translation_overlap": ",".join(sorted(overlap)),
        "header_overlap": ",".join(sorted(header_overlap)),
        "target_gloss": gloss,
    }


def selected_packet(row: dict) -> coherence.Packet | None:
    for packet in coherence.parse_packets(row.get("Comentario_raw_1565_sahagun_escolios", "")):
        if packet.citation_raw != "P_160v":
            continue
        numbers = {number for number, _ in packet.glosses}
        if set(range(11, 23)).issubset(numbers) and set(coherence.public_witness_numbers(row)) == {7, 8, 9, 10}:
            return packet
    return None


def proposal_for_row(row: dict) -> dict[str, str] | None:
    packet = selected_packet(row)
    if not packet:
        return None
    scored: list[tuple[float, dict[str, str]]] = []
    for number, gloss in packet.glosses:
        if 11 <= number <= 22:
            score, evidence = score_candidate(row, packet, number, gloss)
            scored.append((score, evidence))
    scored.sort(key=lambda item: item[0], reverse=True)
    if len(scored) < 2:
        return None
    best_score, best = scored[0]
    second_score = scored[1][0]
    if best_score < 60 or best_score - second_score < 8:
        return None

    number = int(best["new_target_number"])
    unit_numbers = [n for n in coherence.numbers_in(best["occurrence_unit"]) if 7 <= n <= 22]
    gloss_lookup = {n: g for n, g in packet.glosses}
    gloss_numbers = [n for n in unit_numbers if n in gloss_lookup]
    if number not in gloss_numbers:
        gloss_numbers.append(number)
    best["gloss_numbers"] = ",".join(map(str, gloss_numbers))
    best["score"] = f"{best_score:.3f}"
    best["second_score"] = f"{second_score:.3f}"
    best["record_id"] = row.get("record_id", "")
    best["original"] = row.get("Original", "")
    best["editado"] = row.get("Editado", "")
    best["old_target_number"] = str(coherence.target_number(row) or "")
    best["translation"] = row.get("Traducción", "")
    best["citation"] = packet.citation_raw
    return best


def build_commentary(row: dict, packet: coherence.Packet, proposal: dict[str, str]) -> tuple[str, str, str]:
    number = int(proposal["new_target_number"])
    lemma = coherence.clean_space(str(row.get("Editado") or row.get("Original") or ""))
    definition = coherence.normalize_spanishish(proposal["target_gloss"]).rstrip(" ;.")
    witness = coherence.normalize_nahuatl(proposal["occurrence_unit"]).rstrip(" .:")
    witness = coherence.bold_target(witness, row, number)
    witness_line = f"<i>{witness}</i>."
    if packet.citation_raw:
        witness_line += f" {coherence.normalized_citation(packet.citation_raw)}"
    gloss_lookup = {n: coherence.normalize_spanishish(g).rstrip(" ;.") for n, g in packet.glosses}
    gloss_lines = []
    for gloss_number in [int(value) for value in proposal["gloss_numbers"].split(",") if value]:
        if gloss_number in gloss_lookup:
            gloss_lines.append(f"({gloss_number}) {gloss_lookup[gloss_number]};")
    commentary = (
        f"{lemma}.<br/><br/>{definition}<br/><br/>"
        f"{witness_line}<br/><br/>"
        f"Glosas relevantes del escolio:<br/>"
        + "<br/>".join(gloss_lines)
        + "<br/>"
    )
    return commentary, witness_line, definition


def apply_proposal(row: dict, proposal: dict[str, str]) -> None:
    packet = selected_packet(row)
    if not packet:
        return
    old_number = coherence.target_number(row)
    new_number = int(proposal["new_target_number"])
    previous_commentary = str(row.get("Comentario", ""))
    commentary, witness_line, definition = build_commentary(row, packet, proposal)
    for field in FIELDS:
        row[field] = commentary

    metadata = row.get("Sahagun_Escolios_JSON") if isinstance(row.get("Sahagun_Escolios_JSON"), dict) else {}
    old_raw = metadata.get("target_number_raw") or str(old_number or "")
    previous_alignment = metadata.get("target_alignment_v34_1") if isinstance(metadata.get("target_alignment_v34_1"), dict) else {}
    metadata["target_number_base"] = new_number
    metadata["target_number_raw"] = str(new_number)
    alignment = metadata.setdefault("target_alignment_v34_1", {})
    alignment["number_base"] = new_number
    alignment["number_raw"] = str(new_number)
    alignment["packet_header"] = packet.header
    alignment["repair_policy"] = MARKER

    display = metadata.get("display") if isinstance(metadata.get("display"), dict) else {}
    display["html"] = commentary
    display["display_witness_line"] = witness_line
    display["display_gloss"] = definition
    display["citation"] = coherence.citation_object(packet.citation_raw)
    display["lemma"] = coherence.clean_space(str(row.get("Editado") or row.get("Original") or ""))
    display["witness_count"] = 1
    display["issues"] = append_marker(display.get("issues"), MARKER)
    metadata["display"] = display

    metadata["qa_p160v_cluster_repair_2026_06_29"] = {
        "action": "rebuilt_public_fields_from_p160v_numbered_cluster",
        "marker": MARKER,
        "old_target_number_base": old_number,
        "old_target_number_raw": old_raw,
        "new_target_number_base": new_number,
        "new_target_number_raw": str(new_number),
        "score": proposal["score"],
        "second_score": proposal["second_score"],
        "adjacent_text": proposal["adjacent_text"],
        "translation_overlap": proposal["translation_overlap"].split(",") if proposal["translation_overlap"] else [],
        "header_overlap": proposal["header_overlap"].split(",") if proposal["header_overlap"] else [],
        "previous_commentary_sha1": hashlib.sha1(previous_commentary.encode("utf-8")).hexdigest(),
        "previous_alignment_sha1": hashlib.sha1(
            json.dumps(previous_alignment, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }
    row["Sahagun_Escolios_JSON"] = metadata
    row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--audit", type=Path, default=AUDIT_PATH)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    ids = target_missing_ids(args.audit)
    proposals: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in rows:
        if row.get("Fuente") != SOURCE or row.get("record_id", "") not in ids:
            continue
        proposal = proposal_for_row(row)
        if not proposal:
            continue
        proposals.append(proposal)
        counts["proposal_rows"] += 1
        if args.apply:
            apply_proposal(row, proposal)
            counts["applied_rows"] += 1

    write_tsv(
        args.proposals,
        proposals,
        [
            "record_id",
            "original",
            "editado",
            "old_target_number",
            "new_target_number",
            "score",
            "second_score",
            "adjacent_text",
            "form_similarity",
            "translation_overlap",
            "header_overlap",
            "gloss_numbers",
            "target_gloss",
            "occurrence_unit",
            "translation",
            "citation",
        ],
    )
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.apply and proposals:
        write_rows(args.data, rows)

    print("summary", dict(counts))
    print("proposals", args.proposals)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
