"""Edit the whole data.jsonl.gz in VS Code, then save back.

Run directly or via "Edit Data.app" in the project root. Opens the
decompressed JSONL in VS Code (--wait). On save + close, validates each
line, backs up the current gz, and rewrites it.
"""
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
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


def find_code_cli() -> str | None:
    candidates = [
        shutil.which("code"),
        "/usr/local/bin/code",
        "/opt/homebrew/bin/code",
        "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
    ]
    for p in candidates:
        if p and Path(p).exists():
            return p
    return None


def main():
    if not DATA.exists():
        sys.exit(f"data file not found: {DATA}")

    code_bin = find_code_cli()
    if not code_bin:
        sys.exit(
            "VS Code CLI ('code') not found. In VS Code, open the Command "
            "Palette and run \"Shell Command: Install 'code' command in PATH\"."
        )

    with tempfile.NamedTemporaryFile(
        mode="wb", suffix=".jsonl", prefix="data_all_", delete=False
    ) as tmp:
        tmp_path = Path(tmp.name)
        with gzip.open(DATA, "rb") as fin:
            shutil.copyfileobj(fin, tmp)

    print(f"opening {tmp_path} in VS Code ...", file=sys.stderr)
    try:
        subprocess.run([code_bin, "--wait", str(tmp_path)], check=True)
    except subprocess.CalledProcessError as e:
        tmp_path.unlink(missing_ok=True)
        sys.exit(f"editor exited with {e.returncode}; data.jsonl.gz untouched")

    errors = []
    with tmp_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except Exception as e:
                errors.append((i, str(e)))
                if len(errors) >= 5:
                    break
    if errors:
        detail = "\n".join(f"  line {i}: {e}" for i, e in errors)
        tmp_path.unlink(missing_ok=True)
        sys.exit(f"edited file has invalid JSON; data.jsonl.gz untouched:\n{detail}")

    backup = next_backup_path()
    print(f"backing up current data.jsonl.gz → {backup.name}", file=sys.stderr)
    shutil.copy2(DATA, backup)

    tmp_out = DATA.with_suffix(".gz.tmp")
    with tmp_path.open("rb") as fin, gzip.open(tmp_out, "wb") as fout:
        shutil.copyfileobj(fin, fout)
    tmp_out.replace(DATA)
    tmp_path.unlink(missing_ok=True)
    print("rewrote data.jsonl.gz", file=sys.stderr)


if __name__ == "__main__":
    main()
