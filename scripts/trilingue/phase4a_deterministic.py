"""Phase 4a — deterministic completion of the 779 '+' rows.

For each partial:
  1. Tokenize the EO into words.
  2. Apply character rules to each token (normalize_phrase-style, but
     per-token so we can make a confidence call per slot).
  3. Identify which EO token the human-provided TE stub belongs to.
     Strategy: pick the token whose rule-normalized form is closest to
     the stub (exact, then soft, then longest shared suffix). Trust the
     human stub — overwrite that slot with the stub verbatim.
  4. Build the full TE candidate by joining the per-token outputs.
  5. Mark confidence:
        high    — every non-stub token's prediction appears as a known
                  TE form in the gold corpus (so we've seen this word
                  normalized before in the same source).
        medium  — at least one non-stub token is unknown but rules
                  applied cleanly (no residual cedilla, no `^`, no `v`).
        low     — something the rules couldn't resolve; send to LLM.

Outputs:
  phase4a_proposals.jsonl     — full proposed TE + per-token breakdown
  phase4a_stats.txt           — counts by confidence bucket
  phase4a_llm_queue.jsonl     — the subset flagged for LLM (low conf)
"""
import json
import re
import unicodedata
from pathlib import Path

from rules import normalize, strip_accents

HERE = Path(__file__).resolve().parent
PAIRS = HERE / "pairs.jsonl"
PARTIALS = HERE / "partials.jsonl"
PROPOSALS = HERE / "phase4a_proposals.jsonl"
STATS = HERE / "phase4a_stats.txt"
LLM_QUEUE = HERE / "phase4a_llm_queue.jsonl"


def soft_key(s: str) -> str:
    """Collapse the known noisy orthographic dimensions: accents, i/y, u/o,
    and bare h (since syllable-coda `hu`/`uh` alternates freely in EO)."""
    s = strip_accents(s).lower()
    s = re.sub(r"[iy]", "i", s)
    s = re.sub(r"[uo]", "u", s)
    s = s.replace("h", "")
    return s


def longest_common_suffix(a: str, b: str) -> int:
    n = 0
    while n < len(a) and n < len(b) and a[-1 - n] == b[-1 - n]:
        n += 1
    return n


def pick_stub_slot(eo_tokens: list[str], normalized: list[str], stub: str) -> int:
    """Choose the index of the EO token that the human stub aligns with."""
    stub_low = stub.lower()
    # 1. Exact match on normalized form.
    for i, n in enumerate(normalized):
        if n == stub_low:
            return i
    # 2. Soft match (i=y, u=o).
    sstub = soft_key(stub_low)
    for i, n in enumerate(normalized):
        if soft_key(n) == sstub:
            return i
    # 3. Longest common suffix on soft-keys — matches stubs that differ only
    # by coda hu/uh or u/o or i/y. Right-to-left so ties go to the rightmost
    # token (Nahuatl heads are usually last).
    sstub_key = soft_key(stub_low)
    best_i, best_len = len(eo_tokens) - 1, -1
    for i in range(len(normalized) - 1, -1, -1):
        lcs = longest_common_suffix(soft_key(normalized[i]), sstub_key)
        if lcs > best_len:
            best_len = lcs
            best_i = i
    return best_i


def has_residual_junk(token: str) -> bool:
    """Tokens that the rules couldn't clean up fully — ç, ^, or v surviving
    means something's wrong. Accents shouldn't be present either."""
    return any(c in token for c in "ç^v") or token != strip_accents(token).lower()


def main():
    # Build a set of every known TE token from the gold corpus.
    known = set()
    for line in PAIRS.open(encoding="utf-8"):
        if not line.strip():
            continue
        p = json.loads(line)
        for t in p["te_tokens"]:
            known.add(t.lower())

    partials = [json.loads(l) for l in PARTIALS.open(encoding="utf-8") if l.strip()]

    high = medium = low = 0
    llm_queue = []

    with PROPOSALS.open("w", encoding="utf-8") as out:
        for row in partials:
            eo_tokens = row["eo_tokens"]
            stub = row["te_stub"]
            # Per-token normalization. Strip `ni-` only on the first token.
            normalized = [
                normalize(tok, drop_prefix=(i == 0))
                for i, tok in enumerate(eo_tokens)
            ]
            stub_idx = pick_stub_slot(eo_tokens, normalized, stub)
            final = normalized[:]
            final[stub_idx] = stub.lower()

            non_stub = [final[i] for i in range(len(final)) if i != stub_idx]
            unknown = [t for t in non_stub if t not in known]
            junk = [t for t in non_stub if has_residual_junk(t)]

            if not junk and not unknown:
                conf = "high"
                high += 1
            elif not junk:
                conf = "medium"
                medium += 1
            else:
                conf = "low"
                low += 1

            record = {
                "record_id": row["record_id"],
                "eo": row["eo"],
                "te_stub": stub,
                "te_proposed": " ".join(final),
                "per_token": list(zip(eo_tokens, final)),
                "stub_idx": stub_idx,
                "confidence": conf,
                "unknown_tokens": unknown,
                "residual_junk": junk,
                "traduccion": row["traduccion"],
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            if conf == "low":
                llm_queue.append(record)

    with LLM_QUEUE.open("w", encoding="utf-8") as f:
        for r in llm_queue:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    total = high + medium + low
    lines = [
        f"partials processed: {total}",
        f"  high  (all non-stub tokens seen in gold): {high} ({high/total:.1%})",
        f"  medium (rules clean, some unseen tokens):  {medium} ({medium/total:.1%})",
        f"  low    (residual ç/^/v or accents — LLM):  {low} ({low/total:.1%})",
        f"",
        f"LLM queue written: {LLM_QUEUE.name} ({len(llm_queue)} rows)",
        f"full proposals:    {PROPOSALS.name}",
    ]
    STATS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
