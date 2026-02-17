/**
 * POS Service Worker
 * Handles caching of static assets and API fallbacks for offline mode.
 */

const CACHE_NAME = 'salescompass-pos-v1';
const ASSETS_TO_CACHE = [
    '/pos/terminal/',
    '/static/pos/js/terminal.js',
    '/static/pos/js/offline-manager.js',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // API requests - Network first
    if (url.pathname.startsWith('/pos/api/')) {
        event.respondWith(
            fetch(request).catch(() => {
                return caches.match(request);
            })
        );
        return;
    }

    // Static assets - Cache first
    event.respondWith(
        caches.match(request).then((response) => {
            return response || fetch(request);
        })
    );
});
