// A dedicated, disposable worker: never shares query globals with the table worker.
importScripts(`search-worker.js${self.location.search}`);

function extractPairTokens(value, wordOnly) {
  const raw = stripHtmlTags(String(value ?? ""));
  if (!raw.trim()) return [];
  const cleaned = collapseWhitespace(stripPunctuationCharacters(raw));
  if (!cleaned) return [];
  if (!wordOnly) return [cleaned];
  return cleaned.split(/\s+/).filter(Boolean);
}


async function runPairQuery(payload, progress) {
  workerAssetVersion = payload.assetVersion || "dev";
  searchLayerMode = SEARCH_LAYER_MODES.has(payload.searchLayerMode) ? payload.searchLayerMode : "both";
  oldSpanishMode = !!payload.oldSpanishMode;
  accentSensitiveMode = !!payload.accentSensitiveMode;
  activeFilters = payload.useFilters ? (payload.activeFilters || []) : [];
  const selectedSources = payload.useFilters ? new Set(payload.selectedSources || []) : null;
  const column = normalizeFieldKey(payload.column);
  if (!FIELDS_WITH_LAZY_INDEX.has(column)) throw new Error("Unsupported Pair column");
  const allowedTypes = new Set(["filter", "fuenteSet", "wordGroup", "reverse", "reversePreset"]);
  const needs = new Map([[`${column}::normalized`, { field: column, layer: "normalized" }]]);
  for (const filter of activeFilters) {
    if (!allowedTypes.has(filter.type || "filter")) throw new Error("Unsupported Pair filter");
    if (filter.type === "fuenteSet") continue;
    const fields = filter.fields?.length ? filter.fields : [filter.field || "Traducción"];
    for (const rawField of fields) {
      const field = normalizeFieldKey(rawField);
      if (field === "Fuente") continue;
      if (!FIELDS_WITH_LAZY_INDEX.has(field)) throw new Error("Unsupported Pair filter field");
      for (const layer of getSearchLayerModesForField(field)) needs.set(`${field}::${layer}`, { field, layer });
    }
  }
  progress({ phase: "indexes", done: 0, total: needs.size });
  const manifest = await ensureLazyDataManifest();
  if (manifest.pairProjectionVersion !== 1) throw new Error("Pair projections are not available for this data version");
  await ensureLazyMetaRows();
  let loaded = 0;
  for (const need of needs.values()) {
    await ensureLazyFieldIndex(need.field, need.layer);
    progress({ phase: "indexes", done: ++loaded, total: needs.size });
  }
  buildEvalContext();
  const wordOnly = payload.wordOnly;
  const suffixConfig = payload.suffixConfig;
  const pairMap = new Map();
  const suffixes = [
    { key: "first", suffix: suffixConfig.first.norm },
    { key: "second", suffix: suffixConfig.second.norm },
    { key: "third", suffix: suffixConfig.third.norm },
    { key: "fourth", suffix: suffixConfig.fourth.norm }
  ].filter(item => item.suffix);
  const suffixesSorted = suffixes.slice().sort((a, b) => b.suffix.length - a.suffix.length);
  const addRow = row => {
    const value = row[column];
    if (value == null || value === "") return;
    const tokens = extractPairTokens(value, wordOnly);
    tokens.forEach(token => {
      const cleanedToken = String(token).trim();
      if (!cleanedToken) return;
      const normalized = normalizeString(cleanedToken);
      if (!normalized) return;
      const match = suffixesSorted.find(item => normalized.endsWith(item.suffix));
      if (!match) return;
      const stem = normalized.slice(0, -match.suffix.length);
      if (!stem) return;
      let entry = pairMap.get(stem);
      if (!entry) {
        entry = { first: new Map(), second: new Map(), third: new Map(), fourth: new Map() };
        pairMap.set(stem, entry);
      }
      const bucket = entry[match.key];
      if (!bucket) return;
      bucket.set(cleanedToken, (bucket.get(cleanedToken) || 0) + 1);
    });
  };

  const matches = [];
  for (let index = 0; index < lazyMetaRows.length; index++) {
    const row = lazyMetaRows[index];
    if ((!selectedSources || selectedSources.has(row.Fuente)) &&
        (!activeFilters.length || evaluateTextFilters(row))) matches.push(row);
    if (index % 5000 === 0) progress({ phase: "scan", done: index, total: lazyMetaRows.length });
  }
  const overrides = new Map();
  const rawEntry = manifest.pairRawOverrides?.[column];
  if (!rawEntry || !Number.isInteger(rawEntry.count) || rawEntry.count < 0 ||
      !Array.isArray(rawEntry.sources) || (rawEntry.count > 0 && (!rawEntry.path || !rawEntry.sources.length))) {
    throw new Error("Missing or invalid raw Pair projection metadata");
  }
  const matchSources = new Set(matches.map(row => row.Fuente));
  const needsOverrides = rawEntry && rawEntry.sources.some(source => matchSources.has(source));
  if (needsOverrides) {
    progress({ phase: "indexes", done: loaded, total: loaded + 1 });
    const items = await loadJsonlRows(rawEntry.path, { cache: false });
    if (items.length !== rawEntry.count) throw new Error("Incomplete raw Pair projection");
    for (const item of items) {
      if (!lazyMetaById.has(item.record_id) || overrides.has(item.record_id) || typeof item.value !== "string") {
        throw new Error("Invalid raw Pair projection record");
      }
      overrides.set(item.record_id, item.value);
    }
    progress({ phase: "indexes", done: ++loaded, total: loaded });
  }
  for (let index = 0; index < matches.length; index++) {
    const row = matches[index];
    // Overlay only the aggregation input, never the matcher/display indexes.
    addRow(overrides.has(row.record_id) ? { [column]: overrides.get(row.record_id) } : row);
    if (index % 5000 === 0) progress({ phase: "scan", done: index, total: matches.length });
  }
  const pairs = [];
  pairMap.forEach((entry, stem) => {
    if (entry.first.size && entry.second.size) pairs.push({ stem,
      first: [...entry.first], second: [...entry.second],
      third: [...entry.third], fourth: [...entry.fourth] });
  });
  pairs.sort((a, b) => alphaNumCollator.compare(a.stem, b.stem));
  return { pairs, rows: matches.length, cache: {
    metaRows: lazyMetaRows.length,
    indexesLoaded: [...lazyLoadedIndexKeys],
    rowChunksLoaded: 0,
    rawProjection: needsOverrides ? rawEntry.path : null,
    rawOverridesLoaded: overrides.size,
    complete: true,
  } };
}

self.onmessage = event => {
  if (event.data?.type !== "pairs") return;
  runPairQuery(event.data.payload, progress => self.postMessage({ type: "progress", progress }))
    .then(result => self.postMessage({ type: "result", result }))
    .catch(error => self.postMessage({ type: "error", error: error.message || String(error) }));
};
