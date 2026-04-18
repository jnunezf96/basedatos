"""Resubmit only the errored + parse_fail custom_ids from the first batch."""
import json, os, sys
from pathlib import Path
from anthropic import Anthropic

from submit_batch import SYSTEM, build_request  # reuse the same prompt

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "scripts" / "_batch_state"
ERRORED_PATH = STATE / "errored_custom_ids.json"
MAP_PATH = STATE / "latin_dedup_map.json"
RETRY_BATCH_ID_PATH = STATE / "retry_batch_id.txt"


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY missing")
    errored_doc = json.loads(ERRORED_PATH.read_text())
    dedup = json.loads(MAP_PATH.read_text())

    retry_cids = {e["custom_id"] for e in errored_doc["errored"]} | {
        p["custom_id"] for p in errored_doc["parse_fail"]
    }
    print(f"Resubmitting {len(retry_cids)} custom_ids", file=sys.stderr)

    requests = []
    for cid in retry_cids:
        info = dedup[cid]
        requests.append(build_request(cid, info["latin"], info["spanish_ctx"]))

    client = Anthropic()
    batch = client.messages.batches.create(requests=requests)
    RETRY_BATCH_ID_PATH.write_text(batch.id)
    print(f"retry batch_id: {batch.id}", file=sys.stderr)
    print(f"status: {batch.processing_status}", file=sys.stderr)
    print(f"counts: {batch.request_counts}", file=sys.stderr)


if __name__ == "__main__":
    main()
