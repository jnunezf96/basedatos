const COMENTARIO_CONTROL_WIDTH = 44;
const COMENTARIO_ROW_PRESS_DELAY_MS = 220;
const FIXED_CONTROL_COLUMNS = new Set(["Comentario"]);

const TABLE_FIELDS = [
  { key: "Texto estandarizado", label: "Edición", defaultWidth: 108 },
  { key: "Escritura original", label: "Original", defaultWidth: 108 },
  { key: "Traducción", label: "Traducción", defaultWidth: 220 },
  { key: "Fuente", label: "Fuente", defaultWidth: 96 },
  { key: "Comentario", label: "Comentario", defaultWidth: COMENTARIO_CONTROL_WIDTH }
];
const DEFAULT_COLUMN_ORDER = TABLE_FIELDS.map(field => field.key);
const COLUMN_CONTROL_ORDER = DEFAULT_COLUMN_ORDER.slice();
const DEFAULT_COLUMN_WIDTHS = new Map(TABLE_FIELDS.map(field => [field.key, field.defaultWidth]));
const TABLE_MIN_WIDTH = 908;
const APP_ASSET_VERSION = (() => {
  try {
    const src = document.currentScript?.src || "";
    return src ? new URL(src, location.href).searchParams.get("v") || "dev" : "dev";
  } catch {
    return "dev";
  }
})();

