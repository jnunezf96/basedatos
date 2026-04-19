const TABLE_FIELDS = [
  { key: "Texto estandarizado", label: "Edición", defaultWidth: 120 },
  { key: "Escritura original", label: "Original", defaultWidth: 120 },
  { key: "Traducción", label: "Traducción", defaultWidth: 260 },
  { key: "Fuente", label: "Fuente", defaultWidth: 120 },
  { key: "Comentario", label: "Comentario", defaultWidth: 260 }
];
const TABLE_MIN_WIDTH = 908;

const I18N = {
  es: {
    title: "Base de datos náhuatl",
    subtitle: "Filtra y explora cinco columnas con filtros rápidos y mini‑lenguaje.",
    "tab.filters": "Filtros",
    "tab.sources": "Fuentes",
    "tab.regex": "Regex",
    "tab.pairs": "Pares a/i",
    "tab.reverse": "Reverso",
    "reverse.title": "Búsqueda inversa",
    "reverse.hint": "Escribe una palabra en español o francés para encontrar lemas en náhuatl cuya traducción la contenga. Los resultados se muestran agrupados por lema, ordenados por cantidad de fuentes que los respaldan.",
    "reverse.submit": "Buscar",
    "reverse.includeComment": "Incluir Comentario",
    "reverse.chipLabel": "Significado",
    "tab.compare": "Comparar lema",
    "tab.browse": "Relaciones",
    "filter.title": "Filtro",
    "label.column": "Columna",
    "label.scope": "Casilla",
    "scope.whole": "Todo",
    "scope.word": "Palabra",
    "field.grafia.short": "edición",
    "field.paleografia.short": "original",
    "field.traduccion.short": "traducción",
    "field.comentario.short": "comentario",
    "grid.include": "Incluye",
    "grid.exclude": "Excluye",
    "grid.exact": "Exacto",
    "grid.starts": "Empieza",
    "grid.contains": "Contiene",
    "grid.ends": "Termina",
    "action.run": "Ejecutar",
    "action.clear": "Vaciar",
    "placeholder.exact.incl": "{casilla} de {campo} es exactamente...",
    "placeholder.exact.excl": "{casilla} de {campo} no es exactamente...",
    "placeholder.starts.incl": "{casilla} de {campo} empieza con...",
    "placeholder.starts.excl": "{casilla} de {campo} no empieza con...",
    "placeholder.any.incl": "{casilla} de {campo} contiene...",
    "placeholder.any.excl": "{casilla} de {campo} no contiene...",
    "placeholder.ends.incl": "{casilla} de {campo} termina con...",
    "placeholder.ends.excl": "{casilla} de {campo} no termina con...",
    "sources.title": "Fuentes",
    "sources.fill": "Todas",
    "sources.clear": "Ninguna",
    "regex.title": "Mini-lenguaje",
    "rx.wildcards": "Comodines",
    "rx.q1": "1 letra cualquiera",
    "rx.q2": "exactamente 2 letras",
    "rx.star1": "1 o más letras",
    "rx.star2": "2 o más letras",
    "rx.range": "2 a 4 letras",
    "rx.alternatives": "Alternativas",
    "rx.alt.group": "pato <em>o</em> pata",
    "rx.alt.pipe": "equivalente (nivel superior)",
    "rx.alt.escape": "barra literal",
    "rx.templates": "Plantillas C/V",
    "rx.cv.c": "consonante",
    "rx.cv.v": "vocal",
    "rx.cv.n": "nasal (m, n, ñ)",
    "rx.cv.l": "líquida (l, ll, r, rr)",
    "rx.cv.s": "sibilante (s, z, x, tz)",
    "rx.cv.g": "deslizada (y, hu, uh)",
    "rx.cv.p": "oclusiva (p, t, c, ch, tz…)",
    "rx.cv.a": "cualquier letra",
    "rx.cv.repeat": "una o más sílabas",
    "rx.cv.count": "exactamente 2 sílabas",
    "rx.cv.pattern": "patrón C‑V‑C",
    "rx.cv.optional": "C inicial opcional",
    "rx.negclass": "Clase negada",
    "rx.negclass.desc": "cualquier no-vocal",
    "rx.negclass.ex": "excluye vocales y s",
    "rx.cv.note": "Solo activo dentro de llaves { }",
    "rx.containsboth": "Ambas en la misma palabra",
    "rx.both.desc": "la palabra contiene <em>ambas</em>",
    "rx.both.note": "Doble barra <code>||</code> dentro de paréntesis",
    "rx.reduplication": "Reduplicación",
    "rx.redup.desc": "→ <em>pe</em>pech… (hasta 1ª vocal)",
    "rx.redup.ex2": "→ <em>tla</em>tlal…",
    "rx.literal": "Regex literal",
    "rx.lit.desc": "expresión completa entre <code>/</code>",
    "rx.lit.flags": "admite flags: i g m…",
    "pairs.title": "Pares a/i",
    "pairs.run": "Buscar pares",
    "pairs.clear": "Limpiar",
    "pairs.column": "Columna",
    "pairs.suffixes": "Sufijos",
    "pairs.suffixes.first": "i",
    "pairs.suffixes.second": "a",
    "pairs.suffixes.third": "opcional",
    "pairs.suffixes.fourth": "opcional",
    "pairs.useFilters": "Usar filtros actuales",
    "pairs.wordOnly": "Solo palabras",
    "pairs.summary": "Pares encontrados: {{pairs}} · Filas analizadas: {{rows}}",
    "pairs.noResults": "No se encontraron pares a/i.",
    "pairs.header.stem": "Base",
    "pairs.header.a": "Forma en -a",
    "pairs.header.i": "Forma en -i",
    "pairs.header.total": "Total",
    "compare.title": "Comparar lema",
    "compare.run": "Comparar",
    "compare.clear": "Limpiar",
    "compare.query.label": "Lema exacto",
    "compare.query.placeholder": "Ej. chihua",
    "compare.scope": "{{selected}}/{{total}} fuentes en alcance",
    "compare.prompt": "Escribe un lema exacto para comparar fuentes.",
    "compare.noSources": "Selecciona al menos una fuente para comparar.",
    "compare.noMatches": "No hay coincidencias exactas para \"{{query}}\" en las fuentes seleccionadas.",
    "compare.suggestions": "Prueba estas variantes exactas:",
    "compare.summary": "Fuentes: {{sources}} · Filas: {{rows}} · Originales únicos: {{originals}} · Traducciones únicas: {{translations}}",
    "compare.singleSource": "Solo 1 fuente en alcance para este lema.",
    "compare.comment.toggle": "Comentario",
    "browse.title": "Relaciones",
    "browse.run": "Explorar",
    "browse.clear": "Limpiar",
    "browse.mode.label": "Modo",
    "browse.mode.shared": "Compartidos por fuentes",
    "browse.mode.attested": "Muy atestiguados",
    "browse.mode.unique": "Únicos de una fuente",
    "browse.mode.divergent": "Traducciones divergentes",
    "browse.threshold.attested": "Fuentes mín.",
    "browse.threshold.divergent": "Trad. mín.",
    "browse.target.label": "Fuente objetivo",
    "browse.target.placeholder": "Elige una fuente",
    "browse.scope": "{{selected}}/{{total}} fuentes en alcance",
    "browse.prompt": "Elige un modo y explora lemas por relación.",
    "browse.noSources": "Selecciona al menos una fuente para explorar relaciones.",
    "browse.shared.requiresSources": "Selecciona al menos 2 fuentes para ver lemas compartidos.",
    "browse.divergent.requiresSources": "Selecciona al menos 2 fuentes para medir divergencia en traducción.",
    "browse.unique.requiresTarget": "Elige una fuente objetivo dentro del alcance actual.",
    "browse.noResults.shared": "No hay lemas compartidos por todas las fuentes seleccionadas.",
    "browse.noResults.attested": "No hay lemas que alcancen ese nivel de atestiguación.",
    "browse.noResults.unique": "No hay lemas únicos para esa fuente dentro del alcance actual.",
    "browse.noResults.divergent": "No hay lemas con ese nivel de divergencia en traducción.",
    "browse.summary": "Lemas: {{lemmas}} · Fuentes en alcance: {{selected}}/{{total}}",
    "browse.badge.sources": "{{count}} fuentes",
    "browse.badge.rows": "{{count}} filas",
    "browse.badge.translations": "{{count}} trads.",
    "browse.meta.sources": "Fuentes: {{sources}}",
    "browse.meta.translations": "Traducciones: {{translations}}",
    "browse.meta.counts": "{{sources}} fuentes · {{rows}} filas · {{translations}} traducciones",
    "browse.compare": "Aislar",
    "browse.pagesize.label": "Filas",
    "browse.page": "Pág. {{page}} de {{total}}",
    "site.tagline": "Busca y filtra cientos de miles de entradas de diccionarios históricos de náhuatl. Usa los filtros para encontrar palabras por escritura, traducción o fuente; los resultados aparecen en la tabla de abajo.",
    "table.header.paleografia": "Original",
    "table.header.grafia": "Edición",
    "table.header.traduccion": "Traducción",
    "table.header.fuente": "Fuente",
    "table.header.comentario": "Comentario",
    "table.sort.label": "Orden:",
    "table.sort.all": "Todos",
    "table.sort.page": "Página",
    "table.status.loading": "Cargando datos…",
    "table.status.none": "Sin registros para mostrar.",
    "table.status.showing": "Registros mostrados: {{start}}-{{end}} de {{total}}",
    "table.status.detail.auto": "{{exact}} lemas exactos · {{phrase}} frases",
    "table.status.detail.manual": "{{exact}} lemas exactos · {{phrase}} frases · Manual",
    "table.empty": "No hay datos disponibles.",
    "table.export.filename": "tabla.jpg",
    "table.export.png.filename": "tabla.png",
    "table.export.label": "Exportar ▾",
    "table.export.jpeg": "Imagen (JPG)",
    "table.export.png": "Imagen (PNG)",
    "table.export.csv": "Hoja de cálculo (CSV)",
    "table.export.csv.filename": "nahuatl.csv",
    "table.export.empty": "No hay resultados para exportar.",
    "field.paleografia": "Original",
    "field.grafia": "Edición",
    "field.traduccion": "Traducción",
    "field.comentario": "Comentario",
    "nav.left": "Mover a la izquierda",
    "nav.right": "Mover a la derecha",
    "action.add": "Añadir",
    "action.update": "Actualizar",
    "filter.title": "Filtro",
    "lang.toggle": "English",
    "oldspanish.toggle": "Esp. antiguo",
    "label.oldspanish": "Ortografía",
    "label.accent": "Acento",
    "label.logic": "Combinar",
    "accent.sensitive": "Acento exacto",
    "accent.insensitive": "Acento libre",
    "accent.loose": "Libre",
    "accent.strict": "Exacto",
    "logic.and": "Y",
    "logic.or": "O",
    "chips.zone.and": "Y",
    "chips.zone.or": "O",
    "table.pagesize.label": "Filas:",
    "table.columns": "Cols ▾",
    "view.rows": "Filas",
    "view.lemmas": "Lemas",
    "view.lemmas.summary": "Lemas: {{lemmas}} (de {{rows}} filas)",
    "view.lemmas.empty": "Ningún lema coincide con los filtros.",
    "compare.chipLabel": "Comparar"
  },
  en: {
    title: "Nahuatl database",
    subtitle: "Filter and explore five columns with quick filters and a mini-language.",
    "tab.filters": "Filters",
    "tab.sources": "Sources",
    "tab.regex": "Regex guide",
    "tab.pairs": "a/i pairs",
    "tab.reverse": "Reverse",
    "reverse.title": "Reverse lookup",
    "reverse.hint": "Type a Spanish or French word to find Nahuatl lemmas whose translation contains it. Results are grouped by lemma, ranked by the number of sources that back each meaning.",
    "reverse.submit": "Search",
    "reverse.includeComment": "Include Comment",
    "reverse.chipLabel": "Meaning",
    "tab.compare": "Compare lemma",
    "tab.browse": "Browse",
    "filter.title": "Filter",
    "label.column": "Column",
    "label.scope": "Search in",
    "scope.whole": "All",
    "scope.word": "Word",
    "field.grafia.short": "edition",
    "field.paleografia.short": "original",
    "field.traduccion.short": "translation",
    "field.comentario.short": "comment",
    "grid.include": "Include",
    "grid.exclude": "Exclude",
    "grid.exact": "Exact",
    "grid.starts": "Starts with",
    "grid.contains": "Contains",
    "grid.ends": "Ends with",
    "action.run": "Run",
    "action.clear": "Clear",
    "placeholder.exact.incl": "{casilla} in {campo} is exactly...",
    "placeholder.exact.excl": "{casilla} in {campo} is not exactly...",
    "placeholder.starts.incl": "{casilla} in {campo} starts with...",
    "placeholder.starts.excl": "{casilla} in {campo} does not start with...",
    "placeholder.any.incl": "{casilla} in {campo} contains...",
    "placeholder.any.excl": "{casilla} in {campo} does not contain...",
    "placeholder.ends.incl": "{casilla} in {campo} ends with...",
    "placeholder.ends.excl": "{casilla} in {campo} does not end with...",
    "sources.title": "Sources",
    "sources.fill": "All",
    "sources.clear": "None",
    "regex.title": "Mini-language",
    "rx.wildcards": "Wildcards",
    "rx.q1": "any 1 letter",
    "rx.q2": "exactly 2 letters",
    "rx.star1": "1 or more letters",
    "rx.star2": "2 or more letters",
    "rx.range": "2 to 4 letters",
    "rx.alternatives": "Alternatives",
    "rx.alt.group": "pato <em>or</em> pata",
    "rx.alt.pipe": "equivalent (top level)",
    "rx.alt.escape": "literal pipe",
    "rx.templates": "C/V Templates",
    "rx.cv.c": "consonant",
    "rx.cv.v": "vowel",
    "rx.cv.n": "nasal (m, n, ñ)",
    "rx.cv.l": "liquid (l, ll, r, rr)",
    "rx.cv.s": "sibilant (s, z, x, tz)",
    "rx.cv.g": "glide (y, hu, uh)",
    "rx.cv.p": "stop (p, t, c, ch, tz…)",
    "rx.cv.a": "any letter",
    "rx.cv.repeat": "one or more syllables",
    "rx.cv.count": "exactly 2 syllables",
    "rx.cv.pattern": "C‑V‑C pattern",
    "rx.cv.optional": "optional initial C",
    "rx.negclass": "Negated class",
    "rx.negclass.desc": "any non-vowel",
    "rx.negclass.ex": "excludes vowels and s",
    "rx.cv.note": "Only active inside braces { }",
    "rx.containsboth": "Both in same word",
    "rx.both.desc": "word contains <em>both</em>",
    "rx.both.note": "Double pipe <code>||</code> inside parentheses",
    "rx.reduplication": "Reduplication",
    "rx.redup.desc": "→ <em>pe</em>pech… (up to first vowel)",
    "rx.redup.ex2": "→ <em>tla</em>tlal…",
    "rx.literal": "Literal regex",
    "rx.lit.desc": "full expression between <code>/</code>",
    "rx.lit.flags": "supports flags: i g m…",
    "pairs.title": "a/i pairs",
    "pairs.run": "Find pairs",
    "pairs.clear": "Clear",
    "pairs.column": "Column",
    "pairs.suffixes": "Suffixes",
    "pairs.suffixes.first": "i",
    "pairs.suffixes.second": "a",
    "pairs.suffixes.third": "optional",
    "pairs.suffixes.fourth": "optional",
    "pairs.useFilters": "Use current filters",
    "pairs.wordOnly": "Word only",
    "pairs.summary": "Pairs found: {{pairs}} · Rows scanned: {{rows}}",
    "pairs.noResults": "No a/i pairs found.",
    "pairs.header.stem": "Stem",
    "pairs.header.a": "-a form",
    "pairs.header.i": "-i form",
    "pairs.header.total": "Total",
    "compare.title": "Compare lemma",
    "compare.run": "Compare",
    "compare.clear": "Clear",
    "compare.query.label": "Exact lemma",
    "compare.query.placeholder": "E.g. chihua",
    "compare.scope": "{{selected}}/{{total}} sources in scope",
    "compare.prompt": "Enter an exact lemma to compare sources.",
    "compare.noSources": "Select at least one source to compare.",
    "compare.noMatches": "No exact matches for \"{{query}}\" in the selected sources.",
    "compare.suggestions": "Try these exact variants:",
    "compare.summary": "Sources: {{sources}} · Rows: {{rows}} · Unique originals: {{originals}} · Unique translations: {{translations}}",
    "compare.singleSource": "Only 1 source is in scope for this lemma.",
    "compare.comment.toggle": "Comment",
    "browse.title": "Browse relationships",
    "browse.run": "Browse",
    "browse.clear": "Clear",
    "browse.mode.label": "Mode",
    "browse.mode.shared": "Shared by sources",
    "browse.mode.attested": "Widely attested",
    "browse.mode.unique": "Unique to source",
    "browse.mode.divergent": "Divergent translations",
    "browse.threshold.attested": "Min. sources",
    "browse.threshold.divergent": "Min. trans.",
    "browse.target.label": "Target source",
    "browse.target.placeholder": "Choose a source",
    "browse.scope": "{{selected}}/{{total}} sources in scope",
    "browse.prompt": "Choose a mode and browse lemmas by relationship.",
    "browse.noSources": "Select at least one source to browse relationships.",
    "browse.shared.requiresSources": "Select at least 2 sources to browse shared lemmas.",
    "browse.divergent.requiresSources": "Select at least 2 sources to measure translation divergence.",
    "browse.unique.requiresTarget": "Choose a target source within the current scope.",
    "browse.noResults.shared": "No lemmas are shared by all selected sources.",
    "browse.noResults.attested": "No lemmas reach that attestation threshold.",
    "browse.noResults.unique": "No lemmas are unique to that source within the current scope.",
    "browse.noResults.divergent": "No lemmas reach that translation-divergence threshold.",
    "browse.summary": "Lemmas: {{lemmas}} · Sources in scope: {{selected}}/{{total}}",
    "browse.badge.sources": "{{count}} sources",
    "browse.badge.rows": "{{count}} rows",
    "browse.badge.translations": "{{count}} trans.",
    "browse.meta.sources": "Sources: {{sources}}",
    "browse.meta.translations": "Translations: {{translations}}",
    "browse.meta.counts": "{{sources}} sources · {{rows}} rows · {{translations}} translations",
    "browse.compare": "Isolate",
    "browse.pagesize.label": "Rows",
    "browse.page": "Page {{page}} of {{total}}",
    "site.tagline": "Search and filter hundreds of thousands of entries from historical Nahuatl dictionaries. Use the filters to find words by spelling, translation, or source; results appear in the table below.",
    "table.header.paleografia": "Original",
    "table.header.grafia": "Edition",
    "table.header.traduccion": "Translation",
    "table.header.fuente": "Source",
    "table.header.comentario": "Comment",
    "table.sort.label": "Sort:",
    "table.sort.all": "All",
    "table.sort.page": "Page",
    "table.status.loading": "Loading data…",
    "table.status.none": "No records to show.",
    "table.status.showing": "Records shown: {{start}}-{{end}} of {{total}}",
    "table.status.detail.auto": "{{exact}} exact lemmas · {{phrase}} phrases",
    "table.status.detail.manual": "{{exact}} exact lemmas · {{phrase}} phrases · Manual",
    "table.empty": "No data available.",
    "table.export.filename": "table.jpg",
    "table.export.png.filename": "table.png",
    "table.export.label": "Export ▾",
    "table.export.jpeg": "Image (JPG)",
    "table.export.png": "Image (PNG)",
    "table.export.csv": "Spreadsheet (CSV)",
    "table.export.csv.filename": "nahuatl.csv",
    "table.export.empty": "Nothing to export.",
    "field.paleografia": "Original",
    "field.grafia": "Edition",
    "field.traduccion": "Translation",
    "field.comentario": "Comment",
    "nav.left": "Move left",
    "nav.right": "Move right",
    "action.add": "Add filter",
    "action.update": "Update",
    "filter.title": "Filter",
    "lang.toggle": "Español",
    "oldspanish.toggle": "Old Spanish",
    "label.oldspanish": "Spelling",
    "label.accent": "Accent",
    "label.logic": "Combine",
    "accent.sensitive": "Exact accent",
    "accent.insensitive": "Free accent",
    "accent.loose": "Free",
    "accent.strict": "Exact",
    "logic.and": "AND",
    "logic.or": "OR",
    "chips.zone.and": "AND",
    "chips.zone.or": "OR",
    "table.pagesize.label": "Rows:",
    "table.columns": "Cols ▾",
    "view.rows": "Rows",
    "view.lemmas": "Lemmas",
    "view.lemmas.summary": "Lemmas: {{lemmas}} (of {{rows}} rows)",
    "view.lemmas.empty": "No lemmas match the current filters.",
    "compare.chipLabel": "Compare"
  }
};

