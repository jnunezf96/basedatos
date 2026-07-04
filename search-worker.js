// search-worker.js - off-main-thread lazy search engine.
//
// This worker reuses data.js + filters.js so the app's mini-language has a
// single implementation. It loads thin lazy indexes, verifies matches with the
// same matcher as the UI, and returns only the current page's lightweight rows.

importScripts("data.js", "filters.js");

const LAZY_DATA_MANIFEST_PATH = "data/lazy/manifest.json";
const FIELDS_WITH_LAZY_INDEX = new Set(["Editado", "Original", "Traducción", "Comentario"]);
const LAYERED_SEARCH_FIELDS = new Set(["Traducción", "Comentario", "Traducción (es)", "Comentario (es)"]);
const SEARCH_LAYER_MODES = new Set(["normalized", "source", "both"]);
const LAZY_ASSET_DB_NAME = "nahuatl-lazy-assets-v1";
const LAZY_ASSET_STORE = "assets";
const NGRAM_FULL_VERIFY_ROW_LIMIT = 2500;
const NGRAM_FULL_VERIFY_CHUNK_LIMIT = 90;
const RAW_LAYER_PREFIXES = {
  "Traducción": ["Traducción_raw", "Traduccion_raw"],
  "Traducción (es)": ["Traducción_es_raw", "Traduccion_es_raw", "Traducción_raw", "Traduccion_raw"],
  "Comentario": [
    "Comentario_public_raw",
    "Comentario_wimmer_plus_html_raw",
    "Sahagun_Escolios_JSON_display_html_raw",
    "Comentario_raw"
  ],
  "Comentario (es)": [
    "Comentario_es_raw",
    "Comentario_public_raw",
    "Comentario_wimmer_plus_html_raw",
    "Sahagun_Escolios_JSON_display_html_raw",
    "Comentario_raw"
  ]
};

let workerAssetVersion = "dev";
let searchLayerMode = "both";
let lazyDataManifest = null;
let lazyDataManifestPromise = null;
let lazyMetaRows = null;
let lazyMetaById = new Map();
let lazyMetaPromise = null;
let lazyIndexPromises = new Map();
let lazyLoadedIndexKeys = new Set();
let lazyNgramPromises = new Map();
let lazyLoadedNgramKeys = new Map();
let lazyShortTokenPromises = new Map();
let lazyLoadedShortTokenKeys = new Map();
let lazyWordEdgePromises = new Map();
let lazyLoadedWordEdgeKeys = new Map();
let lazyRowChunkPromises = new Map();
let lazyRowChunkCache = new Map();
let lazyRowChunkPaths = new Map();
let lazyDisplayRowsById = new Map();
let lazyCachePromise = null;
let emptyBrowseSeed = 0;
let prioritySortCache = new WeakMap();

const alphaNumCollator = new Intl.Collator("es", { numeric: true, sensitivity: "base" });

function getDataAssetUrl(dataPath) {
  const separator = dataPath.includes("?") ? "&" : "?";
  return `${dataPath}${separator}v=${encodeURIComponent(workerAssetVersion)}`;
}

function getLazyDataUrl(relativePath) {
  const clean = String(relativePath || "").replace(/^\/+/, "");
  const path = clean.startsWith("data/") ? clean : `data/${clean}`;
  return getDataAssetUrl(path);
}

function assetCacheKey(relativePath) {
  return `${workerAssetVersion}|${relativePath}`;
}

