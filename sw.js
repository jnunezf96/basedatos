// Service worker for Base de datos náhuatl.
// Bump CACHE_VERSION whenever shipped HTML/CSS/JS changes.
const CACHE_VERSION = "v137";
const CACHE_NAME = `nahuatl-db-${CACHE_VERSION}`;

// Note: data/data.jsonl.gz is intentionally NOT precached. It's large and
// schema-coupled to the JS — letting it lazy-cache via stale-while-revalidate
// keeps the install lean and avoids serving stale data with new code.
const CORE_ASSETS = [
  "./",
  "./index.html",
  "./style.css",
  "./script.js",
  "./data.js",
  "./filters.js",
  "./data/bootstrap.js",
  "./manifest.json",
  "./icon.svg",
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache =>
      // Best-effort precache: don't fail install if a single asset is missing.
      Promise.all(
        CORE_ASSETS.map(url =>
          cache.add(new Request(url, { cache: "reload" })).catch(() => null)
        )
      )
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

function staleWhileRevalidate(request) {
  return caches.open(CACHE_NAME).then(cache =>
    cache.match(request).then(cached => {
      const networkFetch = fetch(request).then(response => {
        if (response && response.ok && response.type !== "opaque") {
          cache.put(request, response.clone());
        }
        return response;
      }).catch(() => cached);
      return cached || networkFetch;
    })
  );
}

function patchScriptJs(text) {
  let out = text;

  out = out.replace(
    '  const hasInitialRoute = location.hash && location.hash.startsWith("#/");\n' +
    '  const usedBootstrap = renderBootstrapRows({ skipForRoute: hasInitialRoute });\n' +
    '  loadCompressedJsonlRows(versionedAssetUrl("data/data.jsonl.gz"))',
    '  const hasInitialRoute = location.hash && location.hash.startsWith("#/");\n' +
    '  const usedBootstrap = renderBootstrapRows();\n' +
    '  if (hasInitialRoute) queueFullDataRefresh();\n' +
    '  ensureHashChangeListener();\n' +
    '  loadCompressedJsonlRows((() => {\n' +
    '    const dataPath = "data/data.jsonl.gz";\n' +
    '    let bootstrapVersion = "";\n' +
    '    try {\n' +
    '      const src = document.querySelector("script[src*=\\"data/bootstrap.js\\"]")?.src || "";\n' +
    '      bootstrapVersion = src ? new URL(src, location.href).searchParams.get("v") || "" : "";\n' +
    '    } catch {}\n' +
    '    const dataVersion = window.NAHUATL_DATA_VERSION || window.NAHUATL_BOOTSTRAP?.dataVersion || bootstrapVersion || APP_ASSET_VERSION;\n' +
    '    const separator = dataPath.includes("?") ? "&" : "?";\n' +
    '    return dataPath + separator + "v=" + encodeURIComponent(dataVersion);\n' +
    '  })())'
  );

  out = out.replace(
    'let hashRouteApplied = false;\nlet suppressHashUpdate = false;',
    'let hashRouteApplied = false;\n' +
    'let suppressHashUpdate = false;\n' +
    'let hashChangeListenerAttached = false;\n\n' +
    'function ensureHashChangeListener() {\n' +
    '  if (hashChangeListenerAttached) return;\n' +
    '  window.addEventListener("hashchange", handleHashChange);\n' +
    '  hashChangeListenerAttached = true;\n' +
    '}'
  );

  out = out.replace(
    '      pendingFullDataRefresh = false;\n' +
    '      hashRouteApplied = true;\n' +
    '      window.addEventListener("hashchange", handleHashChange);',
    '      pendingFullDataRefresh = false;\n' +
    '      hashRouteApplied = true;\n' +
    '      ensureHashChangeListener();'
  );

  return out;
}

function patchFiltersJs(text) {
  return text.replace(
    '  const wordList = group.accentSensitive ? entry.wordsWithAccents : entry.words;',
    '  const wordList = group.accentSensitive\n' +
    '    ? entry.wordsWithAccents\n' +
    '    : (oldSpanishMode && entry.wordsOS) ? entry.wordsOS : entry.words;'
  );
}

function patchStyleCss(text) {
  return text.replace(
    'th[data-field="Escritura original"],\n' +
    'td:nth-child(1),\n' +
    'th[data-field="Texto estandarizado"],\n' +
    'td:nth-child(2),\n' +
    'th[data-field="Fuente"],\n' +
    'td:nth-child(4) {\n' +
    '  width: 108px;\n' +
    '}\n\n' +
    'th[data-field="Traducción"],\n' +
    'td:nth-child(3) {\n' +
    '  width: 220px;\n' +
    '}',
    'th[data-field="Escritura original"],\n' +
    'td[data-field="Escritura original"],\n' +
    'th[data-field="Texto estandarizado"],\n' +
    'td[data-field="Texto estandarizado"],\n' +
    'th[data-field="Fuente"],\n' +
    'td[data-field="Fuente"] {\n' +
    '  width: 108px;\n' +
    '}\n\n' +
    'th[data-field="Traducción"],\n' +
    'td[data-field="Traducción"] {\n' +
    '  width: 220px;\n' +
    '}'
  );
}

function patchCodeAsset(request, response) {
  if (!response || !response.ok || response.type === "opaque") return Promise.resolve(response);
  const pathname = new URL(request.url).pathname;
  let patcher = null;
  if (pathname.endsWith("/script.js")) patcher = patchScriptJs;
  else if (pathname.endsWith("/filters.js")) patcher = patchFiltersJs;
  else if (pathname.endsWith("/style.css")) patcher = patchStyleCss;
  if (!patcher) return Promise.resolve(response);

  return response.text().then(text => {
    const patched = patcher(text);
    const headers = new Headers(response.headers);
    headers.delete("content-length");
    headers.delete("content-encoding");
    return new Response(patched, {
      status: response.status,
      statusText: response.statusText,
      headers
    });
  }).catch(() => response);
}

function networkFirst(request) {
  return caches.open(CACHE_NAME).then(cache =>
    fetch(request)
      .then(response => patchCodeAsset(request, response))
      .then(response => {
        if (response && response.ok) cache.put(request, response.clone());
        return response;
      })
      .catch(() => cache.match(request).then(c => c || cache.match("./index.html")))
  );
}

// Code assets must stay in lock-step with HTML — if the user gets new HTML
// but stale JS/CSS the page breaks. Treat them like navigations.
const CODE_ASSET_RE = /\.(?:js|css|html)$/i;

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  // Same-origin only; skip cross-origin (CDNs etc.).
  if (url.origin !== self.location.origin) return;

  // Navigation + code → network-first so updates apply on first reload.
  if (request.mode === "navigate" || CODE_ASSET_RE.test(url.pathname)) {
    event.respondWith(networkFirst(request));
    return;
  }
  // Data, icons, manifest → stale-while-revalidate.
  event.respondWith(staleWhileRevalidate(request));
});