let maxDisplayRows = 100;
const FILTER_OWNERS = ["f1"];
let groupCounter = 0;
let editingGroupId = null;
let currentCommitLogic = "AND";
let groupOrder = []; // [{id, logic}] — preserves chip insertion order

// ── Session state ──────────────────────────────────────────────
let sessionCounter = 1;
let sessions = [{ id: "s1", filters: [], order: [], groupCounter: 0 }];
let currentSessionId = "s1";

const FIELD_SHORT = {
  "Escritura original": "Orig.",
  "Texto estandarizado": "Ed.",
  "Traducción": "Trad.",
  "Comentario": "Com.",
};
const MODE_SYMBOL = { exact: "=", starts: "^", any: "~", ends: "$" };

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
const FUENTE_OWNER = "fuentes";
const COMPARE_OWNER = "compareOwner";
const REVERSE_OWNER = "reverseOwner";
const FUENTE_OPTIONS = [
  "153? Trilingüe",
  "1547 Olmos_G",
  "1547 Olmos_V ?",
  "1551-95 Documentos nahuas de la Ciudad de México",
  "1565 Sahagún Escolio",
  "1571 Molina 1",
  "1571 Molina 2",
  "1579 Durán",
  "1580 CF Index",
  "1580 Sahagún/Máynez",
  "1595 Rincón",
  "1598 Tezozomoc",
  "1611 Arenas",
  "1629 Alarcón",
  "1645 Carochi",
  "1692 Guerra",
  "1759 Paredes",
  "1765 Cortés y Zedeño",
  "1780 Clavijero",
  "1780 ? Bnf_361",
  "17?? Bnf_362",
  "17?? Bnf_362bis",
  "1984 Tzinacapan",
  "2002 Mecayapan",
  "2021 Wimmer",
  "C_M",
  "Docs_México",
  "1992 Karttunen",
  "V94 Diccionario Global SNP"
];
sessions[0].fuentes = new Set(FUENTE_OPTIONS);
let selectedFuentes = sessions[0].fuentes;
let lastRenderRows = [];
let lastRenderTotal = 0;
let lastFilteredRows = [];
let displayOffset = 0;
let sortKeys = []; // [{field, dir}]
let sortScope = "all"; // "all" | "page"
const hiddenColumns = new Set();
const expandedLemmas = new Set();
const columnWidths = new Map(TABLE_FIELDS.map(field => [field.key, field.defaultWidth]));
const alphaNumCollator = new Intl.Collator("es", { numeric: true, sensitivity: "base" });
const emptyBrowseSeed = (() => {
  try {
    if (globalThis.crypto?.getRandomValues) {
      const bytes = new Uint32Array(1);
      globalThis.crypto.getRandomValues(bytes);
      return bytes[0] >>> 0;
    }
  } catch {}
  return Math.floor(Math.random() * 0x100000000) >>> 0;
})();
let wimmerShowEs = true;
let lastFocusedInput = null;
let filterCards = [];
let activeCardIndex = 0;
const expandedComments = new Set();
const expandableComments = new Set();
const commentAnchors = new Map();
const pendingComentarioSync = new WeakMap();
let currentLang = "es";
let lastPairResults = null;
let lastPairMeta = null;
let lastRankingSummary = null;
let tableViewMode = "rows"; // "rows" | "lemmas"
let lastLemmaItems = [];
let lastLemmaPageOffsets = [0];

document.addEventListener("DOMContentLoaded", () => {
  loadColumnState();
  setupLanguageToggle();
  setupOldSpanishToggle();
  setupAccentToggle();
  setupLogicToggle();
  setupChipsBarDelegation();
  setupSessionBar();
  setupLiveSearch();
  setStatus(t("table.status.loading"));
  document.addEventListener("focusin", e => {
    if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) {
      lastFocusedInput = e.target;
    }
  });
  document.addEventListener("keydown", e => {
    if (e.key === "Enter") {
      const otherPanel = document.activeElement?.closest("#regexPanel, #pairsPanel");
      if (!otherPanel) {
        e.preventDefault();
        commitFilterCard();
      }
    }
  });
  setupFilterCards();
  initCardNavigation();
  setupTabs();
  setupSortControls();
  setupSortScopeControls();
  updateSortIndicators();
  setupPaginationControls();
  setupPageSizeControls();
  setupColumnZoneInteractions();
  setupStickyHeaderTable();
  setupComentarioToggleAll();
  setupLemmaToggleAll();
  setupExportButtons();
  renderFuenteList();
  setupFuenteActions();
  setupWimmerTranslate();
  setupPairFinder();
  setupViewToggle();
  setupEdicionCellClick();
  setupReverseLookup();
  fetch("data/data.jsonl.gz")
    .then(r => {
      const ds = new DecompressionStream("gzip");
      r.body.pipeTo(ds.writable);
      return new Response(ds.readable).text();
    })
    .then(text => {
      const rows = text.split("\n").filter(Boolean).map(line => JSON.parse(line));
      rows.forEach((row, idx) => {
        row._rid = row.record_id || idx;
        row._prio = parsePriority(row.prio);
        row._browseOrder = computeBrowseOrderKey(row.record_id || idx);
      });
      dataRows = rows;
      applyFuenteFilters();
    });
});

function t(key, vars = {}) {
  const dict = I18N[currentLang] || I18N.es;
  let text = dict[key] ?? I18N.es[key] ?? key;
  Object.entries(vars).forEach(([name, value]) => {
    text = text.replace(new RegExp(`{{\\s*${name}\\s*}}`, "g"), value);
  });
  return text;
}

function applyTranslations() {
  document.documentElement.lang = currentLang;

  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.dataset.i18n;
    if (key) el.textContent = t(key);
  });

  document.querySelectorAll("[data-i18n-html]").forEach(el => {
    const key = el.dataset.i18nHtml;
    if (key) el.innerHTML = t(key);
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.dataset.i18nPlaceholder;
    if (key) el.setAttribute("placeholder", t(key));
  });

  document.querySelectorAll("[data-i18n-placeholder-label]").forEach(el => {
    const key = el.dataset.i18nPlaceholderLabel;
    if (key) el.dataset.placeholderLabel = t(key);
  });

  // Re-apply dynamic filter placeholders after language change
  document.querySelectorAll(".filter-card").forEach(card => updateFilterPlaceholders(card));

  document.querySelectorAll("[data-i18n-aria-label]").forEach(el => {
    const key = el.dataset.i18nAriaLabel;
    if (key) el.setAttribute("aria-label", t(key));
  });

  document.title = t("title");
}

function refreshLanguageDependentUI() {
  const y = getTableScrollTop();
  updateAccentLabels();
  if (!dataRows || !dataRows.length) {
    setStatus(t("table.status.loading"));
    return;
  }
  updateViewToggleLabels();
  renderTable(lastRenderRows, lastRenderTotal);
  refreshPairFinderUI();
  requestAnimationFrame(() => {
    setTableScroll(y);
  });
}

function setupLanguageToggle() {
  const btn = document.getElementById("langToggle");
  const saved = localStorage.getItem("nahuatl-ui-lang");
  if (saved && I18N[saved]) {
    currentLang = saved;
  }
  applyTranslations();
  if (!btn) return;
  btn.addEventListener("click", () => {
    currentLang = currentLang === "es" ? "en" : "es";
    localStorage.setItem("nahuatl-ui-lang", currentLang);
    applyTranslations();
    refreshLanguageDependentUI();
  });
}

function setupOldSpanishToggle() {
  const btns = document.querySelectorAll(".old-spanish-btn");
  btns.forEach(btn => {
    btn.addEventListener("click", () => {
      oldSpanishMode = !oldSpanishMode;
      btns.forEach(b => b.classList.toggle("active", oldSpanishMode));
      normalizationCache = new Map();
      if (activeFilters.length) applyFilters();
    });
  });
}

function updateAccentLabels() {
  document.querySelectorAll(".accent-btn").forEach(btn => {
    const mode = btn.dataset.accent;
    btn.textContent = t(mode === "strict" ? "accent.strict" : "accent.loose");
    btn.classList.toggle("active", (mode === "strict") === accentSensitiveMode);
  });
}

function setupAccentToggle() {
  document.querySelectorAll(".accent-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const nextMode = btn.dataset.accent === "strict";
      if (nextMode === accentSensitiveMode) return;
      accentSensitiveMode = nextMode;
      updateAccentLabels();
      if (activeFilters.length) applyFilters();
    });
  });
  updateAccentLabels();
}

function setupLogicToggle() {
  document.querySelectorAll(".logic-toggle").forEach(toggle => {
    toggle.querySelectorAll(".logic-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        setLogicToggle(btn.dataset.logic);
      });
    });
  });
}

function setLogicToggle(logic) {
  currentCommitLogic = logic === "OR" ? "OR" : "AND";
  document.querySelectorAll(".logic-toggle .logic-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.logic === currentCommitLogic);
  });
}

function setupChipsBarDelegation() {
  const bar = document.getElementById("activeFiltersBar");
  if (!bar) return;

  bar.addEventListener("click", e => {
    // Clear-all button
    if (e.target.closest(".chip-clear-all")) {
      if (editingGroupId) cancelEdit();
      activeFilters = activeFilters.filter(f => f.owner === "f1" || f.owner === FUENTE_OWNER || f.type === "fuenteSet");
      groupOrder = [];
      renderActiveFilterChips();
      applyFilters();
      return;
    }

    // Individual chip remove (×)
    const removeBtn = e.target.closest(".chip-remove");
    if (removeBtn) {
      const chip = removeBtn.closest("[data-group-id]");
      if (!chip) return;
      const groupId = chip.dataset.groupId;
      if (editingGroupId === groupId) cancelEdit();
      activeFilters = activeFilters.filter(f => f.owner !== groupId);
      groupOrder = groupOrder.filter(g => g.id !== groupId);
      renderActiveFilterChips();
      applyFilters();
      return;
    }

    // Chip body click → load for editing (skip synthetic chips — they have no editor)
    const chip = e.target.closest("[data-group-id]");
    if (chip && !e.target.closest(".chip-remove")) {
      if (chip.dataset.groupId === COMPARE_OWNER) return;
      if (chip.dataset.groupId === REVERSE_OWNER) return;
      loadGroupForEditing(chip.dataset.groupId);
    }
  });
}

function setupLiveSearch() {
  document.querySelectorAll(".filter-card").forEach(card => {
    const owner = card.dataset.owner;
    if (!owner) return;
    card.querySelectorAll(".filter-input").forEach(input => {
      input.addEventListener("keydown", e => {
        if (e.key === "Escape") {
          e.preventDefault();
          input.value = "";
        }
      });
    });
  });
}

function renderActiveFilterChips() {
  const bar = document.getElementById("activeFiltersBar");
  if (!bar) return;

  // Card indicator for the live-preview card
  const f1Card = document.querySelector(".filter-card[data-owner='f1']");
  if (f1Card) f1Card.classList.toggle("filter-card--active", activeFilters.some(f => f.owner === "f1"));

  // Collect committed groups (not f1 preview, not fuente, not compare)
  const groups = new Map();
  activeFilters.forEach(f => {
    if (f.type === "fuenteSet" || f.owner === FUENTE_OWNER || f.owner === "f1") return;
    if (f.owner === COMPARE_OWNER) return;
    if (f.owner === REVERSE_OWNER) return;
    if (!groups.has(f.owner)) groups.set(f.owner, []);
    groups.get(f.owner).push(f);
  });

  const compareFilter = activeFilters.find(f => f.owner === COMPARE_OWNER) || null;
  const reverseFilter = activeFilters.find(f => f.owner === REVERSE_OWNER) || null;

  if (!groups.size && !compareFilter && !reverseFilter) {
    bar.style.display = "none";
    bar.innerHTML = "";
    return;
  }
  bar.style.display = "";
  bar.innerHTML = "";

  // Compare chip (rendered first, visually distinct)
  if (compareFilter) {
    const zone = document.createElement("div");
    zone.className = "chips-zone chips-zone-compare";
    const chip = document.createElement("span");
    chip.className = "filter-chip chip-compare";
    chip.dataset.groupId = COMPARE_OWNER;
    const val = String(compareFilter.value);
    const display = val.length > 20 ? val.slice(0, 18) + "…" : val;
    chip.innerHTML =
      `<span class="chip-label"><span class="chip-field">${escapeHtml(t("compare.chipLabel"))}</span> "${escapeHtml(display)}"</span>` +
      `<button type="button" class="chip-remove" aria-label="Quitar filtro">×</button>`;
    zone.appendChild(chip);
    bar.appendChild(zone);
  }

  // Reverse-lookup chip (meaning → lemmas)
  if (reverseFilter) {
    const zone = document.createElement("div");
    zone.className = "chips-zone chips-zone-reverse";
    const chip = document.createElement("span");
    chip.className = "filter-chip chip-reverse";
    chip.dataset.groupId = REVERSE_OWNER;
    const val = String(reverseFilter.value);
    const display = val.length > 24 ? val.slice(0, 22) + "…" : val;
    const fieldsBadge = Array.isArray(reverseFilter.fields) && reverseFilter.fields.includes("Comentario") ? " +C" : "";
    chip.innerHTML =
      `<span class="chip-label"><span class="chip-field">${escapeHtml(t("reverse.chipLabel") + fieldsBadge)}</span> "${escapeHtml(display)}"</span>` +
      `<button type="button" class="chip-remove" aria-label="Quitar filtro">×</button>`;
    zone.appendChild(chip);
    bar.appendChild(zone);
  }

  // Partition by logic using groupOrder for ordering
  const andIds = groupOrder.filter(g => g.logic === "AND" && groups.has(g.id)).map(g => g.id);
  const orIds  = groupOrder.filter(g => g.logic === "OR"  && groups.has(g.id)).map(g => g.id);
  // Also include any groups not yet in groupOrder (safety net)
  groups.forEach((_, id) => {
    if (!andIds.includes(id) && !orIds.includes(id)) andIds.push(id);
  });

  function makeChip(groupId, filters) {
    const field = filters[0].field;
    const scope = filters[0].scope;
    const logic = filters[0].logic || "AND";
    const fieldLabel = FIELD_SHORT[field] || field;
    const scopeBadge = scope === "word" ? " W" : "";

    const parts = filters.map(f => {
      const sym = MODE_SYMBOL[f.mode] || f.mode;
      const sign = f.negate ? "−" : "+";
      const val = String(f.value);
      const display = val.length > 16 ? val.slice(0, 14) + "…" : val;
      return `<span class="chip-part ${f.negate ? "chip-part-excl" : ""}">${sym}${sign}&thinsp;"${escapeHtml(display)}"</span>`;
    }).join('<span class="chip-dot"> · </span>');

    const chip = document.createElement("span");
    chip.className = "filter-chip chip-group";
    chip.dataset.groupId = groupId;
    if (groupId === editingGroupId) chip.classList.add("chip-editing");
    chip.innerHTML =
      `<span class="chip-label"><span class="chip-field">${escapeHtml(fieldLabel + scopeBadge)}</span> ${parts}</span>` +
      `<button type="button" class="chip-remove" aria-label="Quitar filtro">×</button>`;

    return chip;
  }

  // AND zone
  if (andIds.length) {
    const zone = document.createElement("div");
    zone.className = "chips-zone chips-zone-and";
    const label = document.createElement("span");
    label.className = "chips-zone-label";
    label.textContent = t("chips.zone.and");
    zone.appendChild(label);
    andIds.forEach(id => {
      const filters = groups.get(id);
      if (filters) zone.appendChild(makeChip(id, filters));
    });
    bar.appendChild(zone);
  }

  // Divider (only when both zones have chips)
  if (andIds.length && orIds.length) {
    const divider = document.createElement("div");
    divider.className = "chips-zone-divider";
    bar.appendChild(divider);
  }

  // OR zone
  if (orIds.length) {
    const zone = document.createElement("div");
    zone.className = "chips-zone chips-zone-or";
    const label = document.createElement("span");
    label.className = "chips-zone-label";
    label.textContent = t("chips.zone.or");
    zone.appendChild(label);
    orIds.forEach(id => {
      const filters = groups.get(id);
      if (filters) zone.appendChild(makeChip(id, filters));
    });
    bar.appendChild(zone);
  }

  const totalGroups = andIds.length + orIds.length + (compareFilter ? 1 : 0) + (reverseFilter ? 1 : 0);
  if (totalGroups > 1) {
    const clearAll = document.createElement("button");
    clearAll.type = "button";
    clearAll.className = "chip-clear-all";
    clearAll.textContent = "× limpiar todo";
    bar.appendChild(clearAll);
  }

}

