"""Phase 7 — second refinement pass.

Feeds 182 user corrections (phase 5 + phase 7) as few-shots, refines the
643 rows still untouched across both review rounds.
"""
import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic

from phase4b_submit import RULE_PRIMER
from phase6_refine_submit import TASK, build_user

HERE = Path(__file__).resolve().parent
INPUT = HERE / "phase7_input.jsonl"
CORRECTIONS = HERE / "phase7_corrections.jsonl"
STATE = HERE / "_batch"
STATE.mkdir(exist_ok=True)
BATCH_ID_PATH = STATE / "phase7_batch_id.txt"
MAP_PATH = STATE / "phase7_map.json"


def build_system(corrections: list[dict]) -> list[dict]:
    lines = ["EJEMPLOS DE CORRECCIÓN (ANTES → DESPUÉS):", ""]
    for c in corrections:
        lines.append(f"  EO:      {c['eo']}")
        lines.append(f"  STUB:    {c['te_stub']}")
        lines.append(f"  ANTES:   {c['was']}")
        lines.append(f"  DESPUÉS: {c['now']}")
        lines.append("")
    system_text = f"{RULE_PRIMER}\n\n{TASK}\n\n" + "\n".join(lines)
    return [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY missing.")

    rows = [json.loads(l) for l in INPUT.open(encoding="utf-8") if l.strip()]
    corrections = [json.loads(l) for l in CORRECTIONS.open(encoding="utf-8") if l.strip()]
    system = build_system(corrections)

    id_map = {}
    requests = []
    for row in rows:
        cid = row["record_id"].replace(":", "_").replace(".", "_")
        id_map[cid] = row
        requests.append({
            "custom_id": cid,
            "params": {
                "model": "claude-sonnet-4-6",
                "max_tokens": 2048,
                "system": system,
                "messages": [{"role": "user", "content": build_user(row)}],
            },
        })

    MAP_PATH.write_text(json.dumps(id_map, ensure_ascii=False))
    print(f"rows to refine: {len(rows)}", file=sys.stderr)
    print(f"few-shot corrections: {len(corrections)}", file=sys.stderr)
    print(f"system prompt chars: {len(system[0]['text'])}", file=sys.stderr)

    client = Anthropic()
    batch = client.messages.batches.create(requests=requests)
    BATCH_ID_PATH.write_text(batch.id)
    print(f"batch_id: {batch.id}", file=sys.stderr)
    print(f"processing_status: {batch.processing_status}", file=sys.stderr)
    print(f"request_counts: {batch.request_counts}", file=sys.stderr)


if __name__ == "__main__":
    main()
