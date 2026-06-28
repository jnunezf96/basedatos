// filters.js - Filter engine helpers

let activeFilters = [];
let filterIdCounter = 0;

function appendFilter(field, mode, value, logic = "AND", negate = false, scope = "whole", extras = {}) {
  if (!field || !mode || !value) return;
  activeFilters.push({
    id: ++filterIdCounter,
    type: "filter",
    field,
    mode,
    value,
    logic,
    negate,
    scope,
    ...extras
  });
}

function normalizeWordGroupStructure(filter) {
  if (filter.expression) return filter.expression;
  if (filter.conditions) {
    const expression = {
      type: "group",
      logic: "AND",
      children: filter.conditions.map(condition => ({
        type: "condition",
        mode: condition.mode,
        value: condition.value,
        negate: !!condition.negate
      }))
    };
    filter.expression = expression;
    return expression;
  }
  return filter.expression || { type: "group", logic: "AND", children: [] };
}

function normalizeScope(scope) {
  if (scope === "word") return "word";
  if (scope === "phrase") return "phrase";
  return "whole";
}

function candidateMatchesQuery(candidate, query, mode, useLoose) {
  if (!candidate) return false;
  const matchMode = query.effectiveMode || mode;
  if (matchMode === "regex" && query.hasRegex === false) {
    return false;
  }
  if (query.hasRegex && query.strictRegex) {
    query.strictRegex.lastIndex = 0;
    return query.strictRegex.test(candidate);
  }
  if (query.hasWildcards) {
    const regex = useLoose ? query.looseRegex : query.strictRegex;
    if (!regex) return false;
    regex.lastIndex = 0;
    return regex.test(candidate);
  }
  const queryValue = useLoose ? query.loose : query.strict;
  if (!queryValue) return false;
  return wordMatchesCondition(candidate, queryValue, matchMode);
}

function wordMatchesCondition(word, filterValue, mode) {
  switch (mode) {
    case "exact":
      return word === filterValue;
    case "any":
      return word.includes(filterValue);
    case "starts":
      return word.startsWith(filterValue);
    case "ends":
      return word.endsWith(filterValue);
    default:
      return true;
  }
}

function getWordEntryLoose(wordEntry) {
  if (!wordEntry) return "";
  if (wordEntry.loose !== undefined) return wordEntry.loose;
  const raw = wordEntry.raw || "";
  wordEntry.loose = raw && hasFormattingCharacters(raw)
    ? collapseWhitespace(stripPunctuationCharacters(raw))
    : raw;
  return wordEntry.loose;
}

function getWordEntryCandidate(wordEntry, useLoose) {
  return useLoose ? getWordEntryLoose(wordEntry) : (wordEntry?.raw || "");
}

function getSimpleLooseQueryValue(query) {
  if (!query || query.hasRegex || query.hasWildcards) return "";
  if (!query.strict || query.strict !== query.loose) return "";
  return query.strict;
}

function wordEntryMatchesFilterQuery(wordEntry, filter, query) {
  if (!wordEntry) return false;
  const useLoose = query.allowLoose;
  if (!useLoose) return candidateMatchesQuery(wordEntry.raw, query, filter.mode, false);
  if (candidateMatchesQuery(wordEntry.raw, query, filter.mode, false)) return true;
  const simpleValue = getSimpleLooseQueryValue(query);
  if (simpleValue) {
    const mode = query.effectiveMode || filter.mode;
    if (mode === "any" || !wordEntry.raw.includes(simpleValue)) return false;
  }
  if (!hasFormattingCharacters(wordEntry.raw)) return false;
  wordEntry.loose = collapseWhitespace(stripPunctuationCharacters(wordEntry.raw));
  return candidateMatchesQuery(wordEntry.loose, query, filter.mode, true);
}


function matchesWordGroup(row, group) {
  const expression = normalizeWordGroupStructure(group);
  if (!expression || !expression.children.length) return false;
  if (shouldStreamNormalizedWords(group.field)) {
    return forEachNormalizedWordEntry(row, group.field, { accentSensitive: accentSensitiveMode }, wordEntry =>
      evaluateExpressionOnWordEntry(wordEntry, expression)
    );
  }
  const entry = getNormalizedEntry(row, group.field);
  if (!entry.words.length) return false;
  return entry.words.some(wordEntry => evaluateExpressionOnWordEntry(wordEntry, expression));
}