// ── Session management ─────────────────────────────────────────

function sessionLabel(session) {
  // Derive label from first committed filter value, fallback to number
  if (session.filters && session.filters.length) {
    const first = session.filters[0];
    const val = String(first.value ?? "").slice(0, 14);
    if (val) return val;
  }
  const idx = sessions.indexOf(session);
  return String(idx + 1);
}

function saveCurrentSession() {
  const session = sessions.find(s => s.id === currentSessionId);
  if (!session) return;
  // Save committed filters (not f1/fuente)
  session.filters = activeFilters.filter(
    f => f.owner !== "f1" && f.owner !== FUENTE_OWNER && f.type !== "fuenteSet"
  );
  session.order = groupOrder.slice();
  session.groupCounter = groupCounter;
  session.displayOffset = displayOffset;
  session.sortKeys = sortKeys.slice();
  session.sortScope = sortScope;
  session.viewMode = tableViewMode;
  session.expandedComments = Array.from(expandedComments);
  session.expandedLemmas = Array.from(expandedLemmas);
  const scroller = getTableScrollElement();
  session.scrollTop = scroller ? scroller.scrollTop : 0;
}

function loadSession(sessionId) {
  if (sessionId === currentSessionId) return;

  saveCurrentSession();

  // Cancel any in-progress edit
  if (editingGroupId) cancelEdit();

  // Clear card inputs
  const card = document.querySelector(".filter-card[data-owner='f1']");
  if (card) card.querySelectorAll(".filter-input").forEach(i => (i.value = ""));

  // Drop all filters — fuente state now lives on the session itself
  activeFilters = [];

  currentSessionId = sessionId;
  const session = sessions.find(s => s.id === sessionId);
  if (session) {
    activeFilters = session.filters.slice();
    groupOrder = session.order.slice();
    groupCounter = session.groupCounter;
    selectedFuentes = session.fuentes;
    displayOffset = session.displayOffset ?? 0;
    sortKeys = (session.sortKeys ?? []).slice();
    sortScope = session.sortScope ?? "all";
    tableViewMode = session.viewMode ?? "rows";
    expandedComments.clear();
    (session.expandedComments ?? []).forEach(id => expandedComments.add(id));
    expandedLemmas.clear();
    (session.expandedLemmas ?? []).forEach(id => expandedLemmas.add(id));
  }

  renderSessionBar();
  renderFuenteList();
  updateSortIndicators();
  updateSortScopeIndicators();
  updateViewToggleButtons();
  applyFuenteFilters({ keepOffset: true });

  const scroller = getTableScrollElement();
  if (scroller && session) scroller.scrollTop = session.scrollTop ?? 0;
}

function addSession() {
  saveCurrentSession();
  sessionCounter++;
  const id = `s${sessionCounter}`;
  const newSession = { id, filters: [], order: [], groupCounter: 0, fuentes: new Set(FUENTE_OPTIONS) };
  sessions.push(newSession);

  // Cancel edit, clear card
  if (editingGroupId) cancelEdit();
  const card = document.querySelector(".filter-card[data-owner='f1']");
  if (card) card.querySelectorAll(".filter-input").forEach(i => (i.value = ""));

  activeFilters = [];
  groupOrder = [];
  groupCounter = 0;
  currentSessionId = id;
  selectedFuentes = newSession.fuentes;
  displayOffset = 0;
  sortKeys = [];
  sortScope = "all";
  tableViewMode = "rows";
  expandedComments.clear();
  expandedLemmas.clear();

  renderSessionBar();
  renderFuenteList();
  updateSortIndicators();
  updateSortScopeIndicators();
  updateViewToggleButtons();
  applyFuenteFilters();

  const scroller = getTableScrollElement();
  if (scroller) scroller.scrollTop = 0;
}

function closeSession(sessionId) {
  if (sessions.length <= 1) return; // can't close last tab
  const idx = sessions.findIndex(s => s.id === sessionId);
  if (idx === -1) return;

  const isActive = sessionId === currentSessionId;
  sessions.splice(idx, 1);

  if (isActive) {
    // Switch to adjacent session without saving (current session is being discarded)
    const nextSession = sessions[Math.min(idx, sessions.length - 1)];

    if (editingGroupId) cancelEdit();
    const card = document.querySelector(".filter-card[data-owner='f1']");
    if (card) card.querySelectorAll(".filter-input").forEach(i => (i.value = ""));

    activeFilters = [];
    currentSessionId = nextSession.id;
    activeFilters = nextSession.filters.slice();
    groupOrder = nextSession.order.slice();
    groupCounter = nextSession.groupCounter;
    selectedFuentes = nextSession.fuentes;
    displayOffset = nextSession.displayOffset ?? 0;
    sortKeys = (nextSession.sortKeys ?? []).slice();
    sortScope = nextSession.sortScope ?? "all";
    tableViewMode = nextSession.viewMode ?? "rows";
    expandedComments.clear();
    (nextSession.expandedComments ?? []).forEach(eid => expandedComments.add(eid));
    expandedLemmas.clear();
    (nextSession.expandedLemmas ?? []).forEach(eid => expandedLemmas.add(eid));
    renderFuenteList();
    updateSortIndicators();
    updateSortScopeIndicators();
    updateViewToggleButtons();
    applyFuenteFilters({ keepOffset: true });
    const scroller = getTableScrollElement();
    if (scroller) scroller.scrollTop = nextSession.scrollTop ?? 0;
  }

  renderSessionBar();
}

function renderSessionBar() {
  const bar = document.getElementById("sessionBar");
  if (!bar) return;
  bar.innerHTML = "";

  sessions.forEach(session => {
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = "session-tab" + (session.id === currentSessionId ? " session-tab--active" : "");
    tab.dataset.sessionId = session.id;

    const label = document.createElement("span");
    label.className = "session-tab-label";
    label.textContent = sessionLabel(session);
    tab.appendChild(label);

    if (sessions.length > 1) {
      const close = document.createElement("span");
      close.className = "session-tab-close";
      close.textContent = "×";
      close.dataset.closeSession = session.id;
      tab.appendChild(close);
    }

    bar.appendChild(tab);
  });

  const addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.className = "session-tab-add";
  addBtn.textContent = "+";
  addBtn.title = "Nueva búsqueda";
  bar.appendChild(addBtn);
}

function setupSessionBar() {
  renderSessionBar();

  const bar = document.getElementById("sessionBar");
  if (!bar) return;

  bar.addEventListener("click", e => {
    // Close button
    const closeTarget = e.target.closest("[data-close-session]");
    if (closeTarget) {
      e.stopPropagation();
      closeSession(closeTarget.dataset.closeSession);
      return;
    }
    // Add button
    if (e.target.closest(".session-tab-add")) {
      addSession();
      return;
    }
    // Tab click
    const tab = e.target.closest(".session-tab");
    if (tab && tab.dataset.sessionId) {
      loadSession(tab.dataset.sessionId);
    }
  });
}

// Update session bar label after committing filters (label derives from filter values)
function refreshSessionLabel() {
  saveCurrentSession();
  renderSessionBar();
}

function setupTabs() {
  const buttons = document.querySelectorAll(".panel-tabs .tab-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const tabId = btn.dataset.tab;
      document.querySelectorAll(".tab-panel").forEach(panel => {
        panel.classList.toggle("active", panel.id === tabId);
      });
    });
  });
}

function updateFilterPlaceholders(card) {
  const fieldBtn = card.querySelector(".field-btn.active");
  const campo = (fieldBtn?.dataset.placeholderLabel || fieldBtn?.textContent.trim() || "").toLowerCase();
  const scopeBtn = card.querySelector(".scope-btn.active");
  const casilla = (scopeBtn?.dataset.placeholderLabel || scopeBtn?.textContent.trim() || "").toLowerCase();
  card.querySelectorAll(".filter-input[data-mode]").forEach(input => {
    const mode = input.dataset.mode;
    const negate = input.dataset.negate === "true";
    const key = `placeholder.${mode}.${negate ? "excl" : "incl"}`;
    input.placeholder = t(key).replace("{campo}", campo).replace("{casilla}", casilla);
  });
}

function setupFilterCards() {
  FILTER_OWNERS.forEach(owner => setupFilterCard(owner));
}

function setupFilterCard(owner) {
  const card = document.querySelector(`.filter-card[data-owner="${owner}"]`);
  if (!card) return;
  const container = card.parentElement;

  const fieldButtons = card.querySelectorAll(".field-btn");
  fieldButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      fieldButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      updateFilterPlaceholders(card);
    });
  });
  updateFilterPlaceholders(card);

  const scopeButtons = card.querySelectorAll(".scope-btn");
  scopeButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      scopeButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      updateFilterPlaceholders(card);
    });
  });

  const addBtn = card.querySelector(".add-btn");
  if (addBtn) {
    addBtn.addEventListener("click", () => commitFilterCard());
  }

  const cardInputs = card.querySelectorAll(".filter-input");
  cardInputs.forEach(input => {
    input.addEventListener("keydown", e => {
      if (e.key === "Enter") {
        e.preventDefault();
        commitFilterCard();
      }
    });
  });

  const clearBtn = card.querySelector(".clear-btn");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => clearFilterCard(owner));
  }

  const regexButtons = card.querySelectorAll(".regex-insert");
  regexButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const insert = btn.dataset.insert || "";
      let target = getActiveRegexTarget(card, btn);
      if (!target) return;
      if (btn.classList.contains("regex-insert-alt")) {
        const altInput = btn.closest(".regex-toolbar")?.querySelector(".regex-alt-input");
        const raw = altInput ? (altInput.value || altInput.placeholder || "").trim() : "";
        if (!raw) return;
        // Soporta separadores por coma o barra vertical, agrupados
        const parts = raw.split(/[|,]+/).map(s => s.trim()).filter(Boolean);
        if (!parts.length) return;
        const body = parts.join("|");
        insertAtCursor(target, `(?:${body})`);
      } else {
        insertAtCursor(target, insert);
      }
      target.focus();
    });
  });
}

function commitFilterCard() {
  const card = document.querySelector(".filter-card[data-owner='f1']");
  if (!card) return;

  const field = card.querySelector(".field-btn.active")?.dataset.field;
  const scope = card.querySelector(".scope-btn.active")?.dataset.scope || "whole";
  if (!field) return;

  const inputs = [];
  card.querySelectorAll(".filter-input").forEach(input => {
    const raw = sanitizeInput(input.value);
    if (!raw) return;
    inputs.push({ raw, mode: input.dataset.mode, negate: input.dataset.negate === "true" });
  });
  if (!inputs.length) return;

  const isEditing = editingGroupId !== null;
  const groupId = isEditing ? editingGroupId : `group_${++groupCounter}`;
  const logic = currentCommitLogic;
  // Word-scope AND groups use wordGroupId for same-word semantics; OR groups do not.
  const wordGroupId = (scope === "word" && logic === "AND") ? groupId : null;

  // Remove existing filters for this group (re-commit or live-preview cleanup)
  activeFilters = activeFilters.filter(f => f.owner !== groupId && f.owner !== "f1");

  inputs.forEach(({ raw, mode, negate }) => {
    const extras = wordGroupId ? { owner: groupId, wordGroupId } : { owner: groupId };
    appendFilter(field, mode, raw, logic, negate, scope, extras);
  });

  if (isEditing) {
    // Update groupOrder entry logic in case user switched AND/OR during edit
    const entry = groupOrder.find(g => g.id === groupId);
    if (entry) entry.logic = logic;
  } else {
    groupOrder.push({ id: groupId, logic });
  }

  // Reset edit state and card
  editingGroupId = null;
  const addBtn = card.querySelector(".add-btn");
  if (addBtn) addBtn.textContent = t("action.add");
  card.querySelectorAll(".filter-input").forEach(i => (i.value = ""));
  applyFilters();
  refreshSessionLabel();
}

function applyFilterCard(owner) {
  const card = document.querySelector(`.filter-card[data-owner="${owner}"]`);
  if (!card) return;
  removeOwnerFilters(owner);
  resetComentarioState();

  const field = card.querySelector(".field-btn.active")?.dataset.field;
  const scope = card.querySelector(".scope-btn.active")?.dataset.scope || "whole";
  if (!field) return;

  // Word-scope filters from the same card must be evaluated against the same word.
  // Assign a shared wordGroupId so extractWordQuickGroups groups them together.
  const wordGroupId = scope === "word" ? owner : null;

  const inputs = card.querySelectorAll(".filter-input");
  inputs.forEach(input => {
    const raw = sanitizeInput(input.value);
    const mode = input.dataset.mode;
    if (!raw) return;
    const negate = input.dataset.negate === "true";
    const extras = wordGroupId ? { owner, wordGroupId } : { owner };
    appendFilter(field, mode, raw, "AND", negate, scope, extras);
  });

  applyFilters();
}

function clearFilterCard(owner) {
  const card = document.querySelector(`.filter-card[data-owner="${owner}"]`);
  if (card) {
    card.querySelectorAll(".filter-input").forEach(input => (input.value = ""));
  }
  if (editingGroupId) cancelEdit();
  removeOwnerFilters(owner);
  resetComentarioState();
  applyFilters();
}

function cancelEdit() {
  editingGroupId = null;
  const card = document.querySelector(".filter-card[data-owner='f1']");
  if (card) {
    const addBtn = card.querySelector(".add-btn");
    if (addBtn) addBtn.textContent = t("action.add");
  }
  // Remove any chip-editing class (chips will re-render on applyFilters)
}

function loadGroupForEditing(groupId) {
  const card = document.querySelector(".filter-card[data-owner='f1']");
  if (!card) return;

  const filters = activeFilters.filter(f => f.owner === groupId);
  if (!filters.length) return;

  const field = filters[0].field;
  const scope = filters[0].scope || "whole";
  const logic = filters[0].logic || "AND";

  // Set field pill
  card.querySelectorAll(".field-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.field === field);
  });

  // Set scope pill
  card.querySelectorAll(".scope-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.scope === scope);
  });

  // Set logic toggle
  setLogicToggle(logic);

  // Fill inputs — clear all first, then populate
  const allInputs = Array.from(card.querySelectorAll(".filter-input"));
  allInputs.forEach(input => (input.value = ""));

  filters.forEach(f => {
    const match = allInputs.find(
      inp => inp.dataset.mode === f.mode && (inp.dataset.negate === "true") === f.negate && !inp.value
    );
    if (match) match.value = f.value;
  });

  // Set editing state
  editingGroupId = groupId;
  const addBtn = card.querySelector(".add-btn");
  if (addBtn) addBtn.textContent = t("action.update");

  // Re-render chips to show editing highlight
  renderActiveFilterChips();

  // Focus the first populated input
  const firstFilled = allInputs.find(i => i.value);
  if (firstFilled) firstFilled.focus();
}

