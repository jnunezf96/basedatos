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

function matchesWordFilter(word, filter) {
  const query = buildFilterQuery(filter);
  const candidate = query.allowLoose
    ? collapseWhitespace(stripPunctuationCharacters(stripHtmlTags(word)))
    : normalizeString(word);
  const result = candidateMatchesQuery(candidate, query, filter.mode, query.allowLoose);
  return filter.negate ? !result : result;
}

function matchesFilter(row, filter) {
  if (filter && filter.type === "wordGroup") {
    return matchesWordGroup(row, filter);
  }
  if (filter && filter.type === "fuenteSet") {
    const val = row["Fuente"];
    const ok = filter.value instanceof Set ? filter.value.has(val) : Array.isArray(filter.value) ? filter.value.includes(val) : false;
    return filter.negate ? !ok : ok;
  }
  const scope = normalizeScope(filter.scope);
  return scope === "word" ? matchWordScope(row, filter) : matchWholeScope(row, filter);
}

function matchWordScope(row, filter) {
  const entry = getNormalizedEntry(row, filter.field);
  const query = buildFilterQuery(filter);
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

function matchWholeScope(row, filter) {
  const entry = getNormalizedEntry(row, filter.field);
  const query = buildFilterQuery(filter);
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
  const query = buildFilterQuery(condition);
  const useLoose = query.allowLoose;
  const source = useLoose ? wordEntry.loose : wordEntry.raw;
  const result = candidateMatchesQuery(source, query, condition.mode, useLoose);
  return condition.negate ? !result : result;
}

function partitionSimpleFilters(filters) {
  return filters.reduce(
    (acc, filter) => {
      const scope = normalizeScope(filter.scope);
      const logic = (filter.logic ?? "AND").toUpperCase() === "OR" ? "OR" : "AND";
      acc[scope][logic].push(filter);
      return acc;
    },
    {
      whole: { AND: [], OR: [] },
      word: { AND: [] , OR: [] }
    }
  );
}

function evaluateTextFilters(row) {
  if (!activeFilters.length) return true;
  const wordGroups = activeFilters.filter(filter => filter.type === "wordGroup");
  const simpleFilters = activeFilters.filter(filter => filter.type !== "wordGroup");
  const { quickGroups, remainingFilters } = extractWordQuickGroups(simpleFilters);
  const partitions = partitionSimpleFilters(remainingFilters);

  const andGroups = wordGroups.filter(group => (group.logic ?? "AND") === "AND");
  const orGroups = wordGroups.filter(group => (group.logic ?? "AND") === "OR");

  const andMatch =
    partitions.whole.AND.every(filter => matchesFilter(row, filter)) &&
    partitions.word.AND.every(filter => matchesFilter(row, filter)) &&
    quickGroups.every(group => matchesWordQuickGroup(row, group)) &&
    andGroups.every(group => matchesWordGroup(row, group));

  const hasOrFilters =
    partitions.whole.OR.length > 0 ||
    partitions.word.OR.length > 0 ||
    orGroups.length > 0;

  const orMatch = hasOrFilters
    ? partitions.whole.OR.some(filter => matchesFilter(row, filter)) ||
      partitions.word.OR.some(filter => matchesFilter(row, filter)) ||
      orGroups.some(group => matchesWordGroup(row, group))
    : true;

  return andMatch && orMatch;
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

function matchesWordQuickGroup(row, group) {
  if (!group || !group.filters || !group.filters.length) return false;
  const entry = getNormalizedEntry(row, group.field);
  if (!entry.words.length) return false;

  // Use accent-preserved words when any filter in the group is accent-sensitive.
  const accentSensitive = group.filters.some(f => buildFilterQuery(f).accentSensitive);
  const wordList = accentSensitive ? entry.wordsWithAccents : entry.words;

  const hasInclude = group.filters.some(f => !f.negate);
  if (!hasInclude) {
    // Exclude-only: the field must contain no word matching any exclude filter.
    return group.filters.every(filter => {
      const query = buildFilterQuery(filter);
      const useLoose = query.allowLoose;
      return !wordList.some(wordEntry => {
        const candidate = useLoose ? wordEntry.loose : wordEntry.raw;
        return candidateMatchesQuery(candidate, query, filter.mode, useLoose);
      });
    });
  }

  const segments = buildWordQuickSegments(group.filters);
  if (!segments.size) return false;
  return wordList.some(wordEntry => wordEntryMatchesQuickSegments(wordEntry, segments));
}

function buildWordQuickSegments(filters) {
  const segments = new Map();
  filters.forEach(filter => {
    const type = mapModeToWordRowType(filter.mode);
    if (!segments.has(type)) {
      segments.set(type, { include: [], exclude: [] });
    }
    const bucket = filter.negate ? segments.get(type).exclude : segments.get(type).include;
    bucket.push(filter);
  });
  return segments;
}

function wordEntryMatchesQuickSegments(wordEntry, segments) {
  if (!segments.size) return false;
  for (const segment of segments.values()) {
    if (segment.exclude.some(filter => quickFilterMatchesWordEntry(wordEntry, filter))) {
      return false;
    }
    if (segment.include.length && !segment.include.some(filter => quickFilterMatchesWordEntry(wordEntry, filter))) {
      return false;
    }
  }
  return true;
}

function quickFilterMatchesWordEntry(wordEntry, filter) {
  const query = buildFilterQuery(filter);
  const useLoose = query.allowLoose;
  const source = useLoose ? wordEntry.loose : wordEntry.raw;
  return candidateMatchesQuery(source, query, filter.mode, useLoose);
}
