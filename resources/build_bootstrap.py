#!/usr/bin/env python3
"""Build or check the first 100 complete corpus records used for static startup."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DataStats:
    total_rows: int
    bootstrap_rows: list[dict]


def read_data_stats(data_path: Path, bootstrap_limit: int = 100) -> DataStats:
    rows: list[dict] = []
    total = 0
    with gzip.open(data_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"Corpus record {total + 1} is not an object")
            total += 1
            if len(rows) < bootstrap_limit:
                rows.append(row)
    return DataStats(total_rows=total, bootstrap_rows=rows)


def bootstrap_payload(stats: DataStats) -> dict:
    return {"totalRows": stats.total_rows, "rows": stats.bootstrap_rows}


def read_bootstrap(path: Path) -> dict:
    match = re.fullmatch(r"window\.NAHUATL_BOOTSTRAP = (.*);\n?", path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{path} does not match expected bootstrap wrapper")
    return json.loads(match.group(1))


def parse_bootstrap(path: Path) -> tuple[int, int]:
    payload = read_bootstrap(path)
    return int(payload["totalRows"]), len(payload["rows"])


def validate_bootstrap(path: Path, stats: DataStats) -> None:
    if read_bootstrap(path) != bootstrap_payload(stats):
        raise ValueError(f"{path} differs from the first {len(stats.bootstrap_rows)} complete corpus records or total count")


def rebuild_bootstrap(path: Path, stats: DataStats) -> None:
    content = "window.NAHUATL_BOOTSTRAP = " + json.dumps(
        bootstrap_payload(stats), ensure_ascii=False, separators=(",", ":")
    ) + ";\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/data.jsonl.gz")
    parser.add_argument("--bootstrap", type=Path, default=ROOT / "data/bootstrap.js")
    parser.add_argument("--check", action="store_true", help="Check exact content without writing")
    args = parser.parse_args()
    try:
        stats = read_data_stats(args.data)
        if not args.check:
            rebuild_bootstrap(args.bootstrap, stats)
        validate_bootstrap(args.bootstrap, stats)
    except (OSError, ValueError, EOFError) as error:
        parser.exit(1, f"bootstrap failed: {error}\n")
    print(f"bootstrap {'checked' if args.check else 'built'}: {len(stats.bootstrap_rows)} rows, total {stats.total_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