function insertAtCursor(input, text) {
  const start = input.selectionStart ?? input.value.length;
  const end = input.selectionEnd ?? start;
  const before = input.value.slice(0, start);
  const after = input.value.slice(end);
  input.value = before + text + after;
  const pos = start + text.length;
  input.selectionStart = pos;
  input.selectionEnd = pos;
}

function getActiveRegexTarget(card, originBtn) {
  if (lastFocusedInput && card.contains(lastFocusedInput)) {
    return lastFocusedInput;
  }
  const active = document.activeElement;
  if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA") && card.contains(active)) {
    return active;
  }
  if (originBtn) {
    const row = originBtn.closest(".grid-row");
    if (row) {
      const preferred = row.querySelector('.filter-input[data-negate="false"]') || row.querySelector(".filter-input");
      if (preferred) return preferred;
    }
  }
  return card.querySelector('.filter-input[data-negate="false"]') || card.querySelector(".filter-input");
}

function initCardNavigation() {
  filterCards = Array.from(document.querySelectorAll(".filter-card"));
}

function removeOwnerFilters(owner) {
  activeFilters = activeFilters.filter(filter => filter.owner !== owner);
}

function getDominantLemmaFilter(filters = activeFilters) {
  const substantiveFilters = (filters || []).filter(filter => filter.type !== "fuenteSet");
  if (!substantiveFilters.length) return null;
  if (substantiveFilters.some(filter => String(filter.logic || "AND").toUpperCase() === "OR")) {
    return null;
  }
  const candidates = substantiveFilters.filter(filter =>
    !filter.negate &&
    filter.field === "Texto estandarizado" &&
    normalizeScope(filter.scope) === "word" &&
    filter.mode === "exact" &&
    String(filter.logic || "AND").toUpperCase() === "AND"
  );
  return candidates.length === 1 ? candidates[0] : null;
}

function isUnfilteredBrowseState(filters = activeFilters) {
  return !(filters && filters.length);
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

function buildRankingSummary(context, manualOverride = false) {
  if (!context || !context.dominantLemmaFilter) return null;
  const detailKey = manualOverride ? "table.status.detail.manual" : "table.status.detail.auto";
  return t(detailKey, {
    exact: context.exactCount,
    phrase: context.phraseCount
  });
}

function getRankingComparator(context, options = {}) {
  if (options.randomizeBrowse) {
    return compareBrowseOrder;
  }
  if (context && context.usesLemmaTiering) {
    return (a, b) => compareLemmaPriority(a, b, context);
  }
  return comparePriorityOrder;
}

function applyFilters(initial = false, options = {}) {
  if (!dataRows.length) return;
  if (!options.keepOffset) {
    displayOffset = 0;
  }
  let matches = [];
  if (!activeFilters.length) {
    matches = dataRows.slice();
  } else {
    buildEvalContext();
    matches = dataRows.filter(row => evaluateTextFilters(row));
  }
  lastFilteredRows = matches;

  if (tableViewMode === "lemmas") {
    const lemmaItems = buildLemmaItemsFromRows(matches);
    lastLemmaItems = lemmaItems;
    lastLemmaPageOffsets = computeLemmaPageOffsets(lemmaItems, maxDisplayRows);
    const total = lemmaItems.length;
    if (displayOffset >= total) {
      displayOffset = lastLemmaPageOffsets[lastLemmaPageOffsets.length - 1] || 0;
    } else {
      displayOffset = lastLemmaPageOffsets[findLemmaPageIndex(displayOffset)] || 0;
    }
    lastRenderRows = [];
    lastRenderTotal = total;
    lastRankingSummary = null;
    renderTable([], total);
    updateSortIndicators();
    restoreScroll(options);
    renderActiveFilterChips();
    return;
  }

  const rankingContext = buildRankingContext(matches);
  const rankingComparator = getRankingComparator(rankingContext, {
    randomizeBrowse: isUnfilteredBrowseState(activeFilters)
  });
  const total = matches.length;
  if (displayOffset >= total) {
    displayOffset = Math.max(0, total - maxDisplayRows);
  }
  let paged;
  if (sortKeys.length) {
    if (sortScope === "page") {
      const baseRows = matches.slice();
      baseRows.sort(rankingComparator);
      paged = baseRows.slice(displayOffset, displayOffset + maxDisplayRows);
      applyManualSort(paged, sortKeys);
    } else {
      const sorted = matches.slice();
      applyManualSort(sorted, sortKeys);
      paged = sorted.slice(displayOffset, displayOffset + maxDisplayRows);
    }
  } else {
    const sorted = matches.slice();
    sorted.sort(rankingComparator);
    paged = sorted.slice(displayOffset, displayOffset + maxDisplayRows);
  }
  lastRenderRows = paged.slice();
  lastRenderTotal = total;
  lastRankingSummary = buildRankingSummary(rankingContext, sortKeys.length > 0);
  renderTable(paged, total);
  updateSortIndicators();
  restoreScroll(options);
  renderActiveFilterChips();
}

function renderTable(rows, totalCount) {
  const tbody = document.querySelector("#dataTable tbody");
  if (!tbody) return;
  const scroller = getTableScrollElement();
  const savedScroll = scroller ? scroller.scrollTop : 0;
  tbody.innerHTML = "";
  expandableComments.clear();

  syncDataPanelViewAttribute();

  if (tableViewMode === "lemmas") {
    renderLemmasIntoTbody(tbody, totalCount);
    updateTableStatusForLemmas(totalCount);
    updatePaginationControls(totalCount);
    updateComentarioToggleButton([]);
    updateLemmaToggleButton();
    if (scroller) scroller.scrollTop = savedScroll;
    return;
  }

  if (!rows.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = TABLE_FIELDS.filter(f => !hiddenColumns.has(f.key)).length;
    td.className = "table-empty";
    td.textContent = t("table.empty");
    tr.appendChild(td);
    tbody.appendChild(tr);
  } else {
    let stripeIdx = 0;
    rows.forEach(row => {
      const { tr, comentarioMeta, translationMeasureEl } = buildDataRow(row);
      if (stripeIdx % 2 === 0) tr.classList.add("stripe-alt");
      stripeIdx++;
      tbody.appendChild(tr);
      if (comentarioMeta) syncComentarioCell(comentarioMeta, translationMeasureEl);
    });
  }

  updateTableStatus(rows.length, totalCount);
  updatePaginationControls(totalCount);
  updateComentarioToggleButton(rows);
  updateLemmaToggleButton();

  if (scroller) scroller.scrollTop = savedScroll;
}

function buildDataRow(row) {
  const tr = document.createElement("tr");
  if (row.record_id) tr.dataset.recordId = row.record_id;
  let translationMeasureEl = null;
  let comentarioMeta = null;

  TABLE_FIELDS.forEach(field => {
    const td = document.createElement("td");
    if (field.key === "Comentario") {
      const raw = getDisplayValue(row, field.key);
      const safe = raw == null ? "" : String(raw);
      if (!safe.trim()) {
        td.textContent = "";
      } else {
        td.classList.add("comentario-cell");
        const content = document.createElement("div");
        content.className = "comentario-text collapsed";
        content.innerHTML = applyHighlights(safe, field.key);
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "comentario-toggle";
        btn.addEventListener("click", e => {
          e.stopPropagation();
          if (!expandableComments.has(row._rid)) return;
          const isExpanded = expandedComments.has(row._rid);
          if (isExpanded) {
            const anchor = commentAnchors.get(row._rid);
            setCommentExpanded(row._rid, content, btn, false);
            if (anchor) {
              requestAnimationFrame(() => {
                const w = getTableWrapper();
                const rect = btn.getBoundingClientRect();
                const scrollTop = getTableScrollTop();
                const centerNow = rect.top + rect.height / 2 + scrollTop;
                const anchorCenter = anchor.center;
                const viewTop = scrollTop;
                const viewH = w ? w.clientHeight : window.innerHeight;
                const viewBottom = viewTop + viewH;
                if (anchorCenter < viewTop || anchorCenter > viewBottom) {
                  setTableScroll(anchorCenter - viewH * 0.5, "smooth");
                } else {
                  const delta = centerNow - anchorCenter;
                  if (Math.abs(delta) > 1 && w) w.scrollBy({ top: delta, behavior: "smooth" });
                }
              });
            }
          } else {
            const rect = btn.getBoundingClientRect();
            const scrollTop = getTableScrollTop();
            const center = rect.top + rect.height / 2 + scrollTop;
            commentAnchors.set(row._rid, { scrollY: scrollTop, center });
            setCommentExpanded(row._rid, content, btn, true);
          }
          updateComentarioToggleButton(lastRenderRows);
        });
        td.appendChild(content);
        td.appendChild(btn);
        comentarioMeta = { content, btn, rowId: row._rid };
      }
    } else {
      const raw = getDisplayValue(row, field.key);
      if (field.key === "Traducción") {
        const content = document.createElement("div");
        content.className = "traduccion-text";
        content.innerHTML = applyHighlights(raw, field.key);
        td.appendChild(content);
        translationMeasureEl = content;
      } else {
        td.innerHTML = applyHighlights(raw, field.key);
      }
    }
    tr.appendChild(td);
  });

  return { tr, comentarioMeta, translationMeasureEl };
}

function setTableStatusMessage(baseText, detailText = "") {
  const targets = [
    document.getElementById("tableStatus")
  ].filter(Boolean);
  targets.forEach(el => {
    if (!detailText) {
      el.textContent = baseText;
      return;
    }
    el.replaceChildren();
    const main = document.createElement("span");
    main.textContent = baseText;
    const detail = document.createElement("span");
    detail.className = "result-info-detail";
    detail.textContent = detailText;
    el.append(main, detail);
  });
}

function setStatus(message) {
  setTableStatusMessage(message);
}

function updateTableStatus(displayed, total) {
  if (!total) {
    setTableStatusMessage(t("table.status.none"));
    return;
  }
  const start = total === 0 ? 0 : Math.min(displayOffset + 1, total);
  const end = Math.min(displayOffset + displayed, total);
  setTableStatusMessage(
    t("table.status.showing", { start, end, total }),
    lastRankingSummary || ""
  );
}

function restoreScroll(options) {
  if (!options || typeof options.restoreScroll !== "number") return;
  const y = options.restoreScroll;
  const behavior = options.restoreBehavior === "smooth" ? "smooth" : "auto";
  requestAnimationFrame(() => {
    setTableScroll(y, behavior);
  });
}

function getPrimaryTableCard() {
  return document.querySelector(".data-panel");
}

function getPrimaryTableHeader() {
  return document.querySelector(".table-toolbar");
}

function getHeaderTable() {
  return document.getElementById("dataTable");
}

function getBodyTable() {
  return document.getElementById("dataTable");
}

function getTableScrollElement() {
  return document.querySelector(".table-scroll");
}

function getHeaderAnchorY() {
  const anchor = document.getElementById("tableHeaderAnchor");
  if (anchor) {
    const rect = anchor.getBoundingClientRect();
    return rect.top + window.scrollY;
  }
  const header = getPrimaryTableHeader();
  if (!header) return null;
  const rect = header.getBoundingClientRect();
  return rect.top + window.scrollY;
}

function getTableRestoreOptions() {
  return {
    keepOffset: true,
    keepCurrent: true,
    restoreScroll: getTableScrollTop(),
  };
}

function getTableScrollTop() {
  return window.scrollY;
}

function setTableScroll(y, behavior = "auto") {
  window.scrollTo({ top: y, behavior });
}

function getColumnWidth(fieldKey) {
  return columnWidths.get(fieldKey) || TABLE_FIELDS.find(field => field.key === fieldKey)?.defaultWidth || 140;
}

const COLUMN_STATE_KEY = "nawat-columns-v1";

function saveColumnState() {
  try {
    const payload = {
      order: TABLE_FIELDS.map(f => f.key),
      widths: Object.fromEntries(columnWidths),
      hidden: [...hiddenColumns]
    };
    localStorage.setItem(COLUMN_STATE_KEY, JSON.stringify(payload));
  } catch {}
}

function loadColumnState() {
  let payload;
  try {
    const raw = localStorage.getItem(COLUMN_STATE_KEY);
    if (!raw) return;
    payload = JSON.parse(raw);
  } catch { return; }
  if (!payload || typeof payload !== "object") return;

  if (Array.isArray(payload.order)) {
    const byKey = new Map(TABLE_FIELDS.map(f => [f.key, f]));
    const ordered = [];
    payload.order.forEach(key => {
      const field = byKey.get(key);
      if (field && !ordered.includes(field)) ordered.push(field);
    });
    TABLE_FIELDS.forEach(field => {
      if (!ordered.includes(field)) ordered.push(field);
    });
    if (ordered.length === TABLE_FIELDS.length) {
      TABLE_FIELDS.length = 0;
      ordered.forEach(f => TABLE_FIELDS.push(f));
    }
  }

  if (payload.widths && typeof payload.widths === "object") {
    Object.entries(payload.widths).forEach(([key, w]) => {
      if (columnWidths.has(key) && Number.isFinite(w) && w >= 50) {
        columnWidths.set(key, w);
      }
    });
  }

  if (Array.isArray(payload.hidden)) {
    hiddenColumns.clear();
    payload.hidden.forEach(key => {
      if (TABLE_FIELDS.some(f => f.key === key)) hiddenColumns.add(key);
    });
  }
}

function syncColumnLayout() {
  const visibleWidth = TABLE_FIELDS.reduce((sum, field, idx) => {
    return hiddenColumns.has(field.key) ? sum : sum + getColumnWidth(field.key);
  }, 0);
  const minWidth = Math.max(TABLE_MIN_WIDTH, visibleWidth);
  const table = getBodyTable();
  if (table) {
    let colgroup = table.querySelector("colgroup");
    if (!colgroup) {
      colgroup = document.createElement("colgroup");
      table.insertBefore(colgroup, table.firstChild);
    }
    colgroup.innerHTML = "";
    TABLE_FIELDS.forEach((field, idx) => {
      const col = document.createElement("col");
      const width = getColumnWidth(field.key);
      col.style.width = `${width}px`;
      col.style.minWidth = `${width}px`;
      colgroup.appendChild(col);
      table.classList.toggle(`col-hidden-${idx}`, hiddenColumns.has(field.key));
    });
    table.style.width = "100%";
    table.style.minWidth = `${minWidth}px`;
  }
  updateSideLitState();
}

function setupStickyHeaderTable() {
  window.addEventListener("resize", syncColumnLayout);
  syncColumnLayout();
}

function sampleRandomRows(size) {
  if (!dataRows.length) return [];
  if (size >= dataRows.length) {
    return shuffleArray(dataRows.slice());
  }
  const n = Math.max(0, Math.min(size, dataRows.length));
  const reservoir = dataRows.slice(0, n);
  for (let i = n; i < dataRows.length; i++) {
    const j = Math.floor(Math.random() * (i + 1));
    if (j < n) {
      reservoir[j] = dataRows[i];
    }
  }
  return reservoir;
}

function shuffleArray(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function getComentarioLineHeight(el) {
  const computed = window.getComputedStyle(el);
  const lineHeight = parseFloat(computed.lineHeight);
  const fontSize = parseFloat(computed.fontSize);
  if (Number.isFinite(lineHeight)) return lineHeight;
  if (Number.isFinite(fontSize)) return fontSize * 1.35;
  return 18;
}

function getComentarioClampHeight(commentEl, translationEl) {
  const translationHeight = Math.ceil(translationEl?.scrollHeight || translationEl?.clientHeight || 0);
  const lineHeight = getComentarioLineHeight(commentEl);
  const slack = Math.max(2, Math.round(lineHeight * 0.12));
  const baseHeight = translationHeight > 0 ? translationHeight : 120;
  return { lineHeight, clampHeight: baseHeight + slack };
}

function isComentarioExpandable(commentEl, clampHeight, lineHeight) {
  const maxH = `${clampHeight}px`;
  commentEl.style.setProperty("--comentario-max-height", maxH);
  commentEl.dataset.maxHeight = maxH;
  const wasCollapsed = commentEl.classList.contains("collapsed");
  commentEl.classList.add("collapsed");
  const visibleHeight = Math.ceil(commentEl.clientHeight || clampHeight);
  const naturalHeight = Math.ceil(commentEl.scrollHeight);
  if (!wasCollapsed) {
    commentEl.classList.remove("collapsed");
  }
  const hiddenHeight = Math.max(0, naturalHeight - visibleHeight);
  const meaningfulOverflow = Math.max(10, Math.round(lineHeight * 0.8));
  return hiddenHeight >= meaningfulOverflow;
}

function setCommentExpanded(rowId, contentEl, btnEl, expanded) {
  if (expanded) {
    expandedComments.add(rowId);
    contentEl.classList.remove("collapsed");
    btnEl.textContent = "−";
    return;
  }
  expandedComments.delete(rowId);
  commentAnchors.delete(rowId);
  contentEl.classList.add("collapsed");
  btnEl.textContent = "+";
}

function syncComentarioCell(meta, translationEl) {
  const { rowId, content, btn } = meta;
  const { lineHeight, clampHeight } = getComentarioClampHeight(content, translationEl);
  const expandable = isComentarioExpandable(content, clampHeight, lineHeight);
  if (!expandable) {
    setCommentExpanded(rowId, content, btn, false);
    content.classList.remove("collapsed");
    btn.remove();
    return false;
  }
  expandableComments.add(rowId);
  setCommentExpanded(rowId, content, btn, expandedComments.has(rowId));
  return true;
}

function getExpandableRenderRows(rows = lastRenderRows) {
  return rows.filter(r => expandableComments.has(r._rid));
}

function areAllExpandableCommentsExpanded(rows = lastRenderRows) {
  return rows.length > 0 && rows.every(r => expandedComments.has(r._rid));
}

function getVisibleLemmas() {
  if (tableViewMode !== "lemmas") return [];
  const offsets = lastLemmaPageOffsets && lastLemmaPageOffsets.length
    ? lastLemmaPageOffsets : [0];
  const pageIdx = findLemmaPageIndex(displayOffset);
  const startIdx = offsets[pageIdx] || 0;
  const endIdx = pageIdx + 1 < offsets.length ? offsets[pageIdx + 1] : lastLemmaItems.length;
  return lastLemmaItems.slice(startIdx, endIdx).map(item => item.lemma);
}

function flushPendingSyncsInChunks(pendingList, chunkSize = 40) {
  if (!pendingList.length) return;
  let i = 0;
  const step = () => {
    const end = Math.min(i + chunkSize, pendingList.length);
    for (; i < end; i++) {
      const p = pendingList[i];
      syncComentarioCell(p.comentarioMeta, p.translationMeasureEl);
    }
    if (i < pendingList.length) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function setupLemmaToggleAll() {
  const btn = document.getElementById("lemmaExpandAll");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const lemmas = getVisibleLemmas();
    if (!lemmas.length) return;
    const allExpanded = lemmas.every(l => expandedLemmas.has(l));
    const tbody = document.querySelector("#dataTable tbody");
    if (!tbody) return;

    lemmas.forEach(lemma => {
      const groupRow = tbody.querySelector(`tr.lemma-group-row[data-lemma="${CSS.escape(lemma)}"]`);
      if (!groupRow) return;
      const toggleBtn = groupRow.querySelector(".lemma-toggle");
      const isExpanded = expandedLemmas.has(lemma);
      if (allExpanded && isExpanded) {
        expandedLemmas.delete(lemma);
        groupRow.classList.remove("expanded");
        if (toggleBtn) toggleBtn.textContent = "+";
        removeLemmaDetailRows(tbody, lemma);
      } else if (!allExpanded && !isExpanded) {
        expandedLemmas.add(lemma);
        groupRow.classList.add("expanded");
        if (toggleBtn) toggleBtn.textContent = "−";
        const item = lastLemmaItems.find(it => it.lemma === lemma);
        if (item) {
          const stripe = groupRow.classList.contains("stripe-alt");
          appendLemmaDetailRowsAfter(groupRow, item, stripe);
        }
      }
    });
    lastLemmaPageOffsets = computeLemmaPageOffsets(lastLemmaItems, maxDisplayRows);
    updatePaginationControls(lastLemmaItems.length);
    updateLemmaToggleButton();
  });
}

function updateLemmaToggleButton() {
  const btn = document.getElementById("lemmaExpandAll");
  if (!btn) return;
  if (tableViewMode !== "lemmas") {
    btn.hidden = true;
    return;
  }
  const lemmas = getVisibleLemmas();
  btn.hidden = false;
  if (!lemmas.length) {
    btn.textContent = "+";
    btn.disabled = true;
    return;
  }
  btn.disabled = false;
  btn.textContent = lemmas.every(l => expandedLemmas.has(l)) ? "−" : "+";
}

function setupComentarioToggleAll() {
  const btn = document.getElementById("comentarioExpandAll");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const expandableRows = getExpandableRenderRows(lastRenderRows);
    if (!expandableRows.length) return;
    const y = getTableScrollTop();
    if (areAllExpandableCommentsExpanded(expandableRows)) {
      expandableRows.forEach(r => expandedComments.delete(r._rid));
    } else {
      expandableRows.forEach(r => expandedComments.add(r._rid));
    }
    renderTable(lastRenderRows, lastRenderTotal);
    requestAnimationFrame(() => {
      setTableScroll(y);
    });
  });
}

