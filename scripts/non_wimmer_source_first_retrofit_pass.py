#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
RAW_PATH = ROOT / "data" / "data.jsonl.bak1.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_source_first_retrofit_report.jsonl"
SKIP_SOURCES = {"2021 Wimmer", "1992 Karttunen", "V94 Diccionario Global SNP"}


def load_raw(path: Path) -> dict[str, str]:
    raw: dict[str, str] = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            raw[row.get("record_id") or ""] = row.get("Traducción") or ""
    return raw


def replace_first(text: str, pattern: str, replacement: str) -> tuple[str, bool]:
    new, count = re.subn(pattern, replacement, text, count=1, flags=re.I)
    return new, bool(count)


def has(raw: str, pattern: str) -> bool:
    return re.search(pattern, raw, re.I) is not None


def retrofit(raw: str, current: str) -> tuple[str, list[str]]:
    new = current
    reasons: list[str] = []

    if "arcaico:" in new:
        return new, reasons

    if has(raw, r"\bbaladrear\b") and re.search(r"\bfanfarronear\b", new, re.I):
        new, changed = replace_first(new, r"\bfanfarronear\b", "baladrear (arcaico: fanfarronear)")
        if changed:
            reasons.append("baladrear_source_first")

    if has(raw, r"\b(?:bolliciar|bulliciar)\b") and re.search(r"\balborotar\b", new, re.I):
        new, changed = replace_first(new, r"\balborotar\b", "bulliciar (arcaico: alborotar)")
        if changed:
            reasons.append("bulliciar_source_first")

    if has(raw, r"\bemba[çz]arse\b"):
        new, changed = replace_first(
            new,
            r"\bquedarse\s+pasmado\b",
            "embazarse (arcaico: quedarse pasmado)",
        )
        if changed:
            reasons.append("embazarse_source_first")

    if has(raw, r"\bemba[çz]ar\b"):
        new, changed = replace_first(
            new,
            r"\bquedar\s+pasmado\b",
            "embazar (arcaico: quedar pasmado)",
        )
        if changed:
            reasons.append("embazar_source_first")

    if has(raw, r"\bemba[çz][aá]d[ao]\b"):
        new, changed = replace_first(new, r"\bpasmad[ao]\b", "embazado (arcaico: pasmado)")
        if changed:
            reasons.append("embazado_source_first")

    if has(raw, r"\boriniento\b") and re.search(r"\bmohoso\b", new, re.I):
        new, changed = replace_first(new, r"\bmohoso\b", "oriniento (arcaico: mohoso)")
        if changed:
            reasons.append("oriniento_source_first")

    if has(raw, r"\babarr?isco\b|\babarisco\b"):
        new, changed = replace_first(
            new,
            r"\benteramente\s+del\s+todo\b",
            "abarrisco (arcaico: enteramente del todo)",
        )
        if changed:
            reasons.append("abarrisco_source_first")
        elif new.startswith("llevar el ladrón"):
            new = "abarrisco (arcaico: enteramente del todo) " + new
            reasons.append("abarrisco_source_first")

    if has(raw, r"\b[ee]n?m?beodarse\b"):
        new, changed = replace_first(new, r"\bembriagarse\b", "embeodarse (arcaico: embriagarse)")
        if changed:
            reasons.append("embeodarse_source_first")

    if has(raw, r"\b[ee]n?m?beodar\b"):
        new, changed = replace_first(new, r"\bembriagar\b", "embeodar (arcaico: embriagar)")
        if changed:
            reasons.append("embeodar_source_first")

    if has(raw, r"\b[ee]n?m?beoda\b"):
        new, changed = replace_first(new, r"\bembriaga\b", "embeoda (arcaico: embriaga)")
        if changed:
            reasons.append("embeoda_source_first")

    if has(raw, r"\b[ee]n?m?beodan\b"):
        new, changed = replace_first(new, r"\bembriagan\b", "embeodan (arcaico: embriagan)")
        if changed:
            reasons.append("embeodan_source_first")

    if has(raw, r"\b[ee]n?m?beodamiento\b|\b[ee]n?m?beodamento\b") and has(
        raw, r"\bbeodez\b|\bveodez\b"
    ):
        new, changed = replace_first(
            new,
            r"\bembriaguez\b",
            "embeodamiento, beodez (arcaico: embriaguez)",
        )
        if changed:
            reasons.append("embeodamiento_beodez_source_first")
    elif has(raw, r"\b[ee]n?m?beodamiento\b|\b[ee]n?m?beodamento\b"):
        new, changed = replace_first(
            new,
            r"\bembriaguez\b",
            "embeodamiento (arcaico: embriaguez)",
        )
        if changed:
            reasons.append("embeodamiento_source_first")

    if has(raw, r"\bbeodez\b|\bveodez\b") and "beodez (arcaico:" not in new:
        if re.search(r"\(metáfora\s+de\s+la\s+embriaguez\)", new, re.I):
            new, changed = replace_first(
                new,
                r"\(metáfora\s+de\s+la\s+embriaguez\)",
                "(metáfora de la beodez; arcaico: embriaguez)",
            )
        else:
            new, changed = replace_first(new, r"\bembriaguez\b", "beodez (arcaico: embriaguez)")
        if changed:
            reasons.append("beodez_source_first")
        elif re.fullmatch(r"beodez\.?", new, re.I):
            new = re.sub(r"\bbeodez\b", "beodez (arcaico: embriaguez)", new, flags=re.I)
            reasons.append("beodez_source_first")

    if has(raw, r"\bbober[ií]a\b") and has(raw, r"\bbouedad\b|\bbobedad\b"):
        new, changed = replace_first(
            new,
            r"\bbobería\b",
            "bobería, o bobedad (arcaico: bobería)",
        )
        if changed:
            reasons.append("bobedad_source_first")
    elif has(raw, r"\bbouedad\b|\bbobedad\b"):
        new, changed = replace_first(new, r"\bbobería\b", "bobedad (arcaico: bobería)")
        if changed:
            reasons.append("bobedad_source_first")

    if has(raw, r"\brechabar\b") and re.search(r"\bagriar\b", new, re.I):
        new, changed = replace_first(new, r"\bagriar\b", "rechabar (arcaico: agriar)")
        if changed:
            reasons.append("rechabar_source_first")

    if has(raw, r"\bpecilgar\b") and re.search(r"\bpellizcar\b", new, re.I):
        new, changed = replace_first(new, r"\bpellizcar\b", "pecilgar (arcaico: pellizcar)")
        if changed:
            reasons.append("pecilgar_source_first")

    if has(raw, r"\bcovardeser\b") and re.search(r"\bser\s+cobarde\b", new, re.I):
        new, changed = replace_first(new, r"\bser\s+cobarde\b", "cobardecer (arcaico: ser cobarde)")
        if changed:
            reasons.append("covardeser_source_first")

    if has(raw, r"\bemba[çz]adura\b") and re.fullmatch(r"embazadura\.?", new, re.I):
        new = re.sub(
            r"\bembazadura\b",
            "embazadura (arcaico: pasmo o estupor)",
            new,
            flags=re.I,
        )
        reasons.append("embazadura_source_first")

    return new, reasons


