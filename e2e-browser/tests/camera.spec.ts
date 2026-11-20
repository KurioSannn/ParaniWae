/**
 * VERIFIKASI SIKLUS HIDUP KAMERA + PEMUATAN MODEL dengan perangkat kamera PALSU Chromium.
 * Ini BUKAN bukti deteksi pose manusia: aliran video palsu berisi pola sintetis, bukan orang.
 */
import { expect, test } from "@playwright/test";
import { writeFileSync, mkdirSync } from "node:fs";
import AxeBuilder from "@axe-core/playwright";
import { INSTRUMENT_CAMERA, loginUI, trackStates, watch } from "./helpers";

const START = /nyalakan kamera/;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(INSTRUMENT_CAMERA);
  await loginUI(page, "demo-pelajar@silatara.test");
  await expect(page).toHaveURL(/\/app/);
  await page.goto("/app/practice/camera-check");
});

test("[lifecycle] pemberitahuan privasi tampil dan kamera TIDAK diminta sebelum klik", async ({ page }) => {
  await expect(page.getByText(/tidak direkam, disimpan, atau dikirim/)).toBeVisible();
  await expect(page.getByText(/bukan penilaian gerakan/i)).toBeVisible();
  expect(await page.evaluate(() => (window as unknown as { __gum: unknown[] }).__gum.length)).toBe(0);
});

test("[lifecycle] mulai -> preview tampil, 1 track video aktif, TANPA audio; stop -> semua track berhenti", async ({ page }) => {
  await page.getByRole("button", { name: START }).click();
  const video = page.getByLabel("Pratinjau kamera");
  await expect(page.getByRole("button", { name: /Hentikan kamera/ })).toBeVisible();
  await expect.poll(() => video.evaluate((v: HTMLVideoElement) => v.videoWidth)).toBeGreaterThan(0);
  const gum = await page.evaluate(() => (window as unknown as { __gum: { audio?: unknown }[] }).__gum);
  expect(gum).toHaveLength(1);
  expect(gum[0].audio).toBe(false);
  const tracks = await trackStates(page);
  expect(tracks.filter((t) => t.kind === "video" && t.state === "live")).toHaveLength(1);
  expect(tracks.filter((t) => t.kind === "audio")).toHaveLength(0);

  await page.getByRole("button", { name: /Hentikan kamera/ }).click();
  await expect(page.getByText("Kamera dihentikan.")).toBeVisible();
  expect((await trackStates(page)).every((t) => t.state === "ended")).toBe(true);
  expect(await video.evaluate((v: HTMLVideoElement) => v.srcObject)).toBeNull();
  // dapat dimulai lagi tanpa meninggalkan stream lama
  await page.getByRole("button", { name: START }).click();
  await expect(page.getByRole("button", { name: /Hentikan kamera/ })).toBeVisible();
  const live = (await trackStates(page)).filter((t) => t.state === "live");
  expect(live).toHaveLength(1);
});

test("[lifecycle] meninggalkan halaman (navigasi SPA / unmount) menghentikan semua track", async ({ page }) => {
  await page.getByRole("button", { name: START }).click();
  await expect(page.getByRole("button", { name: /Hentikan kamera/ })).toBeVisible();
  await page.getByRole("link", { name: "Lanjut belajar lewat pelajaran teks" }).click();
  await expect(page).toHaveURL(/\/academy/);
  expect((await trackStates(page)).length).toBeGreaterThan(0);
  expect((await trackStates(page)).every((t) => t.state === "ended")).toBe(true);
});

test("[lifecycle] event pagehide (tab ditutup/di-navigasi) menghentikan track", async ({ page }) => {
  await page.getByRole("button", { name: START }).click();
  await expect(page.getByRole("button", { name: /Hentikan kamera/ })).toBeVisible();
  await page.evaluate(() => window.dispatchEvent(new Event("pagehide")));
  await expect.poll(async () => (await trackStates(page)).every((t) => t.state === "ended")).toBe(true);
  await expect(page.getByText("Kamera dihentikan.")).toBeVisible();
});

test("[privasi] selama kamera + deteksi aktif tidak ada request mutasi / unggahan ke server", async ({ page }) => {
  const mutating: string[] = [];
  page.on("request", (r) => { if (!["GET", "HEAD", "OPTIONS"].includes(r.method())) mutating.push(`${r.method()} ${r.url()}`); });
  await page.getByRole("button", { name: START }).click();
  await expect(page.getByRole("button", { name: /Hentikan kamera/ })).toBeVisible();
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  await expect(page.getByTestId("cam-metrics")).toBeVisible({ timeout: 60_000 });
  await page.waitForTimeout(2000);
  expect(mutating).toEqual([]);
});

