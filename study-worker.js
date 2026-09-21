// One isolated worker per Study scope/deck request; table and Pair state stay separate.
importScripts(`search-worker.js${self.location.search}`, `study-core.js${self.location.search}`);
let studyDisplayLayer = "normalized";
let studyDisplayOverrides = new Map();
let studyDecodedEntities = new Map();
let studyDecodeResolve = null;

function decodeStudyEntities(value) {
  return String(value ?? "").replace(STUDY_ENTITY_PATTERN, token => {
    if (!studyDecodedEntities.has(token)) throw new Error("Unresolved Study HTML entity");
    return studyDecodedEntities.get(token);
  });
}

// Assign after importScripts so the imported search adapter cannot replace Study display semantics.
getDisplayValue = function(row, field) {
  if (field === "Traducción" && studyDisplayOverrides.has(row.record_id)) {
    return studyDisplayOverrides.get(row.record_id);
  }
  const layer = field === "Traducción" ? studyDisplayLayer : "normalized";
  return row.__lazyLayers?.[field]?.[layer] ?? row[field] ?? "";
};

async function runStudyQuery(payload, progress) {
  workerAssetVersion = payload.assetVersion || "dev";
  searchLayerMode = SEARCH_LAYER_MODES.has(payload.searchLayerMode) ? payload.searchLayerMode : "both";
  oldSpanishMode = !!payload.oldSpanishMode;
  accentSensitiveMode = !!payload.accentSensitiveMode;
  activeFilters = payload.useCurrent ? (payload.activeFilters || []) : [];
  studyDisplayLayer = payload.displayLayer === "source" ? "source" : "normalized";
  const selectedSources = new Set(payload.selectedSources || []);
  const needs = new Map([
    ["Editado::normalized", { field: "Editado", layer: "normalized" }],
    [`Traducción::${studyDisplayLayer}`, { field: "Traducción", layer: studyDisplayLayer }],
  ]);
  const allowedTypes = new Set(["filter", "fuenteSet", "wordGroup", "reverse", "reversePreset"]);
  for (const filter of activeFilters) {
    if (!allowedTypes.has(filter.type || "filter")) throw new Error("Unsupported Study filter");
    if (filter.type === "fuenteSet") continue;
    for (const item of (filter.fields?.length ? filter.fields : [filter.field || "Traducción"])) {
      const field = normalizeFieldKey(item);
      if (field === "Fuente") continue;
      if (!FIELDS_WITH_LAZY_INDEX.has(field)) throw new Error("Unsupported Study field");
      for (const layer of getSearchLayerModesForField(field)) needs.set(`${field}::${layer}`, { field, layer });
    }
  }
  progress({ phase: "indexes", done: 0, total: needs.size });
  const manifest = await ensureLazyDataManifest();
  await ensureLazyMetaRows();
  let loaded = 0;
  for (const need of needs.values()) {
    await ensureLazyFieldIndex(need.field, need.layer);
    progress({ phase: "indexes", done: ++loaded, total: needs.size });
  }
  buildEvalContext();
  let rows = lazyMetaRows.filter(row => selectedSources.has(row.Fuente) &&
    (!activeFilters.length || evaluateTextFilters(row)));
  let rawProjection = null;
  if (studyDisplayLayer === "source") {
    const entry = manifest.studySourceDisplayOverrides?.["Traducción"];
    if (manifest.studyDisplayProjectionVersion !== 1 || !entry || !Number.isInteger(entry.count) || entry.count < 0 ||
        !Array.isArray(entry.sources) || (entry.count > 0 && (!entry.path || !entry.sources.length))) {
      throw new Error("Missing Study source-display projection");
    }
    const sources = new Set(rows.map(row => row.Fuente));
    if (entry.sources.some(source => sources.has(source))) {
      progress({ phase: "indexes", done: loaded, total: loaded + 1 });
      const items = await loadJsonlRows(entry.path, { cache: false });
      if (items.length !== entry.count) throw new Error("Incomplete Study display projection");
      for (const item of items) {
        if (!lazyMetaById.has(item.record_id) || studyDisplayOverrides.has(item.record_id) || typeof item.value !== "string") {
          throw new Error("Invalid Study display projection record");
        }
        studyDisplayOverrides.set(item.record_id, item.value);
      }
      rawProjection = entry.path;
      progress({ phase: "indexes", done: ++loaded, total: loaded });
    }
  }
  // Decode only entity tokens via the page's existing HTML textarea parser.
  // Each cleanStudyText call remains one substitution pass, as on the page.
  const entityTexts = new Set();
  for (const row of rows) {
    for (const field of ["Editado", "Traducción"]) {
      const text = stripHtmlTags(String(getDisplayValue(row, field)));
      if (text.match(STUDY_ENTITY_PATTERN)) entityTexts.add(text);
    }
  }
  if (entityTexts.size) {
    const decoded = await new Promise(resolve => {
      studyDecodeResolve = resolve;
      self.postMessage({ type: "decodeEntities", texts: [...entityTexts] });
    });
    studyDecodedEntities = new Map(decoded);
  }
  progress({ phase: "scan", done: 0, total: rows.length });
  if (payload.themeTerms?.length) rows = getStudyRowsForThemeByLemma(rows, { _normalizedTerms: payload.themeTerms });
  const direction = payload.direction;
  const possibleCards = countStudyPossibleCardsFromRows(rows, { direction });
  const cards = payload.scopeOnly ? [] : buildStudyCardsFromRows(rows, { direction, limit: payload.limit });
  progress({ phase: "scan", done: rows.length, total: rows.length });
  return { cards, rowCount: rows.length, possibleCards, cache: {
    metaRows: lazyMetaRows.length, indexesLoaded: [...lazyLoadedIndexKeys],
    rowChunksLoaded: 0, rawProjection, displayOverrides: studyDisplayOverrides.size,
    entityTokens: studyDecodedEntities.size, complete: true,
  } };
}

self.onmessage = event => {
  if (event.data?.type === "decodedEntities") {
    studyDecodeResolve?.(event.data.entries);
    studyDecodeResolve = null;
    return;
  }
  if (event.data?.type !== "study") return;
  runStudyQuery(event.data.payload, progress => self.postMessage({ type: "progress", progress }))
    .then(result => self.postMessage({ type: "result", result }))
    .catch(error => self.postMessage({ type: "error", error: error.message || String(error) }));
};
