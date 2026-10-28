const CACHE="practica-v27";
const CORE=["./","index.html","manifest.webmanifest","icon-192.png","icon-512.png","apple-touch-icon.png"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
const withTimeout=(p,ms)=>Promise.race([p,new Promise((_,j)=>setTimeout(()=>j(new Error("timeout")),ms))]);
self.addEventListener("fetch",e=>{
  const req=e.request; if(req.method!=="GET") return;
  const url=new URL(req.url);
  // the app page: try the network briefly for updates, otherwise use the saved copy
  if(req.mode==="navigate"){
    e.respondWith(withTimeout(fetch(req,{cache:"no-store"}),4000).then(res=>{const copy=res.clone();caches.open(CACHE).then(c=>c.put("index.html",copy));return res})
      .catch(()=>caches.match("index.html")));
    return;
  }
  // everything else (fonts, icons): saved copy first, then fetch and save
  e.respondWith(caches.match(req).then(hit=>hit||fetch(req).then(res=>{
    if(res&&(res.ok||res.type==="opaque")&&(url.origin===location.origin||/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname))){const copy=res.clone();caches.open(CACHE).then(c=>c.put(req,copy))}
    return res;
  })));
});
