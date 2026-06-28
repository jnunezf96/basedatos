// data.js - Data storage and normalization helpers

let dataRows = [];
let normalizationCache = new Map();
let oldSpanishMode = false;
let accentSensitiveMode = false; // false = accent-free (default); true = accent-exact

const FIELD_KEY_ALIASES = new Map([
  ["Texto estandarizado", "Editado"],
  ["Escritura original", "Original"]
]);

function normalizeFieldKey(fieldKey) {
  return FIELD_KEY_ALIASES.get(fieldKey) || fieldKey;
}

function normalizeRowFieldKeys(row) {
  if (!row || typeof row !== "object") return row;
  FIELD_KEY_ALIASES.forEach((nextKey, oldKey) => {
    if (Object.prototype.hasOwnProperty.call(row, oldKey)) {
      if (!Object.prototype.hasOwnProperty.call(row, nextKey)) {
        row[nextKey] = row[oldKey];
      }
      delete row[oldKey];
    }
  });
  return row;
}

// ==============================
// Normalization
// ==============================
function normalizeString(str) {
  if (!str) return "";
  return str
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function normalizeOldSpanish(str) {
  if (!str) return str;
  return str
    .replace(/ph/g, "f")
    .replace(/th/g, "t")
    .replace(/qu/g, "c")
    .replace(/nn/g, "n")
    .replace(/ss/g, "s")
    .replace(/x/g, "j")
    .replace(/v/g, "b");
}

function normalizeOldSpanishPatternText(str) {
  if (!str) return str;
  let out = "";
  let literal = "";
  let escaped = false;
  let inClass = false;
  let inBrace = false;

  const flushLiteral = () => {
    if (!literal) return;
    out += normalizeOldSpanish(normalizeString(literal));
    literal = "";
  };

  for (const ch of String(str)) {
    if (escaped) {
      literal += ch;
      escaped = false;
      continue;
    }
    if (ch === "\\") {
      literal += ch;
      escaped = true;
      continue;
    }
    if (inClass) {
      out += ch;
      if (ch === "]") inClass = false;
      continue;
    }
    if (inBrace) {
      out += ch;
      if (ch === "}") inBrace = false;
      continue;
    }
    if (ch === "[") {
      flushLiteral();
      out += ch;
      inClass = true;
      continue;
    }
    if (ch === "{") {
      flushLiteral();
      out += ch;
      inBrace = true;
      continue;
    }
    literal += ch;
  }
  flushLiteral();
  return out;
}

const FORMATTING_REGEX = /[^\p{L}\p{N}\s]/u;
const PUNCTUATION_REGEX = /[^\p{L}\p{N}\s]/gu;
const STREAMING_WORD_FIELDS = new Set(["Comentario"]);

function stripHtmlTags(str) {
  return str.replace(/<[^>]*>/g, " ");
}

function stripPunctuationCharacters(str) {
  return str.replace(PUNCTUATION_REGEX, " ");
}

function collapseWhitespace(str) {
  return str.replace(/\s+/g, " ").trim();
}

function hasFormattingCharacters(value) {
  if (!value) return false;
  const text = String(value);
  for (let i = 0; i < text.length; i += 1) {
    const code = text.charCodeAt(i);
    if (code <= 0x7f) {
      if (
        (code >= 48 && code <= 57) ||
        (code >= 65 && code <= 90) ||
        (code >= 97 && code <= 122) ||
        code === 9 ||
        code === 10 ||
        code === 12 ||
        code === 13 ||
        code === 32
      ) {
        continue;
      }
      return true;
    }
    return FORMATTING_REGEX.test(text);
  }
  return false;
}

function getRawDisplayValue(row, field) {
  const normalizedField = normalizeFieldKey(field);
  return (typeof getDisplayValue === "function")
    ? getDisplayValue(row, normalizedField)
    : (row[normalizedField] ?? row[field] ?? "");
}

function shouldStreamNormalizedWords(field) {
  return STREAMING_WORD_FIELDS.has(field);
}

function normalizeRawTextForSearch(raw, options = {}) {
  const accentSensitive = !!options.accentSensitive;
  const loose = !!options.loose;
  const useOldSpanish = !accentSensitive && options.oldSpanish !== false && oldSpanishMode;
  let text = accentSensitive
    ? stripHtmlTags(String(raw ?? "")).normalize("NFC").toLowerCase()
    : normalizeString(stripHtmlTags(String(raw ?? "")));
  if (useOldSpanish) text = normalizeOldSpanish(text);
  if (loose) text = collapseWhitespace(stripPunctuationCharacters(text));
  return text;
}

// ==============================
// Lazy normalization helpers
// ==============================
function getNormalizationCacheKey(row, field) {
  const usesWimmerEs = typeof wimmerShowEs !== "undefined"
    && wimmerShowEs
    && row.Fuente === "2021 Wimmer";
  return field + (usesWimmerEs ? "_es" : "");
}

function getRowNormalizationCache(row) {
  let rowCache = normalizationCache.get(row);
  if (!rowCache) {
    rowCache = {};
    normalizationCache.set(row, rowCache);
  }
  return rowCache;
}

function getNormalizedTextVariant(row, field, options = {}) {
  if (shouldStreamNormalizedWords(field)) {
    return normalizeRawTextForSearch(getRawDisplayValue(row, field), options);
  }
  const rowCache = getRowNormalizationCache(row);
  const cacheKey = getNormalizationCacheKey(row, field) + "__text";
  if (!rowCache[cacheKey]) {
    rowCache[cacheKey] = {
      raw: getRawDisplayValue(row, field)
    };
  }
  const entry = rowCache[cacheKey];
  const loose = !!options.loose;

  if (options.accentSensitive) {
    if (entry.withAccents === undefined) {
      entry.withAccents = stripHtmlTags(entry.raw).normalize("NFC").toLowerCase();
    }
    if (!loose) return entry.withAccents;
    if (entry.looseWithAccents === undefined) {
      entry.looseWithAccents = collapseWhitespace(stripPunctuationCharacters(entry.withAccents));
    }
    return entry.looseWithAccents;
  }

  if (entry.normalized === undefined) {
    entry.normalized = normalizeString(stripHtmlTags(entry.raw));
  }
  const useOldSpanish = options.oldSpanish !== false && oldSpanishMode;
  if (useOldSpanish) {
    if (entry.normalizedOS === undefined) {
      entry.normalizedOS = normalizeOldSpanish(entry.normalized);
    }
    if (!loose) return entry.normalizedOS;
    if (entry.looseTextOS === undefined) {
      if (entry.looseText === undefined) {
        entry.looseText = collapseWhitespace(stripPunctuationCharacters(entry.normalized));
      }
      entry.looseTextOS = normalizeOldSpanish(entry.looseText);
    }
    return entry.looseTextOS;
  }

  if (!loose) return entry.normalized;
  if (entry.looseText === undefined) {
    entry.looseText = collapseWhitespace(stripPunctuationCharacters(entry.normalized));
  }
  return entry.looseText;
}

function getNormalizedEntry(row, field) {
  const rowCache = getRowNormalizationCache(row);
  const cacheKey = getNormalizationCacheKey(row, field);
  if (!rowCache[cacheKey]) {
    const raw = getRawDisplayValue(row, field);
    const normalized = normalizeString(stripHtmlTags(raw));
    const looseText = collapseWhitespace(stripPunctuationCharacters(normalized));
    const words = normalized
      .split(/\s+/)
      .filter(Boolean)
      .map(word => ({
        raw: word,
        loose: collapseWhitespace(stripPunctuationCharacters(word))
      }));
    // Accent-preserved candidate: NFC-normalized then lowercased (no accent stripping).
    // NFC ensures precomposed form matches user input from browser keyboards.
    const withAccents = stripHtmlTags(raw).normalize("NFC").toLowerCase();
    const looseWithAccents = collapseWhitespace(stripPunctuationCharacters(withAccents));
    const wordsWithAccents = withAccents
      .split(/\s+/)
      .filter(Boolean)
      .map(word => ({
        raw: word,
        loose: collapseWhitespace(stripPunctuationCharacters(word))
      }));
    rowCache[cacheKey] = {
      normalized,
      looseText,
      words,
      withAccents,
      looseWithAccents,
      wordsWithAccents
    };
  }

  const entry = rowCache[cacheKey];
  if (oldSpanishMode && !entry.normalizedOS) {
    entry.normalizedOS = normalizeOldSpanish(entry.normalized);
    entry.looseTextOS = normalizeOldSpanish(entry.looseText);
    entry.wordsOS = entry.words.map(w => ({
      raw: normalizeOldSpanish(w.raw),
      loose: normalizeOldSpanish(w.loose)
    }));
  }

  return entry;
}

const LETTER_WILDCARD_PATTERN = "[A-Za-z\u00C0-\u024F\u1E00-\u1EFF]";
const NAHUATL_GRAPHEME_DIGRAPHS = "ch|tz|hu|uh|qu|cu|uc|ll|rr|gu";
const NAHUATL_GRAPHEME_PATTERN = `(?:${NAHUATL_GRAPHEME_DIGRAPHS}|(?!${NAHUATL_GRAPHEME_DIGRAPHS})[A-Za-z\u00C0-\u024F\u1E00-\u1EFF])`;
const NAHUATL_GRAPHEME_FIELDS = new Set(["Editado", "Original", "Comentario"]);
const REDUPLICATION_VOWELS = /[aeiouáâãäàāéêëèēíîïìīóôõöòōúûüùýÿ]/i;
let reduplicationMarkerCounter = 0;
let sameAgainMarkerCounter = 0;

function getWildcardUnit(options = {}) {
  return NAHUATL_GRAPHEME_FIELDS.has(options.field) ? NAHUATL_GRAPHEME_PATTERN : LETTER_WILDCARD_PATTERN;
}

function buildFilterQuery(filter) {
  const query = parseFilterValue(filter.value ?? "", filter.mode, { field: filter?.field });
  if (filter && filter.strictCompare) {
    query.allowLoose = false;
  }
  return query;
}

function escapeRegex(ch) {
  return ch.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Alias kept for internal callers
const escapeRegexCharacter = escapeRegex;

function escapeRegexClassCharacters(value) {
  return String(value || "").replace(/[\\\]\-\^]/g, "\\$&");
}

function buildCustomBraceClass(inner) {
  const sign = String(inner || "")[0];
  if (sign !== "=" && sign !== "!") return null;
  const body = String(inner).slice(1);
  if (!body) return null;
  return `[${sign === "!" ? "^" : ""}${escapeRegexClassCharacters(body)}]`;
}

function expandVCPlaceholders(value) {
  if (!value) return "";
  const map = {
    C: "(?:ch|tz|hu|uh|qu|cu|uc|ll|rr|gu|[bcdfghjklmnñpqrstvwxyz])",
    V: "[aeiouáâãäàāéêëèēíîïìīóôõöòōúûüùýÿ\u1E00-\u1EFF]",
    N: "(?:m|n|ñ)",
    L: "(?:l|ll|r|rr)",
    S: "(?:tz|s|z|x)",
    G: "(?:hu|uh|y|w)",
    P: "(?:ch|tz|qu|cu|uc|p|t|c|b|d|g|k)",
    A: "[A-Za-z\u00C0-\u024F\u1E00-\u1EFF]"
  };
  const expandInner = segment => segment.replace(/\\[A-Za-z]|[A-Za-z]\??/g, m => {
    if (m.startsWith("\\")) return m.slice(1);
    const optional = m.endsWith("?");
    const key = optional ? m.slice(0, -1) : m;
    const expansion = map[key.toUpperCase()];
    if (!expansion) return m;
    return optional ? `${expansion}?` : expansion;
  });
  // Expande solo dentro de llaves { } y permite escape \{ \} \c \v etc.
  let out = "";
  let i = 0;
  while (i < value.length) {
    const ch = value[i];
    if (ch === "\\") {
      if (i + 1 < value.length) {
        out += ch + value[i + 1];
        i += 2;
      } else {
        out += ch;
        i++;
      }
      continue;
    }
    if (ch === "{") {
      let end = value.indexOf("}", i + 1);
      if (end === -1) {
        out += ch;
        i++;
        continue;
      }
      const inner = value.slice(i + 1, end);
      // Pass numeric quantifiers like {2}, {2,4}, {2,}; accept ":" as ",".
      if (/^\d+([,:]\d*)?$/.test(inner)) {
        out += `{${inner.replace(":", ",")}}`;
        i = end + 1;
        continue;
      }
      const customClass = buildCustomBraceClass(inner);
      if (customClass) {
        out += `(?:${customClass})`;
        i = end + 1;
        continue;
      }
      const countedBlock = parseBraceCount(inner);
      if (countedBlock) {
        out += `(?:${expandInner(countedBlock.body)})${countRangeQuantifier(countedBlock)}`;
        i = end + 1;
        continue;
      }
      const expanded = expandInner(inner);
      out += `(?:${expanded})`;
      i = end + 1;
      continue;
    }
    out += ch;
    i++;
  }
  return out;
}

function parseBraceCount(inner) {
  const match = String(inner || "").match(/^([A-Za-z]+)(\d+)(?:-(\d*))?$/);
  if (!match) return null;
  const min = Number(match[2]);
  const hasRange = match[3] !== undefined;
  const max = hasRange && match[3] !== "" ? Number(match[3]) : hasRange ? null : min;
  if (max !== null && max < min) return null;
  return { body: match[1], min, max };
}

function countRangeQuantifier(range) {
  if (range.max === range.min) return `{${range.min}}`;
  if (range.max === null) return `{${range.min},}`;
  return `{${range.min},${range.max}}`;
}

function expandReduplication(value, options = {}) {
  if (!value) return null;
  const trimmed = value.replace(/^-+/, "").replace(/-+$/, "");
  if (!trimmed || !trimmed.startsWith("+")) return null;
  const base = trimmed.slice(1).trim();
  if (!base) return null;
  const chars = Array.from(base);
  const isVowel = ch => /[aeiouáéíóúüAEIOUÁÉÍÓÚÜ]/.test(ch);
  let vowelIdx = -1;
  for (let i = 0; i < chars.length; i++) {
    if (isVowel(chars[i])) {
      vowelIdx = i;
      break;
    }
  }
  let prefix = vowelIdx >= 0 ? base.slice(0, vowelIdx + 1) : base.slice(0, 1);
  if (!prefix) prefix = base.slice(0, 1);
  const rest = base.slice(prefix.length);
  const escPrefix = escapeRegexCharacter(prefix);
  const restBody = convertWildcardPatternAllowRegex(expandVCPlaceholders(rest), options);
  return `(?:${escPrefix}){2}${restBody}`;
}

function expandReduplicationMarkers(value, options = {}) {
  const source = String(value || "");
  if (!/[{][Rr](?:[1-9]\d*(?:-\d*)?)?[}]/.test(source)) return null;

  let out = "";
  let i = 0;
  while (i < source.length) {
    const marker = findNextReduplicationMarker(source, i);
    if (!marker) {
      out += expandPatternSegmentForRegex(source.slice(i), options);
      break;
    }
    const optionalGroup = readOptionalReduplicationMarkerGroup(source, marker.start);
    if (optionalGroup) {
      out += expandPatternSegmentForRegex(source.slice(i, optionalGroup.openIdx), options);
      const target = readReduplicationMarkerTarget(source, optionalGroup.end);
      if (!target) return null;
      const targetBody = expandPatternSegmentForRegex(target.target, options);
      if (!targetBody) return null;
      out += `(?:${buildReduplicationPrefixBody(targetBody, optionalGroup.infixBody, optionalGroup)})?`;
      i = optionalGroup.end;
      continue;
    }
    out += expandPatternSegmentForRegex(source.slice(i, marker.start), options);
    const target = readReduplicationMarkerTarget(source, marker.end);
    if (!target) return null;
    const targetBody = expandPatternSegmentForRegex(target.target, options);
    if (!targetBody) return null;
    const infixBody = target.infixBody ?? expandPatternSegmentForRegex(target.infix, options);
    out += buildReduplicationFullBody(targetBody, infixBody, marker);
    i = target.end;
  }
  return out || null;
}

function buildReduplicationFullBody(targetBody, infixBody, marker) {
  const groupName = `r${++reduplicationMarkerCounter}`;
  const repeatUnit = `${infixBody}\\k<${groupName}>`;
  return `(?<${groupName}>${targetBody})(?:${repeatUnit})${markerRepeatQuantifier(marker, -1)}`;
}

function buildReduplicationPrefixBody(targetBody, infixBody, marker) {
  const groupName = `r${++reduplicationMarkerCounter}`;
  return `(?<${groupName}>${targetBody})${infixBody}(?:\\k<${groupName}>${infixBody})${markerRepeatQuantifier(marker, -2)}`;
}

function readOptionalReduplicationMarkerGroup(value, markerIdx) {
  const openIdx = markerIdx - 1;
  if (openIdx < 0 || value[openIdx] !== "(" || isEscapedAt(value, openIdx)) return null;
  const closeIdx = findMatchingGroupClose(value, openIdx);
  const marker = readReduplicationMarkerAt(value, markerIdx);
  if (!marker || closeIdx === -1 || closeIdx < marker.end) return null;
  const inner = value.slice(openIdx + 1, closeIdx);
  const innerMarker = readReduplicationMarkerAt(inner, 0);
  if (!innerMarker) return null;
  const tail = inner.slice(innerMarker.raw.length);
  if (splitTopLevel(tail, "|").length > 1) return null;
  if (!tail) {
    return { openIdx, end: closeIdx + 1, infix: "", infixBody: "", min: innerMarker.min, max: innerMarker.max };
  }
  const optionalH = parseOptionalReduplicationHInfix(tail);
  if (optionalH) {
    return { openIdx, end: closeIdx + 1, infix: tail, infixBody: optionalH.body, min: innerMarker.min, max: innerMarker.max };
  }
  if (tail === "h" && !isEscapedAt(tail, 0)) {
    return { openIdx, end: closeIdx + 1, infix: tail, infixBody: "h", min: innerMarker.min, max: innerMarker.max };
  }
  return null;
}

function findNextReduplicationMarker(value, startIdx = 0) {
  for (let i = startIdx; i < value.length; i++) {
    const marker = readReduplicationMarkerAt(value, i);
    if (marker) return marker;
  }
  return null;
}

function isReduplicationMarkerAt(value, idx) {
  return !!readReduplicationMarkerAt(value, idx);
}

function readReduplicationMarkerAt(value, idx) {
  if (idx < 0 || isEscapedAt(value, idx)) return null;
  const match = String(value || "").slice(idx).match(/^\{[Rr]([1-9]\d*(?:-\d*)?)?\}/);
  if (!match) return null;
  const range = parseMarkerCount(match[1]);
  if (!range) return null;
  return {
    raw: match[0],
    start: idx,
    end: idx + match[0].length,
    min: range.min,
    max: range.max
  };
}

function parseMarkerCount(raw) {
  if (!raw) return { min: 2, max: 2 };
  const match = raw.match(/^([1-9]\d*)(?:-(\d*))?$/);
  if (!match) return null;
  const min = Number(match[1]);
  const hasRange = match[2] !== undefined;
  const max = hasRange && match[2] !== "" ? Number(match[2]) : hasRange ? null : min;
  if (max !== null && max < min) return null;
  return { min, max };
}

function markerRepeatQuantifier(marker, offset) {
  const min = Math.max(0, marker.min + offset);
  const max = marker.max === null ? null : Math.max(0, marker.max + offset);
  if (max === min) return `{${min}}`;
  if (max === null) return `{${min},}`;
  return `{${min},${max}}`;
}

function expandPatternSegmentForRegex(segment, options = {}) {
  if (!segment) return "";
  return convertWildcardPatternAllowRegex(expandVCPlaceholders(segment), options);
}

function readReduplicationMarkerTarget(value, startIdx) {
  const brace = findNextBracePlaceholder(value, startIdx);
  if (brace) {
    const prefix = value.slice(startIdx, brace.start);
    const optionalH = parseOptionalReduplicationHInfix(prefix);
    if (optionalH) {
      return {
        infix: prefix,
        infixBody: optionalH.body,
        target: brace.raw,
        end: brace.end
      };
    }
    if (!REDUPLICATION_VOWELS.test(prefix)) {
      return {
        infix: prefix,
        target: brace.raw,
        end: brace.end
      };
    }
  }

  const literal = readLiteralReduplicationTarget(value, startIdx, brace ? brace.start : value.length);
  if (literal) return literal;
  if (brace) {
    return {
      infix: value.slice(startIdx, brace.start),
      target: brace.raw,
      end: brace.end
    };
  }
  return null;
}

function findNextBracePlaceholder(value, startIdx) {
  for (let i = startIdx; i < value.length; i++) {
    if (value[i] !== "{" || isEscapedAt(value, i)) continue;
    const end = value.indexOf("}", i + 1);
    if (end === -1) return null;
    const inner = value.slice(i + 1, end);
    if (/^\d+([,:]\d*)?$/.test(inner) || /^[Rr](?:[1-9]\d*(?:-\d*)?)?$/.test(inner)) {
      i = end;
      continue;
    }
    return {
      raw: value.slice(i, end + 1),
      start: i,
      end: end + 1
    };
  }
  return null;
}

function readLiteralReduplicationTarget(value, startIdx, stopIdx = value.length) {
  const optionalH = readOptionalReduplicationH(value, startIdx, stopIdx);
  if (optionalH) {
    const afterOptionalH = readLiteralSyllable(value, optionalH.end, stopIdx);
    if (afterOptionalH) {
      return {
        infix: optionalH.raw,
        infixBody: optionalH.body,
        target: afterOptionalH.target,
        end: afterOptionalH.end
      };
    }
  }
  if (value[startIdx] === "h") {
    const afterSaltillo = readLiteralSyllable(value, startIdx + 1, stopIdx);
    if (afterSaltillo) {
      return {
        infix: "h",
        target: afterSaltillo.target,
        end: afterSaltillo.end
      };
    }
  }
  const syllable = readLiteralSyllable(value, startIdx, stopIdx);
  return syllable ? { infix: "", target: syllable.target, end: syllable.end } : null;
}

function parseOptionalReduplicationHInfix(value) {
  if (value === "(h)" && !isEscapedAt(value, 0)) {
    return { raw: value, body: "(?:h)?" };
  }
  return null;
}

function expandSameAgainMarkers(value, options = {}) {
  const source = String(value || "");
  if (!source.includes("(") || !/[{][Rr](?:[1-9]\d*(?:-\d*)?)?[}]/.test(source)) return null;
  let out = "";
  let last = 0;
  let changed = false;

  for (let i = 0; i < source.length; i++) {
    if (source[i] !== "(" || isEscapedAt(source, i)) continue;
    const closeIdx = findMatchingGroupClose(source, i);
    if (closeIdx === -1) continue;
    const marker = readReduplicationMarkerAt(source, closeIdx + 1);
    if (!marker) {
      i = closeIdx;
      continue;
    }
    out += expandPatternSegmentForRegex(source.slice(last, i), options);
    const inner = source.slice(i + 1, closeIdx);
    const body = expandPatternSegmentForRegex(inner, options);
    if (!body) return null;
    out += buildSameAgainBody(body, marker);
    last = marker.end;
    i = marker.end - 1;
    changed = true;
  }

  if (!changed) return null;
  out += expandPatternSegmentForRegex(source.slice(last), options);
  return out;
}

function buildSameAgainBody(body, marker) {
  const groupName = `s${++sameAgainMarkerCounter}`;
  return `(?<${groupName}>${body})\\k<${groupName}>${markerRepeatQuantifier(marker, -1)}`;
}

function buildContextCondition(text, options = {}) {
  const source = String(text || "");
  const op = findTopLevelContextOperator(source);
  if (!op) return null;
  const left = source.slice(0, op.index).trim();
  const right = source.slice(op.index + 1).trim();
  if (!left || !right) return null;
  const targetBody = buildCompositePatternBody(left, options);
  const contextBody = buildCompositePatternBody(right, options);
  if (!targetBody || !contextBody) return null;
  if (op.value === ">") return `(?:${targetBody})(?=${contextBody})`;
  return `(?<=${contextBody})(?:${targetBody})`;
}

function buildCompositePatternBody(text, options = {}) {
  const sameAgain = expandSameAgainMarkers(text, options);
  if (sameAgain) return sameAgain;
  const redupMarker = expandReduplicationMarkers(text, options);
  if (redupMarker) return redupMarker;
  const expandedVC = expandVCPlaceholders(text);
  return expandReduplication(expandedVC, options)
    || convertWildcardPatternAllowRegex(expandedVC, options);
}

function findTopLevelContextOperator(value) {
  let escaped = false;
  let parenDepth = 0;
  let braceDepth = 0;
  let bracketDepth = 0;
  for (let i = 0; i < value.length; i++) {
    const ch = value[i];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (ch === "\\") {
      escaped = true;
      continue;
    }
    if (bracketDepth > 0) {
      if (ch === "]") bracketDepth--;
      continue;
    }
    if (braceDepth > 0) {
      if (ch === "{") braceDepth++;
      else if (ch === "}") braceDepth--;
      continue;
    }
    if (ch === "[") {
      bracketDepth++;
      continue;
    }
    if (ch === "{") {
      braceDepth++;
      continue;
    }
    if (ch === "(") {
      parenDepth++;
      continue;
    }
    if (ch === ")" && parenDepth > 0) {
      parenDepth--;
      continue;
    }
    if (parenDepth === 0 && (ch === ">" || ch === "<")) {
      return { index: i, value: ch };
    }
  }
  return null;
}

function readOptionalReduplicationH(value, startIdx, stopIdx = value.length) {
  if (startIdx + 3 <= stopIdx && value.startsWith("(h)", startIdx) && !isEscapedAt(value, startIdx)) {
    return {
      raw: value.slice(startIdx, startIdx + 3),
      body: "(?:h)?",
      end: startIdx + 3
    };
  }
  return null;
}

function readLiteralSyllable(value, startIdx, stopIdx = value.length) {
  if (startIdx >= stopIdx) return null;
  let escaped = false;
  for (let i = startIdx; i < stopIdx; i++) {
    const ch = value[i];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (ch === "\\") {
      escaped = true;
      continue;
    }
    if ("{}()[\\]|^$*+?.".includes(ch)) return null;
    if (REDUPLICATION_VOWELS.test(ch)) {
      return {
        target: value.slice(startIdx, i + 1),
        end: i + 1
      };
    }
  }
  return null;
}

function parseFilterValue(rawValue, mode, options = {}) {
  const cleaned = rawValue == null ? "" : String(rawValue);
  const val = cleaned.trim();
  // "Acento exacto" ON  → all queries are accent-specific (lowercase-only, no stripping).
  // "Sin acento"   OFF → all queries ignore accents (full normalization).
  const queryHasAccents = accentSensitiveMode;

  if (!val) {
    return {
      strict: "",
      loose: "",
      hasRegex: false,
      allowLoose: false,
      hasWildcards: false,
      strictRegex: null,
      looseRegex: null
    };
  }

  const simpleLiteral = parseSimpleLiteralFilterValue(val, mode, queryHasAccents);
  if (simpleLiteral) return simpleLiteral;

  const altParts = splitAlternatives(val);

  const bodies = [];
  altParts.forEach(part => {
    let m = mode;
    let text = part;
    const leading = text.startsWith("-");
    const trailing = text.endsWith("-") && !isEscapedAt(text, text.length - 1);
    if (m === "exact") {
      if (leading && trailing && text.length > 2) {
        m = "any";
        text = text.slice(1, -1);
      } else if (trailing) {
        m = "starts";
        text = text.slice(0, -1);
      } else if (leading) {
        m = "ends";
        text = text.slice(1);
      }
    }
    text = text.replace(/\\-/g, "-").trim();
    if (!text) return;

    // Normalize the query text to match against the appropriate candidate.
    // In old-Spanish mode, normalize literal portions even around wildcards
    // and {vc} placeholders so x behaves like modern j in filters.
    if (!queryHasAccents && oldSpanishMode) {
      text = normalizeOldSpanishPatternText(text);
    } else if (!text.includes("{") && !text.includes("[")) {
      text = queryHasAccents ? text.normalize("NFC").toLowerCase() : normalizeString(text);
    }

    const phraseBody = buildQuotedPhrase(text);
    if (phraseBody) {
      bodies.push({ body: phraseBody, mode: m });
      return;
    }

    const containsBoth = buildContainsBoth(text, options);
    if (containsBoth) {
      bodies.push({ body: containsBoth, mode: m });
      return;
    }
    const context = buildContextCondition(text, options);
    if (context) {
      bodies.push({ body: context, mode: "any" });
      return;
    }
    const sameAgain = expandSameAgainMarkers(text, options);
    if (sameAgain) {
      bodies.push({ body: sameAgain, mode: m });
      return;
    }
    const redupMarker = expandReduplicationMarkers(text, options);
    if (redupMarker) {
      bodies.push({ body: redupMarker, mode: m });
      return;
    }
    const expandedVC = expandVCPlaceholders(text);
    const redup = expandReduplication(expandedVC, options);
    if (redup) {
      bodies.push({ body: redup, mode: m });
      return;
    }
    if (/[()[\]|]/.test(expandedVC)) {
      bodies.push({ body: convertWildcardPatternAllowRegex(expandedVC, options), mode: m });
      return;
    }
    bodies.push({ body: convertWildcardPattern(expandedVC, options), mode: m });
  });

  if (bodies.length) {
    const anchoredParts = bodies.map(b => {
      const bMode = b.mode || mode;
      if (bMode === "exact") return `^(?:${b.body})$`;
      if (bMode === "starts") return `^(?:${b.body})`;
      if (bMode === "ends") return `(?:${b.body})$`;
      return b.body;
    });
    const anchored = anchoredParts.length === 1
      ? anchoredParts[0]
      : anchoredParts.join("|");
    try {
      const rx = new RegExp(anchored, "i");
      return {
        strict: "",
        loose: "",
        hasRegex: true,
        allowLoose: !hasFormattingCharacters(val),
        accentSensitive: queryHasAccents,
        hasWildcards: false,
        strictRegex: rx,
        looseRegex: rx
      };
    } catch {
      // fall through
    }
  }

  // Fallback a coincidencia simple / comodines sin meta especial
  const strictBase = normalizeString(val);
  const strict = oldSpanishMode ? normalizeOldSpanish(strictBase) : strictBase;
  const withoutTags = stripHtmlTags(strict);
  const loose = collapseWhitespace(stripPunctuationCharacters(withoutTags));
  const hasWildcards = /[*?]/.test(val);
  const allowLoose = !hasFormattingCharacters(val);
  const strictRegex = hasWildcards ? createWildcardRegex(strict, mode, options) : null;
  const looseRegex = hasWildcards ? createWildcardRegex(loose, mode, options) : null;

  return {
    strict,
    loose,
    hasRegex: !!strictRegex,
    allowLoose,
    accentSensitive: queryHasAccents,
    hasWildcards,
    strictRegex,
    looseRegex
  };
}

function parseSimpleLiteralFilterValue(val, mode, queryHasAccents) {
  if (mode === "regex") return null;
  if (!val || val.startsWith("+")) return null;
  if (/[\\*?"()[\]{}|<>]/.test(val)) return null;

  let effectiveMode = mode;
  let text = val;
  const leading = text.startsWith("-");
  const trailing = text.endsWith("-") && !isEscapedAt(text, text.length - 1);
  if (mode === "exact") {
    if (leading && trailing && text.length > 2) {
      effectiveMode = "any";
      text = text.slice(1, -1);
    } else if (trailing) {
      effectiveMode = "starts";
      text = text.slice(0, -1);
    } else if (leading) {
      effectiveMode = "ends";
      text = text.slice(1);
    }
  }

  text = text.replace(/\\-/g, "-").trim();
  if (!text) return null;

  let strict = queryHasAccents
    ? text.normalize("NFC").toLowerCase()
    : normalizeString(text);
  if (!queryHasAccents && oldSpanishMode) {
    strict = normalizeOldSpanish(strict);
  }
  const loose = collapseWhitespace(stripPunctuationCharacters(stripHtmlTags(strict)));
  const allowLoose = !hasFormattingCharacters(val);

  return {
    strict,
    loose,
    hasRegex: false,
    allowLoose,
    accentSensitive: queryHasAccents,
    hasWildcards: false,
    strictRegex: null,
    looseRegex: null,
    effectiveMode
  };
}

function splitAlternatives(str) {
  return splitTopLevel(str, "|");
}

function buildQuotedPhrase(value) {
  if (!isQuoted(value)) return null;
  const phrase = unquote(value);
  if (!phrase) return null;
  return escapeRegexCharacter(phrase).replace(/\s+/g, "\\s+");
}

function isQuoted(value) {
  return value.length >= 2 && value[0] === "\"" && value[value.length - 1] === "\"" && !isEscapedAt(value, value.length - 1);
}

function unquote(value) {
  return value.slice(1, -1).replace(/\\(["\\])/g, "$1");
}

function convertWildcardPattern(value, options = {}) {
  const unit = getWildcardUnit(options);
  let out = "";
  for (let i = 0; i < value.length; ) {
    const ch = value[i];
    if (ch === "\\") {
      if (i + 1 < value.length) {
        out += escapeRegexCharacter(value[i + 1]);
        i += 2;
      } else {
        out += "\\\\";
        i++;
      }
      continue;
    }
    if (ch === "?") {
      const range = readWildcardRange(value, i + 1);
      if (range) {
        out += `${unit}{${range.quantifier}}`;
        i += 1 + range.raw.length;
        continue;
      }
      let run = 1;
      while (i + run < value.length && value[i + run] === "?") {
        run++;
      }
      out += `${unit}{${run}}`;
      i += run;
      continue;
    }
    if (ch === "*") {
      const nextIsStar = i + 1 < value.length && value[i + 1] === "*";
      if (nextIsStar) {
        out += `${unit}{2,}`;
        i += 2;
      } else {
        out += `${unit}+`;
        i += 1;
      }
      continue;
    }
    out += escapeRegexCharacter(ch);
    i++;
  }
  return out;
}

function convertWildcardPatternAllowRegex(value, options = {}) {
  const unit = getWildcardUnit(options);
  let out = "";
  let inClass = false;
  for (let i = 0; i < value.length; ) {
    const ch = value[i];
    if (inClass) {
      if (ch === "\\") {
        out += ch;
        if (i + 1 < value.length) {
          out += value[i + 1];
          i += 2;
        } else {
          i++;
        }
        continue;
      }
      out += ch;
      if (ch === "]") inClass = false;
      i++;
      continue;
    }
    if (ch === "\\") {
      if (i + 1 < value.length) {
        if (/\d/.test(value[i + 1])) {
          out += `\\${value[i + 1]}`;
        } else {
          out += escapeRegexCharacter(value[i + 1]);
        }
        i += 2;
      } else {
        out += "\\\\";
        i++;
      }
      continue;
    }
    if (ch === "[") {
      inClass = true;
      out += ch;
      i++;
      continue;
    }
    if (ch === "(") {
      const optionalGroup = readOptionalGroup(value, i, options);
      if (optionalGroup) {
        out += optionalGroup.body;
        i = optionalGroup.end;
        continue;
      }
      out += ch;
      i++;
      continue;
    }
    if (ch === "?") {
      if (i > 0 && value[i - 1] === ")" && precedingGroupHasAlternatives(value, i - 1)) {
        const range = readWildcardRange(value, i + 1);
        if (range) {
          out += `${unit}{${range.quantifier}}`;
          i += 1 + range.raw.length;
          continue;
        }
        let run = 1;
        while (i + run < value.length && value[i + run] === "?") run++;
        out += `${unit}{${run}}`;
        i += run;
        continue;
      }
      // Regex quantifier context: after ( for (?:...), after ) or ] for optional group/class
      if (i > 0 && value[i - 1] === "(" && /[:=!<]/.test(value[i + 1] || "")) {
        out += ch;
        i++;
        continue;
      }
      if (i > 0 && ")]".includes(value[i - 1])) {
        out += ch;
        i++;
        continue;
      }
      const range = readWildcardRange(value, i + 1);
      if (range) {
        out += `${unit}{${range.quantifier}}`;
        i += 1 + range.raw.length;
        continue;
      }
      let run = 1;
      while (i + run < value.length && value[i + run] === "?") run++;
      out += `${unit}{${run}}`;
      i += run;
      continue;
    }
    if (ch === "*") {
      if (i > 0 && value[i - 1] === ")" && precedingGroupHasAlternatives(value, i - 1)) {
        const nextIsStar = i + 1 < value.length && value[i + 1] === "*";
        if (nextIsStar) {
          out += `${unit}{2,}`;
          i += 2;
        } else {
          out += `${unit}+`;
          i += 1;
        }
        continue;
      }
      // Regex quantifier after a group or class — pass through
      if (i > 0 && ")]}".includes(value[i - 1])) {
        out += ch;
        i++;
        continue;
      }
      const nextIsStar = i + 1 < value.length && value[i + 1] === "*";
      if (nextIsStar) {
        out += `${unit}{2,}`;
        i += 2;
      } else {
        out += `${unit}+`;
        i += 1;
      }
      continue;
    }
    if (ch === "+") {
      // Regex quantifier after a group or class — pass through
      if (i > 0 && ")]}".includes(value[i - 1])) {
        out += ch;
        i++;
        continue;
      }
      out += escapeRegexCharacter(ch);
      i++;
      continue;
    }
    // No escapamos metacaracteres de regex para respetar ){}[]| ya presentes
    if (")]{}|".includes(ch)) {
      out += ch;
      i++;
      continue;
    }
    out += escapeRegexCharacter(ch);
    i++;
  }
  return out;
}

function readOptionalGroup(value, startIdx, options = {}) {
  const closeIdx = findMatchingGroupClose(value, startIdx);
  if (closeIdx === -1) return null;
  if (value[closeIdx + 1] === "?") return null;
  if (value[closeIdx + 1] === "\\" && /\d/.test(value[closeIdx + 2] || "")) return null;
  const inner = value.slice(startIdx + 1, closeIdx);
  if (!inner || /^\?[:=!<]/.test(inner) || splitTopLevel(inner, "|").length > 1) return null;
  const body = convertWildcardPatternAllowRegex(expandVCPlaceholders(inner), options);
  return {
    body: `(?:${body})?`,
    end: closeIdx + 1
  };
}

function findMatchingGroupClose(value, openIdx) {
  let inClass = false;
  let escape = false;
  let depth = 0;
  for (let i = openIdx; i < value.length; i++) {
    const ch = value[i];
    if (escape) {
      escape = false;
      continue;
    }
    if (ch === "\\") {
      escape = true;
      continue;
    }
    if (inClass) {
      if (ch === "]") inClass = false;
      continue;
    }
    if (ch === "[") {
      inClass = true;
      continue;
    }
    if (ch === "(") {
      depth++;
      continue;
    }
    if (ch === ")" && depth > 0) {
      depth--;
      if (depth === 0) return i;
    }
  }
  return -1;
}

function isEscapedAt(value, idx) {
  let slashCount = 0;
  for (let i = idx - 1; i >= 0 && value[i] === "\\"; i--) {
    slashCount++;
  }
  return slashCount % 2 === 1;
}

function readWildcardRange(value, startIdx) {
  const match = value.slice(startIdx).match(/^\{(\d+(?:[,:]\d*)?)\}/);
  if (!match) return null;
  return {
    raw: match[0],
    quantifier: match[1].replace(":", ",")
  };
}

function precedingGroupHasAlternatives(value, closeIdx) {
  const openIdx = findMatchingGroupOpen(value, closeIdx);
  if (openIdx === -1) return false;
  return splitTopLevel(value.slice(openIdx + 1, closeIdx), "|").length > 1;
}

function findMatchingGroupOpen(value, closeIdx) {
  const stack = [];
  let inClass = false;
  let escape = false;
  for (let i = 0; i <= closeIdx; i++) {
    const ch = value[i];
    if (escape) {
      escape = false;
      continue;
    }
    if (ch === "\\") {
      escape = true;
      continue;
    }
    if (inClass) {
      if (ch === "]") inClass = false;
      continue;
    }
    if (ch === "[") {
      inClass = true;
      continue;
    }
    if (ch === "(") {
      stack.push(i);
      continue;
    }
    if (ch === ")") {
      const openIdx = stack.pop();
      if (i === closeIdx) return openIdx ?? -1;
    }
  }
  return -1;
}

function splitTopLevel(str, delimiter) {
  const parts = [];
  let buf = "";
  let depth = 0;
  let inClass = false;
  let inQuote = false;
  let escape = false;
  for (let i = 0; i < str.length; i++) {
    const ch = str[i];
    if (escape) {
      buf += ch;
      escape = false;
      continue;
    }
    if (ch === "\\") {
      buf += ch;
      escape = true;
      continue;
    }
    if (ch === "\"") {
      inQuote = !inQuote;
      buf += ch;
      continue;
    }
    if (inQuote) {
      buf += ch;
      continue;
    }
    if (inClass) {
      if (ch === "]") inClass = false;
      buf += ch;
      continue;
    }
    if (ch === "[") {
      inClass = true;
      buf += ch;
      continue;
    }
    if (ch === "(") {
      depth++;
      buf += ch;
      continue;
    }
    if (ch === ")" && depth > 0) {
      depth--;
      buf += ch;
      continue;
    }
    if (str.startsWith(delimiter, i) && depth === 0) {
      parts.push(buf);
      buf = "";
      i += delimiter.length - 1;
      continue;
    }
    buf += ch;
  }
  parts.push(buf);
  return parts.map(p => p.trim()).filter(Boolean);
}

function buildContainsBoth(text, options = {}) {
  if (!text.startsWith("(") || !text.endsWith(")")) return null;
  const inner = text.slice(1, -1);
  if (!inner.includes("||")) return null;
  const parts = splitTopLevel(inner, "||");
  if (parts.length < 2) return null;
  const lookaheads = parts.map(p => {
    const body = expandReduplicationMarkers(p, options)
      || convertWildcardPatternAllowRegex(expandVCPlaceholders(p), options);
    return `(?=.*${body})`;
  });
  return `${lookaheads.join("")}.*`;
}

function createWildcardRegex(value, mode, options = {}) {
  if (!value) return null;
  const body = convertWildcardPattern(value, options);
  let pattern = body;
  if (mode === "exact") {
    pattern = `^${body}$`;
  } else if (mode === "starts") {
    pattern = `^${body}`;
  } else if (mode === "ends") {
    pattern = `${body}$`;
  }
  return new RegExp(pattern, "i");
}