function evaluateExpressionOnWordEntry(wordEntry, node) {
  if (!node) return false;
  if (node.type === "condition") {
    return evaluateConditionAgainstWordEntry(wordEntry, node);
  }
  if (!node.children || !node.children.length) {
    return true;
  }
  if (node.logic === "AND") {
    return node.children.every(child => evaluateExpressionOnWordEntry(wordEntry, child));
  }
  return node.children.some(child => evaluateExpressionOnWordEntry(wordEntry, child));
}

function evaluateConditionAgainstWordEntry(wordEntry, condition) {
  const query = condition._query || buildFilterQuery(condition);
  const result = wordEntryMatchesFilterQuery(wordEntry, condition, query);
  return condition.negate ? !result : result;
}

function getNormalizedWordStreamText(row, field, options = {}) {
  return normalizeRawTextForSearch(getRawDisplayValue(row, field), {
    accentSensitive: !!options.accentSensitive
  });
}

function forEachNormalizedWordEntry(row, field, options, callback) {
  const text = getNormalizedWordStreamText(row, field, options);
  if (!text) return false;
  const rx = /\S+/g;
  let match;
  while ((match = rx.exec(text))) {
    const raw = match[0];
    const wordEntry = { raw };
    if (callback(wordEntry)) return true;
  }
  return false;
}

function normalizedWordEntryExists(row, field, options, predicate) {
  if (shouldStreamNormalizedWords(field)) {
    return forEachNormalizedWordEntry(row, field, options, predicate);
  }
  const entry = getNormalizedEntry(row, field);
  const words = options?.accentSensitive
    ? entry.wordsWithAccents
    : (oldSpanishMode && entry.wordsOS) ? entry.wordsOS : entry.words;
  return words.some(predicate);
}


// Pre-built evaluation context — rebuilt once per applyFilters call, reused for every row.
let _evalCtx = null;

// Pre-compile a single simple filter into a ready-to-run descriptor.
function compileSimpleFilter(filter) {
  if (filter.type === "fuenteSet") return { type: "fuenteSet", filter };
  if (filter.type === "reverse") {
    const tokens = String(filter.value || "")
      .split(/[\s,;]+/)
      .map(tok => normalizeString(tok.trim()))
      .filter(Boolean);
    const fields = Array.isArray(filter.fields) && filter.fields.length
      ? filter.fields
      : ["Traducción"];
    return { type: "reverse", filter, tokens, fields };
  }
  if (filter.type === "reversePreset") {
    const scope = normalizeScope(filter.scope);
    const fields = Array.isArray(filter.fields) && filter.fields.length
      ? filter.fields
      : ["Traducción"];
    const compiledFields = fields.map(field => ({
      filter: { ...filter, field },
      query: buildFilterQuery({ ...filter, field })
    }));
    return { type: "reversePreset", filter, scope, compiledFields };
  }
  const query = buildFilterQuery(filter);
  const scope = normalizeScope(filter.scope);
  return { type: "simple", filter, query, scope };
}

// Pre-compile all conditions in a wordGroup expression tree (mutates node in place).
function precompileExpression(node) {
  if (!node) return;
  if (node.type === "condition") {
    node._query = buildFilterQuery(node);
    return;
  }
  (node.children || []).forEach(precompileExpression);
}

