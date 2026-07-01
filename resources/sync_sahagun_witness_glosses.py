#!/usr/bin/env python3
"""Expand Sahagun Escolios visible glosas to match visible witness numbers.

This is the generalized version of the tzatzi repair: if a public witness span
shows numbered context, the public "Glosas relevantes" block should include the
glosas for those same visible numbers when the preserved raw packet supplies
them. Raw packets are never modified.
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
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from resources import repair_sahagun_internal_coherence as repair  # noqa: E402


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/sahagun_witness_gloss_span_proposals.tsv")
REVIEW_PATH = Path("resources/sahagun_witness_gloss_span_review.tsv")
SUMMARY_PATH = Path("resources/sahagun_witness_gloss_span_summary.json")
SOURCE = "1565 Sahagún Escolios"
MARKER = "sync_visible_witness_glosses_2026_06_29"

ITALIC_RE = re.compile(r"<i\b[^>]*>.*?</i>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
NUM_RE = re.compile(r"\((\d+)[+\-*]?\)")
PUBLIC_GLOSS_RE = re.compile(
    r"\((\d+)[+\-*]?\)\s*(.*?)(?=(?:<br\s*/?>\s*\(\d+)|$)",
    re.I | re.S,
)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", BR_RE.sub(" ", html.unescape(str(value or ""))))).strip()


def ordered_numbers(value: str) -> list[int]:
    numbers: list[int] = []
    for match in NUM_RE.finditer(str(value or "")):
        number = int(match.group(1))
        if number not in numbers:
            numbers.append(number)
    return numbers


def split_commentary(row: dict) -> tuple[str, str]:
    commentary = str(row.get("Comentario", ""))
    if "Glosas relevantes del escolio:" not in commentary:
        return commentary, ""
    return commentary.split("Glosas relevantes del escolio:", 1)


def witness_html(row: dict) -> str:
    before_glosses, _ = split_commentary(row)
    italic_spans = ITALIC_RE.findall(before_glosses)
    numbered = [span for span in italic_spans if NUM_RE.search(span)]
    return " ".join(numbered) if numbered else before_glosses


def current_gloss_map(row: dict) -> dict[int, list[str]]:
    _, gloss_html = split_commentary(row)
    out: dict[int, list[str]] = defaultdict(list)
    for match in PUBLIC_GLOSS_RE.finditer(gloss_html):
        number = int(match.group(1))
        text = match.group(2).strip()
        text = re.sub(r"(?:<br\s*/?>|\s)+$", "", text, flags=re.I).strip()
        text = text.rstrip("; ")
        if text and text not in out[number]:
            out[number].append(text)
    return out


def raw_gloss_map(packet: repair.Packet) -> dict[int, list[str]]:
    out: dict[int, list[str]] = defaultdict(list)
    for number, gloss in packet.glosses:
        text = repair.normalize_spanishish(gloss).strip().rstrip("; ")
        # Blank raw glosses can be parsed as spilling into the next numbered
        # line, e.g. "8:" followed by "9: persona diligente". Do not treat the
        # next gloss marker as text for the empty number.
        if re.match(r"^\d+\s*:", text):
            continue
        if text and not out[number]:
            out[number].append(text)
    return out


def display_citation(row: dict) -> str:
    before_glosses, _ = split_commentary(row)
    matches = re.findall(r"(?:[AP]_\d+[rv](?:-\d+[rv])?|Borrador)", clean_text(before_glosses))
    return matches[-1] if matches else ""


def select_packet(row: dict, witness_numbers: list[int]) -> tuple[repair.Packet | None, int]:
    packets = repair.parse_packets(row.get("Comentario_raw_1565_sahagun_escolios", ""))
    if not packets:
        return None, 0
    citation = display_citation(row).lower()
    witness_words = repair.text_words(clean_text(witness_html(row)))
    best: tuple[int, repair.Packet] | None = None
    for packet in packets:
        packet_words = repair.text_words(packet.witness)
        packet_glosses = raw_gloss_map(packet)
        score = 0
        score += 3 * len(witness_words & packet_words)
        score += 20 * sum(1 for number in witness_numbers if number in packet_glosses)
        if citation and repair.normalized_citation(packet.citation_raw).lower() == citation:
            score += 50
        if best is None or score > best[0]:
            best = (score, packet)
    return (best[1], best[0]) if best else (None, 0)


def choose_current_gloss(row: dict, number: int, texts: list[str]) -> str:
    if not texts:
        return ""
    if len(texts) == 1:
        return texts[0]
    target = repair.target_number(row)
    if target == number:
        display_gloss = row.get("Sahagun_Escolios_JSON", {}).get("display", {}).get("display_gloss", "")
        reference_words = repair.text_words(f"{row.get('Traducción', '')} {display_gloss}")
        if reference_words:
            return max(texts, key=lambda text: len(reference_words & repair.text_words(text)))
    return texts[0]


def build_gloss_block(
    row: dict,
    numbers: list[int],
    current: dict[int, list[str]],
    raw: dict[int, list[str]],
) -> str:
    lines: list[str] = []
    for number in numbers:
        text = choose_current_gloss(row, number, current.get(number, [])) or (raw.get(number, [""])[0])
        text = text.strip().rstrip("; ")
        if text:
            lines.append(f"({number}) {text};<br/>")
    return "".join(lines)


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


def update_row(row: dict, new_commentary: str, numbers: list[int], packet: repair.Packet) -> None:
    old_commentary = str(row.get("Comentario", ""))
    row["Comentario"] = new_commentary
    row["Comentario (es)"] = new_commentary
    row["Comentario_wimmer_plus_html"] = new_commentary

    metadata = row.setdefault("Sahagun_Escolios_JSON", {})
    display = metadata.setdefault("display", {})
    display["html"] = new_commentary
    display["issues"] = append_marker(display.get("issues"), MARKER)

    metadata["qa_v83_visible_witness_gloss_sync"] = {
        "action": "expanded_visible_gloss_block_to_match_visible_witness_numbers",
        "marker": MARKER,
        "included_gloss_numbers": numbers,
        "packet_header": packet.header,
        "raw_packet_preserved": True,
        "old_commentary_sha1": hashlib.sha1(old_commentary.encode("utf-8")).hexdigest(),
    }
    row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), MARKER)


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
    parser.add_argument("--review", type=Path, default=REVIEW_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    proposals: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        numbers = ordered_numbers(witness_html(row))
        if not numbers:
            continue
        current = current_gloss_map(row)
        current_numbers = list(current)
        missing = [number for number in numbers if number not in current]
        duplicates = [number for number in numbers if len(current.get(number, [])) > 1]
        order_mismatch = current_numbers != numbers
        if not missing and not duplicates and not order_mismatch:
            continue

        packet, score = select_packet(row, numbers)
        if packet is None:
            counts["review_no_packet"] += 1
            review.append(
                {
                    "record_id": row.get("record_id", ""),
                    "original": row.get("Original", ""),
                    "editado": row.get("Editado", ""),
                    "witness_numbers": ",".join(map(str, numbers)),
                    "current_gloss_numbers": ",".join(map(str, current)),
                    "missing_numbers": ",".join(map(str, missing)),
                    "reason": "no_raw_packet",
                }
            )
            continue

        raw = raw_gloss_map(packet)
        missing_raw = [number for number in missing if number not in raw]
        if missing_raw:
            counts["review_missing_raw_gloss"] += 1
            review.append(
                {
                    "record_id": row.get("record_id", ""),
                    "original": row.get("Original", ""),
                    "editado": row.get("Editado", ""),
                    "witness_numbers": ",".join(map(str, numbers)),
                    "current_gloss_numbers": ",".join(map(str, current)),
                    "missing_numbers": ",".join(map(str, missing)),
                    "reason": f"missing_raw_gloss:{','.join(map(str, missing_raw))}",
                    "packet_header": packet.header,
                    "packet_score": str(score),
                }
            )
            continue

        before_glosses, _ = split_commentary(row)
        new_gloss_block = build_gloss_block(row, numbers, current, raw)
        new_commentary = f"{before_glosses}Glosas relevantes del escolio:<br/>{new_gloss_block}"
        if new_commentary == row.get("Comentario"):
            continue

        counts["proposal"] += 1
        counts["proposal_rows"] += 1
        counts["proposal_changes"] += max(1, len(missing) + len(duplicates) + (1 if order_mismatch else 0))
        proposals.append(
            {
                "record_id": row.get("record_id", ""),
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "witness_numbers": ",".join(map(str, numbers)),
                "old_gloss_numbers": ",".join(map(str, current)),
                "added_numbers": ",".join(map(str, missing)),
                "deduped_numbers": ",".join(map(str, duplicates)),
                "order_mismatch": "yes" if order_mismatch else "",
                "packet_header": packet.header,
                "packet_score": str(score),
                "witness_sample": clean_text(witness_html(row))[:240],
            }
        )
        if args.apply:
            update_row(row, new_commentary, numbers, packet)
            counts["applied"] += 1

    write_tsv(
        args.proposals,
        proposals,
        [
            "record_id",
            "original",
            "editado",
            "witness_numbers",
            "old_gloss_numbers",
            "added_numbers",
            "deduped_numbers",
            "order_mismatch",
            "packet_header",
            "packet_score",
            "witness_sample",
        ],
    )
    write_tsv(
        args.review,
        review,
        [
            "record_id",
            "original",
            "editado",
            "witness_numbers",
            "current_gloss_numbers",
            "missing_numbers",
            "reason",
            "packet_header",
            "packet_score",
        ],
    )
    if args.apply:
        write_rows(args.data, rows)
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("summary", dict(counts))
    print("proposals", args.proposals)
    print("review", args.review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
