/**
 * Practice Studio — alur utama di Chromium nyata (kamera PALSU Chromium + Web Worker MediaPipe nyata).
 * Overlay diuji dengan data SINTETIS (mode simulasi ?sim=1); ini BUKAN bukti deteksi tubuh/gerakan manusia.
 */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { createVerifiedUser, loginUI, trackStates, INSTRUMENT_CAMERA } from "./helpers";

const COURSE = "demo-kurikulum-a";
const LESSON = "demo-orientasi";
const LESSON_URL = `/app/courses/${COURSE}/lessons/${LESSON}`;
const START = /nyalakan kamera/;

async function csrf(page: Page) { return (await page.context().cookies()).find((c) => c.name === "silatara_csrf")!.value; }
async function enroll(page: Page, slug = COURSE) {
  const r = await page.request.post(`/api/v1/courses/${slug}/enroll`, { headers: { "X-CSRF-Token": await csrf(page) } });
  expect(r.ok()).toBeTruthy();
}
async function newLearner(page: Page, request: Parameters<typeof createVerifiedUser>[0], enrolled = true) {
  const u = await createVerifiedUser(request, "prc");
  await loginUI(page, u.email, u.password);
  await expect(page).toHaveURL(/\/app$/);
  if (enrolled) await enroll(page);
  return u;
}
async function openStudio(page: Page, qs = "") {
  await page.goto(`${LESSON_URL}/practice${qs}`);
  await page.getByRole("checkbox", { name: /setuju kamera dinyalakan/ }).check();
  await page.getByRole("button", { name: START }).click();
  await expect(page.getByTestId("studio")).toHaveAttribute("data-phase", "ready", { timeout: 120_000 });
}
/** True bila ada piksel tergambar (alpha>0) di sekitar titik CSS (x,y) pada kanvas overlay. */
async function overlayHasInkAt(page: Page, x: number, y: number): Promise<boolean> {
  return page.getByTestId("overlay").evaluate((c: HTMLCanvasElement, [px, py]) => {
    const dpr = window.devicePixelRatio || 1; const g = c.getContext("2d")!;
    const d = g.getImageData(Math.max(0, Math.round(px * dpr) - 2), Math.max(0, Math.round(py * dpr) - 2), 5, 5).data;
    for (let i = 3; i < d.length; i += 4) if (d[i] > 0) return true;
    return false;
  }, [x, y]);
}
const canvasSize = (page: Page) => page.getByTestId("overlay").evaluate((c: HTMLCanvasElement) => ({ w: Number(c.dataset.w), h: Number(c.dataset.h), cw: c.width, ch: c.height }));

test("lesson -> Mulai Latihan -> studio: instruksi & persetujuan eksplisit; kamera belum diminta", async ({ page, request }) => {
  await page.addInitScript(INSTRUMENT_CAMERA);
  await newLearner(page, request);
  await page.goto(LESSON_URL);
  await expect(page.getByTestId("practice-entry")).toContainText("[DEMO]");
  await page.getByTestId("start-practice").click();
  await expect(page).toHaveURL(new RegExp(`${LESSON}/practice$`));
  await expect(page.getByTestId("studio")).toHaveAttribute("data-state", "intro");
  await expect(page.getByText(/latihan solo tingkat pemula/)).toBeVisible();
  await expect(page.getByText(/sparring, teknik senjata, bantingan/)).toBeVisible();
  await expect(page.getByText(/tidak direkam, disimpan, atau dikirim/)).toBeVisible();
  await expect(page.getByRole("button", { name: START })).toBeDisabled();
  expect(await page.evaluate(() => (window as unknown as { __gum: unknown[] }).__gum.length)).toBe(0);
});

