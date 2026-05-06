"""Replace compact Wimmer role labels with the original `*~` grammar markers.

Example:
    algo: envolver algo.
becomes:
    v.t. tla-., envolver algo.

The replacement is driven by each row's `Comentario (es)` section markers, not
by a global hard-coded map, so variants like `v.bitrans. motē-` remain as
Wimmer has them.
"""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

import wimmer_translation_pilot as pilot


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "data.jsonl.gz"
REPORT = ROOT / "scripts" / "wimmer_original_grammar_marker_report.jsonl"

COMPACT_SEGMENT_RE = re.compile(
    r"^\s*(persona\s+\+\s+algo|reflexivo\s+\+\s+persona|reflexivo\s+\+\s+algo|"
    r"persona\s*/\s*algo|persona/algo|sujeto\s+inanimado|pasivo\s+impersonal|"
    r"algo|persona|reflexivo|pasivo|impersonal|intransitivo|transitivo|"
    r"rec[ií]proco|bitransitivo)\s*:\s*(.+)$"
    r"|^\s*(refl\.)\s*,\s*(.+)$",
    re.IGNORECASE,
)

FALLBACK_MARKERS = {
    "algo": "v.t. tla-",
    "persona": "v.t. tē-",
    "persona/algo": "v.t. tē-. o tla-",
    "persona / algo": "v.t. tē-. o tla-",
    "persona + algo": "v.bitrans. tētla-",
    "reflexivo": "v.refl",
    "refl.": "v.refl",
    "reflexivo + algo": "v.bitrans. motla-",
    "reflexivo + persona": "v.bitrans. motē-",
    "pasivo": "v.refl. con significado pasivo",
    "pasivo impersonal": "v.pasivo-impers",
    "impersonal": "v.impers",
    "intransitivo": "v.i",
    "transitivo": "v.t",
    "recíproco": "v.recipr",
    "reciproco": "v.recipr",
    "sujeto inanimado": "v.inanim",
    "bitransitivo": "v.bitrans",
}


def role_key(value: str) -> str:
    return re.sub(r"\s+", " ", pilot.normalize(value or "").strip())


def marker_for_segment(role: str, body: str, candidates: list[pilot.Candidate]) -> str | None:
    matches = [candidate for candidate in candidates if candidate.role_label and role_key(candidate.role) == role_key(role)]
    if not matches:
        return None
    scored = sorted(
        ((pilot.overlap_score(body, candidate.text), candidate.index, candidate) for candidate in matches),
        key=lambda item: (-item[0], item[1]),
    )
    if scored and scored[0][0] >= 0.25:
        return scored[0][2].role_label
    labels = sorted({candidate.role_label for candidate in matches if candidate.role_label})
    if len(labels) == 1:
        return labels[0]
    return scored[0][2].role_label if scored else FALLBACK_MARKERS.get(role_key(role))


def convert_translation(row: dict) -> tuple[str, list[dict]]:
    old = row.get("Traducción (es)") or ""
    if ":" not in old:
        return old, []
    candidates = pilot.collect_candidates(row)
    changes: list[dict] = []
    parts: list[str] = []
    for segment in re.split(r"\s*/\s*", old):
        match = COMPACT_SEGMENT_RE.match(segment)
        if not match:
            parts.append(segment)
            continue
        role = match.group(1) or match.group(3)
        body = (match.group(2) or match.group(4)).strip()
        marker = marker_for_segment(role, body, candidates)
        if not marker:
            marker = FALLBACK_MARKERS.get(role_key(role))
        if not marker:
            parts.append(segment)
            continue
        replacement = f"{marker}., {body}"
        parts.append(replacement)
        changes.append({"from": segment, "to": replacement})
    return " / ".join(parts), changes


def main() -> None:
    report_rows: list[dict] = []
    tmp = DATA.with_suffix(".jsonl.gz.tmp")
    with gzip.open(DATA, "rt", encoding="utf-8") as fin, gzip.open(tmp, "wt", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("Fuente") == "2021 Wimmer":
                new_translation, changes = convert_translation(row)
                if changes:
                    old_translation = row.get("Traducción (es)", "")
                    row["Traducción (es)"] = new_translation
                    report_rows.append(
                        {
                            "record_id": row.get("record_id", ""),
                            "lemma": row.get("Texto estandarizado", ""),
                            "old_translation_es": old_translation,
                            "new_translation_es": new_translation,
                            "changes": changes,
                        }
                    )
            fout.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    tmp.replace(DATA)
    with REPORT.open("w", encoding="utf-8") as fout:
        for row in report_rows:
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"updated={len(report_rows)}")
    print(f"report={REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