test("[worker + model loading] worker same-origin; wasm & model dari origin sendiri; tanpa error konsol; frame diproses", async ({ page, browser }, info) => {
  const origin = new URL(info.project.use.baseURL ?? process.env.BASE_URL!).origin;
  const w = watch(page, origin);
  const libWarnings = new Set<string>();
  page.on("console", (c) => { if (c.type() === "warning") libWarnings.add(c.text().replace(/\d{4} \d\d:\d\d:\d\d\.\d+ \d+ /, "")); });
  const assets: Record<string, number> = {};
  page.on("response", (r) => { if (r.url().includes("/mediapipe/")) assets[new URL(r.url()).pathname] = r.status(); });
  const workers: string[] = [];
  page.on("worker", (wk) => workers.push(wk.url()));

  await page.getByRole("button", { name: START }).click();
  await expect(page.getByRole("button", { name: /Hentikan kamera/ })).toBeVisible();
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  const m = page.getByTestId("cam-metrics");
  await expect(m).toBeVisible({ timeout: 90_000 });
  await expect.poll(async () => Number(await m.getAttribute("data-frames")), { timeout: 120_000 }).toBeGreaterThanOrEqual(10);
  const status = await page.getByRole("status").filter({ hasText: /Siap dianalisis|Belum dapat dianalisis|Menstabilkan/ }).first().innerText();

  // inferensi berjalan di Worker (bukan main thread), classic worker dari origin sendiri
  expect(workers, "worker dibuat").toHaveLength(1);
  expect(new URL(workers[0]).origin).toBe(origin);
  expect(new URL(workers[0]).pathname).toBe("/mediapipe/worker/landmarker.worker.js");
  expect(await m.getAttribute("data-engine")).toBe("worker");

  const seen = JSON.stringify(assets);
  expect(Object.keys(assets).some((p) => p.endsWith(".wasm")), `wasm terlihat? ${seen}`).toBe(true);
  expect(Object.keys(assets), seen).toContain("/mediapipe/models/pose_landmarker_lite.task");
  expect(Object.keys(assets), seen).toContain("/mediapipe/models/hand_landmarker.task");
  expect(Object.values(assets).every((s) => s === 200 || s === 304), `status aset: ${seen}`).toBe(true);
  expect(w.external, "request lintas-origin").toEqual([]);
  expect(w.badResponses, "response gagal").toEqual([]);
  expect(w.consoleErrors, "error konsol").toEqual([]);

  const num = async (n: string) => Number(await m.getAttribute(n));
  const metrics = {
    NOTE: "Pengukuran lingkungan uji otomatis (Chromium headless, kamera PALSU/sintetis, container Linux). Bukan kinerja perangkat pengguna dan BUKAN bukti deteksi manusia.",
    browser: `Chromium ${browser.version()}`,
    userAgent: await page.evaluate(() => navigator.userAgent),
    cpuThreads: await page.evaluate(() => navigator.hardwareConcurrency),
    engine: "web-worker (classic, esbuild IIFE)",
    initMs: await num("data-init-ms"), workerStartupMs: await num("data-startup-ms"),
    delegate: await m.getAttribute("data-delegate"), videoResolution: await m.getAttribute("data-video"),
    frames: await num("data-frames"), submitted: await num("data-submitted"),
    droppedBackpressure: await num("data-dropped-bp"), droppedByWorker: await num("data-dropped-worker"), errors: await num("data-errors"),
    latencyMeanMs: await num("data-latency-mean"), latencyMedianMs: await num("data-latency-median"), latencyP95Ms: await num("data-latency-p95"),
    inferenceMeanMs: await num("data-proc-mean"), maxRafGapMs: await num("data-gap-max"), p95RafGapMs: await num("data-gap-p95"), maxEventLoopLagMs: await num("data-lag-max"), p95EventLoopLagMs: await num("data-lag-p95"), longTasks: await num("data-long-tasks"),
    mediapipeLibraryWarnings: [...libWarnings],
    qualityStatusShown: status, posesFrames: await num("data-poses-frames"), handsFrames: await num("data-hands-frames"),
  };
  mkdirSync("artifacts", { recursive: true });
  writeFileSync("artifacts/camera-metrics.json", JSON.stringify(metrics, null, 2));
  info.annotations.push({ type: "metrics", description: JSON.stringify(metrics) });
  expect(metrics.initMs).toBeGreaterThan(0);
  expect(metrics.errors).toBe(0);
});

