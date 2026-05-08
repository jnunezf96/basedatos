#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
SPELLCHECK_SUGGESTIONS_PATH = ROOT / "scripts" / "non_wimmer_spellcheck_suggestions.jsonl"
PYTHON = sys.executable


def run_step(name: str, command: list[str], env: dict[str, str] | None = None) -> tuple[bool, str]:
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=proc_env,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout + result.stderr).strip()
    ok = result.returncode == 0
    status = "ok" if ok else "FAIL"
    print(f"{status}\t{name}")
    if output:
        print(output)
    return ok, output


def parse_changed_rows(output: str) -> int | None:
    match = re.search(r"changed_rows=(\d+)", output)
    return int(match.group(1)) if match else None


def parse_review_rows(output: str) -> int | None:
    match = re.search(r"rows=(\d+)", output)
    return int(match.group(1)) if match else None


def parse_open_review_rows(output: str) -> int | None:
    match = re.search(r"open_review_rows=(\d+)", output)
    return int(match.group(1)) if match else None


def validate_jsonl() -> bool:
    count = 0
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            json.loads(line)
            count += 1
    print(f"ok\tjsonl_parse\nrows={count}")
    return True


def main() -> None:
    failures: list[str] = []

    try:
        validate_jsonl()
    except Exception as exc:
        print(f"FAIL\tjsonl_parse\n{exc}")
        failures.append("jsonl_parse")

    ok, output = run_step(
        "orthography_idempotence",
        [PYTHON, "scripts/non_wimmer_old_spanish_orthography_cluster_pass.py"],
        env={"DRY_RUN": "1"},
    )
    if not ok or parse_changed_rows(output) != 0:
        failures.append("orthography_idempotence")

    ok, output = run_step(
        "context_required_review",
        [PYTHON, "scripts/non_wimmer_context_required_spelling_review.py"],
    )
    if not ok or parse_review_rows(output) != 0:
        failures.append("context_required_review")

    ok, _output = run_step(
        "spellcheck_candidate_inventory",
        [PYTHON, "scripts/non_wimmer_spellcheck_candidate_inventory.py"],
    )
    if not ok:
        failures.append("spellcheck_candidate_inventory")

    refresh_swift = os.environ.get("REFRESH_SWIFT") == "1"
    swift = shutil.which("swift")
    if refresh_swift and swift:
        swift_cache = Path(os.environ.get("TMPDIR", "/private/tmp")) / "nahuatl-db-swift-module-cache"
        swift_cache.mkdir(parents=True, exist_ok=True)
        ok, output = run_step(
            "spanish_spellcheck_suggestions",
            [
                swift,
                "-module-cache-path",
                str(swift_cache),
                "scripts/spanish_spellcheck_candidates.swift",
                "es",
                "scripts/non_wimmer_spellcheck_candidate_tokens.txt",
                "scripts/non_wimmer_spellcheck_suggestions.jsonl",
            ],
            env={"CLANG_MODULE_CACHE_PATH": str(swift_cache)},
        )
        if not ok or "findMisspelledWordInString received error" in output:
            failures.append("spanish_spellcheck_suggestions")
    elif refresh_swift:
        print("FAIL\tspanish_spellcheck_suggestions\nswift not found")
        failures.append("spanish_spellcheck_suggestions")
    else:
        print("WARN\tspanish_spellcheck_suggestions\nusing existing suggestions file; set REFRESH_SWIFT=1 to regenerate")
        if not SPELLCHECK_SUGGESTIONS_PATH.exists() or SPELLCHECK_SUGGESTIONS_PATH.stat().st_size == 0:
            failures.append("spanish_spellcheck_suggestions")

    ok, _output = run_step(
        "spellcheck_suggestion_review",
        [PYTHON, "scripts/non_wimmer_spellcheck_suggestion_review.py"],
    )
    if not ok:
        failures.append("spellcheck_suggestion_review")

    ok, output = run_step(
        "rla_accounting_strict",
        [PYTHON, "scripts/non_wimmer_rla_lexicon_review.py"],
        env={"STRICT": "1"},
    )
    if not ok or parse_open_review_rows(output) != 0:
        failures.append("rla_accounting_strict")

    if failures:
        print("FAIL\tnormalization_gate")
        print("failures=" + ", ".join(failures))
        raise SystemExit(1)

    print("ok\tnormalization_gate")


if __name__ == "__main__":
    main()
