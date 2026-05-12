#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import DefaultDict


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "edition_plus_decondense_report.jsonl"

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿÇç§ƺ\[\]_-]+|\d+|\?")
PLUS_RE = re.compile(r"\s*\+\s*$")
REF_RE = re.compile(r"^(?:vide|vid[eé]|vease|véase|cf\.?)\b", re.I)

# These rows need structural knowledge that is not recoverable from token-by-token
# evidence alone.
CURATED_FIXES = {
    # The `nitlatla` tail is the separated subject/object notation here.
    "1571-molina-2:000303": "yahualoa",
    "1571-molina-2:000304": "yohuilia",
    # Both tokens are old spellings of the phrase; the head should not collapse
    # to only the second token.
    "1765-cortes-y-zedeno:000047": "tlaxilia tlatlacolli",
    # Fused, single-token originals that require decompounding.
    "1984-tzinacapan:000980": "iztac cueitl",
    "1984-tzinacapan:002288": "canachi",
    "1551-95-documentos-nahuas-de-la-ciudad-de-mexico:000891": "in ic etlamantli",
    "1571-molina-1:014139": "tlayohuallotl ipam momanqui",
    # Cortés/Zedeño `amoquali` phrase rows.
    "1765-cortes-y-zedeno:002463": "chihua amo cualli",
    "1765-cortes-y-zedeno:002464": "cuepa amo cualli",
    "1765-cortes-y-zedeno:002467": "ima amo cualli",
    "1571-molina-2:012354": "nacatl amo yollo",
    # `huel/ +` rows whose original uses `vel` as a variant separator.
    "1571-molina-2:008418": "tecetilianime; tecetilique",
    "1571-molina-2:008419": "tencuacuauhti",
    "1571-molina-2:008420": "tlaixmaniliztli; tlaixmanaliztli",
    "1571-molina-2:008421": "tlanemilia",
    "1571-molina-1:014636": "itta",
}

# Sources with very different normalization policy should not decide global
# fallback spellings for the historical `+` rows. They can still decide their own
# source-specific rows.
GLOBAL_EXCLUDED_SOURCE_PREFIXES = ("2021 Wimmer", "1992 Karttunen", "V94")

# Standalone grammar/person markers are only dropped when punctuation makes them
# notation-like. The same strings may be lexical in uninterrupted phrases.
PUNCTUATED_MARKERS = {
    "3",
    "am",
    "an",
    "n",
    "ni",
    "nic",
    "nicno",
    "nictla",
    "nictlatla",
    "niman",
    "nimitz",
    "nin",
    "nino",
    "ninote",
    "nite",
    "nitla",
    "nitlatla",
    "no",
    "ti",
    "tic",
    "timitz",
    "tite",
    "titla",
    "to",
}

PERSON_PREFIXES = (
    "nictlatla",
    "nictla",
    "nitlatla",
    "nitla",
    "ninote",
    "nino",
    "nimitz",
    "timitz",
    "tictla",
    "titla",
    "quin",
    "quim",
    "nic",
    "non",
    "nin",
    "nite",
    "tite",
    "tic",
    "qui",
    "ni",
    "no",
    "mo",
    "ti",
    "ne",
    "n",
    "m",
)


@dataclass
class TokenChoice:
    value: str
    reason: str


@dataclass
class Evidence:
    source_exact: DefaultDict[str, DefaultDict[str, Counter]]
    source_skeleton: DefaultDict[str, DefaultDict[str, Counter]]
    global_exact: DefaultDict[str, Counter]
    global_skeleton: DefaultDict[str, Counter]
    vocab_skeleton: DefaultDict[str, Counter]
    phrase_source: DefaultDict[str, DefaultDict[str, Counter]]
    phrase_global: DefaultDict[str, Counter]


def replace_legacy_chars(value: str) -> str:
    # Do this before decomposing accents; otherwise ç becomes plain c.
    return (
        (value or "")
        .replace("Ç", "Z")
        .replace("ç", "z")
        .replace("ƺ", "z")
        .replace("§", "s")
    )


def strip_accents(value: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", replace_legacy_chars(value))
        if unicodedata.category(ch) != "Mn"
    )


def clean_token(value: str) -> str:
    text = strip_accents(value).lower()
    text = text.replace("[", "").replace("]", "").replace("_", "").replace("-", "")
    return re.sub(r"[^a-z0-9?]+", "", text)


