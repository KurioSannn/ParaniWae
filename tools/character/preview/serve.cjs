// Server statis kecil untuk pratinjau (dipakai di container Playwright): /three/* dari node_modules frontend, /model.glb dari content.
const http = require("http"), fs = require("fs"), path = require("path");
const ROOTS = { "/three/": "/fe_nm/three/", "/model.glb": "/char/silatara-instructor.glb" };
const TYPES = { ".js": "text/javascript", ".html": "text/html", ".glb": "model/gltf-binary" };
http.createServer((req, res) => {
  const u = new URL(req.url, "http://x").pathname;
  let f = u === "/" ? "/preview/viewer.html" : null;
  for (const [p, d] of Object.entries(ROOTS)) if (u.startsWith(p)) f = u === p ? d : d + u.slice(p.length);
  if (!f) f = path.join("/preview", u);
  fs.readFile(f, (e, b) => { if (e) { res.writeHead(404); return res.end(); } res.writeHead(200, { "Content-Type": TYPES[path.extname(f)] || "application/octet-stream" }); res.end(b); });
}).listen(8099, () => console.log("ready"));
