import type { AsyncLandmarkerAdapter } from "@/features/practice/async-adapter";
import type { InferenceConfig } from "@/features/practice/config";
import type { LandmarkFrame } from "@/features/practice/landmarks";
import { Series } from "@/features/practice/stats";

export interface FrameSource { videoWidth: number; videoHeight: number; readyState: number }

export interface PumpStats {
  submitted: number;
  processed: number;
  /** Frame yang DILEWATI karena engine masih sibuk (backpressure). */
  droppedBackpressure: number;
  /** Frame yang dibuang worker (stale/paused/not_ready). */
  droppedByWorker: number;
  /** Frame yang tidak pernah kembali (dianggap hilang setelah timeout). */
  lost: number;
  errors: number;
  posesDetectedFrames: number;
  handsDetectedFrames: number;
  /** Warning internal pustaka (NORM_RECT tanpa IMAGE_DIMENSIONS) yang dilaporkan worker; tidak disembunyikan. */
  libNormRectWarnings: number;
}

export interface PumpDeps {
  adapter: AsyncLandmarkerAdapter;
  source: FrameSource;
  config: InferenceConfig;
  createBitmap(src: FrameSource, maxWidth: number | null): Promise<ImageBitmap>;
  now(): number;
  schedule(cb: (t: number) => void): number;
  cancel(h: number): void;
  onResult?(r: { id: number; frame: LandmarkFrame; latencyMs: number; procMs: number }): void;
  onFatal?(e: { code: string; message: string }): void;
  onNonFatalError?(message: string): void;
  onState?(s: "loading" | "ready" | "paused" | "disposed"): void;
}

const LOST_TIMEOUT_MS = 5000;

/**
 * Menjadwalkan pengiriman frame ke engine asinkron dengan BACKPRESSURE:
 * - tidak ada antrean tak terbatas: maksimum `maxInFlight` frame di engine;
 * - frame baru dilewati (dihitung `droppedBackpressure`) selama engine penuh;
 * - pembatasan frekuensi (`minIntervalMs`) bukan "drop" — itu konfigurasi;
 * - semua ImageBitmap yang tidak jadi dikirim ditutup (tanpa kebocoran).
 */
export class FramePump {
  readonly stats: PumpStats = { submitted: 0, processed: 0, droppedBackpressure: 0, droppedByWorker: 0, lost: 0, errors: 0, posesDetectedFrames: 0, handsDetectedFrames: 0, libNormRectWarnings: 0 };
  readonly latency = new Series();
  readonly proc = new Series();
  private running = false;
  private paused = false;
  private handle: number | null = null;
  private inFlight = 0;
  private seq = 0;
  private lastSubmitAt = Number.NEGATIVE_INFINITY;
  private pending = new Map<number, number>();

  constructor(private readonly d: PumpDeps) {
    d.adapter.setHandlers({
      onResult: (r) => {
        const sent = this.pending.get(r.id);
        if (sent === undefined) return; // sudah dianggap hilang
        this.pending.delete(r.id);
        this.inFlight = Math.max(0, this.inFlight - 1);
        const latencyMs = this.d.now() - sent;
        this.stats.processed += 1;
        this.latency.add(latencyMs);
        this.proc.add(r.procMs);
        if (r.libWarnings) this.stats.libNormRectWarnings = r.libWarnings.normRectNoImageDims;
        if (r.frame.poses.length) this.stats.posesDetectedFrames += 1;
        if (r.frame.hands.length) this.stats.handsDetectedFrames += 1;
        this.d.onResult?.({ id: r.id, frame: r.frame, latencyMs, procMs: r.procMs });
      },
      onDropped: (r) => {
        if (this.pending.delete(r.id)) { this.inFlight = Math.max(0, this.inFlight - 1); this.stats.droppedByWorker += 1; }
      },
      onState: (st) => this.d.onState?.(st),
      onError: (e) => {
        if (e.fatal) { this.stop(); this.d.onFatal?.({ code: e.code, message: e.message }); return; }
        this.stats.errors += 1;
        this.d.onNonFatalError?.(e.message);
        // frame yang gagal diproses dilepas lewat watchdog "lost" bila id tidak diketahui
      },
    });
  }

