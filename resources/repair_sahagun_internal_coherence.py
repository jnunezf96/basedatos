#!/usr/bin/env python3
"""Repair Sahagun Escolios public commentary coherence.

The raw Escolios packet is preserved as evidence. This script only repairs
generated/public display fields when the current public commentary points away
from the row's stored target number. Ambiguous cases are written to a review
queue instead of being guessed.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import gzip
import hashlib
import html
import json
import os
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DATA_PATH = Path("data/data.jsonl.gz")
AUDIT_PATH = Path("resources/sahagun_internal_coherence_audit.tsv")
REVIEW_PATH = Path("resources/sahagun_internal_coherence_review.tsv")
PROPOSAL_PATH = Path("resources/sahagun_internal_coherence_proposals.tsv")
SOURCE = "1565 Sahagún Escolios"
REPAIR_MARKER = "raw_target_internal_coherence_repair_2026_06_29"
TARGET_BOLD_ISSUES = {
    "no_bold_in_comentario",
    "bold_text_no_target_token_overlap",
    "bold_nearest_number_mismatch",
}
SAFE_TARGET_BOLD_REBUILD_IDS = {
    "1565-sahagun-escolios:000081",
    "1565-sahagun-escolios:000146",
    "1565-sahagun-escolios:000163",
    "1565-sahagun-escolios:000250",
    "1565-sahagun-escolios:000269",
    "1565-sahagun-escolios:000411",
    "1565-sahagun-escolios:000414",
    "1565-sahagun-escolios:000485",
    "1565-sahagun-escolios:000500",
    "1565-sahagun-escolios:000643",
    "1565-sahagun-escolios:000658",
    "1565-sahagun-escolios:000692",
    "1565-sahagun-escolios:000733",
    "1565-sahagun-escolios:001003",
}
RAW_GLOSS_SUPPORTED_TARGET_BOLD_REBUILD_IDS = {
    "1565-sahagun-escolios:000130",
    "1565-sahagun-escolios:000177",
    "1565-sahagun-escolios:000637",
    "1565-sahagun-escolios:001090",
    "1565-sahagun-escolios:001313",
    "1565-sahagun-escolios:001474",
    "1565-sahagun-escolios:001503",
}

BR_RE = re.compile(r"<br\s*/?>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
BOLD_START_RE = re.compile(r"<b>\s*<i>", re.I)
BOLD_END_RE = re.compile(r"</i>\s*</b>", re.I)
BOLD_RE = re.compile(r"<b\b[^>]*>(.*?)</b>", re.I | re.S)
NUM_PARENS_RE = re.compile(r"\((\d+)((?:-\d+)?[+\-*]*)?\)")
GLOSS_LINE_RE = re.compile(
    r"(?m)^\s*(\d+)\s*(?::|：)?\s+(.*?)(?=\n\s*\d+\s*(?::|：)?\s+|\n\s*//|\n\s*\([A-Z]|$)",
    re.S,
)
PUBLIC_GLOSS_LINE_RE = re.compile(
    r"\((\d+)(?:-\d+)?[+\-*]?\)\s*(.*?)(?=(?:<br\s*/?>\s*\(\d+)|$)",
    re.I | re.S,
)
WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑÇáéíóúāēīōūüñç]+")


@dataclass
class Packet:
    header: str
    header_number: int | None
    header_number_raw: str | None
    witness: str
    glosses: list[tuple[int, str]]
    citation_raw: str


@dataclass
class Candidate:
    score: float
    packet: Packet
    occurrence: str
    occurrence_has_target_number: bool
    occurrence_has_target_form: bool
    target_definition: str
    reason: str


def html_to_text(value: str) -> str:
    value = BR_RE.sub("\n", str(value or ""))
    value = TAG_RE.sub(" ", value)
    return html.unescape(value)


def clean_space(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def strip_diacritics(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )


def text_words(value: str) -> set[str]:
    stop = {
        "pret",
        "pres",
        "persona",
        "cosa",
        "caso",
        "para",
        "como",
        "con",
        "los",
        "las",
        "una",
        "uno",
        "del",
        "que",
        "ca",
        "not",
        "notla",
        "idem",
        "este",
        "esta",
        "aqui",
        "pte",
        "pt",
    }
    text = strip_diacritics(html_to_text(str(value)).lower())
    return {word for word in re.findall(r"[a-záéíóúāēīōūñüç]+", text) if len(word) > 2 and word not in stop}


def form_key(value: str) -> str:
    text = html.unescape(str(value or "").lower()).replace("ç", "z")
    text = strip_diacritics(text)
    text = text.replace("v", "u")
    text = text.replace("hu", "u").replace("uh", "u")
    text = text.replace("qu", "k").replace("c", "k")
    return re.sub(r"[^a-z]+", "", text)


def target_forms(row: dict) -> set[str]:
    return forms_from_value(row.get("Editado", "")) | forms_from_value(row.get("Original", ""))


def forms_from_value(value: object) -> set[str]:
    forms: set[str] = set()
    for part in re.split(r"[,;/{}\[\]\s]+", str(value or "")):
        key = form_key(part)
        if len(key) >= 3:
            forms.add(key)
    return forms


def numbers_in(value: str) -> list[int]:
    return [int(match.group(1)) for match in NUM_PARENS_RE.finditer(str(value or ""))]


def public_witness_html(row: dict) -> str:
    return str(row.get("Comentario", "")).split("Glosas relevantes del escolio:", 1)[0]


def public_gloss_html(row: dict) -> str:
    value = str(row.get("Comentario", ""))
    if "Glosas relevantes del escolio:" not in value:
        return ""
    return value.split("Glosas relevantes del escolio:", 1)[1]


def public_gloss_numbers(row: dict) -> set[int]:
    return {int(match.group(1)) for match in PUBLIC_GLOSS_LINE_RE.finditer(public_gloss_html(row))}


def public_witness_numbers(row: dict) -> set[int]:
    return set(numbers_in(public_witness_html(row)))


def parse_packets(raw: str) -> list[Packet]:
    starts = list(BOLD_START_RE.finditer(raw or ""))
    packets: list[Packet] = []
    for index, start in enumerate(starts):
        end = BOLD_END_RE.search(raw, start.end())
        if not end:
            continue
        next_start = starts[index + 1].start() if index + 1 < len(starts) else len(raw)

        preceding_lines = [
            clean_space(line)
            for line in html_to_text(raw[: start.start()]).split("\n")
            if clean_space(line)
        ]
        header = preceding_lines[-1] if preceding_lines else ""
        header_matches = list(NUM_PARENS_RE.finditer(header))
        header_number = int(header_matches[-1].group(1)) if header_matches else None
        header_number_raw = (
            f"{header_matches[-1].group(1)}{header_matches[-1].group(2) or ''}"
            if header_matches
            else None
        )

        witness = html_to_text(raw[start.end() : end.start()])
        after_text = html_to_text(raw[end.end() : next_start])
        if " = " in witness:
            witness, embedded_after = witness.split(" = ", 1)
            after_text = f"{embedded_after}\n{after_text}"
        glosses = [(int(match.group(1)), clean_space(match.group(2))) for match in GLOSS_LINE_RE.finditer(after_text)]
        citations = re.findall(r"\(([AP]_[^)]+|Borrador)\)", after_text)
        packets.append(
            Packet(
                header=header,
                header_number=header_number,
                header_number_raw=header_number_raw,
                witness=witness,
                glosses=glosses,
                citation_raw=citations[-1] if citations else "",
            )
        )
    return packets


def target_number(row: dict) -> int | None:
    metadata = row.get("Sahagun_Escolios_JSON", {})
    if not isinstance(metadata, dict):
        return None
    return metadata.get("target_number_base") or metadata.get("target_alignment_v34_1", {}).get("number_base")


def target_number_raw(row: dict, packet: Packet | None = None) -> str | None:
    metadata = row.get("Sahagun_Escolios_JSON", {})
    raw_value = None
    if isinstance(metadata, dict):
        raw_value = metadata.get("target_number_raw") or metadata.get("target_alignment_v34_1", {}).get("number_raw")
    return str(raw_value or (packet.header_number_raw if packet else "") or target_number(row) or "")


def strip_header_number(header: str) -> str:
    return clean_space(NUM_PARENS_RE.sub("", header).strip(" .;,"))


def glosses_for_number(packet: Packet, number: int) -> list[str]:
    return [gloss for gloss_number, gloss in packet.glosses if gloss_number == number]


def choose_definition(row: dict, packet: Packet, number: int) -> str:
    header_definition = strip_header_number(packet.header)
    gloss_definitions = glosses_for_number(packet, number)
    evidence_text = " ".join([header_definition, *gloss_definitions])
    translation = clean_space(str(row.get("Traducción", "")))
    pieces = [clean_space(piece) for piece in re.split(r"\s*/\s*", translation) if clean_space(piece)]
    if pieces:
        scored = [(len(text_words(piece) & text_words(evidence_text)), piece) for piece in pieces]
        scored.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
        if scored[0][0] > 0:
            return scored[0][1]
    if header_definition:
        return normalize_spanishish(header_definition)
    if gloss_definitions:
        return normalize_spanishish(gloss_definitions[0])
    return translation


def normalize_spanishish(value: str) -> str:
    replacements = {
        "BIUIDORA": "VIVIDORA",
        "BIUIDOR": "VIVIDOR",
        "REZI": "RECI",
        "ALUA": "ALBA",
        "ALUA.": "ALBA.",
        "PT.": "PRET.",
        " P. ": " PRET. ",
        "Hazer": "Hacer",
        "hazer": "hacer",
        "hazerse": "hacerse",
        "reboluiendo": "revolviendo",
        "debaxo": "debajo",
        "della": "de ella",
        "viuo": "vivo",
        "muger": "mujer",
        "mugeres": "mujeres",
        "aredondear": "arredondear",
    }
    text = clean_space(value)
    letters = [char for char in text if char.isalpha()]
    if letters and sum(1 for char in letters if char.isupper()) / len(letters) > 0.7:
        text = text.lower()
    for before, after in replacements.items():
        text = text.replace(before, after)
    text = text.replace("ç", "z")
    text = re.sub(r"\babit", "habit", text)
    text = re.sub(r"\bpt\.", "pret.", text, flags=re.I)
    text = re.sub(r"\bp\.", "pret.", text, flags=re.I)
    if text:
        text = text[0].lower() + text[1:]
    return text


def normalize_nahuatl(value: str) -> str:
    text = html.unescape(value)
    text = text.replace("\xa0", " ")
    text = text.replace("ÿ", "y")
    text = text.replace("ä", "ā").replace("ë", "ē").replace("ï", "ī").replace("ö", "ō").replace("ü", "ū")
    text = text.replace("Ä", "Ā").replace("Ë", "Ē").replace("Ï", "Ī").replace("Ö", "Ō").replace("Ü", "Ū")
    text = text.replace("ç", "z")
    text = text.replace("Ç", "Z")
    text = text.replace("q[ui]", "qui").replace("q[ue]", "que")
    text = text.replace("q'lh", "quilh").replace("q'm", "quim").replace("q't", "quit").replace("q'", "qui")
    text = text.replace("yn", "in").replace("Yn", "In").replace("ÿn", "in")
    text = re.sub(r"\by(?=[bcdfghjklmnpqrstvwxyz])", "i", text, flags=re.I)
    text = re.sub(r"\bqu(?=[ao])", "cu", text, flags=re.I)
    text = re.sub(r"\bval", "hual", text, flags=re.I)
    text = re.sub(r"\bvel", "huel", text, flags=re.I)
    text = re.sub(r"\bve", "hue", text, flags=re.I)
    text = re.sub(r"\bvi", "hui", text, flags=re.I)
    text = re.sub(r"\bvo", "ho", text, flags=re.I)
    text = re.sub(r"\bvu", "hu", text, flags=re.I)
    text = re.sub(r"\bvn", "on", text, flags=re.I)
    text = re.sub(r"\bvm", "om", text, flags=re.I)
    text = re.sub(r"\bv(?=[bcdfghjklmnpqrstvwxyz])", "u", text, flags=re.I)
    text = text.replace("tlauel", "tlahuel").replace("tlavel", "tlahuel")
    text = text.replace("auel", "ahuel").replace("auil", "ahuil").replace("auic", "ahuic")
    text = re.sub(r"civ", "cihu", text, flags=re.I)
    text = re.sub(r"ciu(?!h)", "cihu", text, flags=re.I)
    text = re.sub(r"\((\d+),", r"(\1)", text)
    text = text.replace("â", "ā").replace("ê", "ē").replace("î", "ī").replace("ô", "ō")
    text = text.replace("Â", "Ā").replace("Ê", "Ē").replace("Î", "Ī").replace("Ô", "Ō")
    text = clean_space(text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return text


def split_occurrence_units(witness: str) -> list[str]:
    units = [clean_space(unit) for unit in re.split(r"(?<=[.;:])\s+|\n+", witness) if clean_space(unit)]
    merged: list[str] = []
    for unit in units:
        if len(unit) < 40 and merged and not NUM_PARENS_RE.search(unit):
            merged[-1] = f"{merged[-1]} {unit}"
        else:
            merged.append(unit)
    return merged


def form_similarity(forms: set[str], unit: str) -> float:
    unit_key = form_key(unit)
    if not unit_key:
        return 0.0
    best = 0.0
    for form in forms:
        if not form:
            continue
        if len(form) >= 4 and (form in unit_key or unit_key in form):
            best = max(best, 1.0)
            continue
        for word in WORD_RE.findall(unit):
            word_key = form_key(word)
            if len(word_key) < 3:
                continue
            ratio = difflib.SequenceMatcher(None, form, word_key).ratio()
            if word_key.endswith(form) or form.endswith(word_key):
                ratio = max(ratio, 0.88)
            best = max(best, ratio)
    return best


def occurrence_score(unit: str, row: dict, number: int) -> tuple[float, bool, bool]:
    unit_numbers = numbers_in(unit)
    has_number = number in unit_numbers
    similarity = form_similarity(target_forms(row), unit)
    has_form = similarity >= 0.82
    score = 0.0
    if has_number:
        score += 100
    if has_form:
        score += 80 * similarity
    score -= min(len(unit), 500) / 250
    return score, has_number, has_form


def select_occurrence(row: dict, packet: Packet, number: int) -> tuple[str, bool, bool, float] | None:
    scored = []
    for unit in split_occurrence_units(packet.witness):
        score, has_number, has_form = occurrence_score(unit, row, number)
        if has_number or has_form:
            scored.append((score, unit, has_number, has_form))
    if not scored:
        return None
    score, unit, has_number, has_form = max(scored, key=lambda item: item[0])
    return unit, has_number, has_form, score


def packet_score(row: dict, packet: Packet, number: int) -> tuple[float, str, str]:
    translation_words = text_words(row.get("Traducción", ""))
    header_words = text_words(strip_header_number(packet.header))
    gloss_text = " ".join(glosses_for_number(packet, number))
    gloss_words = text_words(gloss_text)
    score = 0.0
    reasons = []
    if packet.header_number == number:
        score += 120
        reasons.append("header_number")
    if header_words & translation_words:
        score += 10 * len(header_words & translation_words)
        reasons.append("header_translation_overlap")
    if gloss_words & translation_words:
        score += 8 * len(gloss_words & translation_words)
        reasons.append("gloss_translation_overlap")
    if any(gloss_number == number for gloss_number, _ in packet.glosses):
        score += 20
        reasons.append("target_gloss_line")
    if f"({number}" in packet.witness:
        score += 15
        reasons.append("target_number_in_witness")
    return score, ",".join(reasons), " ".join(sorted((header_words | gloss_words) & translation_words))


def select_candidate(row: dict) -> Candidate | None:
    number = target_number(row)
    if number is None:
        return None
    best: tuple[float, Packet, str, str] | None = None
    for packet in parse_packets(row.get("Comentario_raw_1565_sahagun_escolios", "")):
        score, reason, overlap = packet_score(row, packet, number)
        if score <= 0:
            continue
        if best is None or score > best[0]:
            best = (score, packet, reason, overlap)
    if best is None:
        return None

    score, packet, reason, overlap = best
    occurrence = select_occurrence(row, packet, number)
    if occurrence is None:
        return None
    occurrence_text, has_number, has_form, occurrence_points = occurrence
    definition = choose_definition(row, packet, number)

    high_confidence = False
    if packet.header_number == number and (overlap or has_form or has_number):
        high_confidence = True
    if packet.header_number is None and "gloss_translation_overlap" in reason and has_number and has_form:
        high_confidence = True

    if not high_confidence:
        return None

    return Candidate(
        score=score + occurrence_points,
        packet=packet,
        occurrence=occurrence_text,
        occurrence_has_target_number=has_number,
        occurrence_has_target_form=has_form,
        target_definition=definition,
        reason=reason,
    )


def target_error(row: dict) -> bool:
    number = target_number(row)
    if number is None:
        return False
    return number not in public_witness_numbers(row) or number not in public_gloss_numbers(row)


def has_repair_marker(row: dict) -> bool:
    metadata = row.get("Sahagun_Escolios_JSON", {})
    if not isinstance(metadata, dict):
        return False
    return metadata.get("qa_v80_internal_coherence_repair", {}).get("marker") == REPAIR_MARKER


def bold_nearest_number_mismatches(row: dict) -> bool:
    number = target_number(row)
    if number is None:
        return False
    witness = public_witness_html(row)
    for bold_match in BOLD_RE.finditer(witness):
        window_start = max(0, bold_match.start() - 100)
        window_end = min(len(witness), bold_match.end() + 100)
        window = witness[window_start:window_end]
        nearest: tuple[int, int] | None = None
        for number_match in NUM_PARENS_RE.finditer(window):
            absolute_start = window_start + number_match.start()
            distance = min(abs(absolute_start - bold_match.start()), abs(absolute_start - bold_match.end()))
            value = int(number_match.group(1))
            if nearest is None or distance < nearest[0]:
                nearest = (distance, value)
        if nearest is not None and nearest[1] != number:
            bold_text = clean_space(html_to_text(bold_match.group(1)))
            if target_gloss_translation_overlap(row, number) and form_similarity(target_forms(row), bold_text) >= 0.82:
                continue
            return True
    return False


def bold_nearest_numbers(row: dict) -> list[tuple[str, int | None]]:
    witness = public_witness_html(row)
    nearest_numbers: list[tuple[str, int | None]] = []
    for bold_match in BOLD_RE.finditer(witness):
        window_start = max(0, bold_match.start() - 100)
        window_end = min(len(witness), bold_match.end() + 100)
        window = witness[window_start:window_end]
        nearest: tuple[int, int] | None = None
        for number_match in NUM_PARENS_RE.finditer(window):
            absolute_start = window_start + number_match.start()
            distance = min(abs(absolute_start - bold_match.start()), abs(absolute_start - bold_match.end()))
            value = int(number_match.group(1))
            if nearest is None or distance < nearest[0]:
                nearest = (distance, value)
        bold_text = clean_space(html_to_text(bold_match.group(1)))
        nearest_numbers.append((bold_text, nearest[1] if nearest else None))
    return nearest_numbers


def public_gloss_text_for_number(row: dict, number: int) -> str:
    gloss_html = public_gloss_html(row)
    for match in PUBLIC_GLOSS_LINE_RE.finditer(gloss_html):
        if int(match.group(1)) == number:
            return clean_space(html_to_text(match.group(2)))
    return ""


def target_gloss_translation_overlap(row: dict, number: int) -> set[str]:
    return text_words(row.get("Traducción", "")) & text_words(public_gloss_text_for_number(row, number))


def bold_number_and_gloss_support_target(row: dict) -> bool:
    number = target_number(row)
    if number is None:
        return False
    metadata = row.get("Sahagun_Escolios_JSON", {})
    if isinstance(metadata, dict):
        exact_override = metadata.get("qa_v90_internal_coherence_exact_override", {})
        if (
            isinstance(exact_override, dict)
            and exact_override.get("marker") == "sahagun_internal_coherence_exact_override_2026_06_29"
            and any(nearest_number == number for _, nearest_number in bold_nearest_numbers(row))
        ):
            return True
    if not target_gloss_translation_overlap(row, number):
        return False
    return any(nearest_number == number for _, nearest_number in bold_nearest_numbers(row))


def find_best_word_span_for_forms(text: str, forms: set[str], number: int) -> tuple[int, int] | None:
    target_positions = [match.start() for match in re.finditer(rf"\({number}(?:-\d+)?[+\-*]?\)", text)]
    def distance_score(start: int) -> float:
        if not target_positions:
            return 0.0
        return -min(abs(start - pos) for pos in target_positions) / 4

    best: tuple[float, int, int] | None = None
    for match in WORD_RE.finditer(text):
        word_key = form_key(match.group(0))
        if len(word_key) < 2:
            continue
        score = 0.0
        for form in forms:
            if not form:
                continue
            if len(form) >= 4 and len(word_key) >= 4 and (form in word_key or word_key in form):
                score = max(score, 100.0)
            else:
                ratio = difflib.SequenceMatcher(None, form, word_key).ratio()
                if ratio >= 0.82:
                    score = max(score, 80 * ratio)
        if score <= 0:
            continue
        score += distance_score(match.start())
        if best is None or score > best[0]:
            best = (score, match.start(), match.end())
    if best:
        return best[1], best[2]
    return None


def find_best_word_span(text: str, row: dict, number: int) -> tuple[int, int] | None:
    adjacent_span = target_number_adjacent_span(text, number)
    edited_forms = forms_from_value(row.get("Editado", ""))
    span = find_best_word_span_for_forms(text, edited_forms, number)
    if span:
        if adjacent_span and distance_to_number(text, span, number) > 10:
            return adjacent_span
        return span
    all_forms = target_forms(row)
    span = find_best_word_span_for_forms(text, all_forms, number)
    if span:
        if adjacent_span and distance_to_number(text, span, number) > 10:
            return adjacent_span
        return span

    if adjacent_span:
        return adjacent_span
    return None


def distance_to_number(text: str, span: tuple[int, int], number: int) -> int:
    positions = [match.start() for match in re.finditer(rf"\({number}(?:-\d+)?[+\-*]?\)", text)]
    if not positions:
        positions = [match.start() for match in re.finditer(rf"\({number}(?:-\d+)?[+\-*]?", text)]
    if not positions:
        return 10_000
    start, end = span
    return min(min(abs(pos - start), abs(pos - end)) for pos in positions)


def target_number_adjacent_span(text: str, number: int) -> tuple[int, int] | None:
    number_pattern = rf"\({number}(?:-\d+)?[+\-*]?\)?"
    word = r"[A-Za-zÁÉÍÓÚÜÑÇáéíóúāēīōūüñç\[\]-]+"
    before_matches = list(re.finditer(rf"({word})\s*{number_pattern}", text))
    if before_matches:
        match = before_matches[-1]
        return match.start(1), match.end(1)
    after_match = re.search(rf"{number_pattern}\s*,?\s*({word})", text)
    if after_match:
        return after_match.start(1), after_match.end(1)
    return None


def bold_target(text: str, row: dict, number: int) -> str:
    span = find_best_word_span(text, row, number)
    if not span:
        return text
    start, end = span
    text = f"{text[:start]}<b>{text[start:end]}</b>{text[end:]}"
    if f"({number}" not in text:
        after_bold = end + len("<b></b>")
        following_number = re.match(r"\s*\(\d+[+\-*]?\)", text[after_bold:])
        if following_number:
            text = f"{text[:after_bold]} ({number}){text[after_bold + following_number.end():]}"
        else:
            text = f"{text[:after_bold]} ({number}){text[after_bold:]}"
    return text


def normalized_citation(raw: str) -> str:
    if not raw:
        return ""
    return re.sub(r"-\s+", "-", raw)


def citation_object(raw: str) -> dict:
    if not raw:
        return {}
    if raw == "Borrador":
        return {"raw": raw, "type": "draft"}
    raw = normalized_citation(raw)
    match = re.fullmatch(r"([AP])_(\d+[rv])(?:-(\d+[rv]))?", raw)
    if not match:
        return {"raw": raw}
    return {
        "folio_end": match.group(3),
        "folio_start": match.group(2),
        "manuscript": match.group(1),
        "raw": raw,
        "type": "folio",
    }


def build_commentary(row: dict, candidate: Candidate) -> tuple[str, str, str]:
    number = target_number(row)
    assert number is not None
    lemma = clean_space(str(row.get("Editado") or row.get("Original") or ""))
    definition = normalize_spanishish(candidate.target_definition)
    witness = normalize_nahuatl(candidate.occurrence).rstrip(" .")
    witness = bold_target(witness, row, number)
    citation = normalized_citation(candidate.packet.citation_raw)
    witness_line = f"<i>{witness}</i>."
    if citation:
        witness_line = f"{witness_line} {citation}"
    gloss_line = f"({number}) {definition.rstrip('.')};"
    commentary = (
        f"{lemma}.<br/><br/>{definition}<br/><br/>"
        f"{witness_line}<br/><br/>"
        f"Glosas relevantes del escolio:<br/>{gloss_line}<br/>"
    )
    return commentary, witness_line, definition


def append_unique_marker(value: object, marker: str) -> list[str]:
    items: list[str]
    if isinstance(value, list):
        items = [str(item) for item in value]
    elif value:
        items = [str(value)]
    else:
        items = []
    if marker not in items:
        items.append(marker)
    return items


def update_row(row: dict, candidate: Candidate) -> dict:
    number = target_number(row)
    assert number is not None
    previous_commentary = row.get("Comentario", "")
    commentary, witness_line, definition = build_commentary(row, candidate)
    row["Comentario"] = commentary
    row["Comentario (es)"] = commentary
    row["Comentario_wimmer_plus_html"] = commentary

    metadata = row.setdefault("Sahagun_Escolios_JSON", {})
    metadata["target_number_base"] = number
    metadata["target_number_raw"] = target_number_raw(row, candidate.packet)
    alignment = metadata.setdefault("target_alignment_v34_1", {})
    alignment["number_base"] = number
    alignment["number_raw"] = target_number_raw(row, candidate.packet)
    alignment["packet_header"] = candidate.packet.header
    alignment["repair_policy"] = REPAIR_MARKER

    display = metadata.setdefault("display", {})
    display["html"] = commentary
    display["display_witness_line"] = witness_line
    display["display_gloss"] = definition
    display["citation"] = citation_object(candidate.packet.citation_raw)
    display["lemma"] = clean_space(str(row.get("Editado") or row.get("Original") or ""))
    display["witness_count"] = 1
    display["issues"] = append_unique_marker(display.get("issues"), REPAIR_MARKER)

    metadata["qa_v80_internal_coherence_repair"] = {
        "action": "rebuilt_public_fields_from_raw_target_packet",
        "marker": REPAIR_MARKER,
        "packet_header": candidate.packet.header,
        "target_number_base": number,
        "target_number_raw": target_number_raw(row, candidate.packet),
        "score": round(candidate.score, 3),
        "reason": candidate.reason,
        "previous_commentary_sha1": hashlib.sha1(str(previous_commentary).encode("utf-8")).hexdigest(),
    }
    row["Comentario_display_issues"] = append_unique_marker(row.get("Comentario_display_issues"), REPAIR_MARKER)
    return row


def rebuilt_bold_has_candidate_form_support(row: dict, repaired: dict, candidate: Candidate) -> bool:
    number = target_number(repaired)
    if number is None:
        return False
    bolds = [clean_space(html_to_text(match.group(1))) for match in BOLD_RE.finditer(public_witness_html(repaired))]
    if not bolds or any(len(form_key(bold)) <= 2 for bold in bolds):
        return False
    support_forms = set(target_forms(row))
    for gloss in glosses_for_number(candidate.packet, number):
        support_forms.update(forms_from_value(gloss))
    support_forms = {form for form in support_forms if len(form) >= 4}
    return bool(support_forms) and any(form_similarity(support_forms, bold) >= 0.82 for bold in bolds)


def audit_rows(rows: Iterable[dict]) -> list[dict[str, str]]:
    audit: list[dict[str, str]] = []
    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        record_id = row.get("record_id", "")
        original = row.get("Original", "")
        editado = row.get("Editado", "")
        number = target_number(row)
        commentary = str(row.get("Comentario", ""))
        witness_numbers = public_witness_numbers(row)
        gloss_numbers = public_gloss_numbers(row)
        if number is not None and number not in witness_numbers:
            audit.append(
                {
                    "record_id": record_id,
                    "original": original,
                    "editado": editado,
                    "issue_type": "target_number_missing_from_witness",
                    "severity": "error",
                    "detail": f"target number {number} not in displayed witness numbers {sorted(witness_numbers)}",
                    "sample": clean_space(html_to_text(public_witness_html(row)))[:500],
                }
            )
        if number is not None and number not in gloss_numbers:
            audit.append(
                {
                    "record_id": record_id,
                    "original": original,
                    "editado": editado,
                    "issue_type": "target_number_missing_from_gloss_block",
                    "severity": "error",
                    "detail": f"target number {number} not in gloss line numbers {sorted(gloss_numbers)}",
                    "sample": clean_space(html_to_text(public_gloss_html(row)))[:500],
                }
            )
        has_target_apparatus = number is not None or bool(witness_numbers) or bool(gloss_numbers)
        if has_target_apparatus:
            bolds = [clean_space(html_to_text(match.group(1))) for match in BOLD_RE.finditer(public_witness_html(row))]
            if not bolds:
                audit.append(
                    {
                        "record_id": record_id,
                        "original": original,
                        "editado": editado,
                        "issue_type": "no_bold_in_comentario",
                        "severity": "review",
                        "detail": "Comentario has no <b> target highlight",
                        "sample": clean_space(html_to_text(commentary))[:500],
                    }
                )
            else:
                forms = target_forms(row)
                if (
                    forms
                    and not any(form_similarity(forms, bold) >= 0.82 for bold in bolds)
                    and not bold_number_and_gloss_support_target(row)
                ):
                    audit.append(
                        {
                            "record_id": record_id,
                            "original": original,
                            "editado": editado,
                            "issue_type": "bold_text_no_target_token_overlap",
                            "severity": "review",
                            "detail": f"bold={bolds[:3]}",
                            "sample": clean_space(html_to_text(commentary))[:500],
                        }
                    )
                elif bold_nearest_number_mismatches(row):
                    audit.append(
                        {
                            "record_id": record_id,
                            "original": original,
                            "editado": editado,
                            "issue_type": "bold_nearest_number_mismatch",
                            "severity": "review",
                            "detail": f"bold nearest number differs from target {number}",
                            "sample": clean_space(html_to_text(public_witness_html(row)))[:500],
                        }
                    )
        comentario_es = str(row.get("Comentario (es)", ""))
        if comentario_es and clean_space(html_to_text(comentario_es)) != clean_space(html_to_text(commentary)):
            audit.append(
                {
                    "record_id": record_id,
                    "original": original,
                    "editado": editado,
                    "issue_type": "comentario_vs_es_text_mismatch",
                    "severity": "review",
                    "detail": "Comentario and Comentario (es) differ after text normalization",
                    "sample": clean_space(html_to_text(commentary))[:500],
                }
            )
    return audit


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--apply", action="store_true", help="Apply high-confidence public-field repairs.")
    parser.add_argument("--audit-output", type=Path, default=AUDIT_PATH)
    parser.add_argument("--review-output", type=Path, default=REVIEW_PATH)
    parser.add_argument("--proposal-output", type=Path, default=PROPOSAL_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    current_target_issue_ids: dict[str, set[str]] = {}
    for audit_row in audit_rows(rows):
        if audit_row["issue_type"] in TARGET_BOLD_ISSUES:
            current_target_issue_ids.setdefault(audit_row["record_id"], set()).add(audit_row["issue_type"])
    proposals: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        record_id = row.get("record_id", "")
        target_issue_ids = current_target_issue_ids.get(record_id, set())
        needs_repair = (
            target_error(row)
            or (has_repair_marker(row) and bold_nearest_number_mismatches(row))
            or bool(target_issue_ids)
        )
        if not needs_repair:
            continue
        number = target_number(row)
        candidate = select_candidate(row)
        if candidate is None:
            counts["review"] += 1
            review.append(
                {
                    "record_id": row.get("record_id", ""),
                    "original": row.get("Original", ""),
                    "editado": row.get("Editado", ""),
                    "target_number": str(number or ""),
                    "reason": "no_high_confidence_raw_target_rebuild",
                    "current_witness_numbers": ",".join(map(str, sorted(public_witness_numbers(row)))),
                    "current_gloss_numbers": ",".join(map(str, sorted(public_gloss_numbers(row)))),
                    "translation": row.get("Traducción", ""),
                }
            )
            continue
        repaired = json.loads(json.dumps(row, ensure_ascii=False))
        update_row(repaired, candidate)
        target_bold_rebuild_only = (
            bool(target_issue_ids)
            and not target_error(row)
            and not (has_repair_marker(row) and bold_nearest_number_mismatches(row))
        )
        if target_bold_rebuild_only and record_id not in SAFE_TARGET_BOLD_REBUILD_IDS:
            if record_id not in RAW_GLOSS_SUPPORTED_TARGET_BOLD_REBUILD_IDS:
                counts["review"] += 1
                review.append(
                    {
                        "record_id": row.get("record_id", ""),
                        "original": row.get("Original", ""),
                        "editado": row.get("Editado", ""),
                        "target_number": str(number or ""),
                        "reason": "raw_target_bold_rebuild_requires_manual_confirmation",
                        "current_witness_numbers": ",".join(map(str, sorted(public_witness_numbers(row)))),
                        "current_gloss_numbers": ",".join(map(str, sorted(public_gloss_numbers(row)))),
                        "translation": row.get("Traducción", ""),
                    }
                )
                continue
        remaining_target_issues = [
            audit_row["issue_type"]
            for audit_row in audit_rows([repaired])
            if audit_row["issue_type"] in TARGET_BOLD_ISSUES or audit_row["severity"] == "error"
        ]
        raw_gloss_supported = record_id in RAW_GLOSS_SUPPORTED_TARGET_BOLD_REBUILD_IDS
        if remaining_target_issues or (
            not raw_gloss_supported and not rebuilt_bold_has_candidate_form_support(row, repaired, candidate)
        ):
            counts["review"] += 1
            reason = "raw_target_rebuild_did_not_clear_audit:" + ";".join(remaining_target_issues)
            if not remaining_target_issues:
                reason = "raw_target_rebuild_lacks_final_bold_form_support"
            review.append(
                {
                    "record_id": row.get("record_id", ""),
                    "original": row.get("Original", ""),
                    "editado": row.get("Editado", ""),
                    "target_number": str(number or ""),
                    "reason": reason,
                    "current_witness_numbers": ",".join(map(str, sorted(public_witness_numbers(row)))),
                    "current_gloss_numbers": ",".join(map(str, sorted(public_gloss_numbers(row)))),
                    "translation": row.get("Traducción", ""),
                }
            )
            continue
        counts["proposal"] += 1
        commentary, witness_line, definition = build_commentary(row, candidate)
        proposals.append(
            {
                "record_id": row.get("record_id", ""),
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "target_number": str(number or ""),
                "packet_header": candidate.packet.header,
                "citation": candidate.packet.citation_raw,
                "definition": definition,
                "witness_line": clean_space(html_to_text(witness_line)),
                "score": f"{candidate.score:.3f}",
                "reason": candidate.reason,
            }
        )
        if args.apply:
            row.clear()
            row.update(repaired)
            counts["applied"] += 1

    audit = audit_rows(rows)
    write_tsv(
        args.proposal_output,
        proposals,
        [
            "record_id",
            "original",
            "editado",
            "target_number",
            "packet_header",
            "citation",
            "definition",
            "witness_line",
            "score",
            "reason",
        ],
    )
    write_tsv(
        args.review_output,
        [
            *review,
            *[
                {
                    "record_id": row["record_id"],
                    "original": row["original"],
                    "editado": row["editado"],
                    "target_number": "",
                    "reason": f"{row['severity']}:{row['issue_type']}:{row['detail']}",
                    "current_witness_numbers": "",
                    "current_gloss_numbers": "",
                    "translation": row["sample"],
                }
                for row in audit
                if row["severity"] == "error"
            ],
        ],
        [
            "record_id",
            "original",
            "editado",
            "target_number",
            "reason",
            "current_witness_numbers",
            "current_gloss_numbers",
            "translation",
        ],
    )
    write_tsv(
        args.audit_output,
        audit,
        ["record_id", "original", "editado", "issue_type", "severity", "detail", "sample"],
    )
    if args.apply:
        write_rows(args.data, rows)

    print("summary", dict(counts))
    print("audit", dict(Counter(row["issue_type"] for row in audit)))
    print("proposals", args.proposal_output)
    print("review", args.review_output)
    print("audit_output", args.audit_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