function buildEvalContext() {
  if (!activeFilters.length) { _evalCtx = null; return; }

  const wordGroups    = activeFilters.filter(f => f.type === "wordGroup");
  const simpleFilters = activeFilters.filter(f => f.type !== "wordGroup");
  const { quickGroups, remainingFilters } = extractWordQuickGroups(simpleFilters);

  // Pre-compile all whole/word-scope partition filters.
  const compiled = remainingFilters.map(compileSimpleFilter);
  const whole = { AND: [], OR: [] };
  const word  = { AND: [], OR: [] };
  compiled.forEach(cf => {
    const logic = (cf.filter.logic ?? "AND").toUpperCase() === "OR" ? "OR" : "AND";
    if (cf.type === "fuenteSet" || cf.scope === "whole") whole[logic].push(cf);
    else word[logic].push(cf);
  });

  // Pre-compile queries and segments for quick groups.
  const compiledQuickGroups = quickGroups.map(group => {
    const accentSensitive = accentSensitiveMode;
    const compiledFilters = group.filters.map(f => ({ filter: f, query: buildFilterQuery(f) }));
    const segments = buildCompiledSegments(compiledFilters);
    const hasInclude = compiledFilters.some(cf => !cf.filter.negate);
    return { field: group.field, accentSensitive, segments, compiledFilters, hasInclude };
  });

  // Pre-compile wordGroup expression trees.
  wordGroups.forEach(g => precompileExpression(normalizeWordGroupStructure(g)));
  const andGroups = wordGroups.filter(g => (g.logic ?? "AND") === "AND");
  const orGroups  = wordGroups.filter(g => (g.logic ?? "AND") === "OR");

  _evalCtx = {
    whole, word,
    compiledQuickGroups,
    andGroups, orGroups,
    hasOrFilters: whole.OR.length > 0 || word.OR.length > 0 || orGroups.length > 0,
  };
}

function evaluateTextFilters(row) {
  if (!_evalCtx) return true;
  const { whole, word, compiledQuickGroups, andGroups, orGroups, hasOrFilters } = _evalCtx;

  const andMatch =
    whole.AND.every(cf => matchCompiledFilter(row, cf)) &&
    word.AND.every(cf => matchCompiledFilter(row, cf)) &&
    compiledQuickGroups.every(group => matchesCompiledQuickGroup(row, group)) &&
    andGroups.every(group => matchesWordGroup(row, group));

  const orMatch = hasOrFilters
    ? whole.OR.some(cf => matchCompiledFilter(row, cf)) ||
      word.OR.some(cf => matchCompiledFilter(row, cf)) ||
      orGroups.some(group => matchesWordGroup(row, group))
    : true;

  return andMatch && orMatch;
}

// Per-row evaluation using a pre-compiled filter descriptor.
function matchCompiledFilter(row, cf) {
  if (cf.type === "fuenteSet") {
    const val = row["Fuente"];
    const ok = cf.filter.value instanceof Set ? cf.filter.value.has(val) : Array.isArray(cf.filter.value) ? cf.filter.value.includes(val) : false;
    return cf.filter.negate ? !ok : ok;
  }
  if (cf.type === "reverse") {
    if (!cf.tokens.length) return true;
    const ok = cf.tokens.every(tok => {
      return cf.fields.some(field => {
        const entry = getNormalizedEntry(row, field);
        return entry.words.some(w => {
          const src = getWordEntryCandidate(w, true);
          return src === tok || src.startsWith(tok);
        });
      });
    });
    return cf.filter.negate ? !ok : ok;
  }
  if (cf.type === "reversePreset") {
    const ok = cf.compiledFields.some(({ filter, query }) => {
      if (cf.scope === "word") return matchWordScopeCompiled(row, filter, query);
      if (cf.scope === "phrase") return matchPhraseScopeCompiled(row, filter, query);
      return matchWholeScopeCompiled(row, filter, query);
    });
    return cf.filter.negate ? !ok : ok;
  }
  const { filter, query, scope } = cf;
  if (scope === "word") return matchWordScopeCompiled(row, filter, query);
  if (scope === "phrase") return matchPhraseScopeCompiled(row, filter, query);
  return matchWholeScopeCompiled(row, filter, query);
}

function matchWholeScopeCompiled(row, filter, query) {
  const useLoose = query.allowLoose;
  const candidateText = getNormalizedTextVariant(row, filter.field, {
    accentSensitive: query.accentSensitive,
    loose: useLoose
  });
  const result = candidateMatchesQuery(candidateText, query, filter.mode, useLoose);
  return filter.negate ? !result : result;
}