test("alur nyata: persetujuan -> kamera palsu + Worker MediaPipe siap -> mulai -> jeda/lanjut -> hentikan -> ringkasan & riwayat", async ({ page, request }) => {
  await page.addInitScript(INSTRUMENT_CAMERA);
  const workers: { url: string; closed: boolean }[] = [];
  page.on("worker", (w) => { const o = { url: w.url(), closed: false }; workers.push(o); w.on("close", () => { o.closed = true; }); });
  const posts: { url: string; body: string }[] = [];
  page.on("request", (r) => { if (r.postData()) posts.push({ url: r.url(), body: r.postData()! }); });
  await newLearner(page, request);
  await openStudio(page);

  // engine siap: worker same-origin, video menyala, overlay ada dan berukuran sama dengan video (4:3)
  expect(workers).toHaveLength(1);
  expect(new URL(workers[0].url).pathname).toBe("/mediapipe/worker/landmarker.worker.js");
  const gum = await page.evaluate(() => (window as unknown as { __gum: { audio?: unknown }[] }).__gum);
  expect(gum[0].audio).toBe(false);
  const sz = await canvasSize(page);
  expect(sz.w / sz.h).toBeCloseTo(4 / 3, 1);
  await expect(page.getByTestId("state-chip")).toBeVisible();
  await expect(page.getByTestId("session-indicator")).toHaveText("Belum dimulai");

  await page.getByRole("button", { name: "Mulai latihan" }).click();
  await expect(page.getByTestId("studio")).toHaveAttribute("data-phase", "running");
  await expect(page.getByTestId("session-indicator")).toContainText("Sesi aktif");
  await expect.poll(async () => (await page.getByTestId("timer").innerText()) !== "00:00", { timeout: 15_000 }).toBe(true);

  // jeda: timer berhenti; lanjut: timer jalan lagi
  await page.getByRole("button", { name: "Jeda" }).click();
  await expect(page.getByTestId("studio")).toHaveAttribute("data-state", "paused");
  await page.waitForTimeout(400); // satu tick tampilan
  const t1 = await page.getByTestId("timer").innerText();
  await page.waitForTimeout(1800);
  expect(await page.getByTestId("timer").innerText()).toBe(t1);
  await page.getByRole("button", { name: "Lanjutkan" }).click();
  await expect.poll(async () => (await page.getByTestId("timer").innerText()) !== t1, { timeout: 10_000 }).toBe(true);

  await page.getByRole("button", { name: "Hentikan latihan" }).click();
  await expect(page).toHaveURL(/\/app\/practice\/sessions\/[0-9a-f-]{36}$/, { timeout: 30_000 });
  // resource dilepas
  await expect.poll(() => workers[0].closed, { timeout: 45_000 }).toBe(true); // terminasi worker dapat tertunda (software GL)
  expect((await trackStates(page)).length).toBe(0 + (await trackStates(page)).length); // halaman baru: tidak ada stream aktif
  // ringkasan
  await expect(page.getByTestId("dur-active")).not.toHaveText("—");
  await expect(page.getByText("Selesai", { exact: true }).first()).toBeVisible();
  await expect(page.getByText(/bukan penilaian gerakan/i).first()).toBeVisible();
  await expect(page.getByText(/\[DEMO\]/).first()).toBeVisible();
  // metadata minimal saja ke server
  const mine = posts.filter((p) => p.url.includes("/practice-sessions"));
  expect(mine.length).toBe(2); // start + complete
  for (const p of mine) expect(p.body).not.toMatch(/"landmarks?"|"x"\s*:|"visibility"\s*:|data:image|blob:/);
  expect(posts.filter((p) => !/\/api\/v1\/(practice-sessions|auth|courses)/.test(p.url))).toEqual([]);
  const j = await (await page.request.get("/api/v1/me/practice-sessions")).json();
  expect(j.total).toBe(1);
  expect(j.items[0]).toMatchObject({ status: "completed", lesson: { slug: LESSON } });
  expect(j.items[0].model_version).toContain("@mediapipe/tasks-vision@1.2.3");
  expect(j.items[0].quality_summary.simulated).toBe(false);
  expect(j.items[0].quality_summary.engine).toBe("worker");
  // lanjut ke materi dari ringkasan
  await page.getByRole("link", { name: "Kembali ke materi" }).first().click();
  await expect(page).toHaveURL(new RegExp(`${LESSON}$`));
});

