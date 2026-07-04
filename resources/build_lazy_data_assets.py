#!/usr/bin/env python3
"""Build static fallback lazy-search assets from data/data.jsonl.gz.

These assets support static hosting, including GitHub Pages. The goal is to keep
the browser on thin indexes and page-sized row chunks instead of loading the
full database for ordinary searches.
"""

from __future__ import annotations

import gzip
import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
OUT_DIR = ROOT / "data" / "lazy"
MANIFEST_PATH = OUT_DIR / "manifest.json"
ROW_CHUNK_SIZE = 250

FIELDS = ("Editado", "Original", "Traducción", "Comentario")
LAYERED_FIELDS = {"Traducción", "Comentario"}
NGRAM_INDEX_FIELDS = set(FIELDS)
NGRAM_SIZE = 3
NGRAM_MAX_POSTINGS = 4000
NGRAM_SHARD_PREFIX = 1
SHORT_TOKEN_INDEX_FIELDS = set(FIELDS)
SHORT_TOKEN_MAX_SIZE = NGRAM_SIZE - 1
SHORT_TOKEN_SHARD_PREFIX = 1
WORD_EDGE_INDEX_FIELDS = {"Editado", "Original"}
WORD_EDGE_SIZE = NGRAM_SIZE
WORD_EDGE_SHARD_PREFIX = 1

RAW_LAYER_PREFIXES = {
    "Traducción": ("Traducción_raw", "Traduccion_raw"),
    "Comentario": (
        "Comentario_public_raw",
        "Comentario_wimmer_plus_html_raw",
        "Sahagun_Escolios_JSON_display_html_raw",
        "Comentario_raw",
    ),
}


def compact_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def strip_html_tags(value: str) -> str:
    return re.sub(r"<[^>]*>", " ", value)


def normalize_string(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def ngram_tokens(value: str) -> list[str]:
    normalized = normalize_string(strip_html_tags(value))
    return re.findall(r"[0-9a-z]+", normalized)


def ngrams_for_value(value: str) -> set[str]:
    grams: set[str] = set()
    for token in ngram_tokens(value):
        if len(token) < NGRAM_SIZE:
            continue
        for idx in range(0, len(token) - NGRAM_SIZE + 1):
            grams.add(token[idx : idx + NGRAM_SIZE])
    return grams


def short_tokens_for_value(value: str) -> set[str]:
    normalized = normalize_string(strip_html_tags(value))
    return {
        token
        for token in re.findall(r"[0-9a-z]+", normalized)
        if 0 < len(token) <= SHORT_TOKEN_MAX_SIZE
    }


def word_edges_for_value(value: str) -> dict[str, set[str]]:
    normalized = normalize_string(strip_html_tags(value))
    edges = {"prefix": set(), "suffix": set(), "prefixLen": set(), "suffixLen": set()}
    for token in re.findall(r"[0-9a-z]+", normalized):
        if len(token) < WORD_EDGE_SIZE:
            continue
        prefix = token[:WORD_EDGE_SIZE]
        suffix = token[-WORD_EDGE_SIZE:]
        token_len = len(token)
        edges["prefix"].add(prefix)
        edges["suffix"].add(suffix)
        edges["prefixLen"].add(f"{prefix}:{token_len}")
        edges["suffixLen"].add(f"{suffix}:{token_len}")
    return edges


def gzip_text_writer(path: Path):
    raw = gzip.GzipFile(filename=str(path), mode="wb", compresslevel=9, mtime=0)
    return raw


def write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip_text_writer(path) as gz:
        for row in rows:
            gz.write(compact_json(row).encode("utf-8"))
            gz.write(b"\n")
            count += 1
    return count


def read_rows() -> Iterable[dict[str, Any]]:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


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
    if not prefixes:
        return ""
    candidates: list[tuple[int, int, str]] = []
    for key in row:
        for rank, prefix in enumerate(prefixes):
            if key.startswith(prefix):
                candidates.append((rank, len(key), key))
                break
    for _rank, _length, key in sorted(candidates):
        value = row.get(key)
        if isinstance(value, (dict, list)) or value is None:
            continue
        text = str(value)
        if text.strip():
            return text
    return ""


def source_display_value(row: dict[str, Any], field: str) -> str:
    if field not in LAYERED_FIELDS:
        return normalized_display_value(row, field)
    raw = source_raw_value(row, field)
    return raw if raw.strip() else normalized_display_value(row, field)


def layer_value(row: dict[str, Any], field: str, layer: str) -> str:
    if layer == "source":
        return source_display_value(row, field)
    return normalized_display_value(row, field)


def remove_old_assets() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "rows").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "indexes").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "ngrams").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "short-tokens").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "word-edges").mkdir(parents=True, exist_ok=True)