function updateComentarioToggleButton(rows) {
  const btn = document.getElementById("comentarioExpandAll");
  if (!btn) return;
  const expandableRows = getExpandableRenderRows(rows);
  if (!expandableRows.length) {
    btn.textContent = "+";
    btn.disabled = true;
    return;
  }
  btn.disabled = false;
  btn.textContent = areAllExpandableCommentsExpanded(expandableRows) ? "−" : "+";
}

function resetComentarioState() {
  expandedComments.clear();
  expandableComments.clear();
  commentAnchors.clear();
}

function setupPaginationControls() {
  const prevs = [document.getElementById("pagePrev")];
  const nexts = [document.getElementById("pageNext")];
  const firsts = [document.getElementById("pageFirst")];
  const lasts = [document.getElementById("pageLast")];

  const hookPrev = btn => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      if (displayOffset <= 0) return;
      if (tableViewMode === "lemmas") {
        const pageIdx = findLemmaPageIndex(displayOffset);
        if (pageIdx <= 0) return;
        displayOffset = lastLemmaPageOffsets[pageIdx - 1] || 0;
      } else {
        displayOffset = Math.max(0, displayOffset - maxDisplayRows);
      }
      applyFilters(false, getTableRestoreOptions(btn));
    });
  };
  const hookNext = btn => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      if (tableViewMode === "lemmas") {
        const pageIdx = findLemmaPageIndex(displayOffset);
        const next = lastLemmaPageOffsets[pageIdx + 1];
        if (next == null) return;
        displayOffset = next;
      } else {
        displayOffset += maxDisplayRows;
      }
      applyFilters(false, getTableRestoreOptions(btn));
    });
  };
  const hookFirst = btn => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      if (displayOffset === 0) return;
      displayOffset = 0;
      applyFilters(false, getTableRestoreOptions(btn));
    });
  };
  const hookLast = btn => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      if (!lastRenderTotal) return;
      let maxOffset;
      if (tableViewMode === "lemmas") {
        maxOffset = lastLemmaPageOffsets[lastLemmaPageOffsets.length - 1] || 0;
      } else {
        const total = lastRenderTotal;
        maxOffset = Math.max(0, total - maxDisplayRows);
      }
      if (displayOffset === maxOffset) return;
      displayOffset = maxOffset;
      applyFilters(false, getTableRestoreOptions(btn));
    });
  };

  [...prevs].forEach(hookPrev);
  [...nexts].forEach(hookNext);
  [...firsts].forEach(hookFirst);
  [...lasts].forEach(hookLast);

  const pageInputs = [document.getElementById("pageInput")];
  pageInputs.forEach(input => {
    if (!input) return;
    const commit = () => {
      const total = lastRenderTotal;
      let totalPages;
      let newOffset;
      if (tableViewMode === "lemmas") {
        totalPages = Math.max(1, lastLemmaPageOffsets.length);
        const page = Math.min(Math.max(1, parseInt(input.value, 10) || 1), totalPages);
        input.value = page;
        newOffset = lastLemmaPageOffsets[page - 1] || 0;
      } else {
        totalPages = Math.max(1, Math.ceil(total / maxDisplayRows));
        const page = Math.min(Math.max(1, parseInt(input.value, 10) || 1), totalPages);
        input.value = page;
        newOffset = (page - 1) * maxDisplayRows;
      }
      if (newOffset === displayOffset) return;
      displayOffset = newOffset;
      applyFilters(false, getTableRestoreOptions(input));
    };
    input.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); commit(); input.blur(); } });
    input.addEventListener("blur", commit);
    input.addEventListener("focus", () => input.select());
  });
}

function updatePaginationControls(total) {
  const prevs = [document.getElementById("pagePrev")].filter(Boolean);
  const nexts = [document.getElementById("pageNext")].filter(Boolean);
  const firsts = [document.getElementById("pageFirst")].filter(Boolean);
  const lasts = [document.getElementById("pageLast")].filter(Boolean);
  if (!prevs.length && !nexts.length && !firsts.length && !lasts.length) return;

  let hasPrev, hasNext, currentPage, totalPages;
  if (tableViewMode === "lemmas") {
    const offsets = lastLemmaPageOffsets && lastLemmaPageOffsets.length
      ? lastLemmaPageOffsets : [0];
    totalPages = Math.max(1, offsets.length);
    const pageIdx = findLemmaPageIndex(displayOffset);
    currentPage = total === 0 ? 1 : pageIdx + 1;
    hasPrev = pageIdx > 0;
    hasNext = pageIdx + 1 < offsets.length;
  } else {
    hasPrev = displayOffset > 0;
    hasNext = displayOffset + maxDisplayRows < total;
    currentPage = total === 0 ? 1 : Math.floor(displayOffset / maxDisplayRows) + 1;
    totalPages = Math.max(1, Math.ceil(total / maxDisplayRows));
  }

  prevs.forEach(btn => (btn.disabled = !hasPrev));
  firsts.forEach(btn => (btn.disabled = !hasPrev));
  nexts.forEach(btn => (btn.disabled = !hasNext));
  lasts.forEach(btn => (btn.disabled = !hasNext));

  const pageInput = document.getElementById("pageInput");
  if (pageInput && document.activeElement !== pageInput) pageInput.value = currentPage;
  const pageTotal = document.getElementById("pageTotal");
  if (pageTotal) pageTotal.textContent = `de ${totalPages} pág.`;
}

function setupSortControls() {
  const buttons = document.querySelectorAll("#dataTable .sort-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", e => {
      const field = btn.dataset.sortField;
      if (!field) return;
      const y = getTableScrollTop();
      if (e.shiftKey) {
        // Shift+click: add/cycle/remove as secondary/tertiary key
        const idx = sortKeys.findIndex(k => k.field === field);
        if (idx === -1) {
          sortKeys.push({ field, dir: "asc" });
        } else if (sortKeys[idx].dir === "asc") {
          sortKeys[idx].dir = "desc";
        } else {
          sortKeys.splice(idx, 1);
        }
      } else {
        // Plain click: single-field sort, cycle asc→desc→off
        if (sortKeys.length === 1 && sortKeys[0].field === field) {
          if (sortKeys[0].dir === "asc") {
            sortKeys = [{ field, dir: "desc" }];
          } else {
            sortKeys = [];
          }
        } else {
          sortKeys = [{ field, dir: "asc" }];
        }
      }
      applyFilters(false, { keepOffset: true, keepCurrent: true, restoreScroll: y });
      updateSortIndicators();
    });
  });
}

function applyManualSort(arr, keys) {
  if (!keys || !keys.length) return;
  arr.sort((a, b) => {
    for (const { field, dir } of keys) {
      const vaRaw = String(getSortFieldValue(a, field));
      const vbRaw = String(getSortFieldValue(b, field));
      const va = buildSortKey(vaRaw);
      const vb = buildSortKey(vbRaw);
      const cmp = alphaNumCollator.compare(va, vb);
      if (cmp !== 0) return dir === "asc" ? cmp : -cmp;
    }
    return compareRecordId(a, b);
  });
}

function getSortFieldValue(row, field) {
  const isDisplayField = TABLE_FIELDS.some(entry => entry.key === field);
  if (isDisplayField) return getDisplayValue(row, field);
  return row[field] ?? "";
}

