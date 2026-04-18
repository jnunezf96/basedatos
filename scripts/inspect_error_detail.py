"""Show the actual error messages for the errored requests."""
import json, sys
from collections import Counter
from pathlib import Path
from anthropic import Anthropic

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "scripts" / "_batch_state"
BATCH_ID_PATH = STATE / "batch_id.txt"

client = Anthropic()
batch_id = BATCH_ID_PATH.read_text().strip()

seen_msgs = Counter()
samples_by_msg = {}
for entry in client.messages.batches.results(batch_id):
    if entry.result.type != "errored":
        continue
    err = entry.result.error.error  # nested .error.error per SDK shape
    key = f"{err.type}: {err.message[:160]}"
    seen_msgs[key] += 1
    samples_by_msg.setdefault(key, []).append(entry.custom_id)

print("Error message distribution:")
for msg, count in seen_msgs.most_common(20):
    print(f"\n[{count}] {msg}")
    print(f"  sample custom_ids: {samples_by_msg[msg][:3]}")
