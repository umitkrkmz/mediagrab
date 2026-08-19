// Minimal service worker - required for PWA installability. MediaGrab only
// works with its own local server running, so there is no offline caching
// here; every request just passes straight through to the network.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));
self.addEventListener("fetch", () => {});