function versionedAssetUrl(path) {
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}v=${encodeURIComponent(APP_ASSET_VERSION)}`;
}

const I18N = {
  es: {
    title: "Base de datos náhuatl",
    subtitle: "Filtra y explora cinco columnas con filtros rápidos y mini‑lenguaje.",
    "tab.filters": "Filtros",
    "tab.sources": "Fuentes",
    "tab.regex": "Regex",
    "tab.pairs": "Pares a/i",
    "tab.study": "Tarjetas",
    "reverse.title": "Filtros guiados",
    "reverse.hint": "Elige una relación: en qué columna buscas y qué columna quieres ver como resultado.",
    "reverse.submit": "Buscar",
    "reverse.apply": "Aplicar filtro",
    "reverse.includeComment": "Incluir Comentario",
    "reverse.inputLabel": "Texto para el objetivo",
    "reverse.presets": "Relaciones entre columnas:",
    "reverse.preset.meaning": "Cómo se dice una idea",
    "reverse.preset.meaningGoal": "Encuentra palabras cuya traducción expresa ese concepto.",
    "reverse.preset.exactMeaning": "Qué entrada significa justo esto",
    "reverse.preset.exactMeaningGoal": "Reduce a una coincidencia de significado más cerrada.",
    "reverse.preset.phraseMeaning": "Qué expresa una frase",
    "reverse.preset.phraseMeaningGoal": "Busca una definición o frase completa en traducciones.",
    "reverse.preset.nahuatlExact": "Dónde aparece esta palabra náhuatl",
    "reverse.preset.nahuatlExactGoal": "Confirma una forma normalizada exacta.",
    "reverse.preset.nahuatlStarts": "Qué palabra estoy recordando",
    "reverse.preset.nahuatlStartsGoal": "Recupera lemas cuando solo sabes el inicio.",
    "reverse.preset.oldSpelling": "Qué es esta grafía antigua",
    "reverse.preset.oldSpellingGoal": "Conecta escritura original con edición normalizada.",
    "reverse.preset.notesMention": "Qué notas hablan de este tema",
    "reverse.preset.notesMentionGoal": "Explora comentarios y observaciones editoriales.",
    "reverse.preset.qAbbrev": "Abreviaturas q^",
    "reverse.preset.qAbbrevGoal": "171 filas con abreviatura paleográfica.",
    "reverse.preset.questionOriginal": "Lecturas con ?",
    "reverse.preset.questionOriginalGoal": "482 filas con incertidumbre en la forma.",
    "reverse.preset.bracedOriginal": "Lecturas { }",
    "reverse.preset.bracedOriginalGoal": "408 filas con alternancias preservadas.",
    "reverse.preset.bnfAdditions": "Añadidos BNF 361",
    "reverse.preset.bnfAdditionsGoal": "61 filas de capas manuscritas.",
    "reverse.preset.rareUse": "Usos raros C&Z",
    "reverse.preset.rareUseGoal": "38 filas marcadas como raras.",
    "reverse.preset.uncertainNotes": "Notas dudosas",
    "reverse.preset.uncertainNotesGoal": "≈1.7k filas con probabilidad o duda.",
    "reverse.preset.slashOriginal": "Con /",
    "reverse.preset.slashOriginalGoal": "307 filas con variantes o segmentos editoriales.",
    "reverse.preset.sectionSign": "Grafía §",
    "reverse.preset.sectionSignGoal": "492 filas con transcripción paleográfica especial.",
    "reverse.preset.phSpelling": "Grafía ph",
    "reverse.preset.phSpellingGoal": "17 filas con grafía colonial o culta.",
    "reverse.preset.jForms": "Formas con j",
    "reverse.preset.jFormsGoal": "144 filas con préstamos, nombres o grafías modernas.",
    "reverse.preset.v94Types": "Tipos V94",
    "reverse.preset.v94TypesGoal": "12 filas con metadatos raros de tipo gramatical.",
    "reverse.preset.greekLatinNotes": "Griego/latín",
    "reverse.preset.greekLatinNotesGoal": "99 filas con notas de lengua clásica.",
    "reverse.preset.editorialInterventions": "Intervenciones",
    "reverse.preset.editorialInterventionsGoal": "782 filas con sic, tachado, borrado o interlineado.",
    "reverse.preset.variantLabels": "Variantes",
    "reverse.preset.variantLabelsGoal": "≈1.2k filas que nombran variantes explícitas.",
    "reverse.preset.reduplicatedRoot": "Reduplicación",
    "reverse.preset.reduplicatedRootGoal": "Busca una raíz con el patrón +raíz.",
    "reverse.preset.sameWordPieces": "Dos piezas",
    "reverse.preset.sameWordPiecesGoal": "Busca dos partes dentro de la misma palabra.",
    "reverse.preset.translationToEdition": "Traducción → Edición",
    "reverse.preset.translationToEditionGoal": "Busca en Traducción; muestra lemas de Edición.",
    "reverse.preset.translationToOriginal": "Traducción → Original",
    "reverse.preset.translationToOriginalGoal": "Busca en Traducción; muestra grafías originales.",
    "reverse.preset.translationPhraseToEdition": "Frase → Edición",
    "reverse.preset.translationPhraseToEditionGoal": "Busca una frase completa en Traducción.",
    "reverse.preset.editionToTranslation": "Edición → Traducción",
    "reverse.preset.editionToTranslationGoal": "Busca en Edición; muestra Traducción.",
    "reverse.preset.editionToOriginal": "Edición → Original",
    "reverse.preset.editionToOriginalGoal": "Busca en Edición; muestra Original.",
    "reverse.preset.originalToEdition": "Original → Edición",
    "reverse.preset.originalToEditionGoal": "Busca en Original; muestra lemas de Edición.",
    "reverse.preset.originalToTranslation": "Original → Traducción",
    "reverse.preset.originalToTranslationGoal": "Busca en Original; muestra Traducción.",
    "reverse.preset.commentToEdition": "Comentario → Edición",
    "reverse.preset.commentToEditionGoal": "Busca en Comentario; muestra lemas de Edición.",
    "reverse.preset.editionToSources": "Edición → Fuentes",
    "reverse.preset.editionToSourcesGoal": "Busca en Edición; muestra Fuente.",
    "reverse.preset.translationToSources": "Traducción → Fuentes",
    "reverse.preset.translationToSourcesGoal": "Busca en Traducción; muestra Fuente.",
    "reverse.preset.sourceToEdition": "Fuente → Edición",
    "reverse.preset.sourceToEditionGoal": "Busca en Fuente; muestra lemas de Edición.",
    "reverse.preset.sourceToTranslation": "Fuente → Traducción",
    "reverse.preset.sourceToTranslationGoal": "Busca en Fuente; muestra Traducción.",
    "reverse.preset.commentToSources": "Comentario → Fuente",
    "reverse.preset.commentToSourcesGoal": "Busca en Comentario; muestra Fuente.",
    "reverse.objective.meaning": "Objetivo: partir de una idea en traducción y ver qué palabras náhuatl la cubren.",
    "reverse.objective.exactMeaning": "Objetivo: aislar entradas donde el significado aparece como una coincidencia exacta.",
    "reverse.objective.phraseMeaning": "Objetivo: encontrar entradas que expresan una frase, definición o explicación completa.",
    "reverse.objective.nahuatlExact": "Objetivo: confirmar una forma náhuatl normalizada y revisar sus fuentes.",
    "reverse.objective.nahuatlStarts": "Objetivo: recuperar posibles lemas cuando solo recuerdas el comienzo.",
    "reverse.objective.oldSpelling": "Objetivo: identificar la edición normalizada detrás de una grafía original o antigua.",
    "reverse.objective.notesMention": "Objetivo: encontrar comentarios, notas o fuentes que mencionan el tema.",
    "reverse.objective.qAbbrev": "Objetivo: expandir abreviaturas q^ en escritura original y compararlas con la edición normalizada (171 filas).",
    "reverse.objective.questionOriginal": "Objetivo: revisar lecturas con signo ? en la escritura original, normalmente incertidumbre paleográfica (482 filas).",
    "reverse.objective.bracedOriginal": "Objetivo: revisar lecturas alternativas entre llaves en la escritura original (408 filas).",
    "reverse.objective.bnfAdditions": "Objetivo: ver añadidos, interlineados o notas de mano en BNF 361; combina Fuente + Comentario (61 filas).",
    "reverse.objective.rareUse": "Objetivo: aislar notas de uso raro en Cortés y Zedeño; combina Fuente + Comentario (38 filas).",
    "reverse.objective.uncertainNotes": "Objetivo: encontrar comentarios donde el editor marca duda, probabilidad o incertidumbre (≈1.7k filas).",
    "reverse.objective.slashOriginal": "Objetivo: revisar formas con / en escritura original, normalmente variantes, alternativas o segmentación editorial (307 filas).",
    "reverse.objective.sectionSign": "Objetivo: revisar transcripciones con § en escritura original, una marca paleográfica especial (492 filas).",
    "reverse.objective.phSpelling": "Objetivo: aislar grafías coloniales o cultas con ph en escritura original (17 filas).",
    "reverse.objective.jForms": "Objetivo: encontrar formas normalizadas con j, útiles para préstamos, nombres y grafías modernas (144 filas).",
    "reverse.objective.v94Types": "Objetivo: encontrar metadatos gramaticales raros en V94, como prefijo, sufijo, artículo o vocativo (12 filas).",
    "reverse.objective.greekLatinNotes": "Objetivo: encontrar comentarios que citan griego o latín como estructura de nota lexicográfica (99 filas).",
    "reverse.objective.editorialInterventions": "Objetivo: encontrar comentarios con intervenciones editoriales como sic, tachado, borrado, añadido o interlineado (782 filas).",
    "reverse.objective.variantLabels": "Objetivo: revisar comentarios que etiquetan variantes explícitamente (≈1.2k filas).",
    "reverse.objective.reduplicatedRoot": "Objetivo: buscar una raíz reduplicada usando el mini-lenguaje; escribe la raíz base y el filtro usará +raíz.",
    "reverse.objective.sameWordPieces": "Objetivo: buscar palabras que contienen dos piezas a la vez; escribe algo como teo||tlatol.",
    "reverse.objective.translationToEdition": "Relación: escribe una palabra que aparece en Traducción; la tabla presenta todos los lemas de Edición asociados.",
    "reverse.objective.translationToOriginal": "Relación: escribe una palabra que aparece en Traducción; la tabla presenta las grafías de Original asociadas.",
    "reverse.objective.translationPhraseToEdition": "Relación: busca una frase en Traducción y presenta los lemas de Edición vinculados a esa frase.",
    "reverse.objective.editionToTranslation": "Relación: escribe un lema de Edición; la tabla presenta sus traducciones documentadas.",
    "reverse.objective.editionToOriginal": "Relación: escribe un lema de Edición; la tabla presenta las grafías originales que lo registran.",
    "reverse.objective.originalToEdition": "Relación: escribe una grafía de Original; la tabla presenta la Edición normalizada correspondiente.",
    "reverse.objective.originalToTranslation": "Relación: escribe una grafía de Original; la tabla presenta las traducciones asociadas.",
    "reverse.objective.commentToEdition": "Relación: escribe un tema en Comentario; la tabla presenta los lemas de Edición conectados con esa nota.",
    "reverse.objective.editionToSources": "Relación: escribe un lema de Edición; la tabla presenta las fuentes que lo atestiguan.",
    "reverse.objective.translationToSources": "Relación: escribe una palabra de Traducción; la tabla presenta las fuentes que contienen ese significado.",
    "reverse.objective.sourceToEdition": "Relación: escribe una fuente o parte de su nombre; la tabla presenta los lemas de Edición en esa fuente.",
    "reverse.objective.sourceToTranslation": "Relación: escribe una fuente o parte de su nombre; la tabla presenta traducciones y lemas de esa fuente.",
    "reverse.objective.commentToSources": "Relación: escribe un tema en Comentario; la tabla presenta las fuentes donde aparece esa nota.",
    "reverse.placeholder.meaning": "Escribe la idea, ej. agua",
    "reverse.placeholder.exactMeaning": "Escribe el significado exacto",
    "reverse.placeholder.phraseMeaning": "Escribe la frase o definición",
    "reverse.placeholder.nahuatlExact": "Escribe la palabra náhuatl",
    "reverse.placeholder.nahuatlStarts": "Escribe el inicio que recuerdas",
    "reverse.placeholder.oldSpelling": "Escribe la grafía antigua",
    "reverse.placeholder.notesMention": "Escribe el tema o palabra de la nota",
    "reverse.placeholder.reduplicatedRoot": "Escribe la raíz, ej. tzitz",
    "reverse.placeholder.sameWordPieces": "Escribe piezas, ej. teo||tlatol",
    "reverse.placeholder.translationToEdition": "Palabra en traducción, ej. agua",
    "reverse.placeholder.translationToOriginal": "Palabra en traducción, ej. agua",
    "reverse.placeholder.translationPhraseToEdition": "Frase en traducción",
    "reverse.placeholder.editionToTranslation": "Lema en edición, ej. atl",
    "reverse.placeholder.editionToOriginal": "Lema en edición",
    "reverse.placeholder.originalToEdition": "Grafía original",
    "reverse.placeholder.originalToTranslation": "Grafía original",
    "reverse.placeholder.commentToEdition": "Tema o palabra en comentario",
    "reverse.placeholder.editionToSources": "Lema en edición",
    "reverse.placeholder.translationToSources": "Palabra en traducción",
    "reverse.placeholder.sourceToEdition": "Fuente o abreviatura, ej. Molina",
    "reverse.placeholder.sourceToTranslation": "Fuente o abreviatura, ej. Molina",
    "reverse.placeholder.commentToSources": "Tema o palabra en comentario",
    "tab.compare": "Comparar lema",
    "tab.browse": "Relaciones",
    "filter.title": "Filtro",
    "filter.help": "Ayuda de filtros",
    "label.column": "Columna",
    "label.scope": "Alcance",
    "scope.whole": "Casilla",
    "scope.word": "Palabra",
    "scope.phrase": "Frase",
    "field.grafia.short": "edición",
    "field.paleografia.short": "original",
    "field.traduccion.short": "traducción",
    "field.comentario.short": "comentario",
    "grid.include": "Incluye",
    "grid.exclude": "Excluye",
    "grid.side.toggle": "Cambiar entre incluye y excluye",
    "grid.exact": "Exacto",
    "grid.starts": "Empieza",
    "grid.contains": "Contiene",
    "grid.ends": "Termina",
    "action.run": "Ejecutar",
    "action.clear": "Vaciar",
    "nav.search": "Buscar",
    "nav.chips": "Aplicados",
    "nav.results": "Resultados",
    "chips.empty": "Ningún filtro aplicado todavía.",
    "placeholder.exact.incl": "es exactamente...",
    "placeholder.exact.excl": "no es exactamente...",
    "placeholder.starts.incl": "empieza con...",
    "placeholder.starts.excl": "no empieza con...",
    "placeholder.any.incl": "contiene...",
    "placeholder.any.excl": "no contiene...",
    "placeholder.ends.incl": "termina con...",
    "placeholder.ends.excl": "no termina con...",
    "sources.title": "Fuentes",
    "sources.selection": "Selección",
    "sources.sort": "Orden",
    "sources.fill": "Todas",
    "sources.clear": "Ninguna",
    "sources.orderAlpha": "Ordenar fuentes A-Z",
    "sources.orderAlpha.short": "A-Z",
    "sources.orderYear": "Ordenar fuentes por año",
    "sources.orderYear.short": "Año",
    "regex.title": "Mini-lenguaje",
    "rx.wildcards": "Comodines",
    "rx.q1": "1 grafema cualquiera",
    "rx.q2": "exactamente 2 grafemas",
    "rx.star1": "1 o más grafemas",
    "rx.star2": "2 o más grafemas",
    "rx.range": "2 a 4 grafemas",
    "rx.optional.any": "grafema opcional",
    "rx.optional.literal": "h opcional",
    "rx.grapheme.note": "En Edición, Original y Comentario, ? cuenta ch/tz/qu/etc. como un grafema",
    "rx.alternatives": "Alternativas",
    "rx.alt.group": "pato <em>o</em> pata",
    "rx.alt.pipe": "equivalente (nivel superior)",
    "rx.alt.escape": "barra literal",
    "rx.escape.meta": "signos literales",
    "rx.alt.wildcard.after": "c/qu + grafemas",
    "rx.phrase.exact": "frase exacta",
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
    "rx.negclass": "Clase negada",
    "rx.negclass.desc": "cualquier no-vocal",
    "rx.negclass.ex": "excluye vocales y s",
    "rx.cv.note": "Solo activo dentro de llaves { }",
    "rx.containsboth": "Ambas en la misma palabra",
    "rx.both.desc": "la palabra contiene <em>ambas</em>",
    "rx.both.note": "Doble barra <code>||</code> dentro de paréntesis",
    "rx.reduplication": "Reduplicación",
    "rx.redup.simple": "→ <em>papaqui</em>",
    "rx.redup.infix": "→ <em>pahpaqui</em>",
    "rx.redup.marker": "→ <em>pahpaqui</em> por patrón",
    "rx.redup.optionalH": "→ <em>papaqui</em> / <em>pahpaqui</em>",
    "rx.redup.optionalMarker": "→ <em>ahuia</em> / <em>aahuia</em>",
    "rx.redup.note": "{R} duplica el siguiente bloque; (h) permite h opcional",
    "rx.repeat.same.grapheme": "mismo grafema repetido",
    "rx.repeat.same.cv": "misma sílaba CV repetida",
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
    "study.title": "Tarjetas",
    "study.hint": "Crea un mazo desde los resultados actuales; cada tarjeta usa Edición y Traducción.",
    "study.mode": "Modo",
    "study.mode.study": "Estudio",
    "study.mode.exam": "Examen",
    "study.view": "Tarjeta",
    "study.view.flip": "2 caras",
    "study.view.both": "1 cara",
    "study.face.flip": "Voltear tarjeta",
    "study.face.next": "Siguiente tarjeta",
    "study.face.zones.flip": "Izquierda: anterior · centro: voltear · derecha: siguiente",
    "study.face.zones.next": "Izquierda: anterior · derecha: siguiente",
    "study.direction": "Dirección",
    "study.direction.nt": "Edición → Traducción",
    "study.direction.tn": "Traducción → Edición",
    "study.limit": "Cartas",
    "study.useFilters": "Usar resultados actuales",
    "study.shortOnly": "Preferir definiciones cortas",
    "study.shuffle": "Mezclar",
    "study.build": "Crear mazo",
    "study.reset": "Reiniciar",
    "study.reveal": "Mostrar",
    "study.flip": "Voltear",
    "study.next": "Siguiente",
    "study.again": "Otra vez",
    "study.hard": "Difícil",
    "study.good": "Bien",
    "study.easy": "Fácil",
    "study.empty": "Crea un mazo para empezar.",
    "study.noCards": "No hay tarjetas con lema y traducción en este alcance.",
    "study.done": "Mazo terminado.",
    "study.summary": "Resumen",
    "study.summary.results": "Resultados",
    "study.summary.primary": "Cartas iniciales: {{cards}} · Respuestas: {{answers}}",
    "study.summary.study": "Cartas estudiadas: {{seen}}",
    "study.summary.score": "Bien/Fácil: {{known}} ({{percent}}%) · Repasar: {{review}}",
    "study.summary.detail": "Otra vez: {{again}} · Difícil: {{hard}} · Bien: {{good}} · Fácil: {{easy}}",
    "study.scope": "{{rows}} filas disponibles · {{cards}} tarjetas posibles",
    "study.cardCount": "{{current}}/{{total}}",
    "study.progress.study": "{{seen}} estudiadas",
    "study.progress": "{{seen}} vistas · {{good}} bien · {{again}} repasar",
    "study.sources": "{{sources}} fuentes · {{rows}} filas",
    "study.front.edition": "Edición",
    "study.front.translation": "Traducción",
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
    "browse.meta.entries": "{{rows}} entradas",
    "browse.meta.counts": "{{sources}} fuentes · {{rows}} filas · {{translations}} traducciones",
    "browse.compare": "Aislar",
    "browse.pagesize.label": "Filas",
    "browse.page": "Pág. {{page}} de {{total}}",
    "site.tagline": "Usa los filtros para encontrar palabras por escritura, traducción o fuente; los resultados aparecen en la tabla de abajo.",
    "table.header.paleografia": "Original",
    "table.header.grafia": "Edición",
    "table.header.traduccion": "Traducción",
    "table.header.fuente": "Fuente",
    "table.header.comentario": "Comentario",
    "table.rowDetail.open": "Mostrar registro",
    "table.rowDetail.close": "Ocultar registro",
    "table.sort.label": "Orden:",
    "table.sort.all": "Todos",
    "table.sort.page": "Página",
    "table.caption": "Resultados de la base de datos náhuatl",
    "table.status.loading": "Cargando datos…",
    "table.status.error": "No se pudieron cargar los datos. Revisa la conexión y vuelve a intentar.",
    "table.status.none": "Sin registros para mostrar.",
    "table.status.showing": "Registros mostrados: {{start}}-{{end}} de {{total}}",
    "table.status.detail.auto": "{{exact}} lemas exactos · {{phrase}} frases",
    "table.status.detail.manual": "{{exact}} lemas exactos · {{phrase}} frases · Manual",
    "table.empty": "No hay datos disponibles.",
    "table.empty.filtered": "Ningún resultado coincide con los filtros activos. Prueba a quitar un filtro, ampliar las fuentes o usar acento libre.",
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
    "field.fuente": "Fuente",
    "nav.left": "Mover a la izquierda",
    "nav.right": "Mover a la derecha",
    "action.add": "Añadir",
    "action.update": "Actualizar",
    "filter.title": "Filtro",
    "lang.toggle": "English",
    "action.share": "Compartir",
    "share.copied": "Enlace copiado",
    "share.failed": "No se pudo compartir",
    "copy.cell": "Texto copiado",
    "page.first": "Primera página",
    "page.prev": "Página anterior",
    "page.next": "Página siguiente",
    "page.last": "Última página",
    "sort.by": "Ordenar por",
    "sort.asc": "ascendente",
    "sort.desc": "descendente",
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
    "chips.zone.and": "×",
    "chips.zone.or": "÷",
    "chips.clearAll": "Limpiar todo",
    "chips.removeFilter": "Quitar filtro",
    "chips.applied": "Filtros aplicados",
    "chips.scope.whole.code": "C",
    "chips.scope.word.code": "P",
    "chips.scope.phrase.code": "F",
    "comentario.expandRow": "Abrir comentario",
    "comentario.collapseRow": "Cerrar comentario",
    "session.new": "Nueva búsqueda",
    "session.close": "Cerrar búsqueda",
    "sort.childHint": "Orden dentro de cada lema",
    "toggle.expandCollapse": "Expandir/Colapsar",
    "page.current": "Página actual",
    "page.total": "de {{total}} pág.",
    "comentario.lang": "Idioma del comentario",
    "list.expandAll": "Expandir/Colapsar registros",
    "lemma.expandAll": "Expandir/Colapsar lemas",
    "comentario.expandAll": "Expandir/Colapsar comentarios",
    "table.pagesize.label": "Filas:",
    "table.pagesize.lemmasLabel": "Lemas:",
    "table.columns": "Cols ▾",
    "columns.title": "Columnas",
    "columns.reset": "Restablecer",
    "columns.show": "Mostrar",
    "columns.hide": "Ocultar",
    "columns.visible": "Visible",
    "columns.hidden": "Oculta",
    "columns.moveLeft": "Mover a la izquierda",
    "columns.moveRight": "Mover a la derecha",
    "columns.narrower": "Más estrecha",
    "columns.wider": "Más ancha",
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
    "tab.study": "Cards",
    "reverse.title": "Guided filters",
    "reverse.hint": "Choose a relationship: which column to search in, and which column to show as the result.",
    "reverse.submit": "Search",
    "reverse.apply": "Apply filter",
    "reverse.includeComment": "Include Comment",
    "reverse.inputLabel": "Text for the objective",
    "reverse.presets": "Column relationships:",
    "reverse.preset.meaning": "How to say an idea",
    "reverse.preset.meaningGoal": "Find words whose translation expresses that concept.",
    "reverse.preset.exactMeaning": "Which entry means exactly this",
    "reverse.preset.exactMeaningGoal": "Narrow to a tighter meaning match.",
    "reverse.preset.phraseMeaning": "What expresses a phrase",
    "reverse.preset.phraseMeaningGoal": "Search for a full phrase or definition in translations.",
    "reverse.preset.nahuatlExact": "Where this Nahuatl word appears",
    "reverse.preset.nahuatlExactGoal": "Confirm an exact normalized form.",
    "reverse.preset.nahuatlStarts": "Which word I am remembering",
    "reverse.preset.nahuatlStartsGoal": "Recover lemmas when you only know the beginning.",
    "reverse.preset.oldSpelling": "What this old spelling is",
    "reverse.preset.oldSpellingGoal": "Connect original spelling to normalized edition.",
    "reverse.preset.notesMention": "Which notes discuss this topic",
    "reverse.preset.notesMentionGoal": "Explore comments and editorial observations.",
    "reverse.preset.qAbbrev": "q^ abbreviations",
    "reverse.preset.qAbbrevGoal": "171 paleographic-abbreviation rows.",
    "reverse.preset.questionOriginal": "Readings with ?",
    "reverse.preset.questionOriginalGoal": "482 uncertain-form rows.",
    "reverse.preset.bracedOriginal": "Readings in { }",
    "reverse.preset.bracedOriginalGoal": "408 preserved-alternate rows.",
    "reverse.preset.bnfAdditions": "BNF 361 additions",
    "reverse.preset.bnfAdditionsGoal": "61 manuscript-layer rows.",
    "reverse.preset.rareUse": "Rare-use C&Z notes",
    "reverse.preset.rareUseGoal": "38 rows marked as rare.",
    "reverse.preset.uncertainNotes": "Uncertain notes",
    "reverse.preset.uncertainNotesGoal": "≈1.7k doubt/probability rows.",
    "reverse.preset.slashOriginal": "With /",
    "reverse.preset.slashOriginalGoal": "307 rows with variants or editorial segments.",
    "reverse.preset.sectionSign": "§ spelling",
    "reverse.preset.sectionSignGoal": "492 rows with special paleographic transcription.",
    "reverse.preset.phSpelling": "ph spelling",
    "reverse.preset.phSpellingGoal": "17 colonial or learned-spelling rows.",
    "reverse.preset.jForms": "Forms with j",
    "reverse.preset.jFormsGoal": "144 loan, name, or modern-spelling rows.",
    "reverse.preset.v94Types": "V94 types",
    "reverse.preset.v94TypesGoal": "12 rows with rare grammatical-type metadata.",
    "reverse.preset.greekLatinNotes": "Greek/Latin",
    "reverse.preset.greekLatinNotesGoal": "99 rows with classical-language notes.",
    "reverse.preset.editorialInterventions": "Interventions",
    "reverse.preset.editorialInterventionsGoal": "782 rows with sic, deletion, addition, or interlinear notes.",
    "reverse.preset.variantLabels": "Variants",
    "reverse.preset.variantLabelsGoal": "≈1.2k rows explicitly labeling variants.",
    "reverse.preset.reduplicatedRoot": "Reduplication",
    "reverse.preset.reduplicatedRootGoal": "Search a root with the +root pattern.",
    "reverse.preset.sameWordPieces": "Two pieces",
    "reverse.preset.sameWordPiecesGoal": "Search two parts inside the same word.",
    "reverse.preset.translationToEdition": "Translation → Edition",
    "reverse.preset.translationToEditionGoal": "Search Translation; show Edition lemmas.",
    "reverse.preset.translationToOriginal": "Translation → Original",
    "reverse.preset.translationToOriginalGoal": "Search Translation; show original spellings.",
    "reverse.preset.translationPhraseToEdition": "Phrase → Edition",
    "reverse.preset.translationPhraseToEditionGoal": "Search a full phrase in Translation.",
    "reverse.preset.editionToTranslation": "Edition → Translation",
    "reverse.preset.editionToTranslationGoal": "Search Edition; show Translation.",
    "reverse.preset.editionToOriginal": "Edition → Original",
    "reverse.preset.editionToOriginalGoal": "Search Edition; show Original.",
    "reverse.preset.originalToEdition": "Original → Edition",
    "reverse.preset.originalToEditionGoal": "Search Original; show Edition lemmas.",
    "reverse.preset.originalToTranslation": "Original → Translation",
    "reverse.preset.originalToTranslationGoal": "Search Original; show Translation.",
    "reverse.preset.commentToEdition": "Comment → Edition",
    "reverse.preset.commentToEditionGoal": "Search Comment; show Edition lemmas.",
    "reverse.preset.editionToSources": "Edition → Sources",
    "reverse.preset.editionToSourcesGoal": "Search Edition; show Source.",
    "reverse.preset.translationToSources": "Translation → Sources",
    "reverse.preset.translationToSourcesGoal": "Search Translation; show Source.",
    "reverse.preset.sourceToEdition": "Source → Edition",
    "reverse.preset.sourceToEditionGoal": "Search Source; show Edition lemmas.",
    "reverse.preset.sourceToTranslation": "Source → Translation",
    "reverse.preset.sourceToTranslationGoal": "Search Source; show Translation.",
    "reverse.preset.commentToSources": "Comment → Source",
    "reverse.preset.commentToSourcesGoal": "Search Comment; show Source.",
    "reverse.objective.meaning": "Objective: start from an idea in translation and see which Nahuatl words cover it.",
    "reverse.objective.exactMeaning": "Objective: isolate entries where the meaning appears as an exact match.",
    "reverse.objective.phraseMeaning": "Objective: find entries that express a full phrase, definition, or explanation.",
    "reverse.objective.nahuatlExact": "Objective: confirm a normalized Nahuatl form and review its sources.",
    "reverse.objective.nahuatlStarts": "Objective: recover possible lemmas when you only remember the beginning.",
    "reverse.objective.oldSpelling": "Objective: identify the normalized edition behind an original or historical spelling.",
    "reverse.objective.notesMention": "Objective: find comments, notes, or sources that mention the topic.",
    "reverse.objective.qAbbrev": "Objective: expand q^ abbreviations in original spelling and compare them to normalized edition (171 rows).",
    "reverse.objective.questionOriginal": "Objective: review ? marks in original spelling, usually paleographic uncertainty (482 rows).",
    "reverse.objective.bracedOriginal": "Objective: review alternate readings preserved in braces in original spelling (408 rows).",
    "reverse.objective.bnfAdditions": "Objective: see additions, interlinear text, or hand notes in BNF 361; combines Source + Comment (61 rows).",
    "reverse.objective.rareUse": "Objective: isolate rare-use notes in Cortés y Zedeño; combines Source + Comment (38 rows).",
    "reverse.objective.uncertainNotes": "Objective: find comments where editors mark doubt, probability, or uncertainty (≈1.7k rows).",
    "reverse.objective.slashOriginal": "Objective: review forms with / in original spelling, usually variants, alternates, or editorial segmentation (307 rows).",
    "reverse.objective.sectionSign": "Objective: review original spellings with §, a special paleographic transcription mark (492 rows).",
    "reverse.objective.phSpelling": "Objective: isolate colonial or learned ph spellings in original spelling (17 rows).",
    "reverse.objective.jForms": "Objective: find normalized forms with j, useful for loans, names, and modern spellings (144 rows).",
    "reverse.objective.v94Types": "Objective: find rare V94 grammatical metadata such as prefix, suffix, article, or vocative (12 rows).",
    "reverse.objective.greekLatinNotes": "Objective: find comments that cite Greek or Latin as a lexicographic-note structure (99 rows).",
    "reverse.objective.editorialInterventions": "Objective: find comments with editorial interventions such as sic, crossed-out, deleted, added, or interlinear text (782 rows).",
    "reverse.objective.variantLabels": "Objective: review comments that explicitly label variants (≈1.2k rows).",
    "reverse.objective.reduplicatedRoot": "Objective: search for a reduplicated root with the mini-language; type the base root and the filter uses +root.",
    "reverse.objective.sameWordPieces": "Objective: search words that contain two pieces at once; type something like teo||tlatol.",
    "reverse.objective.translationToEdition": "Relationship: type a word that appears in Translation; the table shows every associated Edition lemma.",
    "reverse.objective.translationToOriginal": "Relationship: type a word that appears in Translation; the table shows associated Original spellings.",
    "reverse.objective.translationPhraseToEdition": "Relationship: search a phrase in Translation and show Edition lemmas linked to that phrase.",
    "reverse.objective.editionToTranslation": "Relationship: type an Edition lemma; the table shows its documented translations.",
    "reverse.objective.editionToOriginal": "Relationship: type an Edition lemma; the table shows original spellings that record it.",
    "reverse.objective.originalToEdition": "Relationship: type an Original spelling; the table shows the corresponding normalized Edition.",
    "reverse.objective.originalToTranslation": "Relationship: type an Original spelling; the table shows associated translations.",
    "reverse.objective.commentToEdition": "Relationship: type a Comment topic; the table shows Edition lemmas connected to that note.",
    "reverse.objective.editionToSources": "Relationship: type an Edition lemma; the table shows sources that attest it.",
    "reverse.objective.translationToSources": "Relationship: type a Translation word; the table shows sources that contain that meaning.",
    "reverse.objective.sourceToEdition": "Relationship: type a source or part of its name; the table shows Edition lemmas in that source.",
    "reverse.objective.sourceToTranslation": "Relationship: type a source or part of its name; the table shows translations and lemmas from that source.",
    "reverse.objective.commentToSources": "Relationship: type a Comment topic; the table shows sources where that note appears.",
    "reverse.placeholder.meaning": "Type the idea, e.g. water",
    "reverse.placeholder.exactMeaning": "Type the exact meaning",
    "reverse.placeholder.phraseMeaning": "Type the phrase or definition",
    "reverse.placeholder.nahuatlExact": "Type the Nahuatl word",
    "reverse.placeholder.nahuatlStarts": "Type the beginning you remember",
    "reverse.placeholder.oldSpelling": "Type the old spelling",
    "reverse.placeholder.notesMention": "Type the note topic or word",
    "reverse.placeholder.reduplicatedRoot": "Type the root, e.g. tzitz",
    "reverse.placeholder.sameWordPieces": "Type pieces, e.g. teo||tlatol",
    "reverse.placeholder.translationToEdition": "Word in translation, e.g. water",
    "reverse.placeholder.translationToOriginal": "Word in translation, e.g. water",
    "reverse.placeholder.translationPhraseToEdition": "Phrase in translation",
    "reverse.placeholder.editionToTranslation": "Edition lemma, e.g. atl",
    "reverse.placeholder.editionToOriginal": "Edition lemma",
    "reverse.placeholder.originalToEdition": "Original spelling",
    "reverse.placeholder.originalToTranslation": "Original spelling",
    "reverse.placeholder.commentToEdition": "Topic or word in comment",
    "reverse.placeholder.editionToSources": "Edition lemma",
    "reverse.placeholder.translationToSources": "Word in translation",
    "reverse.placeholder.sourceToEdition": "Source or abbreviation, e.g. Molina",
    "reverse.placeholder.sourceToTranslation": "Source or abbreviation, e.g. Molina",
    "reverse.placeholder.commentToSources": "Topic or word in comment",
    "tab.compare": "Compare lemma",
    "tab.browse": "Browse",
    "filter.title": "Filter",
    "filter.help": "Filter help",
    "label.column": "Column",
    "label.scope": "Search in",
    "scope.whole": "Cell",
    "scope.word": "Word",
    "scope.phrase": "Phrase",
    "field.grafia.short": "edition",
    "field.paleografia.short": "original",
    "field.traduccion.short": "translation",
    "field.comentario.short": "comment",
    "grid.include": "Include",
    "grid.exclude": "Exclude",
    "grid.side.toggle": "Switch include/exclude",
    "grid.exact": "Exact",
    "grid.starts": "Starts with",
    "grid.contains": "Contains",
    "grid.ends": "Ends with",
    "action.run": "Run",
    "action.clear": "Clear",
    "nav.search": "Search",
    "nav.chips": "Applied",
    "nav.results": "Results",
    "chips.empty": "No filters applied yet.",
    "placeholder.exact.incl": "is exactly...",
    "placeholder.exact.excl": "is not exactly...",
    "placeholder.starts.incl": "starts with...",
    "placeholder.starts.excl": "does not start with...",
    "placeholder.any.incl": "contains...",
    "placeholder.any.excl": "does not contain...",
    "placeholder.ends.incl": "ends with...",
    "placeholder.ends.excl": "does not end with...",
    "sources.title": "Sources",
    "sources.selection": "Selection",
    "sources.sort": "Order",
    "sources.fill": "All",
    "sources.clear": "None",
    "sources.orderAlpha": "Sort sources A-Z",
    "sources.orderAlpha.short": "A-Z",
    "sources.orderYear": "Sort sources by year",
    "sources.orderYear.short": "Year",
    "regex.title": "Mini-language",
    "rx.wildcards": "Wildcards",
    "rx.q1": "any 1 grapheme",
    "rx.q2": "exactly 2 graphemes",
    "rx.star1": "1 or more graphemes",
    "rx.star2": "2 or more graphemes",
    "rx.range": "2 to 4 graphemes",
    "rx.optional.any": "optional grapheme",
    "rx.optional.literal": "optional h",
    "rx.grapheme.note": "In Edición, Original, and Comment, ? counts ch/tz/qu/etc. as one grapheme",
    "rx.alternatives": "Alternatives",
    "rx.alt.group": "pato <em>or</em> pata",
    "rx.alt.pipe": "equivalent (top level)",
    "rx.alt.escape": "literal pipe",
    "rx.escape.meta": "literal signs",
    "rx.alt.wildcard.after": "c/qu + graphemes",
    "rx.phrase.exact": "exact phrase",
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
    "rx.negclass": "Negated class",
    "rx.negclass.desc": "any non-vowel",
    "rx.negclass.ex": "excludes vowels and s",
    "rx.cv.note": "Only active inside braces { }",
    "rx.containsboth": "Both in same word",
    "rx.both.desc": "word contains <em>both</em>",
    "rx.both.note": "Double pipe <code>||</code> inside parentheses",
    "rx.reduplication": "Reduplication",
    "rx.redup.simple": "→ <em>papaqui</em>",
    "rx.redup.infix": "→ <em>pahpaqui</em>",
    "rx.redup.marker": "→ <em>pahpaqui</em> by pattern",
    "rx.redup.optionalH": "→ <em>papaqui</em> / <em>pahpaqui</em>",
    "rx.redup.optionalMarker": "→ <em>ahuia</em> / <em>aahuia</em>",
    "rx.redup.note": "{R} repeats the next block; (h) allows optional h",
    "rx.repeat.same.grapheme": "same grapheme repeated",
    "rx.repeat.same.cv": "same CV syllable repeated",
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
    "study.title": "Flashcards",
    "study.hint": "Build a deck from the current results; each card uses Edition and Translation.",
    "study.mode": "Mode",
    "study.mode.study": "Study",
    "study.mode.exam": "Exam",
    "study.view": "Card",
    "study.view.flip": "2-sided",
    "study.view.both": "1-sided",
    "study.face.flip": "Flip card",
    "study.face.next": "Next card",
    "study.face.zones.flip": "Left: previous · center: flip · right: next",
    "study.face.zones.next": "Left: previous · right: next",
    "study.direction": "Direction",
    "study.direction.nt": "Edition → Translation",
    "study.direction.tn": "Translation → Edition",
    "study.limit": "Cards",
    "study.useFilters": "Use current results",
    "study.shortOnly": "Prefer short definitions",
    "study.shuffle": "Shuffle",
    "study.build": "Build deck",
    "study.reset": "Restart",
    "study.reveal": "Show",
    "study.flip": "Flip",
    "study.next": "Next",
    "study.again": "Again",
    "study.hard": "Hard",
    "study.good": "Good",
    "study.easy": "Easy",
    "study.empty": "Build a deck to start.",
    "study.noCards": "No cards with both lemma and translation in this scope.",
    "study.done": "Deck finished.",
    "study.summary": "Summary",
    "study.summary.results": "Results",
    "study.summary.primary": "Initial cards: {{cards}} · Answers: {{answers}}",
    "study.summary.study": "Cards studied: {{seen}}",
    "study.summary.score": "Good/Easy: {{known}} ({{percent}}%) · Review: {{review}}",
    "study.summary.detail": "Again: {{again}} · Hard: {{hard}} · Good: {{good}} · Easy: {{easy}}",
    "study.scope": "{{rows}} available rows · {{cards}} possible cards",
    "study.cardCount": "{{current}}/{{total}}",
    "study.progress.study": "{{seen}} studied",
    "study.progress": "{{seen}} views · {{good}} good · {{again}} review",
    "study.sources": "{{sources}} sources · {{rows}} rows",
    "study.front.edition": "Edition",
    "study.front.translation": "Translation",
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
    "browse.meta.entries": "{{rows}} entries",
    "browse.meta.counts": "{{sources}} sources · {{rows}} rows · {{translations}} translations",
    "browse.compare": "Isolate",
    "browse.pagesize.label": "Rows",
    "browse.page": "Page {{page}} of {{total}}",
    "site.tagline": "Use the filters to find words by spelling, translation, or source; results appear in the table below.",
    "table.header.paleografia": "Original",
    "table.header.grafia": "Edition",
    "table.header.traduccion": "Translation",
    "table.header.fuente": "Source",
    "table.header.comentario": "Comment",
    "table.rowDetail.open": "Show record",
    "table.rowDetail.close": "Hide record",
    "table.sort.label": "Sort:",
    "table.sort.all": "All",
    "table.sort.page": "Page",
    "table.caption": "Nahuatl database results",
    "table.status.loading": "Loading data…",
    "table.status.error": "Couldn't load the data. Check the connection and try again.",
    "table.status.none": "No records to show.",
    "table.status.showing": "Records shown: {{start}}-{{end}} of {{total}}",
    "table.status.detail.auto": "{{exact}} exact lemmas · {{phrase}} phrases",
    "table.status.detail.manual": "{{exact}} exact lemmas · {{phrase}} phrases · Manual",
    "table.empty": "No data available.",
    "table.empty.filtered": "No rows match the current filters. Try removing a filter, broadening sources, or using free-accent matching.",
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
    "field.fuente": "Source",
    "nav.left": "Move left",
    "nav.right": "Move right",
    "action.add": "Add filter",
    "action.update": "Update",
    "filter.title": "Filter",
    "lang.toggle": "Español",
    "action.share": "Share",
    "share.copied": "Link copied",
    "share.failed": "Couldn't share",
    "copy.cell": "Text copied",
    "page.first": "First page",
    "page.prev": "Previous page",
    "page.next": "Next page",
    "page.last": "Last page",
    "sort.by": "Sort by",
    "sort.asc": "ascending",
    "sort.desc": "descending",
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
    "chips.zone.and": "×",
    "chips.zone.or": "÷",
    "chips.clearAll": "Clear all",
    "chips.removeFilter": "Remove filter",
    "chips.applied": "Applied filters",
    "chips.scope.whole.code": "C",
    "chips.scope.word.code": "W",
    "chips.scope.phrase.code": "P",
    "comentario.expandRow": "Open comment",
    "comentario.collapseRow": "Close comment",
    "session.new": "New search",
    "session.close": "Close search",
    "sort.childHint": "Order within each lemma",
    "toggle.expandCollapse": "Expand/Collapse",
    "page.current": "Current page",
    "page.total": "of {{total}} pg.",
    "comentario.lang": "Comment language",
    "list.expandAll": "Expand/Collapse records",
    "lemma.expandAll": "Expand/Collapse lemmas",
    "comentario.expandAll": "Expand/Collapse comments",
    "table.pagesize.label": "Rows:",
    "table.pagesize.lemmasLabel": "Lemmas:",
    "table.columns": "Cols ▾",
    "columns.title": "Columns",
    "columns.reset": "Reset",
    "columns.show": "Show",
    "columns.hide": "Hide",
    "columns.visible": "Visible",
    "columns.hidden": "Hidden",
    "columns.moveLeft": "Move left",
    "columns.moveRight": "Move right",
    "columns.narrower": "Narrower",
    "columns.wider": "Wider",
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

const FIELD_SHORT_BY_LANG = {
  es: {
    "Escritura original": "Orig.",
    "Texto estandarizado": "Ed.",
    "Traducción": "Trad.",
    "Comentario": "Com.",
  },
  en: {
    "Escritura original": "Orig.",
    "Texto estandarizado": "Ed.",
    "Traducción": "Tr.",
    "Comentario": "Com.",
  }
};

function fieldShortLabel(field) {
  const dict = FIELD_SHORT_BY_LANG[currentLang] || FIELD_SHORT_BY_LANG.es;
  return dict[field] || FIELD_SHORT_BY_LANG.es[field] || field;
}

function chipScopeCodeForFilter(filter) {
  const scope = normalizeScope(filter.scope || "whole");
  if (scope === "whole") return t("chips.scope.whole.code");
  if (scope === "phrase") return t("chips.scope.phrase.code");
  return t("chips.scope.word.code");
}

function chipPartMarkup(filter, display) {
  const scope = chipScopeCodeForFilter(filter);
  const value = compactQuoteValue(display);
  let body;
  if (filter.mode === "starts") body = `${value}+`;
  else if (filter.mode === "any") body = `+${value}+`;
  else if (filter.mode === "ends") body = `+${value}`;
  else body = value;
  return `${filter.negate ? "-" : ""}${scope}(${body})`;
}

function compactQuoteValue(value) {
  const escaped = escapeHtml(String(value ?? "")
    .replace(/\\/g, "\\\\")
    .replace(/'/g, "\\'")
    .replace(/_/g, "\\_")
    .replace(/\s+/g, "_"));
  return `'${escaped}'`;
}

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
const FUENTE_OWNER = "fuentes";
const COMPARE_OWNER = "compareOwner";
const REVERSE_OWNER = "reverseOwner";
const REVERSE_PRESETS = {
  translationToEdition: {
    titleKey: "reverse.preset.translationToEdition",
    goalKey: "reverse.preset.translationToEditionGoal",
    field: "Traducción",
    mode: "any",
    scope: "word",
    objectiveKey: "reverse.objective.translationToEdition",
    placeholderKey: "reverse.placeholder.translationToEdition",
    viewMode: "lemmas",
    visibleColumns: ["Texto estandarizado", "Traducción", "Fuente"],
    commentFields: ["Traducción", "Comentario"]
  },
  translationToOriginal: {
    titleKey: "reverse.preset.translationToOriginal",
    goalKey: "reverse.preset.translationToOriginalGoal",
    field: "Traducción",
    mode: "any",
    scope: "word",
    objectiveKey: "reverse.objective.translationToOriginal",
    placeholderKey: "reverse.placeholder.translationToOriginal",
    viewMode: "rows",
    visibleColumns: ["Escritura original", "Texto estandarizado", "Traducción", "Fuente"],
    commentFields: ["Traducción", "Comentario"]
  },
  translationToSources: {
    titleKey: "reverse.preset.translationToSources",
    goalKey: "reverse.preset.translationToSourcesGoal",
    field: "Traducción",
    mode: "any",
    scope: "word",
    objectiveKey: "reverse.objective.translationToSources",
    placeholderKey: "reverse.placeholder.translationToSources",
    viewMode: "rows",
    visibleColumns: ["Fuente", "Texto estandarizado", "Traducción"],
    commentFields: ["Traducción", "Comentario"]
  },
  editionToTranslation: {
    titleKey: "reverse.preset.editionToTranslation",
    goalKey: "reverse.preset.editionToTranslationGoal",
    field: "Texto estandarizado",
    mode: "exact",
    scope: "word",
    objectiveKey: "reverse.objective.editionToTranslation",
    placeholderKey: "reverse.placeholder.editionToTranslation",
    viewMode: "rows",
    visibleColumns: ["Texto estandarizado", "Traducción", "Fuente"]
  },
  editionToOriginal: {
    titleKey: "reverse.preset.editionToOriginal",
    goalKey: "reverse.preset.editionToOriginalGoal",
    field: "Texto estandarizado",
    mode: "exact",
    scope: "word",
    objectiveKey: "reverse.objective.editionToOriginal",
    placeholderKey: "reverse.placeholder.editionToOriginal",
    viewMode: "rows",
    visibleColumns: ["Texto estandarizado", "Escritura original", "Fuente"]
  },
  editionToSources: {
    titleKey: "reverse.preset.editionToSources",
    goalKey: "reverse.preset.editionToSourcesGoal",
    field: "Texto estandarizado",
    mode: "exact",
    scope: "word",
    objectiveKey: "reverse.objective.editionToSources",
    placeholderKey: "reverse.placeholder.editionToSources",
    viewMode: "rows",
    visibleColumns: ["Fuente", "Texto estandarizado", "Traducción"]
  },
  originalToEdition: {
    titleKey: "reverse.preset.originalToEdition",
    goalKey: "reverse.preset.originalToEditionGoal",
    field: "Escritura original",
    mode: "any",
    scope: "word",
    objectiveKey: "reverse.objective.originalToEdition",
    placeholderKey: "reverse.placeholder.originalToEdition",
    viewMode: "lemmas",
    visibleColumns: ["Texto estandarizado", "Escritura original", "Traducción", "Fuente"]
  },
  originalToTranslation: {
    titleKey: "reverse.preset.originalToTranslation",
    goalKey: "reverse.preset.originalToTranslationGoal",
    field: "Escritura original",
    mode: "any",
    scope: "word",
    objectiveKey: "reverse.objective.originalToTranslation",
    placeholderKey: "reverse.placeholder.originalToTranslation",
    viewMode: "rows",
    visibleColumns: ["Traducción", "Escritura original", "Texto estandarizado", "Fuente"]
  },
  sourceToEdition: {
    titleKey: "reverse.preset.sourceToEdition",
    goalKey: "reverse.preset.sourceToEditionGoal",
    field: "Fuente",
    mode: "any",
    scope: "whole",
    objectiveKey: "reverse.objective.sourceToEdition",
    placeholderKey: "reverse.placeholder.sourceToEdition",
    viewMode: "lemmas",
    visibleColumns: ["Texto estandarizado", "Fuente", "Traducción"]
  },
  sourceToTranslation: {
    titleKey: "reverse.preset.sourceToTranslation",
    goalKey: "reverse.preset.sourceToTranslationGoal",
    field: "Fuente",
    mode: "any",
    scope: "whole",
    objectiveKey: "reverse.objective.sourceToTranslation",
    placeholderKey: "reverse.placeholder.sourceToTranslation",
    viewMode: "rows",
    visibleColumns: ["Traducción", "Texto estandarizado", "Fuente"]
  },
  commentToEdition: {
    titleKey: "reverse.preset.commentToEdition",
    goalKey: "reverse.preset.commentToEditionGoal",
    field: "Comentario",
    mode: "any",
    scope: "whole",
    objectiveKey: "reverse.objective.commentToEdition",
    placeholderKey: "reverse.placeholder.commentToEdition",
    viewMode: "lemmas",
    visibleColumns: ["Texto estandarizado", "Comentario", "Fuente"]
  },
  commentToSources: {
    titleKey: "reverse.preset.commentToSources",
    goalKey: "reverse.preset.commentToSourcesGoal",
    field: "Comentario",
    mode: "any",
    scope: "whole",
    objectiveKey: "reverse.objective.commentToSources",
    placeholderKey: "reverse.placeholder.commentToSources",
    viewMode: "rows",
    visibleColumns: ["Fuente", "Comentario", "Texto estandarizado"]
  }
};
let currentReversePreset = "translationToEdition";
const FUENTE_OPTIONS = [
  "153? Trilingüe",
  "1547 Olmos_G",
  "1547 Olmos_V ?",
  "1551-95 Documentos nahuas de la Ciudad de México",
  "1565 Sahagún Escolios",
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
const DEFAULT_EXCLUDED_FUENTES = new Set(["1580 CF Index"]);
const DEFAULT_FUENTE_OPTIONS = FUENTE_OPTIONS.filter(name => !DEFAULT_EXCLUDED_FUENTES.has(name));

function createDefaultFuenteSet() {
  return new Set(DEFAULT_FUENTE_OPTIONS);
}

function isDefaultFuenteSelection(set = selectedFuentes) {
  if (!set || set.size !== DEFAULT_FUENTE_OPTIONS.length) return false;
  return DEFAULT_FUENTE_OPTIONS.every(name => set.has(name));
}

sessions[0].fuentes = createDefaultFuenteSet();
let selectedFuentes = sessions[0].fuentes;
let lastRenderRows = [];
let lastRenderTotal = 0;
let lastFilteredRows = [];
let lastScrollNavChipCount = 0;
let displayOffset = 0;
const pageScrollByOffset = new Map();
let sortKeys = []; // [{field, dir}]
let sortScope = "all"; // "all" | "page"
const hiddenColumns = new Set();
const expandedLemmas = new Set();
const expandedMobileRows = new Set();
const mobileRowById = new Map();
const columnWidths = new Map(DEFAULT_COLUMN_WIDTHS);
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
let currentLang = "es";
let dataLoadFailed = false;
let lastPairResults = null;
let lastPairMeta = null;
let studyBaseDeck = [];
let studyDeck = [];
let studyIndex = 0;
let studyAnswerVisible = false;
let studyMode = "study";
let studyViewMode = "flip";
let studyStats = { seen: 0, again: 0, hard: 0, good: 0, easy: 0 };
let studyEmptyMessageKey = "study.empty";
let lastRankingSummary = null;
let tableViewMode = "rows"; // "rows" | "lemmas"
let lastLemmaItems = [];
let lastLemmaPageOffsets = [0];
const prioritySortCache = new WeakMap();
const FUENTE_ORDER_KEY = "nahuatl-source-order-v1";
let fuenteOrderMode = "title"; // "title" | "year"

document.addEventListener("DOMContentLoaded", () => {
  loadColumnState();
  loadFuenteOrderMode();
  syncHeaderOrderToTableFields();
  syncFieldPillOrder();
  setupLanguageToggle();
  setupFilterHelpToggle();
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
    if (e.key !== "Enter") return;
    const target = e.target;
    if (!(target instanceof HTMLElement)) return;
    if (!target.closest("#filtersPanel")) return;
    if (!target.matches(".filter-input")) return;
    e.preventDefault();
    submitFilterCardFromKeyboard(target.closest(".filter-card"));
  });
  setupFilterCards();
  initCardNavigation();
  setupTabs();
  setupSortControls();
  setupSortScopeControls();
  updateSortIndicators();
  setupPaginationControls();
  setupPageSizeControls();
  setupColumnControls();
  setupStickyHeaderTable();
  setupComentarioToggleAll();
  setupTableToggleAll();
  setupLemmaToggleAll();
  setupExportButtons();
  renderFuenteList();
  setupFuenteActions();
  setupWimmerTranslate();
  setupPairFinder();
  setupStudyMode();
  setupViewToggle();
  setupEdicionCellClick();
  setupReverseLookup();
  setupShareButton();
  setupLongPressCopy();
  setupSwipeTabs();
  setupKeyboardAvoidance();
  setupScrollNav();
  loadCompressedJsonl(versionedAssetUrl("data/data.jsonl.gz"))
    .then(text => {
      const rows = text.split("\n").filter(Boolean).map(line => JSON.parse(line));
      rows.forEach((row, idx) => {
        row._rid = row.record_id || idx;
        row._prio = parsePriority(row.prio);
        row._browseOrder = computeBrowseOrderKey(row.record_id || idx);
      });
      dataRows = rows;
      mobileRowById.clear();
      rows.forEach(row => mobileRowById.set(getMobileRowId(row), row));
      buildSourceSlugMaps();
      const initialState = parseHashRoute(location.hash);
      if (initialState) {
        applyParsedState(initialState);
      } else {
        applyFuenteFilters();
      }
      hashRouteApplied = true;
      window.addEventListener("hashchange", handleHashChange);
    })
    .catch(() => {
      dataLoadFailed = true;
      dataRows = [];
      setStatus(t("table.status.error"));
      setTableStatusMessage(t("table.status.error"));
      renderScrollNavBadges();
    });
});

function loadCompressedJsonl(url) {
  return fetch(url).then(response => {
    if (!response.ok) {
      throw new Error(`Data request failed with ${response.status}`);
    }
    if (!response.body) {
      throw new Error("Data response has no body");
    }
    if ("DecompressionStream" in window) {
      const stream = new DecompressionStream("gzip");
      response.body.pipeTo(stream.writable);
      return new Response(stream.readable).text();
    }
    return response.text();
  });
}

// Phone-only: scroll-nav buttons switch the app between three full-viewport
// screens (filters / chips / results). Desktop ignores data-screen entirely —
// all three sections are visible at once in the CSS layout.
function setupScrollNav() {
  document.querySelectorAll(".scroll-nav-btn").forEach(btn => {
    btn.addEventListener("click", () => showScreen(btn.dataset.scroll));
  });
}

function t(key, vars = {}) {
  const dict = I18N[currentLang] || I18N.es;
  let text = dict[key] ?? I18N.es[key] ?? key;
  Object.entries(vars).forEach(([name, value]) => {
    text = text.replace(new RegExp(`{{\\s*${name}\\s*}}`, "g"), value);
  });
  return text;
}

function setTranslatedText(el, key) {
  if (!el || !key) return;
  const label = el.matches(".btn-label") ? el : el.querySelector(":scope > .btn-label");
  const target = label || el;
  if (target.dataset) target.dataset.i18n = key;
  target.textContent = t(key);
}

function setInlineLabelText(el, text) {
  if (!el) return;
  const label = el.querySelector(":scope > .btn-label");
  if (label) label.textContent = text;
  else el.textContent = text;
}

function mobileIconMarkup(iconId, extraClass = "") {
  const className = extraClass ? `mobile-icon ${extraClass}` : "mobile-icon";
  return `<svg class="${className}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="#${iconId}"></use></svg>`;
}

