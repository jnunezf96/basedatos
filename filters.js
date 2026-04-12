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
  return scope === "word" ? "word" : "whole";
}

function candidateMatchesQuery(candidate, query, mode, useLoose) {
  if (!candidate) return false;
  if (mode === "regex" && query.hasRegex === false) {
    return false;
  }
  if (query.hasRegex && query.strictRegex) {
    return query.strictRegex.test(candidate);
  }
  if (query.hasWildcards) {
    const regex = useLoose ? query.looseRegex : query.strictRegex;
    return regex ? regex.test(candidate) : false;
  }
  const queryValue = useLoose ? query.loose : query.strict;
  if (!queryValue) return false;
  return wordMatchesCondition(candidate, queryValue, mode);
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


function matchesWordGroup(row, group) {
  const expression = normalizeWordGroupStructure(group);
  const entry = getNormalizedEntry(row, group.field);
  if (!entry.words.length) return false;
  if (!expression || !expression.children.length) return false;
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
  const useLoose = query.allowLoose;
  const source = useLoose ? wordEntry.loose : wordEntry.raw;
  const result = candidateMatchesQuery(source, query, condition.mode, useLoose);
  return condition.negate ? !result : result;
}


// Pre-built evaluation context — rebuilt once per applyFilters call, reused for every row.
let _evalCtx = null;

// Pre-compile a single simple filter into a ready-to-run descriptor.
function compileSimpleFilter(filter) {
  if (filter.type === "fuenteSet") return { type: "fuenteSet", filter };
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
  const { filter, query, scope } = cf;
  if (scope === "word") return matchWordScopeCompiled(row, filter, query);
  return matchWholeScopeCompiled(row, filter, query);
}

function matchWholeScopeCompiled(row, filter, query) {
  const entry = getNormalizedEntry(row, filter.field);
  const useLoose = query.allowLoose;
  let candidateText;
  if (query.accentSensitive) {
    candidateText = useLoose ? entry.looseWithAccents : entry.withAccents;
  } else if (oldSpanishMode && entry.normalizedOS) {
    candidateText = useLoose ? entry.looseTextOS : entry.normalizedOS;
  } else {
    candidateText = useLoose ? entry.looseText : entry.normalized;
  }
  const result = candidateMatchesQuery(candidateText, query, filter.mode, useLoose);
  return filter.negate ? !result : result;
}

function matchWordScopeCompiled(row, filter, query) {
  const entry = getNormalizedEntry(row, filter.field);
  const useLoose = query.allowLoose;
  const words = query.accentSensitive
    ? entry.wordsWithAccents
    : (oldSpanishMode && entry.wordsOS) ? entry.wordsOS : entry.words;
  const matches = words.some(wordEntry => {
    const candidate = useLoose ? wordEntry.loose : wordEntry.raw;
    return candidateMatchesQuery(candidate, query, filter.mode, useLoose);
  });
  return filter.negate ? !matches : matches;
}

function extractWordQuickGroups(filters) {
  const quickGroups = new Map();
  const remaining = [];
  filters.forEach(filter => {
    if (normalizeScope(filter.scope) === "word" && filter.wordGroupId) {
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

function mapModeToWordRowType(mode) {
  return mode;
}

// Compiled version — used with pre-built context from buildEvalContext().
function matchesCompiledQuickGroup(row, group) {
  const entry = getNormalizedEntry(row, group.field);
  if (!entry.words.length) return false;
  const wordList = group.accentSensitive ? entry.wordsWithAccents : entry.words;

  if (!group.hasInclude) {
    return group.compiledFilters.every(({ filter, query }) => {
      const useLoose = query.allowLoose;
      return !wordList.some(wordEntry => {
        const candidate = useLoose ? wordEntry.loose : wordEntry.raw;
        return candidateMatchesQuery(candidate, query, filter.mode, useLoose);
      });
    });
  }

  if (!group.segments.size) return false;
  return wordList.some(wordEntry => wordEntryMatchesCompiledSegments(wordEntry, group.segments));
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
  const useLoose = query.allowLoose;
  const source = useLoose ? wordEntry.loose : wordEntry.raw;
  return candidateMatchesQuery(source, query, filter.mode, useLoose);
}

