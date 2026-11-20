/**
 * Benchmark: implementasi LAMA (inferensi sinkron di main thread) vs Web Worker, pada kamera, model,
 * resolusi, dan konfigurasi yang SAMA. Pengukuran dijalankan bergantian (A/B interleaved) dan diulang
 * beberapa kali; hasil dilaporkan sebagai median antar-run beserta tiap run. Ini mengukur JALUR KOMPUTASI
 * dan responsivitas, BUKAN akurasi atau kemampuan mendeteksi gerakan manusia.
 */
import type { InferenceConfig } from "@/features/practice/config";
import { MEDIAPIPE_PATHS, MEDIAPIPE_VERSION } from "@/features/practice/config";
import { nowMs } from "@/features/practice/metrics";
import { createFrameBitmap, FramePump, makeFrameScheduler } from "@/features/practice/pipeline";
import { ResponsivenessMonitor, type ResponsivenessSummary } from "@/features/practice/responsiveness";
import { Series } from "@/features/practice/stats";
import { WorkerLandmarkerAdapter } from "@/features/practice/worker-adapter";

export type EngineId = "main-thread-baseline" | "worker";

export interface SeriesSummary { n: number; mean: number | null; median: number | null; p95: number | null; max: number | null }

export interface RunResult {
  engine: EngineId;
  run: number;
  initMs: number | null;
  /** Hanya Worker: waktu dari pembuatan worker hingga pesan pertama. */
  workerStartupMs: number | null;
  durationMs: number;
  submitted: number;
  processed: number;
  /** Frame dilewati karena engine sibuk. Baseline sinkron tidak dapat melewati frame; ia memblokir (lihat responsivitas) -> null. */
  droppedBackpressure: number | null;
  droppedByWorker: number | null;
  latency: SeriesSummary;
  inference: SeriesSummary;
  posesDetectedFrames: number;
  handsDetectedFrames: number;
  responsiveness: ResponsivenessSummary;
  /** Heap JS main thread (hanya Chromium: performance.memory); TIDAK termasuk memori worker/WASM. */
  mainHeapMB: { before: number | null; after: number | null };
  error: string | null;
}

export interface BenchEnv {
  userAgent: string; hardwareConcurrency: number | null; deviceMemoryGB: number | null; crossOriginIsolated: boolean;
  library: string; models: { pose: string; hand: string }; config: InferenceConfig;
  video: { width: number; height: number }; source: { label: string | null; synthetic: boolean };
  framesPerRun: number; repeats: number; startedAt: string;
}

const heapMB = (): number | null => {
  const m = (performance as unknown as { memory?: { usedJSHeapSize: number } }).memory;
  return m ? m.usedJSHeapSize / 1048576 : null;
};
const sum = (s: Series): SeriesSummary => s.summary();

export function collectEnv(video: { videoWidth: number; videoHeight: number }, label: string | null, cfg: InferenceConfig, framesPerRun: number, repeats: number): BenchEnv {
  return {
    userAgent: navigator.userAgent,
    hardwareConcurrency: navigator.hardwareConcurrency ?? null,
    deviceMemoryGB: (navigator as unknown as { deviceMemory?: number }).deviceMemory ?? null,
    crossOriginIsolated: self.crossOriginIsolated ?? false,
    library: `@mediapipe/tasks-vision@${MEDIAPIPE_VERSION}`,
    models: { pose: MEDIAPIPE_PATHS.pose.split("/").pop()!, hand: MEDIAPIPE_PATHS.hand.split("/").pop()! },
    config: cfg, video: { width: video.videoWidth, height: video.videoHeight },
    source: { label, synthetic: !!label && /fake|virtual|synthetic/i.test(label) },
    framesPerRun, repeats, startedAt: new Date().toISOString(),
  };
}

interface Opts { frames: number; cfg: InferenceConfig; timeoutMs: number; run: number }

/** Implementasi LAMA: rAF + detect() sinkron di main thread, tanpa Worker. */
export async function runBaselineMain(video: HTMLVideoElement, o: Opts): Promise<RunResult> {
  const { MediaPipeAdapter } = await import("@/features/practice/mediapipe-adapter");
  const lat = new Series(), inf = new Series();
  const heapBefore = heapMB();
  const engine = new MediaPipeAdapter({ hands: o.cfg.hands, maxPeople: o.cfg.maxPeople });
  const t0 = nowMs();
  let error: string | null = null, poses = 0, hands = 0, processed = 0;
  try { await engine.init(); } catch (e) { error = e instanceof Error ? e.message : String(e); }
  const initMs = nowMs() - t0;
  const mon = new ResponsivenessMonitor();
  const started = nowMs();
  if (!error) {
    mon.start();
    await new Promise<void>((resolve) => {
      let last = -Infinity, idx = 0;
      const tick = (t: number) => {
        if (processed >= o.frames || nowMs() - started > o.timeoutMs) return resolve();
        requestAnimationFrame(tick);
        if (video.readyState < 2 || t - last < o.cfg.minIntervalMs) return;
        last = t;
        const d0 = nowMs();
        try {
          const f = engine.detect(video, t, idx++);
          const dt = nowMs() - d0;
          lat.add(dt); inf.add(dt); processed += 1;
          if (f.poses.length) poses += 1;
          if (f.hands.length) hands += 1;
        } catch (e) { error = e instanceof Error ? e.message : String(e); resolve(); }
      };
      requestAnimationFrame(tick);
    });
  }
  const responsiveness = mon.stop();
  const durationMs = nowMs() - started;
  engine.dispose();
  return {
    engine: "main-thread-baseline", run: o.run, initMs, workerStartupMs: null, durationMs, submitted: processed, processed,
    droppedBackpressure: null, droppedByWorker: null, latency: sum(lat), inference: sum(inf),
    posesDetectedFrames: poses, handsDetectedFrames: hands, responsiveness, mainHeapMB: { before: heapBefore, after: heapMB() }, error,
  };
}

