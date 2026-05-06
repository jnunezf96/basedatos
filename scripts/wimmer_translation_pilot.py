"""Build a review pilot for cleaner 2021 Wimmer Spanish translations.

This script does not rewrite data/data.jsonl.gz. It reads the current dataset,
derives concise Spanish-only proposals for 2021 Wimmer `Traducción (es)` from
`Comentario (es)`, validates them, and writes a small review batch.

Usage:
    python3 scripts/wimmer_translation_pilot.py --limit 25
"""

from __future__ import annotations

import argparse
import gzip
import html
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "data.jsonl.gz"
OUT_JSONL = ROOT / "scripts" / "wimmer_translation_pilot_review.jsonl"
OUT_TXT = ROOT / "scripts" / "wimmer_translation_pilot_review.txt"

ANCHOR_LEMMAS = {"canahuacantli", "cochca", "tlaciuhcayotl", "cotoncayotl"}
META_SECTION = "__meta__"
KNOWN_LABELS = {"botánica", "calendario", "expresión", "metáfora", "ornitología", "parentesco", "plural", "ritual", "topónimo"}
GRAMMAR_ROLE_FALLBACKS = {
    "algo": "v.t. tla-",
    "persona": "v.t. tē-",
    "persona/algo": "v.t. tē-. o tla-",
    "persona + algo": "v.bitrans. tētla-",
    "reflexivo": "v.refl",
    "reflexivo + algo": "v.bitrans. motla-",
    "reflexivo + persona": "v.bitrans. motē-",
    "pasivo": "v.refl. con significado pasivo",
    "pasivo impersonal": "v.pasivo-impers",
    "impersonal": "v.impers",
    "intransitivo": "v.i",
    "transitivo": "v.t",
    "recíproco": "v.recipr",
    "reciproco": "v.recipr",
    "sujeto inanimado": "v.inanim",
    "bitransitivo": "v.bitrans",
}
STOPWORDS = {
    "a", "al", "algo", "alguien", "ante", "aquel", "aquella", "aquello", "aquellos",
    "aquellas", "asi", "así", "bajo", "cada", "como", "con", "contra", "cuando",
    "de", "del", "desde", "donde", "dos", "el", "ella", "ellas", "ello", "ellos",
    "en", "entre", "era", "eran", "es", "esa", "ese", "eso", "esta", "este",
    "estos", "estas", "forma", "hablando", "hacia", "hasta", "hay", "la", "las",
    "le", "les", "lo", "los", "mas", "más", "muy", "no", "o", "para", "por",
    "que", "se", "segun", "según", "ser", "si", "sin", "sobre", "son", "su",
    "sus", "tambien", "también", "un", "una", "unas", "uno", "unos", "y",
}
NAHUATL_MARK_RE = re.compile(r"[āēīōūĀĒĪŌŪâêîôûÂÊÎÔÛ]")
WORD_RE = re.compile(r"[\wÁÉÍÓÚÜÑáéíóúüñ]+", re.UNICODE)
CITATION_RE = re.compile(
    r"\b(?:Sah|Sa|SIS|A\.J\.O\.Anderson|W\.Lehmann|R\.Andrews|Andrews|"
    r"W\.?Jim[eé]nez|Jim[eé]nez|Rammow|Garibay|Molina|Siméon|Grasserie|"
    r"Bnf|Dyckerhoff|Ivanoff|Launey|Par\.|Reglas|Rules|Pintura\s+del\s+gobernador)\b"
    r"|\b(?:Sah|Sa)\s*\d+\s*,\s*\d+",
    re.IGNORECASE,
)
FORM_NOTE_RE = re.compile(
    r"^(?:cf\.?|cfr\.?|v[ée]ase|ver\b|"
    r"(?:a|en|con)?\s*(?:la\s+)?forma\s+pose[ií]da|"
    r"(?:s[oó]lo|solo|solamente|únicamente)\s+(?:en\s+)?(?:la\s+)?forma\s+pose[ií]da|"
    r"plur\.?|plural\.?|v\.[\w.-]+|sustantivo\s+posesivo|top[oó]nimo)\b",
    re.IGNORECASE,
)
GRAMMAR_NOTE_RE = re.compile(
    r"^(?:ap[oó]cope\b|auxiliar\b|diminutivo\b|divino\b|[ée]tnico\b|interj\.?\b|"
    r"loc\.?\b|locativo\b|n\.?\s*(?:divina|posesivo)\b|nombre\s+(?:descriptivo|divino|personal)\b|"
    r"n\.?\s*pers\.?\b|n[uú]mero\b|pasivo\b|passif\b|pft\.?\b|pl\.?\b|plr\.?\b|posible\b|pref\.?\b|"
    r"redup(?:l\.)?\b|honor\.?\b|"
    r"t[eé]rmino\b|top[oó]n\.?\b|var\.?\b)",
    re.IGNORECASE,
)
SECTION_NOISE_RE = re.compile(
    r"\b(?:forma\s+pose[ií]da|forma\s+eventual|forma\b|nombre\s+de|"
    r"pasivo|pft\.?|perfecto|variante|cf\.?|v[ée]ase)\b",
    re.IGNORECASE,
)
SENSE_MARKER_RE = re.compile(r"^\s*(?:\d+\.~|\d+\.)\s*")
LETTER_HEADER_RE = re.compile(r"^\s*[A-Z]\.~")
OUTPUT_LABEL_RE = re.compile(
    r"^\s*(?:algo|persona|persona/algo|persona\s+\+\s+algo|reflexivo|"
    r"reflexivo\s+\+\s+algo|reflexivo\s+\+\s+persona|pasivo|pasivo\s+impersonal|"
    r"impersonal|intransitivo|transitivo|rec[ií]proco|sujeto\s+inanimado|"
    r"bitransitivo)\s*:\s*|"
    r"^\s*(?:v\.[^,/]*|passif|pasivo|impers|refl|recipr)\s*[,.;:]?\s*",
    re.IGNORECASE,
)
SOURCE_ONLY_RE = re.compile(
    r"^(?:"
    r"adular|alem\.?|annalen\b|c[oó]dice\b|descripci[oó]n\b|el\s+glifo\b|"
    r"dib\.?|elisabeth\b|entrada\b|garza\b|hang\b|ingl\.?|matr[ií]cula\b|primeros\s+memoriales\b|"
    r"rammow\b|ruiz\s+de\s+alarc[oó]n\b|sga\b|to\s+\w+|vel[aá]zquez\b|wegwerfen\b|w\.\b"
    r")",
    re.IGNORECASE,
)
COMMENTARY_RE = re.compile(
    r"\b(?:"
    r"citado|describe|descripci[oó]n|dicho\s+de|en\s+este\s+sentido|"
    r"en\s+la\s+mitolog[ií]a|entre\s+las\s+edificaciones|este\s+es|esta\s+es|mercaderes|presagios?|retomado\s+por|ritual\s+en\s+honor|"
    r"se\s+dice|se\s+dirige|"
    r"se\s+presenta|se\s+trata|utilizado\s+por|v[ée]ase"
    r")\b",
    re.IGNORECASE,
)


