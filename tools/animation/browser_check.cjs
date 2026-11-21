// Membuka halaman pratinjau animasi di Chromium nyata, menangkap dua frame berbeda waktu, dan mengukur
// apakah transformasi SVG berubah (bukti animasi berjalan, bukan gambar diam). Jalankan: make animations-browser-check
// Exit code 1 bila ada gambar gagal dimuat, error konsol, atau animasi yang tidak berubah.
const { chromium } = require('/e2e/node_modules/playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = [];
  p.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  p.on('requestfailed', r => errors.push('REQ ' + r.url()));
  await p.goto('file:///anim/index.html');
  await p.waitForTimeout(500);
  const imgs = await p.$$eval('img', xs => xs.map(x => ({ src: x.getAttribute('src'), ok: x.complete && x.naturalWidth > 0 })));
  console.log('img total', imgs.length, 'loaded', imgs.filter(i => i.ok).length);
  await p.screenshot({ path: '/out/preview-t0.png', fullPage: false });
  // buka satu SVG langsung untuk membaca transform terhitung
  const res = [];
  for (const id of ['mv.psdp.kuda-kuda-depan', 'mv.psdp.kuda-kuda-tengah', 'mv.psdp.langkah-angkatan', 'mv.psdp.arah-delapan-penjuru']) {
    await p.goto(`file:///anim/${id}/animation.svg`);
    const sample = async () => p.evaluate(() => {
      const g = document.querySelector('[id$="-root"]') || document.querySelector('circle[r="17"]');
      return g ? getComputedStyle(g).transform + '|' + (g.transform && g.transform.animVal.numberOfItems ? JSON.stringify(g.transform.animVal.getItem(0).matrix.e + ',' + g.transform.animVal.getItem(0).matrix.f) : '') : 'none';
    });
    const a = await sample(); await p.waitForTimeout(1600); const c = await sample();
    await p.screenshot({ path: `/out/${id}-t1600.png` });
    res.push({ id, t0: a, t1600: c, changed: a !== c });
  }
  console.log(JSON.stringify(res, null, 1));
  console.log('errors', JSON.stringify(errors));
  await b.close();
  const failed = imgs.some(i => !i.ok) || errors.length > 0 || res.some(r => !r.changed);
  if (failed) { console.error('GAGAL: animasi tidak termuat/tidak bergerak'); process.exit(1); }
  console.log('OK: semua animasi termuat dan bergerak');
})();
