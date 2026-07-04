#!/usr/bin/env python3
"""Run the standard verification cycle after a cleanup stage.

Default mode is read-only: it validates the gzip, compiles key scripts, parses
the bootstrap, runs the sentence-source audit and Spanish spellcheck, scans any
target residue expressions, and prints the current cache tags.

Use --rebuild-bootstrap, --rebuild-lazy-assets and --bump-cache explicitly when
a data-writing stage has already been reviewed and needs the browser payload
updated.
"""

from __future__ import annotations

import argparse
import gzip
import json
import py_compile
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
BOOTSTRAP_PATH = Path("data/bootstrap.js")
INDEX_PATH = Path("index.html")
SW_PATH = Path("sw.js")
LAZY_ASSET_SCRIPT = Path("resources/build_lazy_data_assets.py")
DISPLAY_FIELDS = ["Traducción", "Traducción (es)", "Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]
DEFAULT_COMPILE_SCRIPTS = [
    Path("resources/audit_sentence_sources.py"),
    Path("resources/spanish_spellcheck_candidates.py"),
    Path("resources/source_cleanup_cedilla_research.py"),
]


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
            total += 1
            if len(rows) < bootstrap_limit:
                rows.append(json.loads(line))
    return DataStats(total_rows=total, bootstrap_rows=rows)


def rebuild_bootstrap(path: Path, stats: DataStats) -> None:
    payload = {"totalRows": stats.total_rows, "rows": stats.bootstrap_rows}
    path.write_text(
        "window.NAHUATL_BOOTSTRAP = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )


def parse_bootstrap(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"window\.NAHUATL_BOOTSTRAP = (.*);\n?$", text)
    if not match:
        raise ValueError(f"{path} does not match expected bootstrap wrapper")
    obj = json.loads(match.group(1))
    return int(obj["totalRows"]), len(obj["rows"])


def bump_index_tag(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"(data/bootstrap\.js\?v=publish-ready-)(\d+)")
    match = pattern.search(text)
    if not match:
        raise ValueError("Could not find data/bootstrap.js publish-ready tag")
    new_version = int(match.group(2)) + 1
    text = pattern.sub(rf"\g<1>{new_version}", text, count=1)
    path.write_text(text, encoding="utf-8")
    return new_version


def bump_sw_cache(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r'(CACHE_VERSION = "v)(\d+)(")')
    match = pattern.search(text)
    if not match:
        raise ValueError("Could not find service-worker CACHE_VERSION")
    new_version = int(match.group(2)) + 1
    text = pattern.sub(rf"\g<1>{new_version}\g<3>", text, count=1)
    path.write_text(text, encoding="utf-8")
    return new_version


def current_tags(index_path: Path, sw_path: Path) -> tuple[str, str]:
    index_text = index_path.read_text(encoding="utf-8")
    sw_text = sw_path.read_text(encoding="utf-8")
    index_match = re.search(r"data/bootstrap\.js\?v=(publish-ready-\d+)", index_text)
    sw_match = re.search(r'CACHE_VERSION = "(v\d+)"', sw_text)
    return (
        index_match.group(1) if index_match else "missing-bootstrap-tag",
        sw_match.group(1) if sw_match else "missing-cache-version",
    )


def compile_scripts(paths: list[Path]) -> None:
    for path in paths:
        py_compile.compile(str(path), doraise=True)


def run_command(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return (result.stdout + result.stderr).strip()


def rebuild_lazy_assets(script: Path) -> str:
    return run_command([sys.executable, str(script)])


def parse_target(raw: str) -> tuple[str | None, re.Pattern[str]]:
    if "::" in raw:
        source, pattern = raw.split("::", 1)
        source = source or None
    else:
        source, pattern = None, raw
    return source, re.compile(pattern, re.I)


def residue_scan(data_path: Path, raw_targets: list[str]) -> list[tuple[str, int, list[tuple[str, str, str]]]]:
    targets = [(raw, *parse_target(raw)) for raw in raw_targets]
    results: list[tuple[str, int, list[tuple[str, str, str]]]] = []
    counts = {raw: 0 for raw, _, _ in targets}
    examples: dict[str, list[tuple[str, str, str]]] = {raw: [] for raw, _, _ in targets}
    with gzip.open(data_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            row_source = row.get("Fuente", "")
            for raw, source, regex in targets:
                if source and row_source != source:
                    continue
                for field in DISPLAY_FIELDS:
                    value = row.get(field, "")
                    if not isinstance(value, str) or not value:
                        continue
                    matches = regex.findall(value)
                    if not matches:
                        continue
                    counts[raw] += len(matches)
                    if len(examples[raw]) < 5:
                        examples[raw].append((str(row.get("record_id", "")), field, str(matches[:3])))
    for raw, _, _ in targets:
        results.append((raw, counts[raw], examples[raw]))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--bootstrap", type=Path, default=BOOTSTRAP_PATH)
    parser.add_argument("--index", type=Path, default=INDEX_PATH)
    parser.add_argument("--sw", type=Path, default=SW_PATH)
    parser.add_argument("--script", action="append", type=Path, help="Additional Python script to compile. Repeatable.")
    parser.add_argument("--target", action="append", default=[], help="Residue scan, optionally Source::regex. Repeatable.")
    parser.add_argument("--rebuild-bootstrap", action="store_true", help="Rewrite data/bootstrap.js from data/data.jsonl.gz.")
    parser.add_argument("--rebuild-lazy-assets", action="store_true", help="Rewrite data/lazy search indexes and row chunks.")
    parser.add_argument("--bump-cache", action="store_true", help="Increment index.html bootstrap tag and sw.js cache version.")
    parser.add_argument("--skip-audit", action="store_true")
    parser.add_argument("--skip-spellcheck", action="store_true")
    parser.add_argument("--skip-cedilla-research", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []

    try:
        stats = read_data_stats(args.data)
        print(f"gzip/data ok totalRows={stats.total_rows} bootstrapRowsSource={len(stats.bootstrap_rows)}")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"gzip/data failed: {exc}")
        stats = DataStats(total_rows=0, bootstrap_rows=[])

    if args.rebuild_bootstrap and stats.total_rows:
        try:
            rebuild_bootstrap(args.bootstrap, stats)
            print(f"rebuilt {args.bootstrap}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"bootstrap rebuild failed: {exc}")

    if args.rebuild_lazy_assets and stats.total_rows:
        try:
            print(rebuild_lazy_assets(LAZY_ASSET_SCRIPT))
        except Exception as exc:  # noqa: BLE001
            failures.append(f"lazy asset rebuild failed: {exc}")

    try:
        bootstrap_total, bootstrap_rows = parse_bootstrap(args.bootstrap)
        print(f"bootstrap parse ok totalRows={bootstrap_total} rows={bootstrap_rows}")
        if stats.total_rows and bootstrap_total != stats.total_rows:
            failures.append(f"bootstrap totalRows mismatch: {bootstrap_total} != {stats.total_rows}")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"bootstrap parse failed: {exc}")

    scripts = list(DEFAULT_COMPILE_SCRIPTS)
    if args.script:
        scripts.extend(args.script)
    try:
        compile_scripts(scripts)
        print("py_compile ok " + " ".join(str(path) for path in scripts))
    except Exception as exc:  # noqa: BLE001
        failures.append(f"py_compile failed: {exc}")

    if not args.skip_audit:
        try:
            output = run_command(
                [
                    sys.executable,
                    "resources/audit_sentence_sources.py",
                    "--units",
                    "/tmp/sentence_source_units_audit.tsv",
                    "--profiles",
                    "/tmp/sentence_source_profiles.json",
                    "--summary",
                    "/tmp/sentence_source_profile_summary.tsv",
                    "--candidates",
                    "/tmp/sentence_source_normalization_candidates.tsv",
                ]
            )
            print(output)
            if "rows=0" not in output:
                failures.append("sentence-source audit produced candidates")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"sentence-source audit failed: {exc}")

    if not args.skip_spellcheck:
        try:
            output = run_command(
                [
                    sys.executable,
                    "resources/spanish_spellcheck_candidates.py",
                    "--output",
                    "/tmp/spanish_spellcheck_verify_cleanup_stage.tsv",
                    "--summary",
                ]
            )
            print(output)
            if "No candidates found." not in output:
                failures.append("Spanish spellcheck produced candidates")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Spanish spellcheck failed: {exc}")

    if not args.skip_cedilla_research:
        try:
            output = run_command(
                [
                    sys.executable,
                    "resources/source_cleanup_cedilla_research.py",
                    "--output",
                    "/tmp/source_cleanup_cedilla_research.tsv",
                    "--summary",
                    "/tmp/source_cleanup_cedilla_research_summary.json",
                ]
            )
            print(output)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"cedilla research failed: {exc}")

    if args.target:
        for raw, count, examples in residue_scan(args.data, args.target):
            print(f"target {raw!r} count={count} examples={examples}")
            if count:
                failures.append(f"target residue remained for {raw}: {count}")

    if args.bump_cache:
        try:
            publish_ready = bump_index_tag(args.index)
            cache_version = bump_sw_cache(args.sw)
            print(f"bumped cache publish-ready-{publish_ready} v{cache_version}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"cache bump failed: {exc}")

    index_tag, sw_tag = current_tags(args.index, args.sw)
    print(f"cache tags {index_tag} {sw_tag}")

    if failures:
        print("FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("verify ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
