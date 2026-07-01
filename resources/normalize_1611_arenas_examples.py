#!/usr/bin/env python3
"""Normalize safe visible Nahuatl example spelling in 1611 Arenas.

Arenas rows are phrasebook examples: bold Nahuatl phrase, equals sign, Spanish
gloss. This pass expands exact visible Spanish abbreviations outside bold spans,
rewrites only the bold Nahuatl side for Nahuatl orthography, and preserves the
public commentary in a raw field before display changes.

Safe automatic rewrites:

* ``ç/Ç`` -> ``c/C`` before e/i, otherwise ``z/Z``
* ``qu-/Qu-`` before a/o -> ``cu-/Cu-``
* initial ``y/Y`` before a consonant -> ``i/I``
* source-attested bracket/nasal spellings such as ``q[ue]`` -> ``que`` and
  ``occëtlamãtli`` -> ``occentlamantli``
* outside-bold Spanish abbreviations such as ``q[ue]`` -> ``que`` and
  ``comunme[n]te`` -> ``comúnmente``
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
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/arenas_1611_example_normalization_proposals.tsv")
REVIEW_PATH = Path("resources/arenas_1611_example_normalization_review.tsv")
SUMMARY_PATH = Path("resources/arenas_1611_example_normalization_summary.json")
SOURCE = "1611 Arenas"
RAW_FIELD = "Comentario_raw_1611_arenas"
CEDILLA_MARKER = "visible_bold_nahuatl_1611_cedilla_to_cz_2026_06_29"
QU_MARKER = "visible_bold_nahuatl_1611_qu_before_ao_to_cu_2026_06_29"
SOURCE_TERM_MAP_MARKER = "visible_bold_nahuatl_1611_source_term_map_2026_06_29"
INITIAL_Y_MARKER = "visible_bold_nahuatl_1611_initial_y_before_consonant_to_i_2026_06_29"
SPANISH_ABBREVIATION_MARKER = "visible_spanish_1611_arenas_abbreviation_expansion_2026_06_29"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]

BOLD_RE = re.compile(r"(<b\b[^>]*>)(.*?)(</b>)", re.I | re.S)
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TOKEN_CHARS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÀÈÌÒÙàèìòùÃẼĨÕãẽĩõËëÇç\\[\\]"
WORD_RE = re.compile(rf"[{TOKEN_CHARS}]+")
QU_BEFORE_AO_RE = re.compile(r"[Qq][Uu](?=[aAoOāĀōŌáÁóÓàÀòÒâÂôÔ])")
INITIAL_Y_BEFORE_CONSONANT_RE = re.compile(r"^[Yy](?=[bcdfghjklmnpqrstvwxyzçÇ])")
CEDILLA_EI = set("eéiíēīèìêîEÉIÍĒĪÈÌÊÎ")
DIACRITIC_TRANS = str.maketrans(
    "ÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÀÈÌÒÙàèìòùÃẼĨÕãẽĩõËëÂÊÎÔâêîôÇç",
    "AEIOUUNaeiouunAEIOaeioAEIOUaeiouAEIOaeioEeAEIOaeioCc",
)
SPANISH_TOKEN_DENY = {
    "cuando",
    "cuanto",
    "cuantos",
    "cuatro",
    "quatro",
    "quarenta",
    "quarto",
    "quinientos",
    "quince",
    "que",
}
NAHUATL_TOKEN_HINTS = (
    "tl",
    "tz",
    "hu",
    "auh",
    "hua",
    "tzin",
    "xoch",
    "atl",
    "tlan",
    "cal",
    "cuauh",
    "quauh",
    "coatl",
    "cihua",
    "çihua",
    "tlaç",
    "tla",
    "qui",
    "xiqu",
    "nict",
    "mitz",
    "nech",
)

SOURCE_TERM_REPLACEMENTS = {
    "cãtela": "cantela",
    "cãpaie": "campa ye",
    "caxtillã": "Caxtillan",
    "cãpa": "campa",
    "cëca": "cenca",
    "cualcã": "cualcan",
    "hael": "huel",
    "hamo": "ahmo",
    "hanozo": "ahnozo",
    "hazo": "ahzo",
    "tleicã": "tleican",
    "[tleicã": "[tleican",
    "ihuã": "ihuan",
    "inõ": "inon",
    "inõpa": "inonpa",
    "inipã": "inipan",
    "inaxcã": "inaxcan",
    "ipã": "ipan",
    "ipã[": "ipan[",
    "xiquittacã": "xiquittacan",
    "xiccahuacã": "xiccahuacan",
    "xicnapalocã": "xicnapalocan",
    "tlamãti": "tlamanti",
    "tehuãtin": "tehuantin",
    "ticchihuacã": "ticchihuacan",
    "ticnamãcaz": "ticnamacaz",
    "motlã": "motlan",
    "nicã": "nican",
    "nimã": "niman",
    "nopã": "nopan",
    "õ": "on",
    "õca": "onca",
    "õpa": "ompa",
    "ocachihtõca": "oc achitonca",
    "panohuacã": "panohuacan",
    "quë": "quen",
    "quëmã": "quenman",
    "quenmã": "quenman",
    "xicualhuicacã": "xicualhuicacan",
    "iquechtzõ": "iquechtzon",
    "yãcuic": "yancuic",
    "zã": "zan",
    "zãnen": "zan nen",
    "]zãnen": "]zan nen",
    "zazã": "zazan",
    "zaxtoltzõtli": "zaxtoltzontli",
    "zatepã": "zatepan",
    "cuauhtlã": "Cuauhtlan",
    "centlamãpan": "centlamampan",
    "tetlã": "tetlan",
    "notetzotzoncahuã": "notetzotzoncahuan",
    "mitzcaquizq[ue]": "mitzcaquizque",
    "mictihq[ue]": "mictihque",
    "oanquichiuhq[ué]": "oanquichiuhque",
    "oanquittaq[ué]": "oanquittaque",
    "onechmictihq[ué]": "onechmictihque",
    "otlahcuaq[ue]": "otlahcuaque",
    "oquiximatq[ué]": "oquiximatque",
    "quimatizq[qué]": "quimatizque",
    "tinechnëquixti": "tinechnenquixti",
    "occëtlamãtli": "occentlamantli",
    "cëtlamanpã": "centlamampan",
    "zëtlamãpã": "centlamampan",
}

SPANISH_ABBREVIATION_REPLACEMENTS = {
    "razonablemente[n]te": "razonablemente",
    "comunme[n]te": "comúnmente",
    "vergue[n]ça": "vergüenza",
    "cincue[n]ta": "cincuenta",
    "aq[ue]llos": "aquellos",
    "viniere[n]": "vinieren",
    "hazie[n]da": "hacienda",
    "conte[n]to": "contento",
    "apre[n]der": "aprender",
    "suele[n]": "suelen",
    "porq[ue]": "porque",
    "aq[ue]lo": "aquello",
    "alguie[n]": "alguien",
    "tie[n]po": "tiempo",
    "tie[m]po": "tiempo",
    "gra[n]de": "grande",
    "agua[r]do": "aguardo",
    "cie[n]to": "ciento",
    "calle[n]": "callen",
    "ve[n]de": "vende",
    "dice[n]": "dicen",
    "sabe[n]": "saben",
    "quie[n]": "quien",
    "ve[n]ga": "venga",
    "te[n]go": "tengo",
    "Bie[n]": "Bien",
    "bie[n]": "bien",
    "bue[n]": "buen",
    "q[ue]": "que",
    "Nõbres": "Nombres",
    "quãto": "cuanto",
    "quãdo": "cuando",
    "lastimarõ": "lastimaron",
    "cantãdo": "cantando",
    "sermõ": "sermón",
    "CãPANARIO": "CAMPANARIO",
}
SPANISH_ABBREVIATION_REPLACEMENT_ITEMS = sorted(
    SPANISH_ABBREVIATION_REPLACEMENTS.items(),
    key=lambda item: len(item[0]),
    reverse=True,
)

REVIEW_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "initial_y_before_consonant",
        re.compile(r"\by[bcdfghjklmnpqrstvwxyzç][A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÀÈÌÒÙàèìòùÃẼĨÕãẽĩõËëÂÊÎÔâêîôç\[]*", re.I),
        "review old initial y used for i before consonant",
    ),
    (
        "q_bracket",
        re.compile(r"\b\w*q\[[^\]]+\]\w*", re.I),
        "review bracketed q expansion",
    ),
    (
        "diaeresis",
        re.compile(r"\b[\wäëïöüÄËÏÖÜÿŸãẽĩõÃẼĨÕ]*[äëïöüÄËÏÖÜÿŸãẽĩõÃẼĨÕ][\wäëïöüÄËÏÖÜÿŸãẽĩõÃẼĨÕ]*\b"),
        "review nasal or diaeresis convention",
    ),
]


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: str, token: str, width: int = 140) -> str:
    text = clean_html(value)
    index = text.lower().find(token.lower())
    if index < 0:
        return text[: width * 2].strip()
    left = max(0, index - width)
    right = min(len(text), index + len(token) + width)
    return text[left:right].strip()


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def token_key(token: str) -> str:
    key = token.translate(DIACRITIC_TRANS).lower().replace("[", "").replace("]", "")
    return re.sub(r"[^a-z]", "", key)


def looks_nahuatl_token(token: str) -> bool:
    key = token_key(token)
    if len(key) < 3 or key in {item.translate(DIACRITIC_TRANS).lower() for item in SPANISH_TOKEN_DENY}:
        return False
    if re.search(r"qu[ao]", key):
        return True
    return any(hint.translate(DIACRITIC_TRANS).lower() in key for hint in NAHUATL_TOKEN_HINTS)


def qu_to_cu(token: str) -> str:
    def repl(match: re.Match[str]) -> str:
        old = match.group(0)
        if old == "QU":
            return "CU"
        if old == "Qu":
            return "Cu"
        return "cu"

    return QU_BEFORE_AO_RE.sub(repl, token)


def cedilla_to_cz(token: str) -> str:
    chars = list(token)
    for index, char in enumerate(chars):
        if char not in {"ç", "Ç"}:
            continue
        next_char = chars[index + 1] if index + 1 < len(chars) else ""
        lower_replacement = "c" if next_char in CEDILLA_EI else "z"
        chars[index] = lower_replacement.upper() if char == "Ç" else lower_replacement
    return "".join(chars)


def normalize_word(token: str) -> tuple[str, list[tuple[str, str, str]]]:
    changes: list[tuple[str, str, str]] = []
    new = cedilla_to_cz(token)
    if new != token:
        changes.append((CEDILLA_MARKER, token, new))

    after_qu = qu_to_cu(new)
    if after_qu != new and looks_nahuatl_token(new):
        changes.append((QU_MARKER, new, after_qu))
        new = after_qu

    replacement = SOURCE_TERM_REPLACEMENTS.get(new.lower())
    if replacement and replacement != new:
        changes.append((SOURCE_TERM_MAP_MARKER, new, replacement))
        new = replacement

    if INITIAL_Y_BEFORE_CONSONANT_RE.search(new):
        after_y = ("I" if new[0].isupper() else "i") + new[1:]
        if after_y != new:
            changes.append((INITIAL_Y_MARKER, new, after_y))
            new = after_y

    return new, changes


def normalize_text(value: str) -> tuple[str, list[tuple[str, str, str]]]:
    changes: list[tuple[str, str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            new, token_changes = normalize_word(old)
            changes.extend(token_changes)
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold(value: object) -> tuple[str, list[tuple[str, str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_text(match.group(2))
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def normalize_spanish_abbreviations(value: object) -> tuple[str, list[tuple[str, str, str]]]:
    text = str(value or "")
    changes: list[tuple[str, str, str]] = []
    pieces: list[str] = []
    last = 0

    def replace_piece(piece: str) -> str:
        for old, new in SPANISH_ABBREVIATION_REPLACEMENT_ITEMS:
            count = piece.count(old)
            if not count:
                continue
            piece = piece.replace(old, new)
            changes.extend((SPANISH_ABBREVIATION_MARKER, old, new) for _ in range(count))
        return piece

    for match in BOLD_RE.finditer(text):
        pieces.append(replace_piece(text[last : match.start()]))
        pieces.append(match.group(0))
        last = match.end()
    pieces.append(replace_piece(text[last:]))
    return "".join(pieces), changes


def bold_texts(value: object) -> list[str]:
    return [clean_html(match.group(2)) for match in BOLD_RE.finditer(str(value or ""))]


def review_candidates(row: dict) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for field in COMMENTARY_FIELDS:
        value = row.get(field, "")
        if not isinstance(value, str) or not value:
            continue
        for bold in bold_texts(value):
            for kind, pattern, note in REVIEW_PATTERNS:
                for match in pattern.finditer(bold):
                    token = match.group(0)
                    if not looks_nahuatl_token(token):
                        continue
                    key = (field, kind, token)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(
                        {
                            "record_id": row.get("record_id", ""),
                            "original": row.get("Original", ""),
                            "editado": row.get("Editado", ""),
                            "field": field,
                            "candidate_kind": kind,
                            "token": token,
                            "note": note,
                            "bold_text": bold[:700],
                            "context": token_context(value, token),
                        }
                    )
    return out


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
        counts["source_rows"] += 1
        if args.apply and RAW_FIELD not in row:
            row[RAW_FIELD] = row.get("Comentario", "")
            counts["raw_preserved_rows"] += 1
        row_changes: list[tuple[str, str, str, str]] = []

        for field in COMMENTARY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, abbreviation_changes = normalize_spanish_abbreviations(value)
            new_value, bold_changes = normalize_bold(new_value)
            field_changes = abbreviation_changes + bold_changes
            if new_value == value:
                continue
            for marker, old, new in field_changes:
                row_changes.append((field, marker, old, new))
            if args.apply:
                row[field] = new_value

        if row_changes:
            counts["proposal_rows"] += 1
            counts["proposal_changes"] += len(row_changes)
            counts["proposal_changes_spanish_abbreviation"] += sum(
                1 for _, marker, _, _ in row_changes if marker == SPANISH_ABBREVIATION_MARKER
            )
            counts["proposal_changes_cedilla"] += sum(1 for _, marker, _, _ in row_changes if marker == CEDILLA_MARKER)
            counts["proposal_changes_qu_before_ao"] += sum(1 for _, marker, _, _ in row_changes if marker == QU_MARKER)
            counts["proposal_changes_initial_y_before_consonant"] += sum(
                1 for _, marker, _, _ in row_changes if marker == INITIAL_Y_MARKER
            )
            counts["proposal_changes_source_term_map"] += sum(
                1 for _, marker, _, _ in row_changes if marker == SOURCE_TERM_MAP_MARKER
            )
            old_tokens = []
            new_tokens = []
            change_markers = []
            for field, marker, old, new in row_changes:
                old_tokens.append(f"{field}:{old}")
                new_tokens.append(f"{field}:{new}")
                if marker not in change_markers:
                    change_markers.append(marker)
            proposals.append(
                {
                    "record_id": row.get("record_id", ""),
                    "original": row.get("Original", ""),
                    "editado": row.get("Editado", ""),
                    "markers": ";".join(change_markers),
                    "old_tokens": " | ".join(old_tokens),
                    "new_tokens": " | ".join(new_tokens),
                    "context": token_context(row.get("Comentario", ""), row_changes[0][2]),
                }
            )
            if args.apply:
                for marker in change_markers:
                    row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), marker)
                    row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), marker)
                qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
                changed_by_marker = Counter(marker for _, marker, _, _ in row_changes)
                previous_commentary_sha1 = hashlib.sha1(str(row.get(RAW_FIELD, "")).encode("utf-8")).hexdigest()
                if any(marker != SPANISH_ABBREVIATION_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1611_arenas_visible_bold_oldspell": {
                            "action": "normalized_visible_old_spellings_inside_bold_nahuatl_examples",
                            "markers": [
                                marker for marker in change_markers if marker != SPANISH_ABBREVIATION_MARKER
                            ],
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker != SPANISH_ABBREVIATION_MARKER
                            ),
                            "changed_by_marker": {
                                marker: count
                                for marker, count in changed_by_marker.items()
                                if marker != SPANISH_ABBREVIATION_MARKER
                            },
                            "previous_commentary_sha1": previous_commentary_sha1,
                        },
                    }
                if any(marker == SPANISH_ABBREVIATION_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1611_arenas_spanish_abbreviation_expansion": {
                            "action": "expanded_visible_spanish_abbreviations_outside_bold_examples",
                            "marker": SPANISH_ABBREVIATION_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": changed_by_marker[SPANISH_ABBREVIATION_MARKER],
                            "previous_commentary_sha1": previous_commentary_sha1,
                        },
                    }
                row["Sentence_Source_JSON"] = qa

        review.extend(review_candidates(row))

    write_tsv(
        args.proposals,
        proposals,
        ["record_id", "original", "editado", "markers", "old_tokens", "new_tokens", "context"],
    )
    write_tsv(
        args.review,
        review,
        ["record_id", "original", "editado", "field", "candidate_kind", "token", "note", "bold_text", "context"],
    )
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.apply and proposals:
        write_rows(args.data, rows)
        counts["applied_rows"] = len(proposals)
        args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"summary {dict(counts)}")
    print(f"proposals {args.proposals}")
    print(f"review {args.review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
