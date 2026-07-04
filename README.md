# Nahuatl Database Website

This app can still run as static files, but the recommended path for a very
large database, especially on mobile, is server-backed search:

> Backend owns search. Frontend only renders pages.

## Large/mobile run path

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

For large/mobile use, do not treat `file://.../index.html` or
`python3 -m http.server` as the main deployment path. Those modes leave the
browser responsible for static/offline data loading. The search service injects
`<meta name="nahuatl-search-api" content="/api/search" />`, which tells the
frontend to ask the backend for result pages. It also omits the static
`data/bootstrap.js` row sample so the first page is loaded through `/api/search`.

You can combine build and serve during local work:

```bash
python3 resources/search_service.py serve --build-if-missing --port 8100
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

Static lazy chunks are kept as an offline/static fallback. They are not the best
architecture for an extremely large mobile database.

Static fallback rules:

- `file://.../index.html` may use the static/offline fallback.
- `*.github.io` is treated as a static GitHub Pages deployment.
- Plain HTTP without `/api/search` is treated as missing the backend.
- To test the static fallback over HTTP, open with `?static=1` or `?offline=1`.

Static fallback assets are generated output. If you need them, rebuild them
locally:

```bash
python3 resources/build_lazy_data_assets.py
```

Do not treat `data/lazy/` as the normal deployment artifact for large/mobile
use.

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