function setButtonState(btn, key, iconId) {
  if (!btn || !key) return;
  setTranslatedText(btn, key);
  if ("i18nAriaLabel" in btn.dataset) btn.dataset.i18nAriaLabel = key;
  if ("i18nTitle" in btn.dataset) btn.dataset.i18nTitle = key;
  btn.setAttribute("aria-label", t(key));
  btn.setAttribute("title", t(key));
  if (!iconId) return;
  const use = btn.querySelector(".mobile-icon use");
  if (!use) return;
  use.setAttribute("href", `#${iconId}`);
  use.setAttribute("xlink:href", `#${iconId}`);
}

function applyTranslations() {
  document.documentElement.lang = currentLang;

  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.dataset.i18n;
    if (key) setTranslatedText(el, key);
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

  document.querySelectorAll("[data-i18n-title]").forEach(el => {
    const key = el.dataset.i18nTitle;
    if (key) el.setAttribute("title", t(key));
  });

  document.title = t("title");
  updatePageSizeLabel();
}

function refreshLanguageDependentUI() {
  const y = getTableScrollTop();
  updateAccentLabels();
  renderColumnControls();
  if (!dataRows || !dataRows.length) {
    setStatus(t(dataLoadFailed ? "table.status.error" : "table.status.loading"));
    setTableStatusMessage(t(dataLoadFailed ? "table.status.error" : "table.status.loading"));
    return;
  }
  updateViewToggleLabels();
  renderSessionBar();
  renderTable(lastRenderRows, lastRenderTotal);
  refreshPairFinderUI();
  refreshStudyModeUI();
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

function setupFilterHelpToggle() {
  const btn = document.querySelector("[data-filter-help-toggle]");
  const help = document.getElementById("filterHelpText");
  if (!btn || !help) return;
  btn.addEventListener("click", () => {
    const expanded = btn.getAttribute("aria-expanded") === "true";
    btn.setAttribute("aria-expanded", expanded ? "false" : "true");
    help.classList.toggle("site-tagline--open", !expanded);
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
      else updateUrlHash();
    });
  });
}

function updateAccentLabels() {
  document.querySelectorAll(".accent-btn").forEach(btn => {
    const mode = btn.dataset.accent;
    setTranslatedText(btn, mode === "strict" ? "accent.strict" : "accent.loose");
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
      else updateUrlHash();
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
      showScreen("filters");
      loadGroupForEditing(chip.dataset.groupId);
    }
  });
}

// Phone-only screen switcher. Safe to call on desktop — the attribute
// is simply ignored there (no CSS rules reference it outside the mobile
// media query).
function showScreen(key) {
  const shell = document.querySelector(".app-shell");
  if (!shell) return;
  shell.dataset.screen = key;
  document.querySelectorAll(".scroll-nav-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.scroll === key);
  });
  window.scrollTo({ top: 0, behavior: "auto" });
}

function countActiveFilterChips() {
  const groupOwners = new Set();
  activeFilters.forEach(filter => {
    if (filter.type === "fuenteSet" || filter.owner === FUENTE_OWNER || filter.owner === "f1") return;
    if (filter.owner) groupOwners.add(filter.owner);
  });
  return groupOwners.size;
}

function formatNavBadgeCount(value) {
  const count = Number(value) || 0;
  if (count >= 1000000) return `${Math.round(count / 1000000)}m`;
  if (count >= 1000) return `${Math.round(count / 1000)}k`;
  return String(count);
}

function setScrollNavBadge(kind, count, options = {}) {
  const badge = document.querySelector(`[data-scroll-badge="${kind}"]`);
  if (!badge) return;
  const value = Math.max(0, Number(count) || 0);
  const shouldShow = options.showZero ? dataRows.length > 0 || value > 0 : value > 0;
  badge.hidden = !shouldShow;
  badge.textContent = formatNavBadgeCount(value);
  if (options.pulse && shouldShow) {
    badge.classList.remove("scroll-nav-badge--pulse");
    void badge.offsetWidth;
    badge.classList.add("scroll-nav-badge--pulse");
  }
}

function updateScrollNavBadges(options = {}) {
  const chipCount = options.chipCount ?? countActiveFilterChips();
  setScrollNavBadge("chips", chipCount, {
    pulse: chipCount > lastScrollNavChipCount
  });
  lastScrollNavChipCount = chipCount;
  setScrollNavBadge("results", options.resultCount ?? lastRenderTotal, { showZero: true });
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
  const chipCount = countActiveFilterChips();
  updateScrollNavBadges({ chipCount });

  // Card indicator for the live-preview card
  const f1Card = document.querySelector(".filter-card[data-owner='f1']");
  if (f1Card) f1Card.classList.toggle("filter-card--active", activeFilters.some(f => f.owner === "f1"));

  // Collect committed groups (not f1 preview or fuente)
  const groups = new Map();
  activeFilters.forEach(f => {
    if (f.type === "fuenteSet" || f.owner === FUENTE_OWNER || f.owner === "f1") return;
    if (!groups.has(f.owner)) groups.set(f.owner, []);
    groups.get(f.owner).push(f);
  });

  if (!groups.size) {
    bar.classList.add("active-filters-bar--empty");
    bar.innerHTML = `<div class="active-filters-empty" data-i18n="chips.empty">${t("chips.empty")}</div>`;
    return;
  }
  bar.classList.remove("active-filters-bar--empty");
  bar.innerHTML = "";

  // Partition by logic using groupOrder for ordering
  const andIds = groupOrder.filter(g => g.logic === "AND" && groups.has(g.id)).map(g => g.id);
  const orIds  = groupOrder.filter(g => g.logic === "OR"  && groups.has(g.id)).map(g => g.id);
  // Also include any groups not yet in groupOrder (safety net)
  groups.forEach((_, id) => {
    if (!andIds.includes(id) && !orIds.includes(id)) andIds.push(id);
  });

  function makeChip(groupId, filters) {
    const logic = filters[0].logic || "AND";
    const fieldNames = filters.flatMap(f => (
      Array.isArray(f.fields) && f.fields.length ? f.fields : [f.field]
    )).filter(Boolean);
    const fieldLabels = [...new Set(fieldNames.map(fieldShortLabel))];
    const mixedFields = fieldLabels.length > 1;
    const fieldLabel = fieldLabels.join("/");
    const partJoiner = logic === "OR" ? "÷" : "×";

    const parts = filters.map(f => {
      const val = String(f.value);
      const display = val.length > 16 ? val.slice(0, 14) + "…" : val;
      const partFields = Array.isArray(f.fields) && f.fields.length ? f.fields : [f.field];
      const partFieldLabel = partFields.map(fieldShortLabel).join("/");
      const fieldPrefix = mixedFields && filters.length > 1 ? `${escapeHtml(partFieldLabel)}:` : "";
      return `<span class="chip-part ${f.negate ? "chip-part-excl" : ""}">${fieldPrefix}${chipPartMarkup(f, display)}</span>`;
    }).join(`<span class="chip-dot"> ${partJoiner} </span>`);

    const chip = document.createElement("span");
    chip.className = "filter-chip chip-group";
    chip.dataset.groupId = groupId;
    if (groupId === editingGroupId) chip.classList.add("chip-editing");
    chip.innerHTML =
      `<span class="chip-label"><span class="chip-field">${escapeHtml(fieldLabel)}</span> ${parts}</span>` +
      `<button type="button" class="chip-remove" aria-label="${escapeHtml(t("chips.removeFilter"))}">×</button>`;

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
    clearAll.className = "chip-clear-all mobile-icon-btn";
    clearAll.innerHTML =
      `${mobileIconMarkup("icon-clear")}<span class="btn-label mobile-icon-label">${escapeHtml(t("chips.clearAll"))}</span>`;
    clearAll.setAttribute("aria-label", t("chips.clearAll"));
    clearAll.setAttribute("title", t("chips.clearAll"));
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
  session.expandedMobileRows = Array.from(expandedMobileRows);
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
    expandedMobileRows.clear();
    (session.expandedMobileRows ?? []).forEach(id => expandedMobileRows.add(id));
    pageScrollByOffset.clear();
  }

  renderSessionBar();
  renderFuenteList();
  updateSortIndicators();
  updateSortScopeIndicators();
  updateViewToggleButtons();
  applyFuenteFilters({ keepOffset: true, preserveExpandState: true });

  const scroller = getTableScrollElement();
  if (scroller && session) scroller.scrollTop = session.scrollTop ?? 0;
}

function addSession() {
  saveCurrentSession();
  sessionCounter++;
  const id = `s${sessionCounter}`;
  const newSession = { id, filters: [], order: [], groupCounter: 0, fuentes: createDefaultFuenteSet() };
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
  expandedMobileRows.clear();
  pageScrollByOffset.clear();

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
    expandedMobileRows.clear();
    (nextSession.expandedMobileRows ?? []).forEach(eid => expandedMobileRows.add(eid));
    pageScrollByOffset.clear();
    renderFuenteList();
    updateSortIndicators();
    updateSortScopeIndicators();
    updateViewToggleButtons();
    applyFuenteFilters({ keepOffset: true, preserveExpandState: true });
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
    const tab = document.createElement("div");
    tab.setAttribute("role", "button");
    tab.tabIndex = session.id === currentSessionId ? 0 : -1;
    tab.setAttribute("aria-pressed", session.id === currentSessionId ? "true" : "false");
    tab.className = "session-tab" + (session.id === currentSessionId ? " session-tab--active" : "");
    tab.dataset.sessionId = session.id;

    const label = document.createElement("span");
    label.className = "session-tab-label";
    label.textContent = sessionLabel(session);
    tab.appendChild(label);

    if (sessions.length > 1) {
      const close = document.createElement("button");
      close.type = "button";
      close.className = "session-tab-close";
      close.textContent = "×";
      close.dataset.closeSession = session.id;
      close.setAttribute("aria-label", `${t("session.close")}: ${sessionLabel(session)}`);
      close.title = t("session.close");
      tab.appendChild(close);
    }

    bar.appendChild(tab);
  });

  const addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.className = "session-tab-add";
  addBtn.textContent = "+";
  addBtn.title = t("session.new");
  addBtn.setAttribute("aria-label", t("session.new"));
  bar.appendChild(addBtn);
  requestAnimationFrame(syncSessionFolderNotch);
}

function syncSessionFolderNotch() {
  const shell = document.querySelector(".panel-shell");
  const activeTab = document.querySelector(".session-tab--active");
  const activePanelBody = document.querySelector(".tab-panel.active > .filter-card, .tab-panel.active > .sources-card");
  if (!shell || !activeTab || !activePanelBody) return;
  const tabRect = activeTab.getBoundingClientRect();
  const bodyRect = activePanelBody.getBoundingClientRect();
  const left = Math.max(0, tabRect.left - bodyRect.left);
  const maxWidth = Math.max(0, bodyRect.width - left);
  const width = Math.max(40, Math.min(tabRect.width, maxWidth));
  shell.style.setProperty("--session-notch-left", `${left}px`);
  shell.style.setProperty("--session-notch-width", `${width}px`);
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

  bar.addEventListener("keydown", e => {
    const closeTarget = e.target.closest("[data-close-session]");
    if (closeTarget && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      closeSession(closeTarget.dataset.closeSession);
      return;
    }
    const tab = e.target.closest(".session-tab");
    if (tab && tab.dataset.sessionId && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      loadSession(tab.dataset.sessionId);
    }
  });

  window.addEventListener("resize", syncSessionFolderNotch);
}

// Update session bar label after committing filters (label derives from filter values)
function refreshSessionLabel() {
  saveCurrentSession();
  renderSessionBar();
}

function setupTabs() {
  const buttons = Array.from(document.querySelectorAll(".panel-tabs .tab-btn"));
  function activate(btn, focus = false) {
    buttons.forEach(b => {
      const on = b === btn;
      b.classList.toggle("active", on);
      b.setAttribute("aria-selected", on ? "true" : "false");
      b.setAttribute("tabindex", on ? "0" : "-1");
    });
    const tabId = btn.dataset.tab;
    document.querySelectorAll(".tab-panel").forEach(panel => {
      panel.classList.toggle("active", panel.id === tabId);
    });
    requestAnimationFrame(syncSessionFolderNotch);
    if (focus) btn.focus();
  }
  buttons.forEach((btn, idx) => {
    btn.addEventListener("click", () => activate(btn));
    btn.addEventListener("keydown", e => {
      let nextIdx = -1;
      if (e.key === "ArrowRight") nextIdx = (idx + 1) % buttons.length;
      else if (e.key === "ArrowLeft") nextIdx = (idx - 1 + buttons.length) % buttons.length;
      else if (e.key === "Home") nextIdx = 0;
      else if (e.key === "End") nextIdx = buttons.length - 1;
      if (nextIdx >= 0) {
        e.preventDefault();
        activate(buttons[nextIdx], true);
      }
    });
  });
}

// Tiny haptic helper — silently no-ops where unsupported.
function vibe(ms) {
  try { if (navigator.vibrate) navigator.vibrate(ms); } catch {}
}

