const TABLE_FIELDS = [
  { key: "Texto estandarizado", label: "Edición" },
  { key: "Escritura original", label: "Original" },
  { key: "Traducción", label: "Traducción" },
  { key: "Fuente", label: "Fuente" },
  { key: "Comentario", label: "Comentario" }
];

const I18N = {
  es: {
    title: "Base de datos náhuatl",
    subtitle: "Filtra y explora cinco columnas con filtros rápidos y mini‑lenguaje.",
    "tab.filters": "Filtros",
    "tab.sources": "Fuentes",
    "tab.regex": "Regex",
    "tab.pairs": "Pares a/i",
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
    "sources.fill": "Llenar",
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
    "site.tagline": "Busca y filtra cientos de miles de entradas de diccionarios históricos de náhuatl. Usa los filtros para encontrar palabras por escritura, traducción o fuente; los resultados aparecen en la tabla de abajo.",
    "table.header.paleografia": "Original",
    "table.header.grafia": "Edición",
    "table.header.traduccion": "Traducción",
    "table.header.fuente": "Fuente",
    "table.header.comentario": "Comentario",
    "table.sort.label": "Orden:",
    "table.sort.all": "Todos",
    "table.sort.page": "Página",
    "table.rank.label": "Rango:",
    "table.rank.group": "Modo de orden",
    "table.rank.auto": "Auto",
    "table.rank.prio": "Prio",
    "table.rank.title.auto": "Ordena por relevancia y luego por prio",
    "table.rank.title.prio": "Ordena solo por prio",
    "table.status.loading": "Cargando datos…",
    "table.status.none": "Sin registros para mostrar.",
    "table.status.showing": "Registros mostrados: {{start}}-{{end}} de {{total}}",
    "table.status.detail.auto": "{{exact}} lemas exactos · {{phrase}} frases · Auto+Prio",
    "table.status.detail.prio": "{{exact}} lemas exactos · {{phrase}} frases · Prio",
    "table.status.detail.manual": "{{exact}} lemas exactos · {{phrase}} frases · Manual",
    "table.empty": "No hay datos disponibles.",
    "table.export.filename": "tabla.jpg",
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
    "logic.and": "Y",
    "logic.or": "O",
    "chips.zone.and": "Y",
    "chips.zone.or": "O",
    "tab.groups": "Grupos",
    "groups.title": "Grupos activos",
    "groups.clearAll": "Limpiar todo",
    "groups.empty": "Sin grupos activos. Añade filtros desde la pestaña Filtros.",
    "groups.logic.and": "Y",
    "groups.logic.or": "O",
    "groups.edit": "Editar",
    "groups.remove": "Quitar",
    "table.pagesize.label": "Filas:",
    "table.columns": "Cols"
  },
  en: {
    title: "Nahuatl database",
    subtitle: "Filter and explore five columns with quick filters and a mini-language.",
    "tab.filters": "Filters",
    "tab.sources": "Sources",
    "tab.regex": "Regex guide",
    "tab.pairs": "a/i pairs",
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
    "sources.fill": "Select all",
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
    "site.tagline": "Search and filter hundreds of thousands of entries from historical Nahuatl dictionaries. Use the filters to find words by spelling, translation, or source; results appear in the table below.",
    "table.header.paleografia": "Original",
    "table.header.grafia": "Edition",
    "table.header.traduccion": "Translation",
    "table.header.fuente": "Source",
    "table.header.comentario": "Comment",
    "table.sort.label": "Sort:",
    "table.sort.all": "All",
    "table.sort.page": "Page",
    "table.rank.label": "Rank:",
    "table.rank.group": "Ranking mode",
    "table.rank.auto": "Auto",
    "table.rank.prio": "Prio",
    "table.rank.title.auto": "Order by relevance, then prio",
    "table.rank.title.prio": "Order only by prio",
    "table.status.loading": "Loading data…",
    "table.status.none": "No records to show.",
    "table.status.showing": "Records shown: {{start}}-{{end}} of {{total}}",
    "table.status.detail.auto": "{{exact}} exact lemmas · {{phrase}} phrases · Auto+Prio",
    "table.status.detail.prio": "{{exact}} exact lemmas · {{phrase}} phrases · Prio",
    "table.status.detail.manual": "{{exact}} exact lemmas · {{phrase}} phrases · Manual",
    "table.empty": "No data available.",
    "table.export.filename": "table.jpg",
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
    "logic.and": "AND",
    "logic.or": "OR",
    "chips.zone.and": "AND",
    "chips.zone.or": "OR",
    "tab.groups": "Groups",
    "groups.title": "Active groups",
    "groups.clearAll": "Clear all",
    "groups.empty": "No active groups. Add filters from the Filters tab.",
    "groups.logic.and": "AND",
    "groups.logic.or": "OR",
    "groups.edit": "Edit",
    "groups.remove": "Remove",
    "table.pagesize.label": "Rows:",
    "table.columns": "Cols"
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
const selectedFuentes = new Set(FUENTE_OPTIONS);
let lastRenderRows = [];
let lastRenderTotal = 0;
let lastFilteredRows = [];
let displayOffset = 0;
let sortKeys = []; // [{field, dir}]
let sortScope = "all"; // "all" | "page"
const hiddenColumns = new Set();
const alphaNumCollator = new Intl.Collator("es", { numeric: true, sensitivity: "base" });
let wimmerShowEs = true;
let lastFocusedInput = null;
let filterCards = [];
let activeCardIndex = 0;
const expandedComments = new Set();
const commentAnchors = new Map();
let comentarioAllExpanded = false;
let currentLang = "es";
let lastPairResults = null;
let lastPairMeta = null;
let rankingMode = "auto";
let lastRankingSummary = null;

document.addEventListener("DOMContentLoaded", () => {
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
      const otherPanel = document.activeElement?.closest("#sourcesPanel, #regexPanel, #pairsPanel");
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
  setupRankingModeControl();
  updateSortIndicators();
  setupPaginationControls();
  setupPageSizeControls();
  setupColumnResizing();
  setupColumnVisibility();
  setupComentarioToggleAll();
  setupExportButtons();
  renderFuenteList();
  setupFuenteActions();
  setupWimmerTranslate();
  setupPairFinder();
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
  const y = window.scrollY;
  updateAccentLabels();
  updateRankingModeControls();
  if (!dataRows || !dataRows.length) {
    setStatus(t("table.status.loading"));
    return;
  }
  renderTable(lastRenderRows, lastRenderTotal);
  refreshPairFinderUI();
  requestAnimationFrame(() => {
    window.scrollTo({ top: y, behavior: "auto" });
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

function updateRankingModeControls() {
  document.querySelectorAll(".rank-mode").forEach(group => {
    group.setAttribute("aria-label", t("table.rank.group"));
  });
  document.querySelectorAll(".rank-mode-btn").forEach(btn => {
    const mode = btn.dataset.rankMode === "prio" ? "prio" : "auto";
    const active = rankingMode === mode;
    const textKey = mode === "prio" ? "table.rank.prio" : "table.rank.auto";
    const titleKey = mode === "prio" ? "table.rank.title.prio" : "table.rank.title.auto";
    btn.textContent = t(textKey);
    btn.title = t(titleKey);
    btn.setAttribute("aria-label", t(titleKey));
    btn.setAttribute("aria-pressed", String(active));
    btn.classList.toggle("active", active);
  });
}

function setupRankingModeControl() {
  const saved = localStorage.getItem("nahuatl-rank-mode");
  if (saved === "auto" || saved === "prio") {
    rankingMode = saved;
  }
  updateRankingModeControls();
  document.querySelectorAll(".rank-mode-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const nextMode = btn.dataset.rankMode === "prio" ? "prio" : "auto";
      if (nextMode === rankingMode) return;
      rankingMode = nextMode;
      localStorage.setItem("nahuatl-rank-mode", rankingMode);
      updateRankingModeControls();
      applyFilters(false, { keepOffset: true, keepCurrent: true, restoreScroll: window.scrollY });
    });
  });
}

function updateAccentLabels() {
  const key = accentSensitiveMode ? "accent.sensitive" : "accent.insensitive";
  document.querySelectorAll(".accent-btn").forEach(b => {
    b.textContent = t(key);
    b.classList.toggle("active", accentSensitiveMode);
  });
}

function setupAccentToggle() {
  document.querySelectorAll(".accent-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      accentSensitiveMode = !accentSensitiveMode;
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

    // Chip body click → load for editing
    const chip = e.target.closest("[data-group-id]");
    if (chip && !e.target.closest(".chip-remove")) {
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

  // Collect committed groups (not f1 preview, not fuente)
  const groups = new Map();
  activeFilters.forEach(f => {
    if (f.type === "fuenteSet" || f.owner === FUENTE_OWNER || f.owner === "f1") return;
    if (!groups.has(f.owner)) groups.set(f.owner, []);
    groups.get(f.owner).push(f);
  });

  if (!groups.size) {
    bar.style.display = "none";
    bar.innerHTML = "";
    return;
  }
  bar.style.display = "";
  bar.innerHTML = "";

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

  const totalGroups = andIds.length + orIds.length;
  if (totalGroups > 1) {
    const clearAll = document.createElement("button");
    clearAll.type = "button";
    clearAll.className = "chip-clear-all";
    clearAll.textContent = "× limpiar todo";
    bar.appendChild(clearAll);
  }

}

function updateGroupsBadge(count) {
  const badge = document.getElementById("groupsBadge");
  if (!badge) return;
  if (count > 0) {
    badge.textContent = count;
    badge.style.display = "";
  } else {
    badge.style.display = "none";
  }
}

function renderGroupsPanel(groups, andIds, orIds) {
  const list = document.getElementById("groupsList");
  const empty = document.getElementById("groupsEmpty");
  if (!list) return;
  list.innerHTML = "";

  const totalGroups = (andIds ? andIds.length : 0) + (orIds ? orIds.length : 0);
  if (empty) empty.style.display = totalGroups === 0 ? "" : "none";
  if (totalGroups === 0) return;

  const MODE_LABEL = { exact: "exacto", starts: "empieza", any: "contiene", ends: "termina" };

  function makeGroupCard(groupId, filters, logic) {
    const field = filters[0].field;
    const scope = filters[0].scope || "whole";
    const fieldLabel = FIELD_SHORT[field] || field;
    const scopeLabel = scope === "word" ? " · palabra" : "";
    const logicLabel = logic === "OR" ? t("groups.logic.or") : t("groups.logic.and");

    const card = document.createElement("div");
    card.className = "group-card";
    card.dataset.groupId = groupId;
    if (groupId === editingGroupId) card.classList.add("group-card--editing");

    const head = document.createElement("div");
    head.className = "group-card-head";

    const meta = document.createElement("span");
    meta.className = "group-card-meta";
    const logicPill = document.createElement("span");
    logicPill.className = `group-logic-pill group-logic-pill--${logic.toLowerCase()}`;
    logicPill.textContent = logicLabel;
    meta.appendChild(logicPill);
    const fieldSpan = document.createElement("span");
    fieldSpan.className = "group-card-field";
    fieldSpan.textContent = fieldLabel + scopeLabel;
    meta.appendChild(fieldSpan);
    head.appendChild(meta);

    const actions = document.createElement("div");
    actions.className = "group-card-actions";

    const editBtn = document.createElement("button");
    editBtn.type = "button";
    editBtn.className = "btn ghost group-edit-btn";
    editBtn.dataset.action = "edit";
    editBtn.dataset.groupId = groupId;
    editBtn.textContent = t("groups.edit");

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "btn ghost group-remove-btn";
    removeBtn.dataset.action = "remove";
    removeBtn.dataset.groupId = groupId;
    removeBtn.textContent = t("groups.remove");

    actions.appendChild(editBtn);
    actions.appendChild(removeBtn);
    head.appendChild(actions);
    card.appendChild(head);

    const condList = document.createElement("ul");
    condList.className = "group-conditions";
    filters.forEach(f => {
      const li = document.createElement("li");
      li.className = "group-condition" + (f.negate ? " group-condition--excl" : "");
      const modeLabel = MODE_LABEL[f.mode] || f.mode;
      const sign = f.negate ? "excluye" : "incluye";
      li.innerHTML = `<span class="gcond-sign">${sign}</span> <span class="gcond-mode">${modeLabel}</span> <span class="gcond-value">${escapeHtml(String(f.value))}</span>`;
      condList.appendChild(li);
    });
    card.appendChild(condList);

    return card;
  }

  // AND section
  if (andIds && andIds.length) {
    andIds.forEach(id => {
      const filters = groups.get(id);
      if (filters) list.appendChild(makeGroupCard(id, filters, "AND"));
    });
  }

  // OR section
  if (orIds && orIds.length) {
    if (andIds && andIds.length) {
      const sep = document.createElement("div");
      sep.className = "groups-section-sep";
      sep.textContent = "— " + t("groups.logic.or") + " —";
      list.appendChild(sep);
    }
    orIds.forEach(id => {
      const filters = groups.get(id);
      if (filters) list.appendChild(makeGroupCard(id, filters, "OR"));
    });
  }
}

function setupGroupsPanel() {
  const clearAllBtn = document.getElementById("groupsClearAll");
  if (clearAllBtn) {
    clearAllBtn.addEventListener("click", () => {
      if (editingGroupId) cancelEdit();
      activeFilters = activeFilters.filter(f => f.owner === "f1" || f.owner === FUENTE_OWNER || f.type === "fuenteSet");
      groupOrder = [];
      renderActiveFilterChips();
      applyFilters();
    });
  }

  const list = document.getElementById("groupsList");
  if (list) {
    list.addEventListener("click", e => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;
      const groupId = btn.dataset.groupId;
      if (btn.dataset.action === "remove") {
        if (editingGroupId === groupId) cancelEdit();
        activeFilters = activeFilters.filter(f => f.owner !== groupId);
        groupOrder = groupOrder.filter(g => g.id !== groupId);
        renderActiveFilterChips();
        applyFilters();
      } else if (btn.dataset.action === "edit") {
        loadGroupForEditing(groupId);
        // Switch to Filtros tab so user can edit
        const filtersTab = document.querySelector(".tab-btn[data-tab='filtersPanel']");
        if (filtersTab) filtersTab.click();
      }
    });
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
}

function loadSession(sessionId) {
  if (sessionId === currentSessionId) return;

  saveCurrentSession();

  // Cancel any in-progress edit
  if (editingGroupId) cancelEdit();

  // Clear card inputs
  const card = document.querySelector(".filter-card[data-owner='f1']");
  if (card) card.querySelectorAll(".filter-input").forEach(i => (i.value = ""));

  // Remove committed and f1 filters (keep fuente)
  activeFilters = activeFilters.filter(f => f.owner === FUENTE_OWNER || f.type === "fuenteSet");

  currentSessionId = sessionId;
  const session = sessions.find(s => s.id === sessionId);
  if (session) {
    activeFilters = [
      ...activeFilters,
      ...session.filters
    ];
    groupOrder = session.order.slice();
    groupCounter = session.groupCounter;
  }

  renderSessionBar();
  applyFilters();
}

function addSession() {
  saveCurrentSession();
  sessionCounter++;
  const id = `s${sessionCounter}`;
  sessions.push({ id, filters: [], order: [], groupCounter: 0 });

  // Cancel edit, clear card
  if (editingGroupId) cancelEdit();
  const card = document.querySelector(".filter-card[data-owner='f1']");
  if (card) card.querySelectorAll(".filter-input").forEach(i => (i.value = ""));

  // Remove committed filters, keep fuente
  activeFilters = activeFilters.filter(f => f.owner === FUENTE_OWNER || f.type === "fuenteSet");
  groupOrder = [];
  groupCounter = 0;
  currentSessionId = id;

  renderSessionBar();
  applyFilters();
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

    activeFilters = activeFilters.filter(f => f.owner === FUENTE_OWNER || f.type === "fuenteSet");
    currentSessionId = nextSession.id;
    activeFilters = [...activeFilters, ...nextSession.filters];
    groupOrder = nextSession.order.slice();
    groupCounter = nextSession.groupCounter;
    applyFilters();
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

function buildRankingContext(rows) {
  const context = {
    mode: rankingMode,
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

  context.usesLemmaTiering = rankingMode === "auto" && (context.exactCount > 0 || context.phraseCount > 0);
  return context;
}

function buildRankingSummary(context, manualOverride = false) {
  if (!context || !context.dominantLemmaFilter) return null;
  const detailKey = manualOverride
    ? "table.status.detail.manual"
    : context.usesLemmaTiering
      ? "table.status.detail.auto"
      : "table.status.detail.prio";
  return t(detailKey, {
    exact: context.exactCount,
    phrase: context.phraseCount
  });
}

function getRankingComparator(context) {
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
  const rankingContext = buildRankingContext(matches);
  const rankingComparator = getRankingComparator(rankingContext);
  const total = matches.length;
  if (displayOffset >= total && total > 0) {
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
  tbody.innerHTML = "";

  if (!rows.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = TABLE_FIELDS.filter(f => !hiddenColumns.has(f.key)).length;
    td.className = "table-empty";
    td.textContent = t("table.empty");
    tr.appendChild(td);
    tbody.appendChild(tr);
  } else {
    rows.forEach(row => {
      const tr = document.createElement("tr");
      if (row.record_id) tr.dataset.recordId = row.record_id;
      let translationTd = null;
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
            const expanded = expandedComments.has(row._rid);
            const content = document.createElement("div");
            content.className = expanded ? "comentario-text" : "comentario-text collapsed";
            content.innerHTML = applyHighlights(safe, field.key);
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "comentario-toggle";
            btn.textContent = expanded ? "−" : "+";
            btn.addEventListener("click", e => {
              e.stopPropagation();
              const isExpanded = expandedComments.has(row._rid);
              if (isExpanded) {
                const anchor = commentAnchors.get(row._rid);
                expandedComments.delete(row._rid);
                content.classList.add("collapsed");
                btn.textContent = "+";
                commentAnchors.delete(row._rid);
                if (anchor) {
                  requestAnimationFrame(() => {
                    const rect = btn.getBoundingClientRect();
                    const centerNow = rect.top + rect.height / 2 + window.scrollY;
                    const anchorCenter = anchor.center;
                    const viewTop = window.scrollY;
                    const viewBottom = viewTop + window.innerHeight;
                    // Si el punto original está fuera de vista, llévalo a la pantalla; si está visible, solo ajusta la diferencia.
                    if (anchorCenter < viewTop || anchorCenter > viewBottom) {
                      const targetTop = anchorCenter - window.innerHeight * 0.5;
                      window.scrollTo({ top: targetTop, behavior: "smooth" });
                    } else {
                      const delta = centerNow - anchorCenter;
                      if (Math.abs(delta) > 1) {
                        window.scrollBy({ top: delta, behavior: "smooth" });
                      }
                    }
                  });
                }
              } else {
                expandedComments.add(row._rid);
                const rect = btn.getBoundingClientRect();
                const center = rect.top + rect.height / 2 + window.scrollY;
                commentAnchors.set(row._rid, { scrollY: window.scrollY, center });
                content.classList.remove("collapsed");
                btn.textContent = "−";
              }
              updateComentarioToggleButton(lastRenderRows);
            });
            td.appendChild(content);
            td.appendChild(btn);
            comentarioMeta = { td, content, btn, rowId: row._rid, expanded };
          }
        } else {
          const raw = getDisplayValue(row, field.key);
          td.innerHTML = applyHighlights(raw, field.key);
          if (field.key === "Traducción") {
            translationTd = td;
          }
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);

      // Ajusta Comentario en función de la altura de Traducción
      if (comentarioMeta && translationTd) {
        const transHeight =
          Math.floor(translationTd.scrollHeight || translationTd.clientHeight || 0);
        const contentEl = comentarioMeta.content;
        const btnEl = comentarioMeta.btn;
        // mide contenido natural
        const naturalHeight = Math.floor(contentEl.scrollHeight);
        const needsToggle = naturalHeight - transHeight > 1;
        const maxH = transHeight > 0 ? `${transHeight}px` : "120px";
        contentEl.style.setProperty("--comentario-max-height", maxH);
        contentEl.dataset.maxHeight = maxH;
        if (!needsToggle) {
          // Alturas iguales: si estaba expandido, conserva el botón para poder colapsar.
          contentEl.classList.remove("collapsed");
          if (comentarioMeta.expanded) {
            comentarioMeta.btn.textContent = "−";
          } else {
            comentarioMeta.btn.remove();
          }
        } else if (comentarioMeta.expanded) {
          contentEl.classList.remove("collapsed");
        } else {
          contentEl.classList.add("collapsed");
        }
      }
    });
  }

  updateTableStatus(rows.length, totalCount);
  updatePaginationControls(totalCount);
  updateComentarioToggleButton(rows);
}

function setTableStatusMessage(baseText, detailText = "") {
  const targets = [
    document.getElementById("tableStatus"),
    document.querySelector(".table-footer .table-status")
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
    detail.className = "table-status-detail";
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
    window.scrollTo({ top: y, behavior });
  });
}

function getFooterAnchorY() {
  const footer = document.querySelector(".table-footer");
  if (!footer) return null;
  const rect = footer.getBoundingClientRect();
  return rect.top + window.scrollY;
}

function getHeaderAnchorY() {
  const header = document.querySelector(".table-header:not(.table-footer)");
  if (!header) return null;
  const rect = header.getBoundingClientRect();
  return rect.top + window.scrollY;
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

function setupComentarioToggleAll() {
  const btn = document.getElementById("comentarioExpandAll");
  if (!btn) return;
  btn.addEventListener("click", () => {
    if (!lastRenderRows.length) return;
    const y = window.scrollY;
    const hasExpanded = lastRenderRows.some(r => expandedComments.has(r._rid));
    if (hasExpanded) {
      lastRenderRows.forEach(r => expandedComments.delete(r._rid));
    } else {
      lastRenderRows.forEach(r => expandedComments.add(r._rid));
    }
    renderTable(lastRenderRows, lastRenderTotal);
    requestAnimationFrame(() => {
      window.scrollTo({ top: y, behavior: "auto" });
    });
  });
}

function updateComentarioToggleButton(rows) {
  const btn = document.getElementById("comentarioExpandAll");
  if (!btn) return;
  if (!rows.length) {
    btn.textContent = "+";
    btn.disabled = true;
    return;
  }
  btn.disabled = false;
  const expandedCount = rows.filter(r => expandedComments.has(r._rid)).length;
  comentarioAllExpanded = expandedCount === rows.length && rows.length > 0;
  btn.textContent = expandedCount > 0 ? "−" : "+";
}

function resetComentarioState() {
  expandedComments.clear();
  commentAnchors.clear();
  comentarioAllExpanded = false;
}

function setupPaginationControls() {
  const prevs = [
    document.getElementById("pagePrev"),
    document.getElementById("pagePrevFooter")
  ];
  const nexts = [
    document.getElementById("pageNext"),
    document.getElementById("pageNextFooter")
  ];
  const firsts = [
    document.getElementById("pageFirst"),
    document.getElementById("pageFirstFooter")
  ];
  const lasts = [
    document.getElementById("pageLast"),
    document.getElementById("pageLastFooter")
  ];

  const hookPrev = btn => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      if (displayOffset <= 0) return;
      displayOffset = Math.max(0, displayOffset - maxDisplayRows);
      const isFooter = btn.id && btn.id.endsWith("Footer");
      const anchor = isFooter ? getHeaderAnchorY() : null;
      const y = anchor ?? window.scrollY;
      const options = { keepOffset: true, keepCurrent: true, restoreScroll: y };
      if (isFooter) options.restoreBehavior = "smooth";
      applyFilters(false, options);
    });
  };
  const hookNext = btn => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      displayOffset += maxDisplayRows;
      const isFooter = btn.id && btn.id.endsWith("Footer");
      const anchor = isFooter ? getHeaderAnchorY() : null;
      const y = anchor ?? window.scrollY;
      const options = { keepOffset: true, keepCurrent: true, restoreScroll: y };
      if (isFooter) options.restoreBehavior = "smooth";
      applyFilters(false, options);
    });
  };
  const hookFirst = btn => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      if (displayOffset === 0) return;
      displayOffset = 0;
      const isFooter = btn.id && btn.id.endsWith("Footer");
      const anchor = isFooter ? getHeaderAnchorY() : null;
      const y = anchor ?? window.scrollY;
      const options = { keepOffset: true, keepCurrent: true, restoreScroll: y };
      if (isFooter) options.restoreBehavior = "smooth";
      applyFilters(false, options);
    });
  };
  const hookLast = btn => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      if (!lastRenderTotal) return;
      const total = lastRenderTotal;
      const maxOffset = Math.max(0, total - maxDisplayRows);
      if (displayOffset === maxOffset) return;
      displayOffset = maxOffset;
      const isFooter = btn.id && btn.id.endsWith("Footer");
      const anchor = isFooter ? getHeaderAnchorY() : null;
      const y = anchor ?? window.scrollY;
      const options = { keepOffset: true, keepCurrent: true, restoreScroll: y };
      if (isFooter) options.restoreBehavior = "smooth";
      applyFilters(false, options);
    });
  };

  [...prevs].forEach(hookPrev);
  [...nexts].forEach(hookNext);
  [...firsts].forEach(hookFirst);
  [...lasts].forEach(hookLast);
}

