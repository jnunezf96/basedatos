# Backend API Contract

This is the frontend/backend boundary for large/mobile deployments. A future
Postgres, Tantivy, or Meilisearch service should satisfy this contract without
requiring the frontend to regain search ownership.

## Runtime Discovery

Backend-served `index.html` must advertise the search endpoint:

```html
<meta name="nahuatl-search-api" content="/api/search" />
```

Static HTML keeps that value blank. Plain HTTP without this backend endpoint is
treated as missing the backend unless the user explicitly opens `?static=1` or
`?offline=1`.

Backend-served HTML should not include `data/bootstrap.js`. The first visible
result page should come from `/api/search`, even for an unfiltered browse.

## `GET /api/health`

Response:

- `ok`: whether the backend database is available.
- `backend`: backend identifier, currently `sqlite-fts5`.
- `contractVersion`: API contract identifier, currently `backend-api-v1`.
- `searchEndpoint`: advertised search endpoint, currently `/api/search`.
- `endpoints`: available backend endpoints.
- `database`: backend database path for local diagnostics.

Clients can use this as a cheap runtime sanity check. The frontend still uses
the HTML meta tag as its normal discovery mechanism.

Service workers or other app-shell caches must not precache bootstrap rows,
full data, lazy indexes, or search workers for backend mode. They also must not
runtime-cache full data, lazy indexes, or the fallback search worker if those
assets are requested in static/offline mode. They also must not cache `/api/*`
responses. Search state is authoritative on the backend and should be fetched
fresh.

Backend HTTP responses for `/api/*`, `/api/health`, `data/data.jsonl.gz`,
`data/lazy/*`, and `search-worker.js` should include `Cache-Control: no-store`
plus no-cache compatibility headers. Static fallback files can exist, but the
large/mobile backend path should not encourage browser or app-shell storage of
database/search assets.

## `GET /api/sources`

This endpoint returns source metadata needed for source chips, fuente counts,
and shareable `#/fuente/...` routes before any row data is loaded. Source
slugs are backend-owned in backend mode; the frontend computes slugs only as a
static fallback.

Response:

- `backend`: backend identifier.
- `strategy`: `source-metadata`.
- `total`: number of sources.
- `sources`: array of `{ name, slug, rowCount }`.

## Shared Request Fields

Backend requests use these common fields where relevant:

- `filters`: array of active filter payloads from the shared frontend
  serializer.
- `fuentes`: selected source labels; empty means all sources.
- `layer`: `both`, `normalized`, or `source`.
- `accentSensitive`: boolean.
- `oldSpanish`: boolean, ignored when `accentSensitive` is true.

Filter payloads are backend-owned. The frontend should serialize user intent,
not decide whether the mini-language is supported.

Row objects returned by backend APIs are public render payloads, not full
database records. They should include display fields, `record_id`/`prio`, and
needed translation/commentary source-layer raw fields, while omitting cleanup
metadata, QA fields, and source JSON blobs.

## `POST /api/search`

Additional request fields:

- `viewMode`: `rows` or `lemmas`.
- `offset`: zero-based result offset.
- `pageSize`: requested page size.
- `sortKeys`: array of `{ field, dir }`.
- `sortScope`: `all` or `page`.
- `randomizeBrowse`: boolean.
- `browseSeed`: integer.

Rows response:

- `backend`: backend identifier.
- `strategy`: backend strategy label. The SQLite bridge uses `streamed-page`
  for ordinary row searches that count matches while retaining only the
  requested page.
- `total`: total matching rows.
- `offset`: echoed offset.
- `pageSize`: effective page size.
- `ids`: current page record ids.
- `rows`: current page row objects only.
- `ranking`: optional ranking summary.
- `scannedCandidates`: optional diagnostic count.

Lemma response adds:

- `viewMode`: `lemmas`.
- `rowTotal`: total rows represented by matching lemmas.
- `lemmaItems`: current page lemma groups only.
- `detailRowsIncluded`: false on each lemma group in backend mode.

Backend lemma pages should include summary metadata only. Detail rows for a
collapsed lemma group are fetched on demand.

## `POST /api/lemma`

Additional request fields:

- `lemma`: exact lemma label from a `/api/search` lemma item.
- common search fields accepted by `/api/search`.

Response:

- `backend`: backend identifier.
- `strategy`: backend strategy label.
- `lemma`: echoed lemma.
- `rowCount`: detail rows for that lemma inside the current filter scope.
- `ids`: detail row record ids.
- `rows`: detail row objects, loaded only when the user expands that lemma.

## `POST /api/pairs`

Additional request fields:

- `column`: searched field.
- `wordOnly`: boolean.
- `suffixes`: `{ first, second, third, fourth }`.

Response:

- `backend`: backend identifier.
- `rows`: number of matching backend rows considered.
- `pairs`: array of pair groups with form/count entries.

## `POST /api/study`

Additional request fields:

- `direction`: `nahuatlToSpanish` or `spanishToNahuatl`.
- `themeTerms`: optional study theme terms.
- `limit`, `sampleLimit`, `maxRows`, `rowsPerGroup`, `seed`.
- `scopeOnly`: when true, return counts without sampled rows.

Response:

- `backend`: backend identifier.
- `strategy`: backend strategy label.
- `rowCount`: matching rows in study scope.
- `possibleCards`: possible study-card groups.
- `rows`: sampled row objects, or `[]` for `scopeOnly`.

## `POST /api/export`

Additional request fields:

- `columns`: exported field keys.
- `labels`: CSV header labels.
- `displayLayer`: `normalized` or `source`.
- sort/browse fields accepted by `/api/search`.

Response:

- UTF-8 CSV text with BOM.
- CSV is produced server-side from the filtered backend result set.

## Verification

Run:

```bash
python3 resources/verify_backend_mode.py
python3 resources/verify_backend_mode.py --http
```

The verifier protects the backend discovery path, health contract metadata,
page-row response shape, streamed row-page selection, public row projection,
lightweight lemma pages plus on-demand lemma detail, mini-language reference behavior from
`resources/backend_search_contract_cases.json`, pair finder, study scope, CSV
export, and the fact that generated search artifacts are not normal deployment
files.