// Horizontal swipes on the panel shell cycle through the top panel tabs.
function setupSwipeTabs() {
  const shell = document.querySelector(".panel-shell");
  if (!shell) return;
  if (typeof window === "undefined" || !window.matchMedia) return;
  const mql = window.matchMedia("(max-width: 640px) and (pointer: coarse)");
  let enabled = mql.matches;
  const onChange = () => { enabled = mql.matches; };
  if (mql.addEventListener) mql.addEventListener("change", onChange);
  else if (mql.addListener) mql.addListener(onChange);

  const IGNORE_SEL = [
    "input",
    "textarea",
    "select",
    "button",
    ".pill-group",
    ".fuente-list",
    ".session-bar",
    ".panel-tabs",
    ".toolbar-controls",
    ".column-control-list",
    ".filter-grid",
    ".table-scroll",
    ".reverse-presets-list"
  ].join(", ");
  let startX = 0, startY = 0, startT = 0, tracking = false;

  shell.addEventListener("touchstart", e => {
    if (!enabled || e.touches.length !== 1) { tracking = false; return; }
    if (e.target.closest && e.target.closest(IGNORE_SEL)) { tracking = false; return; }
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    startT = Date.now();
    tracking = true;
  }, { passive: true });

  shell.addEventListener("touchmove", e => {
    if (!tracking) return;
    const dx = e.touches[0].clientX - startX;
    const dy = e.touches[0].clientY - startY;
    if (Math.abs(dy) > Math.abs(dx) && Math.abs(dy) > 12) tracking = false;
    if (tracking && Math.abs(dx) > 18 && Math.abs(dx) > Math.abs(dy) * 1.2) {
      e.preventDefault();
    }
  }, { passive: false });

  shell.addEventListener("touchend", e => {
    if (!tracking) return;
    tracking = false;
    const t = e.changedTouches[0];
    const dx = t.clientX - startX;
    const dy = t.clientY - startY;
    if (Date.now() - startT > 600) return;
    if (Math.abs(dx) < 60) return;
    if (Math.abs(dy) > Math.abs(dx) * 0.7) return;
    const buttons = Array.from(document.querySelectorAll(".panel-tabs .tab-btn"));
    const idx = buttons.findIndex(b => b.classList.contains("active"));
    if (idx < 0) return;
    const next = dx < 0 ? idx + 1 : idx - 1;
    if (next < 0 || next >= buttons.length) return;
    buttons[next].click();
    vibe(8);
  });
}

function syncFuenteMode(card) {
  const active = card.querySelector(".field-btn.active");
  card.classList.toggle("fuente-mode", active?.dataset.field === "Fuente");
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
    const label = t(key).replace("{campo}", campo).replace("{casilla}", casilla);
    input.placeholder = label;
    input.setAttribute("aria-label", label);
  });
}

function setFilterGridSide(card, side, options = {}) {
  if (!card) return;
  const nextSide = side === "exclude" ? "exclude" : "include";
  card.dataset.filterSide = nextSide;

  card.querySelectorAll("[data-filter-side-choice]").forEach(btn => {
    const active = btn.dataset.filterSideChoice === nextSide;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });

  const toggle = card.querySelector("[data-filter-side-toggle]");
  if (toggle) {
    toggle.classList.toggle("is-exclude", nextSide === "exclude");
    toggle.setAttribute("aria-pressed", nextSide === "exclude" ? "true" : "false");
  }

  if (!options.preserveFocus) return;
  const active = document.activeElement;
  if (!active?.matches?.(".filter-input") || !card.contains(active)) return;
  const target = card.querySelector(
    `.filter-input[data-mode="${active.dataset.mode}"][data-negate="${nextSide === "exclude" ? "true" : "false"}"]`
  );
  if (target) target.focus();
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
      syncFuenteMode(card);
      updateFilterPlaceholders(card);
    });
  });
  syncFuenteMode(card);
  updateFilterPlaceholders(card);
  setFilterGridSide(card, card.dataset.filterSide || "include");

  const sideToggle = card.querySelector("[data-filter-side-toggle]");
  if (sideToggle) {
    sideToggle.addEventListener("click", () => {
      const current = card.dataset.filterSide === "exclude" ? "exclude" : "include";
      setFilterGridSide(card, current === "exclude" ? "include" : "exclude", { preserveFocus: true });
    });
  }

  card.querySelectorAll("[data-filter-side-choice]").forEach(btn => {
    btn.addEventListener("click", () => {
      setFilterGridSide(card, btn.dataset.filterSideChoice, { preserveFocus: true });
    });
  });

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
        e.stopPropagation();
        submitFilterCardFromKeyboard(card);
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

function submitFilterCardFromKeyboard(card) {
  const targetCard = card || document.querySelector(".filter-card[data-owner='f1']");
  const submitBtn = targetCard?.querySelector(".add-btn");
  if (submitBtn && !submitBtn.disabled) {
    submitBtn.click();
    return;
  }
  commitFilterCard();
}

function commitFilterCard() {
  const card = document.querySelector(".filter-card[data-owner='f1']");
  if (!card) return;

  const field = card.querySelector(".field-btn.active")?.dataset.field;
  const scope = card.querySelector(".scope-btn.active")?.dataset.scope || "whole";
  if (!field) return;
  if (field === "Fuente") return;

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
  if (addBtn) setButtonState(addBtn, "action.add", "icon-plus");
  card.querySelectorAll(".filter-input").forEach(i => (i.value = ""));
  setFilterGridSide(card, "include");
  applyFilters();
  refreshSessionLabel();
  vibe(8);
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
    setFilterGridSide(card, "include");
  }
  if (editingGroupId) cancelEdit();
  removeOwnerFilters(owner);
  resetComentarioState();
  applyFilters();
  vibe(8);
}

function cancelEdit() {
  editingGroupId = null;
  const card = document.querySelector(".filter-card[data-owner='f1']");
  if (card) {
    const addBtn = card.querySelector(".add-btn");
    if (addBtn) setButtonState(addBtn, "action.add", "icon-plus");
    setFilterGridSide(card, "include");
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
  syncFuenteMode(card);

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
  const preferredSideFilter = filters.find(f => !f.negate) || filters.find(f => f.negate);
  setFilterGridSide(card, preferredSideFilter?.negate ? "exclude" : "include");

  // Set editing state
  editingGroupId = groupId;
  const addBtn = card.querySelector(".add-btn");
  if (addBtn) setButtonState(addBtn, "action.update", "icon-check");

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
      const sideNegate = card.dataset.filterSide === "exclude" ? "true" : "false";
      const preferred = row.querySelector(`.filter-input[data-negate="${sideNegate}"]`) || row.querySelector(".filter-input");
      if (preferred) return preferred;
    }
  }
  const sideNegate = card.dataset.filterSide === "exclude" ? "true" : "false";
  return card.querySelector(`.filter-input[data-negate="${sideNegate}"]`) || card.querySelector(".filter-input");
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

function hasActiveFilterChips(filters = activeFilters) {
  return (filters || []).some(filter =>
    filter.type !== "fuenteSet" &&
    filter.owner !== FUENTE_OWNER &&
    filter.owner !== "f1"
  );
}

function isUnfilteredBrowseState(filters = activeFilters) {
  return !hasActiveFilterChips(filters);
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

function getRankedPage(rows, comparator, offset, pageSize) {
  if (!rows.length || pageSize <= 0) return [];
  const limit = Math.min(rows.length, Math.max(0, offset) + pageSize);
  if (limit <= 0) return [];
  // For the common first-page case, avoid sorting the entire result set.
  // Once the requested prefix is large, native full sort is faster and simpler.
  if (limit > rows.length / 2) {
    return rows.slice().sort(comparator).slice(offset, offset + pageSize);
  }

  const heap = [];
  rows.forEach(row => {
    if (heap.length < limit) {
      heapPushWorstFirst(heap, row, comparator);
      return;
    }
    if (comparator(row, heap[0]) < 0) {
      heap[0] = row;
      heapSiftDownWorstFirst(heap, 0, comparator);
    }
  });
  heap.sort(comparator);
  return heap.slice(offset, offset + pageSize);
}

function heapIsWorse(a, b, comparator) {
  return comparator(a, b) > 0;
}

function heapPushWorstFirst(heap, row, comparator) {
  heap.push(row);
  let idx = heap.length - 1;
  while (idx > 0) {
    const parent = (idx - 1) >> 1;
    if (!heapIsWorse(heap[idx], heap[parent], comparator)) break;
    [heap[idx], heap[parent]] = [heap[parent], heap[idx]];
    idx = parent;
  }
}

function heapSiftDownWorstFirst(heap, idx, comparator) {
  const len = heap.length;
  while (true) {
    const left = idx * 2 + 1;
    const right = left + 1;
    let worst = idx;
    if (left < len && heapIsWorse(heap[left], heap[worst], comparator)) worst = left;
    if (right < len && heapIsWorse(heap[right], heap[worst], comparator)) worst = right;
    if (worst === idx) break;
    [heap[idx], heap[worst]] = [heap[worst], heap[idx]];
    idx = worst;
  }
}

function applyFilters(initial = false, options = {}) {
  if (!dataRows.length) return;
  bumpHighlightCache();
  if (!options.keepOffset) {
    displayOffset = 0;
    pageScrollByOffset.clear();
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
    updateStudyScope();
    updateUrlHash();
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
      paged = getRankedPage(matches, rankingComparator, displayOffset, maxDisplayRows);
      applyManualSort(paged, sortKeys);
    } else {
      const sorted = matches.slice();
      applyManualSort(sorted, sortKeys);
      paged = sorted.slice(displayOffset, displayOffset + maxDisplayRows);
    }
  } else {
    paged = getRankedPage(matches, rankingComparator, displayOffset, maxDisplayRows);
  }
  lastRenderRows = paged.slice();
  lastRenderTotal = total;
  lastRankingSummary = buildRankingSummary(rankingContext, sortKeys.length > 0);
  renderTable(paged, total);
  updateSortIndicators();
  restoreScroll(options);
  renderActiveFilterChips();
  updateStudyScope();
  updateUrlHash();
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
    updateTableToggleButton();
    updateLemmaToggleButton();
    if (scroller) scroller.scrollTop = savedScroll;
    return;
  }

  if (!rows.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = TABLE_FIELDS.filter(f => !hiddenColumns.has(f.key)).length;
    td.className = "table-empty";
    const filtered = activeFilters.length > 0 || selectedFuentes.size < FUENTE_OPTIONS.length;
    td.textContent = t(filtered ? "table.empty.filtered" : "table.empty");
    tr.appendChild(td);
    tbody.appendChild(tr);
  } else {
    let stripeIdx = 0;
    rows.forEach(row => {
      const { tr, comentarioMeta } = buildDataRow(row);
      if (stripeIdx % 2 === 0) tr.classList.add("stripe-alt");
      stripeIdx++;
      tbody.appendChild(tr);
      let anchor = appendMobileDetailRowAfter(tr, row);
      if (comentarioMeta && syncComentarioCell(comentarioMeta)) {
        anchor = appendComentarioDetailRowAfter(anchor, row);
      }
    });
  }

  updateTableStatus(rows.length, totalCount);
  updatePaginationControls(totalCount);
  updateComentarioToggleButton(rows);
  updateTableToggleButton();
  updateLemmaToggleButton();

  if (scroller) scroller.scrollTop = savedScroll;
}

function buildDataRow(row) {
  const tr = document.createElement("tr");
  const rowId = getMobileRowId(row);
  if (row.record_id) tr.dataset.recordId = row.record_id;
  if (rowId) tr.dataset.mobileRowId = rowId;
  let comentarioMeta = null;
  let mobileToggleAttached = false;

  TABLE_FIELDS.forEach(field => {
    const td = document.createElement("td");
    td.dataset.field = field.key;
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
          toggleComentarioForRow(row, tr, content, btn, btn);
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
      } else {
        td.innerHTML = applyHighlights(raw, field.key);
      }
    }
    if (!mobileToggleAttached && !hiddenColumns.has(field.key)) {
      addMobileRowToggle(td, row);
      mobileToggleAttached = true;
    }
    tr.appendChild(td);
  });

  if (comentarioMeta) attachComentarioRowPress(tr, row, comentarioMeta);

  return { tr, comentarioMeta };
}

function getMobileRowId(row) {
  const rawId = row?._rid ?? row?.record_id;
  return rawId === undefined || rawId === null ? "" : String(rawId);
}

// Phone preview: short fields show inline under the primary so each row
// stands on its own. Comentario is the only one we keep behind the +/-
// toggle because it's often a long paragraph.
const MOBILE_PREVIEW_ORDER = [
  "Texto estandarizado",
  "Escritura original",
  "Traducción",
  "Fuente",
];
function getMobilePreviewFields() {
  return MOBILE_PREVIEW_ORDER.filter(k =>
    TABLE_FIELDS.some(f => f.key === k) && !hiddenColumns.has(k)
  );
}

function rowHasDetailContent(row) {
  const previewFields = new Set(getMobilePreviewFields());
  for (const field of TABLE_FIELDS) {
    if (hiddenColumns.has(field.key)) continue;
    if (previewFields.has(field.key)) continue;
    const raw = getDisplayValue(row, field.key);
    if (raw != null && String(raw).trim()) return true;
  }
  return false;
}

function addMobileRowToggle(td, row) {
  const rowId = getMobileRowId(row);
  if (!rowId) return;
  td.classList.add("mobile-row-anchor-cell");

  // Inline the rest of the preview fields under the primary so each row
  // is self-describing without tapping +.
  const previewFields = getMobilePreviewFields();
  previewFields.slice(1).forEach(key => {
    if (key === td.dataset.field) return;
    const raw = getDisplayValue(row, key);
    const safe = raw == null ? "" : String(raw);
    if (!safe.trim()) return;
    const sub = document.createElement("div");
    const slug = key.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, "-").toLowerCase();
    sub.className = `mobile-row-subtitle mobile-row-sub--${slug}`;
    sub.dataset.field = key;
    sub.innerHTML = applyHighlights(safe, key);
    td.appendChild(sub);
  });

  // Only show the +/- toggle if there's actually something behind it.
  if (!rowHasDetailContent(row)) return;

  const expanded = expandedMobileRows.has(rowId);
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "mobile-row-toggle";
  btn.dataset.mobileRowToggle = rowId;
  btn.textContent = expanded ? "−" : "+";
  btn.setAttribute("aria-expanded", expanded ? "true" : "false");
  btn.setAttribute("aria-label", t(expanded ? "table.rowDetail.close" : "table.rowDetail.open"));
  td.prepend(btn);
}

function setMobileRowToggleState(rowTr, expanded) {
  if (!rowTr) return;
  rowTr.classList.toggle("mobile-row-expanded", expanded);
  const btn = rowTr.querySelector(".mobile-row-toggle");
  if (!btn) return;
  btn.textContent = expanded ? "−" : "+";
  btn.setAttribute("aria-expanded", expanded ? "true" : "false");
  btn.setAttribute("aria-label", t(expanded ? "table.rowDetail.close" : "table.rowDetail.open"));
}

function getVisibleTableColumnCount() {
  const visible = TABLE_FIELDS.filter(field => !hiddenColumns.has(field.key)).length;
  return Math.max(1, visible || TABLE_FIELDS.length);
}

function buildMobileDetailRow(row) {
  const tr = document.createElement("tr");
  tr.className = "mobile-row-detail-row";
  const rowId = getMobileRowId(row);
  if (rowId) tr.dataset.mobileRowId = rowId;

  const td = document.createElement("td");
  td.className = "mobile-row-detail-cell";
  td.colSpan = Math.max(1, TABLE_FIELDS.length);

  const detail = document.createElement("div");
  detail.className = "mobile-row-detail";

  // Skip preview fields already shown in the anchor cell. User-hidden columns
  // stay hidden here too so column controls behave like desktop.
  const previewFields = new Set(getMobilePreviewFields());
  TABLE_FIELDS.forEach(field => {
    if (hiddenColumns.has(field.key)) return;
    if (previewFields.has(field.key)) return;
    const raw = getDisplayValue(row, field.key);
    const safe = raw == null ? "" : String(raw);
    if (!safe.trim()) return;

    const item = document.createElement("div");
    item.className = "mobile-detail-field";
    item.dataset.field = field.key;

    const label = document.createElement("div");
    label.className = "mobile-detail-label";
    const labelKey = getFieldI18nKey(field.key);
    label.textContent = labelKey ? t(labelKey) : field.label;

    const value = document.createElement("div");
    value.className = "mobile-detail-value";
    value.innerHTML = applyHighlights(safe, field.key);

    item.appendChild(label);
    item.appendChild(value);
    detail.appendChild(item);
  });

  if (!detail.children.length) {
    const item = document.createElement("div");
    item.className = "mobile-detail-field mobile-detail-field--empty";
    item.textContent = t("table.empty");
    detail.appendChild(item);
  }

  td.appendChild(detail);
  tr.appendChild(td);
  return tr;
}

function appendMobileDetailRowAfter(anchorRow, row) {
  const rowId = getMobileRowId(row);
  if (!anchorRow || !rowId || !expandedMobileRows.has(rowId)) return anchorRow;
  const detailRow = buildMobileDetailRow(row);
  if (anchorRow.classList.contains("lemma-detail-row")) {
    detailRow.classList.add("lemma-detail-row");
    if (anchorRow.dataset.lemma) detailRow.dataset.lemma = anchorRow.dataset.lemma;
  }
  anchorRow.after(detailRow);
  setMobileRowToggleState(anchorRow, true);
  return detailRow;
}

function buildComentarioDetailRow(row) {
  const tr = document.createElement("tr");
  tr.className = "comentario-detail-row";
  if (row.record_id) tr.dataset.recordId = row.record_id;
  tr.dataset.commentRowId = String(row._rid ?? "");

  const td = document.createElement("td");
  td.className = "comentario-detail-cell";
  td.colSpan = getVisibleTableColumnCount();

  const detail = document.createElement("div");
  detail.className = "comentario-detail";
  detail.innerHTML = applyHighlights(getDisplayValue(row, "Comentario"), "Comentario");

  td.appendChild(detail);
  tr.appendChild(td);
  return tr;
}

function removeComentarioDetailRow(rowId) {
  const key = String(rowId ?? "");
  document.querySelectorAll("#dataTable tbody tr.comentario-detail-row").forEach(row => {
    if (row.dataset.commentRowId === key) row.remove();
  });
}

function appendComentarioDetailRowAfter(anchorRow, row) {
  if (!anchorRow || !row || !expandedComments.has(row._rid)) return anchorRow;
  removeComentarioDetailRow(row._rid);
  const detailRow = buildComentarioDetailRow(row);
  if (anchorRow.classList.contains("lemma-detail-row")) {
    detailRow.classList.add("lemma-detail-row");
    if (anchorRow.dataset.lemma) detailRow.dataset.lemma = anchorRow.dataset.lemma;
  }
  if (anchorRow.classList.contains("stripe-alt")) {
    detailRow.classList.add("stripe-alt");
  }
  anchorRow.after(detailRow);
  return detailRow;
}

function getComentarioDetailAnchor(rowTr, row) {
  const rowId = getMobileRowId(row);
  const next = rowTr?.nextElementSibling;
  if (next?.classList.contains("mobile-row-detail-row") && next.dataset.mobileRowId === rowId) {
    return next;
  }
  return rowTr;
}

function toggleComentarioForRow(row, rowTr, content, btn, originEl = rowTr) {
  if (!row || !rowTr || !content || !btn || !expandableComments.has(row._rid)) return;
  const isExpanded = expandedComments.has(row._rid);
  if (isExpanded) {
    const anchor = commentAnchors.get(row._rid);
    setCommentExpanded(row._rid, content, btn, false);
    if (anchor) restoreCommentPressAnchor(anchor, originEl || rowTr);
  } else {
    const rect = (originEl || rowTr).getBoundingClientRect();
    const scrollTop = getTableScrollTop();
    const center = rect.top + rect.height / 2 + scrollTop;
    commentAnchors.set(row._rid, { scrollY: scrollTop, center });
    setCommentExpanded(row._rid, content, btn, true);
    appendComentarioDetailRowAfter(getComentarioDetailAnchor(rowTr, row), row);
  }
  updateComentarioToggleButton(lastRenderRows);
}