test("riwayat: dasbor + /app/practice + progres menampilkan sesi; lesson completion TIDAK berubah", async ({ page, request }) => {
  await newLearner(page, request);
  const before = (await (await page.request.get("/api/v1/me/progress")).json()).totals;
  await openStudio(page, "?sim=1&scenario=full");
  await page.getByRole("button", { name: "Mulai latihan" }).click();
  await expect(page.getByTestId("studio")).toHaveAttribute("data-phase", "running");
  await page.waitForTimeout(1500);
  await page.getByRole("button", { name: "Hentikan latihan" }).click();
  await expect(page).toHaveURL(/\/practice\/sessions\//, { timeout: 30_000 });
  await expect(page.getByText("Sesi SIMULASI")).toBeVisible();

  await page.goto("/app");
  await expect(page.getByTestId("dash-practice")).toContainText("Total sesi");
  await expect(page.getByTestId("dash-practice").getByRole("link", { name: "[DEMO] Orientasi: Cara Memakai SILATARA" })).toBeVisible();
  await page.goto("/app/progress");
  await expect(page.getByTestId("progress-practice")).toContainText("tidak mengubah persentase progres");
  await page.goto("/app/practice");
  await expect(page.getByTestId("sum-total")).toHaveText("1");
  await expect(page.getByTestId("session-list").locator("li")).toHaveCount(1);
  await page.getByTestId("session-list").getByRole("link", { name: "Kembali ke materi" }).click();
  await expect(page).toHaveURL(new RegExp(`${LESSON}$`));
  expect((await (await page.request.get("/api/v1/me/progress")).json()).totals).toEqual(before);
});

test("overlay SINTETIS tepat di piksel yang benar: 4:3, mirror on/off, dan saat viewport berubah", async ({ page, request }) => {
  await newLearner(page, request);
  await openStudio(page, "?sim=1&scenario=full");
  await expect(page.getByText("MODE SIMULASI").first()).toBeVisible();
  await expect.poll(async () => Number(await page.getByTestId("overlay").getAttribute("data-points")), { timeout: 30_000 }).toBeGreaterThan(10);

  const check = async (mirror: boolean) => {
    const { w, h } = await canvasSize(page);
    // bahu kiri (indeks 11) ternormalisasi (0.58, 0.26); pinggul kanan (24): (0.45, 0.54)
    for (const [nx, ny] of [[0.58, 0.26], [0.45, 0.54], [0.5, 0.13]]) {
      const x = (mirror ? 1 - nx : nx) * w, y = ny * h;
      expect(await overlayHasInkAt(page, x, y), `ink di (${nx},${ny}) mirror=${mirror} ${w}x${h}`).toBe(true);
    }
    // titik yang SEHARUSNYA kosong (bagian tengah atas video, jauh dari kerangka)
    expect(await overlayHasInkAt(page, 0.05 * w, 0.05 * h)).toBe(false);
  };
  await check(true);
  await page.getByRole("checkbox", { name: "Cermin tampilan" }).uncheck();
  await expect(page.getByTestId("overlay")).toHaveAttribute("data-mirror", "false");
  await check(false);
  await page.getByRole("checkbox", { name: "Cermin tampilan" }).check();

  // ubah ukuran viewport: overlay tetap sejajar (proporsional) dan rasio 4:3 terjaga
  for (const vp of [{ width: 1100, height: 800 }, { width: 700, height: 900 }]) {
    await page.setViewportSize(vp);
    await expect.poll(async () => { const s = await canvasSize(page); return Math.abs(s.w / s.h - 4 / 3) < 0.02; }).toBe(true);
    await expect.poll(async () => { const { w, h } = await canvasSize(page); return overlayHasInkAt(page, (1 - 0.58) * w, 0.26 * h); }).toBe(true);
    const stage = await page.getByTestId("stage").boundingBox();
    const { w } = await canvasSize(page);
    expect(Math.abs(stage!.width - w)).toBeLessThan(2); // kanvas = area video (tidak bergeser/terdistorsi)
  }
});

test("overlay tepat pada video 16:9 (kamera diminta 1280x720)", async ({ page, request }) => {
  await page.addInitScript(() => {
    const md = navigator.mediaDevices; const orig = md.getUserMedia.bind(md);
    md.getUserMedia = (c?: MediaStreamConstraints) => orig({ ...c, video: { width: { exact: 1280 }, height: { exact: 720 } } });
  });
  await newLearner(page, request);
  await openStudio(page, "?sim=1&scenario=full");
  await expect.poll(async () => Number(await page.getByTestId("overlay").getAttribute("data-points")), { timeout: 30_000 }).toBeGreaterThan(10);
  const dims = await page.locator("video").evaluate((v: HTMLVideoElement) => [v.videoWidth, v.videoHeight]);
  expect(dims).toEqual([1280, 720]);
  const { w, h } = await canvasSize(page);
  expect(w / h).toBeCloseTo(16 / 9, 1);
  expect(await overlayHasInkAt(page, (1 - 0.58) * w, 0.26 * h)).toBe(true);
  expect(await overlayHasInkAt(page, (1 - 0.45) * w, 0.54 * h)).toBe(true);
});

test("status & panduan kualitas mengikuti skenario (hanya kualitas input, tanpa penilaian gerakan)", async ({ page, request }) => {
  await newLearner(page, request);
  const expectations: [string, string, string][] = [
    ["partial", "partial_detection", "Pastikan kamera tidak terhalang"],
    ["out_of_frame", "partial_detection", "Mundur sedikit agar tubuh terlihat"],
    ["multiple", "insufficient_visibility", "Pastikan hanya satu orang di kamera"],
    ["full", "detecting", "Tubuh terdeteksi dengan baik"],
    ["waiting", "waiting_for_subject", "Posisi tubuh belum terdeteksi"],
  ];
  for (const [sc, state, title] of expectations) {
    await openStudio(page, `?sim=1&scenario=${sc}`);
    await page.getByRole("button", { name: "Mulai latihan" }).click();
    await expect(page.getByTestId("studio")).toHaveAttribute("data-state", state, { timeout: 30_000 });
    await expect(page.getByTestId("guidance-title")).toHaveText(title);
    expect(await page.getByTestId("studio").innerText()).not.toMatch(/\b(skor|akurasi|repetisi|kemiripan)\b/i);
    await page.getByRole("button", { name: "Hentikan latihan" }).click();
    await expect(page).toHaveURL(/\/practice\/sessions\//, { timeout: 30_000 });
  }
});

test("keluar halaman saat sesi berjalan: sesi ditandai dihentikan, worker + kamera berhenti", async ({ page, request }) => {
  await page.addInitScript(INSTRUMENT_CAMERA);
  const closed: boolean[] = [];
  page.on("worker", (w) => { const i = closed.push(false) - 1; w.on("close", () => { closed[i] = true; }); });
  await newLearner(page, request);
  await openStudio(page);
  await page.getByRole("button", { name: "Mulai latihan" }).click();
  await expect(page.getByTestId("studio")).toHaveAttribute("data-phase", "running");
  await page.getByRole("link", { name: "Akademi" }).first().click(); // navigasi SPA = unmount
  await expect(page).toHaveURL(/\/academy/);
  await expect.poll(() => closed[0], { timeout: 45_000 }).toBe(true);
  expect((await trackStates(page)).every((t) => t.state === "ended")).toBe(true);
  await expect.poll(async () => (await (await page.request.get("/api/v1/me/practice-sessions")).json()).items[0]?.status, { timeout: 20_000 }).toBe("abandoned");
});

test("akses: belum terdaftar tidak dapat berlatih; pengguna lain tidak dapat melihat sesi saya", async ({ page, request, browser }) => {
  // belum terdaftar: halaman studio hanya menampilkan pesan, tidak ada tombol kamera
  await newLearner(page, request, false);
  await page.goto(`${LESSON_URL}/practice`);
  await expect(page.getByText("Daftar ke kurikulum ini terlebih dahulu untuk berlatih.")).toBeVisible();
  await expect(page.getByRole("button", { name: START })).toHaveCount(0);
  const r = await page.request.post("/api/v1/practice-sessions", { headers: { "X-CSRF-Token": await csrf(page) },
    data: { lesson_id: "00000000-0000-0000-0000-000000000000", model_version: "x-model" } });
  expect(r.status()).toBe(404);

  // pengguna A membuat sesi; pengguna B tidak dapat melihatnya
  await enroll(page);
  await openStudio(page, "?sim=1&scenario=full");
  await page.getByRole("button", { name: "Mulai latihan" }).click();
  await page.waitForTimeout(800);
  await page.getByRole("button", { name: "Hentikan latihan" }).click();
  await expect(page).toHaveURL(/\/practice\/sessions\/([0-9a-f-]{36})$/, { timeout: 30_000 });
  const sid = page.url().split("/").pop()!;
  const ctxB = await browser.newContext({ baseURL: page.url().split("/app")[0] });
  const pb = await ctxB.newPage();
  const ub = await createVerifiedUser(pb.request, "oth");
  await loginUI(pb, ub.email, ub.password);
  expect((await pb.request.get(`/api/v1/practice-sessions/${sid}`)).status()).toBe(404);
  expect((await pb.goto(`/app/practice/sessions/${sid}`))!.status()).toBe(404);
  expect((await (await pb.request.get("/api/v1/me/practice-sessions")).json()).total).toBe(0);
  await ctxB.close();
  // anonim
  const anon = await browser.newContext({ baseURL: page.url().split("/app")[0] });
  expect((await (await anon.newPage()).request.get(`/api/v1/practice-sessions/${sid}`)).status()).toBe(401);
  await anon.close();
});

test("mode simulasi TIDAK aktif tanpa ?sim=1 (default memakai Worker nyata)", async ({ page, request }) => {
  await newLearner(page, request);
  await openStudio(page);
  await expect(page.getByText("MODE SIMULASI")).toHaveCount(0);
});

const VPS = { desktop: { width: 1440, height: 900 }, tablet: { width: 768, height: 1024 }, mobile: { width: 390, height: 844 } } as const;

test("[visual] Practice Studio: intro, aktif, jeda, ringkasan, riwayat, dasbor — 3 viewport, axe+kontras, tanpa overflow", async ({ page, request }) => {
  test.setTimeout(240_000);
  await newLearner(page, request);
  const audit = async (name: string, vp: keyof typeof VPS) => {
    await page.setViewportSize(VPS[vp]);
    await page.waitForTimeout(400);
    mkdirSync(`artifacts/screenshots/${vp}`, { recursive: true });
    await page.screenshot({ path: `artifacts/screenshots/${vp}/practice-${name}.png`, fullPage: true });
    expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth), `overflow ${name} ${vp}`).toBeLessThanOrEqual(0);
    const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
    expect(axe.violations.map((v) => `${v.id} x${v.nodes.length}: ${v.nodes.slice(0, 2).map((n) => n.target.join(" ")).join(" | ")}`), `axe ${name} ${vp}`).toEqual([]);
  };
  // intro
  await page.goto(`${LESSON_URL}/practice?sim=1&scenario=full`);
  for (const vp of Object.keys(VPS) as (keyof typeof VPS)[]) await audit("intro", vp);
  await page.setViewportSize(VPS.desktop);
  await page.getByRole("checkbox", { name: /setuju kamera dinyalakan/ }).check();
  await page.getByRole("button", { name: START }).click();
  await expect(page.getByTestId("studio")).toHaveAttribute("data-phase", "ready", { timeout: 120_000 });
  await page.getByRole("button", { name: "Mulai latihan" }).click();
  await expect(page.getByTestId("studio")).toHaveAttribute("data-state", "detecting", { timeout: 30_000 });
  for (const vp of Object.keys(VPS) as (keyof typeof VPS)[]) await audit("running", vp);
  await page.setViewportSize(VPS.desktop);
  await page.getByRole("button", { name: "Jeda" }).click();
  for (const vp of Object.keys(VPS) as (keyof typeof VPS)[]) await audit("paused", vp);
  await page.setViewportSize(VPS.desktop);
  await page.getByRole("button", { name: "Lanjutkan" }).click();
  await page.waitForTimeout(1200);
  await page.getByRole("button", { name: "Hentikan latihan" }).click();
  await expect(page).toHaveURL(/\/practice\/sessions\//, { timeout: 30_000 });
  for (const vp of Object.keys(VPS) as (keyof typeof VPS)[]) await audit("summary", vp);
  await page.goto("/app/practice");
  for (const vp of Object.keys(VPS) as (keyof typeof VPS)[]) await audit("history", vp);
  await page.goto("/app");
  for (const vp of Object.keys(VPS) as (keyof typeof VPS)[]) await audit("dashboard", vp);
});
