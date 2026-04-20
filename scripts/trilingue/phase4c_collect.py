"""Phase 4c — poll + fetch the batch and parse results.

Reads _batch/batch_id.txt and partials_map.json, waits for completion,
downloads results, parses the JSON per row and writes:
  phase4b_proposals.jsonl    — {record_id, eo, te_stub, te, note, raw}
  phase4b_errors.jsonl       — any rows the model/parser failed on
  phase4b_stats.txt          — summary
"""
import json
import sys
import time
from pathlib import Path

from anthropic import Anthropic

HERE = Path(__file__).resolve().parent
STATE = HERE / "_batch"
BATCH_ID_PATH = STATE / "batch_id.txt"
MAP_PATH = STATE / "partials_map.json"
PROPOSALS = HERE / "phase4b_proposals.jsonl"
ERRORS = HERE / "phase4b_errors.jsonl"
STATS = HERE / "phase4b_stats.txt"


def extract_json(text: str) -> dict | None:
    t = text.strip()
    # Strip ```json fences if the model added them.
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:].lstrip()
    # Grab the first { ... } block.
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(t[start : end + 1])
    except Exception:
        return None


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

    proposals = []
    errors = []
    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id
        row = id_map.get(cid, {})
        r = result.result
        if r.type != "succeeded":
            errors.append({"custom_id": cid, "row": row, "result_type": r.type,
                           "error": getattr(r, "error", None).__dict__ if getattr(r, "error", None) else None})
            continue
        text = "".join(b.text for b in r.message.content if b.type == "text")
        parsed = extract_json(text)
        if not parsed or "te" not in parsed:
            errors.append({"custom_id": cid, "row": row, "raw": text})
            continue
        proposals.append({
            "record_id": row.get("record_id"),
            "eo": row.get("eo"),
            "te_stub": row.get("te_stub"),
            "te": parsed["te"],
            "note": parsed.get("note", ""),
            "raw": text if parsed.get("note") else None,
        })

    with PROPOSALS.open("w", encoding="utf-8") as f:
        for p in proposals:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with ERRORS.open("w", encoding="utf-8") as f:
        for e in errors:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    noted = sum(1 for p in proposals if p.get("note"))
    lines = [
        f"total proposals: {len(proposals)}",
        f"  with 'note' (model flagged uncertainty): {noted}",
        f"errors (request failed or unparseable JSON): {len(errors)}",
        "",
        f"→ {PROPOSALS.name}",
        f"→ {ERRORS.name}",
    ]
    STATS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
