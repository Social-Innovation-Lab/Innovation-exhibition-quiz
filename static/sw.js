const CACHE='brac-quiz-v1';
const ASSETS=[
  '/', '/static/styles.css', '/static/main.js',
  '/manifest.json', '/static/icons/icon-192.png', '/static/icons/icon-512.png'
];
self.addEventListener('install', e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)));
});
self.addEventListener('fetch', e=>{
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  );
});
