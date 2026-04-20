"""Phase 6 — poll + fetch the refinement batch and update review.txt.

Parses each result's {te, changed, note}. For every row where changed=true
(or where the returned te differs from the current), rewrites the TE line
in review.txt. Preserves the block structure and re-runs the flagging
pass so user-unedited rows with revisions become visible.

Outputs:
  phase6_refinements.jsonl    — {record_id, old_te, new_te, changed, note}
  phase6_stats.txt
  review.txt                  — rewritten with revised TEs (flagged first)
"""
import json
import re
import sys
import time
from pathlib import Path

from anthropic import Anthropic

HERE = Path(__file__).resolve().parent
STATE = HERE / "_batch"
BATCH_ID_PATH = STATE / "phase6_batch_id.txt"
MAP_PATH = STATE / "phase6_map.json"
PROPOSALS = HERE / "phase4b_proposals.jsonl"
PARTIALS = HERE / "partials.jsonl"
REVIEW = HERE / "review.txt"
REFINEMENTS = HERE / "phase6_refinements.jsonl"
STATS = HERE / "phase6_stats.txt"

SEP = "═" * 80
HEADER_RE = re.compile(r"^\[(FLAG|OK)\]\s*(\S+)\s*$")
TE_RE = re.compile(r"^TE\s*:\s*(.*)$")
JUNK_CHARS = set("ç^vÁÉÍÓÚáéíóú")
MARKER_RE = re.compile(r"\s*[\^*]+\s*$")


def extract_json(text: str) -> dict | None:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:].lstrip()
    # Grab the LAST complete {...} block (model sometimes writes more than one).
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

    refinements = []
    errors = []
    new_te_by_rid: dict[str, str] = {}
    new_note_by_rid: dict[str, str] = {}

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
        new_te = parsed["te"].strip()
        old_te = row["current_te"].strip()
        changed = new_te != old_te
        refinements.append({
            "record_id": rid,
            "old_te": old_te,
            "new_te": new_te,
            "changed": changed,
            "note": parsed.get("note", ""),
        })
        if changed:
            new_te_by_rid[rid] = new_te
            note = parsed.get("note", "")
            if note:
                new_note_by_rid[rid] = note

    REFINEMENTS.write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in refinements) + "\n",
        encoding="utf-8",
    )

    changed_count = sum(1 for x in refinements if x["changed"])
    print(f"\nrefinements returned: {len(refinements)}", file=sys.stderr)
    print(f"  revised: {changed_count}", file=sys.stderr)
    print(f"  unchanged: {len(refinements) - changed_count}", file=sys.stderr)
    print(f"  errors: {len(errors)}", file=sys.stderr)

    # Rebuild review.txt with the updated TE values + flagging pass.
    proposals = {json.loads(l)["record_id"]: json.loads(l)
                 for l in PROPOSALS.open(encoding="utf-8") if l.strip()}
    partials = {json.loads(l)["record_id"]: json.loads(l)
                for l in PARTIALS.open(encoding="utf-8") if l.strip()}

    # Also pull in the user's prior edits (rows present in current review.txt
    # whose TE differs from phase4 proposal): those must NOT be overwritten.
    prior_te: dict[str, str] = {}
    prior_note: dict[str, str] = {}
    if REVIEW.exists():
        text = REVIEW.read_text(encoding="utf-8")
        for chunk in text.split(SEP):
            lines = [ln.rstrip() for ln in chunk.splitlines()]
            rid = None
            te = None
            note = None
            for ln in lines:
                m = HEADER_RE.match(ln)
                if m:
                    rid = m.group(2)
                    continue
                m = TE_RE.match(ln)
                if m and rid:
                    te = m.group(1).strip()
                if ln.startswith("NOTE  :") and rid:
                    note = ln[len("NOTE  :"):].strip()
            if rid and te is not None:
                prior_te[rid] = te
                if note:
                    prior_note[rid] = note

    def final_te(rid: str) -> str:
        # Priority: refinement > user edit > original proposal.
        if rid in new_te_by_rid:
            return new_te_by_rid[rid]
        if rid in prior_te:
            return prior_te[rid]
        return proposals[rid]["te"].strip()

    def final_note(rid: str, r: dict) -> str:
        # Priority: refinement note > original proposal note > prior note.
        if rid in new_note_by_rid:
            return new_note_by_rid[rid]
        base = r.get("note") or ""
        if base:
            return base
        return prior_note.get(rid, "")

    def is_flagged(rid: str, te: str, note: str, stub: str) -> bool:
        if note:
            return True
        if any(c in te for c in JUNK_CHARS):
            return True
        s = bare_stub(stub)
        if s and s not in te.lower():
            return True
        if rid in new_te_by_rid:
            return True  # refinement revised it — user should glance.
        return False

    # Only include rows that are still in the current review (drop the 1 the user removed).
    rids_in_review = set(prior_te) if prior_te else set(proposals)
    enriched = []
    for rid, r in proposals.items():
        if rid not in rids_in_review:
            continue
        te = final_te(rid)
        note = final_note(rid, r)
        enriched.append({
            "record_id": rid,
            "eo": r["eo"],
            "te_stub": r["te_stub"],
            "te": te,
            "note": note,
            "traduccion": partials.get(rid, {}).get("traduccion", ""),
            "flag": is_flagged(rid, te, note, r["te_stub"]),
            "refined": rid in new_te_by_rid,
        })
    enriched.sort(key=lambda r: (0 if r["flag"] else 1, r["record_id"]))

    lines = [
        "# Review file — edit ONLY the TE lines. Keep the \"TE    : \" prefix and separators intact.",
        "# Flagged rows (model uncertainty, residual junk, stub rewrites, refinement revisions) are first.",
        "# [REF] tag marks rows the phase-6 refinement pass revised.",
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
        note = collapse(r.get("note") or "")
        if note:
            lines.append(f"NOTE  : {note}")
        lines.append(f"ES    : {collapse(r['traduccion'])}")
        lines.append("")
    lines.append(SEP)

    REVIEW.write_text("\n".join(lines) + "\n", encoding="utf-8")
    flagged = sum(1 for r in enriched if r["flag"] or r["refined"])
    stats = [
        f"refinement results: {len(refinements)} rows",
        f"  revised: {changed_count}",
        f"  unchanged: {len(refinements) - changed_count}",
        f"  errors: {len(errors)}",
        f"",
        f"review.txt rewritten: {len(enriched)} records ({flagged} flagged/refined first)",
    ]
    STATS.write_text("\n".join(stats) + "\n", encoding="utf-8")
    print("\n".join(stats))


if __name__ == "__main__":
    main()