  get isRunning(): boolean { return this.running; }
  get inFlightCount(): number { return this.inFlight; }

  start(): void {
    if (this.running) return;
    this.running = true;
    this.handle = this.d.schedule(this.tick);
  }

  /** Idempoten. Membatalkan jadwal; bitmap yang sedang dibuat akan ditutup saat selesai. */
  stop(): void {
    this.running = false;
    if (this.handle !== null) this.d.cancel(this.handle);
    this.handle = null;
    this.pending.clear();
    this.inFlight = 0;
  }

  setPaused(p: boolean): void {
    if (p === this.paused) return;
    this.paused = p;
    if (p) this.d.adapter.pause(); else this.d.adapter.resume();
  }

  private tick = (t: number): void => {
    if (!this.running) return;
    this.handle = this.d.schedule(this.tick);
    if (this.paused || this.d.source.readyState < 2) return;
    this.reapLost();
    if (t - this.lastSubmitAt < this.d.config.minIntervalMs) return;
    if (this.inFlight >= this.d.config.maxInFlight) { this.stats.droppedBackpressure += 1; return; }
    this.lastSubmitAt = t;
    this.inFlight += 1; // pesan tempat SEBELUM await agar tidak ada frame paralel
    const id = ++this.seq;
    this.d.createBitmap(this.d.source, this.d.config.maxFrameWidth).then((bm) => {
      if (!this.running || this.paused) { bm.close(); this.inFlight = Math.max(0, this.inFlight - 1); return; }
      this.pending.set(id, this.d.now());
      this.stats.submitted += 1;
      this.d.adapter.submit(bm, t, id, id);
    }).catch(() => {
      this.inFlight = Math.max(0, this.inFlight - 1);
      this.stats.errors += 1;
    });
  };

  private reapLost(): void {
    const now = this.d.now();
    for (const [id, sent] of this.pending) {
      if (now - sent > LOST_TIMEOUT_MS) {
        this.pending.delete(id);
        this.inFlight = Math.max(0, this.inFlight - 1);
        this.stats.lost += 1;
      }
    }
  }
}

/** Implementasi bitmap bawaan browser. `maxWidth` null = resolusi asli (tidak ada penurunan diam-diam). */
export async function createFrameBitmap(src: FrameSource, maxWidth: number | null): Promise<ImageBitmap> {
  const video = src as unknown as HTMLVideoElement;
  if (maxWidth && src.videoWidth > maxWidth) {
    const h = Math.round((src.videoHeight * maxWidth) / src.videoWidth);
    return createImageBitmap(video, { resizeWidth: maxWidth, resizeHeight: h });
  }
  return createImageBitmap(video);
}

/**
 * Penjadwal per-FRAME VIDEO (requestVideoFrameCallback) bila didukung, agar hitungan frame yang dilewati
 * mencerminkan frame kamera sebenarnya (bukan tick rAF 60 Hz). Fallback ke requestAnimationFrame.
 */
export function makeFrameScheduler(video: HTMLVideoElement): { schedule: (cb: (t: number) => void) => number; cancel: (h: number) => void; kind: "video-frame" | "animation-frame" } {
  const v = video as HTMLVideoElement & {
    requestVideoFrameCallback?: (cb: (now: number) => void) => number;
    cancelVideoFrameCallback?: (h: number) => void;
  };
  if (typeof v.requestVideoFrameCallback === "function" && typeof v.cancelVideoFrameCallback === "function") {
    return { kind: "video-frame", schedule: (cb) => v.requestVideoFrameCallback!((now) => cb(now)), cancel: (h) => v.cancelVideoFrameCallback!(h) };
  }
  return { kind: "animation-frame", schedule: (cb) => requestAnimationFrame(cb), cancel: (h) => cancelAnimationFrame(h) };
}
