/**
 * Service Worker for Tulasi Nepali PWA
 * Scope: / (Entire website & admin dashboard)
 */

const CACHE_NAME = 'tn-pwa-v1.1';
const OFFLINE_URL = '/offline/';

const PRECACHE_ASSETS = [
    OFFLINE_URL,
    '/static/images/pwa/icon-192x192.png',
    '/static/images/pwa/icon-512x512.png',
    '/static/images/pwa/icon-maskable-192x192.png',
    '/static/images/pwa/icon-maskable-512x512.png',
    '/static/images/pwa/apple-touch-icon.png'
];

// Install: Cache offline fallback and core PWA assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate: Clean up older cache versions
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((name) => {
                    if (name !== CACHE_NAME) {
                        return caches.delete(name);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch: Strategy depending on request type
self.addEventListener('fetch', (event) => {
    const request = event.request;

    // Only process GET requests (POST/PUT/DELETE for logins, quizzes, comments go directly to network)
    if (request.method !== 'GET') {
        return;
    }

    const url = new URL(request.url);

    // Skip cross-origin or analytics/ad requests
    if (url.origin !== location.origin) {
        return;
    }

    // Navigation requests (HTML pages) -> Network-First, fallback to offline page
    if (request.mode === 'navigate' || (request.headers.get('accept') && request.headers.get('accept').includes('text/html'))) {
        event.respondWith(
            fetch(request)
                .then((networkResponse) => {
                    // Cache successful navigation responses for fast reload
                    if (networkResponse && networkResponse.status === 200) {
                        const copy = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            // Avoid caching large dashboard pages blindly
                            if (!url.pathname.startsWith('/rishav/admin/')) {
                                cache.put(request, copy);
                            }
                        });
                    }
                    return networkResponse;
                })
                .catch(async () => {
                    // Check if page is already cached
                    const cachedResponse = await caches.match(request);
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // Otherwise return the offline page
                    return caches.match(OFFLINE_URL);
                })
        );
        return;
    }

    // Static assets (CSS, JS, Fonts, Images) -> Cache-first with network fallback
    if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                if (cachedResponse) {
                    // Update cache in the background (stale-while-revalidate)
                    fetch(request).then((networkResponse) => {
                        if (networkResponse && networkResponse.status === 200) {
                            caches.open(CACHE_NAME).then((cache) => cache.put(request, networkResponse));
                        }
                    }).catch(() => {});
                    return cachedResponse;
                }

                return fetch(request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const copy = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
                    }
                    return networkResponse;
                });
            })
        );
        return;
    }

    // Default: Network with cache fallback
    event.respondWith(
        fetch(request).catch(() => caches.match(request))
    );
});