function restoreCommentPressAnchor(anchor, originEl) {
  requestAnimationFrame(() => {
    const w = getTableWrapper();
    const rect = originEl?.getBoundingClientRect?.();
    if (!rect) return;
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

function attachComentarioRowPress(rowTr, row, meta) {
  rowTr.classList.add("comentario-row-pressable");
  let press = null;
  let clickTimer = 0;

  rowTr.addEventListener("pointerdown", event => {
    if (!canStartComentarioRowPress(event, rowTr)) {
      press = null;
      return;
    }
    press = {
      x: event.clientX,
      y: event.clientY,
      pointerId: event.pointerId,
      hadSelection: hasTextSelectionInside(rowTr),
      moved: false
    };
  });

  rowTr.addEventListener("pointermove", event => {
    if (!press || press.pointerId !== event.pointerId) return;
    if (Math.hypot(event.clientX - press.x, event.clientY - press.y) > 6) {
      press.moved = true;
    }
  });

  rowTr.addEventListener("pointercancel", () => {
    press = null;
    if (clickTimer) {
      clearTimeout(clickTimer);
      clickTimer = 0;
    }
  });

  rowTr.addEventListener("click", event => {
    if (!press) return;
    const candidate = press;
    press = null;
    if (!canFinishComentarioRowPress(event, rowTr, candidate)) return;
    if (clickTimer) clearTimeout(clickTimer);
    clickTimer = window.setTimeout(() => {
      clickTimer = 0;
      if (!rowTr.isConnected) return;
      if (hasTextSelectionInside(rowTr)) return;
      toggleComentarioForRow(row, rowTr, meta.content, meta.btn, rowTr);
    }, COMENTARIO_ROW_PRESS_DELAY_MS);
  });

  rowTr.addEventListener("dblclick", () => {
    press = null;
    if (clickTimer) {
      clearTimeout(clickTimer);
      clickTimer = 0;
    }
  });
}

function canStartComentarioRowPress(event, rowTr) {
  if (isPhoneViewport()) return false;
  if (event.button !== 0 || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return false;
  if (closestElement(event.target, "button, a, input, select, textarea, [contenteditable], [role='button']")) {
    return false;
  }
  return rowTr.contains(event.target);
}

function canFinishComentarioRowPress(event, rowTr, press) {
  if (isPhoneViewport()) return false;
  if (event.detail > 1 || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return false;
  if (press.moved || press.hadSelection) return false;
  if (closestElement(event.target, "button, a, input, select, textarea, [contenteditable], [role='button']")) {
    return false;
  }
  return !hasTextSelectionInside(rowTr);
}

function closestElement(target, selector) {
  const el = target?.nodeType === Node.ELEMENT_NODE ? target : target?.parentElement;
  return el?.closest?.(selector) || null;
}

function hasTextSelectionInside(root) {
  const selection = window.getSelection?.();
  if (!selection || selection.isCollapsed || !String(selection.toString()).trim()) return false;
  return root.contains(selection.anchorNode) || root.contains(selection.focusNode);
}

function toggleMobileRowDetail(rowTr) {
  if (!rowTr || rowTr.classList.contains("mobile-row-detail-row")) return;
  const rowId = rowTr.dataset.mobileRowId;
  if (!rowId) return;
  const row = mobileRowById.get(rowId);
  if (!row) return;
  const next = rowTr.nextElementSibling;
  const existingDetail = next?.classList.contains("mobile-row-detail-row") && next.dataset.mobileRowId === rowId
    ? next : null;

  if (existingDetail) {
    existingDetail.remove();
    expandedMobileRows.delete(rowId);
    setMobileRowToggleState(rowTr, false);
    updateTableToggleButton();
    return;
  }

  expandedMobileRows.add(rowId);
  const detailRow = buildMobileDetailRow(row);
  if (rowTr.classList.contains("lemma-detail-row")) {
    detailRow.classList.add("lemma-detail-row");
    if (rowTr.dataset.lemma) detailRow.dataset.lemma = rowTr.dataset.lemma;
  }
  rowTr.after(detailRow);
  setMobileRowToggleState(rowTr, true);
  updateTableToggleButton();
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
  updateScrollNavBadges({ resultCount: total });
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
  const scroller = getTableScrollElement();
  return scroller ? scroller.scrollTop : window.scrollY;
}

function setTableScroll(y, behavior = "auto") {
  const scroller = getTableScrollElement();
  if (scroller) {
    scroller.scrollTo({ top: y, behavior });
  } else {
    window.scrollTo({ top: y, behavior });
  }
}

function getColumnWidth(fieldKey) {
  if (isFixedControlColumn(fieldKey)) return getColumnMinWidth(fieldKey);
  return columnWidths.get(fieldKey) || TABLE_FIELDS.find(field => field.key === fieldKey)?.defaultWidth || 140;
}

function isFixedControlColumn(fieldKey) {
  return FIXED_CONTROL_COLUMNS.has(fieldKey);
}

function getColumnMinWidth(fieldKey) {
  return fieldKey === "Comentario" ? COMENTARIO_CONTROL_WIDTH : 70;
}

function isPhoneViewport() {
  return typeof window !== "undefined" && window.matchMedia
    && window.matchMedia("(max-width: 640px)").matches;
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

function applyMobileColumnDefaults() {
  if (!isPhoneViewport()) return;
  // Mobile renders non-preview fields in the expandable detail row, so column
  // visibility should mean the same thing on every viewport.
}

function loadColumnState() {
  let payload;
  try {
    const raw = localStorage.getItem(COLUMN_STATE_KEY);
    if (!raw) { applyMobileColumnDefaults(); return; }
    payload = JSON.parse(raw);
  } catch { applyMobileColumnDefaults(); return; }
  if (!payload || typeof payload !== "object") { applyMobileColumnDefaults(); return; }

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
        const compactDefault = DEFAULT_COLUMN_WIDTHS.get(key);
        columnWidths.set(key, Math.min(w, compactDefault || w));
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

function syncHeaderOrderToTableFields() {
  const headerRow = document.querySelector("#dataTable thead.col-headers tr");
  if (!headerRow) return;

  const headerByKey = new Map(
    Array.from(headerRow.querySelectorAll("th[data-field]")).map(th => [th.dataset.field, th])
  );
  TABLE_FIELDS.forEach(field => {
    const th = headerByKey.get(field.key);
    if (th) headerRow.appendChild(th);
  });
}

function getColumnHeaderOrder() {
  const headerFields = Array.from(document.querySelectorAll("#dataTable thead.col-headers th[data-field]"))
    .map(th => th.dataset.field)
    .filter(Boolean);
  return headerFields.length ? headerFields : TABLE_FIELDS.map(field => field.key);
}

function syncFieldPillOrder() {
  const order = new Map(getColumnHeaderOrder().map((fieldKey, idx) => [fieldKey, idx]));
  document.querySelectorAll(".field-group").forEach(group => {
    const buttons = Array.from(group.querySelectorAll(".field-btn"));
    buttons
      .sort((a, b) => {
        const aIdx = order.has(a.dataset.field) ? order.get(a.dataset.field) : Number.MAX_SAFE_INTEGER;
        const bIdx = order.has(b.dataset.field) ? order.get(b.dataset.field) : Number.MAX_SAFE_INTEGER;
        return aIdx - bIdx;
      })
      .forEach(btn => group.appendChild(btn));
  });
}

function ensureColumnHiddenStyles() {
  if (document.getElementById("colHiddenStyleTag")) return;
  const style = document.createElement("style");
  style.id = "colHiddenStyleTag";
  TABLE_FIELDS.forEach((_, idx) => {
    style.textContent += `#dataTable.col-hidden-${idx} col:nth-child(${idx + 1}),` +
      `#dataTable.col-hidden-${idx} th:nth-child(${idx + 1}),` +
      `#dataTable.col-hidden-${idx} tbody tr:not(.mobile-row-detail-row):not(.comentario-detail-row) td:nth-child(${idx + 1}) { display: none; }\n`;
  });
  document.head.appendChild(style);
}

function setupColumnControls() {
  ensureColumnHiddenStyles();

  const btn = document.getElementById("columnMenuBtn");
  const dropdown = document.getElementById("columnMenuDropdown");
  const resetBtn = document.getElementById("columnResetBtn");
  if (!btn || !dropdown) return;

  btn.addEventListener("click", e => {
    e.stopPropagation();
    document.getElementById("exportMenuDropdown")?.classList.remove("open");
    dropdown.classList.toggle("open");
    renderColumnControls();
  });

  dropdown.addEventListener("click", e => {
    e.stopPropagation();
  });

  document.addEventListener("click", e => {
    if (!dropdown.contains(e.target) && e.target !== btn) {
      dropdown.classList.remove("open");
    }
  });

  document.addEventListener("keydown", e => {
    if (e.key === "Escape") dropdown.classList.remove("open");
  });

  if (resetBtn) {
    resetBtn.addEventListener("click", () => resetColumnControls());
  }

  renderColumnControls();
}

function renderColumnControls() {
  const list = document.getElementById("columnControlList");
  const btn = document.getElementById("columnMenuBtn");
  const dropdown = document.getElementById("columnMenuDropdown");
  const resetBtn = document.getElementById("columnResetBtn");

  if (btn) btn.title = t("columns.title");
  if (dropdown) dropdown.setAttribute("aria-label", t("columns.title"));
  if (resetBtn) setTranslatedText(resetBtn, "columns.reset");
  if (!list) return;

  list.innerHTML = "";
  const visibleCount = TABLE_FIELDS.filter(field => !hiddenColumns.has(field.key)).length;
  const controlFields = getColumnControlFields();

  controlFields.forEach(field => {
    const idx = TABLE_FIELDS.findIndex(entry => entry.key === field.key);
    const row = document.createElement("div");
    row.className = "column-control-row";
    row.dataset.field = field.key;

    const visible = !hiddenColumns.has(field.key);
    const canHide = visibleCount > 1 && !(tableViewMode === "lemmas" && field.key === "Texto estandarizado");
    const check = document.createElement("input");
    check.type = "checkbox";
    check.className = "column-visible-check";
    check.checked = visible;
    check.disabled = visible && !canHide;
    check.setAttribute("aria-label", t("columns.visible"));
    check.addEventListener("change", () => setColumnVisible(field.key, check.checked));
    row.appendChild(check);

    const label = document.createElement("label");
    label.className = "column-control-label";
    const labelKey = getFieldI18nKey(field.key);
    label.textContent = labelKey ? t(labelKey) : field.label;
    label.addEventListener("click", () => {
      if (check.disabled) return;
      check.checked = !check.checked;
      setColumnVisible(field.key, check.checked);
    });
    row.appendChild(label);

    const actions = document.createElement("div");
    actions.className = "column-row-actions";

    const orderGroup = document.createElement("div");
    orderGroup.className = "column-action-set";
    orderGroup.appendChild(buildColumnIconButton("←", "columns.moveLeft", idx === 0, () => {
      moveColumnByStep(field.key, -1);
    }));
    orderGroup.appendChild(buildColumnIconButton("→", "columns.moveRight", idx === TABLE_FIELDS.length - 1, () => {
      moveColumnByStep(field.key, 1);
    }));
    actions.appendChild(orderGroup);

    const width = getColumnWidth(field.key);
    const fixedWidth = isFixedControlColumn(field.key);
    const widthGroup = document.createElement("div");
    widthGroup.className = "column-action-set column-action-set--width";
    widthGroup.appendChild(buildColumnIconButton("−", "columns.narrower", isPhoneViewport() || fixedWidth || width <= getColumnMinWidth(field.key), () => {
      adjustColumnWidth(field.key, -20);
    }));
    widthGroup.appendChild(buildColumnIconButton("+", "columns.wider", isPhoneViewport() || fixedWidth || width >= 520, () => {
      adjustColumnWidth(field.key, 20);
    }));
    actions.appendChild(widthGroup);

    row.appendChild(actions);

    list.appendChild(row);
  });
}

function getColumnControlFields() {
  const byKey = new Map(TABLE_FIELDS.map(field => [field.key, field]));
  const ordered = COLUMN_CONTROL_ORDER.map(key => byKey.get(key)).filter(Boolean);
  TABLE_FIELDS.forEach(field => {
    if (!ordered.includes(field)) ordered.push(field);
  });
  return ordered;
}

function buildColumnIconButton(text, labelKey, disabled, onClick) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "column-icon-btn";
  btn.textContent = text;
  btn.title = t(labelKey);
  btn.setAttribute("aria-label", t(labelKey));
  btn.disabled = disabled;
  btn.addEventListener("click", onClick);
  return btn;
}

function applyColumnControlStateChange({ renderRows = true } = {}) {
  const y = getTableScrollTop();
  syncHeaderOrderToTableFields();
  syncFieldPillOrder();
  syncColumnLayout();
  if (renderRows) renderTable(lastRenderRows, lastRenderTotal);
  updateSortIndicators();
  renderColumnControls();
  requestAnimationFrame(() => setTableScroll(y));
  saveColumnState();
}

function setColumnVisible(fieldKey, nextVisible) {
  if (!nextVisible) {
    if (tableViewMode === "lemmas" && fieldKey === "Texto estandarizado") {
      renderColumnControls();
      return;
    }
    const visibleCount = TABLE_FIELDS.filter(field => !hiddenColumns.has(field.key)).length;
    if (visibleCount <= 1) {
      renderColumnControls();
      return;
    }
    hiddenColumns.add(fieldKey);
  } else {
    hiddenColumns.delete(fieldKey);
  }
  sortKeys = sortKeys.filter(key => !hiddenColumns.has(key.field));
  applyColumnControlStateChange();
}

function moveColumnByStep(fieldKey, step) {
  const idx = TABLE_FIELDS.findIndex(field => field.key === fieldKey);
  const nextIdx = idx + step;
  if (idx < 0 || nextIdx < 0 || nextIdx >= TABLE_FIELDS.length) return;
  moveColumn(fieldKey, TABLE_FIELDS[nextIdx].key);
  renderColumnControls();
}

function adjustColumnWidth(fieldKey, delta) {
  if (isPhoneViewport()) return;
  if (isFixedControlColumn(fieldKey)) return;
  const next = Math.max(getColumnMinWidth(fieldKey), Math.min(520, getColumnWidth(fieldKey) + delta));
  columnWidths.set(fieldKey, next);
  applyColumnControlStateChange({ renderRows: false });
}

function resetColumnControls() {
  const byKey = new Map(TABLE_FIELDS.map(field => [field.key, field]));
  const ordered = COLUMN_CONTROL_ORDER.map(key => byKey.get(key)).filter(Boolean);
  if (ordered.length === TABLE_FIELDS.length) {
    TABLE_FIELDS.length = 0;
    ordered.forEach(field => TABLE_FIELDS.push(field));
  }
  hiddenColumns.clear();
  columnWidths.clear();
  DEFAULT_COLUMN_WIDTHS.forEach((width, key) => columnWidths.set(key, width));
  sortKeys = sortKeys.filter(key => TABLE_FIELDS.some(field => field.key === key.field));
  applyColumnControlStateChange();
}

function syncColumnLayout() {
  const visibleWidth = TABLE_FIELDS.reduce((sum, field) => {
    return hiddenColumns.has(field.key) ? sum : sum + getColumnWidth(field.key);
  }, 0);
  const isPhone = isPhoneViewport();
  const firstVisibleIdx = TABLE_FIELDS.findIndex(f => !hiddenColumns.has(f.key));
  const table = getBodyTable();
  if (table) {
    const hasFlexibleVisibleColumns = TABLE_FIELDS.some(field => (
      !hiddenColumns.has(field.key) && !isFixedControlColumn(field.key)
    ));
    const wrapperWidth = Math.ceil(table.parentElement?.clientWidth || 0);
    const layoutWidth = isPhone || !hasFlexibleVisibleColumns
      ? visibleWidth
      : Math.max(TABLE_MIN_WIDTH, visibleWidth, wrapperWidth);
    const layoutWidths = getLayoutColumnWidths(layoutWidth, visibleWidth);
    let colgroup = table.querySelector("colgroup");
    if (!colgroup) {
      colgroup = document.createElement("colgroup");
      table.insertBefore(colgroup, table.firstChild);
    }
    colgroup.innerHTML = "";
    TABLE_FIELDS.forEach((field, idx) => {
      const col = document.createElement("col");
      col.dataset.field = field.key;
      const width = layoutWidths.get(field.key) || getColumnWidth(field.key);
      col.style.width = `${width}px`;
      col.style.minWidth = `${width}px`;
      colgroup.appendChild(col);
      table.classList.toggle(`col-hidden-${idx}`, hiddenColumns.has(field.key));
    });
    table.style.width = isPhone ? "100%" : `${layoutWidth}px`;
    table.style.minWidth = isPhone ? "" : `${layoutWidth}px`;
    table.querySelectorAll("thead th.mobile-th-anchor")
      .forEach(th => th.classList.remove("mobile-th-anchor"));
    let mobileAnchorTh = null;
    if (isPhone && firstVisibleIdx >= 0) {
      const th = table.querySelector(`thead th:nth-child(${firstVisibleIdx + 1})`);
      if (th) {
        mobileAnchorTh = th;
        th.classList.add("mobile-th-anchor");
      }
    }
    syncTableHeaderActionSlots(table, mobileAnchorTh, isPhone);
  }
}

function getLayoutColumnWidths(layoutWidth, visibleWidth) {
  const widths = new Map(TABLE_FIELDS.map(field => [field.key, getColumnWidth(field.key)]));
  const extra = Math.max(0, layoutWidth - visibleWidth);
  if (!extra) return widths;

  const flexible = TABLE_FIELDS.filter(field => (
    !hiddenColumns.has(field.key) && !isFixedControlColumn(field.key)
  ));
  if (!flexible.length) return widths;

  const totalWeight = flexible.reduce((sum, field) => sum + Math.max(1, widths.get(field.key) || 1), 0);
  let remaining = extra;
  flexible.forEach((field, idx) => {
    const base = widths.get(field.key) || 0;
    const share = idx === flexible.length - 1
      ? remaining
      : Math.floor(extra * Math.max(1, base) / totalWeight);
    widths.set(field.key, base + share);
    remaining -= share;
  });
  return widths;
}

function syncTableHeaderActionSlots(table, mobileAnchorTh, isPhone) {
  if (!table) return;
  const mobileExpandAll = document.getElementById("tableExpandAllMobile");
  const commentExpandAll = document.getElementById("comentarioExpandAll");

  // These controls are actions, not data columns. Desktop anchors comment
  // actions to Comentario; mobile anchors the global expand action to the
  // one visible header.
  placeHeaderAction(commentExpandAll, getHeaderCellForField(table, "Comentario"));
  placeHeaderAction(
    mobileExpandAll,
    isPhone && mobileAnchorTh ? mobileAnchorTh : getHeaderCellForField(table, "Texto estandarizado")
  );
}

function getHeaderCellForField(table, fieldKey) {
  return Array.from(table.querySelectorAll("thead th"))
    .find(th => th.dataset.field === fieldKey) || null;
}

function placeHeaderAction(btn, th) {
  if (!btn || !th) return;
  const slot = th.querySelector(".header-actions");
  if (!slot) return;
  const sortBtn = slot.querySelector(".sort-btn");
  if (sortBtn) {
    if (sortBtn.nextElementSibling !== btn) sortBtn.after(btn);
  } else if (btn.parentElement !== slot) {
    slot.appendChild(btn);
  }
}

function setupStickyHeaderTable() {
  let raf = 0;
  window.addEventListener("resize", () => {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      syncColumnLayout();
      syncDataPanelViewAttribute();
      renderColumnControls();
      updateTableToggleButton();
      updateLemmaToggleButton();
    });
  });
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

function setCommentExpanded(rowId, contentEl, btnEl, expanded) {
  if (expanded) {
    expandedComments.add(rowId);
    contentEl.classList.add("collapsed");
    btnEl.textContent = "−";
    btnEl.setAttribute("aria-expanded", "true");
    btnEl.title = t("comentario.collapseRow");
    btnEl.setAttribute("aria-label", t("comentario.collapseRow"));
    contentEl.closest(".comentario-cell")?.classList.add("comentario-cell--expanded");
    return;
  }
  expandedComments.delete(rowId);
  commentAnchors.delete(rowId);
  removeComentarioDetailRow(rowId);
  contentEl.classList.add("collapsed");
  btnEl.textContent = "+";
  btnEl.setAttribute("aria-expanded", "false");
  btnEl.title = t("comentario.expandRow");
  btnEl.setAttribute("aria-label", t("comentario.expandRow"));
  contentEl.closest(".comentario-cell")?.classList.remove("comentario-cell--expanded");
}

function syncComentarioCell(meta) {
  const { rowId, content, btn } = meta;
  expandableComments.add(rowId);
  content.closest(".comentario-cell")?.classList.add("comentario-cell--detail-ready");
  setCommentExpanded(rowId, content, btn, expandedComments.has(rowId));
  return true;
}

function getExpandableRenderRows(rows = lastRenderRows) {
  return rows.filter(r => expandableComments.has(r._rid));
}

function areAllExpandableCommentsExpanded(rows = lastRenderRows) {
  return rows.length > 0 && rows.every(r => expandedComments.has(r._rid));
}

function getVisibleListRows(rows = lastRenderRows) {
  if (tableViewMode !== "rows") return [];
  return rows.filter(row => getMobileRowId(row) && rowHasDetailContent(row));
}

function areAllVisibleListRowsExpanded(rows = getVisibleListRows()) {
  return rows.length > 0 && rows.every(row => expandedMobileRows.has(getMobileRowId(row)));
}

function getRenderedLemmaNames() {
  const tbody = document.querySelector("#dataTable tbody");
  if (!tbody) return [];
  return Array.from(tbody.querySelectorAll("tr.lemma-group-row[data-lemma]"))
    .map(row => row.dataset.lemma)
    .filter(Boolean);
}

function getPagedLemmaNames() {
  const offsets = lastLemmaPageOffsets && lastLemmaPageOffsets.length
    ? lastLemmaPageOffsets : [0];
  const pageIdx = findLemmaPageIndex(displayOffset);
  const startIdx = offsets[pageIdx] || 0;
  const endIdx = pageIdx + 1 < offsets.length ? offsets[pageIdx + 1] : lastLemmaItems.length;
  return lastLemmaItems.slice(startIdx, endIdx).map(item => item.lemma);
}

function getVisibleLemmas() {
  if (tableViewMode !== "lemmas") return [];
  const rendered = getRenderedLemmaNames();
  return rendered.length ? rendered : getPagedLemmaNames();
}

function toggleVisibleListRows() {
  const rows = getVisibleListRows();
  if (!rows.length) return;
  const y = getTableScrollTop();
  if (areAllVisibleListRowsExpanded(rows)) {
    rows.forEach(row => expandedMobileRows.delete(getMobileRowId(row)));
  } else {
    rows.forEach(row => expandedMobileRows.add(getMobileRowId(row)));
  }
  renderTable(lastRenderRows, lastRenderTotal);
  requestAnimationFrame(() => {
    setTableScroll(y);
  });
}

function toggleVisibleLemmas() {
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
      if (toggleBtn) {
        toggleBtn.textContent = "+";
        toggleBtn.setAttribute("aria-expanded", "false");
      }
      removeLemmaDetailRows(tbody, lemma);
    } else if (!allExpanded && !isExpanded) {
      expandedLemmas.add(lemma);
      groupRow.classList.add("expanded");
      if (toggleBtn) {
        toggleBtn.textContent = "−";
        toggleBtn.setAttribute("aria-expanded", "true");
      }
      const item = lastLemmaItems.find(it => it.lemma === lemma);
      if (item) {
        const stripe = groupRow.classList.contains("stripe-alt");
        appendLemmaDetailRowsAfter(groupRow, item, stripe);
      }
    }
  });
  lastLemmaPageOffsets = computeLemmaPageOffsets(lastLemmaItems, maxDisplayRows);
  updatePaginationControls(lastLemmaItems.length);
  updateTableToggleButton();
  updateLemmaToggleButton();
}

function setupTableToggleAll() {
  const buttons = Array.from(document.querySelectorAll(".table-toggle-all"));
  if (!buttons.length) return;
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      if (tableViewMode === "lemmas") toggleVisibleLemmas();
      else toggleVisibleListRows();
    });
  });
}

function setupLemmaToggleAll() {
  const buttons = Array.from(document.querySelectorAll(".lemma-toggle-all"));
  if (!buttons.length) return;
  buttons.forEach(btn => btn.addEventListener("click", toggleVisibleLemmas));
}

function updateTableToggleButton() {
  const buttons = Array.from(document.querySelectorAll(".table-toggle-all"));
  if (!buttons.length) return;
  const isLemmaMode = tableViewMode === "lemmas";
  const items = isLemmaMode ? getVisibleLemmas() : getVisibleListRows();
  const shouldShow = items.length > 0;
  const allExpanded = shouldShow && (isLemmaMode
    ? items.every(lemma => expandedLemmas.has(lemma))
    : areAllVisibleListRowsExpanded(items));
  const labelKey = isLemmaMode ? "lemma.expandAll" : "list.expandAll";
  buttons.forEach(btn => {
    btn.hidden = !shouldShow;
    btn.disabled = !shouldShow;
    btn.textContent = allExpanded ? "−" : "+";
    btn.dataset.i18nTitle = labelKey;
    btn.dataset.i18nAriaLabel = labelKey;
    btn.title = t(labelKey);
    btn.setAttribute("aria-label", t(labelKey));
    btn.setAttribute("aria-pressed", allExpanded ? "true" : "false");
  });
}

function updateLemmaToggleButton() {
  const buttons = Array.from(document.querySelectorAll(".lemma-toggle-all"));
  if (!buttons.length) return;
  if (tableViewMode !== "lemmas") {
    buttons.forEach(btn => {
      btn.hidden = true;
      btn.setAttribute("aria-pressed", "false");
    });
    return;
  }
  const lemmas = getVisibleLemmas();
  if (!lemmas.length) {
    buttons.forEach(btn => {
      btn.hidden = false;
      btn.textContent = "+";
      btn.disabled = true;
      btn.setAttribute("aria-pressed", "false");
    });
    return;
  }
  const allExpanded = lemmas.every(l => expandedLemmas.has(l));
  buttons.forEach(btn => {
    btn.hidden = false;
    btn.disabled = false;
    btn.textContent = allExpanded ? "−" : "+";
    btn.setAttribute("aria-pressed", allExpanded ? "true" : "false");
  });
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
    btn.setAttribute("aria-pressed", "false");
    return;
  }
  btn.disabled = false;
  const allExpanded = areAllExpandableCommentsExpanded(expandableRows);
  btn.textContent = allExpanded ? "−" : "+";
  btn.setAttribute("aria-pressed", allExpanded ? "true" : "false");
}

function resetComentarioState() {
  expandedComments.clear();
  expandableComments.clear();
  commentAnchors.clear();
}

function paginateTo(mutateOffset) {
  const prev = displayOffset;
  pageScrollByOffset.set(prev, getTableScrollTop());
  const ok = mutateOffset();
  if (ok === false || displayOffset === prev) return;
  const restoreY = pageScrollByOffset.get(displayOffset) ?? 0;
  applyFilters(false, {
    keepOffset: true,
    keepCurrent: true,
    restoreScroll: restoreY,
  });
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
      paginateTo(() => {
        if (tableViewMode === "lemmas") {
          const pageIdx = findLemmaPageIndex(displayOffset);
          if (pageIdx <= 0) return false;
          displayOffset = lastLemmaPageOffsets[pageIdx - 1] || 0;
        } else {
          displayOffset = Math.max(0, displayOffset - maxDisplayRows);
        }
      });
    });
  };
  const hookNext = btn => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      paginateTo(() => {
        if (tableViewMode === "lemmas") {
          const pageIdx = findLemmaPageIndex(displayOffset);
          const next = lastLemmaPageOffsets[pageIdx + 1];
          if (next == null) return false;
          displayOffset = next;
        } else {
          displayOffset += maxDisplayRows;
        }
      });
    });
  };
  const hookFirst = btn => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      if (displayOffset === 0) return;
      paginateTo(() => { displayOffset = 0; });
    });
  };
  const hookLast = btn => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      if (!lastRenderTotal) return;
      paginateTo(() => {
        let maxOffset;
        if (tableViewMode === "lemmas") {
          maxOffset = lastLemmaPageOffsets[lastLemmaPageOffsets.length - 1] || 0;
        } else {
          const total = lastRenderTotal;
          maxOffset = Math.max(0, total - maxDisplayRows);
        }
        if (displayOffset === maxOffset) return false;
        displayOffset = maxOffset;
      });
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
      paginateTo(() => { displayOffset = newOffset; });
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
  if (pageTotal) pageTotal.textContent = t("page.total", { total: totalPages });
}

