"""Phase 3 — validate rules against the full gold corpus.

Runs `rules.normalize_phrase` on every gold pair (single + aligned_multi),
reports exact-match accuracy and a soft-match metric that treats i/y and u/o
as equivalent (since those alternations are lexical, not phonological).

Writes:
  phase3_report.txt       — headline accuracy
  phase3_misses.jsonl     — every non-exact miss, with eo/te/pred
"""
import json
import re
import unicodedata
from pathlib import Path

from rules import normalize_phrase

HERE = Path(__file__).resolve().parent
PAIRS = HERE / "pairs.jsonl"
MISSES = HERE / "phase3_misses.jsonl"
REPORT = HERE / "phase3_report.txt"


def soft_key(s: str) -> str:
    # Collapse i/y and u/o so we can measure how many misses are purely
    # lexical alternation noise.
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"[iy]", "i", s)
    s = re.sub(r"[uo]", "u", s)
    return s


def main():
    pairs = [json.loads(l) for l in PAIRS.open(encoding="utf-8") if l.strip()]

    buckets = {"single_token": [], "aligned_multi": [], "mismatched": []}
    for p in pairs:
        buckets[p["category"]].append(p)

    out_misses = []
    lines = []
    for cat in ("single_token", "aligned_multi"):
        rows = buckets[cat]
        exact = 0
        soft = 0
        for p in rows:
            pred = normalize_phrase(p["eo"])
            gold = p["te"].lower()
            if pred == gold:
                exact += 1
                soft += 1
            elif soft_key(pred) == soft_key(gold):
                soft += 1
                out_misses.append({"cat": cat, "record_id": p["record_id"],
                                   "eo": p["eo"], "te": p["te"], "pred": pred, "soft": True})
            else:
                out_misses.append({"cat": cat, "record_id": p["record_id"],
                                   "eo": p["eo"], "te": p["te"], "pred": pred, "soft": False})
        n = len(rows)
        lines.append(f"{cat:16s}  n={n:5d}  exact={exact} ({exact/n:.1%})  soft(i=y, u=o)={soft} ({soft/n:.1%})")

    # Overall across gold
    total = sum(len(buckets[c]) for c in ("single_token", "aligned_multi"))
    exact_total = sum(1 for m in out_misses) if False else None  # placeholder
    # Recompute cleanly:
    total_exact = 0
    total_soft = 0
    for cat in ("single_token", "aligned_multi"):
        for p in buckets[cat]:
            pred = normalize_phrase(p["eo"])
            gold = p["te"].lower()
            if pred == gold:
                total_exact += 1
                total_soft += 1
            elif soft_key(pred) == soft_key(gold):
                total_soft += 1
    lines.append("")
    lines.append(f"TOTAL (single + aligned)  n={total}  exact={total_exact} ({total_exact/total:.1%})  soft={total_soft} ({total_soft/total:.1%})")

    with MISSES.open("w", encoding="utf-8") as f:
        for m in out_misses:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
