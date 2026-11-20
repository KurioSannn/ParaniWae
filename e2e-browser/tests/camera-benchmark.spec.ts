/**
 * BENCHMARK A/B: implementasi lama (sinkron di main thread) vs Web Worker, pada kamera PALSU (sintetis),
 * model/resolusi/konfigurasi yang sama, bergantian (interleaved) dan diulang. Ini benchmark JALUR KOMPUTASI,
 * BUKAN benchmark pose manusia dan BUKAN pengukuran akurasi. Hasil: artifacts/benchmark.json.
 */
import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { loginUI } from "./helpers";

test.setTimeout(1_200_000);
// Opt-in (±6 menit, tab sengaja dibekukan oleh baseline): make bench   (RUN_BENCH=1)
test.skip(!process.env.RUN_BENCH, "set RUN_BENCH=1 (make bench) untuk menjalankan benchmark A/B");

test("benchmark baseline main-thread vs Worker (sintetis)", async ({ page, browser }) => {
  await loginUI(page, "demo-pelajar@silatara.test");
  await page.goto("/app/practice/benchmark");
  await page.getByRole("button", { name: /nyalakan kamera/ }).click();
  await expect(page.getByRole("button", { name: "Hentikan kamera" })).toBeVisible();
  await page.getByLabel("Frame per run").fill(process.env.BENCH_FRAMES ?? "40");
  await page.getByLabel("Ulangan").fill(process.env.BENCH_REPEATS ?? "3");
  const warnings: { phase: string; text: string }[] = [];
  let phase = "setup";
  page.on("console", (c) => { if (c.type() === "warning") { const t = c.text().replace(/\d{4} \d\d:\d\d:\d\d\.\d+ \d+ /, ""); if (!warnings.some((w) => w.phase === phase && w.text === t)) warnings.push({ phase, text: t }); } });
  const poll = setInterval(async () => { try { const st = await page.getByRole("status").last().innerText({ timeout: 200 }); if (/Run \d/.test(st)) phase = st.includes("Worker") ? "worker" : "main-thread-baseline"; } catch { /* sibuk (tab membeku) */ } }, 300);
  await page.getByRole("button", { name: "Jalankan benchmark" }).click();
  await expect(page.getByRole("button", { name: "Berjalan…" })).toBeVisible();
  await expect(page.getByText("Selesai.")).toBeVisible({ timeout: 1_100_000 });
  clearInterval(poll);
  await page.getByText("Data mentah (JSON").click();
  const raw = await page.getByTestId("bench-json").innerText();
  const data = JSON.parse(raw);
  const out = { ...data, mediapipeLibraryWarningsByPhase: warnings, runner: { browser: `Chromium ${browser.version()}`, harness: "Playwright, headless, container Linux (Docker Desktop)", note: "Sumber SINTETIS (kamera palsu Chromium): memvalidasi jalur komputasi; BUKAN deteksi/benchmark pose manusia; BUKAN FPS produk." } };
  mkdirSync("artifacts", { recursive: true });
  writeFileSync("artifacts/benchmark.json", JSON.stringify(out, null, 2));

  expect(data.environment.source.synthetic).toBe(true);
  const w = data.summary.find((s: { engine: string }) => s.engine === "worker");
  const b = data.summary.find((s: { engine: string }) => s.engine === "main-thread-baseline");
  expect(w.okRuns, "run Worker valid").toBeGreaterThan(0);
  expect(b.okRuns, "run baseline valid").toBeGreaterThan(0);
  expect(w.medianOfRuns.processed).toBeGreaterThan(0);
  // klaim yang diuji (terukur, bukan diasumsikan): Worker tidak memblokir main thread lebih parah dari baseline
  expect(w.medianOfRuns.maxUiGapMs).toBeLessThan(b.medianOfRuns.maxUiGapMs);
  console.log("RINGKASAN", JSON.stringify(data.summary));
});
