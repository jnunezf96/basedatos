// data.js - Data storage and normalization helpers

let dataRows = [];
let normalizationCache = new Map();
let oldSpanishMode = false;
let accentSensitiveMode = false; // false = accent-free (default); true = accent-exact

// ==============================
// CSV Loader
// ==============================
function loadCSV(path, callback) {
  Papa.parse(path, {
    download: true,
    header: true,
    skipEmptyLines: true,
    complete: results => callback(results.data)
  });
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
    .replace(/v/g, "b");
}

const FORMATTING_REGEX = /[^\p{L}\p{N}\s]/u;
const PUNCTUATION_REGEX = /[^\p{L}\p{N}\s]/gu;

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
  return FORMATTING_REGEX.test(value);
}

// ==============================
// Lazy normalization helpers
// ==============================
function getNormalizedEntry(row, field) {
  let rowCache = normalizationCache.get(row);
  if (!rowCache) {
    rowCache = {};
    normalizationCache.set(row, rowCache);
  }

  const cacheKey = field + ((typeof wimmerShowEs !== "undefined" && wimmerShowEs && row.Fuente === "2021 Wimmer") ? "_es" : "");
  if (!rowCache[cacheKey]) {
    const raw = (typeof getDisplayValue === "function") ? getDisplayValue(row, field) : (row[field] ?? "");
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

function getNormalizedValue(row, field) {
  return getNormalizedEntry(row, field).normalized;
}

function buildFilterQuery(filter) {
  return parseFilterValue(filter.value ?? "", filter.mode);
}

function escapeRegex(ch) {
  return ch.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Alias kept for internal callers
const escapeRegexCharacter = escapeRegex;

function expandVCPlaceholders(value) {
  if (!value) return "";
  const map = {
    C: "(?:ch|tz|hu|uh|qu|cu|uc|ll|rr|gu|[bcdfghjklmnñpqrstvwxyz])",
    V: "[aeiouáâãäàāéêëèēíîïìīóôõöòōúûüùýÿ]",
    N: "(?:m|n|ñ)",
    L: "(?:l|ll|r|rr)",
    S: "(?:tz|s|z|x)",
    G: "(?:hu|uh|y|w)",
    P: "(?:ch|tz|qu|cu|uc|p|t|c|b|d|g|k)",
    A: "[A-Za-z\u00C0-\u024F]"
  };
  // Expande solo dentro de llaves { } y permite escape \{ \} \C \V \N \L \S \G
  let out = "";
  let i = 0;
  while (i < value.length) {
    const ch = value[i];
    if (ch === "\\") {
      if (i + 1 < value.length) {
        out += value[i + 1];
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
      // Pass numeric quantifiers like {2}, {2,4}, {2,} straight through
      if (/^\d+(,\d*)?$/.test(inner)) {
        out += `{${inner}}`;
        i = end + 1;
        continue;
      }
      const expanded = inner.replace(/\\[A-Z]|[A-Z]\??/g, m => {
        if (m.startsWith("\\")) return m.slice(1);
        const optional = m.endsWith("?");
        const key = optional ? m.slice(0, -1) : m;
        const expansion = map[key];
        if (!expansion) return m;
        return optional ? `${expansion}?` : expansion;
      });
      out += `(${expanded})`;
      i = end + 1;
      continue;
    }
    out += ch;
    i++;
  }
  return out;
}

function expandReduplication(value) {
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
  const restBody = convertWildcardPatternAllowRegex(expandVCPlaceholders(rest));
  return `(?:${escPrefix}){2}${restBody}`;
}

function parseFilterValue(rawValue, mode) {
  const cleaned = rawValue == null ? "" : String(rawValue);
  const literalRegex = cleaned.match(/^\/(.+)\/([gimsuy]*)$/);
  if (literalRegex) {
    try {
      const rx = new RegExp(literalRegex[1], literalRegex[2] || "i");
      return {
        strict: "",
        loose: "",
        hasRegex: true,
        allowLoose: true,
        hasWildcards: false,
        strictRegex: rx,
        looseRegex: rx
      };
    } catch {
      // fall through to other parsing
    }
  }

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

  const altParts = splitAlternatives(val);

  const bodies = [];
  altParts.forEach(part => {
    let m = mode;
    let text = part;
    const leading = text.startsWith("-");
    const trailing = text.endsWith("-");
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

    // Normalize the query text to match against the appropriate candidate:
    // - Plain queries (no accents): full normalization → accent-blind matching
    // - Accented queries: lowercase only → accent-specific matching
    // Skip normalization if the text uses {VC} placeholders or character classes.
    if (!text.includes("{") && !text.includes("[")) {
      text = queryHasAccents ? text.normalize("NFC").toLowerCase() : normalizeString(text);
    }

    const expandedVC = expandVCPlaceholders(text);
    const containsBoth = buildContainsBoth(expandedVC);
    if (containsBoth) {
      bodies.push({ body: containsBoth, mode: m });
      return;
    }
    const redup = expandReduplication(expandedVC);
    if (redup) {
      bodies.push({ body: redup, mode: m });
      return;
    }
    if (/[()[\]|]/.test(expandedVC)) {
      bodies.push({ body: convertWildcardPatternAllowRegex(expandedVC), mode: m });
      return;
    }
    bodies.push({ body: convertWildcardPattern(expandedVC), mode: m });
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
  const strictRegex = hasWildcards ? createWildcardRegex(strict, mode) : null;
  const looseRegex = hasWildcards ? createWildcardRegex(loose, mode) : null;

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

function splitAlternatives(str) {
  const parts = [];
  let buf = "";
  let depth = 0;
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
    if (ch === "|" && depth === 0) {
      if (buf.trim()) parts.push(buf.replace(/\\\|/g, "|").trim());
      buf = "";
      continue;
    }
    buf += ch;
  }
  if (buf.trim()) parts.push(buf.replace(/\\\|/g, "|").trim());
  return parts;
}

function convertWildcardPattern(value) {
  const letter = "[A-Za-z\u00C0-\u024F]";
  let out = "";
  for (let i = 0; i < value.length; ) {
    const ch = value[i];
    if (ch === "?") {
      const rangeMatch = value.slice(i + 1).match(/^\{(\d+(?:,\d*)?)\}/);
      if (rangeMatch) {
        out += `${letter}{${rangeMatch[1]}}`;
        i += 1 + rangeMatch[0].length;
        continue;
      }
      let run = 1;
      while (i + run < value.length && value[i + run] === "?") {
        run++;
      }
      out += `${letter}{${run}}`;
      i += run;
      continue;
    }
    if (ch === "*") {
      const nextIsStar = i + 1 < value.length && value[i + 1] === "*";
      if (nextIsStar) {
        out += `${letter}{2,}`;
        i += 2;
      } else {
        out += `${letter}+`;
        i += 1;
      }
      continue;
    }
    out += escapeRegexCharacter(ch);
    i++;
  }
  return out;
}

function convertWildcardPatternAllowRegex(value) {
  const letter = "[A-Za-z\u00C0-\u024F]";
  let out = "";
  for (let i = 0; i < value.length; ) {
    const ch = value[i];
    if (ch === "?") {
      // Regex quantifier context: after ( for (?:...), after ) or ] for optional group/class
      if (i > 0 && "()[]".includes(value[i - 1])) {
        out += ch;
        i++;
        continue;
      }
      const rangeMatch = value.slice(i + 1).match(/^\{(\d+(?:,\d*)?)\}/);
      if (rangeMatch) {
        out += `${letter}{${rangeMatch[1]}}`;
        i += 1 + rangeMatch[0].length;
        continue;
      }
      let run = 1;
      while (i + run < value.length && value[i + run] === "?") run++;
      out += `${letter}{${run}}`;
      i += run;
      continue;
    }
    if (ch === "*") {
      // Regex quantifier after a group or class — pass through
      if (i > 0 && ")]}".includes(value[i - 1])) {
        out += ch;
        i++;
        continue;
      }
      const nextIsStar = i + 1 < value.length && value[i + 1] === "*";
      if (nextIsStar) {
        out += `${letter}{2,}`;
        i += 2;
      } else {
        out += `${letter}+`;
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
    // No escapamos metacaracteres de regex para respetar {}()[]| ya presentes
    if ("[](){}|".includes(ch)) {
      out += ch;
      i++;
      continue;
    }
    // ^ as negation inside a character class [^...]
    if (ch === "^" && i > 0 && value[i - 1] === "[") {
      out += ch;
      i++;
      continue;
    }
    out += escapeRegexCharacter(ch);
    i++;
  }
  return out;
}

function splitTopLevel(str, delimiter) {
  const parts = [];
  let buf = "";
  let depth = 0;
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
  return parts.map(p => p.replace(/\\\|/g, "|").trim()).filter(Boolean);
}

function buildContainsBoth(text) {
  if (!text.startsWith("(") || !text.endsWith(")")) return null;
  const inner = text.slice(1, -1);
  if (!inner.includes("||")) return null;
  const parts = splitTopLevel(inner, "||");
  if (parts.length < 2) return null;
  const lookaheads = parts.map(p => {
    const body = convertWildcardPatternAllowRegex(expandVCPlaceholders(p));
    return `(?=.*${body})`;
  });
  return `${lookaheads.join("")}.*`;
}

function createWildcardRegex(value, mode) {
  if (!value) return null;
  const body = convertWildcardPattern(value);
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
