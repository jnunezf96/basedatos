"""Trilingüe EO → TE character-level rules.

Importable module: `normalize(eo)` returns the edición form.
Single source of truth for phase 3 validation and phase 4 completion.
"""
import re
import unicodedata


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def strip_verb_prefix(s: str) -> str:
    if s.startswith("ni") and len(s) > 4:
        return s[2:]
    return s


def normalize(s: str, *, drop_prefix: bool = True) -> str:
    """Apply the Trilingüe EO → edición rules. Operates on one whitespace-delimited token."""
    s = s.lower()
    # ç must be handled before NFD — NFD decomposes it to c + combining cedilla,
    # and Mn-strip then loses the cedilla entirely.
    s = s.replace("çu", "zo")
    s = s.replace("ç", "z")
    s = strip_accents(s)
    # Scribal q^ = qui.
    s = s.replace("^", "ui")
    # Stray Spanish s for /z/ before a vowel.
    s = re.sub(r"s([aeiou])", r"z\1", s)
    # qua/quo → cua/cuo.
    s = re.sub(r"qu([ao])", r"cu\1", s)
    # v used for /w/ → hu.
    s = s.replace("v", "hu")
    # Intervocalic u → hu.
    s = re.sub(r"([aeiou])u([aeiou])", r"\1hu\2", s)
    # Word-initial u before vowel → hu.
    s = re.sub(r"(^|\s)u([aeiou])", r"\1hu\2", s)
    # Post-consonant u for l/x clusters.
    s = re.sub(r"([lx])u([aeiou])", r"\1hu\2", s)
    # Intervocalic o between open vowels → hu.
    s = re.sub(r"([ae])o([ae])", r"\1hu\2", s)
    # n → m before labial.
    s = re.sub(r"n([pb])", r"m\1", s)
    # hu → uh at syllable coda — narrow to likely coda consonants (t, c, q).
    s = re.sub(r"([aeiou])hu([ctq])", r"\1uh\2", s)
    # Intervocalic i → y (last, so it doesn't disturb the hu/uh decision).
    s = re.sub(r"([aeiouh])i([ao])", r"\1y\2", s)
    if drop_prefix:
        s = strip_verb_prefix(s)
    return s


def normalize_phrase(s: str, *, drop_prefix_first_only: bool = True) -> str:
    """Apply `normalize` token-by-token. Only strip ni- on the first token —
    a verb's subject prefix is cited once, not on every word of a phrase."""
    tokens = [t for t in re.split(r"\s+", s.strip()) if t]
    out = []
    for i, tok in enumerate(tokens):
        drop = drop_prefix_first_only and i == 0
        out.append(normalize(tok, drop_prefix=drop))
    return " ".join(out)