test("[worker lifecycle] worker ditutup saat deteksi dimatikan, kamera dihentikan, dan saat navigasi", async ({ page }) => {
  const closed: boolean[] = [];
  page.on("worker", (wk) => { const i = closed.push(false) - 1; wk.on("close", () => { closed[i] = true; }); });
  await page.getByRole("button", { name: START }).click();
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  await expect(page.getByTestId("cam-metrics")).toBeVisible({ timeout: 90_000 });
  expect(closed).toEqual([false]);
  await page.getByRole("button", { name: /Matikan deteksi landmark/ }).click();
  // Terminasi worker dapat tertunda (probe terukur: 3–>11 s) karena panggilan GPU sinkron (software GL) tidak dapat disela.
  // Asersi tetap: worker HARUS benar-benar tertutup; batas waktu mengikuti data pengukuran dan beban host.
  await expect.poll(() => closed[0], { timeout: 45_000 }).toBe(true);
  // nyalakan lagi (worker baru), lalu keluar halaman tanpa menekan stop
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  await expect(page.getByTestId("cam-metrics")).toBeVisible({ timeout: 90_000 });
  expect(closed).toHaveLength(2);
  await page.getByRole("link", { name: "Lanjut belajar lewat pelajaran teks" }).click();
  await expect(page).toHaveURL(/\/academy/);
  await expect.poll(() => closed[1], { timeout: 45_000 }).toBe(true);
  expect((await trackStates(page)).every((t) => t.state === "ended")).toBe(true);
});

test("[worker] event pagehide menghentikan worker DAN kamera", async ({ page }) => {
  const closed: boolean[] = [];
  page.on("worker", (wk) => { const i = closed.push(false) - 1; wk.on("close", () => { closed[i] = true; }); });
  await page.getByRole("button", { name: START }).click();
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  await expect(page.getByTestId("cam-metrics")).toBeVisible({ timeout: 90_000 });
  await page.evaluate(() => window.dispatchEvent(new Event("pagehide")));
  await expect.poll(() => closed[0], { timeout: 45_000 }).toBe(true);
  await expect.poll(async () => (await trackStates(page)).every((t) => t.state === "ended")).toBe(true);
});

test("[responsivitas] main thread tetap responsif selama inferensi worker (jeda rAF terukur, bukan diasumsikan)", async ({ page }) => {
  await page.getByRole("button", { name: START }).click();
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  const m = page.getByTestId("cam-metrics");
  await expect(m).toBeVisible({ timeout: 90_000 });
  await expect.poll(async () => Number(await m.getAttribute("data-frames")), { timeout: 120_000 }).toBeGreaterThanOrEqual(5);
  // ukur sendiri dari dalam halaman selama 6 detik saat inferensi berjalan
  const r = await page.evaluate(() => new Promise<{ max: number; p95: number; n: number; longTasks: number }>((resolve) => {
    const gaps: number[] = []; let last = performance.now(), lt = 0;
    try { new PerformanceObserver((l) => { lt += l.getEntries().length; }).observe({ entryTypes: ["longtask"] }); } catch { /* tidak didukung */ }
    const end = last + 6000;
    const tick = (t: number) => { gaps.push(t - last); last = t; if (t < end) requestAnimationFrame(tick); else { gaps.sort((a, b) => a - b); resolve({ max: gaps[gaps.length - 1], p95: gaps[Math.floor(gaps.length * 0.95)], n: gaps.length, longTasks: lt }); } };
    requestAnimationFrame(tick);
  }));
  console.log(`responsivitas saat inferensi worker: ${JSON.stringify(r)}`);
  expect(r.n).toBeGreaterThan(20);
  expect(r.max, "jeda rAF terbesar (ms)").toBeLessThan(500);
  // UI tetap dapat dioperasikan saat inferensi: tombol merespons
  await page.getByRole("button", { name: /Matikan deteksi landmark/ }).click();
  await expect(page.getByTestId("cam-metrics")).toHaveCount(0);
});

test("[privasi] tidak ada storage, log, atau body request berisi frame/landmark selama kamera+deteksi", async ({ page }) => {
  const bodies: string[] = [], logs: string[] = [];
  page.on("request", (r) => { if (r.postData()) bodies.push(`${r.method()} ${r.url()}`); });
  page.on("console", (c) => logs.push(`${c.type()}: ${c.text()}`));
  await page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });
  const before = await page.evaluate(async () => ((await indexedDB.databases?.()) ?? []).map((d) => d.name));
  bodies.length = 0;
  await page.getByRole("button", { name: START }).click();
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  await expect(page.getByTestId("cam-metrics")).toBeVisible({ timeout: 90_000 });
  await expect.poll(async () => Number(await page.getByTestId("cam-metrics").getAttribute("data-frames")), { timeout: 120_000 }).toBeGreaterThanOrEqual(5);
  const state = await page.evaluate(async () => ({
    ls: Object.keys(localStorage), ss: Object.keys(sessionStorage),
    idb: ((await indexedDB.databases?.()) ?? []).map((d) => d.name), cookies: document.cookie,
  }));
  expect(bodies, "request dengan body").toEqual([]);
  expect(state.ls).toEqual([]); expect(state.ss).toEqual([]);
  expect(state.idb).toEqual(before); // tidak ada database baru
  expect(state.cookies).not.toMatch(/landmark|frame|pose/i);
  // Pola DATA nyata (koordinat/visibility/array angka). Warning internal pustaka MediaPipe (nama berkas C++ berisi kata
  // "landmark") bukan data pengguna dan dicatat terpisah di benchmark.
  const DATA = /(visibility|presence)["']?\s*[:=]\s*-?\d|\[\s*-?\d+\.\d+\s*,\s*-?\d+\.\d+|"x"\s*:\s*-?\d|ImageBitmap\s*\{|data:image\//i;
  expect(logs.filter((l) => DATA.test(l)), "console memuat data landmark/frame").toEqual([]);
});

