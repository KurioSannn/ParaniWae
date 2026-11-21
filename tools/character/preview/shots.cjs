// Tangkapan pratinjau: node shots.cjs <outdir>
const { chromium } = require("/e2e/node_modules/playwright");
const { spawn } = require("child_process");
const out = process.argv[2] || "/out";
const SHOTS = [
  ["front-idle", "idle", 0.5, "0,1.0,3.4", "0,0.88,0", 30],
  ["side-idle", "idle", 0.5, "-3.4,1.0,0", "0,0.88,0", 30],
  ["tq-idle", "idle", 0.5, "-2.4,1.3,2.5", "0,0.88,0", 30],
  ["face", "idle", 0.5, "0.12,1.6,0.55", "0,1.575,0.04", 30],
  ["face-34", "idle", 0.5, "-0.35,1.62,0.45", "0,1.58,0.03", 30],
  ["hand-open", "idle", 0.5, "0.75,1.0,0.55", "0.47,0.86,0.02", 28],
  ["hand-fist", "mv.psdp.kuda-kuda-depan", 0.3, "0.85,1.2,0.75", "0.2,0.97,0.08", 30],
  ["kk-depan-side", "mv.psdp.kuda-kuda-depan", 2.0, "-3.6,1.1,0.1", "0,0.85,0.1", 30],
  ["kk-tengah-front", "mv.psdp.kuda-kuda-tengah", 3.4, "0,1.1,3.6", "0,0.82,0", 30],
  ["angkatan-high", "mv.psdp.langkah-angkatan", 1.9, "-3.6,1.1,0.2", "0,0.9,0.2", 30],
  ["angkatan-low", "mv.psdp.langkah-angkatan", 7.0, "-3.6,1.1,0.2", "0,0.9,0.2", 30],
  ["tegak-3-front", "mv.psdp.sikap-tegak", 5.0, "0,1.2,3.4", "0,0.95,0", 30],
  ["pasang-1-tq", "mv.psdp.sikap-pasang-1", 2.2, "-2.4,1.3,2.5", "0,0.9,0.1", 30],
];
(async () => {
  const srv = spawn("node", ["/preview/serve.cjs"], { stdio: ["ignore", "pipe", "inherit"] });
  await new Promise((r) => srv.stdout.once("data", r));
  const b = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const p = await b.newPage({ viewport: { width: 640, height: 800 } });
  const errs = [];
  p.on("pageerror", (e) => errs.push(e.message)); p.on("console", (m) => m.type() === "error" && errs.push(m.text()));
  for (const [name, clip, t, cam, target, fov] of SHOTS) {
    await p.goto(`http://localhost:8099/?clip=${clip}&t=${t}&cam=${cam}&target=${target}&fov=${fov}`);
    await p.waitForFunction(() => window.__ready, null, { timeout: 60000 });
    await p.waitForTimeout(150);
    await p.screenshot({ path: `${out}/${name}.png` });
  }
  console.log("clips", JSON.stringify(await p.evaluate(() => window.__ready.clips)), "errors", JSON.stringify(errs.slice(0, 5)));
  await b.close(); srv.kill();
})().catch((e) => { console.error("FAIL", e); process.exit(1); });