function buildSortKey(value) {
  const raw = stripHtmlTags ? stripHtmlTags(value) : value;
  return String(raw || "")
    .replace(/^[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+/, "")
    .trim();
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

function compareLemmaPriority(a, b, context) {
  const tierA = context.getTier(a);
  const tierB = context.getTier(b);
  if (tierA !== tierB) return tierA - tierB;
  return comparePriorityOrder(a, b);
}

function compareBrowseOrder(a, b) {
  const browseCmp = (a._browseOrder ?? 0) - (b._browseOrder ?? 0);
  if (browseCmp !== 0) return browseCmp;
  return compareRecordId(a, b);
}

function comparePriorityOrder(a, b) {
  const pa = Number.isFinite(a._prio) ? a._prio : Number.POSITIVE_INFINITY;
  const pb = Number.isFinite(b._prio) ? b._prio : Number.POSITIVE_INFINITY;
  if (pa !== pb) return pa - pb;

  const headA = buildSortKey(getDisplayValue(a, "Texto estandarizado") || getDisplayValue(a, "Escritura original"));
  const headB = buildSortKey(getDisplayValue(b, "Texto estandarizado") || getDisplayValue(b, "Escritura original"));
  const headCmp = alphaNumCollator.compare(headA, headB);
  if (headCmp !== 0) return headCmp;

  const sourceCmp = alphaNumCollator.compare(
    buildSortKey(getDisplayValue(a, "Fuente")),
    buildSortKey(getDisplayValue(b, "Fuente"))
  );
  if (sourceCmp !== 0) return sourceCmp;

  return compareRecordId(a, b);
}

function compareRecordId(a, b) {
  return alphaNumCollator.compare(String(a.record_id || a._rid || ""), String(b.record_id || b._rid || ""));
}

function updateSortIndicators() {
  const buttons = document.querySelectorAll("#dataTable .sort-btn");
  const inLemmasView = tableViewMode === "lemmas";
  buttons.forEach(btn => {
    const field = btn.dataset.sortField;
    const idx = sortKeys.findIndex(k => k.field === field);
    btn.textContent = "";
    btn.classList.remove("sort-child");
    if (idx !== -1) {
      const arrow = sortKeys[idx].dir === "asc" ? "↑" : "↓";
      btn.textContent = arrow;
      if (inLemmasView && field !== "Texto estandarizado") {
        btn.classList.add("sort-child");
        btn.title = "Orden dentro de cada lema";
      } else {
        btn.title = "";
      }
      if (sortKeys.length > 1) {
        const badge = document.createElement("span");
        badge.className = "sort-badge";
        badge.textContent = String(idx + 1);
        btn.appendChild(badge);
      }
    } else {
      btn.textContent = "⇅";
      btn.title = "";
    }
  });
}

function setupSortScopeControls() {
  const selects = [document.getElementById("sortScopeSelect")].filter(Boolean);
  const applyScope = (val, triggerEl = null) => {
    sortScope = val === "page" ? "page" : "all";
    applyFilters(false, getTableRestoreOptions(triggerEl));
    updateSortScopeIndicators();
  };
  selects.forEach(sel => {
    sel.value = sortScope;
    sel.addEventListener("change", () => applyScope(sel.value, sel));
  });
}

function updateSortScopeIndicators() {
  const selects = [document.getElementById("sortScopeSelect")].filter(Boolean);
  selects.forEach(sel => {
    sel.value = sortScope;
  });
}

function setupExportButtons() {
  const btn = document.getElementById("exportMenuBtn");
  const dropdown = document.getElementById("exportMenuDropdown");
  if (!btn || !dropdown) return;

  btn.addEventListener("click", e => {
    e.stopPropagation();
    dropdown.classList.toggle("open");
  });

  document.addEventListener("click", e => {
    if (!dropdown.contains(e.target) && e.target !== btn) {
      dropdown.classList.remove("open");
    }
  });

  dropdown.addEventListener("click", e => {
    const item = e.target.closest(".export-menu-item");
    if (!item) return;
    dropdown.classList.remove("open");
    const kind = item.dataset.export;
    if (kind === "jpeg") exportTableAsImage("jpeg");
    else if (kind === "png") exportTableAsImage("png");
    else if (kind === "csv") exportAsCsv();
  });
}

// ── Export helpers (CSV) ─────────────────────────────────────────────────

function getExportRows() {
  const rows = Array.isArray(lastFilteredRows) ? lastFilteredRows.slice() : [];
  return rows;
}

function downloadBlob(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.download = filename;
  link.href = url;
  link.click();
  URL.revokeObjectURL(url);
}

function csvEscape(value) {
  const s = value == null ? "" : String(value);
  if (/[",\r\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}

function exportAsCsv() {
  const rows = getExportRows();
  if (!rows.length) {
    alert(t("table.export.empty"));
    return;
  }
  const columns = [
    "record_id",
    "Fuente",
    "eid",
    "Texto estandarizado",
    "Escritura original",
    "Traducción",
    "Comentario"
  ];
  const lines = [columns.join(",")];
  rows.forEach(row => {
    const cells = columns.map(col => {
      if (col === "Traducción" || col === "Comentario") {
        return csvEscape(getDisplayValue(row, col));
      }
      return csvEscape(row[col] ?? "");
    });
    lines.push(cells.join(","));
  });
  const BOM = "\uFEFF";
  downloadBlob(BOM + lines.join("\r\n") + "\r\n", t("table.export.csv.filename"), "text/csv;charset=utf-8");
}

function exportTableAsImage(format = "jpeg") {
  const headerTable = getHeaderTable();
  const table = getBodyTable();
  if (!headerTable || !table) return;
  const rows = [];
  const head = headerTable.tHead?.rows[0];
  if (head) {
    rows.push(
      Array.from(head.cells)
        .filter((_, idx) => idx !== 4) // omitir Comentario
        .map(c => {
          const label = c.querySelector("span") ? c.querySelector("span").innerText : c.innerText;
          return (label || "").trim();
        })
    );
  }
  Array.from(table.tBodies[0]?.rows || []).forEach(tr => {
    rows.push(
      Array.from(tr.cells)
        .filter((_, idx) => idx !== 4)
        .map(td => td.innerText.replace(/\s+/g, " ").trim())
    );
  });
  if (!rows.length) return;
  const colCount = Math.max(...rows.map(r => r.length));
  const colWidths = new Array(colCount).fill(80);
  rows.forEach(r => {
    r.forEach((cell, i) => {
      const w = Math.max(colWidths[i], cell.length * 7 + 20);
      colWidths[i] = w;
    });
  });
  const rowHeight = 26;
  const padding = 10;
  const width = colWidths.reduce((a, b) => a + b, 0) + padding * 2;
  const height = rows.length * rowHeight + padding * 2;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);
  ctx.font = "13px Arial, sans-serif";
  ctx.textBaseline = "middle";
  let y = padding + rowHeight / 2;
  rows.forEach((row, rowIdx) => {
    let x = padding;
    const isHeader = rowIdx === 0;
    row.forEach((cell, colIdx) => {
      const w = colWidths[colIdx];
      ctx.fillStyle = isHeader ? "#e4e8ff" : rowIdx % 2 === 0 ? "#fbfcff" : "#ffffff";
      ctx.fillRect(x, y - rowHeight / 2, w, rowHeight);
      ctx.strokeStyle = "#d5daf8";
      ctx.strokeRect(x, y - rowHeight / 2, w, rowHeight);
      ctx.fillStyle = "#1a2468";
      ctx.fillText(cell, x + 8, y, w - 16);
      x += w;
    });
    y += rowHeight;
  });
  const isPng = format === "png";
  const mime = isPng ? "image/png" : "image/jpeg";
  const filename = isPng ? t("table.export.png.filename") : t("table.export.filename");
  if (isPng) {
    canvas.toBlob(b => {
      if (!b) return;
      const link = document.createElement("a");
      link.download = filename;
      link.href = URL.createObjectURL(b);
      link.click();
      URL.revokeObjectURL(link.href);
    }, mime);
  } else {
    canvas.toBlob(b => {
      if (!b) return;
      const link = document.createElement("a");
      link.download = filename;
      link.href = URL.createObjectURL(b);
      link.click();
      URL.revokeObjectURL(link.href);
    }, mime, 0.95);
  }
}

function isQuestionLike(text) {
  if (!text) return false;
  const t = String(text).trim();
  if (!t) return false;
  return t.startsWith("¿") || t.endsWith("?");
}

// For Wimmer 2021: auto-translated Traducciones sometimes turn French relative
// clauses ("Qui est pointu.") into Spanish questions ("¿Quién es astuto?").
// Pull the first plain-text definition block out of the Comentario; return ""
// if the Comentario also presents the sense as a question (i.e. the word
// really is an interrogative, like TLEHHUATL or CANNEL).
function extractWimmerDefinition(commentaryHtml, lemma) {
  if (!commentaryHtml) return "";
  const blocks = String(commentaryHtml)
    .split(/\s*(?:<br\s*\/?>\s*){2,}/i)
    .map(b => b.trim())
    .filter(Boolean);
  const lemmaKey = lemma ? normalizeString(String(lemma)).toLowerCase() : "";

  for (const block of blocks) {
    const plain = collapseWhitespace(stripHtmlTags(block)).trim();
    if (!plain) continue;

    // Markup-wrapped block with question content → legitimate interrogative.
    if (/^</.test(block)) {
      if (/[¿?]/.test(plain)) return "";
      continue;
    }

    // Single-token blocks are lemma headers ("tlehhuâtl:"); skip.
    if (!/\s/.test(plain)) continue;

    // Skip grammar-metadata line ("lemma, éventuel de ...").
    if (lemmaKey) {
      const firstToken = normalizeString((block.match(/^[^\s,:.;()<]+/) || [""])[0]).toLowerCase();
      if (firstToken && (lemmaKey.startsWith(firstToken) || firstToken.startsWith(lemmaKey))) continue;
    }

    if (/^Forma?\s*:/i.test(plain)) continue;
    if (isQuestionLike(plain)) return "";
    return plain;
  }
  return "";
}

// Wimmer 2021 references "Launey Introd" / "Andrews Introd" (his grammar and
// Andrews' grammar) appear in Comentario with varied forms — OCR typos in the
// source ("lntrod", "Intod", "Intro", truncated) and auto-translation garbling
// in the Spanish copy ("Introducción", "introdujo", "presentó"). Normalize
// them all to the canonical "Author Introd" form.
const WIMMER_REF_REGEX = /\b(Launey|Andrews)\s+(?:Introducción|Introduction|introdujo|presentó|lntrod|Intod|Intro|introd)\b\.?/g;

function normalizeWimmerReferences(text) {
  if (!text) return text;
  return String(text).replace(WIMMER_REF_REGEX, "$1 Introd");
}

function getWimmerComentario(row, comentarioKey) {
  const raw = row[comentarioKey];
  if (!raw) return raw ?? "";
  const cacheKey = `__wimmerCom_${comentarioKey}`;
  if (row[cacheKey] !== undefined) return row[cacheKey];
  const normalized = normalizeWimmerReferences(raw);
  row[cacheKey] = normalized;
  return normalized;
}

function getWimmerTraduccion(row, traduccionKey, comentarioKey) {
  const raw = row[traduccionKey];
  if (!raw || !isQuestionLike(raw)) return raw ?? "";
  const cacheKey = `__wimmerDef_${traduccionKey}`;
  if (row[cacheKey] !== undefined) return row[cacheKey] || raw;
  const def = extractWimmerDefinition(getWimmerComentario(row, comentarioKey), row["Texto estandarizado"]);
  row[cacheKey] = def;
  return def || raw;
}

function getDisplayValue(row, fieldKey) {
  if (wimmerShowEs && row.Fuente === "2021 Wimmer") {
    const esKey = fieldKey === "Traducción" ? "Traducción (es)"
                : fieldKey === "Comentario"  ? "Comentario (es)"
                : null;
    if (esKey && row[esKey]) {
      if (fieldKey === "Traducción") return getWimmerTraduccion(row, "Traducción (es)", "Comentario (es)");
      if (fieldKey === "Comentario") return getWimmerComentario(row, "Comentario (es)");
      return row[esKey];
    }
  }
  if (row.Fuente === "2021 Wimmer") {
    if (fieldKey === "Traducción") return getWimmerTraduccion(row, "Traducción", "Comentario");
    if (fieldKey === "Comentario") return getWimmerComentario(row, "Comentario");
  }
  return row[fieldKey] ?? "";
}

// ── Wimmer ───────────────────────────────────────────────────────────────────

function setupWimmerTranslate() {
  const langToggle = document.getElementById("wLangToggle");
  if (langToggle) {
    langToggle.textContent = wimmerShowEs ? "ES" : "FR";
    langToggle.classList.toggle("active", wimmerShowEs);
    langToggle.addEventListener("click", () => {
      wimmerShowEs = !wimmerShowEs;
      langToggle.textContent = wimmerShowEs ? "ES" : "FR";
      langToggle.classList.toggle("active", wimmerShowEs);
      normalizationCache = new Map();
      applyFilters(false, getTableRestoreOptions());
    });
  }
}

function sanitizeInput(value) {
  const raw = value == null ? "" : String(value);
  return stripHtmlTags(raw).trim();
}


// =============== Highlight ===============
function applyHighlights(rawValue, fieldKey) {
  if (fieldKey === "Fuente") {
    return rawValue == null ? "" : String(rawValue);
  }
  const val = rawValue == null ? "" : String(rawValue);
  const allFilters = activeFilters.filter(f => f.field === fieldKey && f.value && !f.negate);
  if (!allFilters.length) return val;

  const wordFilters = allFilters.filter(f => normalizeScope(f.scope) === "word");
  const cellFilters = allFilters.filter(f => normalizeScope(f.scope) !== "word");

  let rendered = val;

  // Word scope first: wraps complete tokens before cell-scope can split them.
  if (wordFilters.length) {
    const segments = rendered.split(/(<[^>]+>|\s+)/g);
    rendered = segments
      .map(seg => {
        if (!seg || /^<[^>]+>$/.test(seg) || /^\s+$/.test(seg)) return seg;
        if (tokenMatchesWordFilters(seg, wordFilters)) return `<mark class="hl">${seg}</mark>`;
        if (oldSpanishMode && tokenMatchesWordFiltersOS(seg, wordFilters)) return `<mark class="hl-os">${seg}</mark>`;
        return seg;
      })
      .join("");
  }

  if (cellFilters.length) {
    const regex = buildHighlightRegex(cellFilters);
    const osRegex = oldSpanishMode ? buildOsHighlightRegex(cellFilters) : null;
    if (regex || osRegex) {
      const parts = rendered.split(/(<[^>]+>)/g);
      rendered = parts
        .map(part => {
          if (/^<[^>]+>$/.test(part)) return part;
          if (regex && osRegex) return highlightSegmentDual(part, regex, osRegex);
          if (regex) return highlightSegment(part, regex);
          return highlightSegment(part, osRegex);
        })
        .join("");
    }
  }

  return rendered;
}

function reverseOsExpand(str) {
  let result = "";
  for (let i = 0; i < str.length; i++) {
    const ch = str[i];
    if (ch === "b") result += "[bv]";
    else if (ch === "f") result += "(?:f|ph)";
    else if (ch === "t") result += "(?:t|th)";
    else if (ch === "c") result += "(?:c|qu)";
    else if (ch === "n") result += "(?:n|nn)";
    else if (ch === "s") result += "(?:s|ss)";
    else result += escapeRegex(ch);
  }
  return result;
}

function buildOsHighlightRegex(filters) {
  const sources = [];
  filters.forEach(filter => {
    const rawVal = (filter.value ?? "").trim();
    if (/^\/(.+)\/([gimsuy]*)$/.test(rawVal)) return;
    if (rawVal.startsWith("(") && rawVal.includes("||")) return;
    const parsed = parseFilterValue(rawVal, filter.mode);
    if (!parsed || parsed.hasRegex || parsed.hasWildcards) return;
    const literal = parsed.strict || parsed.loose;
    if (!literal) return;
    const expanded = reverseOsExpand(literal);
    const relaxed = normalizePatternSource(stripAnchors(expanded));
    sources.push(relaxed);
  });
  if (!sources.length) return null;
  try {
    return new RegExp(`(${sources.join("|")})`, "gi");
  } catch {
    return null;
  }
}

function highlightSegmentDual(text, normalRegex, osRegex) {
  let combined;
  try {
    combined = new RegExp(`(${normalRegex.source})|(${osRegex.source})`, "gi");
  } catch {
    return highlightSegment(text, normalRegex);
  }
  const norm = normalRegex.accentSensitive ? text.toLowerCase() : normalizeString(text);
  let result = "";
  let lastIndex = 0;
  combined.lastIndex = 0;
  let match;
  while ((match = combined.exec(norm)) !== null) {
    const start = match.index;
    const end = combined.lastIndex;
    result += text.slice(lastIndex, start);
    const cssClass = match[1] !== undefined ? "hl" : "hl-os";
    result += `<mark class="${cssClass}">${text.slice(start, end)}</mark>`;
    lastIndex = end;
    if (match[0].length === 0) combined.lastIndex++;
  }
  result += text.slice(lastIndex);
  return result;
}

// Strip regex anchors (^ and $) from a pattern source.
// In practice none of our highlight patterns use [^...] negated classes, so a global strip is safe.
function stripAnchors(src) {
  return src.replace(/\^/g, "").replace(/\$/g, "");
}

// Normalize a regex pattern source for accent-insensitive matching.
// Only safe when the pattern has no character classes (no `[`).
function normalizePatternSource(src) {
  return src.includes("[") ? src : normalizeString(src);
}

function buildHighlightRegex(filters) {
  const sources = [];
  let isAccentSensitive = false;
  filters.forEach(filter => {
    const rawVal = (filter.value ?? "").trim();
    const andParts = extractContainsBothParts(rawVal);
    if (andParts && andParts.length) {
      if (accentSensitiveMode) isAccentSensitive = true;
      andParts.forEach(p => {
        const expanded = convertWildcardPatternAllowRegex(expandVCPlaceholders(p));
        if (expanded) sources.push(accentSensitiveMode ? expanded : normalizePatternSource(expanded));
      });
      return;
    }
    const parsed = parseFilterValue(filter.value ?? "", filter.mode);
    if (parsed.accentSensitive) isAccentSensitive = true;
    let rx = parsed.strictRegex || parsed.looseRegex;
    if (!rx) {
      const literal = parsed.strict || parsed.loose;
      if (literal) {
        const pattern = escapeRegex(String(literal)).replace(/\s+/g, "\\W*");
        rx = new RegExp(pattern, "i");
      }
    }
    if (!rx) return;
    const relaxed = stripAnchors(rx.source);
    // Accent-sensitive queries: lowercase the pattern but preserve accents.
    // Plain queries: full normalization (accent-blind).
    const adjusted = parsed.accentSensitive
      ? relaxed.toLowerCase()
      : normalizePatternSource(relaxed);
    sources.push(adjusted);
  });
  if (!sources.length) return null;
  try {
    const rx = new RegExp(`(${sources.join("|")})`, "gi");
    rx.accentSensitive = isAccentSensitive;
    return rx;
  } catch {
    return null;
  }
}

function highlightSegment(text, regex) {
  // For accent-sensitive queries: match on lowercase-only text (preserve accents).
  // For plain queries: match on fully-normalized text (accent-blind).
  // In both cases, positions map 1-to-1 back to the original displayed text.
  const norm = regex.accentSensitive ? text.toLowerCase() : normalizeString(text);
  let result = "";
  let lastIndex = 0;
  regex.lastIndex = 0;
  let match;
  while ((match = regex.exec(norm)) !== null) {
    const start = match.index;
    const end = regex.lastIndex;
    result += text.slice(lastIndex, start);
    result += `<mark class="hl">${text.slice(start, end)}</mark>`;
    lastIndex = end;
    if (match[0].length === 0) regex.lastIndex++;
  }
  result += text.slice(lastIndex);
  return result;
}

function partitionWordFiltersByGroup(filters) {
  const groups = new Map();
  const singles = [];
  filters.forEach(f => {
    if (f.wordGroupId) {
      if (!groups.has(f.wordGroupId)) groups.set(f.wordGroupId, []);
      groups.get(f.wordGroupId).push(f);
    } else {
      singles.push(f);
    }
  });
  return { groups, singles };
}

function tokenMatchesWordFilters(token, filters) {
  const stripped = stripHtmlTags(token);
  const normalizedToken = normalizeString(stripped);
  const lowercaseToken = stripped.toLowerCase(); // accent-preserved
  const testFilter = filter => {
    const query = buildFilterQuery(filter);
    const base = query.accentSensitive ? lowercaseToken : normalizedToken;
    const candidate = query.allowLoose
      ? collapseWhitespace(stripPunctuationCharacters(base))
      : base;
    if (query.hasRegex && query.strictRegex) {
      const src = query.strictRegex.source;
      try {
        const adjSrc = query.accentSensitive ? src.toLowerCase() : normalizePatternSource(src);
        const adjRx = adjSrc === src ? query.strictRegex : new RegExp(adjSrc, query.strictRegex.flags);
        return adjRx.test(candidate);
      } catch {
        return query.strictRegex.test(candidate);
      }
    }
    return candidateMatchesQuery(candidate, query, filter.mode, query.allowLoose);
  };
  const { groups, singles } = partitionWordFiltersByGroup(filters);
  for (const group of groups.values()) {
    if (group.every(testFilter)) return true;
  }
  return singles.some(testFilter);
}

function tokenMatchesWordFiltersOS(token, filters) {
  const normalizedToken = normalizeOldSpanish(normalizeString(stripHtmlTags(token)));
  const testFilter = filter => {
    const query = buildFilterQuery(filter);
    const candidate = query.allowLoose
      ? collapseWhitespace(stripPunctuationCharacters(normalizedToken))
      : normalizedToken;
    return candidateMatchesQuery(candidate, query, filter.mode, query.allowLoose);
  };
  const { groups, singles } = partitionWordFiltersByGroup(filters);
  for (const group of groups.values()) {
    if (group.every(testFilter)) return true;
  }
  return singles.some(testFilter);
}

function extractContainsBothParts(text) {
  if (!text || !text.startsWith("(") || !text.endsWith(")")) return null;
  if (!text.includes("||")) return null;
  return splitTopLevel(text.slice(1, -1), "||");
}

// =============== Fuentes =================
function splitFuenteLabel(name) {
  const m = name.match(/^(\S+)\s+(.+)$/);
  if (m && /\d/.test(m[1])) return { year: m[1], title: m[2] };
  return { year: "", title: name };
}

function updateFuenteCount() {
  const el = document.getElementById("fuenteCount");
  if (!el) return;
  const n = selectedFuentes.size;
  const total = FUENTE_OPTIONS.length;
  el.textContent = `${n}/${total}`;
  el.classList.toggle("fuente-count--full", n === total);
  el.classList.toggle("fuente-count--empty", n === 0);
}

function renderFuenteList() {
  const container = document.getElementById("fuenteList");
  if (!container) return;
  container.innerHTML = "";
  FUENTE_OPTIONS.forEach(name => {
    const { year, title } = splitFuenteLabel(name);
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "fuente-chip";
    chip.dataset.fuente = name;
    chip.setAttribute("aria-pressed", String(selectedFuentes.has(name)));
    if (year) {
      const yearEl = document.createElement("span");
      yearEl.className = "fuente-chip-year";
      yearEl.textContent = year;
      chip.appendChild(yearEl);
    }
    const titleEl = document.createElement("span");
    titleEl.className = "fuente-chip-title";
    titleEl.textContent = title;
    chip.appendChild(titleEl);
    chip.addEventListener("click", () => {
      const next = chip.getAttribute("aria-pressed") !== "true";
      chip.setAttribute("aria-pressed", String(next));
      toggleFuente(name, next);
    });
    container.appendChild(chip);
  });
  updateFuenteCount();
}

function toggleFuente(name, isChecked) {
  if (isChecked) {
    selectedFuentes.add(name);
  } else {
    selectedFuentes.delete(name);
  }
  updateFuenteCount();
  applyFuenteFilters();
}

function setupFuenteActions() {
  const fillBtn = document.getElementById("fuenteFill");
  if (fillBtn) {
    fillBtn.addEventListener("click", () => {
      FUENTE_OPTIONS.forEach(name => selectedFuentes.add(name));
      renderFuenteList();
      applyFuenteFilters();
    });
  }
  const clearBtn = document.getElementById("fuenteClear");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      selectedFuentes.clear();
      renderFuenteList();
      applyFuenteFilters();
    });
  }
}

function applyFuenteFilters(options = {}) {
  removeOwnerFilters(FUENTE_OWNER);
  resetComentarioState();
  const totalOptions = FUENTE_OPTIONS.length;
  const selectedCount = selectedFuentes.size;
  // Si no hay selección, se filtra todo afuera (sin coincidencias).
  if (selectedCount === 0) {
    lastFilteredRows = [];
    lastRenderRows = [];
    lastRenderTotal = 0;
    lastLemmaItems = [];
    renderTable([], 0);
    return;
  }
  if (selectedCount === totalOptions) {
    applyFilters(false, options);
    return;
  }
  appendFilter("Fuente", "exact", new Set(selectedFuentes), "AND", false, "whole", {
    owner: FUENTE_OWNER,
    type: "fuenteSet"
  });
  applyFilters(false, options);
}

function getFieldI18nKey(fieldKey) {
  switch (fieldKey) {
    case "Escritura original":
      return "field.paleografia";
    case "Texto estandarizado":
      return "field.grafia";
    case "Traducción":
      return "field.traduccion";
    case "Comentario":
      return "field.comentario";
    case "Fuente":
      return "table.header.fuente";
    default:
      return "";
  }
}

// ── Compare / lemma helpers (shared by inline compare and lemmas views) ──

function compareLemmaRows(a, b) {
  const pa = Number.isFinite(a._prio) ? a._prio : Number.POSITIVE_INFINITY;
  const pb = Number.isFinite(b._prio) ? b._prio : Number.POSITIVE_INFINITY;
  if (pa !== pb) return pa - pb;
  const originalCmp = alphaNumCollator.compare(
    buildSortKey(a["Escritura original"]),
    buildSortKey(b["Escritura original"])
  );
  if (originalCmp !== 0) return originalCmp;
  return compareRecordId(a, b);
}

function getBrowseDisplayedTranslation(row) {
  return collapseWhitespace(stripHtmlTags(String(getDisplayValue(row, "Traducción") || ""))).trim();
}

function getBrowseNormalizedTranslation(row) {
  return collapseWhitespace(normalizeString(stripHtmlTags(String(getDisplayValue(row, "Traducción") || "")))).trim();
}

function collectBrowseTranslations(rows) {
  const stats = new Map();
  rows.forEach(row => {
    const normalized = getBrowseNormalizedTranslation(row);
    const display = getBrowseDisplayedTranslation(row);
    if (!normalized || !display) return;
    const existing = stats.get(normalized);
    if (existing) {
      existing.count += 1;
    } else {
      stats.set(normalized, { display, normalized, count: 1 });
    }
  });
  const ranked = [...stats.values()].sort((a, b) => {
    if (b.count !== a.count) return b.count - a.count;
    return alphaNumCollator.compare(a.normalized, b.normalized);
  });
  return {
    count: stats.size,
    sample: ranked.slice(0, 3).map(entry => entry.display)
  };
}

function buildLemmaGroupRow(item) {
  const tr = document.createElement("tr");
  tr.className = "lemma-group-row";
  tr.dataset.lemma = item.lemma;
  if (expandedLemmas.has(item.lemma)) tr.classList.add("expanded");

  const headerKeys = new Set(["Texto estandarizado", "Escritura original", "Traducción"]);
  const headerSpan = TABLE_FIELDS.filter(f => headerKeys.has(f.key) && !hiddenColumns.has(f.key)).length;
  const edicionVisible = !hiddenColumns.has("Texto estandarizado");
  let headerRendered = false;

  TABLE_FIELDS.forEach(field => {
    if (headerKeys.has(field.key)) {
      if (headerRendered) return;
      if (!headerSpan) return;
      headerRendered = true;

      const td = document.createElement("td");
      td.dataset.field = edicionVisible ? "Texto estandarizado" : field.key;
      if (headerSpan > 1) td.colSpan = headerSpan;

      const wrap = document.createElement("div");
      wrap.className = "lemma-edicion-cell";

      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "lemma-toggle";
      toggle.setAttribute("aria-label", "Expandir/Colapsar");
      toggle.textContent = expandedLemmas.has(item.lemma) ? "−" : "+";
      wrap.appendChild(toggle);

      const title = document.createElement("span");
      title.className = "lemma-title";
      title.textContent = item.lemma;
      wrap.appendChild(title);

      const count = document.createElement("span");
      count.className = "lemma-count";
      count.textContent = `(${item.rowCount})`;
      count.title = t("browse.meta.counts", {
        sources: item.sourceCount,
        rows: item.rowCount,
        translations: item.translationCount
      });
      wrap.appendChild(count);

      const action = document.createElement("button");
      action.type = "button";
      action.className = "browse-compare-btn";
      action.dataset.browseCompare = item.lemma;
      action.textContent = t("browse.compare");
      wrap.appendChild(action);

      td.appendChild(wrap);
      tr.appendChild(td);
      return;
    }

    const td = document.createElement("td");
    td.dataset.field = field.key;
    if (field.key === "Fuente") {
      td.textContent = String(item.sourceCount || 0);
      if (item.sources && item.sources.length) td.title = item.sources.join(", ");
    } else {
      td.textContent = "";
    }
    tr.appendChild(td);
  });

  return tr;
}

function toggleLemmaExpansion(groupRow, lemma) {
  const tbody = groupRow.parentElement;
  if (!tbody) return;
  const expanded = expandedLemmas.has(lemma);
  const toggleBtn = groupRow.querySelector(".lemma-toggle");
  if (expanded) {
    expandedLemmas.delete(lemma);
    groupRow.classList.remove("expanded");
    if (toggleBtn) toggleBtn.textContent = "+";
    removeLemmaDetailRows(tbody, lemma);
  } else {
    expandedLemmas.add(lemma);
    groupRow.classList.add("expanded");
    if (toggleBtn) toggleBtn.textContent = "−";
    const item = lastLemmaItems.find(it => it.lemma === lemma);
    if (item) {
      const stripe = groupRow.classList.contains("stripe-alt");
      appendLemmaDetailRowsAfter(groupRow, item, stripe);
    }
  }
  lastLemmaPageOffsets = computeLemmaPageOffsets(lastLemmaItems, maxDisplayRows);
  updatePaginationControls(lastLemmaItems.length);
  updateLemmaToggleButton();
}

// ── View-mode helpers (rows / lemmas) ─────────────────────────────────

function syncDataPanelViewAttribute() {
  const panel = document.querySelector(".data-panel");
  if (panel) panel.dataset.viewMode = tableViewMode;
}

function updateViewToggleButtons() {
  document.querySelectorAll(".view-btn[data-view]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.view === tableViewMode);
  });
}