test("[model] mematikan deteksi menghentikan pompa & worker; tombol stop tetap bekerja", async ({ page }) => {
  await page.getByRole("button", { name: START }).click();
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  await expect(page.getByTestId("cam-metrics")).toBeVisible({ timeout: 90_000 });
  await page.getByRole("button", { name: /Matikan deteksi landmark/ }).click();
  await expect(page.getByTestId("cam-metrics")).toHaveCount(0);
  await page.getByRole("button", { name: /Hentikan kamera/ }).click();
  expect((await trackStates(page)).every((t) => t.state === "ended")).toBe(true);
});

test("[kegagalan init] model tidak dapat dimuat -> pesan galat, kamera tetap aktif, worker berhenti, TANPA fallback main-thread", async ({ page }) => {
  const workers: boolean[] = [];
  page.on("worker", (wk) => { const i = workers.push(false) - 1; wk.on("close", () => { workers[i] = true; }); });
  await page.route("**/mediapipe/models/pose_landmarker_lite.task", (r) => r.abort());
  await page.getByRole("button", { name: START }).click();
  await expect(page.getByRole("button", { name: /Hentikan kamera/ })).toBeVisible();
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  const alert = page.getByRole("alert").filter({ hasText: "Mesin landmark gagal" });
  await expect(alert).toBeVisible({ timeout: 60_000 });
  await expect(alert).toContainText("Tidak ada pemrosesan cadangan");
  await expect(page.getByRole("button", { name: /Hentikan kamera/ })).toBeVisible(); // kamera tetap aktif
  await expect(page.getByTestId("cam-metrics")).toHaveCount(0);
  await expect.poll(() => workers[0], { timeout: 45_000 }).toBe(true);
  // dapat dicoba lagi setelah perbaikan (rute dilepas)
  await page.unroute("**/mediapipe/models/pose_landmarker_lite.task");
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  await expect(page.getByTestId("cam-metrics")).toBeVisible({ timeout: 90_000 });
});

test("[kegagalan init] script worker tidak dapat dimuat (404/jaringan) -> galat jelas, tidak macet", async ({ page }) => {
  await page.route("**/mediapipe/worker/landmarker.worker.js", (r) => r.abort());
  await page.getByRole("button", { name: START }).click();
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Mesin landmark gagal" })).toBeVisible({ timeout: 60_000 });
  await expect(page.getByRole("button", { name: /Hentikan kamera/ })).toBeVisible();
});

test("[visual] panel metrik saat deteksi aktif: axe (kontras, CSS ter-render) bersih, tidak overflow, label sumber SINTETIS tampil", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: START }).click();
  await page.getByRole("button", { name: /Nyalakan deteksi landmark/ }).click();
  const m = page.getByTestId("cam-metrics");
  await expect(m).toBeVisible({ timeout: 90_000 });
  await expect.poll(async () => Number(await m.getAttribute("data-frames")), { timeout: 120_000 }).toBeGreaterThanOrEqual(3);
  await expect(m).toContainText("SINTETIS");
  await expect(m).toContainText("bukan FPS produk");
  mkdirSync("artifacts/screenshots/mobile", { recursive: true });
  await page.screenshot({ path: "artifacts/screenshots/mobile/camera-check-metrics.png", fullPage: true });
  await page.setViewportSize({ width: 1440, height: 900 });
  mkdirSync("artifacts/screenshots/desktop", { recursive: true });
  await page.screenshot({ path: "artifacts/screenshots/desktop/camera-check-metrics.png", fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(0);
  const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
  expect(axe.violations.map((v) => `${v.id} x${v.nodes.length}: ${v.nodes.slice(0, 2).map((n) => n.target.join(" ")).join(" | ")}`)).toEqual([]);
});