def skeleton(value: str) -> str:
    text = clean_token(value)
    text = (
        text.replace("hu", "u")
        .replace("uh", "u")
        .replace("qu", "k")
        .replace("c", "k")
        .replace("z", "s")
        .replace("h", "")
    )
    return text


def iy_key(value: str) -> str:
    return clean_token(value).replace("y", "i")


def tokens_with_spans(value: str) -> list[tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in WORD_RE.finditer(value or "")]


def tokens(value: str) -> list[str]:
    return [token for token, _start, _end in tokens_with_spans(value)]


def token_values(value: str) -> list[str]:
    return [clean_token(token) for token in tokens(value) if clean_token(token)]


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", " ".join(token_values(value))).strip()


def phrase_key(value: str) -> str:
    return " ".join(skeleton(token) for token in token_values(value) if skeleton(token))


def edition_base(value: str) -> str:
    return PLUS_RE.sub("", value or "").strip(" ;,/")


def source_excluded_from_global(source: str | None) -> bool:
    return any((source or "").startswith(prefix) for prefix in GLOBAL_EXCLUDED_SOURCE_PREFIXES)


def best(counter: Counter | None, *, min_count: int, min_ratio: float) -> tuple[str | None, int, int]:
    if not counter:
        return None, 0, 0
    total = sum(counter.values())
    value, count = counter.most_common(1)[0]
    if count >= min_count and count / total >= min_ratio:
        return value, count, total
    return None, count, total


def build_evidence(rows: list[dict]) -> Evidence:
    evidence = Evidence(
        source_exact=defaultdict(lambda: defaultdict(Counter)),
        source_skeleton=defaultdict(lambda: defaultdict(Counter)),
        global_exact=defaultdict(Counter),
        global_skeleton=defaultdict(Counter),
        vocab_skeleton=defaultdict(Counter),
        phrase_source=defaultdict(lambda: defaultdict(Counter)),
        phrase_global=defaultdict(Counter),
    )

    for row in rows:
        source = row.get("Fuente")
        original = row.get("Escritura original") or ""
        edition = row.get("Texto estandarizado") or ""
        if "+" in edition:
            continue

        original_tokens = token_values(original)
        edition_tokens = token_values(edition)
        if not original_tokens or not edition_tokens:
            continue

        clean_edition = normalized_text(edition)
        original_phrase_key = phrase_key(original)
        if original_phrase_key and clean_edition:
            evidence.phrase_source[source][original_phrase_key][clean_edition] += 1
            if not source_excluded_from_global(source):
                evidence.phrase_global[original_phrase_key][clean_edition] += 1

        for edition_token in edition_tokens:
            evidence.vocab_skeleton[skeleton(edition_token)][edition_token] += 1

        if len(original_tokens) != len(edition_tokens) or len(original_tokens) > 12:
            continue

        for original_token, edition_token in zip(original_tokens, edition_tokens):
            evidence.source_exact[source][original_token][edition_token] += 1
            evidence.source_skeleton[source][skeleton(original_token)][edition_token] += 1
            if not source_excluded_from_global(source):
                evidence.global_exact[original_token][edition_token] += 1
                evidence.global_skeleton[skeleton(original_token)][edition_token] += 1

    return evidence


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(
                min(
                    prev[j] + 1,
                    cur[j - 1] + 1,
                    prev[j - 1] + (0 if ca == cb else 1),
                )
            )
        prev = cur
    return prev[-1]


def close_to_base(token: str, base_token: str) -> bool:
    if len(base_token) < 3:
        return token == base_token or skeleton(token) == skeleton(base_token)
    if token == base_token:
        return True
    if skeleton(token) == skeleton(base_token):
        return True
    if iy_key(token) == iy_key(base_token):
        return True

    max_len = max(len(token), len(base_token))
    if max_len <= 5:
        return levenshtein(token, base_token) <= 1 or levenshtein(
            skeleton(token), skeleton(base_token)
        ) <= 1
    threshold = max(1, round(max_len * 0.18))
    return levenshtein(token, base_token) <= threshold or levenshtein(
        skeleton(token), skeleton(base_token)
    ) <= threshold


def base_match(token: str, base_tokens: set[str]) -> str | None:
    candidates = [base_token for base_token in base_tokens if close_to_base(token, base_token)]
    if not candidates:
        return None
    return min(candidates, key=lambda base_token: (levenshtein(token, base_token), len(base_token)))


