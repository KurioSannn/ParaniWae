// Pemeriksa tautan & konten publik (tanpa login). Pemakaian: BASE=http://localhost:3010 node link-check.mjs
// - Mulai dari sitemap + halaman utama, ikuti semua <a href> internal (kecuali /app, /api, auth).
// - Gagal bila ada status >= 400, tautan internal rusak, animasi tidak bisa dimuat, atau teks pengembangan bocor.
const BASE = process.env.BASE ?? "http://localhost:3010";
const SKIP = [/^\/app(\/|$)/, /^\/api\//, /^\/masuk/, /^\/daftar/, /^\/lupa-sandi/, /^\/atur-ulang-sandi/, /^\/verifikasi-email/, /^\/undangan/, /^\/dev/, /^\/_next\//];
const FORBIDDEN = ["[DEMO]", "Tahap pengembangan", "contoh teknis", "Contoh teknis", "Data fiktif", "data fiktif", "Belum diverifikasi mitra", "Draf riset", "belum divalidasi instruktur", "needs_reference", "Placeholder", "Prototype", "Rujukan", "Mitra SILATARA", "perguruan mitra", "Perguruan Mitra", "bermitra", "Disusun dari", "hlm.", "Catatan redaksi", "Halaman tidak ditemukan", "Terjadi kesalahan"];

const seen = new Map(); // path -> status
const problems = [];
const queue = [];
const add = (p, from) => { if (!seen.has(p) && !SKIP.some((r) => r.test(p))) { seen.set(p, null); queue.push([p, from]); } };

const sm = await fetch(`${BASE}/sitemap.xml`);
if (!sm.ok) problems.push(`sitemap.xml -> ${sm.status}`);
for (const m of (await sm.text()).matchAll(/<loc>([^<]+)<\/loc>/g)) add(new URL(m[1]).pathname, "sitemap");
for (const p of ["/", "/heritage", "/library", "/academy", "/community", "/community/peta", "/community/kirim-tempat", "/status"]) add(p, "seed");

const svgs = new Set();
while (queue.length) {
  const batch = queue.splice(0, 8);
  await Promise.all(batch.map(async ([path, from]) => {
    let res;
    try { res = await fetch(BASE + path, { redirect: "manual" }); } catch (e) { problems.push(`${path} (dari ${from}) -> ERROR ${e}`); return; }
    seen.set(path, res.status);
    if (res.status >= 300 && res.status < 400) { const loc = res.headers.get("location"); if (loc) add(new URL(loc, BASE).pathname, path); return; }
    if (res.status >= 400) { problems.push(`${path} (dari ${from}) -> ${res.status}`); return; }
    const html = await res.text();
    const visible = html.replace(/<script[\s\S]*?<\/script>/g, "").replace(/<[^>]+>/g, " ");
    if (visible.replace(/\s+/g, " ").trim().length < 400) problems.push(`${path}: halaman hampir kosong`);
    for (const f of FORBIDDEN) if (visible.includes(f)) problems.push(`${path}: teks terlarang "${f}"`);
    for (const m of html.matchAll(/href="([^"#?]+)(?:[?#][^"]*)?"/g)) {
      const h = m[1];
      if (h.startsWith("/") && !h.startsWith("//") && !/\.(png|ico|svg|webmanifest|xml|css|js|txt)$/.test(h)) add(decodeURI(h), path);
    }
    for (const m of html.matchAll(/\/api\/v1\/research\/movements\/[a-z0-9-]+\/animation\.svg/g)) svgs.add(m[0]);
  }));
}
// semua animasi yang dirujuk harus termuat sebagai SVG
const mv = await (await fetch(`${BASE}/api/v1/research/movements`)).json();
for (const m of mv.items) if (m.animation.url) svgs.add(m.animation.url);
for (const s of svgs) {
  const r = await fetch(BASE + s);
  const t = await r.text();
  if (!r.ok || !t.includes("<animateTransform")) problems.push(`animasi rusak: ${s} -> ${r.status}`);
}
const ok = [...seen.values()].filter((s) => s && s < 400).length;
console.log(JSON.stringify({ pages_checked: seen.size, ok_or_redirect: ok, animations_checked: svgs.size, problems: problems.length }, null, 1));
for (const p of problems.slice(0, 60)) console.log("MASALAH", p);
process.exit(problems.length ? 1 : 0);
