#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import html
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
LEXICON_ROOT = ROOT / "resources" / "dictionaries" / "rla-es-2.9" / "ortografia" / "palabras"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_corpus_analogy_spellcheck_report.jsonl"
REVIEW_PATH = ROOT / "scripts" / "non_wimmer_corpus_analogy_spellcheck_review.jsonl"

FIELD = "Traducción"
SKIP_TARGET_SOURCES = {"2021 Wimmer", "1992 Karttunen", "V94 Diccionario Global SNP"}
PROTECTED_EVIDENCE_SOURCES = {"1992 Karttunen"}
TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç]+")
HTML_RE = re.compile(r"<[^>]+>")
ARCHAIC_AFTER_RE = re.compile(r"^\s*\(\s*arcaico\s*:", re.I)
ARCHAIC_SPAN_RE = re.compile(r"\(\s*arcaico\s*:[^)]*\)", re.I)

SOURCEISH_PARTS = (
    "tl",
    "tz",
    "hu",
    "hui",
    "qua",
    "qui",
    "zin",
    "tzin",
    "cauh",
    "yotl",
    "liztli",
)

STOP_TOKENS = {
    "arcaico",
    "cf",
    "cfr",
    "etc",
    "latín",
    "latin",
    "vel",
    "vid",
    "vide",
    "vt",
    "vi",
    "vr",
    "vb",
    "vbo",
    "pft",
    "pret",
    "pres",
    "pt",
}

SAFE_TOKEN_REPLACEMENTS = {
    "aguilidad": "agilidad",
    "ahuela": "abuela",
    "ahuelo": "abuelo",
    "ahuja": "aguja",
    "ahujero": "agujero",
    "ahujerada": "agujerada",
    "ahujerado": "agujerado",
    "amanzamiento": "amansamiento",
    "ariba": "arriba",
    "asechador": "acechador",
    "cibdad": "ciudad",
    "coclillas": "cuclillas",
    "cobdiciador": "codiciador",
    "comprativo": "comparativo",
    "delgades": "delgadez",
    "derrivado": "derribado",
    "despavilador": "despabilador",
    "despaviladura": "despabiladura",
    "despavilar": "despabilar",
    "desuanecimiento": "desvanecimiento",
    "dezmenuzador": "desmenuzador",
    "echos": "hechos",
    "empoluoramiento": "empolvoramiento",
    "enlaviar": "enlabiar",
    "enpolvoramiento": "empolvoramiento",
    "escarvandola": "escarbándola",
    "esaminador": "examinador",
    "gomito": "vómito",
    "governador": "gobernador",
    "hardilla": "ardilla",
    "huebo": "huevo",
    "humido": "húmedo",
    "incapie": "hincapié",
    "labadora": "lavadora",
    "nole": "no le",
    "oiyo": "oyó",
    "prenza": "prensa",
    "preñes": "preñez",
    "razgar": "rasgar",
    "renouandolas": "renovándolas",
    "recidencia": "residencia",
    "resador": "rezador",
    "revanada": "rebanada",
    "revolbedor": "revolvedor",
    "sahuco": "saúco",
    "sentarseen": "sentarse en",
    "sáncto": "santo",
    "subdito": "súbdito",
    "sudito": "súbdito",
    "undia": "un día",
    "vallesta": "ballesta",
    "vallestero": "ballestero",
    "viguela": "vihuela",
    "visabuelo": "bisabuelo",
    "yelada": "helada",
    "yuntera": "juntera",
    "zunbar": "zumbar",
}

REJECT_TOKEN_REPLACEMENTS = {
    ("anega", "hanega"),
}


@dataclass(frozen=True)
class TokenHit:
    row_index: int
    token: str
    start: int
    end: int
    translation: str


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = HTML_RE.sub(" ", value)
    return re.sub(r"\s+", " ", value).strip()


