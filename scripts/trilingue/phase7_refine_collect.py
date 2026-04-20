"""Phase 7 — poll + fetch the second refinement batch, rewrite review.txt.

Preserves ALL user edits from both prior review rounds. Only touches rows
the phase-7 pass refined.
"""
import json
import re
import sys
import time
from pathlib import Path

from anthropic import Anthropic

HERE = Path(__file__).resolve().parent
STATE = HERE / "_batch"
BATCH_ID_PATH = STATE / "phase7_batch_id.txt"
MAP_PATH = STATE / "phase7_map.json"
PROPOSALS = HERE / "phase4b_proposals.jsonl"
PARTIALS = HERE / "partials.jsonl"
REVIEW = HERE / "review.txt"
REFINEMENTS = HERE / "phase7_refinements.jsonl"
STATS = HERE / "phase7_stats.txt"

SEP = "═" * 80
HEADER_RE = re.compile(r"^\[(FLAG|OK|REF)\]\s*(\S+)\s*$")
TE_RE = re.compile(r"^TE\s*:\s*(.*)$")
NOTE_RE = re.compile(r"^NOTE\s*:\s*(.*)$")
JUNK_CHARS = set("ç^vÁÉÍÓÚáéíóú")
MARKER_RE = re.compile(r"\s*[\^*]+\s*$")


def extract_json(text: str) -> dict | None:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:].lstrip()
    matches = list(re.finditer(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", t, re.DOTALL))
    for m in reversed(matches):
        try:
            return json.loads(m.group(0))
        except Exception:
            continue
    return None


def bare_stub(s: str) -> str:
    return MARKER_RE.sub("", s).strip().lower()


def collapse(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def parse_review() -> dict:
    """Return {rid: {te, note}} from current review.txt — the authoritative state."""
    out = {}
    text = REVIEW.read_text(encoding="utf-8")
    for chunk in text.split(SEP):
        rid = te = note = None
        for ln in chunk.splitlines():
            s = ln.rstrip()
            m = HEADER_RE.match(s)
            if m:
                rid = m.group(2)
                continue
            m = TE_RE.match(s)
            if m and rid:
                te = m.group(1).strip()
                continue
            m = NOTE_RE.match(s)
            if m and rid:
                note = m.group(1).strip()
        if rid and te is not None:
            out[rid] = {"te": te, "note": note or ""}
    return out


def main():
    batch_id = BATCH_ID_PATH.read_text().strip()
    id_map = json.loads(MAP_PATH.read_text())

    client = Anthropic()
    while True:
        b = client.messages.batches.retrieve(batch_id)
        print(f"status={b.processing_status}  counts={b.request_counts}", file=sys.stderr)
        if b.processing_status == "ended":
            break
        time.sleep(20)

    prior = parse_review()  # current review.txt — includes all user edits so far

    refinements = []
    errors = []
    new_te: dict[str, str] = {}
    new_note: dict[str, str] = {}

    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id
        row = id_map.get(cid, {})
        rid = row.get("record_id")
        r = result.result
        if r.type != "succeeded":
            errors.append({"custom_id": cid, "row": row, "result_type": r.type})
            continue
        text = "".join(b.text for b in r.message.content if b.type == "text")
        parsed = extract_json(text)
        if not parsed or "te" not in parsed:
            errors.append({"custom_id": cid, "row": row, "raw": text})
            continue
        nt = parsed["te"].strip()
        ot = row["current_te"].strip()
        changed = nt != ot
        refinements.append({
            "record_id": rid,
            "old_te": ot,
            "new_te": nt,
            "changed": changed,
            "note": parsed.get("note", ""),
        })
        if changed:
            new_te[rid] = nt
            if parsed.get("note"):
                new_note[rid] = parsed["note"]

    REFINEMENTS.write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in refinements) + "\n",
        encoding="utf-8",
    )

    changed_count = sum(1 for x in refinements if x["changed"])
    print(f"\nrefinements returned: {len(refinements)}", file=sys.stderr)
    print(f"  revised: {changed_count}", file=sys.stderr)
    print(f"  unchanged: {len(refinements) - changed_count}", file=sys.stderr)
    print(f"  errors: {len(errors)}", file=sys.stderr)

    # Rebuild review.txt preserving every TE in `prior` except where this pass revised.
    proposals = {json.loads(l)["record_id"]: json.loads(l)
                 for l in PROPOSALS.open(encoding="utf-8") if l.strip()}
    partials = {json.loads(l)["record_id"]: json.loads(l)
                for l in PARTIALS.open(encoding="utf-8") if l.strip()}

    def is_flagged(rid: str, te: str, note: str, stub: str) -> bool:
        if note:
            return True
        if any(c in te for c in JUNK_CHARS):
            return True
        s = bare_stub(stub)
        if s and s not in te.lower():
            return True
        if rid in new_te:
            return True
        return False

    enriched = []
    for rid, pr in prior.items():
        p = proposals.get(rid, {})
        te = new_te.get(rid, pr["te"])
        note = new_note.get(rid) if rid in new_te else pr["note"]
        enriched.append({
            "record_id": rid,
            "eo": p.get("eo", ""),
            "te_stub": p.get("te_stub", ""),
            "te": te,
            "note": note or "",
            "traduccion": partials.get(rid, {}).get("traduccion", ""),
            "flag": is_flagged(rid, te, note or "", p.get("te_stub", "")),
            "refined": rid in new_te,
        })
    enriched.sort(key=lambda r: (0 if r["flag"] else 1, r["record_id"]))

    lines = [
        "# Review file — edit ONLY the TE lines. Keep the \"TE    : \" prefix and separators intact.",
        "# [REF] = revised by this refinement pass.  [FLAG] = model uncertainty / residual junk.",
        "# Save when done, then run:  python3 scripts/trilingue/phase5b_commit.py --commit",
        "",
    ]
    for r in enriched:
        if r["refined"]:
            tag = "[REF]  "
        elif r["flag"]:
            tag = "[FLAG] "
        else:
            tag = "[OK]   "
        lines.append(SEP)
        lines.append(f"{tag}{r['record_id']}")
        lines.append(f"EO    : {collapse(r['eo'])}")
        lines.append(f"STUB  : {collapse(r['te_stub'])}")
        lines.append(f"TE    : {collapse(r['te'])}")
        if r["note"]:
            lines.append(f"NOTE  : {collapse(r['note'])}")
        lines.append(f"ES    : {collapse(r['traduccion'])}")
        lines.append("")
    lines.append(SEP)

    REVIEW.write_text("\n".join(lines) + "\n", encoding="utf-8")
    stats = [
        f"refinement results: {len(refinements)} rows",
        f"  revised: {changed_count}",
        f"  unchanged: {len(refinements) - changed_count}",
        f"  errors: {len(errors)}",
        "",
        f"review.txt rewritten: {len(enriched)} records",
    ]
    STATS.write_text("\n".join(stats) + "\n", encoding="utf-8")
    print("\n".join(stats))


if __name__ == "__main__":
    main()
