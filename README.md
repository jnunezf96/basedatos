# Nahuatl Database Website

This app is deployed as a static GitHub Pages site. The production path is:

> GitHub builds lazy search assets. The browser loads only thin indexes and the
> row chunks needed for the current page.

## GitHub Pages run path

The Pages workflow builds `data/lazy/` during deployment, then publishes a
static `_site` artifact. The generated lazy assets stay out of the source tree
because they are large build output.

Static search should use this order:

1. Search thin candidate indexes.
2. Compute the ids for the current page.
3. Load only the row chunks containing those ids.
4. Render only those rows.

The local backend is kept as a diagnostic/reference tool. It is not required for
the public GitHub Pages site.

## Local static verification

Rebuild lazy assets:

```bash
python3 resources/build_lazy_data_assets.py
```

Serve the static site:

```bash
python3 -m http.server 8131
```

Benchmark a share URL:

```bash
node resources/benchmark_static_share_url.mjs \
  'http://127.0.0.1:8131/index.html?static=1#/q?g=A:tr:w:a:0:v.t.;A:ed:w:e:0:%3F%3Fqui' \
  27 \
  '1571-molina-1:001300,1571-molina-1:001301,1571-molina-2:000836,1780-bnf-361:001248,1780-bnf-361:001251'
```

The benchmark checks correctness, full-data avoidance, full-index avoidance,
candidate hydration, heap, and lazy transfer.

## Local backend diagnostic

Build the local SQLite search database:

```bash
python3 resources/search_service.py build
```

Serve the app through the search service:

```bash
python3 resources/search_service.py serve --port 8100
```

Then open:

```text
http://127.0.0.1:8100/index.html
```

## Backend contract

In backend mode:

- `/api/sources` returns source names, slugs, and row counts for the source UI
  and shareable source routes before any row page is loaded. Backend mode uses
  those slugs instead of recomputing route slugs in the browser.
- `/api/search` returns `total`, current page rows, and lemma page data when
  needed.
- Ordinary row searches in the SQLite bridge stream the current page instead of
  keeping every matched row in memory.
- `/api/lemma` returns detail rows only when a backend lemma group is expanded.
- `/api/pairs` runs pair finding server-side.
- `/api/study` samples study-card rows server-side.
- `/api/export` creates CSV exports server-side.
- Row payloads are projected for rendering and omit cleanup metadata, QA fields,
  and source JSON blobs.
- Backend-served HTML loads the first visible page through `/api/search`, not
  through the static bootstrap row sample.
- The phone should not download `data/bootstrap.js`, `data/data.jsonl.gz`,
  `data/lazy/*`, or `search-worker.js` for normal search, pair, study, or CSV
  export flows.
- The service worker does not precache or runtime-cache full DB/static lazy
  search assets; those remain explicit fallback files rather than app-shell
  storage.
- The backend server marks `/api/*`, `data/data.jsonl.gz`, `data/lazy/*`, and
  `search-worker.js` as `no-store`, so browser caches do not retain the DB or
  fallback search indexes in normal backend deployments.

The detailed HTTP contract is in
[docs/backend-api-contract.md](docs/backend-api-contract.md). Treat that file as
the replaceability boundary for a future production search engine.

Static rules:

- `file://.../index.html` may use the static/offline fallback.
- `*.github.io` is treated as a static GitHub Pages deployment.
- Plain HTTP without `/api/search` is treated as missing the backend.
- To test the static fallback over HTTP, open with `?static=1` or `?offline=1`.

Static fallback assets are generated output. If you need them, rebuild them
locally:

```bash
python3 resources/build_lazy_data_assets.py
```

## Development rule

Avoid maintaining two search brains forever. Mini-language parsing, layer
selection, filters, sorting, ranking, old-Spanish normalization, and accent
rules should continue moving toward one authoritative backend implementation.
The frontend should mostly collect user intent, send a request, and render the
returned page.

In backend mode, the frontend should not pre-decide which filter expressions are
supported. It should send the active query to `/api/search` and let the backend
compile, run, or reject it.

Keep backend-bound filter serialization centralized in the frontend. If a
request needs active filters, it should use the shared API filter payload rather
than hand-building a second mapping.

The backend verifier reads reference mini-language cases from
`resources/backend_search_contract_cases.json`. If a grammar rule is
intentionally changed, update those backend contract cases with the new result
rather than copying the old behavior into another frontend search
implementation.

## Quick verification

After building `data/search.sqlite`, run the backend-mode verifier:

```bash
python3 resources/verify_backend_mode.py
```

To also exercise the live HTTP handler on a temporary local port:

```bash
python3 resources/verify_backend_mode.py --http
```

For browser verification, start `resources/search_service.py serve`, run a
search in the browser, and check the server/browser network activity:

- Expected on startup: `GET /api/sources`.
- Expected: `POST /api/search`.
- Expected for pair finder: `POST /api/pairs`.
- Expected for study cards: `POST /api/study`.
- Expected for CSV export: `POST /api/export`.
- Not expected in backend mode: `data/data.jsonl.gz`, `data/lazy/*`, or
  `search-worker.js`.