function matchWordScopeCompiled(row, filter, query) {
  const matches = normalizedWordEntryExists(row, filter.field, { accentSensitive: query.accentSensitive }, wordEntry => {
    return wordEntryMatchesFilterQuery(wordEntry, filter, query);
  });
  return filter.negate ? !matches : matches;
}

function matchPhraseScopeCompiled(row, filter, query) {
  if (shouldStreamNormalizedWords(filter.field)) {
    return matchPhraseScopeCompiledStreaming(row, filter, query);
  }
  const entry = getNormalizedEntry(row, filter.field);
  const phraseQuery = queryMatchesMultiWordPhrase(query, filter.mode, query.allowLoose)
    ? query
    : buildLiteralPhraseQuery(filter, query);
  const useLoose = phraseQuery ? phraseQuery.allowLoose : query.allowLoose;
  const words = (phraseQuery || query).accentSensitive
    ? entry.wordsWithAccents
    : (oldSpanishMode && entry.wordsOS) ? entry.wordsOS : entry.words;
  const matches = phraseQuery
    ? wordSequenceMatchesQuery(words, phraseQuery, filter.mode, useLoose)
    : queryUsesPhraseWindowRegex(query)
      ? phraseWindowMatchesQuery(words, filter, query, useLoose)
    : words.some(wordEntry => {
      return wordEntryMatchesFilterQuery(wordEntry, filter, query);
    });
  return filter.negate ? !matches : matches;
}

function matchPhraseScopeCompiledStreaming(row, filter, query) {
  const phraseQuery = queryMatchesMultiWordPhrase(query, filter.mode, query.allowLoose)
    ? query
    : buildLiteralPhraseQuery(filter, query);
  const useLoose = phraseQuery ? phraseQuery.allowLoose : query.allowLoose;
  const matches = phraseQuery
    ? streamingWordSequenceMatchesQuery(row, filter.field, phraseQuery, filter.mode, useLoose)
    : queryUsesPhraseWindowRegex(query)
      ? streamingPhraseWindowMatchesQuery(row, filter, query, useLoose)
    : normalizedWordEntryExists(row, filter.field, { accentSensitive: query.accentSensitive }, wordEntry => {
      return wordEntryMatchesFilterQuery(wordEntry, filter, query);
    });
  return filter.negate ? !matches : matches;
}

const PHRASE_REGEX_DEFAULT_MAX_WORDS = 8;
const PHRASE_REGEX_EXTRA_WORDS = 6;
const PHRASE_REGEX_HARD_MAX_WORDS = 24;

function queryUsesPhraseWindowRegex(query) {
  return !!(query && (query.hasRegex || query.hasWildcards));
}

function phraseWindowMatchesQuery(words, filter, query, useLoose) {
  return findPhraseWindowMatches(words, filter, query, useLoose, { stopAfterFirst: true }).length > 0;
}

function findPhraseWindowMatches(words, filter, query, useLoose, options = {}) {
  if (!queryUsesPhraseWindowRegex(query)) return [];
  const counts = phraseWindowWordCounts(filter, query);
  if (!counts.length) return [];
  const candidates = words
    .map(wordEntry => ({
      entry: wordEntry,
      candidate: getWordEntryCandidate(wordEntry, useLoose)
    }))
    .filter(item => item.candidate);
  if (!candidates.length) return [];

  const matches = [];
  for (let start = 0; start < candidates.length; start++) {
    for (const count of counts) {
      const end = start + count;
      if (end > candidates.length) continue;
      const slice = candidates.slice(start, end);
      const candidateText = slice.map(item => item.candidate).join(" ");
      if (!candidateMatchesQuery(candidateText, query, filter.mode, useLoose)) continue;
      const matchWords = phraseRegexMatchWords(slice, candidateText, query, useLoose);
      const match = {
        start,
        end,
        words: matchWords.length ? matchWords : slice.map(item => item.entry),
        candidate: candidateText
      };
      matches.push(match);
      if (options.stopAfterFirst) return matches;
      if (options.firstPerStart) break;
    }
  }
  return matches;
}

