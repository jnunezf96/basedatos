#!/usr/bin/env python3
import gzip
import html
import json
import os
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "wimmer_cross_reference_translation_report.jsonl"


CF_RE = re.compile(r"^\s*(?:Cf\.|Ver|Véase|Cfr\.)\s+(.+?)\.?\s*$", re.I)
NOISE_WORDS = {
    "la",
    "las",
    "el",
    "los",
    "variante",
    "variantes",
    "forma",
    "formas",
    "radical",
    "articulo",
    "article",
    "tambien",
    "aussi",
}
BLOCKING_WORDS = {
    "debajo",
    "bajo",
    "sobre",
    "en",
    "de",
    "del",
    "con",
    "para",
    "y",
    "e",
    "o",
    "ou",
    "voir",
    "sous",
}
TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñĀĒĪŌŪāēīōūÂÊÎÔÛâêîôûÇç'-]+")


def key(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.lower().replace("ꞌ", "'")
    text = re.sub(r"[^a-z0-9\s'-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .;:,()[]{}\n\t")
    return text


def simple_cf_target(translation: str) -> str | None:
    match = CF_RE.match(translation or "")
    if not match:
        return None

    rest = html.unescape(match.group(1))
    rest = re.sub(r"\([^)]*\)", " ", rest)
    rest = rest.split(",", 1)[0].split(";", 1)[0]
    tokens = [tok.strip("'-") for tok in TOKEN_RE.findall(rest)]
    tokens = [tok for tok in tokens if tok]
    normalized = [key(tok) for tok in tokens]

    content = [
        original
        for original, normalized_token in zip(tokens, normalized)
        if normalized_token and normalized_token not in NOISE_WORDS
    ]
    content_keys = [key(tok) for tok in content]

    if len(content) != 1:
        return None
    if any(tok in BLOCKING_WORDS for tok in content_keys):
        return None
    if any(tok in BLOCKING_WORDS for tok in normalized if tok not in NOISE_WORDS and tok not in content_keys):
        return None
    return content_keys[0]


def is_cf_only(translation: str) -> bool:
    return bool(CF_RE.match(translation or ""))


def is_usable_translation(text: str) -> bool:
    if not text or is_cf_only(text):
        return False
    if re.search(r"<[^>]+>|&(?:#\d+|[a-z]+);", text):
        return False
    return True


def choose_target(candidates: list[dict], source_id: str) -> dict | None:
    candidates = [row for row in candidates if row.get("record_id") != source_id]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    non_cf = [row for row in candidates if is_usable_translation(row.get("Traducción (es)", "") or "")]
    if len(non_cf) == 1:
        return non_cf[0]

    translations = {row.get("Traducción (es)", "") for row in non_cf}
    if len(translations) == 1 and translations:
        return non_cf[0]
    return None


def main() -> None:
    rows = []
    by_key: dict[str, list[dict]] = {}

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            rows.append(row)
            if row.get("Fuente") == "2021 Wimmer":
                by_key.setdefault(key(row.get("Texto estandarizado", "")), []).append(row)

    report = []

    def resolve(row: dict, seen: set[str]) -> tuple[str | None, str]:
        record_id = row.get("record_id", "")
        if record_id in seen:
            return None, "cycle"
        seen.add(record_id)

        translation = row.get("Traducción (es)", "") or ""
        if is_usable_translation(translation):
            return translation, "direct"

        target_key = simple_cf_target(translation)
        if not target_key:
            return None, "not-simple"

        target = choose_target(by_key.get(target_key, []), record_id)
        if not target:
            return None, f"unresolved:{target_key}"

        resolved, how = resolve(target, seen)
        if resolved:
            return resolved, f"{target_key}>{how}"
        return None, how

    for row in rows:
        if row.get("Fuente") != "2021 Wimmer":
            continue
        old_translation = row.get("Traducción (es)", "") or ""
        if not is_cf_only(old_translation):
            continue

        resolved, reason = resolve(row, set())
        if not resolved or resolved == old_translation:
            continue

        row["Traducción (es)"] = resolved
        report.append(
            {
                "record_id": row.get("record_id"),
                "lemma": row.get("Texto estandarizado"),
                "old_translation_es": old_translation,
                "new_translation_es": resolved,
                "reason": reason,
            }
        )

    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(report)}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