function setupSortControls() {
  const buttons = document.querySelectorAll("#dataTable .sort-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      const field = btn.dataset.sortField;
      if (!field) return;
      cycleSortField(field, e.shiftKey);
    });
  });
}

function cycleSortField(field, additive = false) {
  const y = getTableScrollTop();
  if (additive) {
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
}

function applyManualSort(arr, keys) {
  if (!keys || !keys.length) return;
  // Decorate-sort-undecorate: precompute keys once per row to avoid
  // recomputing them ~2N·log N times inside the comparator.
  const decorated = arr.map(row => {
    const ks = keys.map(({ field }) =>
      buildSortKey(String(getSortFieldValue(row, field)))
    );
    return { row, ks };
  });
  decorated.sort((a, b) => {
    for (let i = 0; i < keys.length; i += 1) {
      const cmp = alphaNumCollator.compare(a.ks[i], b.ks[i]);
      if (cmp !== 0) return keys[i].dir === "asc" ? cmp : -cmp;
    }
    return compareRecordId(a.row, b.row);
  });
  for (let i = 0; i < arr.length; i += 1) arr[i] = decorated[i].row;
}

function getSortFieldValue(row, field) {
  const isDisplayField = TABLE_FIELDS.some(entry => entry.key === field);
  if (field === "Fuente") return getFuenteSortKey(getDisplayValue(row, field));
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

  const sortA = getPrioritySortEntry(a);
  const sortB = getPrioritySortEntry(b);
  const headA = sortA.head;
  const headB = sortB.head;
  const headCmp = alphaNumCollator.compare(headA, headB);
  if (headCmp !== 0) return headCmp;

  const sourceCmp = alphaNumCollator.compare(sortA.source, sortB.source);
  if (sourceCmp !== 0) return sourceCmp;

  return compareRecordId(a, b);
}

function getPrioritySortEntry(row) {
  let entry = prioritySortCache.get(row);
  if (entry) return entry;
  entry = {
    head: buildSortKey(getDisplayValue(row, "Texto estandarizado") || getDisplayValue(row, "Escritura original")),
    source: getFuenteSortKey(getDisplayValue(row, "Fuente"))
  };
  prioritySortCache.set(row, entry);
  return entry;
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
    const headerSpan = btn.closest(".header-bar")?.querySelector("span");
    const fieldLabel = headerSpan?.textContent.trim() || field;
    btn.textContent = "";
    btn.classList.remove("sort-child");
    if (idx !== -1) {
      const dir = sortKeys[idx].dir;
      const arrow = dir === "asc" ? "↑" : "↓";
      btn.textContent = arrow;
      const dirLabel = dir === "asc" ? t("sort.asc") : t("sort.desc");
      btn.setAttribute("aria-label", `${t("sort.by")} ${fieldLabel}, ${dirLabel}`);
      btn.setAttribute("aria-pressed", "true");
      if (inLemmasView && field !== "Texto estandarizado") {
        btn.classList.add("sort-child");
        btn.title = t("sort.childHint");
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
      btn.setAttribute("aria-label", `${t("sort.by")} ${fieldLabel}`);
      btn.setAttribute("aria-pressed", "false");
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
    document.getElementById("columnMenuDropdown")?.classList.remove("open");
    dropdown.classList.toggle("open");
  });

  dropdown.addEventListener("click", e => {
    e.stopPropagation();
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
    if (tr.classList.contains("mobile-row-detail-row")) return;
    rows.push(
      Array.from(tr.cells)
        .filter((_, idx) => idx !== 4)
        .map(td => {
          const clone = td.cloneNode(true);
          clone.querySelectorAll(".mobile-row-toggle").forEach(el => el.remove());
          return (clone.innerText || clone.textContent || "").replace(/\s+/g, " ").trim();
        })
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
    setInlineLabelText(langToggle, wimmerShowEs ? "ES" : "FR");
    langToggle.classList.toggle("active", wimmerShowEs);
    langToggle.addEventListener("click", () => {
      wimmerShowEs = !wimmerShowEs;
      setInlineLabelText(langToggle, wimmerShowEs ? "ES" : "FR");
      langToggle.classList.toggle("active", wimmerShowEs);
      if (currentQueryUsesWimmerLanguage()) {
        applyFilters(false, getTableRestoreOptions());
      } else {
        renderTable(lastRenderRows, lastRenderTotal);
      }
    });
  }
}

const WIMMER_LANGUAGE_FIELDS = new Set(["Traducción", "Comentario"]);

function currentQueryUsesWimmerLanguage() {
  if (sortKeys.some(key => WIMMER_LANGUAGE_FIELDS.has(key.field))) return true;
  return activeFilters.some(filter => {
    if (WIMMER_LANGUAGE_FIELDS.has(filter.field)) return true;
    if (filter.type === "reverse") {
      const fields = Array.isArray(filter.fields) && filter.fields.length ? filter.fields : ["Traducción"];
      return fields.some(field => WIMMER_LANGUAGE_FIELDS.has(field));
    }
    return false;
  });
}

function sanitizeInput(value) {
  const raw = value == null ? "" : String(value);
  return stripHtmlTags(raw).trim();
}


// =============== Highlight ===============
// Compiled-regex cache: keyed by fieldKey, invalidated on filter/mode change.
let highlightCacheVersion = 0;
const highlightRegexCache = new Map();
function bumpHighlightCache() {
  highlightCacheVersion += 1;
  highlightRegexCache.clear();
}
function getHighlightRegexes(fieldKey, cellFilters) {
  const cached = highlightRegexCache.get(fieldKey);
  if (cached && cached.version === highlightCacheVersion) return cached;
  const entry = {
    version: highlightCacheVersion,
    regex: buildHighlightRegex(cellFilters),
    osRegex: oldSpanishMode ? buildOsHighlightRegex(cellFilters) : null,
  };
  highlightRegexCache.set(fieldKey, entry);
  return entry;
}

function applyHighlights(rawValue, fieldKey) {
  if (fieldKey === "Fuente") {
    return rawValue == null ? "" : String(rawValue);
  }
  const val = rawValue == null ? "" : String(rawValue);
  const allFilters = getHighlightFiltersForField(fieldKey);
  if (!allFilters.length) return val;

  const phraseFilters = allFilters.filter(f => normalizeScope(f.scope) === "phrase" && !f.negate);
  const wordFilters = allFilters.filter(f => normalizeScope(f.scope) === "word");
  const cellFilters = allFilters.filter(f => normalizeScope(f.scope) === "whole" && !f.negate);

  let rendered = val;

  if (phraseFilters.length) {
    rendered = applyPhraseHighlights(rendered, phraseFilters);
  }

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
    const { regex, osRegex } = getHighlightRegexes(fieldKey, cellFilters);
    if (regex || osRegex) {
      const parts = rendered.split(/(<[^>]+>)/g);
      const textPartIndexes = parts
        .map((part, idx) => /^<[^>]+>$/.test(part) ? -1 : idx)
        .filter(idx => idx >= 0);
      const firstTextPart = textPartIndexes[0];
      const lastTextPart = textPartIndexes[textPartIndexes.length - 1];
      rendered = parts
        .map((part, idx) => {
          if (/^<[^>]+>$/.test(part)) return part;
          const boundary = {
            isFirstText: idx === firstTextPart,
            isLastText: idx === lastTextPart
          };
          if (regex && osRegex) return highlightSegmentDual(part, regex, osRegex, boundary);
          if (regex) return highlightSegment(part, regex, boundary);
          return highlightSegment(part, osRegex, boundary);
        })
        .join("");
    }
  }

  return rendered;
}

function applyPhraseHighlights(value, filters) {
  const parts = String(value || "").split(/(<[^>]+>)/g);
  return parts
    .map(part => /^<[^>]+>$/.test(part) ? part : highlightPhraseTextSegment(part, filters))
    .join("");
}

function highlightPhraseTextSegment(text, filters) {
  if (!text || !filters.length) return text || "";
  const spans = [];
  filters.forEach(filter => {
    spans.push(...collectPhraseHighlightSpans(text, filter, "hl"));
    if (oldSpanishMode) {
      spans.push(...collectPhraseHighlightSpans(text, filter, "hl-os", { oldSpanish: true }));
    }
  });
  return wrapHighlightSpans(text, spans);
}

function collectPhraseHighlightSpans(text, filter, className, options = {}) {
  const query = buildFilterQuery(filter);
  const phraseQuery = queryMatchesMultiWordPhrase(query, filter.mode, query.allowLoose)
    ? query
    : buildLiteralPhraseQuery(filter, query);
  if (phraseQuery) {
    return collectPhraseSequenceSpans(text, filter, phraseQuery, className, options);
  }
  if (queryUsesPhraseWindowRegex(query)) {
    return collectPhraseRegexWindowSpans(text, filter, query, className, options);
  }
  return collectPhraseTokenSpans(text, filter, query, className, options);
}

function collectPhraseSequenceSpans(text, filter, query, className, options = {}) {
  const useLoose = query.allowLoose;
  const queryWords = splitSearchWords(useLoose ? query.loose : query.strict);
  if (queryWords.length < 2) return [];

  const tokens = tokenizeHighlightWords(text)
    .map(token => ({
      ...token,
      candidate: normalizeHighlightToken(token.raw, query, useLoose, options)
    }))
    .filter(token => token.candidate);
  if (tokens.length < queryWords.length) return [];

  const spans = [];
  const mode = query.effectiveMode || filter.mode;
  for (let i = 0; i <= tokens.length - queryWords.length; i++) {
    const windowTokens = tokens.slice(i, i + queryWords.length);
    const candidates = windowTokens.map(token => token.candidate);
    if (wordSequenceMatchesMode(candidates, queryWords, mode)) {
      spans.push({
        start: windowTokens[0].start,
        end: windowTokens[windowTokens.length - 1].end,
        className
      });
    }
  }
  return spans;
}

function collectPhraseRegexWindowSpans(text, filter, query, className, options = {}) {
  const useLoose = query.allowLoose;
  const tokens = tokenizeHighlightWords(text)
    .map(token => ({
      ...token,
      raw: normalizeHighlightToken(token.raw, query, false, options),
      loose: normalizeHighlightToken(token.raw, query, true, options)
    }))
    .filter(token => token.raw || token.loose);
  return findPhraseWindowMatches(tokens, filter, query, useLoose, { firstPerStart: true })
    .map(match => {
      const first = match.words[0];
      const last = match.words[match.words.length - 1];
      return {
        start: first.start,
        end: last.end,
        className
      };
    });
}

function collectPhraseTokenSpans(text, filter, query, className, options = {}) {
  const useLoose = query.allowLoose;
  return tokenizeHighlightWords(text)
    .filter(token => {
      const candidate = normalizeHighlightToken(token.raw, query, useLoose, options);
      return candidateMatchesQuery(candidate, query, filter.mode, useLoose);
    })
    .map(token => ({ start: token.start, end: token.end, className }));
}

function tokenizeHighlightWords(text) {
  const tokens = [];
  const rx = /\S+/g;
  let match;
  while ((match = rx.exec(text)) !== null) {
    tokens.push({
      raw: match[0],
      start: match.index,
      end: rx.lastIndex
    });
  }
  return tokens;
}

function normalizeHighlightToken(raw, query, useLoose, options = {}) {
  let base;
  if (options.oldSpanish) {
    base = normalizeOldSpanish(normalizeString(raw));
  } else {
    base = query.accentSensitive
      ? String(raw || "").normalize("NFC").toLowerCase()
      : normalizeString(raw);
  }
  return useLoose
    ? collapseWhitespace(stripPunctuationCharacters(base))
    : base;
}

function wrapHighlightSpans(text, spans) {
  if (!spans.length) return text;
  const ordered = spans
    .filter(span => span && span.end > span.start)
    .sort((a, b) => (
      a.start - b.start ||
      highlightClassPriority(a.className) - highlightClassPriority(b.className) ||
      b.end - a.end
    ));
  let result = "";
  let cursor = 0;
  ordered.forEach(span => {
    const start = Math.max(0, Math.min(text.length, span.start));
    const end = Math.max(0, Math.min(text.length, span.end));
    if (start < cursor || end <= start) return;
    result += text.slice(cursor, start);
    result += `<mark class="${span.className}">${text.slice(start, end)}</mark>`;
    cursor = end;
  });
  result += text.slice(cursor);
  return result;
}

function highlightClassPriority(className) {
  return className === "hl" ? 0 : 1;
}

function getHighlightFiltersForField(fieldKey) {
  return activeFilters
    .filter(filter => filter.value && highlightFilterAppliesToField(filter, fieldKey))
    .map(filter => filter.field === fieldKey ? filter : { ...filter, field: fieldKey });
}

function highlightFilterAppliesToField(filter, fieldKey) {
  if (filter.field === fieldKey) return true;
  return Array.isArray(filter.fields) && filter.fields.includes(fieldKey);
}

function reverseOsExpand(str) {
  let result = "";
  for (let i = 0; i < str.length; i++) {
    const ch = str[i];
    if (ch === "b") result += "[bv]";
    else if (ch === "j") result += "[jx]";
    else if (ch === "f") result += "(?:f|ph)";
    else if (ch === "t") result += "(?:t|th)";
    else if (ch === "c") result += "(?:c|qu)";
    else if (ch === "n") result += "(?:n|nn)";
    else if (ch === "s") result += "(?:s|ss)";
    else result += escapeRegex(ch);
  }
  return result;
}

function reverseOsExpandPatternSource(src) {
  const source = String(src || "");
  let out = "";
  let escaped = false;
  let inClass = false;
  for (const ch of source) {
    if (escaped) {
      out += ch;
      escaped = false;
      continue;
    }
    if (ch === "\\") {
      out += ch;
      escaped = true;
      continue;
    }
    if (inClass) {
      out += ch;
      if (ch === "]") inClass = false;
      continue;
    }
    if (ch === "[") {
      out += ch;
      inClass = true;
      continue;
    }
    if (ch === "b") out += "[bv]";
    else if (ch === "j") out += "[jx]";
    else if (ch === "f") out += "(?:f|ph)";
    else if (ch === "t") out += "(?:t|th)";
    else if (ch === "c") out += "(?:c|qu)";
    else if (ch === "n") out += "(?:n|nn)";
    else if (ch === "s") out += "(?:s|ss)";
    else out += ch;
  }
  return out;
}

function buildOsHighlightRegex(filters) {
  const sources = [];
  filters.forEach(filter => {
    const rawVal = (filter.value ?? "").trim();
    if (/^\/(.+)\/([gimsuy]*)$/.test(rawVal)) return;
    if (rawVal.startsWith("(") && rawVal.includes("||")) return;
    const parsed = parseFilterValue(rawVal, filter.mode, { field: filter.field });
    if (!parsed || parsed.hasRegex || parsed.hasWildcards) return;
    const literal = parsed.strict || parsed.loose;
    if (!literal) return;
    const expanded = reverseOsExpand(literal);
    const mode = parsed.effectiveMode || filter.mode;
    const relaxed = normalizePatternSource(anchorHighlightSource(expanded, mode, { allowLoose: parsed.allowLoose }));
    sources.push(relaxed);
  });
  if (!sources.length) return null;
  try {
    return new RegExp(`(${sources.join("|")})`, "gi");
  } catch {
    return null;
  }
}

function highlightSegmentDual(text, normalRegex, osRegex, boundary = {}) {
  let combined;
  try {
    combined = new RegExp(`(${normalRegex.source})|(${osRegex.source})`, "gi");
  } catch {
    return highlightSegment(text, normalRegex, boundary);
  }
  const normalizedText = normalRegex.accentSensitive ? text.toLowerCase() : normalizeString(text);
  const { candidate, textStart, textEnd } = buildHighlightCandidate(normalizedText, boundary);
  const trimLooseEdges = !!(normalRegex.trimLooseEdges || osRegex.trimLooseEdges);
  let result = "";
  let lastIndex = 0;
  combined.lastIndex = 0;
  let match;
  while ((match = combined.exec(candidate)) !== null) {
    let start = Math.max(0, Math.min(text.length, match.index - textStart));
    let end = Math.max(0, Math.min(text.length, combined.lastIndex - textStart));
    if (combined.lastIndex <= textStart || match.index >= textEnd || end <= start) {
      if (match[0].length === 0) combined.lastIndex++;
      continue;
    }
    if (trimLooseEdges) {
      ({ start, end } = trimLooseHighlightEdgeSpan(text, start, end));
      if (end <= start) {
        if (match[0].length === 0) combined.lastIndex++;
        continue;
      }
    }
    if (start < lastIndex) start = lastIndex;
    if (end <= lastIndex) {
      if (match[0].length === 0) combined.lastIndex++;
      continue;
    }
    result += text.slice(lastIndex, start);
    const cssClass = match[1] !== undefined ? "hl" : "hl-os";
    result += `<mark class="${cssClass}">${text.slice(start, end)}</mark>`;
    lastIndex = end;
    if (match[0].length === 0) combined.lastIndex++;
  }
  result += text.slice(lastIndex);
  return result;
}

const HIGHLIGHT_BOUNDARY_SENTINEL = "\uE000";
const LOOSE_HIGHLIGHT_EDGE = "[^0-9A-Za-z\\u00C0-\\u024F\\u1E00-\\u1EFF\\uE000]*";

function anchorHighlightSource(src, mode, options = {}) {
  const looseEdge = options.allowLoose ? LOOSE_HIGHLIGHT_EDGE : "";
  if (mode === "exact") {
    return options.allowLoose
      ? `^${looseEdge}(?:${src})(?=${looseEdge}$)`
      : `^(?:${src})$`;
  }
  if (mode === "starts") {
    return options.allowLoose
      ? `^${looseEdge}(?:${src})`
      : `^(?:${src})`;
  }
  if (mode === "ends") {
    return options.allowLoose
      ? `(?:${src})(?=${looseEdge}$)`
      : `(?:${src})$`;
  }
  return src;
}

function relaxLooseHighlightAnchors(src, mode, allowLoose) {
  if (!allowLoose) return src;
  if (mode === "exact") {
    return src.replace(/^\^/, `^${LOOSE_HIGHLIGHT_EDGE}`).replace(/\$$/, `(?=${LOOSE_HIGHLIGHT_EDGE}$)`);
  }
  if (mode === "starts") {
    return src.replace(/^\^/, `^${LOOSE_HIGHLIGHT_EDGE}`);
  }
  if (mode === "ends") {
    return src.replace(/\$$/, `(?=${LOOSE_HIGHLIGHT_EDGE}$)`);
  }
  return src;
}

// Normalize a regex pattern source for accent-insensitive matching.
// Preserve regex escapes: lowercasing/normalizing `\W` into `\w` changes the
// meaning and breaks phrase highlights such as "estar con" -> `estar\W*con`.
// Character classes are left untouched because normalizing their internals can
// change range/class semantics.
function normalizePatternSource(src) {
  const source = String(src || "");
  let out = "";
  let escaped = false;
  let inClass = false;
  for (const ch of source) {
    if (escaped) {
      out += ch;
      escaped = false;
      continue;
    }
    if (ch === "\\") {
      out += ch;
      escaped = true;
      continue;
    }
    if (inClass) {
      out += ch;
      if (ch === "]") inClass = false;
      continue;
    }
    if (ch === "[") {
      out += ch;
      inClass = true;
      continue;
    }
    out += normalizeString(ch);
  }
  return out;
}

function buildHighlightRegex(filters) {
  const sources = [];
  let isAccentSensitive = false;
  let trimLooseEdges = false;
  filters.forEach(filter => {
    const rawVal = (filter.value ?? "").trim();
    const andParts = extractContainsBothParts(rawVal);
    if (andParts && andParts.length) {
      if (accentSensitiveMode) isAccentSensitive = true;
      andParts.forEach(p => {
        const sourcePart = (!accentSensitiveMode && oldSpanishMode)
          ? normalizeOldSpanishPatternText(p)
          : p;
        const expanded = expandReduplicationMarkers(sourcePart, { field: filter.field })
          || convertWildcardPatternAllowRegex(expandVCPlaceholders(sourcePart), { field: filter.field });
        if (expanded) {
          let adjusted = accentSensitiveMode ? expanded : normalizePatternSource(expanded);
          if (!accentSensitiveMode && oldSpanishMode) {
            adjusted = reverseOsExpandPatternSource(adjusted);
          }
          sources.push(adjusted);
        }
      });
      return;
    }
    const parsed = parseFilterValue(filter.value ?? "", filter.mode, { field: filter.field });
    if (parsed.accentSensitive) isAccentSensitive = true;
    const mode = parsed.effectiveMode || filter.mode;
    if (parsed.allowLoose && ["exact", "starts", "ends"].includes(mode)) {
      trimLooseEdges = true;
    }
    let rx = parsed.strictRegex || parsed.looseRegex;
    let rxHasLooseEdges = false;
    if (!rx) {
      const literal = parsed.strict || parsed.loose;
      if (literal) {
        const pattern = anchorHighlightSource(
          escapeRegex(String(literal)).replace(/\s+/g, "\\W*"),
          mode,
          { allowLoose: parsed.allowLoose }
        );
        rx = new RegExp(pattern, "i");
        rxHasLooseEdges = !!parsed.allowLoose;
      }
    }
    if (!rx) return;
    const relaxed = rxHasLooseEdges
      ? rx.source
      : relaxLooseHighlightAnchors(
          rx.source,
          mode,
          parsed.allowLoose
        );
    // Accent-sensitive queries: lowercase the pattern but preserve accents.
    // Plain queries: full normalization (accent-blind).
    const adjusted = parsed.accentSensitive
      ? relaxed.toLowerCase()
      : normalizePatternSource(relaxed);
    sources.push(
      !parsed.accentSensitive && oldSpanishMode
        ? reverseOsExpandPatternSource(adjusted)
        : adjusted
    );
  });
  if (!sources.length) return null;
  try {
    const rx = new RegExp(`(${sources.join("|")})`, "gi");
    rx.accentSensitive = isAccentSensitive;
    rx.trimLooseEdges = trimLooseEdges;
    return rx;
  } catch {
    return null;
  }
}

function highlightSegment(text, regex, boundary = {}) {
  // For accent-sensitive queries: match on lowercase-only text (preserve accents).
  // For plain queries: match on fully-normalized text (accent-blind).
  // In both cases, positions map 1-to-1 back to the original displayed text.
  const normalizedText = regex.accentSensitive ? text.toLowerCase() : normalizeString(text);
  const { candidate, textStart, textEnd } = buildHighlightCandidate(normalizedText, boundary);
  let result = "";
  let lastIndex = 0;
  regex.lastIndex = 0;
  let match;
  while ((match = regex.exec(candidate)) !== null) {
    let start = Math.max(0, Math.min(text.length, match.index - textStart));
    let end = Math.max(0, Math.min(text.length, regex.lastIndex - textStart));
    if (regex.lastIndex <= textStart || match.index >= textEnd || end <= start) {
      if (match[0].length === 0) regex.lastIndex++;
      continue;
    }
    if (regex.trimLooseEdges) {
      ({ start, end } = trimLooseHighlightEdgeSpan(text, start, end));
      if (end <= start) {
        if (match[0].length === 0) regex.lastIndex++;
        continue;
      }
    }
    if (start < lastIndex) start = lastIndex;
    if (end <= lastIndex) {
      if (match[0].length === 0) regex.lastIndex++;
      continue;
    }
    result += text.slice(lastIndex, start);
    result += `<mark class="hl">${text.slice(start, end)}</mark>`;
    lastIndex = end;
    if (match[0].length === 0) regex.lastIndex++;
  }
  result += text.slice(lastIndex);
  return result;
}

function trimLooseHighlightEdgeSpan(text, start, end) {
  while (start < end && isLooseHighlightEdgeChar(text[start])) start++;
  while (end > start && isLooseHighlightEdgeChar(text[end - 1])) end--;
  return { start, end };
}

function isLooseHighlightEdgeChar(ch) {
  return !/[0-9A-Za-z\u00C0-\u024F\u1E00-\u1EFF]/.test(ch || "");
}

function buildHighlightCandidate(normalizedText, boundary = {}) {
  const prefix = boundary.isFirstText === false ? HIGHLIGHT_BOUNDARY_SENTINEL : "";
  const suffix = boundary.isLastText === false ? HIGHLIGHT_BOUNDARY_SENTINEL : "";
  const candidate = `${prefix}${normalizedText}${suffix}`;
  const textStart = prefix.length;
  return {
    candidate,
    textStart,
    textEnd: textStart + normalizedText.length
  };
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
        adjRx.lastIndex = 0;
        return adjRx.test(candidate);
      } catch {
        query.strictRegex.lastIndex = 0;
        return query.strictRegex.test(candidate);
      }
    }
    return candidateMatchesQuery(candidate, query, filter.mode, query.allowLoose);
  };
  const { groups, singles } = partitionWordFiltersByGroup(filters);
  for (const group of groups.values()) {
    if (wordFilterGroupMatchesForHighlight(group, testFilter)) return true;
  }
  return singles.some(filter => !filter.negate && testFilter(filter));
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
    if (wordFilterGroupMatchesForHighlight(group, testFilter)) return true;
  }
  return singles.some(filter => !filter.negate && testFilter(filter));
}