def preserve_person_prefix(token: str, candidate: str) -> tuple[str, bool]:
    if not token or not candidate or token == candidate:
        return candidate, False
    if len(candidate) >= len(token):
        return candidate, False

    options: list[tuple[int, int, str]] = []
    for prefix in PERSON_PREFIXES:
        if not token.startswith(prefix) or len(token) <= len(prefix) + 1:
            continue
        remainder = token[len(prefix) :]
        if close_to_base(remainder, candidate):
            options.append((levenshtein(remainder, candidate), -len(prefix), prefix + candidate))

    if options:
        _distance, _neg_len, adjusted = min(options)
        return adjusted, True

    return candidate, False


def choose_from_evidence(
    token: str, source: str | None, base_tokens: set[str], evidence: Evidence
) -> TokenChoice:
    cleaned = clean_token(token)
    if not cleaned:
        return TokenChoice("", "empty")

    matched_base = base_match(cleaned, base_tokens)
    if matched_base:
        adjusted, preserved = preserve_person_prefix(cleaned, matched_base)
        if preserved:
            return TokenChoice(adjusted, "prefix_preserved_base")
        if cleaned == matched_base:
            return TokenChoice(matched_base, "base_exact")
        return TokenChoice(matched_base, "base_close")

    skel = skeleton(cleaned)
    checks = (
        (evidence.source_exact[source].get(cleaned), 1, 0.60, "source_exact"),
        (evidence.source_skeleton[source].get(skel), 1, 0.60, "source_skeleton"),
        (evidence.global_exact.get(cleaned), 2, 0.75, "global_exact"),
        (evidence.global_skeleton.get(skel), 3, 0.75, "global_skeleton"),
        (evidence.vocab_skeleton.get(skel), 5, 0.85, "vocab_skeleton"),
    )
    for counter, min_count, min_ratio, reason in checks:
        value, count, total = best(counter, min_count=min_count, min_ratio=min_ratio)
        if value:
            adjusted, preserved = preserve_person_prefix(cleaned, value)
            if preserved:
                return TokenChoice(adjusted, f"prefix_preserved_{reason}:{count}/{total}")
            return TokenChoice(value, f"{reason}:{count}/{total}")

    return TokenChoice(cleaned, "cleaned_original")


def is_variant_marker(original: str, token: str, start: int, end: int) -> bool:
    cleaned = clean_token(token)
    if cleaned not in {"vel", "uel"}:
        return False
    before = original[max(0, start - 4) : start]
    after = original[end : min(len(original), end + 4)]
    return bool(re.search(r"[,;/]\s*$", before) or re.search(r"^\s*[,;/]", after))


def is_punctuated_marker(original: str, token: str, start: int, end: int) -> bool:
    cleaned = clean_token(token)
    if cleaned not in PUNCTUATED_MARKERS:
        return False

    before = original[max(0, start - 4) : start]
    after = original[end : min(len(original), end + 4)]
    return bool(re.search(r"[,;/]\s*$", before) or re.search(r"^\s*[,;/]", after))


def significant_tokens(original: str) -> tuple[list[str], list[str]]:
    kept: list[str] = []
    dropped: list[str] = []
    for token, start, end in tokens_with_spans(original):
        if is_variant_marker(original, token, start, end):
            dropped.append(f"{clean_token(token)}:variant_marker")
            continue
        if is_punctuated_marker(original, token, start, end):
            dropped.append(f"{clean_token(token)}:punctuated_marker")
            continue
        kept.append(token)
    return kept, dropped


def phrase_evidence(row: dict, evidence: Evidence) -> tuple[str | None, str]:
    key = phrase_key(row.get("Escritura original") or "")
    source = row.get("Fuente")
    kept_tokens, _dropped = significant_tokens(row.get("Escritura original") or "")
    min_token_count = len([token for token in kept_tokens if clean_token(token)])

    value, count, total = best(
        evidence.phrase_source[source].get(key), min_count=1, min_ratio=0.75
    )
    if value and len(token_values(value)) >= min_token_count:
        return value, f"source_phrase:{count}/{total}"
    value, count, total = best(evidence.phrase_global.get(key), min_count=1, min_ratio=0.75)
    if value and len(token_values(value)) >= min_token_count:
        return value, f"global_phrase:{count}/{total}"
    return None, ""