function updatePaginationControls(total) {
  const prevs = [
    document.getElementById("pagePrev"),
    document.getElementById("pagePrevFooter")
  ].filter(Boolean);
  const nexts = [
    document.getElementById("pageNext"),
    document.getElementById("pageNextFooter")
  ].filter(Boolean);
  const firsts = [
    document.getElementById("pageFirst"),
    document.getElementById("pageFirstFooter")
  ].filter(Boolean);
  const lasts = [
    document.getElementById("pageLast"),
    document.getElementById("pageLastFooter")
  ].filter(Boolean);
  if (!prevs.length && !nexts.length && !firsts.length && !lasts.length) return;
  const hasPrev = displayOffset > 0;
  const hasNext = displayOffset + maxDisplayRows < total;
  const maxOffset = Math.max(0, total - maxDisplayRows);
  const atLast = displayOffset >= maxOffset;
  prevs.forEach(btn => (btn.disabled = !hasPrev));
  firsts.forEach(btn => (btn.disabled = !hasPrev));
  nexts.forEach(btn => (btn.disabled = !hasNext));
  lasts.forEach(btn => (btn.disabled = !hasNext || atLast));
}

function setupSortControls() {
  const buttons = document.querySelectorAll(".sort-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", e => {
      const field = btn.dataset.sortField;
      if (!field) return;
      const y = window.scrollY;
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

function compareLemmaPriority(a, b, context) {
  const tierA = context.getTier(a);
  const tierB = context.getTier(b);
  if (tierA !== tierB) return tierA - tierB;
  return comparePriorityOrder(a, b);
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
  const buttons = document.querySelectorAll(".sort-btn");
  buttons.forEach(btn => {
    const field = btn.dataset.sortField;
    const idx = sortKeys.findIndex(k => k.field === field);
    btn.textContent = "";
    if (idx !== -1) {
      const arrow = sortKeys[idx].dir === "asc" ? "↑" : "↓";
      btn.textContent = arrow;
      if (sortKeys.length > 1) {
        const badge = document.createElement("span");
        badge.className = "sort-badge";
        badge.textContent = String(idx + 1);
        btn.appendChild(badge);
      }
    } else {
      btn.textContent = "⇅";
    }
  });
}

function setupSortScopeControls() {
  const selects = [
    document.getElementById("sortScopeSelect"),
    document.getElementById("sortScopeSelectFooter")
  ].filter(Boolean);
  const applyScope = val => {
    sortScope = val === "page" ? "page" : "all";
    const anchor = val === "page" ? getFooterAnchorY() : null;
    const y = anchor ?? window.scrollY;
    applyFilters(false, { keepOffset: true, keepCurrent: true, restoreScroll: y });
    updateSortScopeIndicators();
  };
  selects.forEach(sel => {
    sel.value = sortScope;
    sel.addEventListener("change", () => applyScope(sel.value));
  });
}

function updateSortScopeIndicators() {
  const selects = [
    document.getElementById("sortScopeSelect"),
    document.getElementById("sortScopeSelectFooter")
  ].filter(Boolean);
  selects.forEach(sel => {
    sel.value = sortScope;
  });
}

function setupExportButtons() {
  const buttons = [
    document.getElementById("exportJpeg"),
    document.getElementById("exportJpegFooter")
  ].filter(Boolean);
  buttons.forEach(btn => {
    btn.addEventListener("click", () => exportTableAsJpeg());
  });
}

function exportTableAsJpeg() {
  const table = document.getElementById("dataTable");
  if (!table) return;
  const rows = [];
  const head = table.tHead?.rows[0];
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
  canvas.toBlob(b => {
    if (!b) return;
    const link = document.createElement("a");
    link.download = t("table.export.filename");
    link.href = URL.createObjectURL(b);
    link.click();
    URL.revokeObjectURL(link.href);
  }, "image/jpeg", 0.95);
}

function getDisplayValue(row, fieldKey) {
  if (wimmerShowEs && row.Fuente === "2021 Wimmer") {
    const esKey = fieldKey === "Traducción" ? "Traducción (es)"
                : fieldKey === "Comentario"  ? "Comentario (es)"
                : null;
    if (esKey && row[esKey]) return row[esKey];
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
      applyFilters();
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

function tokenMatchesWordFilters(token, filters) {
  const stripped = stripHtmlTags(token);
  const normalizedToken = normalizeString(stripped);
  const lowercaseToken = stripped.toLowerCase(); // accent-preserved
  return filters.some(filter => {
    const query = buildFilterQuery(filter);
    const base = query.accentSensitive ? lowercaseToken : normalizedToken;
    const candidate = query.allowLoose
      ? collapseWhitespace(stripPunctuationCharacters(base))
      : base;
    if (query.hasRegex && query.strictRegex) {
      const src = query.strictRegex.source;
      try {
        // Accent-sensitive: lowercase pattern only; plain: full normalization
        const adjSrc = query.accentSensitive ? src.toLowerCase() : normalizePatternSource(src);
        const adjRx = adjSrc === src ? query.strictRegex : new RegExp(adjSrc, query.strictRegex.flags);
        return adjRx.test(candidate);
      } catch {
        return query.strictRegex.test(candidate);
      }
    }
    return candidateMatchesQuery(candidate, query, filter.mode, query.allowLoose);
  });
}

function tokenMatchesWordFiltersOS(token, filters) {
  const normalizedToken = normalizeOldSpanish(normalizeString(stripHtmlTags(token)));
  return filters.some(filter => {
    const query = buildFilterQuery(filter);
    const candidate = query.allowLoose
      ? collapseWhitespace(stripPunctuationCharacters(normalizedToken))
      : normalizedToken;
    return candidateMatchesQuery(candidate, query, filter.mode, query.allowLoose);
  });
}

function extractContainsBothParts(text) {
  if (!text || !text.startsWith("(") || !text.endsWith(")")) return null;
  if (!text.includes("||")) return null;
  return splitTopLevel(text.slice(1, -1), "||");
}

// =============== Fuentes =================
function renderFuenteList() {
  const container = document.getElementById("fuenteList");
  if (!container) return;
  container.innerHTML = "";
  FUENTE_OPTIONS.forEach(name => {
    const label = document.createElement("label");
    label.className = "fuente-option";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = name;
    checkbox.checked = selectedFuentes.has(name);
    checkbox.addEventListener("change", () => toggleFuente(name, checkbox.checked));
    const text = document.createElement("span");
    text.textContent = name;
    label.appendChild(checkbox);
    label.appendChild(text);
    container.appendChild(label);
  });
}

function toggleFuente(name, isChecked) {
  if (isChecked) {
    selectedFuentes.add(name);
  } else {
    selectedFuentes.delete(name);
  }
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

function applyFuenteFilters() {
  removeOwnerFilters(FUENTE_OWNER);
  resetComentarioState();
  const totalOptions = FUENTE_OPTIONS.length;
  const selectedCount = selectedFuentes.size;
  // Si no hay selección, se filtra todo afuera (sin coincidencias).
  if (selectedCount === 0) {
    renderTable([], 0);
    return;
  }
  // Si todas están seleccionadas, no filtramos la columna Fuente.
  if (selectedCount === totalOptions) {
    applyFilters();
    return;
  }
  // Un solo filtro con set de pertenencia para evaluar rápido.
  appendFilter("Fuente", "exact", new Set(selectedFuentes), "AND", false, "whole", {
    owner: FUENTE_OWNER,
    type: "fuenteSet"
  });
  applyFilters();
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
  const selects = [
    document.getElementById("pageSizeSelect"),
    document.getElementById("pageSizeSelectFooter")
  ].filter(Boolean);
  selects.forEach(sel => {
    sel.value = String(maxDisplayRows);
    sel.addEventListener("change", () => {
      maxDisplayRows = parseInt(sel.value, 10) || 100;
      // Sync both selects
      selects.forEach(s => { s.value = String(maxDisplayRows); });
      displayOffset = 0;
      applyFilters();
    });
  });
}

// ── Column resizing ─────────────────────────────────────────────
function setupColumnResizing() {
  const ths = document.querySelectorAll("#dataTable thead th");
  ths.forEach(th => {
    const handle = document.createElement("div");
    handle.className = "col-resize-handle";
    th.appendChild(handle);

    handle.addEventListener("mousedown", e => {
      e.preventDefault();
      const startX = e.clientX;
      const startWidth = th.offsetWidth;

      function onMouseMove(ev) {
        const newWidth = Math.max(50, startWidth + ev.clientX - startX);
        th.style.width = newWidth + "px";
        th.style.minWidth = newWidth + "px";
      }
      function onMouseUp() {
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
      }
      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
    });
  });
}

// ── Column visibility ───────────────────────────────────────────
function setupColumnVisibility() {
  const btn = document.getElementById("colVisibilityBtn");
  const dropdown = document.getElementById("colVisibilityDropdown");
  if (!btn || !dropdown) return;

  // Build dropdown items
  function buildDropdown() {
    dropdown.innerHTML = "";
    TABLE_FIELDS.forEach((field, idx) => {
      const item = document.createElement("label");
      item.className = "col-visibility-item";
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = !hiddenColumns.has(field.key);
      cb.addEventListener("change", () => {
        const visibleCount = TABLE_FIELDS.filter(f => !hiddenColumns.has(f.key)).length;
        if (!cb.checked && visibleCount <= 1) {
          cb.checked = true;
          return;
        }
        if (cb.checked) {
          hiddenColumns.delete(field.key);
          document.getElementById("dataTable")?.classList.remove(`col-hidden-${idx}`);
        } else {
          hiddenColumns.add(field.key);
          document.getElementById("dataTable")?.classList.add(`col-hidden-${idx}`);
        }
      });
      const span = document.createElement("span");
      span.textContent = field.label;
      item.appendChild(cb);
      item.appendChild(span);
      dropdown.appendChild(item);
    });
  }

  btn.addEventListener("click", e => {
    e.stopPropagation();
    buildDropdown();
    dropdown.classList.toggle("open");
  });

  document.addEventListener("click", e => {
    if (!dropdown.contains(e.target) && e.target !== btn) {
      dropdown.classList.remove("open");
    }
  });

  // Inject CSS rules for col-hidden-N
  const style = document.createElement("style");
  TABLE_FIELDS.forEach((field, idx) => {
    style.textContent += `#dataTable.col-hidden-${idx} th:nth-child(${idx + 1}),` +
      `#dataTable.col-hidden-${idx} td:nth-child(${idx + 1}) { display: none; }\n`;
  });
  document.head.appendChild(style);
}