function phraseRegexMatchWords(slice, candidateText, query, useLoose) {
  const regex = phraseQueryRegex(query, useLoose);
  if (!regex) return [];
  regex.lastIndex = 0;
  const match = regex.exec(candidateText);
  if (!match) return [];
  const matchStart = match.index;
  const matchEnd = Math.max(matchStart + match[0].length, regex.lastIndex);
  if (matchEnd <= matchStart) return [];

  let cursor = 0;
  const offsets = slice.map(item => {
    const start = cursor;
    const end = start + item.candidate.length;
    cursor = end + 1;
    return { start, end, entry: item.entry };
  });
  return offsets
    .filter(offset => matchStart < offset.end && matchEnd > offset.start)
    .map(offset => offset.entry);
}

function phraseQueryRegex(query, useLoose) {
  if (query.hasWildcards) return useLoose ? query.looseRegex : query.strictRegex;
  if (query.hasRegex) return query.strictRegex;
  return null;
}

function phraseWindowWordCounts(filter, query) {
  const estimates = phraseWordCountEstimates(filter, query)
    .filter(count => count > 0);
  const base = estimates.length ? Math.max(...estimates) : 1;
  const variable = phrasePatternMaySpanVariableWords(filter, query);
  const max = variable
    ? Math.min(PHRASE_REGEX_HARD_MAX_WORDS, Math.max(PHRASE_REGEX_DEFAULT_MAX_WORDS, base + PHRASE_REGEX_EXTRA_WORDS))
    : Math.min(PHRASE_REGEX_HARD_MAX_WORDS, Math.max(1, base));
  const counts = [];
  for (let count = Math.max(1, base); count <= max; count++) {
    counts.push(count);
  }
  return counts;
}

function phraseWordCountEstimates(filter, query) {
  const values = [];
  const queryValue = query.allowLoose ? query.loose : query.strict;
  if (queryValue) values.push(queryValue);
  const raw = normalizePhrasePatternInput(filter.value, filter.mode);
  if (raw) values.push(raw);
  if (query.strictRegex) values.push(query.strictRegex.source);
  if (query.looseRegex && query.looseRegex !== query.strictRegex) values.push(query.looseRegex.source);
  return values.map(estimatePhraseWordCountFromPattern);
}

function normalizePhrasePatternInput(value, mode) {
  let raw = String(value ?? "").trim();
  const literalRegex = raw.match(/^\/(.+)\/([gimsuy]*)$/);
  if (literalRegex) return literalRegex[1];
  if (isQuoted(raw)) return unquote(raw);
  if (mode === "exact") {
    const leading = raw.startsWith("-");
    const trailing = raw.endsWith("-") && !isEscapedAt(raw, raw.length - 1);
    if (leading && trailing && raw.length > 2) raw = raw.slice(1, -1);
    else if (leading) raw = raw.slice(1);
    else if (trailing) raw = raw.slice(0, -1);
  }
  return raw.replace(/\\-/g, "-").trim();
}

function estimatePhraseWordCountFromPattern(value) {
  const prepared = String(value || "")
    .replace(/\\[sW](?:[+*?]|\{\d+(?:,\d*)?\})?/g, " ")
    .replace(/\\p\{Zs\}(?:[+*?]|\{\d+(?:,\d*)?\})?/g, " ")
    .replace(/\[\^?\\s\](?:[+*?]|\{\d+(?:,\d*)?\})?/g, " ");
  return prepared.trim().split(/\s+/).filter(Boolean).length;
}

function phrasePatternMaySpanVariableWords(filter, query) {
  const raw = normalizePhrasePatternInput(filter.value, filter.mode);
  const sources = [
    raw,
    query.strictRegex ? query.strictRegex.source : "",
    query.looseRegex && query.looseRegex !== query.strictRegex ? query.looseRegex.source : ""
  ].filter(Boolean);
  return sources.some(src => (
    /\.\*|\.\+|\[[^\]]*\\s[^\]]*\][*+]|\(\?:[^)]*\\s[^)]*\)[*+]|\{0,/.test(src)
  ));
}

