import type { AsyncLandmarkerAdapter } from "@/features/practice/async-adapter";
import type { InferenceConfig } from "@/features/practice/config";
import { createFrameBitmap, type FrameSource } from "@/features/practice/pipeline";
import type { LandmarkFrame } from "@/features/practice/landmarks";

/**
 * Deteksi pose pada SATU frame video referensi (saat jeda/seek) atau berkelanjutan saat diputar.
 * Hanya satu frame in-flight; permintaan baru saat sibuk ditandai `pending` lalu dijalankan setelahnya (tanpa antrean menumpuk).
 * Overlay dihitung di browser dan TIDAK disimpan; hanya timestamp + provenance anotasi yang dikirim ke server.
 */
// Inferensi pertama (kompilasi graph/delegate) dapat memakan beberapa detik pada perangkat tanpa GPU; jangan menyatakan "macet" terlalu dini.
const WATCHDOG_MS = 20_000;

export class ReferenceFrameDetector {
  private seq = 0;
  private inFlightId: number | null = null;
  private rerun = false;
  private disposed = false;
  private lastSource: (FrameSource & { currentTime: number }) | null = null;
  private lastCfg: InferenceConfig | null = null;
  lastError: string | null = null;

  constructor(
    private readonly adapter: AsyncLandmarkerAdapter,
    private readonly onFrame: (f: LandmarkFrame, timeMs: number) => void,
    private readonly onStatus?: (s: "busy" | "idle") => void,
    private readonly makeBitmap: typeof createFrameBitmap = createFrameBitmap,
    private readonly nowMs: () => number = () => performance.now(),
    private readonly onNote?: (msg: string | null) => void,
  ) {
    const times = new Map<number, number>();
    this.times = times;
    adapter.setHandlers({
      onResult: (r) => {
        if (r.id !== this.inFlightId) return;
        this.finish();
        this.onNote?.(null);
        this.onFrame(r.frame, times.get(r.id) ?? 0);
        times.delete(r.id);
        this.maybeRerun();
      },
      onDropped: (r) => {
        if (r.id !== this.inFlightId) return;
        this.lastError = `Frame dilewati oleh mesin (${r.reason}).`;
        this.onNote?.(this.lastError);
        this.finish(); this.maybeRerun();
      },
      onError: (e) => { this.lastError = e.message; this.onNote?.(e.message); if (e.fatal) { this.finish(); } },
    });
  }
  private times: Map<number, number>;

  private finish() { this.inFlightId = null; this.onStatus?.("idle"); }
  private maybeRerun() { if (this.rerun && this.lastSource && this.lastCfg) { this.rerun = false; void this.detect(this.lastSource, this.lastCfg); } }

  get busy(): boolean { return this.inFlightId !== null; }

  /** Minta deteksi untuk frame video saat ini. Bila sibuk, hanya satu permintaan terbaru yang diingat. */
  async detect(source: FrameSource & { currentTime: number }, cfg: InferenceConfig): Promise<void> {
    if (this.disposed) return;
    this.lastSource = source; this.lastCfg = cfg;
    if (this.inFlightId !== null) { this.rerun = true; return; }
    if (source.readyState < 2) return;
    const id = ++this.seq;
    this.inFlightId = id;
    this.onStatus?.("busy");
    try {
      const bm = await this.makeBitmap(source, cfg.maxFrameWidth);
      if (this.disposed) { bm.close(); this.inFlightId = null; return; }
      this.times.set(id, Math.round(source.currentTime * 1000));
      this.adapter.submit(bm, this.nowMs(), id, id);
      // watchdog: bila engine tidak pernah menjawab, lepaskan agar tidak macet selamanya (galat dilaporkan, bukan disembunyikan)
      setTimeout(() => { if (this.inFlightId === id && !this.disposed) { this.lastError = "Mesin deteksi tidak merespons."; this.onNote?.(this.lastError); this.finish(); } }, WATCHDOG_MS);
    } catch (e) {
      this.lastError = e instanceof Error ? e.message : "Gagal membaca frame video.";
      this.onNote?.(this.lastError);
      this.finish();
    }
  }

  async dispose(): Promise<void> { this.disposed = true; this.inFlightId = null; await this.adapter.dispose(); }
}