def build_assets() -> dict[str, Any]:
    remove_old_assets()

    manifest: dict[str, Any] = {
        "version": "lazy-v1",
        "rowChunkSize": ROW_CHUNK_SIZE,
        "rowChunks": [],
        "meta": "lazy/meta.jsonl.gz",
        "indexes": {},
        "ngrams": {},
        "shortTokens": {},
        "wordEdges": {},
        "fields": list(FIELDS),
        "ngramSize": NGRAM_SIZE,
        "shortTokenMaxSize": SHORT_TOKEN_MAX_SIZE,
        "wordEdgeSize": WORD_EDGE_SIZE,
    }

    row_chunk: list[dict[str, Any]] = []
    row_chunk_idx = 0
    meta_rows: list[dict[str, Any]] = []
    index_rows: dict[tuple[str, str], list[dict[str, str]]] = {}
    ngram_rows: dict[tuple[str, str], dict[str, list[int]]] = {}
    short_token_rows: dict[tuple[str, str], dict[str, list[int]]] = {}
    word_edge_rows: dict[tuple[str, str, str], dict[str, list[int]]] = {}
    for field in FIELDS:
        layers = ("normalized", "source") if field in LAYERED_FIELDS else ("normalized",)
        for layer in layers:
            index_rows[(field, layer)] = []
            if field in NGRAM_INDEX_FIELDS:
                ngram_rows[(field, layer)] = {}
            if field in SHORT_TOKEN_INDEX_FIELDS:
                short_token_rows[(field, layer)] = {}
            if field in WORD_EDGE_INDEX_FIELDS:
                for kind in ("prefix", "suffix", "prefixLen", "suffixLen"):
                    word_edge_rows[(field, layer, kind)] = {}

    total = 0
    for total, row in enumerate(read_rows(), start=1):
        row_id = str(row.get("record_id") or f"row:{total:06d}")
        chunk_name = f"rows-{row_chunk_idx:04d}"
        meta_rows.append({
            "record_id": row_id,
            "Fuente": row.get("Fuente", ""),
            "Editado": row.get("Editado", ""),
            "prio": row.get("prio", ""),
            "eid": row.get("eid", ""),
            "_lazyChunk": chunk_name,
            "_lazyIndex": total - 1,
        })

        row_chunk.append(row)
        if len(row_chunk) >= ROW_CHUNK_SIZE:
            path = OUT_DIR / "rows" / f"{chunk_name}.jsonl.gz"
            write_jsonl_gz(path, row_chunk)
            manifest["rowChunks"].append({
                "id": chunk_name,
                "path": f"lazy/rows/{chunk_name}.jsonl.gz",
                "count": len(row_chunk),
            })
            row_chunk = []
            row_chunk_idx += 1

        for field in FIELDS:
            layers = ("normalized", "source") if field in LAYERED_FIELDS else ("normalized",)
            for layer in layers:
                value = layer_value(row, field, layer)
                if value:
                    index_rows[(field, layer)].append({"record_id": row_id, "value": value})
                    if field in NGRAM_INDEX_FIELDS:
                        for gram in ngrams_for_value(value):
                            ngram_rows[(field, layer)].setdefault(gram, []).append(total - 1)
                    if field in SHORT_TOKEN_INDEX_FIELDS:
                        for token in short_tokens_for_value(value):
                            short_token_rows[(field, layer)].setdefault(token, []).append(total - 1)
                    if field in WORD_EDGE_INDEX_FIELDS:
                        for kind, edges in word_edges_for_value(value).items():
                            for edge in edges:
                                word_edge_rows[(field, layer, kind)].setdefault(edge, []).append(total - 1)

    if row_chunk:
        chunk_name = f"rows-{row_chunk_idx:04d}"
        path = OUT_DIR / "rows" / f"{chunk_name}.jsonl.gz"
        write_jsonl_gz(path, row_chunk)
        manifest["rowChunks"].append({
            "id": chunk_name,
            "path": f"lazy/rows/{chunk_name}.jsonl.gz",
            "count": len(row_chunk),
        })

    write_jsonl_gz(OUT_DIR / "meta.jsonl.gz", meta_rows)
    manifest["totalRows"] = total

    for (field, layer), rows in index_rows.items():
        slug = {
            "Editado": "editado",
            "Original": "original",
            "Traducción": "traduccion",
            "Comentario": "comentario",
        }[field]
        path = OUT_DIR / "indexes" / f"{slug}-{layer}.jsonl.gz"
        write_jsonl_gz(path, rows)
        manifest["indexes"].setdefault(field, {})[layer] = {
            "path": f"lazy/indexes/{slug}-{layer}.jsonl.gz",
            "count": len(rows),
        }
        if field in NGRAM_INDEX_FIELDS:
            grams = {
                gram: postings
                for gram, postings in ngram_rows[(field, layer)].items()
                if len(postings) <= NGRAM_MAX_POSTINGS
            }
            shard_dir = OUT_DIR / "ngrams" / f"{slug}-{layer}-{NGRAM_SIZE}g"
            shard_groups: dict[str, dict[str, list[int]]] = {}
            for gram, postings in grams.items():
                shard = gram[:NGRAM_SHARD_PREFIX]
                shard_groups.setdefault(shard, {})[gram] = postings
            shard_manifest = {}
            for shard, shard_grams in sorted(shard_groups.items()):
                shard_path = shard_dir / f"{shard}.jsonl.gz"
                write_jsonl_gz(
                    shard_path,
                    ({"gram": gram, "rows": rows} for gram, rows in sorted(shard_grams.items())),
                )
                shard_manifest[shard] = f"lazy/ngrams/{slug}-{layer}-{NGRAM_SIZE}g/{shard}.jsonl.gz"
            manifest["ngrams"].setdefault(field, {})[layer] = {
                "count": len(grams),
                "size": NGRAM_SIZE,
                "maxPostings": NGRAM_MAX_POSTINGS,
                "shardPrefix": NGRAM_SHARD_PREFIX,
                "shards": shard_manifest,
            }
        if field in SHORT_TOKEN_INDEX_FIELDS:
            shard_dir = OUT_DIR / "short-tokens" / f"{slug}-{layer}-short"
            shard_groups: dict[str, dict[str, list[int]]] = {}
            for token, postings in short_token_rows[(field, layer)].items():
                shard = token[:SHORT_TOKEN_SHARD_PREFIX]
                shard_groups.setdefault(shard, {})[token] = postings
            shard_manifest = {}
            for shard, shard_tokens in sorted(shard_groups.items()):
                shard_path = shard_dir / f"{shard}.jsonl.gz"
                write_jsonl_gz(
                    shard_path,
                    ({"token": token, "rows": rows} for token, rows in sorted(shard_tokens.items())),
                )
                shard_manifest[shard] = f"lazy/short-tokens/{slug}-{layer}-short/{shard}.jsonl.gz"
            manifest["shortTokens"].setdefault(field, {})[layer] = {
                "count": sum(len(tokens) for tokens in shard_groups.values()),
                "maxSize": SHORT_TOKEN_MAX_SIZE,
                "shardPrefix": SHORT_TOKEN_SHARD_PREFIX,
                "shards": shard_manifest,
            }
        if field in WORD_EDGE_INDEX_FIELDS:
            for kind in ("prefix", "suffix", "prefixLen", "suffixLen"):
                shard_dir = OUT_DIR / "word-edges" / f"{slug}-{layer}-{kind}-{WORD_EDGE_SIZE}g"
                shard_groups: dict[str, dict[str, list[int]]] = {}
                for edge, postings in word_edge_rows[(field, layer, kind)].items():
                    shard = edge[:WORD_EDGE_SHARD_PREFIX]
                    shard_groups.setdefault(shard, {})[edge] = postings
                shard_manifest = {}
                for shard, shard_edges in sorted(shard_groups.items()):
                    shard_path = shard_dir / f"{shard}.jsonl.gz"
                    write_jsonl_gz(
                        shard_path,
                        ({"edge": edge, "rows": rows} for edge, rows in sorted(shard_edges.items())),
                    )
                    shard_manifest[shard] = (
                        f"lazy/word-edges/{slug}-{layer}-{kind}-{WORD_EDGE_SIZE}g/{shard}.jsonl.gz"
                    )
                layer_manifest = manifest["wordEdges"].setdefault(field, {}).setdefault(layer, {})
                layer_manifest[kind] = {
                    "count": sum(len(edges) for edges in shard_groups.values()),
                    "size": WORD_EDGE_SIZE,
                    "shardPrefix": WORD_EDGE_SHARD_PREFIX,
                    "shards": shard_manifest,
                }

    MANIFEST_PATH.write_text(compact_json(manifest) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    manifest = build_assets()
    print(
        f"wrote {manifest['totalRows']} rows, "
        f"{len(manifest['rowChunks'])} row chunks, "
        f"{sum(len(v) for v in manifest['indexes'].values())} indexes"
    )


if __name__ == "__main__":
    main()
