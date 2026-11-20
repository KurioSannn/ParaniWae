import type { LandmarkFrame } from "@/features/practice/landmarks";
import type { DropReason, ErrorCode } from "@/features/practice/worker/protocol";

export interface InitInfo {
  initMs: number;
  /** Waktu dari pembuatan worker sampai pesan pertama diterima (overhead startup worker). */
  startupMs: number;
  delegate: string | null;
  library: string;
}

export interface AdapterHandlers {
  onResult(r: { id: number; frame: LandmarkFrame; procMs: number; libWarnings?: { normRectNoImageDims: number } }): void;
  onDropped(r: { id: number; reason: DropReason }): void;
  onError(e: { fatal: boolean; code: ErrorCode; message: string }): void;
  onState?(s: "loading" | "ready" | "paused" | "disposed"): void;
}

/**
 * Antarmuka mesin landmark ASINKRON (inferensi tidak berjalan di main thread).
 * `submit` MENGAMBIL ALIH kepemilikan `bitmap` (ditransfer lalu ditutup). Implementasi tidak boleh
 * menjalankan inferensi berat secara sinkron di main thread sebagai fallback diam-diam.
 */
export interface AsyncLandmarkerAdapter {
  readonly name: string;
  setHandlers(h: AdapterHandlers): void;
  init(): Promise<InitInfo>;
  submit(bitmap: ImageBitmap, timestampMs: number, frameIndex: number, id: number): void;
  pause(): void;
  resume(): void;
  dispose(): Promise<void>;
}
