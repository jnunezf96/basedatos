#!/usr/bin/env python3
"""Verify the large/mobile backend-search contract.

Run this after building data/search.sqlite. It checks the source files that
select backend mode, then runs a small SQLite search and confirms the backend
returns only one page of rows.
"""

from __future__ import annotations

import argparse
import contextlib
import http.client
import importlib.util
import json
import re
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "search.sqlite"
BACKEND_CONTRACT_CASES_PATH = ROOT / "resources" / "backend_search_contract_cases.json"


def fail(message: str) -> None:
    raise AssertionError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def load_search_service() -> Any:
    path = ROOT / "resources" / "search_service.py"
    spec = importlib.util.spec_from_file_location("nahuatl_search_service", path)
    require(spec is not None and spec.loader is not None, "could not load search_service.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def backend_case_search_kwargs(case: dict[str, Any]) -> dict[str, Any]:
    request = case.get("request") or {}
    return {
        "filters": request.get("filters") if isinstance(request.get("filters"), list) else [],
        "fuentes": request.get("fuentes") if isinstance(request.get("fuentes"), list) else [],
        "layer": request.get("layer") or "both",
        "offset": int(request.get("offset") or 0),
        "page_size": int(request.get("pageSize") or request.get("page_size") or 10),
        "accent_sensitive": bool(request.get("accentSensitive")),
        "old_spanish": bool(request.get("oldSpanish")),
        "sort_keys": request.get("sortKeys") if isinstance(request.get("sortKeys"), list) else [],
        "sort_scope": request.get("sortScope") or "all",
        "randomize_browse": bool(request.get("randomizeBrowse")),
        "browse_seed": int(request.get("browseSeed") or 0),
        "view_mode": request.get("viewMode") or "rows",
    }


def assert_public_row_shape(row: dict[str, Any], context: str) -> None:
    public_fields = {
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
    public_prefixes = (
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
    extra = [
        key for key in row
        if key not in public_fields and not any(key.startswith(prefix) for prefix in public_prefixes)
    ]
    require(not extra, f"{context} should not expose internal row keys: {extra[:5]}")


def verify_backend_contract_cases(search_service: Any, db_path: Path) -> list[str]:
    cases = json.loads(BACKEND_CONTRACT_CASES_PATH.read_text(encoding="utf-8"))
    require(isinstance(cases, list) and cases, "backend search contract cases should be a non-empty list")
    names: set[str] = set()
    for case in cases:
        name = str(case.get("name") or "")
        require(name and name not in names, "backend search contract case names should be unique")
        names.add(name)
        result = search_service.search_database(db_path, **backend_case_search_kwargs(case))
        expected = case.get("expect") or {}
        if "total" in expected:
            require(
                result.get("total") == expected["total"],
                f"backend search contract case {name} should return expected total",
            )
        if "ids" in expected:
            require(
                result.get("ids") == expected["ids"],
                f"backend search contract case {name} should return expected ids",
            )
    return [f"SQLite backend satisfies {len(cases)} backend search contract cases"]


def verify_file_contracts() -> list[str]:
    checks: list[str] = []
    index_html = read_text("index.html")
    search_service = read_text("resources/search_service.py")
    script_js = read_text("script.js")
    sw_js = read_text("sw.js")
    gitignore = read_text(".gitignore")
    api_contract = read_text("docs/backend-api-contract.md")

    require(
        '<meta name="nahuatl-search-api" content="" />' in index_html,
        "static index.html should keep the search API meta tag blank",
    )
    checks.append("static HTML does not opt into backend mode by itself")

    require('BACKEND_ID = "sqlite-fts5"' in search_service, "search_service.py should identify the backend")
    require(
        'API_CONTRACT_VERSION = "backend-api-v1"' in search_service,
        "search_service.py should identify the backend API contract version",
    )
    require('SEARCH_API_PATH = "/api/search"' in search_service, "search_service.py should define /api/search")
    require('"/api/sources"' in search_service, "search_service.py should expose /api/sources")
    require('"/api/lemma"' in search_service, "search_service.py should expose /api/lemma")
    require('"/api/pairs"' in search_service, "search_service.py should expose /api/pairs")
    require('"/api/study"' in search_service, "search_service.py should expose /api/study")
    require('"/api/export"' in search_service, "search_service.py should expose /api/export")
    require("def health_payload" in search_service, "search_service.py should expose health contract metadata")
    require(
        'API_POST_ENDPOINTS = ("/api/search", "/api/lemma", "/api/pairs", "/api/study", "/api/export")' in search_service
        and 'NO_STORE_STATIC_PATHS = {"data/data.jsonl.gz", "search-worker.js"}' in search_service
        and 'NO_STORE_STATIC_PREFIXES = ("data/lazy/",)' in search_service
        and "def is_no_store_path(path: str) -> bool:" in search_service
        and 'self.send_header("Cache-Control", "no-store, max-age=0")' in search_service,
        "backend server should send no-store headers for API and large fallback search assets",
    )
    require(
        "def streamed_ordered_page(" in search_service
        and "class WorstFirstPageEntry" in search_service
        and 'response_payload(total, offset, page_size, page_rows, "streamed-page")' in search_service,
        "ordinary backend row searches should stream the current page instead of materializing all matched rows",
    )
    require("def sources_payload(db_path: Path)" in search_service, "backend should expose source metadata without frontend rows")
    checks.append("backend service exposes contract metadata plus source, search, lemma, pairs, study, and export endpoints")

    for marker in ("GET /api/health", "GET /api/sources", "POST /api/search", "POST /api/lemma", "POST /api/pairs", "POST /api/study", "POST /api/export"):
        require(marker in api_contract, f"backend API contract should document {marker}")
    require("contractVersion" in api_contract, "backend API contract should document contractVersion")
    require(
        "The frontend should serialize user intent" in api_contract,
        "backend API contract should keep filter semantics backend-owned",
    )
    checks.append("backend API contract documents replaceable production search boundary")

    require(
        'const SEARCH_API_DEFAULT_PATH = "/api/search";' in script_js,
        "script.js should use /api/search as its default backend path",
    )
    require(
        "function getSourcesApiEndpoint()" in script_js
        and "async function hydrateSourcesFromApi()" in script_js
        and "function replaceFuenteOptions(items)" in script_js,
        "frontend should hydrate source metadata from the backend when available",
    )
    require(
        "const apiSourceSlugs = new Map();" in script_js
        and "apiSourceSlugs.set(item.name, item.slug);" in script_js
        and "apiSourceSlugs.get(name) || slugifySourceName(name)" in script_js,
        "frontend should prefer backend-provided source slugs for share routes",
    )
    require(
        'function getSearchApiEndpoint()' in script_js,
        "script.js should discover an advertised search API endpoint",
    )
    require(
        "function isStaticFallbackMode()" in script_js
        and 'location.protocol === "file:"' in script_js
        and 'params.get("static")' in script_js
        and 'params.get("offline")' in script_js,
        "static fallback should be limited to file:// or explicit static/offline mode",
    )
    require(
        "function shouldRequireBackendSearch() {\n  return !getSearchApiEndpoint() && !isStaticFallbackMode();\n}" in script_js,
        "plain HTTP without /api/search should require the backend",
    )
    backend_startup = re.search(
        r"if \(shouldRequireBackendSearch\(\)\).*?const hasInitialRoute = .*?if \(getSearchApiEndpoint\(\)\).*?applyFuenteFilters\(\{ keepOffset: true \}\);.*?return;.*?const usedBootstrap = renderBootstrapRows\(\);",
        script_js,
        re.S,
    )
    require(
        backend_startup is not None,
        "backend startup should query /api/search before considering bootstrap rows",
    )
    require(
        "await hydrateSourcesFromApi();\n  buildSourceSlugMaps();\n  renderFuenteList();" in script_js,
        "backend startup should build source slugs before parsing hash routes",
    )
    require(
        "function scheduleFullDataLoad() {\n  if (getSearchApiEndpoint() || !isStaticFallbackMode()) return;" in script_js,
        "non-static backend mode should not schedule full data loading",
    )
    require(
        "function ensureFullDataLoad() {\n  if (getSearchApiEndpoint()) {" in script_js
        and "if (!isStaticFallbackMode()) {\n    renderBackendRequiredState();" in script_js,
        "non-static backend mode should not load data/data.jsonl.gz",
    )
    require(
        "function shouldUseLazyQueryPath() {\n  if (getSearchApiEndpoint() || !isStaticFallbackMode()) return false;" in script_js,
        "backend mode should not enter the static lazy-query path",
    )
    require(
        "areSearchApiSupportedFilters" not in script_js and "isSearchApiSupportedFilter" not in script_js,
        "backend mode should not duplicate backend filter support checks in the browser",
    )
    require(
        "function shouldUseSearchApiPath() {" in script_js
        and 'if (tableViewMode !== "rows" && tableViewMode !== "lemmas") return false;\n  return true;' in script_js,
        "backend mode should send row/lemma searches to /api/search without JS support gating",
    )
    require(
        "function getLemmaDetailApiEndpoint()" in script_js
        and "function queryLemmaDetailApi(payload)" in script_js
        and "async function ensureLemmaDetailRows(item)" in script_js,
        "backend lemma groups should fetch detail rows through /api/lemma on expansion",
    )
    require(
        "async function renderLemmaDetailRowsForExpandedGroup(groupRow, item, stripe)" in script_js
        and "renderLemmaDetailRowsForExpandedGroup(groupRow, item, stripe);" in script_js,
        "expanded backend lemma groups should use the shared on-demand detail renderer",
    )
    require(
        "function getApiFilterPayload(filters = activeFilters)" in script_js,
        "backend requests should share one frontend filter serializer",
    )
    require(
        "filters: getApiFilterPayload(activeFilters)" in script_js,
        "search/export requests should use the shared filter serializer",
    )
    require(
        "filters: useFilters ? getApiFilterPayload(activeFilters) : []" in script_js,
        "pair finder requests should use the shared filter serializer",
    )
    require(
        "filters: useCurrent ? getApiFilterPayload(activeFilters) : []" in script_js,
        "study requests should use the shared filter serializer",
    )
    require(
        "if (getSearchApiEndpoint()) {\n    renderActiveFilterChips();\n    renderSearchApiUnavailableState(options);\n    return;\n  }" in script_js,
        "backend mode should fail closed instead of falling back to browser search",
    )
    checks.append("frontend disables full-data/static lazy search and sends filters to backend authority")

    require(
        re.search(r"(?m)^data/lazy/?$", gitignore) is not None,
        "generated static lazy assets should be ignored",
    )
    require(
        re.search(r"(?m)^data/search\.sqlite\*$", gitignore) is not None,
        "generated SQLite search database should be ignored",
    )
    checks.append("generated search artifacts stay out of the normal worktree")

    match = re.search(r"const\s+CORE_ASSETS\s*=\s*\[(.*?)\];", sw_js, re.S)
    require(match is not None, "sw.js should define CORE_ASSETS")
    core_assets = match.group(1)
    require("data/bootstrap.js" not in core_assets, "service worker should not precache bootstrap rows")
    require("data/data.jsonl.gz" not in core_assets, "service worker should not precache full data")
    require("data/lazy" not in core_assets, "service worker should not precache lazy indexes")
    require("search-worker.js" not in core_assets, "service worker should not precache lazy search worker")
    require('url.pathname.startsWith("/api/")' in sw_js, "service worker should not cache backend API responses")
    require(
        "function isLargeSearchFallbackAsset(url)" in sw_js
        and 'path === "data/data.jsonl.gz"' in sw_js
        and 'path === "search-worker.js"' in sw_js
        and 'path.startsWith("data/lazy/")' in sw_js
        and "if (isLargeSearchFallbackAsset(url)) return;" in sw_js,
        "service worker should bypass runtime caching for full DB, lazy chunks, and fallback search worker",
    )
    checks.append("service worker keeps bootstrap/full/static search assets and API responses out of cache")

    return checks


def verify_database_smoke(db_path: Path) -> list[str]:
    require(db_path.exists(), f"missing {db_path.relative_to(ROOT)}; run resources/search_service.py build")
    search_service = load_search_service()
    health = search_service.health_payload(db_path)
    require(health.get("ok") is True, "health payload should report ok=true")
    require(health.get("backend") == "sqlite-fts5", "health payload should report sqlite-fts5")
    require(health.get("contractVersion") == "backend-api-v1", "health payload should report backend-api-v1")
    require(health.get("searchEndpoint") == "/api/search", "health payload should advertise /api/search")
    require(
        {"/api/sources", "/api/search", "/api/lemma", "/api/pairs", "/api/study", "/api/export"}.issubset(set(health.get("endpoints") or [])),
        "health payload should list backend endpoints",
    )
    sources = search_service.sources_payload(db_path)
    require(sources.get("backend") == "sqlite-fts5", "source metadata should run on backend")
    require(sources.get("strategy") == "source-metadata", "source metadata should report source-metadata strategy")
    require(sources.get("total", 0) >= 20, "source metadata should return source count")
    first_source = (sources.get("sources") or [None])[0]
    require(isinstance(first_source, dict), "source metadata should return source records")
    require(first_source.get("name") and first_source.get("slug"), "source metadata should include source name and slug")
    require(isinstance(first_source.get("rowCount"), int), "source metadata should include row count")
    nemi_filter = {
        "field": "Editado",
        "mode": "exact",
        "scope": "word",
        "value": "nemi",
        "logic": "AND",
        "negate": False,
    }
    result = search_service.search_database(
        db_path,
        filters=[nemi_filter],
        fuentes=[],
        layer="both",
        offset=0,
        page_size=3,
    )

    require(result.get("backend") == "sqlite-fts5", "search backend should be sqlite-fts5")
    require(result.get("strategy") == "streamed-page", "filtered row search should stream the requested page")
    require(result.get("total", 0) >= 3, "search should report a total result count")
    require(result.get("pageSize") == 3, "search response should preserve requested page size")
    require(len(result.get("ids") or []) == 3, "search response should return current page ids")
    require(len(result.get("rows") or []) == 3, "search response should return only current page rows")
    for row in result.get("rows") or []:
        assert_public_row_shape(row, "search response row")

    word_group_result = search_service.search_database(
        db_path,
        filters=[{
            "type": "wordGroup",
            "field": "Editado",
            "logic": "AND",
            "scope": "word",
            "expression": {
                "type": "group",
                "logic": "AND",
                "children": [
                    {"type": "condition", "mode": "starts", "value": "ne", "negate": False},
                    {"type": "condition", "mode": "ends", "value": "i", "negate": False},
                ],
            },
        }],
        fuentes=[],
        layer="both",
        offset=0,
        page_size=3,
    )
    require(word_group_result.get("backend") == "sqlite-fts5", "word-group search should run on backend")
    require(word_group_result.get("strategy") == "streamed-page", "word-group search should stream the requested page")
    require(word_group_result.get("total", 0) >= 3, "word-group search should report result count")
    require(len(word_group_result.get("rows") or []) == 3, "word-group search should return only current page rows")
    for row in word_group_result.get("rows") or []:
        assert_public_row_shape(row, "word-group response row")

    random_browse_result = search_service.search_database(
        db_path,
        filters=[],
        fuentes=[],
        layer="both",
        offset=0,
        page_size=3,
        randomize_browse=True,
        browse_seed=123,
    )
    require(random_browse_result.get("strategy") == "streamed-page", "random browse should stream the requested page")
    require(len(random_browse_result.get("rows") or []) == 3, "random browse should return only current page rows")
    for row in random_browse_result.get("rows") or []:
        assert_public_row_shape(row, "random browse row")

    con = sqlite3.connect(db_path)
    try:
        raw_heavy = con.execute("SELECT row_json FROM rows ORDER BY length(row_json) DESC LIMIT 1").fetchone()[0]
    finally:
        con.close()
    heavy_row = json.loads(raw_heavy)
    projected_heavy = search_service.public_row_payload(heavy_row)
    require(len(projected_heavy) < len(heavy_row), "public row projection should remove internal metadata from wide rows")
    assert_public_row_shape(projected_heavy, "projected wide row")
    require("Sentence_Source_JSON" not in projected_heavy, "public row projection should omit source JSON blobs")

    lemma_result = search_service.search_database(
        db_path,
        filters=[nemi_filter],
        fuentes=[],
        layer="both",
        offset=0,
        page_size=2,
        view_mode="lemmas",
    )
    require(lemma_result.get("viewMode") == "lemmas", "lemma search should return lemma view")
    require(len(lemma_result.get("lemmaItems") or []) == 2, "lemma search should return current page lemma groups")
    first_lemma = lemma_result["lemmaItems"][0]
    require(first_lemma.get("detailRowsIncluded") is False, "lemma page groups should omit detail rows")
    require("rows" not in first_lemma, "lemma page groups should not embed detail rows")
    lemma_detail = search_service.fetch_lemma_detail(
        db_path,
        lemma=first_lemma["lemma"],
        filters=[nemi_filter],
        fuentes=[],
        layer="both",
    )
    require(lemma_detail.get("backend") == "sqlite-fts5", "lemma detail should run on backend")
    require(lemma_detail.get("rowCount") == first_lemma.get("rowCount"), "lemma detail should return the group's row count")
    require(len(lemma_detail.get("rows") or []) == first_lemma.get("rowCount"), "lemma detail should return detail rows on demand")
    for row in lemma_detail.get("rows") or []:
        assert_public_row_shape(row, "lemma detail row")

    pairs_result = search_service.run_pair_finder(
        db_path,
        filters=[nemi_filter],
        fuentes=[],
        column="Editado",
        word_only=True,
        suffixes={"first": "i", "second": "ia"},
        layer="both",
    )
    require(pairs_result.get("backend") == "sqlite-fts5", "pair finder should run on backend")
    require(pairs_result.get("rows", 0) >= 1, "pair finder should scan filtered backend rows")
    require(isinstance(pairs_result.get("pairs"), list), "pair finder should return a pairs list")

    study_result = search_service.run_study_sampler(
        db_path,
        filters=[nemi_filter],
        fuentes=[],
        layer="both",
        limit=10,
        sample_limit=20,
        max_rows=50,
        scope_only=True,
    )
    require(study_result.get("backend") == "sqlite-fts5", "study sampler should run on backend")
    require(study_result.get("rowCount", 0) >= 1, "study sampler should count filtered backend rows")
    require(isinstance(study_result.get("possibleCards"), int), "study sampler should return card count")
    require(study_result.get("rows") == [], "study scope-only mode should not return sampled rows")

    study_rows_result = search_service.run_study_sampler(
        db_path,
        filters=[nemi_filter],
        fuentes=[],
        layer="both",
        limit=5,
        sample_limit=10,
        max_rows=10,
        scope_only=False,
        seed=1,
    )
    for row in study_rows_result.get("rows") or []:
        assert_public_row_shape(row, "study sample row")

    csv_text = search_service.export_csv_text(
        db_path,
        filters=[nemi_filter],
        fuentes=[],
        layer="both",
        columns=["Editado", "Original"],
        labels=["Editado", "Original"],
    )
    require(csv_text.startswith("\ufeffEditado,Original"), "CSV export should return a BOM-prefixed header")
    require(csv_text.count("\n") >= 2, "CSV export should return filtered data rows")

    return [
        "SQLite backend reports health and API contract metadata",
        "SQLite backend returns source metadata for frontend route/source UI setup",
        "SQLite backend returns total, ids, and one page of rows",
        "SQLite backend streams ordinary row pages without keeping every matched row",
        "SQLite backend projects API rows to public display/search-layer fields",
        "SQLite backend compiles a word-group filter without browser prevalidation",
        "SQLite backend keeps lemma pages lightweight and serves detail rows on demand",
        "SQLite backend owns pair finder, study scope, and CSV export smoke paths",
    ]


def verify_served_index_contract(search_service: Any) -> list[str]:
    html_text = search_service.backend_index_html()
    require(
        '<meta name="nahuatl-search-api" content="/api/search" />' in html_text,
        "served index should advertise /api/search",
    )
    require(
        '<meta name="nahuatl-search-api" content="" />' not in html_text,
        "served index should not keep the blank static search API meta tag",
    )
    require(
        "data/bootstrap.js" not in html_text,
        "served backend index should not include bootstrap rows",
    )
    return ["served index HTML advertises /api/search and omits bootstrap rows"]


def http_response(
    host: str,
    port: int,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    headers = {}
    raw_body = None
    if body is not None:
        raw_body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["content-type"] = "application/json"
    con = http.client.HTTPConnection(host, port, timeout=10)
    try:
        con.request(method, path, body=raw_body, headers=headers)
        response = con.getresponse()
        raw = response.read()
        response_headers = {key.lower(): value for key, value in response.getheaders()}
        return response.status, raw, response_headers
    finally:
        con.close()


def http_request(
    host: str,
    port: int,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> tuple[int, str]:
    status, raw, _headers = http_response(host, port, method, path, body)
    return status, raw.decode("utf-8")


def assert_no_store_headers(headers: dict[str, str], context: str) -> None:
    cache_control = headers.get("cache-control", "")
    require("no-store" in cache_control, f"{context} should send Cache-Control: no-store")
    require(headers.get("pragma", "").lower() == "no-cache", f"{context} should send Pragma: no-cache")
    require(headers.get("expires", "") == "0", f"{context} should send Expires: 0")


def verify_live_http_contract(search_service: Any, db_path: Path) -> list[str]:
    require(db_path.exists(), f"missing {db_path.relative_to(ROOT)}; run resources/search_service.py build")
    handler = type("VerifiedSearchHandler", (search_service.SearchHandler,), {"db_path": db_path})
    httpd = search_service.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    host, port = httpd.server_address
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        nemi_filter = {
            "field": "Editado",
            "mode": "exact",
            "scope": "word",
            "value": "nemi",
            "logic": "AND",
            "negate": False,
        }
        status, health_bytes, health_headers = http_response(host, port, "GET", "/api/health")
        require(status == 200, f"/api/health should return 200, got {status}")
        assert_no_store_headers(health_headers, "/api/health")
        health = json.loads(health_bytes.decode("utf-8"))
        require(health.get("ok") is True, "/api/health should report ok=true")
        require(health.get("backend") == "sqlite-fts5", "/api/health should report sqlite-fts5")
        require(health.get("contractVersion") == "backend-api-v1", "/api/health should report backend-api-v1")
        require(health.get("searchEndpoint") == "/api/search", "/api/health should advertise /api/search")
        require(
            {"/api/sources", "/api/search", "/api/lemma", "/api/pairs", "/api/study", "/api/export"}.issubset(set(health.get("endpoints") or [])),
            "/api/health should list backend endpoints",
        )

        status, sources_bytes, sources_headers = http_response(host, port, "GET", "/api/sources")
        require(status == 200, f"/api/sources should return 200, got {status}")
        assert_no_store_headers(sources_headers, "/api/sources")
        sources = json.loads(sources_bytes.decode("utf-8"))
        require(sources.get("backend") == "sqlite-fts5", "HTTP /api/sources should use sqlite-fts5")
        require(sources.get("strategy") == "source-metadata", "HTTP /api/sources should return source metadata")
        require(sources.get("total", 0) >= 20, "HTTP /api/sources should return source count")
        source_names = [item.get("name") for item in sources.get("sources") or [] if isinstance(item, dict)]
        require("1645 Carochi" in source_names, "HTTP /api/sources should include source names")

        status, html_text = http_request(host, port, "GET", "/index.html")
        require(status == 200, f"/index.html should return 200, got {status}")
        require(
            '<meta name="nahuatl-search-api" content="/api/search" />' in html_text,
            "HTTP-served index should advertise /api/search",
        )
        require("data/bootstrap.js" not in html_text, "HTTP-served index should not include bootstrap rows")

        status, search_bytes, search_headers = http_response(host, port, "POST", "/api/search", {
            "filters": [nemi_filter],
            "offset": 0,
            "pageSize": 3,
        })
        require(status == 200, f"/api/search should return 200, got {status}")
        assert_no_store_headers(search_headers, "/api/search")
        result = json.loads(search_bytes.decode("utf-8"))
        require(result.get("backend") == "sqlite-fts5", "HTTP /api/search should use sqlite-fts5")
        require(result.get("strategy") == "streamed-page", "HTTP /api/search should stream filtered rows")
        require(result.get("total", 0) >= 3, "HTTP /api/search should return a total")
        require(len(result.get("ids") or []) == 3, "HTTP /api/search should return current page ids")
        require(len(result.get("rows") or []) == 3, "HTTP /api/search should return only current page rows")
        for row in result.get("rows") or []:
            assert_public_row_shape(row, "HTTP /api/search row")

        status, lemma_raw = http_request(host, port, "POST", "/api/search", {
            "filters": [nemi_filter],
            "viewMode": "lemmas",
            "offset": 0,
            "pageSize": 2,
        })
        require(status == 200, f"HTTP lemma /api/search should return 200, got {status}")
        lemma_result = json.loads(lemma_raw)
        lemma_item = (lemma_result.get("lemmaItems") or [None])[0]
        require(isinstance(lemma_item, dict), "HTTP lemma search should return lemma groups")
        require(lemma_item.get("detailRowsIncluded") is False, "HTTP lemma search should omit detail rows")
        require("rows" not in lemma_item, "HTTP lemma search should not embed detail rows")

        status, lemma_detail_raw = http_request(host, port, "POST", "/api/lemma", {
            "filters": [nemi_filter],
            "lemma": lemma_item.get("lemma"),
        })
        require(status == 200, f"/api/lemma should return 200, got {status}")
        lemma_detail = json.loads(lemma_detail_raw)
        require(lemma_detail.get("backend") == "sqlite-fts5", "HTTP /api/lemma should use sqlite-fts5")
        require(lemma_detail.get("rowCount") == lemma_item.get("rowCount"), "HTTP /api/lemma should return detail row count")
        require(len(lemma_detail.get("rows") or []) == lemma_item.get("rowCount"), "HTTP /api/lemma should return detail rows")
        for row in lemma_detail.get("rows") or []:
            assert_public_row_shape(row, "HTTP /api/lemma row")

        status, pairs_raw = http_request(host, port, "POST", "/api/pairs", {
            "filters": [nemi_filter],
            "column": "Editado",
            "wordOnly": True,
            "suffixes": {"first": "i", "second": "ia"},
        })
        require(status == 200, f"/api/pairs should return 200, got {status}")
        pairs = json.loads(pairs_raw)
        require(pairs.get("backend") == "sqlite-fts5", "HTTP /api/pairs should use sqlite-fts5")
        require(pairs.get("rows", 0) >= 1, "HTTP /api/pairs should scan filtered backend rows")
        require(isinstance(pairs.get("pairs"), list), "HTTP /api/pairs should return pair list")

        status, study_raw = http_request(host, port, "POST", "/api/study", {
            "filters": [nemi_filter],
            "limit": 10,
            "sampleLimit": 20,
            "maxRows": 50,
            "scopeOnly": True,
        })
        require(status == 200, f"/api/study should return 200, got {status}")
        study = json.loads(study_raw)
        require(study.get("backend") == "sqlite-fts5", "HTTP /api/study should use sqlite-fts5")
        require(study.get("rowCount", 0) >= 1, "HTTP /api/study should count filtered backend rows")
        require(study.get("rows") == [], "HTTP /api/study scopeOnly should not return rows")

        status, csv_text = http_request(host, port, "POST", "/api/export", {
            "filters": [nemi_filter],
            "columns": ["Editado", "Original"],
            "labels": ["Editado", "Original"],
        })
        require(status == 200, f"/api/export should return 200, got {status}")
        require(csv_text.startswith("\ufeffEditado,Original"), "HTTP /api/export should return CSV header")
        require(csv_text.count("\n") >= 2, "HTTP /api/export should return filtered data rows")

        for path in ("/data/data.jsonl.gz", "/search-worker.js"):
            status, _raw, headers = http_response(host, port, "HEAD", path)
            require(status == 200, f"HEAD {path} should return 200, got {status}")
            assert_no_store_headers(headers, path)

        return [
            "live HTTP backend reports health/source metadata and serves search, lemma detail, pair, study, and export paths",
            "live HTTP backend marks API and large fallback search assets no-store",
        ]
    finally:
        with contextlib.suppress(Exception):
            httpd.shutdown()
        with contextlib.suppress(Exception):
            httpd.server_close()
        thread.join(timeout=5)


def verify_browser_backend_network_contract(search_service: Any, db_path: Path) -> list[str]:
    require(db_path.exists(), f"missing {db_path.relative_to(ROOT)}; run resources/search_service.py build")
    proof_script = ROOT / "resources" / "browser_backend_network_proof.mjs"
    require(proof_script.exists(), "missing browser backend network proof script")
    handler = type("BrowserVerifiedSearchHandler", (search_service.SearchHandler,), {"db_path": db_path})
    httpd = search_service.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    host, port = httpd.server_address
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://{host}:{port}/index.html"
        result = subprocess.run(
            ["node", str(proof_script), url],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        if result.returncode != 0:
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            detail = "\n".join(part for part in (stdout, stderr) if part)
            fail(f"browser backend network proof failed\n{detail}")
        return [line.removeprefix("ok - ") for line in result.stdout.splitlines() if line.startswith("ok - ")]
    finally:
        with contextlib.suppress(Exception):
            httpd.shutdown()
        with contextlib.suppress(Exception):
            httpd.server_close()
        thread.join(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--skip-db", action="store_true", help="Only verify source-file contracts")
    parser.add_argument("--http", action="store_true", help="Also verify a temporary live HTTP server")
    parser.add_argument("--browser", action="store_true", help="Also verify backend-mode browser network requests with headless Chrome")
    args = parser.parse_args()

    checks = verify_file_contracts()
    search_service = load_search_service()
    checks.extend(verify_served_index_contract(search_service))
    if not args.skip_db:
        checks.extend(verify_database_smoke(args.db))
        checks.extend(verify_backend_contract_cases(search_service, args.db))
    if args.http:
        checks.extend(verify_live_http_contract(search_service, args.db))
    if args.browser:
        checks.extend(verify_browser_backend_network_contract(search_service, args.db))

    for check in checks:
        print(f"ok - {check}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"error - {exc}", file=sys.stderr)
        raise SystemExit(1)