@dataclass
class Segment:
    text: str
    bold: bool = False
    small: bool = False
    italic: bool = False


@dataclass
class ParsedLine:
    segments: list[Segment] = field(default_factory=list)

    def text(self, *, include_bold: bool = True, include_small: bool = True) -> str:
        parts: list[str] = []
        for seg in self.segments:
            if not include_bold and seg.bold:
                continue
            if not include_small and seg.small:
                continue
            parts.append(seg.text)
        return collapse(" ".join(parts))

    @property
    def has_bold(self) -> bool:
        return any(seg.bold for seg in self.segments)

    @property
    def small_text(self) -> str:
        return collapse(" ".join(seg.text for seg in self.segments if seg.small))

    @property
    def bold_text(self) -> str:
        return collapse(" ".join(seg.text for seg in self.segments if seg.bold))


@dataclass
class Candidate:
    text: str
    snippet: str
    origin: str
    index: int
    label: str | None = None
    marker: str | None = None
    role: str | None = None
    role_label: str | None = None
    features: set[str] = field(default_factory=set)
    old_score: float = 0.0
    corpus_score: float = 0.0


class CommentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[ParsedLine] = [ParsedLine()]
        self.bold = 0
        self.small = 0
        self.italic = 0

    def _break(self) -> None:
        if self.lines[-1].segments:
            self.lines.append(ParsedLine())

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        tag = tag.lower()
        if tag == "br":
            self._break()
        elif tag == "b":
            self.bold += 1
        elif tag == "small":
            self.small += 1
        elif tag in {"i", "em"}:
            self.italic += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "b":
            self.bold = max(0, self.bold - 1)
        elif tag == "small":
            self.small = max(0, self.small - 1)
        elif tag in {"i", "em"}:
            self.italic = max(0, self.italic - 1)

    def handle_data(self, data: str) -> None:
        if not data:
            return
        self.lines[-1].segments.append(
            Segment(data, bold=self.bold > 0, small=self.small > 0, italic=self.italic > 0)
        )


