// Service worker for Base de datos náhuatl.
// Bump CACHE_VERSION whenever shipped HTML/CSS/JS changes.
const CACHE_VERSION = "v540";
const CACHE_NAME = `nahuatl-db-${CACHE_VERSION}`;

// Large static search assets are intentionally not precached or runtime-cached.
// They are static/offline fallback assets, not normal large/mobile deployment
// assets, and caching them can quickly consume phone storage.
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

function patchCodeAsset(request, response) {
  return Promise.resolve(response);
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

function isLargeSearchFallbackAsset(url) {
  const path = url.pathname.replace(/^\/+/, "");
  return path === "data/data.jsonl.gz"
    || path === "search-worker.js"
    || path.startsWith("data/lazy/");
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

  // Backend search/API responses must not be cached by the app shell.
  if (url.pathname.startsWith("/api/")) return;

  // Full DB, static lazy chunks, and the fallback search worker must never be
  // stored by the app shell. Backend mode should not request them at all.
  if (isLargeSearchFallbackAsset(url)) return;

  // Navigation + code → network-first so updates apply on first reload.
  if (request.mode === "navigate" || CODE_ASSET_RE.test(url.pathname)) {
    event.respondWith(networkFirst(request));
    return;
  }
  // Data, icons, manifest → stale-while-revalidate.
  event.respondWith(staleWhileRevalidate(request));
});
