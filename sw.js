// Keystone Quest service worker.
// - The game page and icons are cached so the home-screen app opens offline.
// - Published adventures from api.php are cached on each successful load, so
//   they stay playable offline. The network is always tried first, so updates
//   show up as soon as there's a connection.
// - Editor requests (they carry the X-Edit-Key header) and saves are never cached.
// Bump VERSION when changing this file's caching rules.
const VERSION = 'kq-v1';
const SHELL = `${VERSION}-shell`;
const DATA = `${VERSION}-data`;
const FONTS = `${VERSION}-fonts`;
const SHELL_FILES = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => !k.startsWith(VERSION)).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function networkFirst(request, cacheName, fallbackUrl) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (err) {
    const cached = (await cache.match(request)) || (fallbackUrl && (await caches.match(fallbackUrl)));
    if (cached) return cached;
    throw err;
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const fresh = fetch(request).then(r => { if (r.ok || r.type === 'opaque') cache.put(request, r.clone()); return r; }).catch(() => cached);
  return cached || fresh;
}

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    event.respondWith(staleWhileRevalidate(req, FONTS));
    return;
  }
  if (url.origin !== self.location.origin) return;

  if (url.pathname.endsWith('/api.php')) {
    if (req.headers.has('X-Edit-Key') || url.searchParams.get('action') !== 'list') return; // editors always go to the server
    event.respondWith(networkFirst(req, DATA));
    return;
  }
  if (req.mode === 'navigate') {
    event.respondWith(networkFirst(req, SHELL, 'index.html'));
    return;
  }
  event.respondWith(caches.match(req).then(hit => hit || fetch(req)));
});
