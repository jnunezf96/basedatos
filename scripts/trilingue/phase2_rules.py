"""Phase 2 — induce character-level EO → TE rules, measure against gold.

Runs the current rule set over every single-token gold pair and reports
accuracy. Mismatches are dumped, grouped by the EO→TE diff, so the next
missing rule is obvious.

Rules live in `normalize()` as an ordered list of regex subs; edit there to
iterate. Prefix-dropping and morphology are intentionally NOT handled here —
that's a separate pass (Phase 2b / Phase 4).
"""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAIRS = HERE / "pairs.jsonl"
MISSES = HERE / "phase2_misses.jsonl"
REPORT = HERE / "phase2_report.txt"


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


# Only the 1sg subject `ni-` reliably drops in the edición. Object/reflexive
# prefixes (te-, tla-, mo-, ne-, nic-, nino-, ...) stay — they're part of the
# citation form. Stripping more than `ni-` created hundreds of false drops.
def strip_verb_prefix(s: str) -> str:
    if s.startswith("ni") and len(s) > 4:
        return s[2:]
    return s


def normalize(s: str, *, drop_prefix: bool = True) -> str:
    s = s.lower()
    # ç handling MUST precede NFD: NFD decomposes ç to c+◌̧ and Mn-strip then
    # turns it into plain c, masking the cedilla signal entirely.
    s = s.replace("çu", "zo")  # Spanish u for /o/ after cedilla.
    s = s.replace("ç", "z")
    s = strip_accents(s)
    # Scribal abbreviation q^ = qui.
    s = s.replace("^", "ui")
    # Stray Spanish s for /z/ before a vowel.
    s = re.sub(r"s([aeiou])", r"z\1", s)
    # qua/quo → cua/cuo.
    s = re.sub(r"qu([ao])", r"cu\1", s)
    # v used for semivowel /w/ → hu everywhere.
    s = s.replace("v", "hu")
    # Intervocalic u (= /w/) written hu.
    s = re.sub(r"([aeiou])u([aeiou])", r"\1hu\2", s)
    # Word-initial u before vowel → hu.
    s = re.sub(r"(^|\s)u([aeiou])", r"\1hu\2", s)
    # Post-consonant u → hu for l/x clusters (lu → lhu, xu → xhu).
    s = re.sub(r"([lx])u([aeiou])", r"\1hu\2", s)
    # Intervocalic o (= /w/) between open vowels → hu.
    s = re.sub(r"([ae])o([ae])", r"\1hu\2", s)
    # n → m before labial.
    s = re.sub(r"n([pb])", r"m\1", s)
    # hu at syllable coda — narrow to likely coda consonants (t, c, q) so the
    # rule doesn't fire before labials / nasals / liquids where hu stays intact.
    s = re.sub(r"([aeiou])hu([ctq])", r"\1uh\2", s)
    # Intervocalic i (= /y/) → y — applied LAST so the prior hu→uh decision
    # isn't disturbed by a freshly-created y.
    s = re.sub(r"([aeiouh])i([ao])", r"\1y\2", s)
    # Strip only the 1sg subject prefix.
    if drop_prefix:
        s = strip_verb_prefix(s)
    return s


def diff_key(a: str, b: str) -> str:
    """Compact signature of where a and b differ — used to cluster misses."""
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    j = 0
    while j < len(a) - i and j < len(b) - i and a[-1 - j] == b[-1 - j]:
        j += 1
    aa = a[i : len(a) - j] or "∅"
    bb = b[i : len(b) - j] or "∅"
    return f"{aa} → {bb}"


def main():
    pairs = [json.loads(l) for l in PAIRS.open(encoding="utf-8") if l.strip()]
    single = [p for p in pairs if p["category"] == "single_token"]

    n = len(single)
    hits = 0
    misses = []
    diff_counter: Counter[str] = Counter()

    for p in single:
        pred = normalize(p["eo"])
        gold = p["te"].lower()
        if pred == gold:
            hits += 1
        else:
            misses.append({"record_id": p["record_id"], "eo": p["eo"], "te": p["te"], "pred": pred})
            diff_counter[diff_key(pred, gold)] += 1

    with MISSES.open("w", encoding="utf-8") as f:
        for m in misses:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    lines = [
        f"single-token pairs: {n}",
        f"hits: {hits} ({hits/n:.1%})",
        f"misses: {len(misses)} ({len(misses)/n:.1%})",
        "",
        "top 30 miss clusters (pred → gold slice):",
    ]
    for sig, c in diff_counter.most_common(30):
        lines.append(f"  {c:5d}  {sig}")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