def lemma_key(row: dict[str, object]) -> str:
    value = str(row.get("Texto estandarizado") or row.get("Escritura original") or "")
    value = strip_accents(value)
    value = re.sub(r"\s*\+\s*$", "", value)
    value = re.sub(r"[^a-zñç]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def lexeme_from_line(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    token = line.split("/", 1)[0].strip().lower()
    if not token or not TOKEN_RE.fullmatch(token):
        return None
    return token


def load_lexicon() -> tuple[set[str], set[str]]:
    exact: set[str] = set()
    for path in LEXICON_ROOT.rglob("*.txt"):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line in lines:
            token = lexeme_from_line(line)
            if token:
                exact.add(token)
    return exact, {strip_accents(token) for token in exact}


def edit_distance_at_most_one(left: str, right: str) -> bool:
    if left == right:
        return False
    if abs(len(left) - len(right)) > 1:
        return False
    i = j = edits = 0
    while i < len(left) and j < len(right):
        if left[i] == right[j]:
            i += 1
            j += 1
            continue
        edits += 1
        if edits > 1:
            return False
        if len(left) == len(right):
            i += 1
            j += 1
        elif len(left) < len(right):
            j += 1
        else:
            i += 1
    if i < len(left) or j < len(right):
        edits += 1
    return edits <= 1


def relation(old: str, new: str) -> str | None:
    old_f = strip_accents(old)
    new_f = strip_accents(new)
    safe = SAFE_TOKEN_REPLACEMENTS.get(old)
    if safe and strip_accents(safe) == new_f:
        return "safe-token"
    if (old_f, new_f) in REJECT_TOKEN_REPLACEMENTS:
        return None
    if old_f == new_f and old != new:
        return "accent"
    if old_f.replace("ç", "c") == new_f:
        return "cedilla"
    if old_f.replace("ss", "s") == new_f:
        return "ss-s"
    if old_f.replace("x", "j") == new_f or old_f.replace("j", "x") == new_f:
        return "x-j"
    if old_f.replace("z", "c") == new_f:
        return "z-c"
    if old_f.replace("c", "z") == new_f:
        return "c-z"
    if old_f.replace("u", "v") == new_f or old_f.replace("v", "u") == new_f:
        return "u-v"
    if old_f.replace("b", "v") == new_f or old_f.replace("v", "b") == new_f:
        return "b-v"
    if f"h{old_f}" == new_f:
        return "missing-h"
    if old_f.replace("ph", "f") == new_f:
        return "ph-f"
    return None


def is_morph_variant(old: str, new: str) -> bool:
    old_f = strip_accents(old)
    new_f = strip_accents(new)
    if old_f.endswith("s") and old_f[:-1] == new_f:
        return True
    if new_f.endswith("s") and new_f[:-1] == old_f:
        return True
    if len(old_f) == len(new_f) and old_f[:-1] == new_f[:-1]:
        if {old_f[-1], new_f[-1]} <= {"a", "o", "e"}:
            return True
    if old_f + "r" == new_f or new_f + "r" == old_f:
        return True
    if old_f.endswith("ora") and new_f == old_f[:-1]:
        return True
    return False


def sourceish(token: str) -> bool:
    folded = strip_accents(token)
    if len(folded) >= 8 and any(part in folded for part in SOURCEISH_PARTS):
        return True
    return False


def is_after_archaic_annotation(text: str, end: int) -> bool:
    return ARCHAIC_AFTER_RE.match(text[end : end + 32]) is not None


def archaic_spans(text: str) -> list[tuple[int, int]]:
    return [match.span() for match in ARCHAIC_SPAN_RE.finditer(text)]


def in_spans(position: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in spans)


def is_candidate_token(token: str) -> bool:
    if token in SAFE_TOKEN_REPLACEMENTS:
        return True
    folded = strip_accents(token)
    if len(folded) < 5:
        return False
    if folded in STOP_TOKENS:
        return False
    if not re.search(r"[aeiou]", folded):
        return False
    return True


def row_source_text(row: dict[str, object]) -> str:
    return " ".join(
        str(row.get(field) or "")
        for field in ("Escritura original", "Texto estandarizado", "Comentario", "Comentario (es)")
    ).lower()


def preserve_case(old: str, new: str) -> str:
    if old.isupper():
        return new.upper()
    if old[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def context_window(text: str, start: int, end: int) -> str:
    left = text[max(0, start - 40) : start]
    right = text[end : end + 40]
    return f"{left}[{text[start:end]}]{right}"


def build_candidates(rows: list[dict[str, object]], lexicon: set[str], lexicon_folded: set[str]) -> list[dict[str, object]]:
    by_lemma: dict[str, list[int]] = defaultdict(list)
    global_counts: Counter[str] = Counter()

    for index, row in enumerate(rows):
        source = row.get("Fuente")
        if source in PROTECTED_EVIDENCE_SOURCES:
            continue
        translation = str(row.get(FIELD) or "")
        if not translation:
            continue
        by_lemma[lemma_key(row)].append(index)
        for match in TOKEN_RE.finditer(translation):
            global_counts[match.group(0).lower()] += 1

    proposals: dict[tuple[int, str, str], dict[str, object]] = {}

    for index, row in enumerate(rows):
        if row.get("Fuente") in SKIP_TARGET_SOURCES:
            continue
        translation = str(row.get(FIELD) or "")
        if not translation:
            continue
        spans = archaic_spans(translation)
        for match in TOKEN_RE.finditer(translation):
            if in_spans(match.start(), spans):
                continue
            old = match.group(0).lower()
            new = SAFE_TOKEN_REPLACEMENTS.get(old)
            if not new:
                continue
            if is_after_archaic_annotation(translation, match.end()):
                continue
            proposals[(index, old, new)] = {
                "record_id": row.get("record_id"),
                "source": row.get("Fuente"),
                "lemma": row.get("Texto estandarizado"),
                "old_token": old,
                "new_token": new,
                "relation": "safe-token",
                "old_count": global_counts[old],
                "new_count": global_counts[strip_accents(new)],
                "context": context_window(translation, match.start(), match.end()),
                "old_translation": row.get(FIELD),
            }

    for key, indexes in by_lemma.items():
        if not key or len(indexes) < 2:
            continue
        token_hits: dict[str, list[TokenHit]] = defaultdict(list)
        for index in indexes:
            row = rows[index]
            translation = str(row.get(FIELD) or "")
            spans = archaic_spans(translation)
            for match in TOKEN_RE.finditer(translation):
                if in_spans(match.start(), spans):
                    continue
                token = match.group(0)
                token_low = token.lower()
                if not is_candidate_token(token_low):
                    continue
                token_hits[token_low].append(TokenHit(index, token, match.start(), match.end(), translation))

        tokens = sorted(token_hits)
        for old in tokens:
            old_folded = strip_accents(old)
            old_valid = old in lexicon or old_folded in lexicon_folded
            if old_valid and old not in SAFE_TOKEN_REPLACEMENTS and not any(ch in old for ch in "ç"):
                continue
            if sourceish(old):
                continue

            best: tuple[int, str, str] | None = None
            safe_replacement = SAFE_TOKEN_REPLACEMENTS.get(old)
            if safe_replacement:
                best = (9, safe_replacement, "safe-token")
            for new in tokens:
                if best and best[2] == "safe-token":
                    break
                if old == new:
                    continue
                if is_morph_variant(old, new):
                    continue
                new_folded = strip_accents(new)
                rel = relation(old, new)
                if not rel:
                    continue
                new_valid = new in lexicon or new_folded in lexicon_folded
                if not new_valid:
                    continue
                old_count = global_counts[old]
                new_count = global_counts[new]
                score = 0
                if new_count >= old_count:
                    score += 2
                if new_count >= 2:
                    score += 1
                if not old_valid:
                    score += 2
                if rel in {"accent", "one-edit", "cedilla", "ss-s", "z-c", "u-v", "b-v", "missing-h", "ph-f"}:
                    score += 1
                if score < 4:
                    continue
                if best is None or score > best[0] or (score == best[0] and global_counts[new] > global_counts[best[1]]):
                    best = (score, new, rel)

            if not best:
                continue
            _score, new, rel = best
            for hit in token_hits[old]:
                row = rows[hit.row_index]
                source = row.get("Fuente")
                if source in SKIP_TARGET_SOURCES:
                    continue
                if is_after_archaic_annotation(hit.translation, hit.end):
                    continue
                source_text = row_source_text(row)
                if old in source_text and old not in strip_accents(str(row.get(FIELD) or "")).lower():
                    continue
                proposals[(hit.row_index, old, new)] = {
                    "record_id": row.get("record_id"),
                    "source": source,
                    "lemma": row.get("Texto estandarizado"),
                    "old_token": old,
                    "new_token": new,
                    "relation": rel,
                    "old_count": global_counts[old],
                    "new_count": global_counts[new],
                    "context": context_window(hit.translation, hit.start, hit.end),
                    "old_translation": row.get(FIELD),
                }

    return sorted(
        proposals.values(),
        key=lambda item: (
            str(item["source"]),
            str(item["lemma"]),
            str(item["old_token"]),
            str(item["record_id"]),
        ),
    )


def apply_proposals(rows: list[dict[str, object]], proposals: list[dict[str, object]]) -> list[dict[str, object]]:
    by_record: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in proposals:
        by_record[str(item["record_id"])].append(item)

    report = []
    for row in rows:
        record_id = str(row.get("record_id") or "")
        items = by_record.get(record_id)
        if not items:
            continue
        old_translation = str(row.get(FIELD) or "")
        new_translation = old_translation
        reasons = []
        for item in items:
            old_token = str(item["old_token"])
            new_token = str(item["new_token"])
            pattern = re.compile(rf"\b{re.escape(old_token)}\b", re.I)

            def repl(match: re.Match[str]) -> str:
                if is_after_archaic_annotation(new_translation, match.end()):
                    return match.group(0)
                return preserve_case(match.group(0), new_token)

            updated = pattern.sub(repl, new_translation)
            if updated != new_translation:
                new_translation = updated
                reasons.append(f"{old_token}_to_{new_token}:{item['relation']}")
        new_translation = clean_duplicate_normalizations(new_translation, reasons)
        if new_translation != old_translation:
            row[FIELD] = new_translation
            report.append(
                {
                    "record_id": row.get("record_id"),
                    "source": row.get("Fuente"),
                    "lemma": row.get("Texto estandarizado"),
                    "reasons": sorted(set(reasons)),
                    "old_translation": old_translation,
                    "new_translation": new_translation,
                }
            )
    return report


def clean_duplicate_normalizations(text: str, reasons: list[str]) -> str:
    cleaned = text
    replacements = [
        (re.compile(r"\bpunzar\s+\[punzar\]", re.I), "punzar", "drop_duplicate_punzar_bracket"),
        (re.compile(r"\benlazar\s+\[enlazar\]", re.I), "enlazar", "drop_duplicate_enlazar_bracket"),
        (re.compile(r"\bdibujo,\s*i\.\s*dibujo\b", re.I), "dibujo", "drop_duplicate_dibujo"),
        (re.compile(r"\bsaúco,\s*o\s+saúco\b", re.I), "saúco", "drop_duplicate_sauco"),
        (re.compile(r"\bcaballeriza\s*/\s*caballeriza\b", re.I), "caballeriza", "drop_duplicate_caballeriza"),
        (re.compile(r"\bturbar\s+o\s+turbar\b", re.I), "turbar", "drop_duplicate_turbar"),
    ]
    for pattern, replacement, reason in replacements:
        updated, count = pattern.subn(replacement, cleaned)
        if count:
            cleaned = updated
            reasons.append(reason)
    return cleaned


def read_rows() -> list[dict[str, object]]:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def write_rows(rows: list[dict[str, object]]) -> None:
    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = read_rows()
    lexicon, lexicon_folded = load_lexicon()
    proposals = build_candidates(rows, lexicon, lexicon_folded)

    with REVIEW_PATH.open("w", encoding="utf-8") as fh:
        for item in proposals:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    report = apply_proposals(rows, proposals)

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    if args.apply:
        write_rows(rows)

    print(f"proposals={len(proposals)}")
    print(f"changed_rows={len(report)}")
    print(f"applied={args.apply}")
    print(f"review={REVIEW_PATH}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
