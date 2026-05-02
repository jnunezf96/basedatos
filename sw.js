// Service worker for Base de datos náhuatl.
// Bump CACHE_VERSION whenever shipped HTML/CSS/JS changes.
const CACHE_VERSION = "v49";
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

function networkFirst(request) {
  return caches.open(CACHE_NAME).then(cache =>
    fetch(request).then(response => {
      if (response && response.ok) cache.put(request, response.clone());
      return response;
    }).catch(() => cache.match(request).then(c => c || cache.match("./index.html")))
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
