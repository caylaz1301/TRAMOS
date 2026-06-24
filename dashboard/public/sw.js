/**
 * Service Worker for TRAMOS Dashboard PWA Support
 * Provides offline caching and background sync
 */

const CACHE_NAME = 'tramos-v1';
const STATIC_CACHE = 'tramos-static-v1';
const API_CACHE = 'tramos-api-v1';

// Static assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
];

// API routes to cache
const API_ROUTES = [
  '/api/analytics/dashboard',
  '/api/analytics/stats/timeline',
  '/api/health',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker');

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== STATIC_CACHE && name !== API_CACHE)
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // API requests - network first, cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request, API_CACHE));
    return;
  }

  // Static assets - cache first, network fallback
  if (
    url.pathname.match(/\.(js|css|png|jpg|jpeg|svg|ico|woff2?)$/) ||
    url.pathname === '/'
  ) {
    event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
    return;
  }

  // HTML pages - network first, cache fallback
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirstStrategy(request, STATIC_CACHE));
    return;
  }
});

// Cache first strategy
async function cacheFirstStrategy(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  if (cached) {
    // Return cached, update in background
    updateCache(request, cacheName);
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // Return offline fallback for HTML requests
    if (request.headers.get('accept')?.includes('text/html')) {
      const offline = await cache.match('/');
      if (offline) return offline;
    }
    throw error;
  }
}

// Network first strategy
async function networkFirstStrategy(request, cacheName) {
  const cache = await caches.open(cacheName);

  try {
    const response = await fetch(request);

    if (response.ok) {
      cache.put(request, response.clone());
    }

    return response;
  } catch (error) {
    const cached = await cache.match(request);

    if (cached) {
      return cached;
    }

    // Return error response for API requests
    if (request.url.includes('/api/')) {
      return new Response(
        JSON.stringify({ error: 'offline', message: 'You are offline' }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    throw error;
  }
}

// Background cache update
async function updateCache(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      await cache.put(request, response);
    }
  } catch (error) {
    // Silently fail - cached version is being used
  }
}

// Push notification handling
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();

  const options = {
    body: data.body || data.message,
    icon: '/icon-192.png',
    badge: '/badge-72.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/',
      id: data.id,
    },
    actions: [
      { action: 'view', title: 'Lihat' },
      { action: 'dismiss', title: 'Tutup' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'TRAMOS', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'dismiss') return;

  const url = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Focus existing window if open
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.navigate(url);
            return client.focus();
          }
        }

        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
  );
});

// Background sync for failed requests
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  }
});

async function syncMessages() {
  // Sync any pending message sends
  const cache = await caches.open(API_CACHE);
  const requests = await cache.keys();

  for (const request of requests) {
    if (request.url.includes('/api/messages')) {
      try {
        await fetch(request);
        console.log('[SW] Synced:', request.url);
      } catch (error) {
        console.log('[SW] Sync failed:', request.url);
      }
    }
  }
}

// Message handling from main thread
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  }
});

console.log('[SW] Service worker loaded');
