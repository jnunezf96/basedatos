#!/usr/bin/env python3
"""Build static fallback lazy-search assets from data/data.jsonl.gz.

These assets support static hosting, including GitHub Pages. The goal is to keep
the browser on thin indexes and page-sized row chunks instead of loading the
full database for ordinary searches.
"""

from __future__ import annotations

import gzip
import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
from itertools import zip_longest
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


def publish_manifest(manifest: dict[str, Any]) -> None:
    """Publish only after every referenced asset is complete."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=OUT_DIR,
                                     prefix=".manifest-", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(compact_json(manifest) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, MANIFEST_PATH)
    finally:
        temporary.unlink(missing_ok=True)


def build_display_projections(manifest: dict[str, Any], *, study: bool = False) -> dict[str, Any]:
    """Add sparse Pair raw or Study source-display projections.

    Search indexes contain display values, which can differ from Pair raw
    fields or Study source-display fallback. Validate the existing metadata against the source before any
    writes; publish immutable assets first and the manifest atomically last.
    """
    fields = ("Traducción",) if study else FIELDS
    directory = "study-source" if study else "pair-raw"
    if manifest.get("version") != "lazy-v1":
        raise ValueError("Unsupported lazy manifest version for display projections")
    if type(manifest.get("totalRows")) is not int or manifest["totalRows"] < 0:
        raise ValueError("Invalid lazy manifest row count for display projections")
    if not isinstance(manifest.get("meta"), str) or not manifest["meta"]:
        raise ValueError("Missing lazy metadata path for display projections")
    with DATA_PATH.open("rb") as handle:
        source_digest = hashlib.file_digest(handle, "sha256").hexdigest()
    projections: dict[str, list[dict[str, str]]] = {field: [] for field in fields}
    sources: dict[str, set[str]] = {field: set() for field in fields}
    meta_path = ROOT / "data" / manifest["meta"]
    total = 0
    with gzip.open(meta_path, "rt", encoding="utf-8") as handle:
        metadata = (json.loads(line) for line in handle if line.strip())
        for total, (row, meta) in enumerate(zip_longest(read_rows(), metadata), start=1):
            if row is None or meta is None:
                raise ValueError("Display projection source and metadata row counts differ")
            row_id = str(row.get("record_id") or f"row:{total:06d}")
            if row_id != meta.get("record_id") or row.get("Fuente", "") != meta.get("Fuente", ""):
                raise ValueError(f"Display projection source identity differs at row {total}")
            for field in fields:
                value = row.get(field)
                raw = "" if value is None else str(value)
                # Study source display falls back to the original field, unlike
                # the search source layer which falls back to normalized display.
                if study:
                    raw = source_raw_value(row, field) or raw
                indexed = layer_value(row, field, "source") if study else normalized_display_value(row, field)
                if raw != indexed:
                    projections[field].append({"record_id": row_id, "value": raw})
                    sources[field].add(str(row.get("Fuente", "")))
    if total != manifest.get("totalRows"):
        raise ValueError("Display projection source count differs from manifest")
    with DATA_PATH.open("rb") as handle:
        if hashlib.file_digest(handle, "sha256").hexdigest() != source_digest:
            raise ValueError("Display projection source changed while reading")

    entries = {field: {"count": 0, "sources": []} for field in fields}
    projection_dir = OUT_DIR / directory
    projection_dir.mkdir(parents=True, exist_ok=True)
    for field, rows in projections.items():
        if not rows:
            continue
        slug = {"Editado": "editado", "Original": "original", "Traducción": "traduccion", "Comentario": "comentario"}[field]
        with tempfile.NamedTemporaryFile(dir=projection_dir, prefix=".projection-", delete=False) as handle:
            temporary = Path(handle.name)
            try:
                with gzip.GzipFile(filename="", fileobj=handle, mode="wb", compresslevel=9, mtime=0) as compressed:
                    for row in rows:
                        compressed.write((compact_json(row) + "\n").encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            with temporary.open("rb") as handle:
                digest = hashlib.file_digest(handle, "sha256").hexdigest()
            name = f"{slug}-{digest[:16]}.jsonl.gz"
            target = projection_dir / name
            if target.exists():
                if target.read_bytes() != temporary.read_bytes():
                    raise ValueError("Display projection content digest collision")
            else:
                os.replace(temporary, target)
            entries[field] = {"path": f"lazy/{directory}/{name}", "count": len(rows),
                              "sources": sorted(sources[field]), "sha256": digest}
        finally:
            temporary.unlink(missing_ok=True)
    updated = ({**manifest, "studyDisplayProjectionVersion": 1,
                "studySourceDisplayOverrides": entries, "studyProjectionSourceSha256": source_digest}
               if study else
               {**manifest, "pairProjectionVersion": 1, "pairRawOverrides": entries,
                "pairProjectionSourceSha256": source_digest})
    publish_manifest(updated)
    return updated


def build_pair_projections(manifest: dict[str, Any]) -> dict[str, Any]:
    return build_display_projections(manifest)


def build_study_projections(manifest: dict[str, Any]) -> dict[str, Any]:
    return build_display_projections(manifest, study=True)


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

    return build_study_projections(build_pair_projections(manifest))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    projection_mode = parser.add_mutually_exclusive_group()
    projection_mode.add_argument("--study-projections-only", action="store_true",
                                 help="Add Study source-display projections without rebuilding other lazy assets")
    projection_mode.add_argument("--pair-projections-only", action="store_true",
                        help="Validate and add raw Pair projections without rebuilding other lazy assets")
    args = parser.parse_args()
    if args.study_projections_only:
        manifest = build_study_projections(json.loads(MANIFEST_PATH.read_text(encoding="utf-8")))
        print(f"wrote Study source-display projections for {manifest['totalRows']} rows")
        return
    if args.pair_projections_only:
        manifest = build_pair_projections(json.loads(MANIFEST_PATH.read_text(encoding="utf-8")))
        print(f"wrote {sum(entry['count'] > 0 for entry in manifest['pairRawOverrides'].values())} Pair projections for {manifest['totalRows']} rows")
        return
    manifest = build_assets()
    print(
        f"wrote {manifest['totalRows']} rows, "
        f"{len(manifest['rowChunks'])} row chunks, "
        f"{sum(len(v) for v in manifest['indexes'].values())} indexes"
    )


if __name__ == "__main__":
    main()
