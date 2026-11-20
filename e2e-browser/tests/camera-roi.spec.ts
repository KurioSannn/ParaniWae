/**
 * REGRESI + BUKTI investigasi warning MediaPipe `NORM_RECT without IMAGE_DIMENSIONS`:
 *  - muncul PER INISIALISASI graph (bukan per frame), tidak bergantung pada bentuk/aspect ratio input;
 *  - mode `square-pad` (frame diberi bingkai persegi + koordinat dipetakan balik) berjalan di worker tanpa error.
 * Warning berasal dari graph internal pustaka dan tidak dapat dihilangkan dari API Tasks JS; kita menghitungnya, bukan menyembunyikannya.
 */
import { expect, test } from "@playwright/test";
import { loginUI } from "./helpers";

test.setTimeout(300_000);
test("warning NORM_RECT: per-inisialisasi (bukan per-frame), independen bentuk input; square-pad berjalan", async ({ page }) => {
  const log: { variant: string; text: string }[] = [];
  let variant = "setup";
  page.on("console", (c) => { if (c.type() === "warning") log.push({ variant, text: c.text().replace(/\d{4} \d\d:\d\d:\d\d\.\d+ \d+ /, "").slice(0, 140) }); });
  await loginUI(page, "demo-pelajar@silatara.test");
  await page.goto("/app/practice/camera-check");
  const variants = ["native-640x480", "native-640x480-squarepad", "square-pad-640x640", "square-crop-480x480", "wide-pad-854x480"];
  const out: Record<string, unknown> = {};
  for (const v of variants) {
    variant = v;
    out[v] = await page.evaluate(async (name) => {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      const video = document.createElement("video"); video.muted = true; video.srcObject = stream; await video.play();
      await new Promise((r) => setTimeout(r, 500));
      const W = video.videoWidth, H = video.videoHeight;
      const make = async () => {
        if (name.startsWith("native")) return createImageBitmap(video);  // native + varian squarepad memakai frame asli
        const [cw, ch] = name.includes("square-pad") ? [Math.max(W, H), Math.max(W, H)] : name.includes("square-crop") ? [Math.min(W, H), Math.min(W, H)] : [854, 480];
        const c = new OffscreenCanvas(cw, ch); const g = c.getContext("2d")!; g.fillStyle = "#000"; g.fillRect(0, 0, cw, ch);
        if (name.includes("crop")) g.drawImage(video, (W - cw) / 2, 0, cw, ch, 0, 0, cw, ch); else g.drawImage(video, (cw - W) / 2, (ch - H) / 2);
        return createImageBitmap(c);
      };
      const w = new Worker("/mediapipe/worker/landmarker.worker.js");
      let ready: (v: unknown) => void = () => undefined; const readyP = new Promise((r) => (ready = r));
      let pending: (() => void) | null = null; let processed = 0, poses = 0, hands = 0, errors = 0, maxLibWarnings = 0;
      w.onmessage = (e) => { const m = e.data; if (m.type === "ready") ready(m); if (m.type === "result") { processed++; maxLibWarnings = Math.max(maxLibWarnings, m.libWarnings?.normRectNoImageDims ?? 0); poses += m.frame.poses.length ? 1 : 0; hands += m.frame.hands.length ? 1 : 0; pending?.(); } if (m.type === "dropped") pending?.(); if (m.type === "error") { errors++; pending?.(); } };
      w.postMessage({ type: "init", config: { wasmBase: "/mediapipe/wasm", poseModel: "/mediapipe/models/pose_landmarker_lite.task", handModel: "/mediapipe/models/hand_landmarker.task", hands: true, maxPeople: 2, delegate: "auto", maxFrameAgeMs: 5000, libraryVersion: "1.2.3", inputShape: name.endsWith("squarepad") ? "square-pad" : "native" } });
      await readyP;
      let dims = "";
      for (let i = 0; i < 12; i++) {
        const bm = await make(); dims = `${bm.width}x${bm.height}`;
        await new Promise<void>((res) => { pending = res; w.postMessage({ type: "frame", id: i + 1, bitmap: bm, timestampMs: performance.now(), frameIndex: i, sentAtEpochMs: Date.now() }, [bm]); });
      }
      w.postMessage({ type: "dispose" }); w.terminate(); stream.getTracks().forEach((t) => t.stop());
      return { dims, processed, poses, hands, errors, maxLibWarnings };
    }, v);
  }
  const summary: Record<string, Record<string, number>> = {};
  for (const l of log) { summary[l.variant] ??= {}; summary[l.variant][l.text] = (summary[l.variant][l.text] ?? 0) + 1; }
  console.log("HASIL", JSON.stringify(out));
  for (const v of variants) {
    const o = out[v] as { processed: number; errors: number; maxLibWarnings: number };
    expect(o.processed, `${v}: semua frame diproses`).toBe(12);
    expect(o.errors, `${v}: tanpa error`).toBe(0);
    // warning per inisialisasi graph: JAUH di bawah jumlah frame (12) dan tidak bergantung bentuk input
    const n = Object.entries(summary[v] ?? {}).filter(([t]) => t.includes("NORM_RECT")).reduce((a, [, b]) => a + b, 0);
    expect(n, `${v}: warning tidak per-frame`).toBeLessThanOrEqual(3);
    expect(o.maxLibWarnings, `${v}: penghitung worker konsisten`).toBeLessThanOrEqual(3);
  }
  console.log("WARNING_PER_VARIAN", JSON.stringify(summary, null, 1));
  expect(Object.keys(out).length).toBe(5);
});
