// Service worker for Base de datos náhuatl.
// Bump CACHE_VERSION whenever shipped HTML/CSS/JS or the data file changes.
const CACHE_VERSION = "v1";
const CACHE_NAME = `nahuatl-db-${CACHE_VERSION}`;

const CORE_ASSETS = [
  "./",
  "./index.html",
  "./style.css",
  "./script.js",
  "./data.js",
  "./filters.js",
  "./manifest.json",
  "./icon.svg",
  "./data/data.jsonl.gz",
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

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  // Same-origin only; skip cross-origin (CDNs etc.).
  if (url.origin !== self.location.origin) return;

  // Navigation requests → network-first so users get fresh HTML when online.
  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request));
    return;
  }
  // Everything else (CSS, JS, data, icon, manifest) → stale-while-revalidate.
  event.respondWith(staleWhileRevalidate(request));
});