function wordFilterGroupMatchesForHighlight(filters, testFilter) {
  const segments = new Map();
  let hasInclude = false;
  filters.forEach(filter => {
    const type = mapModeToWordRowType(filter.mode);
    if (!segments.has(type)) segments.set(type, { include: [], exclude: [] });
    const segment = segments.get(type);
    if (filter.negate) {
      segment.exclude.push(filter);
    } else {
      hasInclude = true;
      segment.include.push(filter);
    }
  });
  if (!hasInclude) return false;
  for (const segment of segments.values()) {
    if (segment.exclude.some(testFilter)) return false;
    if (segment.include.length && !segment.include.some(testFilter)) return false;
  }
  return true;
}

function extractContainsBothParts(text) {
  if (!text || !text.startsWith("(") || !text.endsWith(")")) return null;
  if (!text.includes("||")) return null;
  return splitTopLevel(text.slice(1, -1), "||");
}

// =============== Fuentes =================
function splitFuenteLabel(name) {
  const m = name.match(/^(\S+)(?:\s+(\?))?\s+(.+)$/);
  if (m && /\d/.test(m[1])) {
    return { year: [m[1], m[2]].filter(Boolean).join(" "), title: m[3] };
  }
  return { year: "", title: name };
}

function normalizeFuenteSortText(value) {
  return String(value || "")
    .replace(/[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+/g, "")
    .trim();
}

function getFuenteSortKey(name) {
  const { year, title } = splitFuenteLabel(String(name || ""));
  return [title, year]
    .map(part => normalizeFuenteSortText(part) || buildSortKey(part))
    .filter(Boolean)
    .join(" ");
}

function compareFuenteNames(a, b) {
  return alphaNumCollator.compare(getFuenteSortKey(a), getFuenteSortKey(b));
}

function loadFuenteOrderMode() {
  try {
    const saved = localStorage.getItem(FUENTE_ORDER_KEY);
    if (saved === "year" || saved === "title") fuenteOrderMode = saved;
  } catch {}
}

function saveFuenteOrderMode() {
  try {
    localStorage.setItem(FUENTE_ORDER_KEY, fuenteOrderMode);
  } catch {}
}

function getFuenteDisplayOptions() {
  if (fuenteOrderMode === "year") return FUENTE_OPTIONS.slice();
  return FUENTE_OPTIONS.slice().sort(compareFuenteNames);
}

function syncFuenteOrderControls() {
  document.querySelectorAll("[data-fuente-order]").forEach(btn => {
    const active = btn.dataset.fuenteOrder === fuenteOrderMode;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-pressed", String(active));
  });
}

function setFuenteOrderMode(mode) {
  const next = mode === "year" ? "year" : "title";
  if (fuenteOrderMode === next) {
    syncFuenteOrderControls();
    return;
  }
  fuenteOrderMode = next;
  saveFuenteOrderMode();
  syncFuenteOrderControls();
  renderFuenteList();
}

function setupFuenteOrderControls() {
  document.querySelectorAll("[data-fuente-order]").forEach(btn => {
    btn.addEventListener("click", () => setFuenteOrderMode(btn.dataset.fuenteOrder));
  });
  syncFuenteOrderControls();
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
  getFuenteDisplayOptions().forEach(name => {
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
  setupFuenteOrderControls();
  const fillBtn = document.getElementById("fuenteFill");
  if (fillBtn) {
    fillBtn.addEventListener("click", () => {
      selectedFuentes.clear();
      DEFAULT_FUENTE_OPTIONS.forEach(name => selectedFuentes.add(name));
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
  if (options.preserveExpandState) {
    expandableComments.clear();
    commentAnchors.clear();
  } else {
    resetComentarioState();
  }
  const totalOptions = FUENTE_OPTIONS.length;
  const selectedCount = selectedFuentes.size;
  // Si no hay selección, se filtra todo afuera (sin coincidencias).
  if (selectedCount === 0) {
    lastFilteredRows = [];
    lastRenderRows = [];
    lastRenderTotal = 0;
    lastLemmaItems = [];
    renderTable([], 0);
    updateStudyScope();
    updateUrlHash();
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
  return getNormalizedTextVariant(row, "Traducción", { loose: true, oldSpanish: false });
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
      toggle.setAttribute("aria-label", t("toggle.expandCollapse"));
      toggle.setAttribute("aria-expanded", expandedLemmas.has(item.lemma) ? "true" : "false");
      toggle.textContent = expandedLemmas.has(item.lemma) ? "−" : "+";
      wrap.appendChild(toggle);

      const title = document.createElement("span");
      title.className = "lemma-title";
      title.textContent = item.lemma;
      wrap.appendChild(title);

      const count = document.createElement("span");
      count.className = "lemma-count";
      count.textContent = `(${item.rowCount})`;
      count.title = t("browse.meta.entries", { rows: item.rowCount });
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
    td.textContent = "";
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
    if (toggleBtn) {
      toggleBtn.textContent = "+";
      toggleBtn.setAttribute("aria-expanded", "false");
    }
    removeLemmaDetailRows(tbody, lemma);
  } else {
    expandedLemmas.add(lemma);
    groupRow.classList.add("expanded");
    if (toggleBtn) {
      toggleBtn.textContent = "−";
      toggleBtn.setAttribute("aria-expanded", "true");
    }
    const item = lastLemmaItems.find(it => it.lemma === lemma);
    if (item) {
      const stripe = groupRow.classList.contains("stripe-alt");
      appendLemmaDetailRowsAfter(groupRow, item, stripe);
    }
  }
  lastLemmaPageOffsets = computeLemmaPageOffsets(lastLemmaItems, maxDisplayRows);
  updatePaginationControls(lastLemmaItems.length);
  updateTableToggleButton();
  updateLemmaToggleButton();
}

// ── View-mode helpers (rows / lemmas) ─────────────────────────────────

function syncDataPanelViewAttribute() {
  const panel = document.querySelector(".data-panel");
  if (!panel) return;
  const viewport = isPhoneViewport() ? "mobile" : "desktop";
  panel.dataset.viewMode = tableViewMode;
  panel.dataset.tableViewport = viewport;
  panel.dataset.tableContext = `${viewport}-${tableViewMode}`;
}

function updateViewToggleButtons() {
  document.querySelectorAll(".view-btn[data-view]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.view === tableViewMode);
  });
}

function updateViewToggleLabels() {
  updateViewToggleButtons();
  updatePageSizeLabel();
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
  updatePageSizeLabel();
  renderColumnControls();
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

// ── Guided filters (intention shortcuts that create normal chips) ────

function hasReverseChip() {
  return activeFilters.some(f => f.owner === REVERSE_OWNER);
}

function presetNeedsInput(preset) {
  return preset?.requiresInput !== false;
}

function buildGuidedFilterSpecs(preset, value, options = {}) {
  if (!preset) return [];
  if (Array.isArray(preset.filters)) return preset.filters.slice();
  if (!presetNeedsInput(preset) || !value) return [];
  const inputValue = preset.valuePrefix ? `${preset.valuePrefix}${value}` : value;
  const fields = options.includeComment && Array.isArray(preset.commentFields)
    ? preset.commentFields
    : [preset.field];
  return [{
    field: preset.field,
    mode: preset.mode,
    scope: preset.scope,
    value: inputValue,
    fields: fields.length > 1 ? fields : null
  }];
}

function orderColumnsForGuidedPresentation(columns) {
  if (!Array.isArray(columns) || !columns.length) return;
  const byKey = new Map(TABLE_FIELDS.map(field => [field.key, field]));
  const orderedKeys = [];
  columns.forEach(key => {
    if (byKey.has(key) && !orderedKeys.includes(key)) orderedKeys.push(key);
  });
  DEFAULT_COLUMN_ORDER.forEach(key => {
    if (byKey.has(key) && !orderedKeys.includes(key)) orderedKeys.push(key);
  });
  if (orderedKeys.length !== TABLE_FIELDS.length) return;
  TABLE_FIELDS.length = 0;
  orderedKeys.forEach(key => TABLE_FIELDS.push(byKey.get(key)));
  syncHeaderOrderToTableFields();
  syncFieldPillOrder();
}

function applyGuidedPresentation(preset) {
  if (!preset) return;
  if (preset.viewMode === "lemmas" || preset.viewMode === "rows") {
    tableViewMode = preset.viewMode;
    updateViewToggleButtons();
  }
  if (Array.isArray(preset.visibleColumns) && preset.visibleColumns.length) {
    orderColumnsForGuidedPresentation(preset.visibleColumns);
    const visible = new Set(preset.visibleColumns);
    hiddenColumns.clear();
    TABLE_FIELDS.forEach(field => {
      if (!visible.has(field.key)) hiddenColumns.add(field.key);
    });
    if (tableViewMode === "lemmas") hiddenColumns.delete("Texto estandarizado");
    sortKeys = sortKeys.filter(key => !hiddenColumns.has(key.field));
    syncColumnLayout();
    renderColumnControls();
  }
}

function setReverseChip(query, options = {}) {
  const presetKey = REVERSE_PRESETS[options.preset] ? options.preset : currentReversePreset;
  const preset = REVERSE_PRESETS[presetKey] || REVERSE_PRESETS.translationToEdition;
  const val = sanitizeInput(query).trim();
  activeFilters = activeFilters.filter(f => f.owner !== REVERSE_OWNER);
  groupOrder = groupOrder.filter(g => g.id !== REVERSE_OWNER);
  if (presetNeedsInput(preset) && !val) {
    renderActiveFilterChips();
    applyFilters();
    return;
  }
  const specs = buildGuidedFilterSpecs(preset, val, options);
  specs.forEach(spec => {
    const fields = Array.isArray(spec.fields) && spec.fields.length > 1 ? spec.fields : null;
    const extras = {
      owner: REVERSE_OWNER,
      reversePreset: presetKey
    };
    if (fields) {
      extras.type = "reversePreset";
      extras.fields = fields;
    }
    appendFilter(
      spec.field,
      spec.mode,
      spec.value,
      spec.logic || "AND",
      !!spec.negate,
      spec.scope || "whole",
      extras
    );
  });
  if (specs.length) groupOrder.push({ id: REVERSE_OWNER, logic: "AND" });
  applyGuidedPresentation(preset);
  displayOffset = 0;
  renderActiveFilterChips();
  applyFilters();
}

function removeReverseChip() {
  if (!hasReverseChip()) return;
  activeFilters = activeFilters.filter(f => f.owner !== REVERSE_OWNER);
  groupOrder = groupOrder.filter(g => g.id !== REVERSE_OWNER);
  renderActiveFilterChips();
  applyFilters();
}

function setupReverseLookup() {
  const input = document.getElementById("reverseInput");
  const submit = document.getElementById("reverseSubmit");
  const clear = document.getElementById("reverseClear");
  const includeComment = document.getElementById("reverseIncludeComment");
  const objective = document.getElementById("reverseObjective");
  const presetsList = document.getElementById("reversePresetsList");
  if (!input || !submit) return;
  if (presetsList) {
    presetsList.innerHTML = Object.entries(REVERSE_PRESETS).map(([id, preset]) => {
      const count = Number.isFinite(preset.count) ? `<span class="reverse-preset-count">≈${escapeHtml(preset.count)}</span>` : "";
      return `
        <button type="button" class="reverse-preset-btn" data-reverse-preset="${escapeHtml(id)}">
          ${count}
          <span class="reverse-preset-title" data-i18n="${escapeHtml(preset.titleKey)}">${escapeHtml(t(preset.titleKey))}</span>
          <span class="reverse-preset-objective" data-i18n="${escapeHtml(preset.goalKey)}">${escapeHtml(t(preset.goalKey))}</span>
        </button>`;
    }).join("");
  }
  const presetButtons = Array.from(document.querySelectorAll("[data-reverse-preset]"));

  function setPreset(next) {
    currentReversePreset = REVERSE_PRESETS[next] ? next : "translationToEdition";
    presetButtons.forEach(btn => {
      btn.classList.toggle("active", btn.dataset.reversePreset === currentReversePreset);
    });
    const preset = REVERSE_PRESETS[currentReversePreset];
    const needsInput = presetNeedsInput(preset);
    if (objective && preset?.objectiveKey) {
      objective.dataset.i18n = preset.objectiveKey;
      objective.textContent = t(preset.objectiveKey);
    }
    if (input) {
      input.hidden = !needsInput;
      input.disabled = !needsInput;
      if (!needsInput) {
        input.value = "";
        delete input.dataset.i18nPlaceholder;
        input.removeAttribute("placeholder");
      } else if (preset?.placeholderKey) {
        input.dataset.i18nPlaceholder = preset.placeholderKey;
        input.setAttribute("placeholder", t(preset.placeholderKey));
      }
    }
    const canIncludeComment = !!(preset && preset.commentFields);
    if (includeComment) {
      includeComment.disabled = !canIncludeComment;
      if (!canIncludeComment) includeComment.checked = false;
      const opt = includeComment.closest(".reverse-field-opt");
      opt?.classList.toggle("is-disabled", !canIncludeComment);
      if (opt) opt.hidden = !canIncludeComment;
    }
    setButtonState(submit, needsInput ? "reverse.submit" : "reverse.apply", "icon-search");
  }

  function run() {
    const preset = REVERSE_PRESETS[currentReversePreset];
    const query = presetNeedsInput(preset) ? input.value.trim() : "";
    if (presetNeedsInput(preset) && !query) {
      removeReverseChip();
      return;
    }
    setReverseChip(query, {
      includeComment: !!(includeComment && includeComment.checked && preset?.commentFields),
      preset: currentReversePreset
    });
  }

  presetButtons.forEach(btn => {
    btn.addEventListener("click", () => setPreset(btn.dataset.reversePreset));
  });
  setPreset(currentReversePreset);

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
    const mobileToggle = e.target.closest(".mobile-row-toggle");
    if (mobileToggle) {
      e.stopPropagation();
      toggleMobileRowDetail(mobileToggle.closest("tr"));
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
    // Phone-only: tapping anywhere on the anchor cell expands the row.
    if (cell.classList.contains("mobile-row-anchor-cell")
        && window.matchMedia
        && window.matchMedia("(max-width: 640px)").matches
        && !e.target.closest("button, a, input, select, textarea, mark")) {
      toggleMobileRowDetail(tr);
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
    const sources = [...sourceSet].sort(compareFuenteNames);
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
    const { tr, comentarioMeta } = buildDataRow(row);
    tr.classList.add("lemma-detail-row");
    tr.dataset.lemma = item.lemma;
    if (stripe) tr.classList.add("stripe-alt");
    const edicionCell = tr.querySelector('td[data-field="Texto estandarizado"]');
    if (edicionCell) {
      const mobileToggle = edicionCell.querySelector(".mobile-row-toggle");
      edicionCell.replaceChildren();
      if (mobileToggle) edicionCell.appendChild(mobileToggle);
      edicionCell.appendChild(buildLemmaMobileDetailPreview(row));
    }
    anchor.after(tr);
    anchor = tr;
    anchor = appendMobileDetailRowAfter(anchor, row);
    if (comentarioMeta && syncComentarioCell(comentarioMeta)) {
      anchor = appendComentarioDetailRowAfter(anchor, row);
    }
  });
}

function buildLemmaMobileDetailPreview(row) {
  const preview = document.createElement("div");
  preview.className = "lemma-mobile-detail-preview";

  const addLine = (className, fieldKey) => {
    const raw = getDisplayValue(row, fieldKey);
    const safe = raw == null ? "" : String(raw).trim();
    if (!safe) return;
    const line = document.createElement("div");
    line.className = className;
    line.dataset.field = fieldKey;
    line.innerHTML = applyHighlights(safe, fieldKey);
    preview.appendChild(line);
  };

  addLine("lemma-mobile-detail-primary", "Escritura original");
  addLine("mobile-row-subtitle mobile-row-sub--traduccion", "Traducción");
  addLine("mobile-row-subtitle mobile-row-sub--fuente", "Fuente");

  return preview;
}

function removeLemmaDetailRows(tbody, lemma) {
  tbody.querySelectorAll(`tr.lemma-detail-row[data-lemma="${CSS.escape(lemma)}"]`)
    .forEach(tr => tr.remove());
}

function computeLemmaPageOffsets(items, pageSize) {
  if (!items.length || pageSize <= 0) return [0];
  const offsets = [0];
  for (let i = pageSize; i < items.length; i += pageSize) {
    offsets.push(i);
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
  updateScrollNavBadges({ resultCount: total });
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

// ── Flashcard study mode ──────────────────────────────────────────
let studyEntityDecoder = null;

function decodeStudyEntities(value) {
  if (!studyEntityDecoder) studyEntityDecoder = document.createElement("textarea");
  studyEntityDecoder.innerHTML = String(value ?? "");
  return studyEntityDecoder.value;
}

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

function isStudyLeakyToken(token, forms) {
  return isStudyLeakyKey(getStudyLeakKey(token), forms);
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

function getStudyLimit() {
  const value = parseInt(document.getElementById("studyLimit")?.value || "50", 10);
  return Number.isFinite(value) && value > 0 ? value : 50;
}

function getStudyDirection() {
  const value = document.getElementById("studyDirection")?.value;
  return value === "spanishToNahuatl" ? value : "nahuatlToSpanish";
}

function getStudyMode() {
  return studyMode === "exam" ? "exam" : "study";
}

function getStudyViewMode() {
  return studyViewMode === "both" ? "both" : "flip";
}

function resetStudyAnswerState() {
  studyAnswerVisible = false;
}

function setStudyMode(nextMode) {
  studyMode = nextMode === "exam" ? "exam" : "study";
  resetStudyAnswerState();
  syncStudyModeButtons();
  syncStudyViewButtons();
  renderStudyCard();
}

function setStudyViewMode(nextMode) {
  studyViewMode = nextMode === "both" ? "both" : "flip";
  resetStudyAnswerState();
  syncStudyViewButtons();
  renderStudyCard();
}

function syncStudyModeButtons() {
  document.querySelectorAll(".study-mode-btn[data-study-mode]").forEach(btn => {
    const active = btn.dataset.studyMode === getStudyMode();
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function syncStudyViewButtons() {
  const control = document.getElementById("studyViewControl");
  if (control) control.hidden = getStudyMode() !== "study";
  document.querySelectorAll(".study-mode-btn[data-study-view]").forEach(btn => {
    const active = btn.dataset.studyView === getStudyViewMode();
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function getStudyRows() {
  const useCurrent = document.getElementById("studyUseFilters")?.checked ?? true;
  if (useCurrent) return Array.isArray(lastFilteredRows) ? lastFilteredRows.slice() : [];
  return dataRows.filter(row => selectedFuentes.has(row.Fuente));
}

function addStudyTranslation(entry, translation) {
  const normalized = normalizeString(translation);
  if (!normalized) return;
  const existing = entry.translationStats.get(normalized);
  if (existing) existing.count += 1;
  else entry.translationStats.set(normalized, { display: translation, count: 1, normalized });
}

function buildStudyCardsFromRows(rows, options = {}) {
  const shortOnly = !!options.shortOnly;
  const direction = options.direction || "nahuatlToSpanish";
  const byLemma = new Map();
  const sortedRows = rows.slice().sort(comparePriorityOrder);

  sortedRows.forEach(row => {
    const lemma = cleanStudyText(getDisplayValue(row, "Texto estandarizado"));
    const translation = getStudyCardTranslation(row, lemma, direction);
    if (!lemma || !translation) return;
    if (shortOnly && translation.length > 180) return;
    const key = normalizeString(lemma);
    if (!key) return;
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
          if (b.count !== a.count) return b.count - a.count;
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

function countStudyPossibleCardsFromRows(rows, options = {}) {
  const shortOnly = document.getElementById("studyShortOnly")?.checked ?? true;
  const direction = options.direction || getStudyDirection();
  const seen = new Set();
  rows.forEach(row => {
    const lemma = cleanStudyText(getDisplayValue(row, "Texto estandarizado"));
    const translation = getStudyCardTranslation(row, lemma, direction);
    if (!lemma || !translation) return;
    if (shortOnly && translation.length > 180) return;
    const key = normalizeString(lemma);
    if (key) seen.add(key);
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

function getStudyPossibleCardCount() {
  const rows = getStudyRows();
  return countStudyPossibleCardsFromRows(rows, { direction: getStudyDirection() });
}

function updateStudyScope() {
  const el = document.getElementById("studyScope");
  if (!el) return;
  const rows = getStudyRows();
  const cards = rows.length ? getStudyPossibleCardCount() : 0;
  el.textContent = t("study.scope", { rows: rows.length, cards });
}

function resetStudyStats() {
  studyStats = { seen: 0, again: 0, hard: 0, good: 0, easy: 0 };
}

function getStudyAnswerCount() {
  return studyStats.again + studyStats.hard + studyStats.good + studyStats.easy;
}

function getStudySummaryText() {
  if (getStudyMode() === "study") {
    return t("study.summary.study", { seen: studyStats.seen });
  }
  const answers = getStudyAnswerCount();
  const known = studyStats.good + studyStats.easy;
  const review = studyStats.again + studyStats.hard;
  const percent = answers ? Math.round((known / answers) * 100) : 0;
  return [
    t("study.summary.primary", { cards: studyBaseDeck.length, answers }),
    t("study.summary.score", { known, percent, review }),
    t("study.summary.detail", {
      again: studyStats.again,
      hard: studyStats.hard,
      good: studyStats.good,
      easy: studyStats.easy
    })
  ].join("\n");
}

function getStudyProgressText() {
  if (getStudyMode() === "study") return t("study.progress.study", { seen: studyStats.seen });
  return t("study.progress", {
    seen: studyStats.seen,
    good: studyStats.good + studyStats.easy,
    again: studyStats.again + studyStats.hard
  });
}

function buildStudyDeck() {
  const rows = getStudyRows();
  const limit = getStudyLimit();
  const shortOnly = document.getElementById("studyShortOnly")?.checked ?? true;
  const shouldShuffle = document.getElementById("studyShuffle")?.checked ?? true;
  let cards = buildStudyCardsFromRows(rows, {
    shortOnly,
    direction: getStudyDirection()
  });
  if (shouldShuffle) cards = shuffleStudyCards(cards);
  studyBaseDeck = cards.slice(0, limit);
  studyDeck = studyBaseDeck.slice();
  studyIndex = 0;
  resetStudyAnswerState();
  studyEmptyMessageKey = studyDeck.length ? "study.empty" : "study.noCards";
  resetStudyStats();
  renderStudyCard();
  updateStudyScope();
}

function resetStudyDeck() {
  studyDeck = studyBaseDeck.slice();
  studyIndex = 0;
  resetStudyAnswerState();
  resetStudyStats();
  renderStudyCard();
}

function getCurrentStudyCard() {
  if (!studyDeck.length) return null;
  if (studyIndex < 0 || studyIndex >= studyDeck.length) return null;
  return studyDeck[studyIndex];
}

function setStudyText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function renderStudyCard() {
  const current = getCurrentStudyCard();
  const isDone = studyDeck.length > 0 && studyIndex >= studyDeck.length;
  const isExamMode = getStudyMode() === "exam";
  const isStudyBothMode = !isExamMode && getStudyViewMode() === "both";
  const countEl = document.getElementById("studyCardCount");
  const fillEl = document.getElementById("studyProgressFill");
  const faceEl = document.querySelector(".study-face");
  const backWrap = document.getElementById("studyBackWrap");
  const revealBtn = document.getElementById("studyRevealBtn");
  const nextBtn = document.getElementById("studyNextBtn");
  const resetBtn = document.getElementById("studyResetBtn");
  const gradeBtns = document.querySelectorAll(".study-grade-btn");
  const showStudyCardType = current && !isDone && !isExamMode;

  if (faceEl) {
    faceEl.classList.toggle("study-face--one-sided", showStudyCardType && isStudyBothMode);
    faceEl.classList.toggle("study-face--two-sided", showStudyCardType && !isStudyBothMode);
    faceEl.classList.toggle("study-face--back", showStudyCardType && !isStudyBothMode && studyAnswerVisible);
    faceEl.classList.toggle("study-face--exam", current && !isDone && isExamMode);
    faceEl.classList.toggle("study-face--pressable", showStudyCardType);
    if (showStudyCardType) {
      const faceActionKey = isStudyBothMode ? "study.face.zones.next" : "study.face.zones.flip";
      faceEl.setAttribute("role", "button");
      faceEl.setAttribute("tabindex", "0");
      faceEl.setAttribute("aria-label", t(faceActionKey));
      faceEl.setAttribute("title", t(faceActionKey));
    } else {
      faceEl.removeAttribute("role");
      faceEl.removeAttribute("tabindex");
      faceEl.removeAttribute("aria-label");
      faceEl.removeAttribute("title");
    }
  }

  if (countEl) {
    const currentNumber = current ? studyIndex + 1 : isDone ? studyDeck.length : 0;
    countEl.textContent = t("study.cardCount", { current: currentNumber, total: studyDeck.length });
  }
  if (fillEl) {
    const pct = studyDeck.length ? Math.min(100, (studyIndex / studyDeck.length) * 100) : 0;
    fillEl.style.width = `${pct}%`;
  }

  if (!studyDeck.length) {
    setStudyText("studyFrontLabel", t("study.front.edition"));
    setStudyText("studyBackLabel", t("study.front.translation"));
    setStudyText("studyFront", t(studyEmptyMessageKey));
    setStudyText("studyBack", "");
    setStudyText("studyMeta", "");
  } else if (isDone) {
    setStudyText("studyFrontLabel", t("study.summary"));
    setStudyText("studyBackLabel", t("study.summary.results"));
    setStudyText("studyFront", t("study.done"));
    setStudyText("studyBack", getStudySummaryText());
    setStudyText("studyMeta", getStudyProgressText());
  } else if (current) {
    const showingStudyBack = !isExamMode && !isStudyBothMode && studyAnswerVisible;
    setStudyText("studyFront", showingStudyBack ? current.back : current.front);
    setStudyText("studyBack", (isStudyBothMode || (isExamMode && studyAnswerVisible)) ? current.back : "");
    setStudyText("studyFrontLabel", t(showingStudyBack ? current.backLabelKey : current.frontLabelKey));
    setStudyText("studyBackLabel", t(current.backLabelKey));
    setStudyText("studyMeta", t("study.sources", {
      sources: current.sourceCount,
      rows: current.rowCount
    }));
  }

  if (backWrap) {
    const showBackPanel = isDone || (current && (isStudyBothMode || (isExamMode && studyAnswerVisible)));
    backWrap.hidden = !showBackPanel;
  }
  if (nextBtn) {
    nextBtn.hidden = isExamMode;
    nextBtn.disabled = !current || isDone;
  }
  if (revealBtn) {
    setButtonState(revealBtn, isExamMode ? "study.reveal" : "study.flip", isExamMode ? "icon-question" : "icon-swap-horizontal");
    revealBtn.hidden = isStudyBothMode;
    revealBtn.disabled = !current || isDone || (isExamMode && studyAnswerVisible);
  }
  if (resetBtn) resetBtn.disabled = !studyDeck.length;
  gradeBtns.forEach(btn => {
    btn.hidden = !isExamMode;
    btn.disabled = !current || !studyAnswerVisible;
  });

  setStudyText("studyProgress", getStudyProgressText());
}

function revealStudyAnswer() {
  if (!getCurrentStudyCard()) return;
  if (!studyAnswerVisible) studyStats.seen += 1;
  studyAnswerVisible = true;
  renderStudyCard();
}

function turnStudyCard() {
  if (!getCurrentStudyCard()) return;
  if (getStudyMode() === "exam") {
    revealStudyAnswer();
    return;
  }
  if (getStudyViewMode() === "both") return;
  studyAnswerVisible = !studyAnswerVisible;
  renderStudyCard();
}

function advanceStudyCard() {
  const current = getCurrentStudyCard();
  if (!current || getStudyMode() !== "study") return;
  studyIndex += 1;
  studyStats.seen = Math.max(studyStats.seen, Math.min(studyIndex, studyDeck.length));
  resetStudyAnswerState();
  renderStudyCard();
}

function previousStudyCard() {
  const current = getCurrentStudyCard();
  if (!current || getStudyMode() !== "study") return;
  if (studyIndex <= 0) return;
  studyIndex -= 1;
  resetStudyAnswerState();
  renderStudyCard();
}

function activateStudyFaceCenter() {
  if (!getCurrentStudyCard() || getStudyMode() !== "study") return;
  if (getStudyViewMode() === "flip") turnStudyCard();
}

function handleStudyFaceClick(event) {
  const current = getCurrentStudyCard();
  if (!current || getStudyMode() !== "study") return;
  const rect = event.currentTarget.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const zone = x / rect.width;
  if (zone < 1 / 3) previousStudyCard();
  else if (zone > 2 / 3) advanceStudyCard();
  else activateStudyFaceCenter();
}

function handleStudyFaceKeydown(event) {
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    previousStudyCard();
    return;
  }
  if (event.key === "ArrowRight") {
    event.preventDefault();
    advanceStudyCard();
    return;
  }
  if (event.key !== "Enter" && event.key !== " " && event.key !== "Spacebar") return;
  event.preventDefault();
  activateStudyFaceCenter();
}

function gradeStudyCard(grade) {
  const current = getCurrentStudyCard();
  if (!current) return;
  if (!studyAnswerVisible) {
    revealStudyAnswer();
    return;
  }
  if (!studyStats[grade]) studyStats[grade] = 0;
  studyStats[grade] += 1;
  if (grade === "again" || grade === "hard") {
    const delay = grade === "again" ? 3 : 8;
    const target = Math.min(studyDeck.length, studyIndex + delay);
    studyDeck.splice(target, 0, current);
  }
  studyIndex += 1;
  resetStudyAnswerState();
  renderStudyCard();
}

function refreshStudyModeUI() {
  updateStudyScope();
  renderStudyCard();
}

function setupStudyMode() {
  const buildBtn = document.getElementById("studyBuildBtn");
  const resetBtn = document.getElementById("studyResetBtn");
  const revealBtn = document.getElementById("studyRevealBtn");
  const nextBtn = document.getElementById("studyNextBtn");
  const faceEl = document.querySelector(".study-face");
  document.querySelectorAll(".study-mode-btn[data-study-mode]").forEach(btn => {
    btn.addEventListener("click", () => setStudyMode(btn.dataset.studyMode));
  });
  document.querySelectorAll(".study-mode-btn[data-study-view]").forEach(btn => {
    btn.addEventListener("click", () => setStudyViewMode(btn.dataset.studyView));
  });
  if (buildBtn) buildBtn.addEventListener("click", buildStudyDeck);
  if (resetBtn) resetBtn.addEventListener("click", resetStudyDeck);
  if (revealBtn) revealBtn.addEventListener("click", turnStudyCard);
  if (nextBtn) nextBtn.addEventListener("click", advanceStudyCard);
  if (faceEl) {
    faceEl.addEventListener("click", handleStudyFaceClick);
    faceEl.addEventListener("keydown", handleStudyFaceKeydown);
  }
  document.querySelectorAll(".study-grade-btn[data-study-grade]").forEach(btn => {
    btn.addEventListener("click", () => gradeStudyCard(btn.dataset.studyGrade));
  });
  ["studyUseFilters", "studyShortOnly", "studyDirection", "studyLimit"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("change", updateStudyScope);
  });
  syncStudyModeButtons();
  syncStudyViewButtons();
  updateStudyScope();
  renderStudyCard();
}

// ── Page-size controls ──────────────────────────────────────────
function updatePageSizeLabel() {
  const label = document.querySelector('label[for="pageSizeSelect"]');
  if (!label) return;
  label.textContent = t(tableViewMode === "lemmas" ? "table.pagesize.lemmasLabel" : "table.pagesize.label");
}

function setupPageSizeControls() {
  const selects = [document.getElementById("pageSizeSelect")].filter(Boolean);
  updatePageSizeLabel();
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
  syncFieldPillOrder();
  syncColumnLayout();
  renderTable(lastRenderRows, lastRenderTotal);
  requestAnimationFrame(() => setTableScroll(y));
  saveColumnState();
}

// ── URL hash routing (shareable filter state) ──────────────────────

const FIELD_CODE_OUT = {
  "Texto estandarizado": "te",
  "Escritura original": "eo",
  "Traducción": "tr",
  "Comentario": "co",
  "Fuente": "fu",
};
const FIELD_CODE_IN = Object.fromEntries(
  Object.entries(FIELD_CODE_OUT).map(([k, v]) => [v, k])
);
const SCOPE_CODE_OUT = { whole: "c", word: "w", phrase: "p" };
const SCOPE_CODE_IN = { t: "whole", c: "whole", w: "word", p: "phrase" };
const MODE_CODE_OUT = { exact: "e", starts: "s", any: "a", ends: "d" };
const MODE_CODE_IN = { e: "exact", s: "starts", a: "any", d: "ends" };

const sourceToSlug = new Map();
const slugToSource = new Map();
let hashRouteApplied = false;
let suppressHashUpdate = false;

function buildSourceSlugMaps() {
  sourceToSlug.clear();
  slugToSource.clear();
  const collisions = new Set();
  for (const row of dataRows) {
    const rid = row.record_id;
    if (!rid) continue;
    const sep = rid.indexOf(":");
    if (sep < 0) continue;
    const slug = rid.slice(0, sep);
    const fuente = row.Fuente;
    if (!slug || !fuente) continue;
    if (!sourceToSlug.has(fuente)) sourceToSlug.set(fuente, slug);
    if (!slugToSource.has(slug)) {
      slugToSource.set(slug, fuente);
    } else if (slugToSource.get(slug) !== fuente) {
      collisions.add(`${slug} ⇒ ${slugToSource.get(slug)} | ${fuente}`);
    }
  }
  if (collisions.size && typeof console !== "undefined") {
    console.warn("Source-slug collisions detected (share URLs may route to first source only):",
      [...collisions]);
  }
}

function getCommittedGroups() {
  return groupOrder
    .map(g => ({
      id: g.id,
      logic: g.logic,
      filters: activeFilters.filter(
        f => f.owner === g.id && f.type !== "fuenteSet"
      ),
    }))
    .filter(g => g.filters.length > 0);
}

function tryCanonicalLemma(groups) {
  if (groups.length !== 1) return null;
  const filters = groups[0].filters;
  if (filters.length !== 1) return null;
  const f = filters[0];
  if (f.field !== "Texto estandarizado") return null;
  if (f.mode !== "exact") return null;
  if (normalizeScope(f.scope) !== "whole") return null;
  if (f.negate) return null;
  if (typeof f.value !== "string" || !f.value) return null;
  return f.value;
}

function buildHash() {
  if (oldSpanishMode || accentSensitiveMode) return serializeQueryHash();
  const groups = getCommittedGroups();
  const defaultSources = isDefaultFuenteSelection();
  const sel = selectedFuentes.size;
  const lema = tryCanonicalLemma(groups);

  if (lema && defaultSources) {
    return `#/lema/${encodeURIComponent(lema)}`;
  }
  if (lema && sel === 1) {
    const only = [...selectedFuentes][0];
    const slug = sourceToSlug.get(only);
    if (slug) return `#/lema/${encodeURIComponent(lema)}/${encodeURIComponent(slug)}`;
  }
  if (!groups.length && sel === 1) {
    const only = [...selectedFuentes][0];
    const slug = sourceToSlug.get(only);
    if (slug) return `#/fuente/${encodeURIComponent(slug)}`;
  }
  if (!groups.length && defaultSources) return "";
  return serializeQueryHash();
}

function serializeQueryHash() {
  const groups = getCommittedGroups();
  const groupSpecs = groups.map(g => {
    const f0 = g.filters[0];
    const fieldCode = FIELD_CODE_OUT[f0.field];
    if (!fieldCode) return "";
    const groupScope = normalizeScope(f0.scope);
    const scopeCode = SCOPE_CODE_OUT[groupScope] || "c";
    const logicCode = g.logic === "OR" ? "O" : "A";
    const inputs = g.filters.map(f => {
      const m = MODE_CODE_OUT[f.mode] || "a";
      const n = f.negate ? "1" : "0";
      const inputScope = normalizeScope(f.scope);
      const inputScopePrefix = inputScope !== groupScope
        ? `${SCOPE_CODE_OUT[inputScope] || "c"}:`
        : "";
      const raw = typeof f.value === "string" ? f.value : "";
      return `${m}:${n}:${inputScopePrefix}${encodeURIComponent(raw)}`;
    }).join("|");
    return `${logicCode}:${fieldCode}:${scopeCode}:${inputs}`;
  }).filter(Boolean);

  const params = [];
  if (groupSpecs.length) params.push(`g=${groupSpecs.join(";")}`);
  if (!isDefaultFuenteSelection()) {
    const slugs = [...selectedFuentes]
      .map(name => sourceToSlug.get(name))
      .filter(Boolean);
    params.push(`f=${slugs.join(",")}`);
  }
  if (oldSpanishMode) params.push("o=1");
  if (accentSensitiveMode) params.push("a=s");
  return params.length ? `#/q?${params.join("&")}` : "";
}

function updateUrlHash() {
  if (!hashRouteApplied || suppressHashUpdate) return;
  const next = buildHash();
  const current = location.hash;
  if (next === current) return;
  if (!next && !current) return;
  if (next) {
    history.replaceState(null, "", next);
  } else {
    history.replaceState(null, "", location.pathname + location.search);
  }
}

function parseHashRoute(hash) {
  if (!hash || !hash.startsWith("#/")) return null;
  const body = hash.slice(2);
  if (body.startsWith("q?") || body === "q") {
    const qIdx = body.indexOf("?");
    return parseQueryHash(qIdx >= 0 ? body.slice(qIdx + 1) : "");
  }
  const parts = body.split("/").filter(Boolean);
  if (!parts.length) return null;
  const head = parts[0];
  if (head === "lema" && parts.length >= 2) {
    let lema;
    try { lema = decodeURIComponent(parts[1]); } catch { return null; }
    if (!lema) return null;
    let fuentes = null;
    if (parts[2]) {
      let slug;
      try { slug = decodeURIComponent(parts[2]); } catch { return null; }
      const name = slugToSource.get(slug);
      if (name) fuentes = [name];
    }
    return {
      groups: [{
        logic: "AND",
        field: "Texto estandarizado",
        scope: "whole",
        inputs: [{ mode: "exact", negate: false, value: lema }],
      }],
      fuentes,
      oldSpanish: false,
      accent: false,
    };
  }
  if (head === "fuente" && parts.length >= 2) {
    let slug;
    try { slug = decodeURIComponent(parts[1]); } catch { return null; }
    const name = slugToSource.get(slug);
    if (!name) return null;
    return { groups: [], fuentes: [name], oldSpanish: false, accent: false };
  }
  return null;
}

function parseQueryHash(qs) {
  const state = { groups: [], fuentes: null, oldSpanish: false, accent: false };
  if (!qs) return state;
  const params = new Map();
  for (const part of qs.split("&")) {
    if (!part) continue;
    const eq = part.indexOf("=");
    if (eq < 0) params.set(part, "");
    else params.set(part.slice(0, eq), part.slice(eq + 1));
  }
  const gs = params.get("g") || "";
  if (gs) {
    for (const spec of gs.split(";")) {
      const g = parseGroupSpec(spec);
      if (g) state.groups.push(g);
    }
  }
  if (params.has("f")) {
    const slugs = (params.get("f") || "").split(",").filter(Boolean);
    state.fuentes = slugs.map(s => slugToSource.get(s)).filter(Boolean);
  }
  state.oldSpanish = params.get("o") === "1";
  state.accent = params.get("a") === "s";
  return state;
}

function parseGroupSpec(spec) {
  if (!spec) return null;
  const parts = spec.split(":");
  if (parts.length < 4) return null;
  const logic = parts[0] === "O" ? "OR" : "AND";
  const field = FIELD_CODE_IN[parts[1]];
  const scope = SCOPE_CODE_IN[parts[2]] || "whole";
  if (!field) return null;
  const inputsStr = parts.slice(3).join(":");
  const inputs = inputsStr.split("|").map(spec => parseInputSpec(spec, scope)).filter(Boolean);
  if (!inputs.length) return null;
  return { logic, field, scope, inputs };
}

function parseInputSpec(spec, defaultScope = "whole") {
  if (!spec) return null;
  const parts = spec.split(":");
  if (parts.length < 3) return null;
  const mode = MODE_CODE_IN[parts[0]];
  if (!mode) return null;
  const negate = parts[1] === "1";
  let scope = defaultScope;
  let valueStartIdx = 2;
  if (parts.length >= 4 && SCOPE_CODE_IN[parts[2]]) {
    scope = SCOPE_CODE_IN[parts[2]];
    valueStartIdx = 3;
  }
  let value;
  try { value = decodeURIComponent(parts.slice(valueStartIdx).join(":")); } catch { return null; }
  if (!value) return null;
  return { mode, negate, value, scope };
}

function applyParsedState(state) {
  if (!state) return false;
  suppressHashUpdate = true;
  try {
    if (editingGroupId) editingGroupId = null;
    activeFilters = [];
    groupOrder = [];
    groupCounter = 0;

    state.groups.forEach(g => {
      const groupId = `group_${++groupCounter}`;
      g.inputs.forEach(inp => {
        const inputScope = inp.scope || g.scope;
        const wordGroupId = (inputScope === "word" && g.logic === "AND") ? groupId : null;
        const extras = wordGroupId
          ? { owner: groupId, wordGroupId }
          : { owner: groupId };
        appendFilter(g.field, inp.mode, inp.value, g.logic, inp.negate, inputScope, extras);
      });
      groupOrder.push({ id: groupId, logic: g.logic });
    });

    selectedFuentes.clear();
    if (state.fuentes && state.fuentes.length) {
      state.fuentes.forEach(name => selectedFuentes.add(name));
    } else if (!state.fuentes) {
      DEFAULT_FUENTE_OPTIONS.forEach(name => selectedFuentes.add(name));
    }

    const desiredOldSpanish = !!state.oldSpanish;
    if (oldSpanishMode !== desiredOldSpanish) {
      oldSpanishMode = desiredOldSpanish;
      normalizationCache = new Map();
      document.querySelectorAll(".old-spanish-btn").forEach(b =>
        b.classList.toggle("active", oldSpanishMode)
      );
    }
    const desiredAccent = !!state.accent;
    if (accentSensitiveMode !== desiredAccent) {
      accentSensitiveMode = desiredAccent;
      updateAccentLabels();
    }

    renderFuenteList();
    renderActiveFilterChips();
    applyFuenteFilters();
  } finally {
    suppressHashUpdate = false;
  }
  return true;
}

function handleHashChange() {
  if (!hashRouteApplied) return;
  const state = parseHashRoute(location.hash);
  if (state) applyParsedState(state);
}

// ── Service worker (PWA install + offline cache) ────────────────────
if ("serviceWorker" in navigator && location.protocol !== "file:") {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  });
}

// ── Toast (transient feedback) ──────────────────────────────────────
let toastEl = null;
let toastTimer = null;
function showToast(message) {
  if (!toastEl) {
    toastEl = document.createElement("div");
    toastEl.className = "toast";
    toastEl.setAttribute("role", "status");
    toastEl.setAttribute("aria-live", "polite");
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = message;
  toastEl.classList.add("toast--visible");
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.classList.remove("toast--visible");
  }, 1800);
}

async function copyText(text) {
  if (!text) return false;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {}
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  } catch {
    return false;
  }
}

// ── Web Share button ────────────────────────────────────────────────
function setupShareButton() {
  const btn = document.getElementById("shareBtn");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    const url = location.href;
    const title = document.title;
    const shareData = { title, url };
    if (navigator.share) {
      try {
        await navigator.share(shareData);
        return;
      } catch (err) {
        // User cancelled — silent. Other errors fall through to copy.
        if (err && err.name === "AbortError") return;
      }
    }
    const ok = await copyText(url);
    showToast(t(ok ? "share.copied" : "share.failed"));
  });
}

// ── Long-press to copy cell text ────────────────────────────────────
function setupLongPressCopy() {
  const tbody = document.querySelector("#dataTable tbody");
  if (!tbody) return;
  let pressTimer = null;
  let pressStart = null;
  let pressTarget = null;
  let firedCopy = false;

  function reset() {
    if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; }
    pressStart = null;
    pressTarget = null;
  }

  tbody.addEventListener("pointerdown", e => {
    if (e.pointerType === "mouse") return;
    const cell = e.target.closest("td");
    if (!cell) return;
    if (e.target.closest(".mobile-row-toggle, button, a, input, select, textarea")) return;
    firedCopy = false;
    pressStart = { x: e.clientX, y: e.clientY };
    pressTarget = cell;
    pressTimer = setTimeout(async () => {
      pressTimer = null;
      if (!pressTarget) return;
      const clone = pressTarget.cloneNode(true);
      clone.querySelectorAll(".mobile-row-toggle").forEach(el => el.remove());
      const text = (clone.innerText || clone.textContent || "").replace(/\s+/g, " ").trim();
      if (!text) return;
      const ok = await copyText(text);
      if (ok) {
        firedCopy = true;
        showToast(t("copy.cell"));
        vibe(12);
      }
    }, 450);
  });

  tbody.addEventListener("pointermove", e => {
    if (!pressStart) return;
    const dx = e.clientX - pressStart.x;
    const dy = e.clientY - pressStart.y;
    if (Math.hypot(dx, dy) > 10) reset();
  });

  ["pointerup", "pointercancel", "pointerleave"].forEach(ev =>
    tbody.addEventListener(ev, () => reset())
  );

  // Suppress the click that follows a long-press.
  tbody.addEventListener("click", e => {
    if (firedCopy) {
      firedCopy = false;
      e.stopPropagation();
      e.preventDefault();
    }
  }, true);
}

// On phones with the soft keyboard open, scroll the focused input into view
// above the keyboard. Uses visualViewport when available; harmless otherwise.
function setupKeyboardAvoidance() {
  if (typeof window === "undefined") return;
  const vv = window.visualViewport;
  if (!vv) return;
  if (!window.matchMedia || !window.matchMedia("(pointer: coarse)").matches) return;

  let raf = 0;
  function ensureFocusedVisible() {
    const el = document.activeElement;
    if (!el || !el.matches) return;
    if (!el.matches("input, textarea, select")) return;
    const rect = el.getBoundingClientRect();
    const top = vv.offsetTop;
    const bottom = top + vv.height;
    // 12px breathing room above the keyboard / below the URL bar.
    const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const behavior = reduced ? "auto" : "smooth";
    if (rect.bottom > bottom - 12) {
      el.scrollIntoView({ block: "center", behavior });
    } else if (rect.top < top + 12) {
      el.scrollIntoView({ block: "center", behavior });
    }
  }
  function onChange() {
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(ensureFocusedVisible);
  }
  vv.addEventListener("resize", onChange);
  vv.addEventListener("scroll", onChange);
  document.addEventListener("focusin", onChange);
}