/** Implementasi baru: Web Worker + FramePump (backpressure). */
export async function runWorker(video: HTMLVideoElement, o: Opts): Promise<RunResult> {
  const heapBefore = heapMB();
  const adapter = new WorkerLandmarkerAdapter(o.cfg);
  let error: string | null = null;
  const pump = new FramePump({
    adapter, source: video, config: o.cfg, createBitmap: createFrameBitmap, now: nowMs,
    schedule: makeFrameScheduler(video).schedule, cancel: makeFrameScheduler(video).cancel,
    onFatal: ({ message }) => { error = message; },
  });
  let initMs: number | null = null, startupMs: number | null = null;
  try {
    const info = await adapter.init();
    initMs = info.initMs; startupMs = info.startupMs;
  } catch (e) { error = e instanceof Error ? e.message : String(e); }
  const mon = new ResponsivenessMonitor();
  const started = nowMs();
  if (!error) {
    mon.start(); pump.start();
    await new Promise<void>((resolve) => {
      const check = () => {
        if (error || pump.stats.processed >= o.frames || nowMs() - started > o.timeoutMs) return resolve();
        setTimeout(check, 50);
      };
      check();
    });
  }
  const responsiveness = mon.stop();
  const durationMs = nowMs() - started;
  pump.stop();
  await adapter.dispose();
  return {
    engine: "worker", run: o.run, initMs, workerStartupMs: startupMs, durationMs, submitted: pump.stats.submitted, processed: pump.stats.processed,
    droppedBackpressure: pump.stats.droppedBackpressure, droppedByWorker: pump.stats.droppedByWorker,
    latency: sum(pump.latency), inference: sum(pump.proc),
    posesDetectedFrames: pump.stats.posesDetectedFrames, handsDetectedFrames: pump.stats.handsDetectedFrames,
    responsiveness, mainHeapMB: { before: heapBefore, after: heapMB() }, error,
  };
}

export interface EngineSummary {
  engine: EngineId; runs: number; okRuns: number;
  medianOfRuns: {
    initMs: number | null; workerStartupMs: number | null; latencyMedianMs: number | null; latencyMeanMs: number | null; latencyP95Ms: number | null;
    processed: number | null; droppedBackpressure: number | null; maxUiGapMs: number | null; p95UiGapMs: number | null; maxLoopLagMs: number | null; p95LoopLagMs: number | null; longTasks: number | null; longTaskTotalMs: number | null;
  };
}

const med = (xs: (number | null | undefined)[]): number | null => {
  const v = xs.filter((x): x is number => typeof x === "number").sort((a, b) => a - b);
  if (!v.length) return null;
  const m = v.length >> 1;
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
};

/** Median antar-run per mesin. Run yang error dikeluarkan dari median tetapi tetap dihitung di `runs`. */
export function summarizeRuns(results: RunResult[]): EngineSummary[] {
  const out: EngineSummary[] = [];
  for (const engine of ["main-thread-baseline", "worker"] as const) {
    const all = results.filter((r) => r.engine === engine);
    if (!all.length) continue;
    const ok = all.filter((r) => !r.error && r.processed > 0);
    out.push({
      engine, runs: all.length, okRuns: ok.length,
      medianOfRuns: {
        initMs: med(ok.map((r) => r.initMs)), workerStartupMs: med(ok.map((r) => r.workerStartupMs)),
        latencyMedianMs: med(ok.map((r) => r.latency.median)), latencyMeanMs: med(ok.map((r) => r.latency.mean)), latencyP95Ms: med(ok.map((r) => r.latency.p95)),
        processed: med(ok.map((r) => r.processed)), droppedBackpressure: med(ok.map((r) => r.droppedBackpressure)),
        maxUiGapMs: med(ok.map((r) => r.responsiveness.maxGapMs)), p95UiGapMs: med(ok.map((r) => r.responsiveness.p95GapMs)),
        maxLoopLagMs: med(ok.map((r) => r.responsiveness.loopLag.maxMs)), p95LoopLagMs: med(ok.map((r) => r.responsiveness.loopLag.p95Ms)),
        longTasks: med(ok.map((r) => r.responsiveness.longTasks.count)), longTaskTotalMs: med(ok.map((r) => r.responsiveness.longTasks.totalMs)),
      },
    });
  }
  return out;
}
