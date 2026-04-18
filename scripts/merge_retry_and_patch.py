"""Fetch retry-batch results, merge into results_by_latin.json, re-run patch."""
import json, os, sys
from pathlib import Path
from anthropic import Anthropic

from collect_and_patch import patch  # reuse the gzip rewrite

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "scripts" / "_batch_state"
MAP_PATH = STATE / "latin_dedup_map.json"
RESULTS_PATH = STATE / "results_by_latin.json"
RETRY_BATCH_ID_PATH = STATE / "retry_batch_id.txt"


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY missing")
    client = Anthropic()
    dedup = json.loads(MAP_PATH.read_text())
    cid_to_latin = {cid: info["latin"] for cid, info in dedup.items()}
    by_latin = json.loads(RESULTS_PATH.read_text())
    before = len(by_latin)

    retry_bid = RETRY_BATCH_ID_PATH.read_text().strip()
    n_ok = n_err = n_parse_fail = 0
    parse_fail_samples = []
    for entry in client.messages.batches.results(retry_bid):
        cid = entry.custom_id
        latin = cid_to_latin.get(cid)
        if latin is None:
            continue
        if entry.result.type != "succeeded":
            n_err += 1
            continue
        msg = entry.result.message
        text = "".join(b.text for b in msg.content if b.type == "text").strip()
        try:
            parsed = json.loads(text)
            by_latin[latin] = {
                "latin_modern": parsed["latin_modern"].strip(),
                "spanish_translation": parsed["spanish_translation"].strip(),
            }
            n_ok += 1
        except Exception as e:
            n_parse_fail += 1
            parse_fail_samples.append((latin, text[:200], str(e)))

    print(f"retry parsed ok={n_ok} err={n_err} parse_fail={n_parse_fail}", file=sys.stderr)
    print(f"results grew: {before} -> {len(by_latin)}", file=sys.stderr)
    if parse_fail_samples:
        print("\nparse_fail samples:", file=sys.stderr)
        for lat, raw, err in parse_fail_samples[:5]:
            print(f"  latin={lat!r}\n  raw={raw!r}\n  err={err}", file=sys.stderr)

    RESULTS_PATH.write_text(json.dumps(by_latin, ensure_ascii=False))
    patched, skipped = patch(by_latin)
    print(f"\nfinal patched={patched} still_skipped={skipped}", file=sys.stderr)


if __name__ == "__main__":
    main()
