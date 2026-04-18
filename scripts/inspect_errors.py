"""Pull batch results, categorize errors, and save successful results to disk."""
import json, os, sys
from collections import Counter
from pathlib import Path
from anthropic import Anthropic

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "scripts" / "_batch_state"
MAP_PATH = STATE / "latin_dedup_map.json"
BATCH_ID_PATH = STATE / "batch_id.txt"
RESULTS_PATH = STATE / "results_by_latin.json"
ERRORED_PATH = STATE / "errored_custom_ids.json"

def main():
    client = Anthropic()
    batch_id = BATCH_ID_PATH.read_text().strip()
    dedup = json.loads(MAP_PATH.read_text())
    cid_to_info = dedup

    by_latin = {}
    errored = []
    parse_fail = []
    err_types = Counter()
    for entry in client.messages.batches.results(batch_id):
        cid = entry.custom_id
        info = cid_to_info.get(cid)
        if info is None:
            continue
        latin = info["latin"]
        if entry.result.type != "succeeded":
            t = entry.result.type
            err_types[t] += 1
            err_detail = None
            if t == "errored":
                err_detail = getattr(entry.result.error, "error", None) or entry.result.error
                err_types[f"errored:{getattr(err_detail, 'type', 'unknown')}"] += 1
            errored.append({"custom_id": cid, "latin": latin, "spanish_ctx": info["spanish_ctx"], "type": t})
            continue
        msg = entry.result.message
        text = "".join(b.text for b in msg.content if b.type == "text").strip()
        try:
            parsed = json.loads(text)
            by_latin[latin] = {
                "latin_modern": parsed["latin_modern"].strip(),
                "spanish_translation": parsed["spanish_translation"].strip(),
            }
        except Exception as e:
            parse_fail.append({"custom_id": cid, "latin": latin, "raw": text, "err": str(e)})

    print(f"succeeded+parsed: {len(by_latin)}", file=sys.stderr)
    print(f"parse_fail: {len(parse_fail)}", file=sys.stderr)
    print(f"errored: {len(errored)}", file=sys.stderr)
    print(f"error type breakdown: {dict(err_types)}", file=sys.stderr)

    RESULTS_PATH.write_text(json.dumps(by_latin, ensure_ascii=False))
    ERRORED_PATH.write_text(json.dumps({"errored": errored, "parse_fail": parse_fail}, ensure_ascii=False))
    print(f"\nWrote {RESULTS_PATH.name} ({len(by_latin)} entries)", file=sys.stderr)
    print(f"Wrote {ERRORED_PATH.name} ({len(errored) + len(parse_fail)} entries)", file=sys.stderr)

    # show a few sample errored Latin strings
    if errored:
        print("\nSample errored Latin strings:", file=sys.stderr)
        for e in errored[:8]:
            print(f"  {e['latin']!r}  (ctx: {e['spanish_ctx']!r})", file=sys.stderr)
    if parse_fail:
        print("\nSample parse_fail:", file=sys.stderr)
        for p in parse_fail[:3]:
            print(f"  latin={p['latin']!r}", file=sys.stderr)
            print(f"  raw: {p['raw'][:200]!r}", file=sys.stderr)

if __name__ == "__main__":
    main()