function buildLiteralPhraseQuery(filter, query) {
  const raw = String(filter.value ?? "").trim();
  if (!raw || !isQuoted(raw)) return null;
  const text = unquote(raw).trim();
  if (!/\s/.test(text)) return null;
  let strict = query.accentSensitive
    ? text.normalize("NFC").toLowerCase()
    : normalizeString(text);
  if (!query.accentSensitive && oldSpanishMode) {
    strict = normalizeOldSpanish(strict);
  }
  const loose = collapseWhitespace(stripPunctuationCharacters(stripHtmlTags(strict)));
  return {
    ...query,
    strict,
    loose,
    hasRegex: false,
    allowLoose: !hasFormattingCharacters(text),
    hasWildcards: false,
    strictRegex: null,
    looseRegex: null,
    effectiveMode: query.effectiveMode || filter.mode
  };
}

function queryMatchesMultiWordPhrase(query, mode, useLoose) {
  if (!query || query.hasRegex || query.hasWildcards) return false;
  const queryValue = useLoose ? query.loose : query.strict;
  if (!queryValue || !/\s/.test(queryValue.trim())) return false;
  const matchMode = query.effectiveMode || mode;
  return ["exact", "any", "starts", "ends"].includes(matchMode);
}

function wordSequenceMatchesQuery(words, query, mode, useLoose) {
  const queryValue = useLoose ? query.loose : query.strict;
  const queryWords = splitSearchWords(queryValue);
  if (queryWords.length < 2) return false;
  const candidateWords = words
    .map(wordEntry => getWordEntryCandidate(wordEntry, useLoose))
    .filter(Boolean);
  if (candidateWords.length < queryWords.length) return false;

  const matchMode = query.effectiveMode || mode;
  for (let i = 0; i <= candidateWords.length - queryWords.length; i++) {
    const slice = candidateWords.slice(i, i + queryWords.length);
    if (wordSequenceMatchesMode(slice, queryWords, matchMode)) return true;
  }
  return false;
}

function streamingWordSequenceMatchesQuery(row, field, query, mode, useLoose) {
  const queryValue = useLoose ? query.loose : query.strict;
  const queryWords = splitSearchWords(queryValue);
  if (queryWords.length < 2) return false;
  const window = [];
  return forEachNormalizedWordEntry(row, field, { accentSensitive: query.accentSensitive }, wordEntry => {
    const candidate = getWordEntryCandidate(wordEntry, useLoose);
    if (!candidate) return false;
    window.push(candidate);
    if (window.length > queryWords.length) window.shift();
    return window.length === queryWords.length
      && wordSequenceMatchesMode(window, queryWords, query.effectiveMode || mode);
  });
}

function streamingPhraseWindowMatchesQuery(row, filter, query, useLoose) {
  if (!queryUsesPhraseWindowRegex(query)) return false;
  const counts = phraseWindowWordCounts(filter, query);
  if (!counts.length) return false;
  const maxCount = Math.max(...counts);
  const window = [];
  return forEachNormalizedWordEntry(row, filter.field, { accentSensitive: query.accentSensitive }, wordEntry => {
    const candidate = getWordEntryCandidate(wordEntry, useLoose);
    if (!candidate) return false;
    window.push(candidate);
    if (window.length > maxCount) window.shift();
    for (const count of counts) {
      if (count > window.length) continue;
      const candidateText = window.slice(window.length - count).join(" ");
      if (candidateMatchesQuery(candidateText, query, filter.mode, useLoose)) return true;
    }
    return false;
  });
}

