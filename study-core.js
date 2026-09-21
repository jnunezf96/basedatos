// Shared Study semantics for the page and isolated static worker.
// decodeStudyEntities and getDisplayValue are supplied by each environment.

const STUDY_ENTITY_PATTERN = /&(?:#(?:[xX][0-9A-Fa-f]+|[0-9]+);?|[A-Za-z][A-Za-z0-9]*;?)/g;

function cleanStudyText(value) {
  return collapseWhitespace(decodeStudyEntities(stripHtmlTags(String(value ?? ""))))
    .replace(/\s+([,.;:!?])/g, "$1")
    .trim();
}

function getStudyTranslation(row) {
  return cleanStudyText(getDisplayValue(row, "Traducción"));
}

const STUDY_LEAK_PLACEHOLDER = "[...]";
const STUDY_PROMPT_NOISE_WORDS = new Set([
  "a", "al", "b", "c", "cf", "cfr", "de", "del", "du", "el", "en", "eventual",
  "eventuel", "forma", "forme", "la", "le", "les", "los", "plur", "plural",
  "metafora", "metaforico", "metaphore", "metaphor", "posible", "possible",
  "parentesco", "parente", "posee", "poseida", "possedee", "see", "sobre",
  "sur", "un", "una", "une", "v", "ver", "voir"
]);


const studyThemeRowMetaCache = new WeakMap();
const studyCardInfoCache = new WeakMap();
const STUDY_THEME_FUNCTION_TERMS = new Set([
  "a", "al", "ante", "bajo", "cabe", "con", "contra", "de", "del", "desde",
  "durante", "e", "el", "en", "entre", "hacia", "hasta", "la", "las", "lo",
  "los", "mediante", "ni", "o", "para", "por", "que", "segun", "sin", "so",
  "sobre", "tras", "u", "un", "una", "unas", "unos", "versus", "via", "y",
  "abajo", "arriba", "dentro", "debajo", "encima", "fuera", "junto",
  "adelante", "atras", "cerca", "lejos", "ahi", "alli", "aqui", "alla",
  "aca", "donde", "cuando", "como", "cual", "quien",
  "ipan", "icpac", "itic", "itech", "ixpan", "nahuac", "nepantla", "pan",
  "tloc", "tlampa"
]);

function getStudyLeakKey(value) {
  return normalizeString(cleanStudyText(value))
    .replace(/[\u00b7'’ʼ`´-]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, "");
}

function addStudyLeakForm(forms, key) {
  if (key.length >= 4) forms.add(key);
}

function addStudyLeakDerivedForms(forms, key) {
  if (key.endsWith("hua") && key.length > 5) addStudyLeakForm(forms, `${key.slice(0, -3)}uh`);
  if (key.endsWith("ia") && key.length > 4) addStudyLeakForm(forms, `${key.slice(0, -1)}h`);
  if (key.endsWith("oa") && key.length > 4) addStudyLeakForm(forms, `${key.slice(0, -1)}h`);
}

function addStudyLeakBaseForms(forms, key) {
  [
    "liztica", "cayotl", "liztli", "yotl", "tli", "lli", "tin", "meh",
    "huan", "tl", "li", "in", "yo"
  ].forEach(suffix => {
    if (!key.endsWith(suffix) || key.length <= suffix.length + 3) return;
    const base = key.slice(0, -suffix.length);
    addStudyLeakForm(forms, base);
    addStudyLeakDerivedForms(forms, base);
  });
}

function getStudyLeakForms(lemma) {
  const forms = new Set();
  const cleaned = cleanStudyText(lemma);
  const full = getStudyLeakKey(cleaned);
  addStudyLeakForm(forms, full);
  addStudyLeakDerivedForms(forms, full);
  addStudyLeakBaseForms(forms, full);
  cleaned.split(/[^\p{L}\p{N}\u00b7'’ʼ`´-]+/u).forEach(part => {
    const key = getStudyLeakKey(part);
    addStudyLeakForm(forms, key);
    addStudyLeakDerivedForms(forms, key);
    addStudyLeakBaseForms(forms, key);
  });
  return forms;
}

function getCommonPrefixLength(a, b) {
  const max = Math.min(a.length, b.length);
  let i = 0;
  while (i < max && a[i] === b[i]) i += 1;
  return i;
}

function getStudyComparableLeakKeys(key) {
  const keys = new Set([key]);
  const hless = key.replace(/h/g, "");
  if (hless.length >= 4) keys.add(hless);
  const quAsC = key.replace(/qu/g, "c");
  if (quAsC.length >= 4) keys.add(quAsC);
  const quAsCHless = quAsC.replace(/h/g, "");
  if (quAsCHless.length >= 4) keys.add(quAsCHless);
  return keys;
}

function isStudyLeakyKeyPair(key, form, options = {}) {
  const allowContains = options.allowContains !== false;
    if (key === form) return true;
    if (allowContains && form.length >= 5 && key.length >= 5 && (key.includes(form) || form.includes(key))) return true;
    const min = Math.min(key.length, form.length);
    const prefixLength = getCommonPrefixLength(key, form);
    if (min >= 5 && Math.abs(key.length - form.length) <= 2 && prefixLength >= 5) return true;
    const finalPair = `${key[key.length - 1] || ""}${form[form.length - 1] || ""}`;
    if (min >= 5 && key.length === form.length && prefixLength >= min - 1 && (finalPair === "ah" || finalPair === "ha")) {
      return true;
    }
  return false;
}

function isStudyLeakyKey(key, forms) {
  if (key.length < 4) return false;
  const keyVariants = getStudyComparableLeakKeys(key);
  for (const form of forms) {
    const formVariants = getStudyComparableLeakKeys(form);
    for (const keyVariant of keyVariants) {
      for (const formVariant of formVariants) {
        if (isStudyLeakyKeyPair(keyVariant, formVariant)) return true;
      }
    }
  }
  return false;
}

function isStudyLeakyCombinedKey(key, forms) {
  if (key.length < 4) return false;
  const keyVariants = getStudyComparableLeakKeys(key);
  for (const form of forms) {
    const formVariants = getStudyComparableLeakKeys(form);
    for (const keyVariant of keyVariants) {
      for (const formVariant of formVariants) {
        if (isStudyLeakyKeyPair(keyVariant, formVariant, { allowContains: false })) return true;
      }
    }
  }
  return false;
}

function getStudyMaskableTokens(text) {
  const tokens = [];
  const pattern = /[\p{L}\p{M}\u00b7'’ʼ`´-]+/gu;
  let match;
  while ((match = pattern.exec(text))) {
    tokens.push({
      start: match.index,
      end: match.index + match[0].length,
      key: getStudyLeakKey(match[0])
    });
  }
  return tokens;
}

function maskStudyTranslationLeaks(translation, lemma) {
  const forms = getStudyLeakForms(lemma);
  const text = cleanStudyText(translation);
  if (!forms.size || !text) return text;
  const tokens = getStudyMaskableTokens(text);
  const masked = tokens.map(token => isStudyLeakyKey(token.key, forms));
  for (let i = 0; i < tokens.length; i += 1) {
    let combined = tokens[i].key;
    for (let j = i + 1; j < Math.min(tokens.length, i + 4); j += 1) {
      combined += tokens[j].key;
      if (isStudyLeakyCombinedKey(combined, forms)) {
        for (let k = i; k <= j; k += 1) masked[k] = true;
      }
    }
  }
  let out = "";
  let cursor = 0;
  tokens.forEach((token, index) => {
    out += text.slice(cursor, token.start);
    out += masked[index] ? STUDY_LEAK_PLACEHOLDER : text.slice(token.start, token.end);
    cursor = token.end;
  });
  return out + text.slice(cursor);
}

function isStudyPromptMetaSegment(segment) {
  const normalized = normalizeString(cleanStudyText(segment)).trim();
  if (!normalized) return true;
  if (/^(?:Cf\.?|Cfr\.?|cf\.?|cfr\.?|Ver|Voir|See)\b/.test(cleanStudyText(segment))) return true;
  if (/^(?:[bc]|variante|variant)\.?\s*~/i.test(cleanStudyText(segment))) return true;
  return [
    /^(?:(?:solo|solamente|unicamente)\s+)?(?:la\s+forma|(?:a|en|con)\s+(?:la\s+)?forma)\s+poseida\b/,
    /^(?:seulement\s+)?(?:la\s+forme|(?:a|en|avec)\s+(?:la\s+)?forme)\s+possedee\b/,
    /^forme possedee\b/,
    /^en composicion con\b/,
    /^en composition avec\b/,
    /^metaf(?:ora|orico|oricamente)?[.,;:]*$/,
    /^metaph(?:ore|orique|oriquement)?[.,;:]*$/
  ].some(pattern => pattern.test(normalized));
}

function cleanStudyPromptTranslation(translation) {
  const text = cleanStudyText(translation);
  if (!text) return "";
  const segments = text.split(/\s*\/\s*/).map(part => part.trim()).filter(Boolean);
  if (!segments.length) return "";
  const kept = segments.filter(segment => !isStudyPromptMetaSegment(segment));
  return kept.join(" / ");
}

function stripStudyPromptCitation(text) {
  return cleanStudyText(text)
    .replace(/\s*(?:;\s*)?(?:Sah|Sa)\s*\d+\s*,\s*\d+(?:\s*=\s*.+?)?\.?\s*$/i, "")
    .trim();
}

function normalizeStudyPromptMarker(text) {
  return cleanStudyText(text)
    .replace(/\b(met[aá]fora|m[eé]taphor(?:e)?|metaphor)\s*(?:\.,?|[.,:])\s*/gi, "$1: ")
    .replace(/\b(metaf[oó]rico|metaf[oó]ricamente)\s*(?:\.,?|[.,:])\s*/gi, "$1: ")
    .replace(/\b(parentesco|parent[eé])\s*(?:\.,?|[.,:])\s*/gi, "$1: ")
    .replace(/\b(?:plural|plur)\s*(?:\.,?|[.,:])\s*/gi, "plural: ");
}

function removeStudyPromptLeakPlaceholders(text) {
  return cleanStudyText(text)
    .replace(/\s*\[\.\.\.\]\s*/g, " ")
    .replace(/\s+([,.;:!?])/g, "$1")
    .replace(/([,;:])\s*(?:[,;:]\s*)+/g, "$1 ")
    .replace(/([.;:])\s*,\s*/g, "$1 ")
    .replace(/,\s*([.;:!?])/g, "$1")
    .replace(/\s+/g, " ")
    .replace(/,\s*$/, "")
    .trim();
}

function cleanMaskedStudyPromptSegment(segment) {
  const withoutCitation = stripStudyPromptCitation(segment);
  if (isStudyPromptMetaSegment(withoutCitation)) return "";
  if (!withoutCitation.includes(STUDY_LEAK_PLACEHOLDER)) {
    return normalizeStudyPromptMarker(withoutCitation);
  }
  let unmasked = removeStudyPromptLeakPlaceholders(withoutCitation);
  if (/^(?:plural|plur)\b/i.test(normalizeString(unmasked))) {
    unmasked = unmasked.replace(/\bhonor\.\s*/gi, "");
  }
  const cleaned = normalizeStudyPromptMarker(unmasked);
  return isStudyPromptUsable(cleaned) ? cleaned : "";
}

function cleanMaskedStudyPrompt(text) {
  const segments = cleanStudyText(text).split(/\s*\/\s*/).map(part => part.trim()).filter(Boolean);
  return segments
    .map(cleanMaskedStudyPromptSegment)
    .filter(Boolean)
    .join(" / ");
}

function isStudyPromptUsable(text) {
  if (/^(?:Cf\.?|Cfr\.?|cf\.?|cfr\.?|Ver|Voir|See)\b/.test(cleanStudyText(text))) return false;
  const normalized = normalizeString(cleanStudyText(text).split(STUDY_LEAK_PLACEHOLDER).join(" "))
    .replace(/[^\p{L}\p{N}\s]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (!normalized) return false;
  return normalized.split(/\s+/).some(word => word.length >= 4 && !STUDY_PROMPT_NOISE_WORDS.has(word));
}

function getStudyCardTranslation(row, lemma, direction) {
  const translation = getStudyTranslation(row);
  if (!translation) return "";
  if (direction !== "spanishToNahuatl") return translation;
  const promptTranslation = cleanStudyPromptTranslation(translation);
  if (!promptTranslation) return "";
  const masked = cleanMaskedStudyPrompt(maskStudyTranslationLeaks(promptTranslation, lemma));
  return isStudyPromptUsable(masked) ? masked : "";
}


function getStudyThemeTextIndex(value) {
  const text = normalizeString(cleanStudyText(value));
  return {
    text,
    tokens: new Set(text.split(/[^\p{L}\p{N}]+/u).filter(Boolean))
  };
}

function isStudyThemeTermAllowed(term) {
  if (!term) return false;
  if (STUDY_THEME_FUNCTION_TERMS.has(term)) return false;
  return term.length > 1 || /\s/.test(term);
}

function getStudyThemeTerms(theme) {
  if (!theme._normalizedTerms) {
    theme._normalizedTerms = theme.terms
      .map(term => normalizeString(cleanStudyText(term)).trim())
      .filter(Boolean)
      .filter(isStudyThemeTermAllowed)
      .map(term => ({
        term,
        exact: !term.includes(" ") && term.length <= 4
      }));
  }
  return theme._normalizedTerms;
}

function studyThemeTermMatchesIndex(termSpec, index) {
  return termSpec.exact ? index.tokens.has(termSpec.term) : index.text.includes(termSpec.term);
}

function studyThemeMatchesIndex(theme, index) {
  return getStudyThemeTerms(theme).some(term => studyThemeTermMatchesIndex(term, index));
}

function getStudyRowThemeMeta(row) {
  const lemmaValue = getDisplayValue(row, "Editado");
  const translationValue = getDisplayValue(row, "Traducción");
  const cached = studyThemeRowMetaCache.get(row);
  if (cached && cached.lemmaValue === lemmaValue && cached.translationValue === translationValue) {
    return cached;
  }
  const meta = {
    lemmaValue,
    translationValue,
    lemmaKey: normalizeString(cleanStudyText(lemmaValue)),
    translation: cleanStudyText(translationValue)
  };
  studyThemeRowMetaCache.set(row, meta);
  return meta;
}

function groupStudyRowsByLemma(rows) {
  const groups = new Map();
  rows.forEach(row => {
    const meta = getStudyRowThemeMeta(row);
    const key = meta.lemmaKey;
    if (!key) return;
    let group = groups.get(key);
    if (!group) {
      group = { key, rows: [], translationText: "" };
      groups.set(key, group);
    }
    group.rows.push(row);
    if (meta.translation) group.translationText += ` ${meta.translation}`;
  });
  return [...groups.values()];
}

function getStudyRowsForThemeByLemma(rows, theme) {
  const selectedRows = [];
  groupStudyRowsByLemma(rows).forEach(group => {
    const index = getStudyThemeTextIndex(group.translationText);
    if (studyThemeMatchesIndex(theme, index)) selectedRows.push(...group.rows);
  });
  return selectedRows;
}

function addStudyTranslation(entry, translation) {
  const normalized = normalizeString(translation);
  if (!normalized) return;
  const existing = entry.translationStats.get(normalized);
  if (existing) existing.count += 1;
  else entry.translationStats.set(normalized, { display: translation, count: 1, normalized, length: translation.length });
}

function getStudyCardInfo(row, direction, cache) {
  const targetCache = cache || studyCardInfoCache;
  const lemmaValue = getDisplayValue(row, "Editado");
  const translationValue = getDisplayValue(row, "Traducción");
  const cached = targetCache.get(row);
  const cachedMatches = cached
    && cached.lemmaValue === lemmaValue
    && cached.translationValue === translationValue;
  if (cachedMatches && cached.byDirection.has(direction)) {
    return cached.byDirection.get(direction);
  }
  const lemma = cleanStudyText(lemmaValue);
  const key = normalizeString(lemma);
  const translation = lemma ? getStudyCardTranslation(row, lemma, direction) : "";
  const info = lemma && key && translation ? { lemma, key, translation } : null;
  const bucket = cachedMatches ? cached : { lemmaValue, translationValue, byDirection: new Map() };
  bucket.byDirection.set(direction, info);
  targetCache.set(row, bucket);
  return info;
}

function selectStudyDeckLemmaKeys(rows, direction, limit, cache) {
  const seen = new Set();
  const sample = [];
  if (!limit) return new Set();
  rows.forEach(row => {
    const info = getStudyCardInfo(row, direction, cache);
    if (!info || seen.has(info.key)) return;
    seen.add(info.key);
    if (sample.length < limit) sample.push(info.key);
    else {
      const slot = Math.floor(Math.random() * seen.size);
      if (slot < limit) sample[slot] = info.key;
    }
  });
  return new Set(sample);
}

function buildStudyCardsFromRows(rows, options = {}) {
  const direction = options.direction || "nahuatlToSpanish";
  const limit = Number.isFinite(options.limit) && options.limit > 0 ? Math.floor(options.limit) : 0;
  const selectedKeys = limit ? selectStudyDeckLemmaKeys(rows, direction, limit, studyCardInfoCache) : null;
  const byLemma = new Map();

  rows.forEach(row => {
    const lemma = cleanStudyText(getDisplayValue(row, "Editado"));
    const key = normalizeString(lemma);
    if (!lemma || !key) return;
    if (selectedKeys && !selectedKeys.has(key)) return;
    const info = getStudyCardInfo(row, direction, studyCardInfoCache);
    if (!info) return;
    const { translation } = info;
    let entry = byLemma.get(key);
    if (!entry) {
      entry = {
        lemma,
        rows: 0,
        sources: new Set(),
        translationStats: new Map()
      };
      byLemma.set(key, entry);
    }
    entry.rows += 1;
    if (row.Fuente) entry.sources.add(row.Fuente);
    addStudyTranslation(entry, translation);
  });

  return [...byLemma.values()]
    .map(entry => {
      const translations = [...entry.translationStats.values()]
        .sort((a, b) => {
          const qualityA = getStudyTranslationLengthBucket(a.length);
          const qualityB = getStudyTranslationLengthBucket(b.length);
          if (qualityA !== qualityB) return qualityA - qualityB;
          if (b.count !== a.count) return b.count - a.count;
          if (a.length !== b.length) return a.length - b.length;
          return alphaNumCollator.compare(a.normalized, b.normalized);
        })
        .slice(0, 3)
        .map(item => item.display);
      if (!translations.length) return null;
      const translation = translations.join("; ");
      const nahuatlToSpanish = direction !== "spanishToNahuatl";
      return {
        lemma: entry.lemma,
        translation,
        front: nahuatlToSpanish ? entry.lemma : translation,
        back: nahuatlToSpanish ? translation : entry.lemma,
        frontLabelKey: nahuatlToSpanish ? "study.front.edition" : "study.front.translation",
        backLabelKey: nahuatlToSpanish ? "study.front.translation" : "study.front.edition",
        sourceCount: entry.sources.size,
        rowCount: entry.rows
      };
    })
    .filter(Boolean);
}

function getStudyTranslationLengthBucket(length) {
  if (length <= 180) return 0;
  if (length <= 280) return 1;
  return 2;
}

function countStudyPossibleCardsFromRows(rows, options = {}) {
  const direction = options.direction || getStudyDirection();
  const seen = new Set();
  rows.forEach(row => {
    const info = getStudyCardInfo(row, direction, studyCardInfoCache);
    if (info) seen.add(info.key);
  });
  return seen.size;
}

function shuffleStudyCards(cards) {
  for (let i = cards.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [cards[i], cards[j]] = [cards[j], cards[i]];
  }
  return cards;
}