function openLazyAssetDb() {
  if (!("indexedDB" in self)) return Promise.resolve(null);
  if (lazyCachePromise) return lazyCachePromise;
  lazyCachePromise = new Promise(resolve => {
    const request = indexedDB.open(LAZY_ASSET_DB_NAME, 1);
    request.onupgradeneeded = () => {
      request.result.createObjectStore(LAZY_ASSET_STORE, { keyPath: "key" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => resolve(null);
    request.onblocked = () => resolve(null);
  });
  return lazyCachePromise;
}

async function readCachedRows(key) {
  const db = await openLazyAssetDb();
  if (!db) return null;
  return new Promise(resolve => {
    const tx = db.transaction(LAZY_ASSET_STORE, "readonly");
    const request = tx.objectStore(LAZY_ASSET_STORE).get(key);
    request.onsuccess = () => resolve(request.result?.rows || null);
    request.onerror = () => resolve(null);
  });
}

async function writeCachedRows(key, rows) {
  const db = await openLazyAssetDb();
  if (!db) return;
  try {
    await new Promise(resolve => {
      const tx = db.transaction(LAZY_ASSET_STORE, "readwrite");
      tx.objectStore(LAZY_ASSET_STORE).put({
        key,
        rows,
        savedAt: Date.now()
      });
      tx.oncomplete = () => resolve();
      tx.onerror = () => resolve();
      tx.onabort = () => resolve();
    });
  } catch {
    // Cache is opportunistic; quota or private-mode failures should not break search.
  }
}

async function loadJsonlRows(relativePath, options = {}) {
  const cacheKey = assetCacheKey(relativePath);
  if (options.cache !== false) {
    const cached = await readCachedRows(cacheKey);
    if (cached) return cached;
  }
  const rows = await loadCompressedJsonlRows(getLazyDataUrl(relativePath), options);
  if (options.cache !== false) writeCachedRows(cacheKey, rows);
  return rows;
}

async function loadCompressedJsonlRows(url, options = {}) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Data request failed with ${response.status}`);
  }
  if (!response.body) {
    return parseJsonlText(await response.text(), options);
  }

  let stream = response.body;
  const responseUrl = new URL(response.url || url, location.href);
  const isGzipFile = /\.gz$/i.test(responseUrl.pathname);
  const browserAlreadyInflated = /\bgzip\b/i.test(response.headers.get("content-encoding") || "");
  if (isGzipFile && !browserAlreadyInflated) {
    if (!("DecompressionStream" in self)) {
      throw new Error("This browser cannot decompress the data stream.");
    }
    stream = stream.pipeThrough(new DecompressionStream("gzip"));
  }

  const reader = stream.getReader();
  const decoder = new TextDecoder();
  const rows = [];
  let carry = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    carry += decoder.decode(value, { stream: true });
    const lines = carry.split("\n");
    carry = lines.pop() || "";
    for (const line of lines) {
      if (line) rows.push(JSON.parse(line));
    }
  }
  carry += decoder.decode();
  if (carry.trim()) rows.push(JSON.parse(carry));
  return rows;
}

function parseJsonlText(text) {
  const rows = [];
  for (const line of text.split("\n")) {
    if (line) rows.push(JSON.parse(line));
  }
  return rows;
}

async function ensureLazyDataManifest() {
  if (lazyDataManifest) return lazyDataManifest;
  if (!lazyDataManifestPromise) {
    lazyDataManifestPromise = fetch(getDataAssetUrl(LAZY_DATA_MANIFEST_PATH))
      .then(response => {
        if (!response.ok) throw new Error(`Lazy manifest request failed with ${response.status}`);
        return response.json();
      })
      .then(manifest => {
        lazyDataManifest = manifest;
        lazyRowChunkPaths = new Map((manifest.rowChunks || []).map(chunk => [chunk.id, chunk.path]));
        return manifest;
      });
  }
  return lazyDataManifestPromise;
}

function parsePriority(value) {
  if (value == null || value === "") return Number.POSITIVE_INFINITY;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : Number.POSITIVE_INFINITY;
}

function computeBrowseOrderKey(value) {
  const text = String(value ?? "");
  let hash = 2166136261 ^ emptyBrowseSeed;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function prepareLazyMetaRow(row, idx) {
  row._rid = row.record_id || idx;
  row._prio = parsePriority(row.prio);
  row._browseOrder = computeBrowseOrderKey(row.record_id || idx);
  row.__lazyMeta = true;
  row.__lazyLayers = row.__lazyLayers || {};
  return row;
}

async function ensureLazyMetaRows() {
  if (lazyMetaRows) return lazyMetaRows;
  if (!lazyMetaPromise) {
    lazyMetaPromise = ensureLazyDataManifest()
      .then(manifest => loadJsonlRows(manifest.meta))
      .then(rows => {
        lazyMetaById = new Map();
        rows.forEach((row, idx) => {
          prepareLazyMetaRow(row, idx);
          lazyMetaById.set(row.record_id, row);
        });
        lazyMetaRows = rows;
        return rows;
      });
  }
  return lazyMetaPromise;
}

function searchLayerAppliesToField(fieldKey) {
  return LAYERED_SEARCH_FIELDS.has(normalizeFieldKey(fieldKey));
}

function getDisplayBaseField(row, fieldKey) {
  const normalizedField = normalizeFieldKey(fieldKey);
  if (row.Fuente === "2021 Wimmer") {
    if (normalizedField === "Traducción" && row["Traducción (es)"]) return "Traducción (es)";
    if (normalizedField === "Comentario" && row["Comentario (es)"]) return "Comentario (es)";
  }
  return normalizedField;
}

function getNormalizedDisplayValue(row, fieldKey) {
  const normalizedField = normalizeFieldKey(fieldKey);
  const baseField = getDisplayBaseField(row, normalizedField);
  return row[baseField] ?? row[normalizedField] ?? row[fieldKey] ?? "";
}

function getSourceRawValue(row, fieldKey) {
  const prefixes = RAW_LAYER_PREFIXES[normalizeFieldKey(fieldKey)] || [];
  if (!prefixes.length) return "";
  const candidates = [];
  Object.keys(row || {}).forEach(key => {
    const rank = prefixes.findIndex(prefix => key.startsWith(prefix));
    if (rank === -1) return;
    candidates.push({ key, rank });
  });
  candidates.sort((a, b) =>
    a.rank - b.rank ||
    a.key.length - b.key.length ||
    alphaNumCollator.compare(a.key, b.key)
  );
  for (const candidate of candidates) {
    const value = row[candidate.key];
    if (value == null || typeof value === "object") continue;
    if (String(value).trim()) return value;
  }
  return "";
}

function getSourceDisplayValue(row, fieldKey) {
  const normalizedField = normalizeFieldKey(fieldKey);
  if (normalizedField !== "Traducción" && normalizedField !== "Comentario") {
    return row[normalizedField] ?? row[fieldKey] ?? "";
  }
  const raw = getSourceRawValue(row, normalizedField);
  if (raw) return raw;
  return getNormalizedDisplayValue(row, normalizedField);
}

function getSearchLayerModesForField(fieldKey) {
  const normalizedField = normalizeFieldKey(fieldKey);
  if (!searchLayerAppliesToField(normalizedField)) return ["normalized"];
  if (searchLayerMode === "both") return ["normalized", "source"];
  return [SEARCH_LAYER_MODES.has(searchLayerMode) ? searchLayerMode : "normalized"];
}

function getSearchDisplayValueForLayer(row, fieldKey, layer) {
  const normalizedField = normalizeFieldKey(fieldKey);
  const lazyLayer = row?.__lazyLayers?.[normalizedField];
  if (lazyLayer) {
    if (searchLayerAppliesToField(normalizedField) && layer === "source") {
      return lazyLayer.source ?? lazyLayer.normalized ?? row[normalizedField] ?? "";
    }
    return lazyLayer.normalized ?? row[normalizedField] ?? "";
  }
  return searchLayerAppliesToField(normalizedField) && layer === "source"
    ? getSourceDisplayValue(row, normalizedField)
    : getNormalizedDisplayValue(row, normalizedField);
}

function getSearchDisplayValue(row, fieldKey) {
  return getSearchDisplayValueForLayer(row, fieldKey, "normalized");
}

function getDisplayValue(row, fieldKey) {
  return getNormalizedDisplayValue(row, fieldKey);
}

function getLazyIndexManifestEntry(manifest, field, layer) {
  const fieldIndexes = manifest?.indexes?.[field];
  if (!fieldIndexes) return null;
  return fieldIndexes[layer] || fieldIndexes.normalized || null;
}

function getLazyIndexCacheKey(field, layer) {
  return `${field}::${layer}`;
}

function getLazyNgramCacheKey(field, layer) {
  return `${field}::${layer}`;
}

function getLazyNgramShardCacheKey(field, layer, shard) {
  return `${field}::${layer}::${shard}`;
}

function getLazyShortTokenShardCacheKey(field, layer, shard) {
  return `${field}::${layer}::${shard}`;
}

function getLazyWordEdgeShardCacheKey(field, layer, kind, shard) {
  return `${field}::${layer}::${kind}::${shard}`;
}

async function ensureLazyFieldIndex(field, layer) {
  const normalizedField = normalizeFieldKey(field);
  const effectiveLayer = searchLayerAppliesToField(normalizedField) ? layer : "normalized";
  const key = getLazyIndexCacheKey(normalizedField, effectiveLayer);
  if (lazyLoadedIndexKeys.has(key)) return;
  if (!lazyIndexPromises.has(key)) {
    lazyIndexPromises.set(key, Promise.all([ensureLazyDataManifest(), ensureLazyMetaRows()])
      .then(([manifest]) => {
        const entry = getLazyIndexManifestEntry(manifest, normalizedField, effectiveLayer);
        if (!entry?.path) throw new Error(`Missing lazy index for ${key}`);
        return loadJsonlRows(entry.path);
      })
      .then(rows => {
        rows.forEach(item => {
          const row = lazyMetaById.get(item.record_id);
          if (!row) return;
          row.__lazyLayers = row.__lazyLayers || {};
          const layerMap = row.__lazyLayers[normalizedField] || {};
          layerMap[effectiveLayer] = item.value || "";
          row.__lazyLayers[normalizedField] = layerMap;
          if (effectiveLayer === "normalized" && item.value != null) {
            row[normalizedField] = item.value;
          }
        });
        normalizationCache = new Map();
        lazyLoadedIndexKeys.add(key);
      }));
  }
  return lazyIndexPromises.get(key);
}

async function ensureLazyNgramShard(field, layer, shard) {
  const normalizedField = normalizeFieldKey(field);
  const effectiveLayer = searchLayerAppliesToField(normalizedField) ? layer : "normalized";
  const key = getLazyNgramShardCacheKey(normalizedField, effectiveLayer, shard);
  if (lazyLoadedNgramKeys.has(key)) return lazyLoadedNgramKeys.get(key);
  if (!lazyNgramPromises.has(key)) {
    lazyNgramPromises.set(key, ensureLazyDataManifest()
      .then(manifest => {
        const entry = manifest?.ngrams?.[normalizedField]?.[effectiveLayer];
        const path = entry?.shards?.[shard];
        if (!path) return null;
        return loadJsonlRows(path);
      })
      .then(rows => {
        if (!rows) return null;
        const map = new Map();
        rows.forEach(item => {
          if (item?.gram && Array.isArray(item.rows)) map.set(item.gram, item.rows);
        });
        lazyLoadedNgramKeys.set(key, map);
        return map;
      }));
  }
  return lazyNgramPromises.get(key);
}

async function ensureLazyShortTokenShard(field, layer, shard) {
  const normalizedField = normalizeFieldKey(field);
  const effectiveLayer = searchLayerAppliesToField(normalizedField) ? layer : "normalized";
  const key = getLazyShortTokenShardCacheKey(normalizedField, effectiveLayer, shard);
  if (lazyLoadedShortTokenKeys.has(key)) return lazyLoadedShortTokenKeys.get(key);
  if (!lazyShortTokenPromises.has(key)) {
    lazyShortTokenPromises.set(key, ensureLazyDataManifest()
      .then(manifest => {
        const entry = manifest?.shortTokens?.[normalizedField]?.[effectiveLayer];
        const path = entry?.shards?.[shard];
        if (!path) return null;
        return loadJsonlRows(path);
      })
      .then(rows => {
        if (!rows) return null;
        const map = new Map();
        rows.forEach(item => {
          if (item?.token && Array.isArray(item.rows)) map.set(item.token, item.rows);
        });
        lazyLoadedShortTokenKeys.set(key, map);
        return map;
      }));
  }
  return lazyShortTokenPromises.get(key);
}

async function ensureLazyWordEdgeShard(field, layer, kind, shard) {
  const normalizedField = normalizeFieldKey(field);
  const effectiveLayer = searchLayerAppliesToField(normalizedField) ? layer : "normalized";
  const key = getLazyWordEdgeShardCacheKey(normalizedField, effectiveLayer, kind, shard);
  if (lazyLoadedWordEdgeKeys.has(key)) return lazyLoadedWordEdgeKeys.get(key);
  if (!lazyWordEdgePromises.has(key)) {
    lazyWordEdgePromises.set(key, ensureLazyDataManifest()
      .then(manifest => {
        const entry = manifest?.wordEdges?.[normalizedField]?.[effectiveLayer]?.[kind];
        const path = entry?.shards?.[shard];
        if (!path) return null;
        return loadJsonlRows(path);
      })
      .then(rows => {
        if (!rows) return null;
        const map = new Map();
        rows.forEach(item => {
          if (item?.edge && Array.isArray(item.rows)) map.set(item.edge, item.rows);
        });
        lazyLoadedWordEdgeKeys.set(key, map);
        return map;
      }));
  }
  return lazyWordEdgePromises.get(key);
}

function getNgramShard(field, layer, gram) {
  const normalizedField = normalizeFieldKey(field);
  const effectiveLayer = searchLayerAppliesToField(normalizedField) ? layer : "normalized";
  const entry = lazyDataManifest?.ngrams?.[normalizedField]?.[effectiveLayer];
  const prefixLen = Number(entry?.shardPrefix) || 1;
  return gram.slice(0, prefixLen);
}

function getShortTokenShard(field, layer, token) {
  const normalizedField = normalizeFieldKey(field);
  const effectiveLayer = searchLayerAppliesToField(normalizedField) ? layer : "normalized";
  const entry = lazyDataManifest?.shortTokens?.[normalizedField]?.[effectiveLayer];
  const prefixLen = Number(entry?.shardPrefix) || 1;
  return token.slice(0, prefixLen);
}

function getWordEdgeShard(field, layer, kind, edge) {
  const normalizedField = normalizeFieldKey(field);
  const effectiveLayer = searchLayerAppliesToField(normalizedField) ? layer : "normalized";
  const entry = lazyDataManifest?.wordEdges?.[normalizedField]?.[effectiveLayer]?.[kind];
  const prefixLen = Number(entry?.shardPrefix) || 1;
  return edge.slice(0, prefixLen);
}

function hasUnescapedPipe(value) {
  let escaped = false;
  for (const ch of String(value || "")) {
    if (escaped) {
      escaped = false;
      continue;
    }
    if (ch === "\\") {
      escaped = true;
      continue;
    }
    if (ch === "|") return true;
  }
  return false;
}

function stripOptionalAndClassSyntax(value) {
  let out = "";
  let escaped = false;
  let parenDepth = 0;
  let braceDepth = 0;
  for (const ch of String(value || "")) {
    if (escaped) {
      if (parenDepth === 0 && braceDepth === 0) out += ch;
      escaped = false;
      continue;
    }
    if (ch === "\\") {
      escaped = true;
      continue;
    }
    if (ch === "(") {
      parenDepth += 1;
      out += " ";
      continue;
    }
    if (ch === ")" && parenDepth > 0) {
      parenDepth -= 1;
      out += " ";
      continue;
    }
    if (ch === "{") {
      braceDepth += 1;
      out += " ";
      continue;
    }
    if (ch === "}" && braceDepth > 0) {
      braceDepth -= 1;
      out += " ";
      continue;
    }
    if (parenDepth === 0 && braceDepth === 0) out += ch;
  }
  return out;
}

function ngramsFromFilterValue(value) {
  if (!value || oldSpanishMode || hasUnescapedPipe(value)) return [];
  const stripped = stripOptionalAndClassSyntax(value).replace(/[?*<>"]/g, " ");
  const normalized = normalizeString(stripped);
  const grams = new Set();
  const tokens = normalized.match(/[0-9a-z]+/g) || [];
  tokens.forEach(token => {
    if (token.length < 3) return;
    for (let idx = 0; idx <= token.length - 3; idx += 1) {
      grams.add(token.slice(idx, idx + 3));
    }
  });
  return [...grams];
}

function shortTokensFromFilterValue(value) {
  if (!value || oldSpanishMode || hasUnescapedPipe(value)) return [];
  if (!hasFormattingCharacters(value)) return [];
  if (/[\\*?"()[\]{}|<>]/.test(String(value))) return [];
  const normalized = normalizeString(stripHtmlTags(String(value)));
  const tokens = normalized.match(/[0-9a-z]+/g) || [];
  return [...new Set(tokens.filter(token => token.length > 0 && token.length < 3))];
}

function literalEdgeFromFilterValue(value, kind) {
  const normalized = normalizeString(stripHtmlTags(String(value || "")));
  if (!normalized) return "";
  if (kind === "prefix") {
    const match = normalized.match(/^[0-9a-z]{3,}/);
    return match ? match[0].slice(0, 3) : "";
  }
  const match = normalized.match(/[0-9a-z]{3,}$/);
  return match ? match[0].slice(-3) : "";
}

function wildcardAlnumLengthRange(value) {
  const normalized = normalizeString(stripHtmlTags(String(value || "")));
  if (!normalized || normalized.includes("*")) return null;
  let min = 0;
  let max = 0;
  for (const ch of normalized) {
    if (ch === "?") {
      min += 1;
      max += 2;
    } else if (/[0-9a-z]/.test(ch)) {
      min += 1;
      max += 1;
    } else {
      return null;
    }
  }
  if (min < 3 || max > 64) return null;
  return { min, max };
}

function lengthEdgeAlternatives(edge, kind, lengthRange) {
  if (!edge || !lengthRange) return null;
  const lengthKind = kind === "prefix" ? "prefixLen" : "suffixLen";
  const alternatives = [];
  for (let len = lengthRange.min; len <= lengthRange.max; len += 1) {
    alternatives.push({ kind: lengthKind, edge: `${edge}:${len}` });
  }
  return alternatives;
}

function wordEdgeKeysFromFilter(filter) {
  if (!filter?.value || oldSpanishMode || hasUnescapedPipe(filter.value)) return [];
  const value = String(filter.value);
  if (!/[?*]/.test(value)) return [];
  if (/[\\"()[\]{}|<>]/.test(value)) return [];
  const scope = normalizeScope(filter.scope);
  if (scope !== "word" && scope !== "wordPhrase") return [];
  const mode = filter.mode;
  const groups = [];
  const lengthRange = mode === "exact" ? wildcardAlnumLengthRange(value) : null;
  if ((mode === "exact" || mode === "starts") && /^[0-9A-Za-z]/.test(value)) {
    const edge = literalEdgeFromFilterValue(value, "prefix");
    const alternatives = lengthEdgeAlternatives(edge, "prefix", lengthRange);
    if (alternatives) groups.push(alternatives);
    else if (edge) groups.push([{ kind: "prefix", edge }]);
  }
  if ((mode === "exact" || mode === "ends") && /[0-9A-Za-z]$/.test(value)) {
    const edge = literalEdgeFromFilterValue(value, "suffix");
    const alternatives = lengthEdgeAlternatives(edge, "suffix", lengthRange);
    if (alternatives) groups.push(alternatives);
    else if (edge) groups.push([{ kind: "suffix", edge }]);
  }
  return groups;
}

function hasOrLogic(filters) {
  return (filters || []).some(filter => String(filter?.logic || "AND").toUpperCase() === "OR");
}

function intersectSortedArrays(left, right) {
  const out = [];
  let i = 0;
  let j = 0;
  while (i < left.length && j < right.length) {
    const a = left[i];
    const b = right[j];
    if (a === b) {
      out.push(a);
      i += 1;
      j += 1;
    } else if (a < b) {
      i += 1;
    } else {
      j += 1;
    }
  }
  return out;
}

function unionSortedArrays(arrays) {
  const set = new Set();
  arrays.forEach(arr => arr.forEach(value => set.add(value)));
  return [...set].sort((a, b) => a - b);
}

async function getNgramCandidatesForFilter(filter) {
  const field = normalizeFieldKey(filter.field);
  const grams = ngramsFromFilterValue(filter.value);
  if (!grams.length) return null;
  const layers = getSearchLayerModesForField(field);
  const layerCandidates = [];
  for (const layer of layers) {
    let candidate = null;
    let usable = 0;
    for (const gram of grams) {
      const shard = getNgramShard(field, layer, gram);
      const ngramIndex = await ensureLazyNgramShard(field, layer, shard);
      if (!ngramIndex) continue;
      const rows = ngramIndex.get(gram);
      if (!rows) continue;
      usable += 1;
      candidate = candidate == null ? rows : intersectSortedArrays(candidate, rows);
      if (!candidate.length) break;
    }
    if (usable > 0) layerCandidates.push(candidate || []);
  }
  if (!layerCandidates.length) return null;
  return unionSortedArrays(layerCandidates);
}

async function getShortTokenCandidatesForFilter(filter) {
  const field = normalizeFieldKey(filter.field);
  const tokens = shortTokensFromFilterValue(filter.value);
  if (!tokens.length) return null;
  const layers = getSearchLayerModesForField(field);
  const layerCandidates = [];
  for (const layer of layers) {
    let candidate = null;
    let usable = 0;
    for (const token of tokens) {
      const shard = getShortTokenShard(field, layer, token);
      const tokenIndex = await ensureLazyShortTokenShard(field, layer, shard);
      if (!tokenIndex) continue;
      const rows = tokenIndex.get(token) || [];
      usable += 1;
      candidate = candidate == null ? rows : intersectSortedArrays(candidate, rows);
      if (!candidate.length) break;
    }
    if (usable > 0) layerCandidates.push(candidate || []);
  }
  if (!layerCandidates.length) return null;
  return unionSortedArrays(layerCandidates);
}

async function getWordEdgeCandidatesForFilter(filter) {
  const field = normalizeFieldKey(filter.field);
  const edgeGroups = wordEdgeKeysFromFilter(filter);
  if (!edgeGroups.length) return null;
  const layers = getSearchLayerModesForField(field);
  const layerCandidates = [];
  for (const layer of layers) {
    let candidate = null;
    let usable = 0;
    for (const alternatives of edgeGroups) {
      const alternativeRows = [];
      for (const { kind, edge } of alternatives) {
        const shard = getWordEdgeShard(field, layer, kind, edge);
        const edgeIndex = await ensureLazyWordEdgeShard(field, layer, kind, shard);
        if (!edgeIndex) continue;
        alternativeRows.push(edgeIndex.get(edge) || []);
      }
      if (!alternativeRows.length) continue;
      const rows = unionSortedArrays(alternativeRows);
      usable += 1;
      candidate = candidate == null ? rows : intersectSortedArrays(candidate, rows);
      if (!candidate.length) break;
    }
    if (usable > 0) layerCandidates.push(candidate || []);
  }
  if (!layerCandidates.length) return null;
  return unionSortedArrays(layerCandidates);
}

async function getLazyCandidatesForFilter(filter) {
  const ngramCandidates = await getNgramCandidatesForFilter(filter);
  const shortTokenCandidates = await getShortTokenCandidatesForFilter(filter);
  const wordEdgeCandidates = await getWordEdgeCandidatesForFilter(filter);
  const candidateSets = [ngramCandidates, shortTokenCandidates, wordEdgeCandidates].filter(Boolean);
  if (!candidateSets.length) return null;
  const rows = candidateSets.reduce((current, rows) =>
    current == null ? rows : intersectSortedArrays(current, rows), null);
  return {
    rows,
    usedNgrams: !!ngramCandidates,
    usedShortTokens: !!shortTokenCandidates,
    usedWordEdges: !!wordEdgeCandidates,
  };
}

async function buildLazyCandidateInfo(filters = activeFilters) {
  if (oldSpanishMode || hasOrLogic(filters)) return null;
  let candidate = null;
  let usedNgrams = false;
  let usedShortTokens = false;
  let usedWordEdges = false;
  for (const filter of filters || []) {
    if (!filter || filter.negate || filter.type === "fuenteSet" || filter.type === "wordGroup") continue;
    const field = normalizeFieldKey(filter.field);
    if (!field || !FIELDS_WITH_LAZY_INDEX.has(field)) continue;
    const fieldCandidates = await getLazyCandidatesForFilter(filter);
    if (!fieldCandidates) continue;
    usedNgrams = usedNgrams || fieldCandidates.usedNgrams;
    usedShortTokens = usedShortTokens || fieldCandidates.usedShortTokens;
    usedWordEdges = usedWordEdges || fieldCandidates.usedWordEdges;
    candidate = candidate == null ? fieldCandidates.rows : intersectSortedArrays(candidate, fieldCandidates.rows);
    if (!candidate.length) break;
  }
  if (!usedNgrams && !usedShortTokens && !usedWordEdges) return null;
  const rows = candidate.map(idx => lazyMetaRows[idx]).filter(Boolean);
  const chunkIds = [...new Set(rows.map(row => row._lazyChunk).filter(Boolean))];
  return { rows, chunkCount: chunkIds.length, chunkIds, usedNgrams, usedShortTokens, usedWordEdges };
}

async function loadLazyRowChunk(chunkId) {
  if (!chunkId) return [];
  if (lazyRowChunkCache.has(chunkId)) return lazyRowChunkCache.get(chunkId);
  if (!lazyRowChunkPromises.has(chunkId)) {
    lazyRowChunkPromises.set(chunkId, ensureLazyDataManifest()
      .then(() => {
        const path = lazyRowChunkPaths.get(chunkId);
        if (!path) throw new Error(`Missing lazy row chunk ${chunkId}`);
        return loadJsonlRows(path);
      })
      .then(rows => {
        rows.forEach((row, idx) => {
          normalizeRowFieldKeys(row);
          row._rid = row.record_id || idx;
          row._prio = parsePriority(row.prio);
          row._browseOrder = computeBrowseOrderKey(row.record_id || idx);
          if (row.record_id) lazyDisplayRowsById.set(row.record_id, row);
        });
        lazyRowChunkCache.set(chunkId, rows);
        return rows;
      }));
  }
  return lazyRowChunkPromises.get(chunkId);
}

async function hydrateCandidateRows(candidateInfo) {
  const chunks = [...new Set(candidateInfo.rows.map(row => row._lazyChunk).filter(Boolean))];
  await Promise.all(chunks.map(loadLazyRowChunk));
  return candidateInfo.rows
    .map(row => lazyDisplayRowsById.get(row.record_id))
    .filter(Boolean);
}

function collectLazyIndexNeeds(filters = []) {
  const needs = new Map();
  filters.forEach(filter => {
    if (!filter || filter.type === "fuenteSet") return;
    const field = normalizeFieldKey(filter.field);
    if (!field || field === "Fuente" || !FIELDS_WITH_LAZY_INDEX.has(field)) return;
    const layers = getSearchLayerModesForField(field);
    needs.set(field, new Set([...(needs.get(field) || []), ...layers]));
  });
  return [...needs.entries()].flatMap(([field, layers]) =>
    [...layers].map(layer => ({ field, layer }))
  );
}

function getDominantLemmaFilter(filters = activeFilters) {
  const substantiveFilters = (filters || []).filter(filter => filter.type !== "fuenteSet");
  if (!substantiveFilters.length) return null;
  if (substantiveFilters.some(filter => String(filter.logic || "AND").toUpperCase() === "OR")) {
    return null;
  }
  const candidates = substantiveFilters.filter(filter =>
    !filter.negate &&
    filter.field === "Editado" &&
    normalizeScope(filter.scope) === "word" &&
    filter.mode === "exact" &&
    String(filter.logic || "AND").toUpperCase() === "AND"
  );
  return candidates.length === 1 ? candidates[0] : null;
}

function buildRankingContext(rows) {
  const context = {
    dominantLemmaFilter: getDominantLemmaFilter(activeFilters),
    exactCount: 0,
    phraseCount: 0,
    usesLemmaTiering: false,
    getTier: () => 2
  };

  if (!context.dominantLemmaFilter) return context;

  const tierCache = new WeakMap();
  const query = buildFilterQuery(context.dominantLemmaFilter);
  const mode = context.dominantLemmaFilter.mode;

  context.getTier = row => {
    if (tierCache.has(row)) return tierCache.get(row);
    const entry = getNormalizedEntry(row, context.dominantLemmaFilter.field);
    const useLoose = query.allowLoose;
    const words = query.accentSensitive
      ? entry.wordsWithAccents
      : (oldSpanishMode && entry.wordsOS) ? entry.wordsOS : entry.words;
    const matched = words.some(wordEntry => {
      const candidate = useLoose ? wordEntry.loose : wordEntry.raw;
      return candidateMatchesQuery(candidate, query, mode, useLoose);
    });
    const tier = !matched ? 2 : words.length === 1 ? 0 : 1;
    tierCache.set(row, tier);
    return tier;
  };

  rows.forEach(row => {
    const tier = context.getTier(row);
    if (tier === 0) context.exactCount += 1;
    else if (tier === 1) context.phraseCount += 1;
  });

  context.usesLemmaTiering = context.exactCount > 0 || context.phraseCount > 0;
  return context;
}

function buildSortKey(value) {
  const raw = typeof stripHtmlTags === "function" ? stripHtmlTags(String(value || "")) : String(value || "");
  return raw.replace(/^[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+/, "").trim();
}

function getFuenteSortKey(value) {
  return normalizeString(String(value || ""));
}

function getPrioritySortEntry(row) {
  let entry = prioritySortCache.get(row);
  if (entry) return entry;
  entry = {
    head: buildSortKey(getDisplayValue(row, "Editado") || getDisplayValue(row, "Original")),
    source: getFuenteSortKey(getDisplayValue(row, "Fuente"))
  };
  prioritySortCache.set(row, entry);
  return entry;
}

function compareRecordId(a, b) {
  return alphaNumCollator.compare(String(a.record_id || a._rid || ""), String(b.record_id || b._rid || ""));
}

function comparePriorityOrder(a, b) {
  const pa = Number.isFinite(a._prio) ? a._prio : Number.POSITIVE_INFINITY;
  const pb = Number.isFinite(b._prio) ? b._prio : Number.POSITIVE_INFINITY;
  if (pa !== pb) return pa - pb;

  const sortA = getPrioritySortEntry(a);
  const sortB = getPrioritySortEntry(b);
  const headCmp = alphaNumCollator.compare(sortA.head, sortB.head);
  if (headCmp !== 0) return headCmp;

  const sourceCmp = alphaNumCollator.compare(sortA.source, sortB.source);
  if (sourceCmp !== 0) return sourceCmp;

  return compareRecordId(a, b);
}

function compareBrowseOrder(a, b) {
  const browseCmp = (a._browseOrder ?? 0) - (b._browseOrder ?? 0);
  if (browseCmp !== 0) return browseCmp;
  return compareRecordId(a, b);
}

function compareLemmaPriority(a, b, context) {
  const tierA = context.getTier(a);
  const tierB = context.getTier(b);
  if (tierA !== tierB) return tierA - tierB;
  return comparePriorityOrder(a, b);
}

function getRankingComparator(context, options = {}) {
  if (options.randomizeBrowse) return compareBrowseOrder;
  if (context && context.usesLemmaTiering) return (a, b) => compareLemmaPriority(a, b, context);
  return comparePriorityOrder;
}

function getRankedPage(rows, comparator, offset, pageSize) {
  if (!rows.length || pageSize <= 0) return [];
  return rows.slice().sort(comparator).slice(offset, offset + pageSize);
}

async function runQuery(payload) {
  workerAssetVersion = payload.assetVersion || "dev";
  searchLayerMode = SEARCH_LAYER_MODES.has(payload.searchLayerMode) ? payload.searchLayerMode : "both";
  oldSpanishMode = !!payload.oldSpanishMode;
  accentSensitiveMode = !!payload.accentSensitiveMode;
  activeFilters = Array.isArray(payload.activeFilters) ? payload.activeFilters : [];
  emptyBrowseSeed = Number(payload.emptyBrowseSeed) >>> 0;
  prioritySortCache = new WeakMap();

  await ensureLazyMetaRows();
  const candidateInfo = await buildLazyCandidateInfo(activeFilters);
  let scanRows = lazyMetaRows;
  let usedNgrams = false;
  let usedShortTokens = false;
  let usedWordEdges = false;
  let hydratedCandidates = false;
  let candidateFiltered = false;
  let fallbackIndexesLoaded = false;
  if (candidateInfo && candidateInfo.rows.length === 0) {
    scanRows = [];
    usedNgrams = candidateInfo.usedNgrams;
    usedShortTokens = candidateInfo.usedShortTokens;
    usedWordEdges = candidateInfo.usedWordEdges;
  } else if (
    candidateInfo &&
    candidateInfo.rows.length <= NGRAM_FULL_VERIFY_ROW_LIMIT &&
    candidateInfo.chunkCount <= NGRAM_FULL_VERIFY_CHUNK_LIMIT
  ) {
    scanRows = await hydrateCandidateRows(candidateInfo);
    usedNgrams = candidateInfo.usedNgrams;
    usedShortTokens = candidateInfo.usedShortTokens;
    usedWordEdges = candidateInfo.usedWordEdges;
    hydratedCandidates = true;
  } else {
    const needs = collectLazyIndexNeeds(activeFilters);
    await Promise.all(needs.map(need => ensureLazyFieldIndex(need.field, need.layer)));
    if (candidateInfo) {
      scanRows = candidateInfo.rows;
      usedNgrams = candidateInfo.usedNgrams;
      usedShortTokens = candidateInfo.usedShortTokens;
      usedWordEdges = candidateInfo.usedWordEdges;
      candidateFiltered = true;
    }
    fallbackIndexesLoaded = needs.length > 0;
  }

  let matches;
  if (!activeFilters.length) {
    matches = scanRows.slice();
  } else {
    buildEvalContext();
    matches = scanRows.filter(row => evaluateTextFilters(row));
  }

  const offset = Math.max(0, Number(payload.offset) || 0);
  const pageSize = Math.max(1, Number(payload.pageSize) || 100);
  const rankingContext = buildRankingContext(matches);
  const rankingComparator = getRankingComparator(rankingContext, {
    randomizeBrowse: !!payload.randomizeBrowse
  });
  const pageRows = getRankedPage(matches, rankingComparator, offset, pageSize);

  return {
    requestSignature: payload.requestSignature,
    querySignature: payload.querySignature,
    offset,
    pageSize,
    total: matches.length,
    rows: pageRows,
    ranking: rankingContext.dominantLemmaFilter ? {
      exact: rankingContext.exactCount,
      phrase: rankingContext.phraseCount,
      manual: false
    } : null,
    cache: {
      indexedDB: !!(await openLazyAssetDb()),
      indexesLoaded: [...lazyLoadedIndexKeys],
      ngramsLoaded: [...lazyLoadedNgramKeys.keys()],
      shortTokensLoaded: [...lazyLoadedShortTokenKeys.keys()],
      wordEdgesLoaded: [...lazyLoadedWordEdgeKeys.keys()],
      usedNgrams,
      usedShortTokens,
      usedWordEdges,
      hydratedCandidates,
      candidateFiltered,
      fallbackIndexesLoaded,
      candidateCount: candidateInfo ? candidateInfo.rows.length : null,
      candidateChunkCount: candidateInfo ? candidateInfo.chunkCount : null,
      candidateChunks: candidateInfo ? candidateInfo.chunkIds : [],
      scanRowCount: scanRows.length
    }
  };
}

self.onmessage = event => {
  const msg = event.data || {};
  if (msg.type !== "query") return;
  runQuery(msg.payload || {})
    .then(result => {
      self.postMessage({ type: "result", id: msg.id, result });
    })
    .catch(error => {
      self.postMessage({
        type: "error",
        id: msg.id,
        error: error?.message || String(error)
      });
    });
};