function splitSearchWords(value) {
  return String(value || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
}

function wordSequenceMatchesMode(candidateWords, queryWords, mode) {
  if (candidateWords.length !== queryWords.length) return false;
  if (mode === "starts") {
    return candidateWords.every((word, idx) =>
      idx === queryWords.length - 1
        ? word.startsWith(queryWords[idx])
        : word === queryWords[idx]
    );
  }
  if (mode === "ends") {
    return candidateWords.every((word, idx) =>
      idx === 0
        ? word.endsWith(queryWords[idx])
        : word === queryWords[idx]
    );
  }
  if (mode === "any") {
    return candidateWords.every((word, idx) => {
      if (idx === 0 && idx === queryWords.length - 1) {
        return word.includes(queryWords[idx]);
      }
      if (idx === 0) return word.endsWith(queryWords[idx]);
      if (idx === queryWords.length - 1) return word.startsWith(queryWords[idx]);
      return word === queryWords[idx];
    });
  }
  return candidateWords.every((word, idx) => word === queryWords[idx]);
}

function extractWordQuickGroups(filters) {
  const quickGroups = new Map();
  const remaining = [];
  filters.forEach(filter => {
    if (normalizeScope(filter.scope) === "word" && filter.wordGroupId && !filterValueLooksMultiWord(filter.value)) {
      const fieldKey = filter.field || "Campo";
      const key = `${fieldKey}__${filter.wordGroupId}`;
      if (!quickGroups.has(key)) {
        quickGroups.set(key, {
          id: filter.wordGroupId,
          field: fieldKey,
          filters: []
        });
      }
      quickGroups.get(key).filters.push(filter);
    } else {
      remaining.push(filter);
    }
  });
  return {
    quickGroups: Array.from(quickGroups.values()),
    remainingFilters: remaining
  };
}

function filterValueLooksMultiWord(value) {
  const raw = String(value || "").trim();
  if (!raw) return false;
  const unwrapped = raw.length >= 2 && raw[0] === "\"" && raw[raw.length - 1] === "\""
    ? raw.slice(1, -1)
    : raw;
  return /\s/.test(unwrapped.trim());
}

function mapModeToWordRowType(mode) {
  return mode;
}

// Compiled version — used with pre-built context from buildEvalContext().
function matchesCompiledQuickGroup(row, group) {
  if (shouldStreamNormalizedWords(group.field)) {
    return matchesCompiledQuickGroupStreaming(row, group);
  }
  const entry = getNormalizedEntry(row, group.field);
  if (!entry.words.length) return false;
  const wordList = group.accentSensitive
    ? entry.wordsWithAccents
    : (oldSpanishMode && entry.wordsOS) ? entry.wordsOS : entry.words;

  if (!group.hasInclude) {
    return group.compiledFilters.every(({ filter, query }) => {
      return !wordList.some(wordEntry => {
        return wordEntryMatchesFilterQuery(wordEntry, filter, query);
      });
    });
  }

  if (!group.segments.size) return false;
  return wordList.some(wordEntry => wordEntryMatchesCompiledSegments(wordEntry, group.segments));
}

function matchesCompiledQuickGroupStreaming(row, group) {
  if (!group.hasInclude) {
    return group.compiledFilters.every(({ filter, query }) => {
      return !forEachNormalizedWordEntry(row, group.field, { accentSensitive: query.accentSensitive }, wordEntry => {
        return wordEntryMatchesFilterQuery(wordEntry, filter, query);
      });
    });
  }

  if (!group.segments.size) return false;
  return forEachNormalizedWordEntry(row, group.field, { accentSensitive: group.accentSensitive }, wordEntry =>
    wordEntryMatchesCompiledSegments(wordEntry, group.segments)
  );
}

// segments built from pre-compiled { filter, query } pairs.
function buildCompiledSegments(compiledFilters) {
  const segments = new Map();
  compiledFilters.forEach(({ filter, query }) => {
    const type = mapModeToWordRowType(filter.mode);
    if (!segments.has(type)) segments.set(type, { include: [], exclude: [] });
    const bucket = filter.negate ? segments.get(type).exclude : segments.get(type).include;
    bucket.push({ filter, query });
  });
  return segments;
}

function wordEntryMatchesCompiledSegments(wordEntry, segments) {
  if (!segments.size) return false;
  for (const segment of segments.values()) {
    if (segment.exclude.some(({ filter, query }) => compiledQueryMatchesWordEntry(wordEntry, filter, query))) return false;
    if (segment.include.length && !segment.include.some(({ filter, query }) => compiledQueryMatchesWordEntry(wordEntry, filter, query))) return false;
  }
  return true;
}

function compiledQueryMatchesWordEntry(wordEntry, filter, query) {
  return wordEntryMatchesFilterQuery(wordEntry, filter, query);
}