function updateViewToggleLabels() {
  updateViewToggleButtons();
}

function setViewMode(next) {
  if (next !== "rows" && next !== "lemmas") return;
  if (tableViewMode === next) return;
  tableViewMode = next;
  displayOffset = 0;
  if (next === "lemmas" && hiddenColumns.has("Texto estandarizado")) {
    hiddenColumns.delete("Texto estandarizado");
    syncColumnLayout();
  }
  updateViewToggleButtons();
  applyFilters();
}

function setupViewToggle() {
  document.querySelectorAll(".view-btn[data-view]").forEach(btn => {
    btn.addEventListener("click", () => {
      setViewMode(btn.dataset.view);
    });
  });
  updateViewToggleButtons();
}

// ── Compare chip (synthetic filter on Texto estandarizado) ──────────

function hasCompareChip() {
  return activeFilters.some(f => f.owner === COMPARE_OWNER);
}

function setCompareChip(lemma) {
  const query = sanitizeInput(lemma).trim();
  if (!query) return;
  activeFilters = activeFilters.filter(f => f.owner !== COMPARE_OWNER);
  appendFilter("Texto estandarizado", "exact", query, "AND", false, "whole", {
    owner: COMPARE_OWNER,
    type: "compare",
    strictCompare: true
  });
  displayOffset = 0;
  renderActiveFilterChips();
  applyFilters();
}

function removeCompareChip() {
  if (!hasCompareChip()) return;
  activeFilters = activeFilters.filter(f => f.owner !== COMPARE_OWNER);
  renderActiveFilterChips();
  applyFilters();
}

// ── Reverse lookup chip (meaning → ranked lemmas) ───────────────────

function hasReverseChip() {
  return activeFilters.some(f => f.owner === REVERSE_OWNER);
}

function setReverseChip(query, options = {}) {
  const val = sanitizeInput(query).trim();
  activeFilters = activeFilters.filter(f => f.owner !== REVERSE_OWNER);
  if (!val) {
    renderActiveFilterChips();
    applyFilters();
    return;
  }
  const fields = options.includeComment ? ["Traducción", "Comentario"] : ["Traducción"];
  appendFilter("Traducción", "any", val, "AND", false, "word", {
    owner: REVERSE_OWNER,
    type: "reverse",
    fields
  });
  if (tableViewMode !== "rows") {
    tableViewMode = "rows";
    updateViewToggleButtons();
  }
  displayOffset = 0;
  renderActiveFilterChips();
  applyFilters();
}

function removeReverseChip() {
  if (!hasReverseChip()) return;
  activeFilters = activeFilters.filter(f => f.owner !== REVERSE_OWNER);
  renderActiveFilterChips();
  applyFilters();
}

function setupReverseLookup() {
  const input = document.getElementById("reverseInput");
  const submit = document.getElementById("reverseSubmit");
  const clear = document.getElementById("reverseClear");
  const includeComment = document.getElementById("reverseIncludeComment");
  if (!input || !submit) return;

  function run() {
    const query = input.value.trim();
    if (!query) {
      removeReverseChip();
      return;
    }
    setReverseChip(query, { includeComment: !!(includeComment && includeComment.checked) });
  }

  submit.addEventListener("click", run);
  input.addEventListener("keydown", e => {
    if (e.key === "Enter") {
      e.preventDefault();
      run();
    } else if (e.key === "Escape") {
      input.value = "";
    }
  });
  if (clear) {
    clear.addEventListener("click", () => {
      input.value = "";
      removeReverseChip();
    });
  }
  if (includeComment) {
    includeComment.addEventListener("change", () => {
      if (hasReverseChip() && input.value.trim()) run();
    });
  }
}

function setupEdicionCellClick() {
  const tbody = document.querySelector("#dataTable tbody");
  if (!tbody) return;
  tbody.addEventListener("click", e => {
    const cmpBtn = e.target.closest(".browse-compare-btn[data-browse-compare]");
    if (cmpBtn) {
      e.stopPropagation();
      setCompareChip(cmpBtn.dataset.browseCompare || "");
      return;
    }
    const cell = e.target.closest("td");
    if (!cell) return;
    const tr = cell.closest("tr");
    if (!tr) return;
    if (tr.classList.contains("lemma-group-row")) {
      toggleLemmaExpansion(tr, tr.dataset.lemma || "");
      return;
    }
  });
}

function buildLemmaItemsFromRows(rows) {
  const map = new Map();
  rows.forEach(row => {
    const lemma = sanitizeInput(row["Texto estandarizado"]);
    if (!lemma) return;
    let entry = map.get(lemma);
    if (!entry) {
      entry = { lemma, rows: [] };
      map.set(lemma, entry);
    }
    entry.rows.push(row);
  });
  const items = [];
  const hasUserSort = Array.isArray(sortKeys) && sortKeys.length > 0;
  const childSortKeys = hasUserSort
    ? sortKeys.filter(k => k.field !== "Texto estandarizado")
    : [];
  map.forEach(entry => {
    const sortedRows = entry.rows.slice();
    if (childSortKeys.length) {
      applyManualSort(sortedRows, childSortKeys);
    } else {
      sortedRows.sort(compareLemmaRows);
    }
    const sourceSet = new Set(sortedRows.map(r => r["Fuente"]).filter(Boolean));
    const sources = [...sourceSet].sort((a, b) => alphaNumCollator.compare(a, b));
    const translations = collectBrowseTranslations(sortedRows);
    items.push({
      lemma: entry.lemma,
      rows: sortedRows,
      sources,
      sourceCount: sources.length,
      rowCount: sortedRows.length,
      translationCount: translations.count,
      sampleTranslations: translations.sample
    });
  });
  const lemmaSortKey = hasUserSort
    ? sortKeys.find(k => k.field === "Texto estandarizado")
    : null;
  if (lemmaSortKey) {
    const dir = lemmaSortKey.dir === "desc" ? -1 : 1;
    items.sort((a, b) => dir * alphaNumCollator.compare(a.lemma, b.lemma));
  } else {
    items.sort((a, b) => {
      if (a.sourceCount !== b.sourceCount) return b.sourceCount - a.sourceCount;
      if (a.rowCount !== b.rowCount) return b.rowCount - a.rowCount;
      return alphaNumCollator.compare(a.lemma, b.lemma);
    });
  }
  return items;
}

function renderLemmasIntoTbody(tbody, totalCount) {
  if (!totalCount) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    const visibleCount = TABLE_FIELDS.filter(f => !hiddenColumns.has(f.key)).length;
    td.colSpan = Math.max(1, visibleCount || TABLE_FIELDS.length);
    td.className = "table-empty";
    td.textContent = t("view.lemmas.empty");
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  const offsets = lastLemmaPageOffsets && lastLemmaPageOffsets.length
    ? lastLemmaPageOffsets : [0];
  const pageIdx = findLemmaPageIndex(displayOffset);
  const startIdx = offsets[pageIdx];
  const endIdx = pageIdx + 1 < offsets.length ? offsets[pageIdx + 1] : lastLemmaItems.length;
  const slice = lastLemmaItems.slice(startIdx, endIdx);

  slice.forEach((item, groupIdx) => {
    const stripe = groupIdx % 2 === 0;
    const groupRow = buildLemmaGroupRow(item);
    if (stripe) groupRow.classList.add("stripe-alt");
    tbody.appendChild(groupRow);
    if (expandedLemmas.has(item.lemma)) {
      appendLemmaDetailRowsAfter(groupRow, item, stripe);
    }
  });
}

function appendLemmaDetailRowsAfter(anchorRow, item, stripe) {
  let anchor = anchorRow;
  item.rows.forEach(row => {
    const { tr, comentarioMeta, translationMeasureEl } = buildDataRow(row);
    tr.classList.add("lemma-detail-row");
    tr.dataset.lemma = item.lemma;
    if (stripe) tr.classList.add("stripe-alt");
    const edicionCell = tr.querySelector('td[data-field="Texto estandarizado"]');
    if (edicionCell) edicionCell.textContent = "";
    anchor.after(tr);
    anchor = tr;
    if (comentarioMeta) syncComentarioCell(comentarioMeta, translationMeasureEl);
  });
}

function removeLemmaDetailRows(tbody, lemma) {
  tbody.querySelectorAll(`tr.lemma-detail-row[data-lemma="${CSS.escape(lemma)}"]`)
    .forEach(tr => tr.remove());
}

function computeLemmaPageOffsets(items, pageSize) {
  if (!items.length || pageSize <= 0) return [0];
  const offsets = [0];
  let i = 0;
  while (i < items.length) {
    let cost = 0;
    while (i < items.length) {
      const itemCost = 1 + (expandedLemmas.has(items[i].lemma) ? items[i].rows.length : 0);
      if (cost > 0 && cost + itemCost > pageSize) break;
      cost += itemCost;
      i++;
    }
    if (i < items.length) offsets.push(i);
  }
  return offsets;
}

function findLemmaPageIndex(itemOffset) {
  const offsets = lastLemmaPageOffsets;
  if (!offsets || !offsets.length) return 0;
  for (let p = offsets.length - 1; p >= 0; p--) {
    if (itemOffset >= offsets[p]) return p;
  }
  return 0;
}

function updateTableStatusForLemmas(total) {
  const rowsTotal = lastFilteredRows.length;
  setTableStatusMessage(t("view.lemmas.summary", { lemmas: total, rows: rowsTotal }));
}

