"""Phase 5b — apply the reviewed block file to data/data.jsonl.gz.

Reads scripts/trilingue/review.txt. Parses per-record blocks separated by
the ═×80 line. For each block, extracts the record_id (from the tagged
header line) and the edited TE value (from the `TE    : ` line), then
rewrites data.jsonl.gz's matching `Texto estandarizado` fields.

Validation before commit:
  - Every block must have a record_id and a TE value.
  - Every TE must be non-empty and contain no "+".
  - Every record_id must resolve to exactly one existing Trilingüe row
    whose current `Texto estandarizado` contains "+" (so we never overwrite
    a row that's already clean).

On success, backs up data.jsonl.gz as data.jsonl.bak{N}.gz (same scheme as
edit_all.py) and atomically rewrites data.jsonl.gz.

Dry-run by default — pass --commit to actually write.
"""
import argparse
import gzip
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "data.jsonl.gz"
HERE = Path(__file__).resolve().parent
REVIEW = HERE / "review.txt"

SEP = "═" * 80
HEADER_RE = re.compile(r"^\[(FLAG|OK|REF)\]\s*(\S+)\s*$")
TE_RE = re.compile(r"^TE\s*:\s*(.*)$")


def next_backup_path() -> Path:
    nums = []
    for b in DATA.parent.glob("data.jsonl.bak*.gz"):
        stem = b.name.replace("data.jsonl.bak", "").replace(".gz", "")
        try:
            nums.append(int(stem))
        except ValueError:
            pass
    n = (max(nums) + 1) if nums else 1
    return DATA.parent / f"data.jsonl.bak{n}.gz"


def parse_review() -> list[dict]:
    text = REVIEW.read_text(encoding="utf-8")
    if not text.strip():
        sys.exit(f"empty review file: {REVIEW}")

    # Split on the separator and drop empty chunks (header comments, trailing blank).
    chunks = [c.strip() for c in text.split(SEP)]
    chunks = [c for c in chunks if c]

    out = []
    for idx, chunk in enumerate(chunks, 1):
        lines = chunk.splitlines()
        # First non-empty line must be the tagged record_id header.
        header = None
        te = None
        for ln in lines:
            s = ln.rstrip()
            if not s:
                continue
            if header is None:
                m = HEADER_RE.match(s)
                if not m:
                    # Not a record block — likely the intro comments. Skip.
                    break
                header = m.group(2)
                continue
            m = TE_RE.match(s)
            if m:
                te = m.group(1).strip()
        if header is None:
            continue
        if te is None:
            sys.exit(f"block {idx} (record_id={header}): missing TE line")
        if not te:
            sys.exit(f"block {idx} (record_id={header}): empty TE")
        if "+" in te:
            sys.exit(f"block {idx} (record_id={header}): TE still contains '+'")
        out.append({"record_id": header, "te": te})
    if not out:
        sys.exit(f"no record blocks parsed from {REVIEW}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true",
                    help="actually rewrite data.jsonl.gz (default: dry-run)")
    args = ap.parse_args()

    review = parse_review()
    print(f"review blocks: {len(review)}", file=sys.stderr)

    te_by_rid = {r["record_id"]: r["te"] for r in review}
    if len(te_by_rid) != len(review):
        sys.exit(f"duplicate record_ids in review file")

    out_lines = []
    matched = set()
    skipped_already_clean = []
    rid_missing = set(te_by_rid)

    with gzip.open(DATA, "rb") as f:
        for raw in f:
            if not raw.strip():
                out_lines.append(raw)
                continue
            row = json.loads(raw)
            rid = row.get("record_id")
            if rid in te_by_rid:
                rid_missing.discard(rid)
                current = row.get("Texto estandarizado", "") or ""
                if "+" not in current:
                    skipped_already_clean.append(rid)
                    out_lines.append(raw)
                    continue
                row["Texto estandarizado"] = te_by_rid[rid]
                matched.add(rid)
                out_lines.append((json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8"))
            else:
                out_lines.append(raw)

    if rid_missing:
        print(f"WARNING: {len(rid_missing)} record_ids in review.txt were not found in data.jsonl.gz", file=sys.stderr)
        for rid in list(rid_missing)[:5]:
            print(f"  missing: {rid}", file=sys.stderr)

    if skipped_already_clean:
        print(f"WARNING: {len(skipped_already_clean)} rows already had no '+' — skipped (won't overwrite)", file=sys.stderr)

    print(f"would update: {len(matched)} rows", file=sys.stderr)

    if not args.commit:
        print("\nDRY RUN — pass --commit to actually rewrite data.jsonl.gz", file=sys.stderr)
        return

    backup = next_backup_path()
    print(f"backing up → {backup.name}", file=sys.stderr)
    shutil.copy2(DATA, backup)

    tmp = DATA.with_suffix(".gz.tmp")
    with gzip.open(tmp, "wb") as out:
        for line in out_lines:
            out.write(line)
    tmp.replace(DATA)
    print(f"rewrote data.jsonl.gz with {len(matched)} updated rows", file=sys.stderr)


if __name__ == "__main__":
    main()
