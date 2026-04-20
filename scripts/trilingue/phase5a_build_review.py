"""Phase 5a — emit a human-readable review file in per-record block format.

Reads phase4b_proposals.jsonl. Writes scripts/trilingue/review.txt with one
block per record, priority-sorted (flagged rows first).

Block format (editable):

════════════════════════════════════════════════════════════════════════════════
[FLAG]  153-trilingue:eid:1341732
EO    : vide mijankos dominica 8 posticath f
STUB  : 8
TE    : 8
NOTE  : EO is a bibliographic cross-reference, not a Nahuatl phrase...
ES    : Seguramente.

Edit only the TE line (keep the "TE    : " prefix exact). Don't touch the
record_id line or the separator. phase5b_commit.py parses blocks by
separator and extracts the TE value per record.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROPOSALS = HERE / "phase4b_proposals.jsonl"
PARTIALS = HERE / "partials.jsonl"
OUT = HERE / "review.txt"

JUNK_CHARS = set("ç^vÁÉÍÓÚáéíóú")
MARKER_RE = re.compile(r"\s*[\^*]+\s*$")
SEP = "═" * 80


def bare_stub(s: str) -> str:
    return MARKER_RE.sub("", s).strip().lower()


def is_flagged(row: dict) -> bool:
    if row.get("note"):
        return True
    if any(c in row["te"] for c in JUNK_CHARS):
        return True
    stub = bare_stub(row["te_stub"])
    if stub and stub not in row["te"].lower():
        return True
    return False


def collapse(s: str) -> str:
    """Collapse newlines/tabs inside a field so each field stays on one line."""
    return re.sub(r"\s+", " ", (s or "").strip())


def main():
    partials = {r["record_id"]: r for r in (json.loads(l) for l in PARTIALS.open(encoding="utf-8") if l.strip())}
    rows = [json.loads(l) for l in PROPOSALS.open(encoding="utf-8") if l.strip()]

    enriched = []
    for r in rows:
        p = partials.get(r["record_id"], {})
        enriched.append({
            **r,
            "traduccion": p.get("traduccion", ""),
            "flag": is_flagged(r),
        })
    enriched.sort(key=lambda r: (0 if r["flag"] else 1, r["record_id"]))

    lines = [
        "# Review file — edit ONLY the TE lines. Keep the \"TE    : \" prefix and separators intact.",
        "# Flagged rows (model uncertainty, residual junk, stub rewrites) are first.",
        "# Save when done, then run:  python3 scripts/trilingue/phase5b_commit.py --commit",
        "",
    ]
    for r in enriched:
        tag = "[FLAG] " if r["flag"] else "[OK]   "
        lines.append(SEP)
        lines.append(f"{tag}{r['record_id']}")
        lines.append(f"EO    : {collapse(r['eo'])}")
        lines.append(f"STUB  : {collapse(r['te_stub'])}")
        lines.append(f"TE    : {collapse(r['te'])}")
        note = collapse(r.get("note") or "")
        if note:
            lines.append(f"NOTE  : {note}")
        lines.append(f"ES    : {collapse(r['traduccion'])}")
        lines.append("")
    lines.append(SEP)

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    flagged = sum(1 for r in enriched if r["flag"])
    print(f"wrote {OUT.name}: {len(enriched)} records ({flagged} flagged, {len(enriched)-flagged} clean)")
    print(f"open in VS Code, edit TE lines as needed, then run phase5b_commit.py")


if __name__ == "__main__":
    main()
