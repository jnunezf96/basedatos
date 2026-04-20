"""Phase 4b retry — rerun the 90 rows that hit the max_tokens cliff.

Same system prompt, but max_tokens=2048 and a hard instruction to emit JSON
first. Uses the streaming (non-batch) API — 90 rows is small enough that
waiting 30 seconds beats round-tripping through Batch again.
"""
import json
import os
import sys
import time
from pathlib import Path

from anthropic import Anthropic

from phase4b_submit import build_system, pick_few_shots, build_user

HERE = Path(__file__).resolve().parent
ERRORS = HERE / "phase4b_errors.jsonl"
PROPOSALS = HERE / "phase4b_proposals.jsonl"

HARD_INSTRUCTION = (
    "\n\nIMPORTANTÍSIMO: La PRIMERA carácter de tu respuesta debe ser `{`. "
    "No escribas razonamiento, ni análisis, ni texto previo al JSON. "
    "Devuelve el JSON directamente y nada más."
)


def extract_json(text: str) -> dict | None:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:].lstrip()
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(t[start : end + 1])
    except Exception:
        return None


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY missing.")

    errs = [json.loads(l) for l in ERRORS.open(encoding="utf-8") if l.strip()]
    rows = [e["row"] for e in errs if e.get("row")]
    print(f"retrying {len(rows)} rows", file=sys.stderr)

    few_shots = pick_few_shots()
    system = build_system(few_shots)
    # Append the hard instruction onto the cached system text.
    system[0]["text"] = system[0]["text"] + HARD_INSTRUCTION

    client = Anthropic()
    recovered = []
    still_bad = []
    for i, row in enumerate(rows):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=system,
                messages=[{"role": "user", "content": build_user(row)}],
            )
            text = "".join(b.text for b in resp.content if b.type == "text")
            parsed = extract_json(text)
            if parsed and "te" in parsed:
                recovered.append({
                    "record_id": row.get("record_id"),
                    "eo": row.get("eo"),
                    "te_stub": row.get("te_stub"),
                    "te": parsed["te"],
                    "note": parsed.get("note", ""),
                })
            else:
                still_bad.append({"record_id": row.get("record_id"), "row": row, "raw": text})
        except Exception as e:
            still_bad.append({"record_id": row.get("record_id"), "row": row, "error": str(e)})
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(rows)}  recovered={len(recovered)}  bad={len(still_bad)}", file=sys.stderr)

    # Append recovered to the main proposals file.
    with PROPOSALS.open("a", encoding="utf-8") as f:
        for r in recovered:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Rewrite errors file with only the still-bad ones.
    with ERRORS.open("w", encoding="utf-8") as f:
        for e in still_bad:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"recovered: {len(recovered)}  still-bad: {len(still_bad)}", file=sys.stderr)


if __name__ == "__main__":
    main()
