/**
 * Worker landmark (classic worker, di-bundle menjadi IIFE oleh esbuild -> public/mediapipe/worker/).
 * Dipilih classic worker karena MediaPipe memuat loader wasm lewat `importScripts` (tidak tersedia di module worker).
 *
 * Privasi: worker TIDAK memiliki jalur jaringan ke server aplikasi untuk data pengguna. Satu-satunya akses
 * jaringan adalah MediaPipe memuat wasm + model dari origin sendiri. Frame/landmark hanya dikembalikan ke
 * main thread lewat postMessage; tidak ada penyimpanan, logging, atau telemetri.
 */
import { FilesetResolver, HandLandmarker, PoseLandmarker } from "@mediapipe/tasks-vision";
import { unpadLandmark, squarePad } from "../letterbox";
import { toLandmarkFrame } from "./convert";
import type { FromWorker, ToWorker, WorkerInitConfig } from "./protocol";

interface Ctx {
  postMessage(m: FromWorker): void;
  onmessage: ((e: MessageEvent<ToWorker>) => void) | null;
  close(): void;
}
const ctx = self as unknown as Ctx;

type Detector<R> = { detectForVideo(src: ImageBitmap, ts: number): R; close(): void };
let pose: Detector<{ landmarks: never[][]; worldLandmarks?: never[][] }> | null = null;
let hand: Detector<{ landmarks: never[][]; handedness: never[][] }> | null = null;
let state: "idle" | "loading" | "ready" | "paused" | "disposed" = "idle";
let lastTs = -1;
let maxAge = 500;
let delegateUsed: string | null = null;

const send = (m: FromWorker) => ctx.postMessage(m);

// Hitung (JANGAN sembunyikan) warning internal MediaPipe; tetap diteruskan ke console asli.
let normRectNoImageDims = 0;
const origWarn = console.warn.bind(console);
console.warn = (...a: unknown[]) => {
  if (String(a[0]).includes("NORM_RECT without IMAGE_DIMENSIONS")) normRectNoImageDims += 1;
  origWarn(...a);
};
let inputShape: "native" | "square-pad" = "native";
let padCanvas: OffscreenCanvas | null = null;

async function init(cfg: WorkerInitConfig) {
  if (state !== "idle") return;
  state = "loading";
  send({ type: "status", state: "loading" });
  maxAge = cfg.maxFrameAgeMs;
  inputShape = cfg.inputShape ?? "native";
  const t0 = performance.now();
  try {
    const fileset = await FilesetResolver.forVisionTasks(cfg.wasmBase);
    const tryDelegates = cfg.delegate === "auto" ? (["GPU", "CPU"] as const) : ([cfg.delegate] as const);
    const make = async <T,>(create: (d: "GPU" | "CPU") => Promise<T>): Promise<T> => {
      let lastErr: unknown;
      for (const d of tryDelegates) {
        try {
          const r = await create(d);
          delegateUsed = delegateUsed ?? d;
          return r;
        } catch (e) {
          lastErr = e;
        }
      }
      throw lastErr;
    };
    pose = (await make((delegate) => PoseLandmarker.createFromOptions(fileset, {
      baseOptions: { modelAssetPath: cfg.poseModel, delegate }, runningMode: "VIDEO", numPoses: cfg.maxPeople,
    }))) as unknown as typeof pose;
    if (cfg.hands) {
      hand = (await make((delegate) => HandLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: cfg.handModel, delegate }, runningMode: "VIDEO", numHands: 2,
      }))) as unknown as typeof hand;
    }
    state = "ready";
    send({ type: "ready", initMs: performance.now() - t0, delegate: delegateUsed, library: `@mediapipe/tasks-vision@${cfg.libraryVersion}` });
    send({ type: "status", state: "ready" });
  } catch (e) {
    state = "disposed";
    send({ type: "error", fatal: true, code: "INIT_FAILED", message: e instanceof Error ? e.message : String(e) });
  }
}

function frame(m: Extract<ToWorker, { type: "frame" }>) {
  const { bitmap } = m;
  try {
    if (state === "paused") return send({ type: "dropped", id: m.id, reason: "paused" });
    if (state !== "ready" || !pose) return send({ type: "dropped", id: m.id, reason: "not_ready" });
    if (Date.now() - m.sentAtEpochMs > maxAge) return send({ type: "dropped", id: m.id, reason: "stale" });
    const ts = Math.max(m.timestampMs, lastTs + 1); // MediaPipe VIDEO mode butuh timestamp naik
    lastTs = ts;
    const t0 = performance.now();
    let src: ImageBitmap | OffscreenCanvas = bitmap;
    const w = bitmap.width, hgt = bitmap.height;
    if (inputShape === "square-pad") {
      const { size, padX, padY } = squarePad(w, hgt);
      if (!padCanvas || padCanvas.width !== size) padCanvas = new OffscreenCanvas(size, size);
      const g = padCanvas.getContext("2d")!;
      g.fillStyle = "#000"; g.fillRect(0, 0, size, size); g.drawImage(bitmap, padX, padY);
      src = padCanvas;
    }
    const p = pose.detectForVideo(src as ImageBitmap, ts);
    const h = hand ? hand.detectForVideo(src as ImageBitmap, ts) : null;
    const procMs = performance.now() - t0;
    const out = toLandmarkFrame(p, h, { timestampMs: m.timestampMs, width: w, height: hgt, frameIndex: m.frameIndex });
    if (inputShape === "square-pad") {
      for (const po of out.poses) po.landmarks = po.landmarks.map((l) => unpadLandmark(l, w, hgt));
      for (const ha of out.hands) ha.landmarks = ha.landmarks.map((l) => unpadLandmark(l, w, hgt));
    }
    send({ type: "result", id: m.id, procMs, frame: out, libWarnings: { normRectNoImageDims } });
  } catch (e) {
    send({ type: "error", fatal: false, code: "DETECT_FAILED", id: m.id, message: e instanceof Error ? e.message : String(e) });
  } finally {
    bitmap.close(); // selalu lepaskan ImageBitmap yang ditransfer
  }
}

function dispose() {
  if (state === "disposed") return;
  try { pose?.close(); hand?.close(); } catch { /* abaikan */ }
  pose = hand = null;
  state = "disposed";
  send({ type: "status", state: "disposed" });
  ctx.close();
}

ctx.onmessage = (e) => {
  const m = e.data;
  switch (m.type) {
    case "init": void init(m.config); break;
    case "frame": frame(m); break;
    case "pause": if (state === "ready") { state = "paused"; send({ type: "status", state: "paused" }); } break;
    case "resume": if (state === "paused") { state = "ready"; send({ type: "status", state: "ready" }); } break;
    case "dispose": dispose(); break;
  }
};
