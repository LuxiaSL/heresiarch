/* Heresiarch mobile — service-worker shell.
 *
 * Strategy:
 *   - api/* under our scope and any non-GET: network only. Game state
 *     lives on the server (LAN mode) or in the page (Pyodide mode) —
 *     never cache it.
 *   - App shell (./, manifest, icons, and anything else fetched from
 *     scope — incl. the wasm runtime in the serverless build):
 *     network-first with cache fallback, so dev iteration and Pages
 *     deploys always win when online, but the installed app still
 *     launches with no connection.
 *
 * All URLs are relative to the SW script so the same file works at the
 * LAN root and under a subpath (GitHub Pages /heresiarch/).
 *
 * Bump VERSION when shell assets change shape; day-to-day edits don't
 * need it (network-first re-caches on every successful load).
 */

const VERSION = "hx-shell-v2";
const SHELL = [
  "./",
  "manifest.webmanifest",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/icon-maskable-512.png",
  "icons/apple-touch-icon.png",
];
const API_PREFIX = new URL("api/", self.registration.scope).pathname;

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.pathname.startsWith(API_PREFIX)) {
    return; // network only — let the page handle failures
  }
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(VERSION).then((c) => c.put(e.request, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() =>
        caches.match(e.request).then((hit) => hit || Response.error()),
      ),
  );
});
