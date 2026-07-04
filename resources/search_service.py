#!/usr/bin/env python3
"""SQLite FTS5 backend search service.

This is the recommended run path for very large/mobile deployments. It builds
a local SQLite database from data/data.jsonl.gz, uses FTS5 trigram indexes to
narrow candidate rows, verifies matches server-side, and returns only the
requested page rows.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import heapq
import html
import io
import json
import random
import re
import sqlite3
import sys
import unicodedata
from functools import cmp_to_key
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
DB_PATH = ROOT / "data" / "search.sqlite"
BACKEND_ID = "sqlite-fts5"
API_CONTRACT_VERSION = "backend-api-v1"
SEARCH_API_PATH = "/api/search"
API_POST_ENDPOINTS = ("/api/search", "/api/lemma", "/api/pairs", "/api/study", "/api/export")
API_ENDPOINTS = (*API_POST_ENDPOINTS, "/api/sources")
NO_STORE_STATIC_PATHS = {"data/data.jsonl.gz", "search-worker.js"}
NO_STORE_STATIC_PREFIXES = ("data/lazy/",)
DISPLAY_FIELDS = ("Editado", "Original", "Traducción", "Comentario")
LAYERED_FIELDS = {"Traducción", "Comentario", "Traducción (es)", "Comentario (es)"}
SEARCH_FIELDS = {"Editado", "Original", "Traducción", "Comentario", "Fuente"}
FIELD_CODE_IN = {
    "ed": "Editado",
    "te": "Editado",
    "or": "Original",
    "eo": "Original",
    "tr": "Traducción",
    "co": "Comentario",
    "fu": "Fuente",
}
MODE_CODE_IN = {"e": "exact", "s": "starts", "a": "any", "d": "ends"}
SCOPE_CODE_IN = {"t": "whole", "c": "whole", "w": "word", "p": "phrase", "m": "wordPhrase"}
FTS_COLUMNS = {
    ("Editado", "normalized"): "editado",
    ("Original", "normalized"): "original",
    ("Traducción", "normalized"): "traduccion",
    ("Traducción", "source"): "traduccion_source",
    ("Comentario", "normalized"): "comentario",
    ("Comentario", "source"): "comentario_source",
}
RAW_LAYER_PREFIXES = {
    "Traducción": ("Traducción_raw", "Traduccion_raw"),
    "Comentario": (
        "Comentario_public_raw",
        "Comentario_wimmer_plus_html_raw",
        "Sahagun_Escolios_JSON_display_html_raw",
        "Comentario_raw",
    ),
}
PUBLIC_ROW_FIELDS = {
    "record_id",
    "eid",
    "prio",
    "Fuente",
    "Editado",
    "Original",
    "Traducción",
    "Traducción (es)",
    "Comentario",
    "Comentario (es)",
}
PUBLIC_RAW_PREFIXES = (
    "Traducción_raw",
    "Traduccion_raw",
    "Traducción_es_raw",
    "Traduccion_es_raw",
    "Comentario_raw",
    "Comentario_public_raw",
    "Comentario_wimmer_plus_html_raw",
    "Comentario_es_raw",
    "Sahagun_Escolios_JSON_display_html_raw",
)
PUBLIC_RAW_PREFIXES_BY_FIELD = {
    "Traducción": ("Traducción_raw", "Traduccion_raw"),
    "Traducción (es)": ("Traducción_es_raw", "Traduccion_es_raw", "Traducción_raw", "Traduccion_raw"),
    "Comentario": (
        "Comentario_public_raw",
        "Comentario_wimmer_plus_html_raw",
        "Sahagun_Escolios_JSON_display_html_raw",
        "Comentario_raw",
    ),
    "Comentario (es)": (
        "Comentario_es_raw",
        "Comentario_public_raw",
        "Comentario_wimmer_plus_html_raw",
        "Sahagun_Escolios_JSON_display_html_raw",
        "Comentario_raw",
    ),
}
WORD_RE = re.compile(r"[0-9A-Za-zÀ-ɏḀ-ỿ]+")
LETTER_PATTERN = r"[A-Za-zÀ-ɏḀ-ỿ]"
NAHUATL_GRAPHEME_DIGRAPHS = ("ch", "tz", "hu", "uh", "qu", "cu", "uc", "ll", "rr", "gu")
NAHUATL_GRAPHEME_PATTERN = (
    r"(?:" + "|".join(NAHUATL_GRAPHEME_DIGRAPHS) + r"|(?!"
    + "|".join(NAHUATL_GRAPHEME_DIGRAPHS) + r")" + LETTER_PATTERN + r")"
)
NAHUATL_GRAPHEME_FIELDS = {"Editado", "Original", "Comentario"}
PLACEHOLDER_PATTERNS = {
    "c": r"(?:ch|tz|hu|uh|qu|cu|uc|ll|rr|gu|[bcdfghjklmnñpqrstvwxyz])",
    "v": r"[aeiouaāeēiīoōu]",
    "n": r"(?:m|n|ñ)",
    "l": r"(?:l|ll|r|rr)",
    "s": r"(?:tz|s|z|x)",
    "g": r"(?:hu|uh|y|w)",
    "p": r"(?:ch|tz|qu|cu|uc|p|t|c|b|d|g|k)",
    "a": LETTER_PATTERN,
}
REGEX_META_CHARS = set("\\.^$*+?{}[]()|")
REDUPLICATION_VOWELS = re.compile(r"[aeiouáéíóúüāēīōū]", re.IGNORECASE)
REDUPLICATION_MARKER_RE = re.compile(r"\{[Rr]([1-9]\d*(?:-\d*)?)?\}")
REDUPLICATION_GROUP_COUNTER = 0


def strip_html_tags(value: str) -> str:
    return re.sub(r"<[^>]*>", " ", html.unescape(str(value or "")))


def normalize_string(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", strip_html_tags(value).lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_with_accents(value: str) -> str:
    return unicodedata.normalize("NFC", strip_html_tags(value).lower())


def normalize_old_spanish(value: str) -> str:
    return (
        value
        .replace("ph", "f")
        .replace("th", "t")
        .replace("qu", "c")
        .replace("nn", "n")
        .replace("ss", "s")
        .replace("x", "j")
        .replace("v", "b")
    )


def normalize_old_spanish_pattern_text(value: str) -> str:
    if not value:
        return ""
    out: list[str] = []
    literal: list[str] = []
    escaped = False
    in_class = False
    in_brace = False

    def flush_literal() -> None:
        if not literal:
            return
        out.append(normalize_old_spanish(normalize_string("".join(literal))))
        literal.clear()

    for ch in str(value):
        if escaped:
            literal.append(ch)
            escaped = False
            continue
        if ch == "\\":
            literal.append(ch)
            escaped = True
            continue
        if in_class:
            out.append(ch)
            if ch == "]":
                in_class = False
            continue
        if in_brace:
            out.append(ch)
            if ch == "}":
                in_brace = False
            continue
        if ch == "[":
            flush_literal()
            out.append(ch)
            in_class = True
            continue
        if ch == "{":
            flush_literal()
            out.append(ch)
            in_brace = True
            continue
        literal.append(ch)
    flush_literal()
    return "".join(out)


def normalize_for_search(value: str, accent_sensitive: bool = False, old_spanish: bool = False) -> str:
    if accent_sensitive:
        return normalize_with_accents(value)
    normalized = normalize_string(value)
    return normalize_old_spanish(normalized) if old_spanish else normalized


def normalize_query_source(value: str, accent_sensitive: bool = False, old_spanish: bool = False) -> str:
    if accent_sensitive:
        return normalize_with_accents(value)
    if old_spanish:
        return normalize_old_spanish_pattern_text(value)
    return normalize_string(value)


def collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def strip_punctuation_characters(value: str) -> str:
    return re.sub(r"[^\w\sÀ-ɏḀ-ỿ]", " ", value, flags=re.UNICODE)


def has_formatting_characters(value: str) -> bool:
    return bool(re.search(r"[^\w\sÀ-ɏḀ-ỿ]", value or "", flags=re.UNICODE))


def display_base_field(row: dict[str, Any], field: str) -> str:
    if row.get("Fuente") == "2021 Wimmer":
        if field == "Traducción" and row.get("Traducción (es)"):
            return "Traducción (es)"
        if field == "Comentario" and row.get("Comentario (es)"):
            return "Comentario (es)"
    return field


def normalized_display_value(row: dict[str, Any], field: str) -> str:
    base = display_base_field(row, field)
    value = row.get(base)
    if value is None:
        value = row.get(field, "")
    return "" if value is None else str(value)


def source_raw_value(row: dict[str, Any], field: str) -> str:
    prefixes = RAW_LAYER_PREFIXES.get(field, ())
    candidates: list[tuple[int, int, str]] = []
    for key in row:
        for rank, prefix in enumerate(prefixes):
            if key.startswith(prefix):
                candidates.append((rank, len(key), key))
                break
    for _rank, _length, key in sorted(candidates):
        value = row.get(key)
        if value is None or isinstance(value, (dict, list)):
            continue
        text = str(value)
        if text.strip():
            return text
    return ""


def source_display_value(row: dict[str, Any], field: str) -> str:
    if field not in RAW_LAYER_PREFIXES:
        return normalized_display_value(row, field)
    raw = source_raw_value(row, field)
    return raw if raw.strip() else normalized_display_value(row, field)


def layer_values(row: dict[str, Any], field: str, layer: str = "both") -> list[str]:
    if field == "Fuente":
        return [str(row.get("Fuente", ""))]
    if field not in LAYERED_FIELDS:
        return [normalized_display_value(row, field)]
    values = []
    if layer in ("both", "normalized"):
        values.append(normalized_display_value(row, field))
    if layer in ("both", "source"):
        values.append(source_display_value(row, field))
    return values or [normalized_display_value(row, field)]


def first_public_raw_key(row: dict[str, Any], prefixes: tuple[str, ...]) -> str | None:
    candidates: list[tuple[int, int, tuple[tuple[int, Any], ...], str]] = []
    for key, value in row.items():
        if value is None or isinstance(value, (dict, list)) or not str(value).strip():
            continue
        for rank, prefix in enumerate(prefixes):
            if key.startswith(prefix):
                candidates.append((rank, len(key), natural_key(key), key))
                break
    if not candidates:
        return None
    return sorted(candidates)[0][3]


def public_row_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        key: value
        for key, value in row.items()
        if key in PUBLIC_ROW_FIELDS
    }
    for prefixes in PUBLIC_RAW_PREFIXES_BY_FIELD.values():
        key = first_public_raw_key(row, prefixes)
        if key:
            payload[key] = row[key]
    return payload


def public_rows_payload(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [public_row_payload(row) for row in rows]


def row_record_id(row: dict[str, Any], idx: int) -> str:
    return str(row.get("record_id") or f"row:{idx:06d}")


def parse_priority(value: Any) -> float:
    try:
        if value in (None, ""):
            return float("inf")
        return float(value)
    except (TypeError, ValueError):
        return float("inf")


def build_database(data_path: Path = DATA_PATH, db_path: Path = DB_PATH) -> int:
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("PRAGMA temp_store=MEMORY")
    con.executescript(
        """
        CREATE TABLE rows (
          id INTEGER PRIMARY KEY,
          record_id TEXT NOT NULL UNIQUE,
          fuente TEXT NOT NULL,
          editado TEXT NOT NULL,
          original TEXT NOT NULL,
          traduccion TEXT NOT NULL,
          traduccion_source TEXT NOT NULL,
          comentario TEXT NOT NULL,
          comentario_source TEXT NOT NULL,
          prio REAL,
          row_json TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE search_fts USING fts5(
          editado,
          original,
          traduccion,
          traduccion_source,
          comentario,
          comentario_source,
          content='rows',
          content_rowid='id',
          tokenize='trigram'
        );
        CREATE INDEX rows_fuente_idx ON rows(fuente);
        CREATE INDEX rows_prio_idx ON rows(prio, editado, fuente, record_id);
        """
    )

    row_batch = []
    fts_batch = []
    count = 0
    with gzip.open(data_path, "rt", encoding="utf-8") as handle:
        for count, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            rid = row_record_id(row, count)
            editado = normalized_display_value(row, "Editado")
            original = normalized_display_value(row, "Original")
            traduccion = normalized_display_value(row, "Traducción")
            traduccion_source = source_display_value(row, "Traducción")
            comentario = normalized_display_value(row, "Comentario")
            comentario_source = source_display_value(row, "Comentario")
            row_batch.append(
                (
                    count,
                    rid,
                    str(row.get("Fuente", "")),
                    editado,
                    original,
                    traduccion,
                    traduccion_source,
                    comentario,
                    comentario_source,
                    parse_priority(row.get("prio")),
                    json.dumps(row, ensure_ascii=False, separators=(",", ":")),
                )
            )
            fts_batch.append((count, editado, original, traduccion, traduccion_source, comentario, comentario_source))
            if len(row_batch) >= 5000:
                insert_batches(con, row_batch, fts_batch)
                row_batch.clear()
                fts_batch.clear()
    if row_batch:
        insert_batches(con, row_batch, fts_batch)
    con.execute("INSERT INTO search_fts(search_fts) VALUES('optimize')")
    con.commit()
    con.close()
    return count


def insert_batches(con: sqlite3.Connection, rows: list[tuple[Any, ...]], fts_rows: list[tuple[Any, ...]]) -> None:
    con.executemany(
        """
        INSERT INTO rows (
          id, record_id, fuente, editado, original, traduccion, traduccion_source,
          comentario, comentario_source, prio, row_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    con.executemany(
        """
        INSERT INTO search_fts(
          rowid, editado, original, traduccion, traduccion_source, comentario, comentario_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        fts_rows,
    )
    con.commit()


def decode_filter_value(value: str) -> str:
    try:
        return unquote(value)
    except Exception:
        return value


def parse_group_spec(spec: str) -> list[dict[str, Any]]:
    if not spec:
        return []
    parts = spec.split(":")
    if len(parts) < 4:
        return []
    logic = "OR" if parts[0] == "O" else "AND"
    field = FIELD_CODE_IN.get(parts[1])
    scope = SCOPE_CODE_IN.get(parts[2], "whole")
    if not field:
        return []
    inputs_str = ":".join(parts[3:])
    filters = []
    for input_spec in inputs_str.split("|"):
        parsed = parse_input_spec(input_spec, scope)
        if not parsed:
            continue
        parsed.update({"field": field, "logic": logic})
        filters.append(parsed)
    return filters


def parse_input_spec(spec: str, default_scope: str) -> dict[str, Any] | None:
    parts = spec.split(":")
    if len(parts) < 3:
        return None
    mode = MODE_CODE_IN.get(parts[0])
    if not mode:
        return None
    negate = parts[1] == "1"
    scope = default_scope
    value_start = 2
    if len(parts) >= 4 and parts[2] in SCOPE_CODE_IN:
        scope = SCOPE_CODE_IN[parts[2]]
        value_start = 3
    value = decode_filter_value(":".join(parts[value_start:])).strip()
    if not value:
        return None
    return {"mode": mode, "negate": negate, "scope": scope, "value": value}


def filters_from_get_params(params: dict[str, list[str]]) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = []
    for group in params.get("g", [""])[0].split(";"):
        filters.extend(parse_group_spec(group))
    if filters:
        return filters
    field = params.get("field", ["Editado"])[0]
    value = params.get("q", [""])[0].strip()
    if value:
        filters.append(
            {
                "field": FIELD_CODE_IN.get(field, field),
                "mode": params.get("mode", ["any"])[0],
                "scope": params.get("scope", ["word"])[0],
                "value": value,
                "logic": "AND",
                "negate": False,
            }
        )
    return filters


def is_escaped_at(value: str, idx: int) -> bool:
    slash_count = 0
    pos = idx - 1
    while pos >= 0 and value[pos] == "\\":
        slash_count += 1
        pos -= 1
    return slash_count % 2 == 1


def split_top_level(value: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    brace_depth = 0
    in_class = False
    in_quote = False
    escaped = False
    idx = 0
    while idx < len(value):
        ch = value[idx]
        if escaped:
            buf.append(ch)
            escaped = False
            idx += 1
            continue
        if ch == "\\":
            buf.append(ch)
            escaped = True
            idx += 1
            continue
        if ch == '"':
            in_quote = not in_quote
            buf.append(ch)
            idx += 1
            continue
        if in_quote:
            buf.append(ch)
            idx += 1
            continue
        if in_class:
            if ch == "]":
                in_class = False
            buf.append(ch)
            idx += 1
            continue
        if ch == "[":
            in_class = True
            buf.append(ch)
            idx += 1
            continue
        if ch == "{":
            brace_depth += 1
            buf.append(ch)
            idx += 1
            continue
        if ch == "}" and brace_depth:
            brace_depth -= 1
            buf.append(ch)
            idx += 1
            continue
        if ch == "(":
            depth += 1
            buf.append(ch)
            idx += 1
            continue
        if ch == ")" and depth:
            depth -= 1
            buf.append(ch)
            idx += 1
            continue
        if depth == 0 and brace_depth == 0 and value.startswith(delimiter, idx):
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
            idx += len(delimiter)
            continue
        buf.append(ch)
        idx += 1
    part = "".join(buf).strip()
    if part:
        parts.append(part)
    return parts


def find_matching_group_close(value: str, open_idx: int) -> int:
    in_class = False
    escaped = False
    depth = 0
    for idx in range(open_idx, len(value)):
        ch = value[idx]
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if in_class:
            if ch == "]":
                in_class = False
            continue
        if ch == "[":
            in_class = True
            continue
        if ch == "(":
            depth += 1
            continue
        if ch == ")" and depth:
            depth -= 1
            if depth == 0:
                return idx
    return -1


def read_wildcard_range(value: str, start_idx: int) -> tuple[str, str] | None:
    match = re.match(r"^\{(\d+(?:[,:]\d*)?)\}", value[start_idx:])
    if not match:
        return None
    return match.group(0), match.group(1).replace(":", ",")


def regex_escape(value: str) -> str:
    return re.escape(value)


def regex_escape_class(value: str) -> str:
    return re.sub(r"([\\\]\-\^])", r"\\\1", value)


def wildcard_unit(field: str) -> str:
    return NAHUATL_GRAPHEME_PATTERN if field in NAHUATL_GRAPHEME_FIELDS else LETTER_PATTERN


def expand_brace_inner(inner: str) -> str:
    out: list[str] = []
    idx = 0
    while idx < len(inner):
        ch = inner[idx]
        if ch == "\\" and idx + 1 < len(inner):
            out.append(regex_escape(inner[idx + 1]))
            idx += 2
            continue
        if ch.isalpha():
            optional = idx + 1 < len(inner) and inner[idx + 1] == "?"
            pattern = PLACEHOLDER_PATTERNS.get(ch.lower())
            if pattern:
                out.append(f"(?:{pattern})?" if optional else pattern)
                idx += 2 if optional else 1
                continue
        out.append(regex_escape(ch))
        idx += 1
    return "".join(out)


def expand_vc_placeholders(value: str) -> str:
    if not value:
        return ""
    out: list[str] = []
    idx = 0
    while idx < len(value):
        ch = value[idx]
        if ch == "\\":
            if idx + 1 < len(value):
                out.append(ch + value[idx + 1])
                idx += 2
            else:
                out.append(ch)
                idx += 1
            continue
        if ch != "{":
            out.append(ch)
            idx += 1
            continue
        end = value.find("}", idx + 1)
        if end == -1:
            out.append(ch)
            idx += 1
            continue
        inner = value[idx + 1:end]
        if re.match(r"^\d+([,:]\d*)?$", inner):
            out.append("{" + inner.replace(":", ",") + "}")
            idx = end + 1
            continue
        if inner.startswith(("=", "!")) and len(inner) > 1:
            negate = "^" if inner[0] == "!" else ""
            out.append(f"(?:[{negate}{regex_escape_class(inner[1:])}])")
            idx = end + 1
            continue
        counted = re.match(r"^([A-Za-z]+)(\d+)(?:-(\d*))?$", inner)
        if counted:
            min_count = int(counted.group(2))
            max_raw = counted.group(3)
            if max_raw is None:
                quantifier = f"{{{min_count}}}"
            elif max_raw == "":
                quantifier = f"{{{min_count},}}"
            else:
                max_count = int(max_raw)
                quantifier = f"{{{min_count},{max_count}}}" if max_count >= min_count else ""
            if quantifier:
                out.append(f"(?:{expand_brace_inner(counted.group(1))}){quantifier}")
                idx = end + 1
                continue
        out.append(f"(?:{expand_brace_inner(inner)})")
        idx = end + 1
    return "".join(out)


def convert_wildcard_pattern(value: str, field: str, allow_regex: bool = False) -> str:
    unit = wildcard_unit(field)
    out: list[str] = []
    in_class = False
    idx = 0
    while idx < len(value):
        ch = value[idx]
        if allow_regex and in_class:
            out.append(ch)
            if ch == "\\" and idx + 1 < len(value):
                out.append(value[idx + 1])
                idx += 2
                continue
            if ch == "]":
                in_class = False
            idx += 1
            continue
        if ch == "\\":
            if idx + 1 < len(value):
                if allow_regex and value[idx + 1].isdigit():
                    out.append("\\" + value[idx + 1])
                else:
                    out.append(regex_escape(value[idx + 1]))
                idx += 2
            else:
                out.append(r"\\")
                idx += 1
            continue
        if allow_regex and ch == "[":
            in_class = True
            out.append(ch)
            idx += 1
            continue
        if allow_regex and ch == "(":
            optional = read_optional_group(value, idx, field)
            if optional:
                body, end = optional
                out.append(body)
                idx = end
                continue
            out.append(ch)
            idx += 1
            continue
        if ch == "?":
            wildcard_range = read_wildcard_range(value, idx + 1)
            if wildcard_range:
                raw, quantifier = wildcard_range
                out.append(f"{unit}{{{quantifier}}}")
                idx += 1 + len(raw)
                continue
            run = 1
            while idx + run < len(value) and value[idx + run] == "?":
                run += 1
            out.append(f"{unit}{{{run}}}")
            idx += run
            continue
        if ch == "*":
            if idx + 1 < len(value) and value[idx + 1] == "*":
                out.append(f"{unit}{{2,}}")
                idx += 2
            else:
                out.append(f"{unit}+")
                idx += 1
            continue
        if allow_regex and ch == "+" and idx > 0 and value[idx - 1] in ")]}":
            out.append(ch)
            idx += 1
            continue
        if allow_regex and ch in ")]{}|":
            out.append(ch)
            idx += 1
            continue
        out.append(regex_escape(ch))
        idx += 1
    return "".join(out)


def read_optional_group(value: str, start_idx: int, field: str) -> tuple[str, int] | None:
    close_idx = find_matching_group_close(value, start_idx)
    if close_idx == -1:
        return None
    if close_idx + 1 < len(value) and value[close_idx + 1] in "?*+":
        return None
    if close_idx + 2 < len(value) and value[close_idx + 1] == "\\" and value[close_idx + 2].isdigit():
        return None
    inner = value[start_idx + 1:close_idx]
    if not inner or inner.startswith("?") or len(split_top_level(inner, "|")) > 1:
        return None
    body = convert_wildcard_pattern(expand_vc_placeholders(inner), field, allow_regex=True)
    return f"(?:{body})?", close_idx + 1


def expand_reduplication(value: str, field: str) -> str | None:
    if not value:
        return None
    trimmed = re.sub(r"^-+", "", value)
    trimmed = re.sub(r"-+$", "", trimmed)
    if not trimmed.startswith("+"):
        return None
    base = trimmed[1:].strip()
    if not base:
        return None
    vowel_match = REDUPLICATION_VOWELS.search(base)
    prefix_end = vowel_match.end() if vowel_match else 1
    prefix = base[:prefix_end] or base[:1]
    rest = base[len(prefix):]
    rest_body = convert_wildcard_pattern(expand_vc_placeholders(rest), field, allow_regex=True)
    return f"(?:{regex_escape(prefix)}){{2}}{rest_body}"


def next_reduplication_group_name(prefix: str) -> str:
    global REDUPLICATION_GROUP_COUNTER
    REDUPLICATION_GROUP_COUNTER += 1
    return f"{prefix}{REDUPLICATION_GROUP_COUNTER}"


def parse_marker_count(raw: str | None) -> dict[str, int | None] | None:
    if not raw:
        return {"min": 2, "max": 2}
    match = re.match(r"^([1-9]\d*)(?:-(\d*))?$", raw)
    if not match:
        return None
    min_count = int(match.group(1))
    has_range = match.group(2) is not None
    max_count = int(match.group(2)) if has_range and match.group(2) != "" else None if has_range else min_count
    if max_count is not None and max_count < min_count:
        return None
    return {"min": min_count, "max": max_count}


def marker_repeat_quantifier(marker: dict[str, Any], offset: int) -> str:
    min_count = max(0, int(marker["min"]) + offset)
    max_value = marker["max"]
    max_count = None if max_value is None else max(0, int(max_value) + offset)
    if max_count == min_count:
        return f"{{{min_count}}}"
    if max_count is None:
        return f"{{{min_count},}}"
    return f"{{{min_count},{max_count}}}"


def read_reduplication_marker_at(value: str, idx: int) -> dict[str, Any] | None:
    if idx < 0 or is_escaped_at(value, idx):
        return None
    match = REDUPLICATION_MARKER_RE.match(value[idx:])
    if not match:
        return None
    marker_range = parse_marker_count(match.group(1))
    if not marker_range:
        return None
    return {
        "raw": match.group(0),
        "start": idx,
        "end": idx + len(match.group(0)),
        "min": marker_range["min"],
        "max": marker_range["max"],
    }


def find_next_reduplication_marker(value: str, start_idx: int = 0) -> dict[str, Any] | None:
    for idx in range(start_idx, len(value)):
        marker = read_reduplication_marker_at(value, idx)
        if marker:
            return marker
    return None


def expand_pattern_segment_for_regex(segment: str, field: str) -> str:
    if not segment:
        return ""
    return convert_wildcard_pattern(expand_vc_placeholders(segment), field, allow_regex=True)


def parse_optional_reduplication_h_infix(value: str) -> dict[str, str] | None:
    if value == "(h)" and not is_escaped_at(value, 0):
        return {"raw": value, "body": "(?:h)?"}
    return None


def read_optional_reduplication_h(value: str, start_idx: int, stop_idx: int | None = None) -> dict[str, Any] | None:
    stop = len(value) if stop_idx is None else stop_idx
    if start_idx + 3 <= stop and value.startswith("(h)", start_idx) and not is_escaped_at(value, start_idx):
        return {"raw": value[start_idx:start_idx + 3], "body": "(?:h)?", "end": start_idx + 3}
    return None


def read_literal_syllable(value: str, start_idx: int, stop_idx: int | None = None) -> dict[str, Any] | None:
    stop = len(value) if stop_idx is None else stop_idx
    if start_idx >= stop:
        return None
    escaped = False
    for idx in range(start_idx, stop):
        ch = value[idx]
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch in "{}()[\\]|^$*+?.":
            return None
        if REDUPLICATION_VOWELS.search(ch):
            return {"target": value[start_idx:idx + 1], "end": idx + 1}
    return None


def find_next_brace_placeholder(value: str, start_idx: int) -> dict[str, Any] | None:
    idx = start_idx
    while idx < len(value):
        if value[idx] != "{" or is_escaped_at(value, idx):
            idx += 1
            continue
        end = value.find("}", idx + 1)
        if end == -1:
            return None
        inner = value[idx + 1:end]
        if re.match(r"^\d+([,:]\d*)?$", inner) or re.match(r"^[Rr](?:[1-9]\d*(?:-\d*)?)?$", inner):
            idx = end + 1
            continue
        return {"raw": value[idx:end + 1], "start": idx, "end": end + 1}
    return None


def read_literal_reduplication_target(value: str, start_idx: int, stop_idx: int | None = None) -> dict[str, Any] | None:
    stop = len(value) if stop_idx is None else stop_idx
    optional_h = read_optional_reduplication_h(value, start_idx, stop)
    if optional_h:
        after_optional = read_literal_syllable(value, optional_h["end"], stop)
        if after_optional:
            return {
                "infix": optional_h["raw"],
                "infixBody": optional_h["body"],
                "target": after_optional["target"],
                "end": after_optional["end"],
            }
    if start_idx < stop and value[start_idx] == "h":
        after_saltillo = read_literal_syllable(value, start_idx + 1, stop)
        if after_saltillo:
            return {
                "infix": "h",
                "target": after_saltillo["target"],
                "end": after_saltillo["end"],
            }
    syllable = read_literal_syllable(value, start_idx, stop)
    return {"infix": "", "target": syllable["target"], "end": syllable["end"]} if syllable else None


def read_reduplication_marker_target(value: str, start_idx: int, field: str) -> dict[str, Any] | None:
    brace = find_next_brace_placeholder(value, start_idx)
    if brace:
        prefix = value[start_idx:brace["start"]]
        optional_h = parse_optional_reduplication_h_infix(prefix)
        if optional_h:
            return {"infix": prefix, "infixBody": optional_h["body"], "target": brace["raw"], "end": brace["end"]}
        if not REDUPLICATION_VOWELS.search(prefix):
            return {"infix": prefix, "target": brace["raw"], "end": brace["end"]}

    literal = read_literal_reduplication_target(value, start_idx, brace["start"] if brace else len(value))
    if literal:
        return literal
    if brace:
        return {"infix": value[start_idx:brace["start"]], "target": brace["raw"], "end": brace["end"]}
    return None


def build_reduplication_full_body(target_body: str, infix_body: str, marker: dict[str, Any]) -> str:
    group_name = next_reduplication_group_name("r")
    return f"(?P<{group_name}>{target_body})(?:{infix_body}(?P={group_name})){marker_repeat_quantifier(marker, -1)}"


def build_reduplication_prefix_body(target_body: str, infix_body: str, marker: dict[str, Any]) -> str:
    group_name = next_reduplication_group_name("r")
    return (
        f"(?P<{group_name}>{target_body}){infix_body}"
        f"(?:(?P={group_name}){infix_body}){marker_repeat_quantifier(marker, -2)}"
    )


def read_optional_reduplication_marker_group(value: str, marker_idx: int) -> dict[str, Any] | None:
    open_idx = marker_idx - 1
    if open_idx < 0 or value[open_idx] != "(" or is_escaped_at(value, open_idx):
        return None
    close_idx = find_matching_group_close(value, open_idx)
    marker = read_reduplication_marker_at(value, marker_idx)
    if not marker or close_idx == -1 or close_idx < marker["end"]:
        return None
    inner = value[open_idx + 1:close_idx]
    inner_marker = read_reduplication_marker_at(inner, 0)
    if not inner_marker:
        return None
    tail = inner[len(inner_marker["raw"]):]
    if len(split_top_level(tail, "|")) > 1:
        return None
    if not tail:
        return {"openIdx": open_idx, "end": close_idx + 1, "infixBody": "", "min": inner_marker["min"], "max": inner_marker["max"]}
    optional_h = parse_optional_reduplication_h_infix(tail)
    if optional_h:
        return {
            "openIdx": open_idx,
            "end": close_idx + 1,
            "infixBody": optional_h["body"],
            "min": inner_marker["min"],
            "max": inner_marker["max"],
        }
    if tail == "h" and not is_escaped_at(tail, 0):
        return {"openIdx": open_idx, "end": close_idx + 1, "infixBody": "h", "min": inner_marker["min"], "max": inner_marker["max"]}
    return None


def expand_reduplication_markers(value: str, field: str) -> str | None:
    source = str(value or "")
    if not REDUPLICATION_MARKER_RE.search(source):
        return None
    out: list[str] = []
    idx = 0
    while idx < len(source):
        marker = find_next_reduplication_marker(source, idx)
        if not marker:
            out.append(expand_pattern_segment_for_regex(source[idx:], field))
            break
        optional_group = read_optional_reduplication_marker_group(source, marker["start"])
        if optional_group:
            out.append(expand_pattern_segment_for_regex(source[idx:optional_group["openIdx"]], field))
            target = read_reduplication_marker_target(source, optional_group["end"], field)
            if not target:
                return None
            target_body = expand_pattern_segment_for_regex(target["target"], field)
            if not target_body:
                return None
            out.append(
                f"(?:{build_reduplication_prefix_body(target_body, optional_group['infixBody'], optional_group)})?"
            )
            idx = optional_group["end"]
            continue
        out.append(expand_pattern_segment_for_regex(source[idx:marker["start"]], field))
        target = read_reduplication_marker_target(source, marker["end"], field)
        if not target:
            return None
        target_body = expand_pattern_segment_for_regex(target["target"], field)
        if not target_body:
            return None
        infix_body = target.get("infixBody")
        if infix_body is None:
            infix_body = expand_pattern_segment_for_regex(target.get("infix", ""), field)
        out.append(build_reduplication_full_body(target_body, infix_body, marker))
        idx = target["end"]
    return "".join(out) or None


def expand_same_again_markers(value: str, field: str) -> str | None:
    source = str(value or "")
    if "(" not in source or not REDUPLICATION_MARKER_RE.search(source):
        return None
    out: list[str] = []
    last = 0
    changed = False
    idx = 0
    while idx < len(source):
        if source[idx] != "(" or is_escaped_at(source, idx):
            idx += 1
            continue
        close_idx = find_matching_group_close(source, idx)
        if close_idx == -1:
            idx += 1
            continue
        marker = read_reduplication_marker_at(source, close_idx + 1)
        if not marker:
            idx = close_idx + 1
            continue
        out.append(expand_pattern_segment_for_regex(source[last:idx], field))
        inner = source[idx + 1:close_idx]
        body = expand_pattern_segment_for_regex(inner, field)
        if not body:
            return None
        group_name = next_reduplication_group_name("s")
        out.append(f"(?P<{group_name}>{body})(?P={group_name}){marker_repeat_quantifier(marker, -1)}")
        last = marker["end"]
        idx = marker["end"]
        changed = True
    if not changed:
        return None
    out.append(expand_pattern_segment_for_regex(source[last:], field))
    return "".join(out)


def build_composite_pattern_body(value: str, field: str) -> str:
    same_again = expand_same_again_markers(value, field)
    if same_again is not None:
        return same_again
    redup_marker = expand_reduplication_markers(value, field)
    if redup_marker is not None:
        return redup_marker
    expanded = expand_vc_placeholders(value)
    redup = expand_reduplication(expanded, field)
    if redup is not None:
        return redup
    return convert_wildcard_pattern(expanded, field, allow_regex=True)


def build_contains_both_body(value: str, field: str) -> str | None:
    if not value.startswith("(") or not value.endswith(")"):
        return None
    inner = value[1:-1]
    if "||" not in inner:
        return None
    parts = split_top_level(inner, "||")
    if len(parts) < 2:
        return None
    lookaheads = []
    for part in parts:
        body = build_composite_pattern_body(part, field)
        lookaheads.append(f"(?=.*{body})")
    return "".join(lookaheads) + ".*"


def find_top_level_context_operator(value: str) -> tuple[int, str] | None:
    escaped = False
    paren_depth = 0
    brace_depth = 0
    bracket_depth = 0
    for idx, ch in enumerate(value):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if bracket_depth:
            if ch == "]":
                bracket_depth -= 1
            continue
        if brace_depth:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
            continue
        if ch == "[":
            bracket_depth += 1
            continue
        if ch == "{":
            brace_depth += 1
            continue
        if ch == "(":
            paren_depth += 1
            continue
        if ch == ")" and paren_depth:
            paren_depth -= 1
            continue
        if paren_depth == 0 and ch in "<>":
            return idx, ch
    return None


def compile_context_component_body(value: str, field: str) -> str | None:
    contains_both = build_contains_both_body(value, field)
    if contains_both is not None:
        return contains_both
    return build_composite_pattern_body(value, field)


def build_context_query(value: str, field: str) -> dict[str, Any] | None:
    op = find_top_level_context_operator(value)
    if not op:
        return None
    idx, operator = op
    left = value[:idx].strip()
    right = value[idx + 1:].strip()
    if not left or not right:
        return None
    target_body = compile_context_component_body(left, field)
    context_body = compile_context_component_body(right, field)
    if not target_body or not context_body:
        return None
    try:
        target_regex = re.compile(target_body, re.IGNORECASE)
        context_regex = re.compile(context_body, re.IGNORECASE)
    except re.error:
        return {"kind": "unsupported", "terms": []}
    return {
        "kind": "context",
        "op": operator,
        "targetRegex": target_regex,
        "contextRegex": context_regex,
        "allowLoose": not has_formatting_characters(value),
        "terms": pattern_literal_terms(left) + pattern_literal_terms(right),
    }


def is_quoted(value: str) -> bool:
    return len(value) >= 2 and value[0] == '"' and value[-1] == '"' and not is_escaped_at(value, len(value) - 1)


def unquote_value(value: str) -> str:
    return value[1:-1].replace(r"\"", '"').replace(r"\\", "\\")


def compile_pattern_body(value: str, field: str) -> str:
    if is_quoted(value):
        return regex_escape(unquote_value(value)).replace(r"\ ", r"\s+")
    contains_both = build_contains_both_body(value, field)
    if contains_both is not None:
        return contains_both
    return build_composite_pattern_body(value, field)


def pattern_literal_terms(value: str, accent_sensitive: bool = False, old_spanish: bool = False) -> list[str]:
    terms: list[str] = []
    buf: list[str] = []
    escaped = False
    in_brace = False
    in_class = False
    for ch in value:
        if escaped:
            if ch.isalnum():
                buf.append(ch)
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if in_brace:
            if ch == "}":
                in_brace = False
            continue
        if in_class:
            if ch == "]":
                in_class = False
            continue
        if ch == "{":
            if buf:
                terms.append("".join(buf))
                buf = []
            in_brace = True
            continue
        if ch == "[":
            if buf:
                terms.append("".join(buf))
                buf = []
            in_class = True
            continue
        if ch.isalnum():
            buf.append(ch)
            continue
        if buf:
            terms.append("".join(buf))
            buf = []
    if buf:
        terms.append("".join(buf))
    normalized_terms = [normalize_for_search(term, accent_sensitive, old_spanish) for term in terms]
    return [term for term in normalized_terms if len(term) >= 3]


def build_filter_query(filter_item: dict[str, Any]) -> dict[str, Any]:
    raw = str(filter_item.get("value", "") or "").strip()
    mode = str(filter_item.get("mode", "any"))
    field = str(filter_item.get("field", ""))
    accent_sensitive = bool(filter_item.get("accentSensitive"))
    old_spanish = bool(filter_item.get("oldSpanish")) and not accent_sensitive
    if not raw:
        return {"kind": "empty", "terms": []}
    normalized_raw = normalize_query_source(raw, accent_sensitive, old_spanish)
    context_query = build_context_query(normalized_raw, field)
    if context_query is not None:
        context_query["accentSensitive"] = accent_sensitive
        context_query["oldSpanish"] = old_spanish
        return context_query

    simple_literal = mode != "regex" and not raw.startswith("+") and not re.search(r'[\\*?"()[\]{}|<>]', raw)
    effective_mode = mode
    literal_text = normalized_raw
    if simple_literal:
        leading = literal_text.startswith("-")
        trailing = literal_text.endswith("-") and not is_escaped_at(literal_text, len(literal_text) - 1)
        if mode == "exact":
            if leading and trailing and len(literal_text) > 2:
                effective_mode = "any"
                literal_text = literal_text[1:-1]
            elif trailing:
                effective_mode = "starts"
                literal_text = literal_text[:-1]
            elif leading:
                effective_mode = "ends"
                literal_text = literal_text[1:]
        literal_text = literal_text.replace(r"\-", "-").strip()
        return {
            "kind": "literal",
            "strict": literal_text,
            "loose": collapse_spaces(strip_punctuation_characters(literal_text)),
            "mode": effective_mode,
            "terms": [term for term in re.findall(r"[0-9a-z]+", literal_text) if len(term) >= 3],
            "accentSensitive": accent_sensitive,
            "oldSpanish": old_spanish,
        }

    top_level_parts = split_top_level(normalized_raw, "|") or [normalized_raw]
    bodies: list[tuple[str, str]] = []
    for part in top_level_parts:
        text = part.strip()
        if not text:
            continue
        part_mode = mode
        leading = text.startswith("-")
        trailing = text.endswith("-") and not is_escaped_at(text, len(text) - 1)
        if part_mode == "exact":
            if leading and trailing and len(text) > 2:
                part_mode = "any"
                text = text[1:-1]
            elif trailing:
                part_mode = "starts"
                text = text[:-1]
            elif leading:
                part_mode = "ends"
                text = text[1:]
        text = text.replace(r"\-", "-").strip()
        if not text:
            continue
        bodies.append((compile_pattern_body(text, field), part_mode))
    if not bodies:
        return {"kind": "empty", "terms": []}

    anchored_parts = []
    for body, part_mode in bodies:
        if part_mode == "exact":
            anchored_parts.append(f"^(?:{body})$")
        elif part_mode == "starts":
            anchored_parts.append(f"^(?:{body})")
        elif part_mode == "ends":
            anchored_parts.append(f"(?:{body})$")
        else:
            anchored_parts.append(body)
    anchored = anchored_parts[0] if len(anchored_parts) == 1 else "|".join(anchored_parts)
    phrase_parts = [body for body, part_mode in bodies]
    phrase_any = phrase_parts[0] if len(phrase_parts) == 1 else "|".join(phrase_parts)
    try:
        strict_regex = re.compile(anchored, re.IGNORECASE)
        phrase_regex = re.compile(phrase_any, re.IGNORECASE)
    except re.error:
        return {"kind": "unsupported", "terms": []}
    return {
        "kind": "regex",
        "regex": strict_regex,
        "phraseRegex": phrase_regex,
        "mode": mode,
        "allowLoose": not has_formatting_characters(raw),
        "terms": pattern_literal_terms(normalized_raw, accent_sensitive, old_spanish),
        "termMode": "all" if "||" in normalized_raw else "any" if len(top_level_parts) > 1 else "all",
        "accentSensitive": accent_sensitive,
        "oldSpanish": old_spanish,
    }


def compile_filter_items(filters: list[dict[str, Any]], accent_sensitive: bool = False, old_spanish: bool = False) -> list[dict[str, Any]]:
    compiled: list[dict[str, Any]] = []
    for item in filters:
        cloned = dict(item)
        cloned["accentSensitive"] = bool(cloned.get("accentSensitive", accent_sensitive))
        cloned["oldSpanish"] = bool(cloned.get("oldSpanish", old_spanish)) and not cloned["accentSensitive"]
        if cloned.get("type") == "wordGroup":
            cloned["_expression"] = compile_word_group_expression(cloned, cloned["accentSensitive"], cloned["oldSpanish"])
        else:
            cloned["_query"] = build_filter_query(cloned)
        compiled.append(cloned)
    return compiled


def fts_literal(value: str) -> str:
    normalized = normalize_string(value)
    tokens = [token for token in re.findall(r"[0-9a-z]+", normalized) if len(token) >= 3]
    if not tokens:
        return ""
    return " ".join(tokens)


def fts_columns_for_filter(field: str, layer: str) -> list[str]:
    if field in ("Fuente", ""):
        return []
    if field not in LAYERED_FIELDS:
        column = FTS_COLUMNS.get((field, "normalized"))
        return [column] if column else []
    layers = ("normalized", "source") if layer == "both" else (layer,)
    return [FTS_COLUMNS[(field, item)] for item in layers if (field, item) in FTS_COLUMNS]


def fts_match_for_filter(filter_item: dict[str, Any], layer: str) -> str:
    if filter_item.get("negate"):
        return ""
    if filter_item.get("type") in {"reversePreset", "wordGroup"}:
        return ""
    query = filter_item.get("_query") or build_filter_query(filter_item)
    if query.get("kind") == "unsupported":
        return ""
    if query.get("accentSensitive") or query.get("oldSpanish"):
        return ""
    terms = query.get("terms") or []
    value = " ".join(dict.fromkeys(term for term in terms if len(term) >= 3))
    if query.get("termMode") == "any" and len(value.split()) > 1:
        return ""
    if not value and query.get("kind") != "regex":
        value = fts_literal(str(filter_item.get("value", "")))
    if len(value.replace(" ", "")) < 3:
        return ""
    columns = fts_columns_for_filter(str(filter_item.get("field", "")), layer)
    if not columns:
        return ""
    column_expr = " ".join(columns) if len(columns) > 1 else columns[0]
    return f"{{{column_expr}}} : {value}"


def candidate_sql(filters: list[dict[str, Any]], fuentes: list[str], layer: str) -> tuple[str, list[Any], bool]:
    where = []
    args: list[Any] = []
    can_limit_in_sql = not filters
    if fuentes:
        where.append(f"r.fuente IN ({','.join('?' for _ in fuentes)})")
        args.extend(fuentes)
    positive_matches = [
        fts_match_for_filter(filter_item, layer)
        for filter_item in filters
        if str(filter_item.get("logic", "AND")).upper() == "AND"
    ]
    positive_matches = [match for match in positive_matches if match]
    for match in positive_matches:
        where.append("r.id IN (SELECT rowid FROM search_fts WHERE search_fts MATCH ?)")
        args.append(match)
    sql = "SELECT r.id, r.row_json FROM rows r"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY r.prio IS NULL, r.prio, r.editado COLLATE NOCASE, r.fuente COLLATE NOCASE, r.record_id"
    return sql, args, can_limit_in_sql


def normalize_scope(scope: str) -> str:
    return scope if scope in {"whole", "word", "phrase", "wordPhrase"} else "whole"


def word_tokens(value: str, accent_sensitive: bool = False, old_spanish: bool = False) -> list[str]:
    return WORD_RE.findall(normalize_for_search(value, accent_sensitive, old_spanish))


def phrase_window_counts(query_text: str, accent_sensitive: bool = False, old_spanish: bool = False) -> list[int]:
    raw = normalize_for_search(query_text, accent_sensitive, old_spanish)
    literal_words = re.findall(r"[0-9a-zÀ-ɏḀ-ỿ]+", raw)
    base = max(1, len(literal_words))
    may_span = bool(re.search(r"\s|\\s|\([^)]*\s+[^)]*\)", raw))
    if may_span:
        return list(range(1, min(8, max(2, base + 2)) + 1))
    return [1]


def regex_matches_phrase_windows(text: str, regex: re.Pattern[str], query_text: str, accent_sensitive: bool = False, old_spanish: bool = False) -> bool:
    tokens = WORD_RE.findall(collapse_spaces(normalize_for_search(text, accent_sensitive, old_spanish)))
    if not tokens:
        return False
    for count in phrase_window_counts(query_text, accent_sensitive, old_spanish):
        if count > len(tokens):
            continue
        for start in range(0, len(tokens) - count + 1):
            if regex.search(" ".join(tokens[start:start + count])):
                return True
    return False


def context_matches_candidate(candidate: str, query: dict[str, Any]) -> bool:
    target_regex = query["targetRegex"]
    context_regex = query["contextRegex"]
    operator = query.get("op")
    for match in target_regex.finditer(candidate):
        if operator == ">":
            if context_regex.match(candidate, match.end()):
                return True
            continue
        prefix = candidate[:match.start()]
        for context_match in context_regex.finditer(prefix):
            if context_match.end() == match.start():
                return True
    return False


def context_matches_text(text: str, query: dict[str, Any], scope: str) -> bool:
    accent_sensitive = bool(query.get("accentSensitive"))
    old_spanish = bool(query.get("oldSpanish")) and not accent_sensitive
    normalized_text = collapse_spaces(normalize_for_search(text, accent_sensitive, old_spanish))
    loose_text = collapse_spaces(strip_punctuation_characters(normalized_text))
    targets = [normalized_text]
    if query.get("allowLoose") and loose_text != normalized_text:
        targets.append(loose_text)
    if scope == "word":
        return any(context_matches_candidate(token, query) for candidate in targets for token in WORD_RE.findall(candidate))
    if scope == "wordPhrase":
        return context_matches_text(text, query, "word") or context_matches_text(text, query, "phrase")
    if scope == "phrase":
        tokens = WORD_RE.findall(normalized_text)
        for count in phrase_window_counts(" ".join(query.get("terms") or []), accent_sensitive, old_spanish):
            if count > len(tokens):
                continue
            for start in range(0, len(tokens) - count + 1):
                if context_matches_candidate(" ".join(tokens[start:start + count]), query):
                    return True
        return False
    return any(context_matches_candidate(candidate, query) for candidate in targets)


def match_text(text: str, query_text: str, mode: str, scope: str, compiled_query: dict[str, Any] | None = None) -> bool:
    compiled_query = compiled_query or build_filter_query({"value": query_text, "mode": mode})
    if compiled_query.get("kind") == "unsupported":
        return False
    match_mode = str(compiled_query.get("mode") or mode)
    if compiled_query.get("kind") == "context":
        return context_matches_text(text, compiled_query, scope)
    accent_sensitive = bool(compiled_query.get("accentSensitive"))
    old_spanish = bool(compiled_query.get("oldSpanish")) and not accent_sensitive
    normalized_text = collapse_spaces(normalize_for_search(text, accent_sensitive, old_spanish))
    loose_text = collapse_spaces(strip_punctuation_characters(normalized_text))
    if compiled_query.get("kind") == "regex":
        regex = compiled_query["regex"]
        phrase_regex = compiled_query.get("phraseRegex") or regex
        targets = [normalized_text]
        if compiled_query.get("allowLoose") and loose_text != normalized_text:
            targets.append(loose_text)
        if scope == "word":
            return any(regex.search(token) for candidate in targets for token in WORD_RE.findall(candidate))
        if scope == "wordPhrase":
            return match_text(text, query_text, mode, "word", compiled_query) or match_text(text, query_text, mode, "phrase", compiled_query)
        if scope == "phrase":
            if mode == "exact":
                return regex_matches_phrase_windows(text, regex, query_text, accent_sensitive, old_spanish)
            if mode == "any":
                return any(phrase_regex.search(candidate) for candidate in targets)
            return any(regex.search(candidate) for candidate in targets)
        return any(regex.search(candidate) for candidate in targets)

    normalized_query = collapse_spaces(str(compiled_query.get("strict", "")))
    if not normalized_query:
        return False
    if scope == "word":
        return any(match_candidate(token, normalized_query, match_mode) for token in word_tokens(text, accent_sensitive, old_spanish))
    if scope == "wordPhrase":
        return match_text(text, query_text, mode, "word", compiled_query) or match_text(text, query_text, mode, "phrase", compiled_query)
    if scope == "phrase":
        return match_candidate(normalized_text, normalized_query, "any" if match_mode == "exact" else match_mode)
    return match_candidate(normalized_text, normalized_query, match_mode)


def match_candidate(candidate: str, query: str, mode: str) -> bool:
    if mode == "exact":
        return candidate == query
    if mode == "starts":
        return candidate.startswith(query)
    if mode == "ends":
        return candidate.endswith(query)
    return query in candidate


def filter_value_looks_multi_word(value: Any) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return False
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        raw = raw[1:-1]
    return bool(re.search(r"\s", raw.strip()))


def normalize_word_group_structure(filter_item: dict[str, Any]) -> dict[str, Any]:
    expression = filter_item.get("expression")
    if isinstance(expression, dict):
        return expression
    conditions = filter_item.get("conditions")
    if isinstance(conditions, list):
        children = []
        for condition in conditions:
            if not isinstance(condition, dict):
                continue
            children.append({
                "type": "condition",
                "mode": condition.get("mode"),
                "value": condition.get("value"),
                "negate": bool(condition.get("negate")),
            })
        return {"type": "group", "logic": "AND", "children": children}
    return {"type": "group", "logic": "AND", "children": []}


def compile_word_group_expression_node(
    node: Any,
    field: str,
    accent_sensitive: bool,
    old_spanish: bool,
) -> dict[str, Any]:
    if not isinstance(node, dict):
        return {"type": "group", "logic": "AND", "children": []}
    node_type = str(node.get("type") or "group")
    if node_type == "condition":
        condition = dict(node)
        condition["type"] = "condition"
        condition["field"] = str(condition.get("field") or field)
        condition["mode"] = str(condition.get("mode") or "any")
        condition["value"] = str(condition.get("value") or "")
        condition["negate"] = bool(condition.get("negate"))
        condition["accentSensitive"] = bool(condition.get("accentSensitive", accent_sensitive))
        condition["oldSpanish"] = bool(condition.get("oldSpanish", old_spanish)) and not condition["accentSensitive"]
        condition["_query"] = build_filter_query(condition)
        return condition
    logic = "OR" if str(node.get("logic") or "AND").upper() == "OR" else "AND"
    children = [
        compile_word_group_expression_node(child, field, accent_sensitive, old_spanish)
        for child in (node.get("children") if isinstance(node.get("children"), list) else [])
    ]
    return {"type": "group", "logic": logic, "children": children}


def compile_word_group_expression(filter_item: dict[str, Any], accent_sensitive: bool, old_spanish: bool) -> dict[str, Any]:
    field = str(filter_item.get("field") or "")
    expression = normalize_word_group_structure(filter_item)
    return compile_word_group_expression_node(expression, field, accent_sensitive, old_spanish)


def split_word_quick_groups(filters: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[list[dict[str, Any]]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    remaining: list[dict[str, Any]] = []
    for item in filters:
        group_id = str(item.get("wordGroupId") or "")
        scope = normalize_scope(str(item.get("scope", "whole")))
        field = str(item.get("field", ""))
        if scope == "word" and group_id and not filter_value_looks_multi_word(item.get("value")):
            grouped.setdefault((field, group_id), []).append(item)
        else:
            remaining.append(item)
    return remaining, list(grouped.values())


def word_candidate_matches_filter(token: str, filter_item: dict[str, Any]) -> bool:
    mode = str(filter_item.get("mode", "any"))
    value = str(filter_item.get("value", ""))
    compiled_query = filter_item.get("_query") or build_filter_query(filter_item)
    match_mode = str(compiled_query.get("mode") or mode)
    if compiled_query.get("kind") == "unsupported":
        return False
    if compiled_query.get("kind") == "context":
        return context_matches_candidate(token, compiled_query)
    if compiled_query.get("kind") == "regex":
        regex = compiled_query["regex"]
        if regex.search(token):
            return True
        if compiled_query.get("allowLoose"):
            loose = collapse_spaces(strip_punctuation_characters(token))
            return loose != token and regex.search(loose) is not None
        return False

    normalized_query = collapse_spaces(str(compiled_query.get("strict", "")))
    if not normalized_query:
        return False
    if match_candidate(token, normalized_query, match_mode):
        return True
    if compiled_query.get("allowLoose"):
        loose = collapse_spaces(strip_punctuation_characters(token))
        return loose != token and match_candidate(loose, normalized_query, match_mode)
    return False


def word_matches_group_segments(token: str, filters: list[dict[str, Any]]) -> bool:
    segments: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for item in filters:
        mode = str(item.get("mode", "any"))
        segment = segments.setdefault(mode, {"include": [], "exclude": []})
        bucket = "exclude" if item.get("negate") else "include"
        segment[bucket].append(item)
    for segment in segments.values():
        if any(word_candidate_matches_filter(token, item) for item in segment["exclude"]):
            return False
        if segment["include"] and not any(word_candidate_matches_filter(token, item) for item in segment["include"]):
            return False
    return True


def row_matches_word_group(row: dict[str, Any], filters: list[dict[str, Any]], layer: str) -> bool:
    if not filters:
        return True
    field = str(filters[0].get("field", ""))
    if field not in SEARCH_FIELDS:
        return False
    has_include = any(not item.get("negate") for item in filters)
    accent_sensitive = any(bool((item.get("_query") or {}).get("accentSensitive")) for item in filters)
    old_spanish = any(bool((item.get("_query") or {}).get("oldSpanish")) for item in filters) and not accent_sensitive
    tokens: list[str] = []
    for text in layer_values(row, field, layer):
        tokens.extend(word_tokens(text, accent_sensitive, old_spanish))
    if not has_include:
        return all(not word_candidate_matches_filter(token, item) for token in tokens for item in filters)
    return any(word_matches_group_segments(token, filters) for token in tokens)


def word_group_expression_matches_token(token: str, node: dict[str, Any]) -> bool:
    if node.get("type") == "condition":
        matches = word_candidate_matches_filter(token, node)
        return not matches if node.get("negate") else matches
    children = node.get("children") if isinstance(node.get("children"), list) else []
    if not children:
        return True
    if str(node.get("logic") or "AND").upper() == "OR":
        return any(word_group_expression_matches_token(token, child) for child in children)
    return all(word_group_expression_matches_token(token, child) for child in children)


def row_matches_word_group_expression(row: dict[str, Any], filter_item: dict[str, Any], layer: str) -> bool:
    field = str(filter_item.get("field", ""))
    if field not in SEARCH_FIELDS:
        return False
    expression = filter_item.get("_expression") or compile_word_group_expression(
        filter_item,
        bool(filter_item.get("accentSensitive")),
        bool(filter_item.get("oldSpanish")),
    )
    accent_sensitive = bool(filter_item.get("accentSensitive"))
    old_spanish = bool(filter_item.get("oldSpanish")) and not accent_sensitive
    tokens: list[str] = []
    for text in layer_values(row, field, layer):
        tokens.extend(word_tokens(text, accent_sensitive, old_spanish))
    return any(word_group_expression_matches_token(token, expression) for token in tokens)


def row_matches_reverse_preset(row: dict[str, Any], filter_item: dict[str, Any], layer: str) -> bool:
    raw_fields = filter_item.get("fields")
    fields = [str(item) for item in raw_fields if str(item) in SEARCH_FIELDS] if isinstance(raw_fields, list) else []
    if not fields:
        field = str(filter_item.get("field", ""))
        fields = [field] if field in SEARCH_FIELDS else []
    ok = False
    for field in fields:
        field_filter = dict(filter_item)
        field_filter["type"] = "filter"
        field_filter["field"] = field
        field_filter["negate"] = False
        field_filter.pop("_query", None)
        field_filter["_query"] = build_filter_query(field_filter)
        if row_matches_filter(row, field_filter, layer):
            ok = True
            break
    return not ok if filter_item.get("negate") else ok


def row_matches_filter(row: dict[str, Any], filter_item: dict[str, Any], layer: str) -> bool:
    filter_type = str(filter_item.get("type") or "filter")
    if filter_type == "wordGroup":
        return row_matches_word_group_expression(row, filter_item, layer)
    if filter_type == "reversePreset":
        return row_matches_reverse_preset(row, filter_item, layer)
    if filter_type not in {"filter", "compare"}:
        return False
    field = str(filter_item.get("field", ""))
    if field not in SEARCH_FIELDS:
        return False
    mode = str(filter_item.get("mode", "any"))
    scope = normalize_scope(str(filter_item.get("scope", "whole")))
    value = str(filter_item.get("value", ""))
    compiled_query = filter_item.get("_query") or build_filter_query(filter_item)
    matches = any(match_text(text, value, mode, scope, compiled_query) for text in layer_values(row, field, layer))
    return not matches if filter_item.get("negate") else matches


def row_matches_filters(row: dict[str, Any], filters: list[dict[str, Any]], layer: str) -> bool:
    remaining_filters, word_groups = split_word_quick_groups(filters)
    and_filters = [item for item in remaining_filters if str(item.get("logic", "AND")).upper() != "OR"]
    or_filters = [item for item in remaining_filters if str(item.get("logic", "AND")).upper() == "OR"]
    and_ok = all(row_matches_filter(row, item, layer) for item in and_filters) and all(
        row_matches_word_group(row, group, layer) for group in word_groups
    )
    or_ok = any(row_matches_filter(row, item, layer) for item in or_filters) if or_filters else True
    return and_ok and or_ok


def build_sort_key(value: Any) -> str:
    return re.sub(r"^[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", "", strip_html_tags(str(value or ""))).strip()


def natural_key(value: Any) -> tuple[tuple[int, Any], ...]:
    normalized = normalize_string(str(value or ""))
    parts = re.split(r"(\d+)", normalized)
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in parts if part != "")


def display_sort_value(row: dict[str, Any], field: str) -> str:
    if field == "Fuente":
        return normalize_string(normalized_display_value(row, "Fuente"))
    return build_sort_key(normalized_display_value(row, field))


def record_id_sort_key(row: dict[str, Any]) -> tuple[tuple[int, Any], ...]:
    return natural_key(row.get("record_id") or row.get("_rid") or "")


def priority_sort_key(row: dict[str, Any], tier: int = 2) -> tuple[Any, ...]:
    head = build_sort_key(normalized_display_value(row, "Editado") or normalized_display_value(row, "Original"))
    source = normalize_string(normalized_display_value(row, "Fuente"))
    return (
        tier,
        parse_priority(row.get("prio")),
        natural_key(head),
        natural_key(source),
        record_id_sort_key(row),
    )


def browse_order_key(row: dict[str, Any], browse_seed: int) -> tuple[int, tuple[tuple[int, Any], ...]]:
    text = str(row.get("record_id") or row.get("_rid") or "")
    value = (2166136261 ^ (browse_seed & 0xFFFFFFFF)) & 0xFFFFFFFF
    for ch in text:
        value ^= ord(ch)
        value = (value * 16777619) & 0xFFFFFFFF
    return value, record_id_sort_key(row)


def get_dominant_lemma_filter(filters: list[dict[str, Any]]) -> dict[str, Any] | None:
    substantive = [item for item in filters if item.get("type") != "fuenteSet"]
    if not substantive:
        return None
    if any(str(item.get("logic", "AND")).upper() == "OR" for item in substantive):
        return None
    candidates = [
        item for item in substantive
        if not item.get("negate")
        and str(item.get("field", "")) == "Editado"
        and normalize_scope(str(item.get("scope", "whole"))) == "word"
        and str(item.get("mode", "")) == "exact"
        and str(item.get("logic", "AND")).upper() == "AND"
    ]
    return candidates[0] if len(candidates) == 1 else None


def lemma_tier(row: dict[str, Any], filter_item: dict[str, Any]) -> int:
    query = filter_item.get("_query") or build_filter_query(filter_item)
    accent_sensitive = bool(query.get("accentSensitive"))
    old_spanish = bool(query.get("oldSpanish")) and not accent_sensitive
    tokens = word_tokens(normalized_display_value(row, str(filter_item.get("field", "Editado"))), accent_sensitive, old_spanish)
    if not tokens:
        return 2
    matched = any(word_candidate_matches_filter(token, filter_item) for token in tokens)
    if not matched:
        return 2
    return 0 if len(tokens) == 1 else 1


def build_ranking(filters: list[dict[str, Any]], rows: list[dict[str, Any]]) -> tuple[dict[str, int] | None, dict[str, int]]:
    dominant = get_dominant_lemma_filter(filters)
    if not dominant:
        return None, {}
    tiers: dict[str, int] = {}
    exact = 0
    phrase = 0
    for idx, row in enumerate(rows):
        row_id = str(row.get("record_id") or row.get("_rid") or idx)
        tier = lemma_tier(row, dominant)
        tiers[row_id] = tier
        if tier == 0:
            exact += 1
        elif tier == 1:
            phrase += 1
    return {"exact": exact, "phrase": phrase, "manual": False}, tiers


class WorstFirstPageEntry:
    __slots__ = ("key", "row")

    def __init__(self, key: tuple[Any, ...], row: dict[str, Any]) -> None:
        self.key = key
        self.row = row

    def __lt__(self, other: "WorstFirstPageEntry") -> bool:
        return self.key > other.key


def add_page_candidate(heap: list[WorstFirstPageEntry], key: tuple[Any, ...], row: dict[str, Any], limit: int) -> None:
    if limit <= 0:
        return
    entry = WorstFirstPageEntry(key, row)
    if len(heap) < limit:
        heapq.heappush(heap, entry)
        return
    if key < heap[0].key:
        heapq.heapreplace(heap, entry)


def streamed_ordered_page(
    candidates: Any,
    *,
    filters: list[dict[str, Any]],
    layer: str,
    offset: int,
    page_size: int,
    sort_keys: list[dict[str, Any]],
    sort_scope: str,
    randomize_browse: bool,
    browse_seed: int,
) -> tuple[int, int, list[dict[str, Any]], dict[str, int] | None]:
    limit = offset + page_size
    dominant = get_dominant_lemma_filter(filters)
    ranking = {"exact": 0, "phrase": 0, "manual": False} if dominant else None
    heap: list[WorstFirstPageEntry] = []
    total = 0
    scanned = 0

    for item in candidates:
        scanned += 1
        row = json.loads(item["row_json"])
        if not row_matches_filters(row, filters, layer):
            continue
        total += 1
        tier = 2
        if dominant:
            tier = lemma_tier(row, dominant)
            if tier == 0:
                ranking["exact"] += 1
            elif tier == 1:
                ranking["phrase"] += 1
        if randomize_browse and not filters and not sort_keys:
            key = browse_order_key(row, browse_seed)
        else:
            key = priority_sort_key(row, tier)
        add_page_candidate(heap, key, row, limit)

    page_rows = [entry.row for entry in sorted(heap, key=lambda entry: entry.key)[offset:offset + page_size]]
    if sort_keys and sort_scope == "page":
        page_rows.sort(key=cmp_to_key(manual_sort_compare(sort_keys)))
        if ranking:
            ranking["manual"] = True
    if ranking and ranking["exact"] == 0 and ranking["phrase"] == 0:
        ranking = None
    return total, scanned, page_rows, ranking


def manual_sort_compare(sort_keys: list[dict[str, Any]]):
    normalized_keys = [
        {
            "field": str(item.get("field", "")),
            "dir": "desc" if str(item.get("dir", "asc")).lower() == "desc" else "asc",
        }
        for item in sort_keys
        if isinstance(item, dict) and str(item.get("field", "")) in SEARCH_FIELDS
    ]

    def compare(a: dict[str, Any], b: dict[str, Any]) -> int:
        for item in normalized_keys:
            key_a = natural_key(display_sort_value(a, item["field"]))
            key_b = natural_key(display_sort_value(b, item["field"]))
            if key_a < key_b:
                return -1 if item["dir"] == "asc" else 1
            if key_a > key_b:
                return 1 if item["dir"] == "asc" else -1
        if record_id_sort_key(a) < record_id_sort_key(b):
            return -1
        if record_id_sort_key(a) > record_id_sort_key(b):
            return 1
        return 0

    return compare


def ordered_page(
    rows: list[dict[str, Any]],
    *,
    filters: list[dict[str, Any]],
    offset: int,
    page_size: int,
    sort_keys: list[dict[str, Any]],
    sort_scope: str,
    randomize_browse: bool,
    browse_seed: int,
) -> tuple[list[dict[str, Any]], dict[str, int] | None]:
    ranking, tiers = build_ranking(filters, rows)
    if randomize_browse and not filters and not sort_keys:
        ordered = sorted(rows, key=lambda row: browse_order_key(row, browse_seed))
        return ordered[offset:offset + page_size], ranking

    def ranked_key(row: dict[str, Any]) -> tuple[Any, ...]:
        row_id = str(row.get("record_id") or row.get("_rid") or "")
        return priority_sort_key(row, tiers.get(row_id, 2))

    if sort_keys:
        if sort_scope == "page":
            page = sorted(rows, key=ranked_key)[offset:offset + page_size]
            page.sort(key=cmp_to_key(manual_sort_compare(sort_keys)))
            if ranking:
                ranking = {**ranking, "manual": True}
            return page, ranking
        ordered = sorted(rows, key=cmp_to_key(manual_sort_compare(sort_keys)))
        if ranking:
            ranking = {**ranking, "manual": True}
        return ordered[offset:offset + page_size], ranking

    ordered = sorted(rows, key=ranked_key)
    return ordered[offset:offset + page_size], ranking


def split_fuente_label(name: Any) -> tuple[str, str]:
    text = str(name or "")
    match = re.match(r"^(\S+)(?:\s+(\?))?\s+(.+)$", text)
    if match and re.search(r"\d", match.group(1)):
        year = " ".join(part for part in (match.group(1), match.group(2)) if part)
        return year, match.group(3)
    return "", text


def normalize_fuente_sort_text(value: Any) -> str:
    return re.sub(r"[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", "", str(value or "")).strip()


def fuente_sort_key(value: Any) -> tuple[tuple[tuple[int, Any], ...], ...]:
    year, title = split_fuente_label(value)
    parts = [
        normalize_fuente_sort_text(title) or build_sort_key(title),
        normalize_fuente_sort_text(year) or build_sort_key(year),
    ]
    return tuple(natural_key(part) for part in parts if part)


def clean_display_text(row: dict[str, Any], field: str) -> str:
    return collapse_spaces(strip_html_tags(normalized_display_value(row, field)))


def browse_displayed_translation(row: dict[str, Any]) -> str:
    return clean_display_text(row, "Traducción")


def browse_normalized_translation(row: dict[str, Any]) -> str:
    return collapse_spaces(strip_punctuation_characters(normalize_string(normalized_display_value(row, "Traducción"))))


def add_lemma_dossier_entry(
    stats: dict[str, dict[str, Any]],
    key: str,
    display: str,
    row: dict[str, Any],
) -> None:
    if not key or not display:
        return
    entry = stats.get(key)
    if entry is None:
        entry = {"display": display, "count": 0, "sources": set()}
        stats[key] = entry
    entry["count"] += 1
    source = clean_display_text(row, "Fuente")
    if source:
        entry["sources"].add(source)


def ranked_lemma_dossier_entries(stats: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    entries = list(stats.values())
    entries.sort(key=lambda item: (-int(item.get("count") or 0), natural_key(item.get("display") or "")))
    return [
        {
            "display": item.get("display", ""),
            "count": int(item.get("count") or 0),
            "sources": sorted(item.get("sources") or [], key=fuente_sort_key),
        }
        for item in entries
    ]


def collect_browse_translations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stats: dict[str, dict[str, Any]] = {}
    for row in rows:
        normalized = browse_normalized_translation(row)
        display = browse_displayed_translation(row)
        if not normalized or not display:
            continue
        entry = stats.get(normalized)
        if entry:
            entry["count"] += 1
        else:
            stats[normalized] = {"display": display, "normalized": normalized, "count": 1}
    ranked = sorted(stats.values(), key=lambda item: (-int(item.get("count") or 0), natural_key(item.get("normalized") or "")))
    return {
        "count": len(stats),
        "sample": [str(item.get("display") or "") for item in ranked[:3]],
    }


def collect_lemma_translation_clusters(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for row in rows:
        add_lemma_dossier_entry(stats, browse_normalized_translation(row), browse_displayed_translation(row), row)
    return ranked_lemma_dossier_entries(stats)


def add_lemma_summary_row(groups: dict[str, dict[str, Any]], row: dict[str, Any]) -> None:
    lemma = collapse_spaces(str(normalized_display_value(row, "Editado") or ""))
    if not lemma:
        return
    group = groups.get(lemma)
    if group is None:
        group = {
            "lemma": lemma,
            "rowCount": 0,
            "sources": set(),
            "_translationStats": {},
            "_clusterStats": {},
        }
        groups[lemma] = group
    group["rowCount"] += 1
    source = str(row.get("Fuente") or "")
    if source:
        group["sources"].add(source)
    normalized = browse_normalized_translation(row)
    display = browse_displayed_translation(row)
    if normalized and display:
        translation_stats = group["_translationStats"]
        entry = translation_stats.get(normalized)
        if entry:
            entry["count"] += 1
        else:
            translation_stats[normalized] = {"display": display, "normalized": normalized, "count": 1}
        add_lemma_dossier_entry(group["_clusterStats"], normalized, display, row)


def sort_lemma_summary_items(items: list[dict[str, Any]], sort_keys: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lemma_sort_key = next(
        (
            item for item in sort_keys
            if isinstance(item, dict) and str(item.get("field", "")) == "Editado"
        ),
        None,
    )
    if lemma_sort_key:
        reverse = str(lemma_sort_key.get("dir", "asc")).lower() == "desc"
        items.sort(key=lambda item: natural_key(item.get("lemma") or ""), reverse=reverse)
    else:
        items.sort(key=lambda item: (-int(item.get("sourceCount") or 0), -int(item.get("rowCount") or 0), natural_key(item.get("lemma") or "")))
    return items


def finalize_lemma_summary_items(groups: dict[str, dict[str, Any]], sort_keys: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for group in groups.values():
        translation_stats = group.get("_translationStats") or {}
        ranked_translations = sorted(
            translation_stats.values(),
            key=lambda item: (-int(item.get("count") or 0), natural_key(item.get("normalized") or "")),
        )
        sources = sorted(group.get("sources") or [], key=fuente_sort_key)
        items.append({
            "lemma": group.get("lemma") or "",
            "sources": sources,
            "sourceCount": len(sources),
            "rowCount": int(group.get("rowCount") or 0),
            "translationCount": len(translation_stats),
            "sampleTranslations": [str(item.get("display") or "") for item in ranked_translations[:3]],
            "translationClusters": ranked_lemma_dossier_entries(group.get("_clusterStats") or {}),
        })
    return sort_lemma_summary_items(items, sort_keys)


def stream_lemma_summary_items(
    candidates: Any,
    *,
    filters: list[dict[str, Any]],
    layer: str,
    sort_keys: list[dict[str, Any]],
) -> tuple[int, int, list[dict[str, Any]]]:
    groups: dict[str, dict[str, Any]] = {}
    row_total = 0
    scanned = 0
    for item in candidates:
        scanned += 1
        row = json.loads(item["row_json"])
        if not row_matches_filters(row, filters, layer):
            continue
        row_total += 1
        add_lemma_summary_row(groups, row)
    return row_total, scanned, finalize_lemma_summary_items(groups, sort_keys)


def lemma_row_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        parse_priority(row.get("prio")),
        natural_key(build_sort_key(normalized_display_value(row, "Original"))),
        record_id_sort_key(row),
    )


def build_lemma_items(rows: list[dict[str, Any]], sort_keys: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        lemma = collapse_spaces(str(normalized_display_value(row, "Editado") or ""))
        if not lemma:
            continue
        grouped.setdefault(lemma, []).append(row)

    child_sort_keys = [
        item for item in sort_keys
        if isinstance(item, dict) and str(item.get("field", "")) != "Editado"
    ]
    items: list[dict[str, Any]] = []
    for lemma, lemma_rows in grouped.items():
        sorted_rows = list(lemma_rows)
        if child_sort_keys:
            sorted_rows.sort(key=cmp_to_key(manual_sort_compare(child_sort_keys)))
        else:
            sorted_rows.sort(key=lemma_row_sort_key)
        sources = sorted({str(row.get("Fuente") or "") for row in sorted_rows if row.get("Fuente")}, key=fuente_sort_key)
        translations = collect_browse_translations(sorted_rows)
        items.append({
            "lemma": lemma,
            "rows": sorted_rows,
            "sources": sources,
            "sourceCount": len(sources),
            "rowCount": len(sorted_rows),
            "translationCount": int(translations.get("count") or 0),
            "sampleTranslations": translations.get("sample") or [],
            "translationClusters": collect_lemma_translation_clusters(sorted_rows),
        })

    return sort_lemma_summary_items(items, sort_keys)


def lemma_item_payload(item: dict[str, Any], include_rows: bool = False) -> dict[str, Any]:
    payload = {
        key: value
        for key, value in item.items()
        if key != "rows"
    }
    if include_rows:
        payload["rows"] = item.get("rows") or []
        payload["detailRowsIncluded"] = True
    else:
        payload["detailRowsIncluded"] = False
    return payload


def sorted_lemma_detail_rows(
    rows: list[dict[str, Any]],
    lemma: str,
    sort_keys: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lemma = collapse_spaces(str(lemma or ""))
    detail_rows = [
        row for row in rows
        if collapse_spaces(str(normalized_display_value(row, "Editado") or "")) == lemma
    ]
    child_sort_keys = [
        item for item in sort_keys
        if isinstance(item, dict) and str(item.get("field", "")) != "Editado"
    ]
    if child_sort_keys:
        detail_rows.sort(key=cmp_to_key(manual_sort_compare(child_sort_keys)))
    else:
        detail_rows.sort(key=lemma_row_sort_key)
    return detail_rows


def search_database(
    db_path: Path,
    *,
    filters: list[dict[str, Any]],
    fuentes: list[str],
    layer: str,
    offset: int,
    page_size: int,
    accent_sensitive: bool = False,
    old_spanish: bool = False,
    sort_keys: list[dict[str, Any]] | None = None,
    sort_scope: str = "all",
    randomize_browse: bool = False,
    browse_seed: int = 0,
    view_mode: str = "rows",
) -> dict[str, Any]:
    layer = layer if layer in {"both", "normalized", "source"} else "both"
    view_mode = "lemmas" if view_mode == "lemmas" else "rows"
    offset = max(0, offset)
    page_size = min(max(1, page_size), 500)
    sort_keys = sort_keys if isinstance(sort_keys, list) else []
    sort_scope = "page" if sort_scope == "page" else "all"
    filters = compile_filter_items(filters, accent_sensitive, old_spanish)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    sql, args, can_limit_in_sql = candidate_sql(filters, fuentes, layer)
    if view_mode == "rows" and can_limit_in_sql and not sort_keys and not randomize_browse:
        if fuentes:
            total = con.execute(
                f"SELECT COUNT(*) FROM rows r WHERE r.fuente IN ({','.join('?' for _ in fuentes)})",
                args,
            ).fetchone()[0]
        else:
            total = con.execute("SELECT COUNT(*) FROM rows").fetchone()[0]
        page_sql = sql + " LIMIT ? OFFSET ?"
        rows = [json.loads(item["row_json"]) for item in con.execute(page_sql, [*args, page_size, offset])]
        con.close()
        return response_payload(total, offset, page_size, rows, "sql-page")

    if view_mode == "rows" and not (sort_keys and sort_scope == "all"):
        total, scanned, page_rows, ranking = streamed_ordered_page(
            con.execute(sql, args),
            filters=filters,
            layer=layer,
            offset=offset,
            page_size=page_size,
            sort_keys=sort_keys,
            sort_scope=sort_scope,
            randomize_browse=randomize_browse,
            browse_seed=browse_seed,
        )
        con.close()
        payload = response_payload(total, offset, page_size, page_rows, "streamed-page")
        payload["scannedCandidates"] = scanned
        payload["ranking"] = ranking
        return payload

    if view_mode == "lemmas":
        row_total, scanned, lemma_items = stream_lemma_summary_items(
            con.execute(sql, args),
            filters=filters,
            layer=layer,
            sort_keys=sort_keys,
        )
        con.close()
        total_lemmas = len(lemma_items)
        page_items = [lemma_item_payload(item) for item in lemma_items[offset:offset + page_size]]
        payload = response_payload(total_lemmas, offset, page_size, [], "lemma-summaries")
        payload["viewMode"] = "lemmas"
        payload["rowTotal"] = row_total
        payload["lemmaItems"] = page_items
        payload["ids"] = [item.get("lemma") for item in page_items if item.get("lemma")]
        payload["scannedCandidates"] = scanned
        return payload

    total = 0
    matched_rows: list[dict[str, Any]] = []
    scanned = 0
    for item in con.execute(sql, args):
        scanned += 1
        row = json.loads(item["row_json"])
        if not row_matches_filters(row, filters, layer):
            continue
        matched_rows.append(row)
        total += 1
    con.close()

    page_rows, ranking = ordered_page(
        matched_rows,
        filters=filters,
        offset=offset,
        page_size=page_size,
        sort_keys=sort_keys,
        sort_scope=sort_scope,
        randomize_browse=randomize_browse,
        browse_seed=browse_seed,
    )
    payload = response_payload(total, offset, page_size, page_rows, "fts-candidates")
    payload["scannedCandidates"] = scanned
    payload["ranking"] = ranking
    return payload


def fetch_lemma_detail(
    db_path: Path,
    *,
    lemma: str,
    filters: list[dict[str, Any]],
    fuentes: list[str],
    layer: str,
    accent_sensitive: bool = False,
    old_spanish: bool = False,
    sort_keys: list[dict[str, Any]] | None = None,
    sort_scope: str = "all",
) -> dict[str, Any]:
    layer = layer if layer in {"both", "normalized", "source"} else "both"
    sort_keys = sort_keys if isinstance(sort_keys, list) else []
    filters = compile_filter_items(filters, accent_sensitive, old_spanish)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    sql, args, _can_limit_in_sql = candidate_sql(filters, fuentes, layer)
    target_lemma = collapse_spaces(str(lemma or ""))
    detail_rows: list[dict[str, Any]] = []
    scanned = 0
    for item in con.execute(sql, args):
        scanned += 1
        row = json.loads(item["row_json"])
        if not row_matches_filters(row, filters, layer):
            continue
        if collapse_spaces(str(normalized_display_value(row, "Editado") or "")) != target_lemma:
            continue
        detail_rows.append(row)
    con.close()
    rows = sorted_lemma_detail_rows(detail_rows, target_lemma, sort_keys)
    return {
        "backend": BACKEND_ID,
        "strategy": "lemma-detail",
        "lemma": target_lemma,
        "rowCount": len(rows),
        "scannedCandidates": scanned,
        "ids": [row.get("record_id") for row in rows if row.get("record_id")],
        "rows": public_rows_payload(rows),
    }


def response_payload(total: int, offset: int, page_size: int, rows: list[dict[str, Any]], strategy: str) -> dict[str, Any]:
    public_rows = public_rows_payload(rows)
    return {
        "backend": BACKEND_ID,
        "strategy": strategy,
        "total": total,
        "offset": offset,
        "pageSize": page_size,
        "ids": [row.get("record_id") for row in public_rows],
        "rows": public_rows,
    }


def export_display_value(row: dict[str, Any], field: str, display_layer: str) -> str:
    field = field if field in SEARCH_FIELDS else "Editado"
    if display_layer == "source" and field in LAYERED_FIELDS:
        return source_raw_value(row, field) or normalized_display_value(row, field)
    return normalized_display_value(row, field)


def export_rows(
    db_path: Path,
    *,
    filters: list[dict[str, Any]],
    fuentes: list[str],
    layer: str,
    accent_sensitive: bool = False,
    old_spanish: bool = False,
    sort_keys: list[dict[str, Any]] | None = None,
    sort_scope: str = "all",
    randomize_browse: bool = False,
    browse_seed: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    layer = layer if layer in {"both", "normalized", "source"} else "both"
    sort_keys = sort_keys if isinstance(sort_keys, list) else []
    sort_scope = "page" if sort_scope == "page" else "all"
    filters = compile_filter_items(filters, accent_sensitive, old_spanish)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    sql, args, _can_limit_in_sql = candidate_sql(filters, fuentes, layer)
    rows: list[dict[str, Any]] = []
    scanned = 0
    for item in con.execute(sql, args):
        scanned += 1
        row = json.loads(item["row_json"])
        if filters and not row_matches_filters(row, filters, layer):
            continue
        rows.append(row)
    con.close()
    if rows:
        rows, _ranking = ordered_page(
            rows,
            filters=filters,
            offset=0,
            page_size=len(rows),
            sort_keys=sort_keys,
            sort_scope=sort_scope,
            randomize_browse=randomize_browse,
            browse_seed=browse_seed,
        )
    return rows, scanned


def export_csv_text(
    db_path: Path,
    *,
    filters: list[dict[str, Any]],
    fuentes: list[str],
    layer: str,
    columns: list[str],
    labels: list[str],
    display_layer: str = "normalized",
    accent_sensitive: bool = False,
    old_spanish: bool = False,
    sort_keys: list[dict[str, Any]] | None = None,
    sort_scope: str = "all",
    randomize_browse: bool = False,
    browse_seed: int = 0,
) -> str:
    safe_columns = [str(item) for item in columns if str(item) in SEARCH_FIELDS]
    if not safe_columns:
        safe_columns = ["Editado", "Original", "Traducción", "Comentario", "Fuente"]
    safe_labels = [str(item) for item in labels]
    if len(safe_labels) != len(safe_columns):
        safe_labels = safe_columns[:]
    rows, _scanned = export_rows(
        db_path,
        filters=filters,
        fuentes=fuentes,
        layer=layer,
        accent_sensitive=accent_sensitive,
        old_spanish=old_spanish,
        sort_keys=sort_keys,
        sort_scope=sort_scope,
        randomize_browse=randomize_browse,
        browse_seed=browse_seed,
    )
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(safe_labels)
    for row in rows:
        writer.writerow([export_display_value(row, field, display_layer) for field in safe_columns])
    return "\ufeff" + out.getvalue()


def form_map_payload(form_map: dict[str, int]) -> list[list[Any]]:
    return sorted(form_map.items(), key=lambda item: (-item[1], natural_key(item[0])))


def pair_tokens(value: Any, word_only: bool) -> list[str]:
    raw = strip_html_tags(str(value or ""))
    if not raw.strip():
        return []
    cleaned = collapse_spaces(strip_punctuation_characters(raw))
    if not cleaned:
        return []
    if not word_only:
        return [cleaned]
    return [token for token in cleaned.split() if token]


def run_pair_finder(
    db_path: Path,
    *,
    filters: list[dict[str, Any]],
    fuentes: list[str],
    column: str,
    word_only: bool,
    suffixes: dict[str, str],
    accent_sensitive: bool = False,
    old_spanish: bool = False,
    layer: str = "both",
) -> dict[str, Any]:
    field = column if column in SEARCH_FIELDS else "Editado"
    filters = compile_filter_items(filters, accent_sensitive, old_spanish)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    sql, args, _can_limit_in_sql = candidate_sql(filters, fuentes, layer)
    normalized_suffixes = [
        (key, normalize_string(value))
        for key, value in suffixes.items()
        if key in {"first", "second", "third", "fourth"} and normalize_string(value)
    ]
    normalized_suffixes.sort(key=lambda item: len(item[1]), reverse=True)
    pair_map: dict[str, dict[str, dict[str, int]]] = {}
    scanned = 0
    for item in con.execute(sql, args):
        row = json.loads(item["row_json"])
        if filters and not row_matches_filters(row, filters, layer):
            continue
        scanned += 1
        for token in pair_tokens(row.get(field), word_only):
            cleaned = str(token).strip()
            normalized = normalize_string(cleaned)
            if not normalized:
                continue
            match = next((entry for entry in normalized_suffixes if normalized.endswith(entry[1])), None)
            if not match:
                continue
            key, suffix = match
            stem = normalized[: -len(suffix)]
            if not stem:
                continue
            entry = pair_map.setdefault(stem, {"first": {}, "second": {}, "third": {}, "fourth": {}})
            bucket = entry[key]
            bucket[cleaned] = bucket.get(cleaned, 0) + 1
    con.close()
    pairs = []
    for stem, entry in pair_map.items():
        if entry["first"] and entry["second"]:
            pairs.append({
                "stem": stem,
                "first": form_map_payload(entry["first"]),
                "second": form_map_payload(entry["second"]),
                "third": form_map_payload(entry["third"]),
                "fourth": form_map_payload(entry["fourth"]),
            })
    pairs.sort(key=lambda item: natural_key(item["stem"]))
    return {"backend": BACKEND_ID, "rows": scanned, "pairs": pairs}


def study_clean_text(value: Any) -> str:
    return collapse_spaces(strip_html_tags(str(value or ""))).strip()


def study_theme_index(value: str) -> dict[str, Any]:
    text = normalize_string(study_clean_text(value))
    return {
        "text": text,
        "tokens": set(re.split(r"[^\wÀ-ɏḀ-ỿ]+", text)),
    }


def study_term_matches_index(term_spec: dict[str, Any], index: dict[str, Any]) -> bool:
    term = str(term_spec.get("term") or "").strip()
    if not term:
        return False
    if term_spec.get("exact"):
        return term in index["tokens"]
    return term in index["text"]


def normalize_study_theme_terms(raw_terms: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_terms, list):
        return []
    terms: list[dict[str, Any]] = []
    for item in raw_terms:
        if isinstance(item, dict):
            raw = str(item.get("term") or "")
            explicit_exact = bool(item.get("exact"))
        else:
            raw = str(item or "")
            explicit_exact = False
        term = normalize_string(study_clean_text(raw)).strip()
        if not term:
            continue
        terms.append({
            "term": term,
            "exact": explicit_exact or (" " not in term and len(term) <= 4),
        })
    return terms


def study_group_matches_theme(group: dict[str, Any], theme_terms: list[dict[str, Any]]) -> bool:
    if not theme_terms:
        return True
    index = study_theme_index(group.get("translation_text", ""))
    return any(study_term_matches_index(term, index) for term in theme_terms)


def study_row_card_info(row: dict[str, Any], direction: str) -> tuple[str, str, str] | None:
    lemma = study_clean_text(normalized_display_value(row, "Editado"))
    if not lemma:
        return None
    key = normalize_string(lemma)
    if not key:
        return None
    translation = study_clean_text(normalized_display_value(row, "Traducción"))
    if not translation:
        return None
    # The browser still applies the detailed leak-masking rules for Spanish -> Nahuatl.
    # Server-side filtering only prevents obviously empty cards from being sampled.
    return lemma, key, translation


def study_group_has_card(group: dict[str, Any], direction: str) -> bool:
    return any(study_row_card_info(row, direction) for row in group.get("rows", []))


def run_study_sampler(
    db_path: Path,
    *,
    filters: list[dict[str, Any]],
    fuentes: list[str],
    accent_sensitive: bool = False,
    old_spanish: bool = False,
    layer: str = "both",
    direction: str = "nahuatlToSpanish",
    theme_terms: list[dict[str, Any]] | None = None,
    limit: int = 100,
    sample_limit: int = 300,
    max_rows: int = 2500,
    rows_per_group: int = 8,
    seed: int = 0,
    scope_only: bool = False,
) -> dict[str, Any]:
    layer = layer if layer in {"both", "normalized", "source"} else "both"
    direction = "spanishToNahuatl" if direction == "spanishToNahuatl" else "nahuatlToSpanish"
    limit = min(max(1, int(limit or 100)), 500)
    sample_limit = min(max(limit, int(sample_limit or limit * 3)), 1500)
    max_rows = min(max(0, int(max_rows or 0)), 5000)
    rows_per_group = min(max(1, int(rows_per_group or 1)), 25)
    filters = compile_filter_items(filters, accent_sensitive, old_spanish)
    theme_terms = normalize_study_theme_terms(theme_terms or [])

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    sql, args, _can_limit_in_sql = candidate_sql(filters, fuentes, layer)
    groups: dict[str, dict[str, Any]] = {}
    scanned = 0
    matched_rows = 0
    for item in con.execute(sql, args):
        scanned += 1
        row = json.loads(item["row_json"])
        if filters and not row_matches_filters(row, filters, layer):
            continue
        info = study_row_card_info(row, direction)
        lemma = study_clean_text(normalized_display_value(row, "Editado"))
        key = normalize_string(lemma)
        if not key:
            continue
        group = groups.setdefault(key, {
            "key": key,
            "rows": [],
            "translation_text": "",
        })
        group["rows"].append(row)
        translation = study_clean_text(normalized_display_value(row, "Traducción"))
        if translation:
            group["translation_text"] += f" {translation}"
        if info:
            matched_rows += 1
    con.close()

    scoped_groups = [group for group in groups.values() if study_group_matches_theme(group, theme_terms)]
    row_count = sum(len(group["rows"]) for group in scoped_groups)
    eligible_groups = [group for group in scoped_groups if study_group_has_card(group, direction)]
    possible_cards = len(eligible_groups)
    selected_rows: list[dict[str, Any]] = []
    if not scope_only and max_rows > 0 and eligible_groups:
        rng = random.Random(seed or None)
        selectable = eligible_groups[:]
        rng.shuffle(selectable)
        for group in selectable[:sample_limit]:
            group_rows = sorted(group["rows"], key=priority_sort_key)
            selected_rows.extend(group_rows[:rows_per_group])
            if len(selected_rows) >= max_rows:
                selected_rows = selected_rows[:max_rows]
                break

    return {
        "backend": BACKEND_ID,
        "strategy": "study-sampler",
        "scannedCandidates": scanned,
        "matchedRows": matched_rows,
        "rowCount": row_count,
        "possibleCards": possible_cards,
        "rows": [] if scope_only else public_rows_payload(selected_rows),
        "limit": limit,
    }


def request_to_search_payload(params: dict[str, list[str]], body: dict[str, Any] | None = None) -> dict[str, Any]:
    body = body or {}
    filters = body.get("filters")
    if not isinstance(filters, list):
        filters = filters_from_get_params(params)
    fuentes = body.get("fuentes")
    if not isinstance(fuentes, list):
        fuentes = [item for item in params.get("fuente", []) if item]
    layer = str(body.get("layer") or params.get("layer", params.get("l", ["both"]))[0])
    if layer == "o":
        layer = "source"
    elif layer == "e":
        layer = "normalized"
    accent_sensitive = bool(body.get("accentSensitive")) or params.get("a", [""])[0] == "s"
    old_spanish = (bool(body.get("oldSpanish")) or params.get("o", [""])[0] == "1") and not accent_sensitive
    offset = int(body.get("offset") or params.get("offset", ["0"])[0] or 0)
    page_size = int(body.get("pageSize") or params.get("pageSize", ["100"])[0] or 100)
    sort_keys = body.get("sortKeys") if isinstance(body.get("sortKeys"), list) else []
    sort_scope = str(body.get("sortScope") or "all")
    view_mode = str(body.get("viewMode") or "rows")
    randomize_browse = bool(body.get("randomizeBrowse"))
    try:
        browse_seed = int(body.get("browseSeed") or 0)
    except (TypeError, ValueError):
        browse_seed = 0
    return {
        "filters": filters,
        "fuentes": [str(item) for item in fuentes if item],
        "layer": layer,
        "offset": offset,
        "page_size": page_size,
        "accent_sensitive": accent_sensitive,
        "old_spanish": old_spanish,
        "sort_keys": sort_keys,
        "sort_scope": sort_scope,
        "view_mode": view_mode,
        "randomize_browse": randomize_browse,
        "browse_seed": browse_seed,
    }


def request_to_export_payload(body: dict[str, Any] | None = None) -> dict[str, Any]:
    body = body or {}
    search_payload = request_to_search_payload({}, body)
    columns = body.get("columns") if isinstance(body.get("columns"), list) else []
    labels = body.get("labels") if isinstance(body.get("labels"), list) else []
    display_layer = str(body.get("displayLayer") or "normalized")
    return {
        "filters": search_payload["filters"],
        "fuentes": search_payload["fuentes"],
        "layer": search_payload["layer"],
        "accent_sensitive": search_payload["accent_sensitive"],
        "old_spanish": search_payload["old_spanish"],
        "sort_keys": search_payload["sort_keys"],
        "sort_scope": search_payload["sort_scope"],
        "randomize_browse": search_payload["randomize_browse"],
        "browse_seed": search_payload["browse_seed"],
        "columns": [str(item) for item in columns],
        "labels": [str(item) for item in labels],
        "display_layer": "source" if display_layer == "source" else "normalized",
    }


def request_to_lemma_payload(body: dict[str, Any] | None = None) -> dict[str, Any]:
    body = body or {}
    search_payload = request_to_search_payload({}, body)
    return {
        "lemma": str(body.get("lemma") or ""),
        "filters": search_payload["filters"],
        "fuentes": search_payload["fuentes"],
        "layer": search_payload["layer"],
        "accent_sensitive": search_payload["accent_sensitive"],
        "old_spanish": search_payload["old_spanish"],
        "sort_keys": search_payload["sort_keys"],
        "sort_scope": search_payload["sort_scope"],
    }


def request_to_pair_payload(body: dict[str, Any] | None = None) -> dict[str, Any]:
    body = body or {}
    filters = body.get("filters") if isinstance(body.get("filters"), list) else []
    fuentes = body.get("fuentes") if isinstance(body.get("fuentes"), list) else []
    suffixes = body.get("suffixes") if isinstance(body.get("suffixes"), dict) else {}
    layer = str(body.get("layer") or "both")
    if layer == "o":
        layer = "source"
    elif layer == "e":
        layer = "normalized"
    accent_sensitive = bool(body.get("accentSensitive"))
    old_spanish = bool(body.get("oldSpanish")) and not accent_sensitive
    return {
        "filters": filters,
        "fuentes": [str(item) for item in fuentes if item],
        "column": str(body.get("column") or "Editado"),
        "word_only": bool(body.get("wordOnly", True)),
        "suffixes": {str(key): str(value) for key, value in suffixes.items()},
        "accent_sensitive": accent_sensitive,
        "old_spanish": old_spanish,
        "layer": layer,
    }


def request_to_study_payload(body: dict[str, Any] | None = None) -> dict[str, Any]:
    body = body or {}
    filters = body.get("filters") if isinstance(body.get("filters"), list) else []
    fuentes = body.get("fuentes") if isinstance(body.get("fuentes"), list) else []
    theme_terms = body.get("themeTerms") if isinstance(body.get("themeTerms"), list) else []
    layer = str(body.get("layer") or "both")
    if layer == "o":
        layer = "source"
    elif layer == "e":
        layer = "normalized"
    accent_sensitive = bool(body.get("accentSensitive"))
    old_spanish = bool(body.get("oldSpanish")) and not accent_sensitive

    def int_value(key: str, default: int) -> int:
        try:
            return int(body.get(key) or default)
        except (TypeError, ValueError):
            return default

    return {
        "filters": filters,
        "fuentes": [str(item) for item in fuentes if item],
        "accent_sensitive": accent_sensitive,
        "old_spanish": old_spanish,
        "layer": layer,
        "direction": str(body.get("direction") or "nahuatlToSpanish"),
        "theme_terms": theme_terms,
        "limit": int_value("limit", 100),
        "sample_limit": int_value("sampleLimit", 300),
        "max_rows": int_value("maxRows", 2500),
        "rows_per_group": int_value("rowsPerGroup", 8),
        "seed": int_value("seed", 0),
        "scope_only": bool(body.get("scopeOnly")),
    }


def relative_database_path(db_path: Path) -> str:
    try:
        return str(db_path.relative_to(ROOT))
    except ValueError:
        return str(db_path)


def health_payload(db_path: Path) -> dict[str, Any]:
    return {
        "ok": db_path.exists(),
        "backend": BACKEND_ID,
        "contractVersion": API_CONTRACT_VERSION,
        "searchEndpoint": SEARCH_API_PATH,
        "endpoints": list(API_ENDPOINTS),
        "database": relative_database_path(db_path),
    }


def source_slug(value: Any) -> str:
    text = normalize_string(str(value or ""))
    return re.sub(r"[^0-9a-z]+", "-", text).strip("-") or "source"


def sources_payload(db_path: Path) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT fuente, COUNT(*) AS row_count FROM rows GROUP BY fuente"
        ).fetchall()
    finally:
        con.close()
    sources = [
        {
            "name": str(fuente or ""),
            "slug": source_slug(fuente),
            "rowCount": int(row_count or 0),
        }
        for fuente, row_count in rows
        if fuente
    ]
    sources.sort(key=lambda item: natural_key(item["name"]))
    return {
        "backend": BACKEND_ID,
        "strategy": "source-metadata",
        "total": len(sources),
        "sources": sources,
    }


def is_no_store_path(path: str) -> bool:
    if path == "/api/health" or path in API_ENDPOINTS:
        return True
    clean = path.replace("\\", "/").lstrip("/")
    return clean in NO_STORE_STATIC_PATHS or any(clean.startswith(prefix) for prefix in NO_STORE_STATIC_PREFIXES)


class SearchHandler(SimpleHTTPRequestHandler):
    db_path = DB_PATH

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        if is_no_store_path(urlparse(self.path).path):
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json(health_payload(self.db_path))
            return
        if parsed.path == "/api/search":
            params = parse_qs(parsed.query)
            self.handle_search(params)
            return
        if parsed.path == "/api/sources":
            self.handle_sources()
            return
        if parsed.path in {"", "/", "/index.html"}:
            self.send_index()
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in API_POST_ENDPOINTS:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("content-length") or 0)
        body = {}
        if length:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        if parsed.path == "/api/export":
            self.handle_export(body)
            return
        if parsed.path == "/api/lemma":
            self.handle_lemma(body)
            return
        if parsed.path == "/api/study":
            self.handle_study(body)
            return
        if parsed.path == "/api/pairs":
            self.handle_pairs(body)
            return
        params = parse_qs(parsed.query)
        self.handle_search(params, body)

    def handle_sources(self) -> None:
        if not self.db_path.exists():
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Run: python3 resources/search_service.py build")
            return
        try:
            result = sources_payload(self.db_path)
        except Exception as exc:  # noqa: BLE001
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self.send_json(result)

    def handle_search(self, params: dict[str, list[str]], body: dict[str, Any] | None = None) -> None:
        if not self.db_path.exists():
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Run: python3 resources/search_service.py build")
            return
        try:
            payload = request_to_search_payload(params, body)
            result = search_database(self.db_path, **payload)
        except Exception as exc:  # noqa: BLE001
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self.send_json(result)

    def handle_lemma(self, body: dict[str, Any] | None = None) -> None:
        if not self.db_path.exists():
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Run: python3 resources/search_service.py build")
            return
        try:
            payload = request_to_lemma_payload(body)
            if not payload.get("lemma"):
                raise ValueError("lemma is required")
            result = fetch_lemma_detail(self.db_path, **payload)
        except Exception as exc:  # noqa: BLE001
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self.send_json(result)

    def handle_pairs(self, body: dict[str, Any] | None = None) -> None:
        if not self.db_path.exists():
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Run: python3 resources/search_service.py build")
            return
        try:
            payload = request_to_pair_payload(body)
            result = run_pair_finder(self.db_path, **payload)
        except Exception as exc:  # noqa: BLE001
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self.send_json(result)

    def handle_study(self, body: dict[str, Any] | None = None) -> None:
        if not self.db_path.exists():
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Run: python3 resources/search_service.py build")
            return
        try:
            payload = request_to_study_payload(body)
            result = run_study_sampler(self.db_path, **payload)
        except Exception as exc:  # noqa: BLE001
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self.send_json(result)

    def handle_export(self, body: dict[str, Any] | None = None) -> None:
        if not self.db_path.exists():
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Run: python3 resources/search_service.py build")
            return
        try:
            payload = request_to_export_payload(body)
            csv_text = export_csv_text(self.db_path, **payload)
        except Exception as exc:  # noqa: BLE001
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self.send_text(csv_text, "text/csv; charset=utf-8")

    def send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            return

    def send_text(self, text: str, content_type: str, status: int = HTTPStatus.OK) -> None:
        raw = text.encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            return

    def send_index(self) -> None:
        try:
            html_text = backend_index_html()
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        raw = html_text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def backend_index_html() -> str:
    html_text = (ROOT / "index.html").read_text(encoding="utf-8")
    html_text = html_text.replace(
        '<meta name="nahuatl-search-api" content="" />',
        f'<meta name="nahuatl-search-api" content="{SEARCH_API_PATH}" />',
        1,
    )
    return re.sub(r'\n\s*<script src="data/bootstrap\.js[^"]*"></script>', "", html_text, count=1)


def serve(db_path: Path, host: str, port: int, build_if_missing: bool) -> None:
    if build_if_missing and not db_path.exists():
        count = build_database(DATA_PATH, db_path)
        print(f"built {db_path} with {count} rows", flush=True)
    handler = type("ConfiguredSearchHandler", (SearchHandler,), {"db_path": db_path})
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"serving {ROOT} with /api/search on http://{host}:{port}", flush=True)
    httpd.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    build_p = sub.add_parser("build", help="Build data/search.sqlite from data/data.jsonl.gz")
    build_p.add_argument("--data", type=Path, default=DATA_PATH)
    build_p.add_argument("--db", type=Path, default=DB_PATH)
    serve_p = sub.add_parser("serve", help="Serve static files plus the /api/search backend")
    serve_p.add_argument("--db", type=Path, default=DB_PATH)
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8100)
    serve_p.add_argument("--build-if-missing", action="store_true")
    search_p = sub.add_parser("search", help="Run a one-off search against the SQLite backend")
    search_p.add_argument("query")
    search_p.add_argument("--field", default="Editado")
    search_p.add_argument("--mode", default="any")
    search_p.add_argument("--scope", default="word")
    search_p.add_argument("--layer", default="both")
    search_p.add_argument("--accent-sensitive", action="store_true")
    search_p.add_argument("--old-spanish", action="store_true")
    search_p.add_argument("--offset", type=int, default=0)
    search_p.add_argument("--page-size", type=int, default=10)
    search_p.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()

    if args.cmd == "build":
        count = build_database(args.data, args.db)
        print(f"built {args.db} with {count} rows")
        return 0
    if args.cmd == "serve":
        serve(args.db, args.host, args.port, args.build_if_missing)
        return 0
    if args.cmd == "search":
        result = search_database(
            args.db,
            filters=[{
                "field": FIELD_CODE_IN.get(args.field, args.field),
                "mode": args.mode,
                "scope": args.scope,
                "value": args.query,
                "logic": "AND",
                "negate": False,
            }],
            fuentes=[],
            layer=args.layer,
            offset=args.offset,
            page_size=args.page_size,
            accent_sensitive=args.accent_sensitive,
            old_spanish=args.old_spanish,
        )
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