def proposed_edition(row: dict, evidence: Evidence) -> tuple[str, dict]:
    record_id = row.get("record_id") or ""
    original = row.get("Escritura original") or ""
    old_edition = row.get("Texto estandarizado") or ""
    base = edition_base(old_edition)

    meta = {
        "decision": "apply",
        "source_evidence": "",
        "global_evidence": "",
        "orthography_reason": "",
        "i_y_reason": "",
        "t_reason": "",
        "semantic_note": "",
        "dropped_markers": "",
    }

    curated = CURATED_FIXES.get(record_id)
    if curated:
        meta["decision"] = "apply_curated"
        meta["orthography_reason"] = "curated"
        return curated, meta

    phrase_value, phrase_reason = phrase_evidence(row, evidence)
    if phrase_value and phrase_value != normalized_text(old_edition):
        meta["decision"] = "apply_phrase_evidence"
        if phrase_reason.startswith("source"):
            meta["source_evidence"] = phrase_reason
        else:
            meta["global_evidence"] = phrase_reason
        return phrase_value, meta

    base_tokens = set(token_values(base))
    kept_tokens, dropped_markers = significant_tokens(original)
    choices = [choose_from_evidence(token, row.get("Fuente"), base_tokens, evidence) for token in kept_tokens]
    proposed = re.sub(r"\s+", " ", " ".join(choice.value for choice in choices if choice.value)).strip()

    reasons = Counter(choice.reason.split(":")[0] for choice in choices if choice.reason)
    meta["orthography_reason"] = "; ".join(f"{key}={value}" for key, value in sorted(reasons.items()))
    meta["dropped_markers"] = "; ".join(dropped_markers)

    old_clean = clean_token(original)
    new_clean = clean_token(proposed)
    if old_clean.replace("y", "i") == new_clean.replace("y", "i") and old_clean != new_clean:
        meta["i_y_reason"] = "i/y-normalized"
    if old_clean.replace("tl", "t").replace("tt", "t") != new_clean.replace("tl", "t").replace(
        "tt", "t"
    ):
        meta["t_reason"] = "t-family-normalized"

    if REF_RE.search(original.strip()):
        meta["semantic_note"] = "reference-like original"

    return proposed, meta


def read_rows() -> list[dict]:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def write_rows(rows: list[dict]) -> None:
    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes to data/data.jsonl.gz")
    parser.add_argument(
        "--report-path",
        default=str(REPORT_PATH),
        help="write the JSONL report here; defaults to scripts/edition_plus_decondense_report.jsonl",
    )
    args = parser.parse_args()

    rows = read_rows()
    evidence = build_evidence(rows)
    report = []
    changed = 0

    for row in rows:
        old_edition = row.get("Texto estandarizado") or ""
        if "+" not in old_edition:
            continue

        new_edition, meta = proposed_edition(row, evidence)
        if not new_edition or new_edition == old_edition:
            meta["decision"] = "review_unresolved"
            new_edition = edition_base(old_edition)
        if "+" in new_edition:
            meta["decision"] = "review_plus_remaining"

        report_item = {
            "record_id": row.get("record_id"),
            "source": row.get("Fuente"),
            "decision": meta["decision"],
            "safe_to_apply": not meta["decision"].startswith("review"),
            "original": row.get("Escritura original"),
            "old_edition": old_edition,
            "new_edition": new_edition,
            "translation": row.get("Traducción"),
            "source_evidence": meta["source_evidence"],
            "global_evidence": meta["global_evidence"],
            "orthography_reason": meta["orthography_reason"],
            "i_y_reason": meta["i_y_reason"],
            "t_reason": meta["t_reason"],
            "semantic_note": meta["semantic_note"],
            "dropped_markers": meta["dropped_markers"],
        }
        report.append(report_item)

        if args.apply and report_item["safe_to_apply"]:
            row["Texto estandarizado"] = new_edition
            changed += 1

    report_path = Path(args.report_path)
    with report_path.open("w", encoding="utf-8") as fh:
        for item in report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    if args.apply:
        write_rows(rows)

    safe_count = sum(1 for item in report if item["safe_to_apply"])
    review_count = len(report) - safe_count
    print(f"plus_rows={len(report)}")
    print(f"safe_rows={safe_count}")
    print(f"review_rows={review_count}")
    print(f"changed_rows={changed if args.apply else 0}")
    print(f"applied={args.apply}")
    print(f"report={report_path}")


if __name__ == "__main__":
    main()
