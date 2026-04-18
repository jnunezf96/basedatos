"""Once the batch has finished: fetch results, parse, back up, rewrite data.jsonl.gz.

Usage:
  ANTHROPIC_API_KEY=... python3 scripts/collect_and_patch.py
"""
import gzip, io, json, os, shutil, sys
from pathlib import Path
from anthropic import Anthropic

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "data.jsonl.gz"
STATE = ROOT / "scripts" / "_batch_state"
MAP_PATH = STATE / "latin_dedup_map.json"
BATCH_ID_PATH = STATE / "batch_id.txt"
RESULTS_PATH = STATE / "results_by_latin.json"


def next_backup_path() -> Path:
    """Pick data.jsonl.bakN.gz where N is one greater than the highest existing."""
    backups = list(DATA.parent.glob("data.jsonl.bak*.gz"))
    nums = []
    for b in backups:
        stem = b.name.replace("data.jsonl.bak", "").replace(".gz", "")
        try:
            nums.append(int(stem))
        except ValueError:
            continue
    n = (max(nums) + 1) if nums else 1
    return DATA.parent / f"data.jsonl.bak{n}.gz"


def fetch_results() -> dict[str, dict]:
    """Pulls the batch and returns {latin_orig: {"latin_modern":..., "spanish_translation":...}}."""
    client = Anthropic()
    batch_id = BATCH_ID_PATH.read_text().strip()
    dedup = json.loads(MAP_PATH.read_text())  # {custom_id: {"latin","spanish_ctx"}}
    cid_to_latin = {cid: info["latin"] for cid, info in dedup.items()}

    batch = client.messages.batches.retrieve(batch_id)
    print(f"batch {batch_id}: status={batch.processing_status} counts={batch.request_counts}", file=sys.stderr)
    if batch.processing_status != "ended":
        sys.exit("batch has not ended yet; run again later")

    by_latin: dict[str, dict] = {}
    n_ok = n_err = n_parse_fail = 0
    for entry in client.messages.batches.results(batch_id):
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
        except Exception:
            n_parse_fail += 1
            continue
    print(f"results: ok={n_ok} errored={n_err} parse_fail={n_parse_fail}", file=sys.stderr)
    RESULTS_PATH.write_text(json.dumps(by_latin, ensure_ascii=False))
    return by_latin


def rewrite_comentario(comentario: str, modern: str, translation: str) -> str:
    """Take original `Comentario` and rewrite the line-4 Latin into
    `<orig>  >  <modern>`, then append line 5 = Spanish translation.
    If line 4 already contains ` > ` (idempotent re-run), leave it alone."""
    parts = comentario.split("<br />")
    if len(parts) < 4:
        return comentario
    latin_line = parts[3]
    latin_orig = latin_line.strip()
    if not latin_orig:
        return comentario
    if " > " not in latin_line:
        parts[3] = f"  {latin_orig}  >  {modern}"
    # drop any existing line 5+ so re-runs stay idempotent
    parts = parts[:4]
    parts.append(f"  {translation}")
    return "<br />".join(parts)


def patch(by_latin: dict[str, dict]) -> tuple[int, int]:
    backup = next_backup_path()
    print(f"backing up current data.jsonl.gz → {backup.name}", file=sys.stderr)
    shutil.copy2(DATA, backup)

    tmp = DATA.with_suffix(".gz.tmp")
    patched = skipped = 0
    with gzip.open(DATA, "rt", encoding="utf-8") as fin, gzip.open(tmp, "wt", encoding="utf-8") as fout:
        for line in fin:
            try:
                r = json.loads(line)
            except Exception:
                fout.write(line)
                continue
            if r.get("Fuente") == "153? Trilingüe":
                c = r.get("Comentario", "")
                parts = [p.strip() for p in c.split("<br />")]
                latin = parts[3].strip() if len(parts) >= 4 else ""
                hit = by_latin.get(latin) if latin else None
                if hit:
                    r["Comentario"] = rewrite_comentario(
                        c, hit["latin_modern"], hit["spanish_translation"]
                    )
                    patched += 1
                else:
                    skipped += 1
            fout.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(DATA)
    print(f"patched={patched} skipped_trilingue={skipped}", file=sys.stderr)
    return patched, skipped


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY missing")
    if not BATCH_ID_PATH.exists():
        sys.exit("no batch_id.txt — submit first")
    if RESULTS_PATH.exists():
        print(f"reusing cached {RESULTS_PATH.name}", file=sys.stderr)
        by_latin = json.loads(RESULTS_PATH.read_text())
    else:
        by_latin = fetch_results()
    patch(by_latin)


if __name__ == "__main__":
    main()