def collapse(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def normalize(value: str) -> str:
    import unicodedata

    return "".join(
        ch for ch in unicodedata.normalize("NFD", value or "") if unicodedata.category(ch) != "Mn"
    ).lower()


def word_count(value: str) -> int:
    return len(WORD_RE.findall(value or ""))


def strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", html.unescape(value or ""))


def source_word_count(value: str) -> int:
    return word_count(strip_html(value))


def content_tokens(value: str) -> set[str]:
    tokens: set[str] = set()
    for token in WORD_RE.findall(strip_html(value or "")):
        key = re.sub(r"[^a-z0-9]+", "", normalize(token))
        if len(key) < 3 or key.isdigit() or key in STOPWORDS:
            continue
        tokens.add(key)
    return tokens


def translation_segments(value: str) -> list[str]:
    segments: list[str] = []
    for raw in re.split(r"\s*/\s*", strip_html(value or "")):
        cleaned = clean_source_text(raw)
        if cleaned.strip(" .;,:"):
            segments.append(cleaned.strip(" .;,:"))
    return segments


def overlap_score(a: str, b: str) -> float:
    a_tokens = content_tokens(a)
    b_tokens = content_tokens(b)
    if not a_tokens or not b_tokens:
        return 0.0
    inter = len(a_tokens & b_tokens)
    if not inter:
        return 0.0
    precision = inter / len(a_tokens)
    recall = inter / len(b_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    a_norm = normalize(a)
    b_norm = normalize(b)
    if len(a_tokens) <= 3 and (a_norm in b_norm or b_norm in a_norm):
        f1 = max(f1, 0.92)
    return f1


def best_old_score(text: str, old_segments: list[str]) -> float:
    return max((overlap_score(text, seg) for seg in old_segments), default=0.0)


def sentence_case(value: str) -> str:
    value = collapse(value)
    if not value:
        return value
    if value.upper() == value:
        value = value.lower()
    return value[0].upper() + value[1:]


def lower_initial(value: str) -> str:
    value = collapse(value)
    if not value:
        return value
    return value[0].lower() + value[1:]


def ensure_period(value: str) -> str:
    value = collapse(value)
    if not value:
        return value
    return value if value[-1] in ".!?" else value + "."


def join_glosses(values: list[str]) -> str:
    cleaned = [collapse(value) for value in values if collapse(value)]
    if not cleaned:
        return ""
    use_semicolon = any("," in value or word_count(value) > 4 for value in cleaned)
    return ("; " if use_semicolon else ", ").join(cleaned)


def split_glosses(value: str) -> list[str]:
    return [part.strip(" ,.;:") for part in re.split(r"\s*(?:;|,|\by\b)\s*", value) if part.strip(" ,.;:")]


def genericize_possessive(value: str) -> str:
    value = collapse(value)
    value = re.sub(r"\((?:Par\.?|S\.?|M\.?)\)", "", value, flags=re.IGNORECASE)
    value = re.sub(
        r"(^|[,.;]\s+)(?:mi|mis|tu|tus|su|sus|nuestro|nuestra|nuestros|nuestras|"
        r"vuestro|vuestra|vuestros|vuestras)\s+",
        r"\1",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"(^|[,.;]\s+)plural\.?,?\s+", r"\1", value, flags=re.IGNORECASE)
    return collapse(value.strip(" ,.;:"))


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        value = collapse(value)
        key = normalize(value).strip(" .;,:")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def clean_source_text(value: str) -> str:
    value = collapse(value)
    value = re.sub(r"^[,;:\s.-]+", "", value)
    value = re.split(r"\s+-\s+", value, maxsplit=1)[0]
    value = re.sub(r"\(\s*\)", "", value)
    value = re.sub(r"\([^)]*(?:Par\.?|S\.?|M\.?|Bnf|z\d+|[a-z]\s*\d+\s*[rv]?|m\s+[ivxlc]+|Rules|Reglas)[^)]*\)", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(?:Sah|Sa|SIS)\s*\d+[^.;]*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(?:A\.J\.O\.Anderson|W\.Lehmann|W\.?Jim[eé]nez|Jim[eé]nez|R\.Andrews|Andrews|Rammow|Garibay|Molina|Siméon|Grasserie|Bnf|Pintura\s+del\s+gobernador)\b.*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(?:Dyckerhoff|Ivanoff|Launey|Olmos|Mendieta|Motolin[ií]a|Tezozomoc|Torquemada|Clavijero|Clav\.)\b.*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(?:M|S|K)\.\s*$", "", value)
    value = re.sub(r"\bIngl\.\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(?:Alem|Ingl|Franc)\.\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bcomparad[oa]s?\s+en\s+con\b", "comparados con", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+([,.;:!?])", r"\1", value)
    return collapse(value.strip(" ,.;:"))


def clean_non_bold_text(value: str) -> str:
    value = clean_source_text(value)
    value = re.sub(r"^\s*(?:o|y)\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^\s*[,.;:]+\s*", "", value)
    return collapse(value)


def is_bad_definition(value: str) -> bool:
    value = collapse(value)
    normalized = normalize(value)
    if not value:
        return True
    labeled_definition = bool(re.match(
        r"^(?:botanica|calendario|metafora|nombre divino|nombre personal|ornitologia|ritual|toponimo),",
        normalized,
    ))
    if not labeled_definition and (FORM_NOTE_RE.search(normalized) or GRAMMAR_NOTE_RE.search(normalized)):
        return True
    if normalized in {"forma", "plur", "plural", "toponimo", "etnico", "pft", "locativo", "posible", "honor"}:
        return True
    if re.search(r"\b(?:cf|cfr|ver)\b", normalized):
        return True
    if "poseia solo forma" in normalized or "solo forma" in normalized:
        return True
    if "'" in value or "’" in value:
        return True
    if normalized in {"r", "r.", "d.diego", "d diego", "entrada", "n divino", "n.divino", "tla", "tla.", "tla-"}:
        return True
    if re.search(r"\b(?:apareceria|aparecería|transcribe|texto correspondiente|nombre antiguo|este es|sacerdote)\b", normalized):
        return True
    if re.search(r"\b(?:alem|annalen|begriff|bedeutung|clav|ein|faucon|hang|humide|meilleur|mouille|petit|quelque|sept|to\s+\w+|unterwelt|wegwerfen)\b", normalized):
        return True
    if re.search(r"\bp\s*:", normalized):
        return True
    if SOURCE_ONLY_RE.search(value):
        return True
    if COMMENTARY_RE.search(value):
        return True
    if normalized.startswith((
        "nota:", "forma:", "forma ", "variante ", "etym", "vease", "véase",
        "nombre propio ",
        "cf.", "cfr.", "como ", "describe ", "se dice ", "citado ", "atestiguado ",
        "pero ", "probablemente ", "sin duda ", "r.simeon", "r. simeon", "x ", "para ",
        "d.diego", "d. diego",
    )):
        return True
    return False


def starts_sense_marker(line: ParsedLine) -> bool:
    return bool(SENSE_MARKER_RE.match(line.text(include_small=False)))


def is_letter_header(line: ParsedLine) -> bool:
    return bool(LETTER_HEADER_RE.match(line.text(include_small=False)))


def strip_sense_marker(value: str) -> str:
    return SENSE_MARKER_RE.sub("", value or "", count=1)


def compact_definition(value: str) -> str:
    value = clean_non_bold_text(strip_sense_marker(value))
    value = re.sub(r"^\s*n\.?\s*divin[oa]\.?\s*", "nombre divino, ", value, flags=re.IGNORECASE)
    value = re.sub(r"^\s*met[aá]fora\.?,?\s*", "metáfora, ", value, flags=re.IGNORECASE)
    value = re.sub(r"^\s*metaph\.?,?\s*", "metáfora, ", value, flags=re.IGNORECASE)
    value = re.sub(r"^\s*expresi[oó]n\.?,?\s*", "expresión, ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bpor\s+ap[oó]cope\b.*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bCf\..*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bV[ée]ase\b.*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bEl\s+refl\.\s+sirve\s+como\s+pasivo\s+para\s+\w+\.\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bHom[oó]nimo\b.*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*\([^)]*[āēīōūâêîôûĀĒĪŌŪÂÊÎÔÛ][^)]*\)", "", value)
    value = re.sub(r"\s*'[^']*[āēīōūâêîôûĀĒĪŌŪÂÊÎÔÛ][^']*'", "", value)
    value = re.sub(r"\s*'[^']*'", "", value)
    value = re.sub(r"\b(el\s+t[eé]rmino|la\s+palabra)\s+[a-zāēīōūâêîôû-]+\s+(?:tambi[eé]n\s+)?designa(?:r[ií]a)?(?:\s+seg[uú]n\s+\w+)?\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^\s*designa(?:r[ií]a)?(?:\s+seg[uú]n\s+\w+)?(?:\s+com[uú]nmente)?\s+(?:a(?:l| la| los| las)?\s+)?", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^\s*de manera m[aá]s general a\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^\s*se\s+traduce\s+(?:por|como)\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^\s*nombre\s+de\s+la\s+planta\b", "nombre de planta", value, flags=re.IGNORECASE)
    value = re.sub(r"^\s*Nombre\s+divino,\s*", "nombre divino, ", value)
    value = re.sub(r"^\s*Ritual,\s*", "ritual, ", value)
    value = re.sub(r"^\s*Top[oó]nimo,\s*", "topónimo, ", value)
    value = re.sub(r"^\s*Calendario,\s*", "calendario, ", value)
    value = re.sub(r"^\s*Bot[aá]nica,\s*", "botánica, ", value)
    value = re.sub(r"^\s*Ornitolog[ií]a,\s*", "ornitología, ", value)
    value = re.sub(r",\s*,+", ", ", value)
    if re.search(r"\bcomparad[oa]s?\s+con\b", value, flags=re.IGNORECASE):
        value = re.split(r"\bcomparad[oa]s?\s+con\b", value, maxsplit=1, flags=re.IGNORECASE)[0]
    if ":" in value and word_count(value.split(":", 1)[0]) >= 7:
        value = value.split(":", 1)[0]
    if ";" in value and word_count(value) > 18:
        value = value.split(";", 1)[0]
    if "," in value and word_count(value) > 20:
        left, right = value.split(",", 1)
        if word_count(left) >= 4 and not re.search(r"\b(?:calendario|met[aá]fora|parentesco|plural|top[oó]nimo|ritual|bot[aá]nica|ornitolog[ií]a)\b", normalize(left)):
            value = left
    value = re.sub(r"\s+([,.;:!?])", r"\1", value)
    return collapse(value.strip(" ,.;:"))


def definition_from_line(line: ParsedLine) -> str:
    if is_letter_header(line):
        return ""
    value = line.text(include_bold=False, include_small=False)
    if not value and starts_sense_marker(line):
        value = line.text(include_small=False)
    value = compact_definition(value)
    if not value or is_bad_definition(value):
        return ""
    if value.startswith(("(", ")", ",", ";", ":")):
        return ""
    if word_count(value) > 28:
        return ""
    if NAHUATL_MARK_RE.search(value) or has_likely_nahuatl_word(value):
        return ""
    return sentence_case(value)


def peel_inline_label(value: str) -> tuple[str | None, str]:
    match = re.match(
        r"^\s*(met[aá]fora|expresi[oó]n|plural|parentesco|bot[aá]nica|ornitolog[ií]a|calendario|ritual|top[oó]nimo)\s*,\s*(.+)$",
        value,
        flags=re.IGNORECASE,
    )
    if not match:
        return None, value
    label = normalize(match.group(1))
    label = {
        "botanica": "botánica",
        "expresion": "expresión",
        "metafora": "metáfora",
        "ornitologia": "ornitología",
        "toponimo": "topónimo",
    }.get(label, label)
    return label, sentence_case(match.group(2))


def has_likely_nahuatl_word(value: str) -> bool:
    allowed = {
        "azteca", "aztecas", "chichimeca", "chichimecas", "chinampa", "chinampas",
        "mexica", "mexicas", "mexico", "mexicano", "mexicanos", "nahuatl",
        "otomies", "otomíes", "tenochtitlan", "tlaxcala", "tlaxcalteca", "tlaxcaltecas",
    }
    for token in WORD_RE.findall(value or ""):
        key = re.sub(r"[^a-z0-9]+", "", normalize(token))
        if len(key) < 5 or key in allowed:
            continue
        if re.search(r"(?:tl|tz|zt|auh|euh|iuh|yoh|tzin|teca|xoch|cuauh|cauh|chih|hu[aeio])", key):
            return True
        if key.endswith(("tli", "tzin", "tontli", "tin", "meh", "can", "yan", "yotl", "cayotl")):
            return True
    return False


def extract_glosses(plain: str, *, max_words: int = 6) -> list[str]:
    plain = clean_non_bold_text(plain)
    if is_bad_definition(plain):
        return []
    glosses = [genericize_possessive(part) for part in split_glosses(plain)]
    out: list[str] = []
    for gloss in glosses:
        if not gloss or is_bad_definition(gloss):
            continue
        if word_count(gloss) > max_words:
            continue
        if NAHUATL_MARK_RE.search(gloss) or has_likely_nahuatl_word(gloss):
            continue
        out.append(gloss)
    return out


def section_marker(small_text: str) -> str | None:
    text = clean_source_text(small_text)
    text = re.sub(r"^\*~\s*", "", text).strip()
    normalized = normalize(text)
    if not text:
        return None
    if re.search(r"\bforma\s+pose[ií]da\b", normalized):
        return META_SECTION
    if SECTION_NOISE_RE.search(normalized):
        return None
    if re.search(r"\bplur\.?|plural\b", normalized):
        return "plural"
    if re.search(r"\bmet[aá]fora|metaf\.?|metaf[oó]rico|metaphor", normalized):
        return "metáfora"
    if re.search(r"\bparentesco|parent[eé]\b", normalized):
        return "parentesco"
    if re.search(r"\bbot\.?|bot[aá]nica\b", normalized):
        return "botánica"
    if re.search(r"\bornit\.?|ornitolog[ií]a\b", normalized):
        return "ornitología"
    if len(text.split()) <= 3 and not FORM_NOTE_RE.search(normalized):
        return text.strip(" .,:;").lower()
    return None


def section_role(small_text: str) -> str | None:
    text = clean_source_text(small_text)
    text = re.sub(r"^\*~\s*", "", text).strip()
    normalized = normalize(text)
    normalized = re.sub(r"\s+", " ", normalized)
    if not normalized:
        return None
    if "bitrans" in normalized:
        if re.search(r"\btetla\s*-?", normalized):
            return "persona + algo"
        if re.search(r"\bmotla\s*-?", normalized):
            return "reflexivo + algo"
        if re.search(r"\bmote\s*-?", normalized):
            return "reflexivo + persona"
        return "bitransitivo"
    if re.search(r"pasivo\s*-\s*impers|passif\s*-\s*impers", normalized):
        return "pasivo impersonal"
    if "impers" in normalized:
        return "impersonal"
    if "recipr" in normalized:
        return "recíproco"
    if "refl" in normalized:
        if re.search(r"pasiv|passif|sentido pasivo|significado pasivo", normalized):
            return "pasivo"
        return "reflexivo"
    if re.search(r"\bpassif\b|\bpasiv", normalized):
        return "pasivo"
    if re.search(r"\bv\.?\s*inanim\b|\binanim", normalized):
        return "sujeto inanimado"
    if re.search(r"\bv\.?\s*i\b|\bintrans", normalized):
        return "intransitivo"
    if re.search(r"\bv\.?\s*t\b|\btrans", normalized):
        has_tetla = bool(re.search(r"\btetla\s*-?", normalized))
        has_motla = bool(re.search(r"\bmotla\s*-?", normalized))
        has_mote = bool(re.search(r"\bmote\s*-?", normalized))
        has_te = bool(re.search(r"\bte\s*-", normalized)) and not (has_tetla or has_mote)
        has_tla = bool(re.search(r"\btla\s*-", normalized)) and not (has_tetla or has_motla)
        if has_te and has_tla:
            return "persona/algo"
        if has_te:
            return "persona"
        if has_tla:
            return "algo"
        return "transitivo"
    return None


def section_role_label(small_text: str) -> str | None:
    text = clean_source_text(small_text)
    text = re.sub(r"^\*~\s*", "", text).strip(" .,:;")
    if not text:
        return None
    normalized = normalize(text)
    if ":" in text:
        return None
    if re.match(r"^(?:v\.|passif|pasivo|impers|refl|recipr)", normalized):
        return normalize_grammar_marker_label(text)
    return None


def normalize_grammar_marker_label(label: str) -> str:
    label = collapse(label).strip(" .,:;")
    label = re.sub(r"^V\.", "v.", label)
    label = re.sub(r"^N\.", "n.", label)
    label = re.sub(r"^Adj\.", "adj.", label)
    label = re.sub(r"^Adv\.", "adv.", label)
    return label


def reconciled_role_label(label: str | None, text: str) -> str | None:
    if not label:
        return None
    label = normalize_grammar_marker_label(label)
    normalized = normalize(label)
    if "bitrans" in normalized or re.search(r"\b(?:tetla|motla|mote)\s*-?", normalized):
        return label
    if not re.search(r"\bv\.?\s*t\b", normalized):
        return label
    has_tla = bool(re.search(r"\btla\s*-?", normalized))
    has_te = bool(re.search(r"\bte\s*-?", normalized))
    if has_tla and has_te:
        return label
    signature = object_contrast_signature(text)
    if signature == {"person"} and has_tla:
        return re.sub(r"\btla\s*-?", "tē-", label, count=1, flags=re.IGNORECASE)
    if signature == {"thing"} and has_te:
        return re.sub(r"\bt[ēeê]\s*-?", "tla-", label, count=1, flags=re.IGNORECASE)
    return label


def inline_role_context(line: ParsedLine) -> tuple[str | None, str | None]:
    small = line.small_text
    if not small or line.text() == small:
        return None, None
    return section_role(small), section_role_label(small)


def is_definition_section_marker(small_text: str) -> bool:
    text = clean_source_text(small_text)
    text = re.sub(r"^\*~\s*", "", text).strip()
    normalized = normalize(text)
    if not text or re.search(r"\b(?:forma|vocativ|sufijo|redup|diminutivo|ap[oó]cope)\b", normalized):
        return False
    if re.match(r"^(?:v\.|n\.|adj\.?|adv\.?|sust\.?)", normalized):
        return True
    return bool(KNOWN_LABELS.intersection({section_marker(small_text) or ""}))


def section_prefix(marker: str | None) -> str | None:
    if not marker or marker == META_SECTION:
        return None
    if marker in KNOWN_LABELS:
        return marker
    return None


def parse_comment(comment: str) -> list[ParsedLine]:
    parser = CommentParser()
    parser.feed(comment or "")
    return [line for line in parser.lines if line.text()]


def bold_keys(lines: list[ParsedLine]) -> set[str]:
    keys: set[str] = set()
    for line in lines:
        for token in re.findall(r"[\wāēīōūâêîôûĀĒĪŌŪÂÊÎÔÛ]+", line.bold_text):
            key = re.sub(r"[^a-z0-9]+", "", normalize(token))
            if len(key) >= 4:
                keys.add(key)
    return keys


def extract_proposal(row: dict) -> tuple[str, list[str], str]:
    lines = parse_comment(row.get("Comentario (es)") or row.get("Comentario") or "")
    primary: list[str] = []
    labeled: dict[str, list[str]] = {}
    fallback_examples: list[str] = []
    definition_snippets: list[str] = []
    fallback_snippets: list[str] = []
    current_marker: str | None = None
    awaiting_section_definition = False

    for line in lines:
        visible = line.text()
        small = line.small_text
        if small and visible == small:
            if "*~" in normalize(small):
                current_marker = section_marker(small)
                awaiting_section_definition = is_definition_section_marker(small)
            continue

        if is_letter_header(line):
            current_marker = None
            awaiting_section_definition = False
            continue

        definition = ""
        if starts_sense_marker(line):
            definition = definition_from_line(line)
            awaiting_section_definition = False
        elif awaiting_section_definition and current_marker != META_SECTION:
            definition = definition_from_line(line)
            awaiting_section_definition = False

        if definition:
            inline_label, definition = peel_inline_label(definition)
            target_marker = inline_label or current_marker
            if target_marker and target_marker != META_SECTION:
                labeled.setdefault(target_marker, []).append(definition)
            else:
                primary.append(definition)
            definition_snippets.append(visible)
            continue

        plain = clean_non_bold_text(line.text(include_bold=False, include_small=False))
        if not plain:
            continue

        if line.has_bold:
            glosses = extract_glosses(plain)
            if not glosses:
                continue
            fallback_examples.extend(glosses)
            fallback_snippets.append(visible)
            continue

        if current_marker == META_SECTION:
            glosses = extract_glosses(plain)
            if glosses:
                fallback_examples.extend(glosses)
                fallback_snippets.append(visible)
            continue

        if current_marker:
            glosses = extract_glosses(plain)
            if glosses:
                if current_marker == "plural":
                    glosses = [
                        clean_source_text(re.sub(r"\bhonor\.\s*", "", g, flags=re.IGNORECASE))
                        for g in glosses
                    ]
                    glosses = [g for g in glosses if g and normalize(g) not in {"honor", "plur", "plural"}]
                labeled.setdefault(current_marker, []).extend(glosses)
                definition_snippets.append(visible)
            continue

        if not primary:
            definition = definition_from_line(line)
            if definition:
                primary.append(definition)
                definition_snippets.append(visible)

    primary = dedupe(primary)
    fallback_examples = dedupe(fallback_examples)
    labeled = {label: dedupe(values) for label, values in labeled.items() if dedupe(values)}

    parts: list[str] = []
    if primary:
        parts.extend(ensure_period(item) for item in primary[:8])

    for label, values in sorted(labeled.items()):
        if label in {"metáfora", "parentesco", "plural"}:
            continue
        prefix = section_prefix(label)
        if not prefix or not values:
            continue
        phrase = join_glosses([lower_initial(value) for value in values[:4]])
        parts.append(ensure_period(f"{prefix}, {phrase}"))

    if not parts and fallback_examples:
        parts.append(ensure_period(join_glosses(fallback_examples[:4])))

    for label in ("metáfora", "parentesco", "plural"):
        values = labeled.get(label)
        if not values:
            continue
        parts.append(f"{label}: {join_glosses(values[:4])}.")

    proposal = " / ".join(parts)
    reason = classify_reason(row, proposal, bool(primary), bool(fallback_examples), bool(labeled))
    snippets = definition_snippets if parts and definition_snippets else fallback_snippets
    return proposal, snippets[:4], reason


def candidate_text_from_raw(raw: str, *, origin: str) -> str:
    text = compact_definition(raw)
    if origin in {"example", "form-plain", "meta-plain"}:
        text = genericize_possessive(text)
    if not text or is_bad_definition(text):
        return ""
    if text.startswith(("(", ")", ",", ";", ":")):
        return ""
    if word_count(text) > 36:
        return ""
    if NAHUATL_MARK_RE.search(text) or has_likely_nahuatl_word(text):
        return ""
    return sentence_case(text)


def feature_word_bucket(text: str) -> str:
    count = word_count(text)
    if count <= 2:
        return "words:1-2"
    if count <= 5:
        return "words:3-5"
    if count <= 10:
        return "words:6-10"
    if count <= 20:
        return "words:11-20"
    return "words:21+"


def make_candidate(
    line: ParsedLine,
    *,
    raw: str,
    origin: str,
    index: int,
    marker: str | None,
    role: str | None,
    role_label: str | None,
) -> Candidate | None:
    text = candidate_text_from_raw(raw, origin=origin)
    if not text:
        return None
    inline_label, text = peel_inline_label(text)
    label = inline_label or (marker if marker in KNOWN_LABELS else None)
    if label in {"parentesco", "plural"}:
        text = genericize_possessive(text)
        if label == "plural":
            text = re.sub(r"^\s*(?:relativo|pariente)\s*,\s*", "", text, flags=re.IGNORECASE)
        text = sentence_case(text)
    features = {
        f"origin:{origin}",
        f"marker:{marker or 'none'}",
        f"label:{label or 'none'}",
        f"role:{role or 'none'}",
        feature_word_bucket(text),
        "bold" if line.has_bold else "plain",
        "early" if index < 12 else "late",
    }
    if starts_sense_marker(line):
        features.add("sense-marker")
    if line.small_text:
        features.add("mixed-small")
    return Candidate(
        text=text,
        snippet=line.text(),
        origin=origin,
        index=index,
        label=label,
        marker=marker,
        role=role,
        role_label=role_label,
        features=features,
    )


def collect_candidates(row: dict) -> list[Candidate]:
    lines = parse_comment(row.get("Comentario (es)") or row.get("Comentario") or "")
    candidates: list[Candidate] = []
    current_marker: str | None = None
    current_role: str | None = None
    current_role_label: str | None = None
    current_numbered_role: str | None = None
    current_numbered_role_label: str | None = None
    in_numbered_sense = False
    awaiting_section_definition = False

    for index, line in enumerate(lines):
        visible = line.text()
        small = line.small_text
        if small and visible == small:
            if "*~" in normalize(small):
                current_marker = section_marker(small)
                current_role = section_role(small)
                current_role_label = section_role_label(small)
                awaiting_section_definition = is_definition_section_marker(small)
                current_numbered_role = None
                current_numbered_role_label = None
                in_numbered_sense = False
            continue

        if is_letter_header(line):
            current_marker = None
            current_role = None
            current_role_label = None
            current_numbered_role = None
            current_numbered_role_label = None
            in_numbered_sense = False
            awaiting_section_definition = False
            continue

        line_role, line_role_label = inline_role_context(line)
        if starts_sense_marker(line):
            origin = "numbered"
            current_numbered_role = line_role or current_role
            current_numbered_role_label = line_role_label or current_role_label
            in_numbered_sense = True
        elif awaiting_section_definition and current_marker != META_SECTION:
            origin = "section-head"
            in_numbered_sense = False
        elif line.has_bold:
            origin = "example"
        elif current_marker == META_SECTION:
            origin = "form-plain"
        elif current_marker:
            origin = "section-plain"
        elif in_numbered_sense:
            origin = "numbered-support"
        else:
            origin = "plain"

        raw = line.text(include_bold=False, include_small=False)
        if not raw and starts_sense_marker(line):
            raw = line.text(include_small=False)
        candidate_role = line_role or current_role
        candidate_role_label = line_role_label or current_role_label
        if origin == "numbered-support":
            candidate_role = current_numbered_role
            candidate_role_label = current_numbered_role_label
        candidate = make_candidate(
            line,
            raw=raw,
            origin=origin,
            index=index,
            marker=current_marker,
            role=candidate_role,
            role_label=candidate_role_label,
        )
        if candidate:
            candidates.append(candidate)

        if awaiting_section_definition:
            awaiting_section_definition = False

    return dedupe_candidates(candidates)


def dedupe_candidates(candidates: list[Candidate]) -> list[Candidate]:
    seen: set[str] = set()
    out: list[Candidate] = []
    for candidate in candidates:
        key = normalize(candidate.text).strip(" .;,:")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    return out


def build_corpus_model(rows: list[dict]) -> dict[str, tuple[float, int]]:
    stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in rows:
        old_segments = translation_segments(row.get("Traducción (es)") or row.get("Traducción") or "")
        if not old_segments:
            continue
        for candidate in collect_candidates(row):
            score = best_old_score(candidate.text, old_segments)
            positive = score >= 0.58 or (score >= 0.42 and word_count(candidate.text) <= 5)
            for feature in candidate.features:
                stats[feature][1] += 1
                if positive:
                    stats[feature][0] += 1
    return {
        feature: ((positive + 1) / (total + 2), total)
        for feature, (positive, total) in stats.items()
    }


def corpus_confidence(candidate: Candidate, model: dict[str, tuple[float, int]]) -> float:
    weighted: list[tuple[float, int]] = []
    for feature in candidate.features:
        rate, total = model.get(feature, (0.0, 0))
        if total >= 25:
            weighted.append((rate, total))
    if not weighted:
        return 0.0
    weighted.sort(reverse=True)
    best = weighted[:4]
    return sum(rate * min(total, 1000) for rate, total in best) / sum(min(total, 1000) for _, total in best)


def candidate_rank(candidate: Candidate) -> float:
    return (candidate.old_score * 0.78) + (candidate.corpus_score * 0.22)


def same_candidate_family(left: Candidate, right: Candidate) -> bool:
    if left.label != right.label:
        return False
    if left.label is None and right.label is None and left.role != right.role:
        return False
    if left.marker != right.marker and left.label is None and right.label is None:
        return False
    if left.origin == right.origin:
        return True
    definition_origins = {"numbered", "section-head", "plain", "section-plain"}
    if left.origin in definition_origins and right.origin in definition_origins:
        return True
    return left.label is not None


def better_redundant_candidate(left: Candidate, right: Candidate) -> Candidate:
    left_rank = candidate_rank(left)
    right_rank = candidate_rank(right)
    if abs(left_rank - right_rank) > 0.04:
        return left if left_rank > right_rank else right
    left_words = word_count(left.text)
    right_words = word_count(right.text)
    if left_words != right_words:
        return left if left_words > right_words else right
    return left if left.index <= right.index else right


def label_mentions_in_old(old_segments: list[str]) -> dict[str, list[str]]:
    mentioned: dict[str, list[str]] = {}
    aliases = {
        "botánica": ("botanica", "botanico", "botanica medicinal"),
        "calendario": ("calendario",),
        "expresión": ("expresion",),
        "metáfora": ("metafora", "metaforico", "metaph"),
        "ornitología": ("ornitologia",),
        "parentesco": ("parentesco", "pariente"),
        "plural": ("plural", "plur"),
        "ritual": ("ritual",),
        "topónimo": ("toponimo", "topon"),
    }
    for segment in old_segments:
        normalized = normalize(segment)
        for label, keys in aliases.items():
            if any(re.search(rf"\b{re.escape(key)}\b", normalized) for key in keys):
                mentioned.setdefault(label, []).append(segment)
    return mentioned


def object_contrast_signature(value: str) -> set[str]:
    normalized = normalize(value)
    signature: set[str] = set()
    if re.search(r"\b(?:algo|cosa|cosas|objeto|objetos)\b", normalized):
        signature.add("thing")
    if re.search(
        r"\b(?:a|al|a\s+la|a\s+las|a\s+los)\s+(?:alguien|otra?s?\s+personas?|una?s?\s+personas?)\b"
        r"|\bhacer\s+que\s+(?:alguien|una?s?\s+personas?)\b",
        normalized,
    ):
        signature.add("person")
    return signature


def preserves_numbered_object_contrast(left: Candidate, right: Candidate) -> bool:
    if left.origin != "numbered" or right.origin != "numbered":
        return False
    left_signature = object_contrast_signature(left.text)
    right_signature = object_contrast_signature(right.text)
    return bool(left_signature and right_signature and left_signature != right_signature)


def prune_redundant_candidates(candidates: list[Candidate]) -> list[Candidate]:
    kept: list[Candidate] = []
    for candidate in sorted(candidates, key=lambda c: (-candidate_rank(c), c.index)):
        candidate_tokens = content_tokens(candidate.text)
        if not candidate_tokens:
            continue
        replacement: tuple[int, Candidate] | None = None
        redundant = False
        for index, kept_candidate in enumerate(kept):
            kept_tokens = content_tokens(kept_candidate.text)
            if not kept_tokens:
                continue
            short_duplicate = (
                candidate.label == kept_candidate.label
                and candidate.role == kept_candidate.role
                and min(word_count(candidate.text), word_count(kept_candidate.text)) <= 2
                and (candidate_tokens <= kept_tokens or kept_tokens <= candidate_tokens)
            )
            if not short_duplicate and not same_candidate_family(candidate, kept_candidate):
                meta_overlap = (
                    {candidate.marker, kept_candidate.marker} == {META_SECTION, None}
                    and overlap_score(candidate.text, kept_candidate.text) >= 0.34
                )
                if not meta_overlap:
                    continue
                if candidate.marker == META_SECTION:
                    redundant = True
                    break
                replacement = (index, candidate)
                redundant = True
                break
            if preserves_numbered_object_contrast(candidate, kept_candidate):
                continue
            overlap = overlap_score(candidate.text, kept_candidate.text)
            if candidate_tokens <= kept_tokens or overlap >= 0.80:
                winner = better_redundant_candidate(candidate, kept_candidate)
                if winner is kept_candidate:
                    redundant = True
                    break
                replacement = (index, candidate)
                redundant = True
                break
            if kept_tokens <= candidate_tokens:
                replacement = (index, candidate)
                redundant = True
                break
        if replacement:
            kept[replacement[0]] = replacement[1]
        elif not redundant:
            kept.append(candidate)
    return sorted(kept, key=lambda c: c.index)


def select_corpus_candidates(row: dict, model: dict[str, tuple[float, int]]) -> list[Candidate]:
    candidates = collect_candidates(row)
    old = row.get("Traducción (es)") or row.get("Traducción") or ""
    old_segments = translation_segments(old)
    selected: dict[str, Candidate] = {}

    for candidate in candidates:
        candidate.old_score = best_old_score(candidate.text, old_segments)
        candidate.corpus_score = corpus_confidence(candidate, model)

    for segment in old_segments:
        best: Candidate | None = None
        best_score = 0.0
        for candidate in candidates:
            if candidate.origin == "numbered-support":
                continue
            seg_score = overlap_score(candidate.text, segment)
            combined = (seg_score * 0.82) + (candidate.corpus_score * 0.18)
            if combined > best_score:
                best = candidate
                best_score = combined
        if best and (best_score >= 0.50 or (best.old_score >= 0.38 and best.corpus_score >= 0.56)):
            selected[normalize(best.text)] = best

    for label, segments in label_mentions_in_old(old_segments).items():
        if label == "expresión":
            continue
        label_candidates = [candidate for candidate in candidates if candidate.label == label]
        if not label_candidates:
            continue
        best = None
        best_score = 0.0
        for candidate in label_candidates:
            segment_score = max((overlap_score(candidate.text, segment) for segment in segments), default=0.0)
            origin_bonus = 0.12 if candidate.origin in {"section-head", "section-plain"} else 0.0
            brevity_bonus = 0.08 if word_count(candidate.text) <= 8 else 0.0
            source_label_bonus = 0.0
            if label == "plural" and word_count(candidate.text) <= 4 and "plural" in normalize(candidate.snippet):
                source_label_bonus = 0.12
            score = (
                (segment_score * 0.62)
                + (candidate.corpus_score * 0.18)
                + origin_bonus
                + brevity_bonus
                + source_label_bonus
            )
            if score > best_score:
                best = candidate
                best_score = score
        label_threshold = 0.16 if label in {"metáfora", "parentesco", "plural"} else 0.24
        if best and (best_score >= label_threshold or best.origin in {"section-head", "section-plain"}):
            selected[normalize(best.text)] = best

    old_bad = contamination_score(row) >= 4 or is_bad_definition(old)
    old_short = word_count(old) <= 4
    needs_global_fallback = old_short or len(old_segments) <= 2 or not selected
    for candidate in candidates:
        if candidate.origin == "numbered-support":
            continue
        reliable = candidate.corpus_score >= 0.58 and candidate.origin in {
            "numbered", "section-head", "plain", "section-plain"
        }
        if candidate.old_score >= 0.58 or (candidate.old_score >= 0.40 and candidate.corpus_score >= 0.50):
            selected[normalize(candidate.text)] = candidate
        elif old_bad and needs_global_fallback and reliable and candidate.index < 80:
            selected[normalize(candidate.text)] = candidate

    limit = min(14, max(6, len(old_segments) + 2))
    pruned = prune_redundant_candidates(list(selected.values()))
    ranked = sorted(pruned, key=lambda c: (-candidate_rank(c), c.index))[:limit]
    return sorted(ranked, key=lambda c: c.index)


def proposal_from_candidates(candidates: list[Candidate]) -> str:
    primary: list[str] = []
    labeled: dict[str, list[str]] = {}
    label_order: list[str] = []
    for candidate in candidates:
        if candidate.label in KNOWN_LABELS:
            if candidate.label not in labeled:
                label_order.append(candidate.label)
            labeled.setdefault(candidate.label, []).append(candidate.text)
        elif candidate.role_label:
            marker = reconciled_role_label(candidate.role_label, candidate.text)
            primary.append(f"{marker}., {lower_initial(candidate.text)}")
        elif candidate.role:
            marker = GRAMMAR_ROLE_FALLBACKS.get(normalize(candidate.role))
            if marker:
                marker = reconciled_role_label(marker, candidate.text) or marker
                primary.append(f"{marker}., {lower_initial(candidate.text)}")
            else:
                primary.append(f"{candidate.role}: {lower_initial(candidate.text)}")
        else:
            primary.append(candidate.text)

    parts = [ensure_period(text) for text in dedupe(primary)]
    for label in label_order:
        values = dedupe(labeled.get(label, []))
        if not values:
            continue
        phrase = join_glosses([sentence_case(value) for value in values])
        parts.append(ensure_period(f"{label}: {phrase}"))
    return " / ".join(parts)


def extract_corpus_proposal(row: dict, model: dict[str, tuple[float, int]]) -> tuple[str, list[str], str]:
    selected = select_corpus_candidates(row, model)
    proposal = proposal_from_candidates(selected)
    snippets = [candidate.snippet for candidate in selected[:4]]
    if not proposal:
        return extract_proposal(row)
    reason = classify_reason(
        row,
        proposal,
        any(candidate.origin != "example" for candidate in selected),
        any(candidate.origin == "example" for candidate in selected),
        any(candidate.label for candidate in selected),
    )
    return proposal, snippets, f"corpus-{reason}"


def contains_bold_form(value: str, keys: set[str]) -> bool:
    words = [re.sub(r"[^a-z0-9]+", "", normalize(t)) for t in WORD_RE.findall(value or "")]
    return any(word in keys for word in words if len(word) >= 4)


def has_citation(value: str) -> bool:
    return bool(CITATION_RE.search(value or ""))


def strip_output_labels(value: str) -> str:
    return " / ".join(re.sub(OUTPUT_LABEL_RE, "", part).strip() for part in re.split(r"\s*/\s*", value or ""))


def validate_proposal(row: dict, proposal: str) -> list[str]:
    errors: list[str] = []
    lines = parse_comment(row.get("Comentario (es)") or row.get("Comentario") or "")
    if not proposal:
        errors.append("empty")
        return errors
    if "<" in proposal or ">" in proposal:
        errors.append("html")
    if has_citation(proposal):
        errors.append("citation")
    proposal_check = strip_output_labels(proposal)
    if NAHUATL_MARK_RE.search(proposal_check):
        errors.append("nahuatl-diacritic")
    if has_likely_nahuatl_word(proposal_check):
        errors.append("likely-nahuatl-word")
    if contains_bold_form(proposal, bold_keys(lines)):
        errors.append("bold-form-leak")
    lemma_key = re.sub(r"[^a-z0-9]+", "", normalize(row.get("Texto estandarizado") or ""))
    proposal_words = [re.sub(r"[^a-z0-9]+", "", normalize(t)) for t in WORD_RE.findall(proposal)]
    if lemma_key and lemma_key in proposal_words:
        errors.append("lemma-leak")
    if is_bad_definition(proposal_check):
        errors.append("not-a-definition")
    for part in re.split(r"\s*/\s*|\s*;\s*", proposal):
        part = re.sub(OUTPUT_LABEL_RE, "", part)
        part_check = re.sub(
            r"^\s*(?:bot[aá]nica|calendario|expresi[oó]n|met[aá]fora|ornitolog[ií]a|parentesco|plural|ritual|top[oó]nimo)\s*:\s*",
            "",
            part,
            flags=re.IGNORECASE,
        )
        if is_bad_definition(part_check):
            errors.append("bad-part")
            break
    if word_count(proposal) < 1:
        errors.append("too-short")
    return errors


def contamination_score(row: dict) -> int:
    old = row.get("Traducción (es)") or row.get("Traducción") or ""
    score = 0
    if NAHUATL_MARK_RE.search(old):
        score += 4
    if is_bad_definition(old):
        score += 4
    if has_citation(old):
        score += 1
    lemma_key = re.sub(r"[^a-z0-9]+", "", normalize(row.get("Texto estandarizado") or ""))
    old_key = re.sub(r"[^a-z0-9]+", "", normalize(old))
    old_word_keys = {re.sub(r"[^a-z0-9]+", "", normalize(t)) for t in WORD_RE.findall(old)}
    if len(lemma_key) >= 4 and (lemma_key in old_word_keys or (NAHUATL_MARK_RE.search(old) and lemma_key[: min(8, len(lemma_key))] in old_key)):
        score += 3
    return score


def classify_reason(row: dict, proposal: str, has_primary: bool, has_fallback: bool, has_labeled: bool) -> str:
    old = row.get("Traducción (es)") or row.get("Traducción") or ""
    if is_bad_definition(old) and has_fallback and not has_primary and not has_labeled:
        return "possessed-only"
    if contamination_score(row) >= 4:
        return "short-leaky"
    if has_labeled:
        return "comment-senses"
    if has_primary and word_count(old) <= 3:
        return "short-definition"
    return "comment-cleanup"


def changed(old: str, proposal: str) -> bool:
    def key(value: str) -> str:
        return re.sub(r"\s+", " ", normalize(value).replace("/", " ")).strip(" .;,:")

    return key(old) != key(proposal)


def sort_key_for_order(row: dict, order: str) -> tuple:
    if order == "longest-translation":
        return (
            -row["old_word_count"],
            -row["comment_word_count"],
            -row["contamination_score"],
            row["lemma"],
            row["record_id"],
        )
    if order == "longest-comment":
        return (
            -row["comment_word_count"],
            -row["old_word_count"],
            -row["contamination_score"],
            row["lemma"],
            row["record_id"],
        )
    return (
        row["old_word_count"],
        -row["contamination_score"],
        0 if row["anchor"] else 1,
        row["lemma"],
        row["record_id"],
    )


def build_candidates(limit: int, order: str = "shortest-risk") -> list[dict]:
    rows: list[dict] = []
    source_rows: list[dict] = []
    with gzip.open(DATA, "rt", encoding="utf-8") as fin:
        for line in fin:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("Fuente") != "2021 Wimmer":
                continue
            source_rows.append(row)

    model = build_corpus_model(source_rows)

    for row in source_rows:
        proposal, snippets, reason = extract_corpus_proposal(row, model)
        old = row.get("Traducción (es)") or row.get("Traducción") or ""
        old_risk = contamination_score(row)
        is_anchor = normalize(row.get("Texto estandarizado", "")) in ANCHOR_LEMMAS
        if order == "shortest-risk" and old_risk <= 0 and not is_anchor:
            continue
        errors = validate_proposal(row, proposal)
        if errors or not changed(old, proposal):
            continue
        rows.append(
            {
                "record_id": row.get("record_id", ""),
                "eid": row.get("eid", ""),
                "lemma": row.get("Texto estandarizado", ""),
                "old_translation_es": old,
                "proposed_translation_es": proposal,
                "source_snippets": snippets,
                "reason": reason,
                "old_word_count": word_count(old),
                "comment_word_count": source_word_count(row.get("Comentario (es)") or row.get("Comentario") or ""),
                "contamination_score": old_risk,
                "anchor": is_anchor,
            }
        )

    rows.sort(key=lambda r: sort_key_for_order(r, order))

    if order == "shortest-risk":
        anchors = [r for r in rows if r["anchor"]]
        anchor_ids = {r["record_id"] for r in anchors}
        selected = anchors[:limit]
        for row in rows:
            if len(selected) >= limit:
                break
            if row["record_id"] in anchor_ids:
                continue
            selected.append(row)
    else:
        selected = rows[:limit]

    selected.sort(key=lambda r: sort_key_for_order(r, order))
    return selected[:limit]


def output_paths(order: str, out_prefix: str | None = None) -> tuple[Path, Path]:
    if out_prefix:
        base = Path(out_prefix)
        if not base.is_absolute():
            base = ROOT / base
        return base.with_suffix(".jsonl"), base.with_suffix(".txt")
    if order == "longest-translation":
        base = ROOT / "scripts" / "wimmer_translation_pilot_longest_translation_review"
        return base.with_suffix(".jsonl"), base.with_suffix(".txt")
    if order == "longest-comment":
        base = ROOT / "scripts" / "wimmer_translation_pilot_longest_comment_review"
        return base.with_suffix(".jsonl"), base.with_suffix(".txt")
    return OUT_JSONL, OUT_TXT


def write_outputs(rows: list[dict], order: str, out_jsonl: Path, out_txt: Path) -> None:
    with out_jsonl.open("w", encoding="utf-8") as fout:
        for row in rows:
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")

    lines = [
        f"# 2021 Wimmer Traducción (es) Pilot Review — {order}",
        "# Review-only output. This file does not patch data/data.jsonl.gz.",
        "# Fields: old translation, proposed translation, reason, source snippets.",
        "",
    ]
    sep = "═" * 80
    for idx, row in enumerate(rows, 1):
        lines.append(sep)
        lines.append(f"{idx:02d}. {row['lemma']}  [{row['record_id']}]")
        lines.append(
            f"REASON : {row['reason']}  tr_wc={row['old_word_count']}  "
            f"com_wc={row['comment_word_count']}  risk={row['contamination_score']}"
        )
        lines.append(f"OLD    : {row['old_translation_es']}")
        lines.append(f"NEW    : {row['proposed_translation_es']}")
        for snippet in row["source_snippets"]:
            lines.append(f"SOURCE : {snippet}")
        lines.append("")
    lines.append(sep)
    out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a 2021 Wimmer Spanish translation review pilot.")
    parser.add_argument("--limit", type=int, default=25, help="number of review rows to emit")
    parser.add_argument(
        "--order",
        choices=("shortest-risk", "longest-translation", "longest-comment"),
        default="shortest-risk",
        help="candidate ordering for the review batch",
    )
    parser.add_argument("--out-prefix", help="optional output path prefix without extension")
    args = parser.parse_args()

    rows = build_candidates(args.limit, args.order)
    out_jsonl, out_txt = output_paths(args.order, args.out_prefix)
    write_outputs(rows, args.order, out_jsonl, out_txt)
    anchors = ", ".join(r["lemma"] for r in rows if r["anchor"]) or "none"
    print(f"wrote {out_jsonl.relative_to(ROOT)}")
    print(f"wrote {out_txt.relative_to(ROOT)}")
    print(f"rows={len(rows)} anchors={anchors}")


if __name__ == "__main__":
    main()