function setupPairFinder() {
  const select = document.getElementById("pairColumn");
  if (select) {
    select.innerHTML = "";
    const columns = TABLE_FIELDS.map(field => field.key).filter(key => key !== "Fuente");
    columns.forEach(key => {
      const option = document.createElement("option");
      option.value = key;
      const labelKey = getFieldI18nKey(key);
      if (labelKey) option.dataset.i18n = labelKey;
      option.textContent = labelKey ? t(labelKey) : key;
      select.appendChild(option);
    });
    if (columns.includes("Texto estandarizado")) {
      select.value = "Texto estandarizado";
    }
  }

  const btn = document.getElementById("pairFindBtn");
  if (btn) {
    btn.addEventListener("click", () => runPairFinder());
  }

  const clearBtn = document.getElementById("pairClearBtn");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      lastPairResults = null;
      lastPairMeta = null;
      const resultsEl = document.getElementById("pairResults");
      if (resultsEl) resultsEl.innerHTML = "";
    });
  }
}

function refreshPairFinderUI() {
  if (Array.isArray(lastPairResults)) {
    renderPairResults(lastPairResults, lastPairMeta);
  }
}

function getPairFinderRows(useFilters) {
  if (!useFilters) return dataRows.slice();
  if (!activeFilters.length) return dataRows.slice();
  return dataRows.filter(row => evaluateTextFilters(row));
}

function extractPairTokens(value, wordOnly) {
  const raw = stripHtmlTags(String(value ?? ""));
  if (!raw.trim()) return [];
  const cleaned = collapseWhitespace(stripPunctuationCharacters(raw));
  if (!cleaned) return [];
  if (!wordOnly) return [cleaned];
  return cleaned.split(/\s+/).filter(Boolean);
}

function formatPairForms(formMap) {
  const items = Array.from(formMap.entries()).sort((a, b) => b[1] - a[1]);
  return items
    .map(([form, count]) => (count > 1 ? `${form} (${count})` : form))
    .join(", ");
}

function sumPairCounts(formMap) {
  let total = 0;
  formMap.forEach(count => {
    total += count;
  });
  return total;
}

function getPairSuffixConfigFromInputs() {
  const firstInput = document.getElementById("pairSuffixFirst");
  const secondInput = document.getElementById("pairSuffixSecond");
  const thirdInput = document.getElementById("pairSuffixThird");
  const fourthInput = document.getElementById("pairSuffixFourth");
  const rawFirst = (firstInput?.value || "").trim() || t("pairs.suffixes.first");
  const rawSecond = (secondInput?.value || "").trim() || t("pairs.suffixes.second");
  const rawThird = (thirdInput?.value || "").trim();
  const rawFourth = (fourthInput?.value || "").trim();
  const normFirst = normalizeString(rawFirst);
  const normSecond = normalizeString(rawSecond);
  const normThird = normalizeString(rawThird);
  const normFourth = normalizeString(rawFourth);
  return {
    first: { raw: rawFirst, norm: normFirst },
    second: { raw: rawSecond, norm: normSecond },
    third: { raw: rawThird, norm: normThird },
    fourth: { raw: rawFourth, norm: normFourth },
    labelFirst: rawFirst ? `-${rawFirst}` : t("pairs.header.i"),
    labelSecond: rawSecond ? `-${rawSecond}` : t("pairs.header.a"),
    labelThird: rawThird ? `-${rawThird}` : "",
    labelFourth: rawFourth ? `-${rawFourth}` : ""
  };
}

function runPairFinder() {
  const resultsEl = document.getElementById("pairResults");
  const select = document.getElementById("pairColumn");
  if (!resultsEl || !select) return;

  const useFilters = document.getElementById("pairUseFilters")?.checked ?? true;
  const wordOnly = document.getElementById("pairWordOnly")?.checked ?? true;
  const suffixConfig = getPairSuffixConfigFromInputs();
  const column = select.value;
  const rows = getPairFinderRows(useFilters);

  const pairMap = new Map();
  const suffixes = [
    { key: "first", suffix: suffixConfig.first.norm },
    { key: "second", suffix: suffixConfig.second.norm },
    { key: "third", suffix: suffixConfig.third.norm },
    { key: "fourth", suffix: suffixConfig.fourth.norm }
  ].filter(item => item.suffix);
  const suffixesSorted = suffixes.slice().sort((a, b) => b.suffix.length - a.suffix.length);
  rows.forEach(row => {
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
  });

  const pairs = [];
  pairMap.forEach((entry, stem) => {
    if (entry.first.size && entry.second.size) {
      pairs.push({
        stem,
        first: entry.first,
        second: entry.second,
        third: entry.third,
        fourth: entry.fourth
      });
    }
  });

  pairs.sort((a, b) => alphaNumCollator.compare(a.stem, b.stem));
  renderPairResults(pairs, {
    rows: rows.length,
    labelFirst: suffixConfig.labelFirst,
    labelSecond: suffixConfig.labelSecond,
    labelThird: suffixConfig.labelThird,
    labelFourth: suffixConfig.labelFourth
  });
}

function renderPairResults(pairs, meta) {
  const resultsEl = document.getElementById("pairResults");
  if (!resultsEl) return;
  lastPairResults = pairs;
  lastPairMeta = meta;
  resultsEl.innerHTML = "";

  const summary = document.createElement("div");
  summary.className = "pair-summary";
  const rowCount = meta && typeof meta.rows === "number" ? meta.rows : 0;
  summary.textContent = t("pairs.summary", { pairs: pairs.length, rows: rowCount });
  resultsEl.appendChild(summary);

  if (!pairs.length) {
    const empty = document.createElement("div");
    empty.className = "pair-empty";
    empty.textContent = t("pairs.noResults");
    resultsEl.appendChild(empty);
    return;
  }

  const table = document.createElement("table");
  table.className = "pair-table";
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  const labelFirst = meta?.labelFirst || t("pairs.header.a");
  const labelSecond = meta?.labelSecond || t("pairs.header.i");
  const includeThird = Boolean(meta?.labelThird);
  const includeFourth = Boolean(meta?.labelFourth);
  const headCells = [t("pairs.header.stem"), labelFirst, labelSecond];
  if (includeThird) {
    headCells.push(meta.labelThird);
  }
  if (includeFourth) {
    headCells.push(meta.labelFourth);
  }
  headCells.push(t("pairs.header.total"));
  headCells.forEach(text => {
    const th = document.createElement("th");
    th.textContent = text;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  pairs.forEach(pair => {
    const tr = document.createElement("tr");
    const firstForms = formatPairForms(pair.first);
    const secondForms = formatPairForms(pair.second);
    const thirdForms = includeThird ? formatPairForms(pair.third || new Map()) : "";
    const fourthForms = includeFourth ? formatPairForms(pair.fourth || new Map()) : "";
    const total = [
      sumPairCounts(pair.first),
      sumPairCounts(pair.second),
      includeThird ? sumPairCounts(pair.third || new Map()) : 0,
      includeFourth ? sumPairCounts(pair.fourth || new Map()) : 0
    ].reduce((sum, count) => sum + count, 0);
    const cells = [pair.stem, firstForms, secondForms];
    if (includeThird) {
      cells.push(thirdForms);
    }
    if (includeFourth) {
      cells.push(fourthForms);
    }
    cells.push(String(total));
    cells.forEach(text => {
      const td = document.createElement("td");
      td.textContent = text;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  resultsEl.appendChild(table);
}

// ── Page-size controls ──────────────────────────────────────────
function setupPageSizeControls() {
  const selects = [document.getElementById("pageSizeSelect")].filter(Boolean);
  selects.forEach(sel => {
    sel.value = String(maxDisplayRows);
    sel.addEventListener("change", () => {
      maxDisplayRows = parseInt(sel.value, 10) || 100;
      // Sync both selects
      selects.forEach(s => { s.value = String(maxDisplayRows); });
      displayOffset = 0;
      applyFilters(false, getTableRestoreOptions(sel));
    });
  });
}

// ── Column reorder (shared helper used by zone drag) ────────────
function moveColumn(srcKey, dstKey) {
  const srcIdx = TABLE_FIELDS.findIndex(f => f.key === srcKey);
  const dstIdx = TABLE_FIELDS.findIndex(f => f.key === dstKey);
  if (srcIdx < 0 || dstIdx < 0 || srcIdx === dstIdx) return;

  const [moved] = TABLE_FIELDS.splice(srcIdx, 1);
  TABLE_FIELDS.splice(dstIdx, 0, moved);

  const headerRow = document.querySelector("#dataTable thead tr");
  if (headerRow) {
    const srcTh = headerRow.querySelector(`th[data-field="${CSS.escape(srcKey)}"]`);
    const dstTh = headerRow.querySelector(`th[data-field="${CSS.escape(dstKey)}"]`);
    if (srcTh && dstTh) {
      if (srcIdx < dstIdx) dstTh.after(srcTh);
      else dstTh.before(srcTh);
    }
  }

  const y = getTableScrollTop();
  syncColumnLayout();
  renderTable(lastRenderRows, lastRenderTotal);
  requestAnimationFrame(() => setTableScroll(y));
  saveColumnState();
}

// ── Zone-based header interactions ──────────────────────────────
// Left/right edges: drag=resize, click=show adjacent hidden run.
// Top/bottom bands: drag=reorder, click=hide (circular: last hide restores all).
const ZONE_EDGE_PX = 6;
const ZONE_BAND_PX = 8;
const DRAG_THRESHOLD_PX = 4;

function computeZone(th, clientX, clientY) {
  const rect = th.getBoundingClientRect();
  const x = clientX - rect.left;
  const y = clientY - rect.top;
  if (x < ZONE_EDGE_PX) return "left";
  if (x > rect.width - ZONE_EDGE_PX) return "right";
  if (y < ZONE_BAND_PX) return "top";
  if (y > rect.height - ZONE_BAND_PX) return "bottom";
  return "body";
}

function getHiddenRun(key, side) {
  const idx = TABLE_FIELDS.findIndex(f => f.key === key);
  if (idx < 0) return [];
  const step = side === "left" ? -1 : 1;
  const run = [];
  for (let i = idx + step; i >= 0 && i < TABLE_FIELDS.length; i += step) {
    const k = TABLE_FIELDS[i].key;
    if (!hiddenColumns.has(k)) break;
    run.push(k);
  }
  return run;
}

function hideColumnCircular(key) {
  if (tableViewMode === "lemmas" && key === "Texto estandarizado") return;
  const total = TABLE_FIELDS.length;
  const willBeHidden = hiddenColumns.size + (hiddenColumns.has(key) ? 0 : 1);
  const y = getTableScrollTop();
  if (willBeHidden >= total) {
    hiddenColumns.clear();
  } else {
    hiddenColumns.add(key);
  }
  sortKeys = sortKeys.filter(k => !hiddenColumns.has(k.field));
  syncColumnLayout();
  renderTable(lastRenderRows, lastRenderTotal);
  requestAnimationFrame(() => setTableScroll(y));
  saveColumnState();
}

function showHiddenRun(key, side) {
  const run = getHiddenRun(key, side);
  if (!run.length) return;
  run.forEach(k => hiddenColumns.delete(k));
  const y = getTableScrollTop();
  saveColumnState();
  syncColumnLayout();
  renderTable(lastRenderRows, lastRenderTotal);
  requestAnimationFrame(() => setTableScroll(y));
}

function updateSideLitState() {
  const headerRow = document.querySelector("#dataTable thead tr");
  if (!headerRow) return;
  const visible = TABLE_FIELDS.filter(f => !hiddenColumns.has(f.key));
  const firstVisibleKey = visible.length ? visible[0].key : null;
  const lastVisibleKey = visible.length ? visible[visible.length - 1].key : null;
  TABLE_FIELDS.forEach(field => {
    const th = headerRow.querySelector(`th[data-field="${CSS.escape(field.key)}"]`);
    if (!th) return;
    if (hiddenColumns.has(field.key)) {
      th.classList.remove("th-left-lit", "th-right-lit", "th-edge-outer-left", "th-edge-outer-right");
      return;
    }
    th.classList.toggle("th-left-lit", getHiddenRun(field.key, "left").length > 0);
    th.classList.toggle("th-right-lit", getHiddenRun(field.key, "right").length > 0);
    th.classList.toggle("th-edge-outer-left", field.key === firstVisibleKey);
    th.classList.toggle("th-edge-outer-right", field.key === lastVisibleKey);
  });
}

function setupColumnZoneInteractions() {
  if (!document.getElementById("colHiddenStyleTag")) {
    const style = document.createElement("style");
    style.id = "colHiddenStyleTag";
    TABLE_FIELDS.forEach((_, idx) => {
      style.textContent += `#dataTable.col-hidden-${idx} col:nth-child(${idx + 1}),` +
        `#dataTable.col-hidden-${idx} th:nth-child(${idx + 1}),` +
        `#dataTable.col-hidden-${idx} td:nth-child(${idx + 1}) { display: none; }\n`;
    });
    document.head.appendChild(style);
  }

  const headerTable = getHeaderTable();
  if (!headerTable) return;
  const ths = headerTable.querySelectorAll("thead th[data-field]");

  ths.forEach(th => {
    th.addEventListener("mousemove", e => {
      if (e.buttons) return;
      if (e.target.closest("button, input, a")) {
        th.classList.remove("th-hover-left", "th-hover-right", "th-hover-top", "th-hover-bottom", "th-hover-body");
        return;
      }
      const zone = computeZone(th, e.clientX, e.clientY);
      th.classList.remove("th-hover-left", "th-hover-right", "th-hover-top", "th-hover-bottom", "th-hover-body");
      th.classList.add(`th-hover-${zone}`);
    });
    th.addEventListener("mouseleave", () => {
      th.classList.remove("th-hover-left", "th-hover-right", "th-hover-top", "th-hover-bottom", "th-hover-body");
    });

    th.addEventListener("mousedown", e => {
      if (e.button !== 0) return;
      if (e.target.closest("button, input, a")) return;
      const zone = computeZone(th, e.clientX, e.clientY);
      if (zone === "body") return;
      e.preventDefault();

      const startX = e.clientX;
      const startY = e.clientY;
      const srcKey = th.dataset.field;
      let dragStarted = false;

      // Split-pane resize: dragging a border shrinks one neighbor and grows the
      // other by the same amount; outer edges of the table stay fixed, so table
      // total width is invariant. Both neighbors must be visible; otherwise no-op.
      let leftKey = null;
      let rightKey = null;
      let startLeftWidth = 0;
      let startRightWidth = 0;
      const idx = TABLE_FIELDS.findIndex(f => f.key === srcKey);
      if (zone === "left" || zone === "right") {
        if (zone === "right") {
          leftKey = srcKey;
          let nextIdx = idx + 1;
          while (nextIdx < TABLE_FIELDS.length && hiddenColumns.has(TABLE_FIELDS[nextIdx].key)) nextIdx++;
          if (nextIdx < TABLE_FIELDS.length) rightKey = TABLE_FIELDS[nextIdx].key;
        } else {
          rightKey = srcKey;
          let prevIdx = idx - 1;
          while (prevIdx >= 0 && hiddenColumns.has(TABLE_FIELDS[prevIdx].key)) prevIdx--;
          if (prevIdx >= 0) leftKey = TABLE_FIELDS[prevIdx].key;
        }
        if (leftKey && rightKey) {
          startLeftWidth = getColumnWidth(leftKey);
          startRightWidth = getColumnWidth(rightKey);
        } else {
          leftKey = null;
          rightKey = null;
        }
      }

      function clearDropTargets() {
        headerTable.querySelectorAll(".col-drop-target")
          .forEach(el => el.classList.remove("col-drop-target"));
      }

      function onMove(ev) {
        const dx = ev.clientX - startX;
        const dy = ev.clientY - startY;
        const moved = Math.hypot(dx, dy) > DRAG_THRESHOLD_PX;

        if (zone === "left" || zone === "right") {
          if (!moved) return;
          dragStarted = true;
          if (!leftKey || !rightKey) return; // outer edges: no-op
          const MIN = 50;
          const totalPair = startLeftWidth + startRightWidth;
          let newLeft = startLeftWidth + dx;
          if (newLeft < MIN) newLeft = MIN;
          if (newLeft > totalPair - MIN) newLeft = totalPair - MIN;
          const newRight = totalPair - newLeft;
          columnWidths.set(leftKey, newLeft);
          columnWidths.set(rightKey, newRight);
          syncColumnLayout();
          return;
        }

        if (zone === "top" || zone === "bottom") {
          if (!moved) return;
          dragStarted = true;
          clearDropTargets();
          const under = document.elementFromPoint(ev.clientX, ev.clientY);
          const dstTh = under && under.closest("#dataTable thead th");
          if (dstTh && dstTh.dataset.field && dstTh.dataset.field !== srcKey) {
            dstTh.classList.add("col-drop-target");
          }
        }
      }

      function onUp(ev) {
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);

        if (!dragStarted) {
          if (zone === "top" || zone === "bottom") {
            hideColumnCircular(srcKey);
          } else if (zone === "left" || zone === "right") {
            showHiddenRun(srcKey, zone);
          }
          return;
        }

        if (zone === "top" || zone === "bottom") {
          const under = document.elementFromPoint(ev.clientX, ev.clientY);
          const dstTh = under && under.closest("#dataTable thead th");
          clearDropTargets();
          if (dstTh && dstTh.dataset.field && dstTh.dataset.field !== srcKey) {
            moveColumn(srcKey, dstTh.dataset.field);
          }
        } else if (zone === "left" || zone === "right") {
          saveColumnState();
        }
      }

      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    });
  });

  syncColumnLayout();
}

