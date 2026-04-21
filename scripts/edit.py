"""Edit a single entry in data/data.jsonl.gz in your editor.

Usage:
    python3 scripts/edit.py <eid>                  # edit by eid
    python3 scripts/edit.py --find "palabra"       # list eids whose fields contain "palabra"
    python3 scripts/edit.py --record-id <rid>      # edit by record_id

On save the gzip is rewritten and the previous file is kept as data.jsonl.bakN.gz.
"""
import argparse, gzip, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "data.jsonl.gz"


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


def pick_editor() -> list[str]:
    """Return an argv-prefix like ['code', '--wait'] for the user's editor."""
    env_editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if env_editor:
        return env_editor.split()
    if shutil.which("code"):
        return ["code", "--wait"]
    if shutil.which("nano"):
        return ["nano"]
    return ["vi"]


def find_entry(key: str, value: str):
    """Scan the file and return (byte_offset_of_line, line_index, record)."""
    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if str(r.get(key, "")) == value:
                return i, r
    return None, None


def do_find(needle: str, limit: int = 30):
    needle_l = needle.lower()
    hits = 0
    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            blob = " ".join(str(v) for v in r.values()).lower()
            if needle_l in blob:
                hits += 1
                print(
                    f"{r.get('eid'):>12}  "
                    f"{r.get('Fuente',''):<22}  "
                    f"{r.get('Escritura original','')[:40]:<40}  "
                    f"{r.get('Traducción','')[:60]}"
                )
                if hits >= limit:
                    print(f"... truncated at {limit} matches. Refine --find.")
                    return
    if hits == 0:
        print("no matches")


def do_edit(lookup_key: str, lookup_value: str):
    print(f"searching for {lookup_key} == {lookup_value!r} ...", file=sys.stderr)
    line_idx, record = find_entry(lookup_key, lookup_value)
    if record is None:
        sys.exit(f"no entry found with {lookup_key} == {lookup_value!r}")

    editor_cmd = pick_editor()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", prefix=f"edit_{lookup_value}_",
        delete=False, encoding="utf-8",
    ) as tmp:
        json.dump(record, tmp, ensure_ascii=False, indent=2)
        tmp_path = Path(tmp.name)

    print(f"opening {tmp_path} in {' '.join(editor_cmd)} ...", file=sys.stderr)
    try:
        subprocess.run(editor_cmd + [str(tmp_path)], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"editor exited with {e.returncode}; no changes written")

    try:
        new_record = json.loads(tmp_path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.exit(f"edited file is not valid JSON ({e}); data.jsonl.gz untouched")
    finally:
        tmp_path.unlink(missing_ok=True)

    if new_record == record:
        print("no changes — data.jsonl.gz untouched", file=sys.stderr)
        return

    backup = next_backup_path()
    print(f"backing up current data.jsonl.gz → {backup.name}", file=sys.stderr)
    shutil.copy2(DATA, backup)

    # Re-stream, replacing the target line by matching the same lookup key
    tmp_out = DATA.with_suffix(".gz.tmp")
    replaced = 0
    with gzip.open(DATA, "rt", encoding="utf-8") as fin, gzip.open(tmp_out, "wt", encoding="utf-8") as fout:
        for line in fin:
            try:
                r = json.loads(line)
            except Exception:
                fout.write(line)
                continue
            if str(r.get(lookup_key, "")) == lookup_value:
                fout.write(json.dumps(new_record, ensure_ascii=False) + "\n")
                replaced += 1
            else:
                fout.write(line)
    tmp_out.replace(DATA)
    print(f"rewrote data.jsonl.gz ({replaced} record{'s' if replaced != 1 else ''} replaced)", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="Edit a single record in data.jsonl.gz")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("eid", nargs="?", help="entry eid, e.g. 1353814.0")
    g.add_argument("--record-id", dest="record_id", help="record_id, e.g. 1765-cortes-y-zedeno:000001")
    g.add_argument("--find", dest="find", help="search all fields for a substring (read-only)")
    args = ap.parse_args()

    if args.find:
        do_find(args.find)
    elif args.record_id:
        do_edit("record_id", args.record_id)
    else:
        do_edit("eid", args.eid)


if __name__ == "__main__":
    main()
