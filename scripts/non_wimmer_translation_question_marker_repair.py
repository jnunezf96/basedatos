#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from non_wimmer_translation_normalize_pass import (  # noqa: E402
    DATA_PATH,
    REPORT_PATH,
    normalize_translation,
)

REPAIR_REPORT_PATH = ROOT / "scripts" / "non_wimmer_translation_question_marker_repair_report.jsonl"
QUESTION_MARKER_JOIN_RE = re.compile(r"(?<![¿?])(?<=\S)\?(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])")


def main() -> None:
    original_report = []
    expected_by_id = {}

    with REPORT_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            final_translation, final_reasons = normalize_translation(
                item["old_translation"], item["source"]
            )
            repaired_translation = QUESTION_MARKER_JOIN_RE.sub(" ?", final_translation)
            if repaired_translation != final_translation:
                final_translation = repaired_translation
                if "question_marker_spacing" not in final_reasons:
                    final_reasons.append("question_marker_spacing")
            item["new_translation"] = final_translation
            item["reasons"] = final_reasons
            original_report.append(item)
            expected_by_id[item["record_id"]] = item

    rows = []
    repairs = []
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            item = expected_by_id.get(row.get("record_id"))
            if item:
                old_current = row.get("Traducción") or ""
                final = item["new_translation"]
                if old_current != final:
                    row["Traducción"] = final
                    repairs.append(
                        {
                            "record_id": row.get("record_id"),
                            "source": row.get("Fuente"),
                            "lemma": row.get("Texto estandarizado"),
                            "old_current_translation": old_current,
                            "repaired_translation": final,
                        }
                    )
            rows.append(row)

    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in original_report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    with REPAIR_REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in repairs:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"repaired_rows={len(repairs)}")
    print(f"report={REPAIR_REPORT_PATH}")


if __name__ == "__main__":
    main()