def write_rows(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n", compresslevel=9) as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    tmp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--raw", type=Path, default=RAW_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    raw_by_id = load_raw(args.raw)
    rows: list[dict] = []
    report: list[dict] = []
    counts: Counter[str] = Counter()

    with gzip.open(args.data, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            record_id = row.get("record_id") or ""
            source = row.get("Fuente") or ""
            old = row.get("Traducción") or ""
            raw = raw_by_id.get(record_id, "")
            if source not in SKIP_SOURCES and raw and old:
                new, reasons = retrofit(raw, old)
                if new != old:
                    row["Traducción"] = new
                    counts.update(reasons)
                    report.append(
                        {
                            "record_id": record_id,
                            "source": source,
                            "lemma": row.get("Texto estandarizado"),
                            "reasons": reasons,
                            "raw_translation": raw,
                            "old_translation": old,
                            "new_translation": new,
                        }
                    )
            rows.append(row)

    args.report.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in report),
        encoding="utf-8",
    )

    if args.apply:
        write_rows(args.data, rows)

    print(f"mode={'apply' if args.apply else 'dry-run'}")
    print(f"changed_rows={len(report)}")
    print(f"report={args.report}")
    if counts:
        print("top_reasons=")
        for reason, count in counts.most_common():
            print(f"{reason}\t{count}")


if __name__ == "__main__":
    main()
