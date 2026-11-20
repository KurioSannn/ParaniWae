import type { AdapterHandlers, AsyncLandmarkerAdapter, InitInfo } from "@/features/practice/async-adapter";
import { DEFAULT_INFERENCE_CONFIG, MEDIAPIPE_PATHS, MEDIAPIPE_VERSION, type InferenceConfig } from "@/features/practice/config";
import type { FromWorker, ToWorker, WorkerInitConfig, WorkerLike } from "@/features/practice/worker/protocol";

export type WorkerFactory = () => WorkerLike;
const defaultFactory: WorkerFactory = () => new Worker(MEDIAPIPE_PATHS.worker) as unknown as WorkerLike; // classic worker, same-origin

/**
 * Adapter yang menjalankan MediaPipe di Web Worker. TIDAK ada fallback sinkron di main thread:
 * bila worker gagal/crash, error dilaporkan ke UI.
 */
export class WorkerLandmarkerAdapter implements AsyncLandmarkerAdapter {
  readonly name = "mediapipe-worker";
  private worker: WorkerLike | null = null;
  private handlers: AdapterHandlers | null = null;
  private disposed = false;

  constructor(
    private readonly cfg: InferenceConfig = DEFAULT_INFERENCE_CONFIG,
    private readonly factory: WorkerFactory = defaultFactory,
    private readonly clock: () => number = () => performance.now(),
  ) {}

  setHandlers(h: AdapterHandlers): void { this.handlers = h; }

  init(): Promise<InitInfo> {
    if (this.worker || this.disposed) return Promise.reject(new Error("Adapter sudah diinisialisasi atau di-dispose"));
    return new Promise<InitInfo>((resolve, reject) => {
      const created = this.clock();
      let firstMsgAt: number | null = null;
      let settled = false;
      const fail = (code: "INIT_FAILED" | "INIT_TIMEOUT" | "WORKER_CRASH", message: string) => {
        if (settled) { this.handlers?.onError({ fatal: true, code, message }); void this.dispose(); return; } // crash setelah init: lepas worker
        settled = true;
        clearTimeout(timer);
        this.handlers?.onError({ fatal: true, code, message });
        void this.dispose();
        reject(new Error(message));
      };
      const timer = setTimeout(() => fail("INIT_TIMEOUT", "Inisialisasi model melebihi batas waktu."), this.cfg.initTimeoutMs);
      let w: WorkerLike;
      try {
        w = this.factory();
      } catch (e) {
        clearTimeout(timer);
        return reject(e);
      }
      this.worker = w;
      w.onmessage = (ev: MessageEvent<FromWorker>) => {
        const m = ev.data;
        firstMsgAt ??= this.clock();
        switch (m.type) {
          case "ready":
            if (!settled) {
              settled = true; clearTimeout(timer);
              resolve({ initMs: m.initMs, startupMs: (firstMsgAt ?? this.clock()) - created, delegate: m.delegate, library: m.library });
            }
            break;
          case "status": this.handlers?.onState?.(m.state); break;
          case "result": this.handlers?.onResult({ id: m.id, frame: m.frame, procMs: m.procMs, libWarnings: m.libWarnings }); break;
          case "dropped": this.handlers?.onDropped({ id: m.id, reason: m.reason }); break;
          case "error":
            if (m.fatal) fail(m.code === "INIT_FAILED" ? "INIT_FAILED" : "WORKER_CRASH", m.message);
            else this.handlers?.onError({ fatal: false, code: m.code, message: m.message });
            break;
        }
      };
      w.onerror = (ev) => fail("WORKER_CRASH", ev.message || "Worker berhenti tiba-tiba.");
      w.onmessageerror = () => fail("WORKER_CRASH", "Pesan dari worker tidak dapat dibaca.");
      const config: WorkerInitConfig = {
        wasmBase: MEDIAPIPE_PATHS.wasm, poseModel: MEDIAPIPE_PATHS.pose, handModel: MEDIAPIPE_PATHS.hand,
        hands: this.cfg.hands, maxPeople: this.cfg.maxPeople, delegate: this.cfg.delegate,
        maxFrameAgeMs: this.cfg.maxFrameAgeMs, libraryVersion: MEDIAPIPE_VERSION, inputShape: this.cfg.inputShape,
      };
      w.postMessage({ type: "init", config });
    });
  }

  submit(bitmap: ImageBitmap, timestampMs: number, frameIndex: number, id: number): void {
    if (!this.worker || this.disposed) { bitmap.close(); return; } // jangan bocorkan bitmap
    const msg: ToWorker = { type: "frame", id, bitmap, timestampMs, frameIndex, sentAtEpochMs: Date.now() };
    try {
      this.worker.postMessage(msg, [bitmap]); // transfer (zero-copy); bitmap menjadi milik worker
    } catch {
      bitmap.close();
    }
  }

  pause(): void { this.worker?.postMessage({ type: "pause" }); }
  resume(): void { this.worker?.postMessage({ type: "resume" }); }

  /** Idempoten. Menghentikan worker dan melepas semua handler. */
  async dispose(): Promise<void> {
    if (this.disposed) return;
    this.disposed = true;
    const w = this.worker;
    this.worker = null;
    if (!w) return;
    try { w.postMessage({ type: "dispose" }); } catch { /* worker sudah mati */ }
    w.onmessage = w.onerror = w.onmessageerror = null;
    w.terminate(); // jaminan berhenti walau worker macet
    this.handlers?.onState?.("disposed");
  }
}
