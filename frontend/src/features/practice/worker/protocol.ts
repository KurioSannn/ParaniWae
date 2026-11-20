import type { LandmarkFrame } from "@/features/practice/landmarks";

/** Konfigurasi yang dikirim ke worker saat init. Semua URL harus same-origin. */
export interface WorkerInitConfig {
  wasmBase: string;
  poseModel: string;
  handModel: string;
  hands: boolean;
  maxPeople: number;
  delegate: "auto" | "GPU" | "CPU";
  maxFrameAgeMs: number;
  libraryVersion: string;
  inputShape?: "native" | "square-pad";
}

/** main -> worker */
export type ToWorker =
  | { type: "init"; config: WorkerInitConfig }
  | { type: "frame"; id: number; bitmap: ImageBitmap; timestampMs: number; frameIndex: number; sentAtEpochMs: number }
  | { type: "pause" }
  | { type: "resume" }
  | { type: "dispose" };

export type WorkerState = "loading" | "ready" | "paused" | "disposed";
export type DropReason = "not_ready" | "paused" | "stale" | "busy";
export type ErrorCode = "INIT_FAILED" | "DETECT_FAILED" | "WORKER_CRASH" | "INIT_TIMEOUT";

/** worker -> main */
export type FromWorker =
  | { type: "status"; state: WorkerState }
  | { type: "ready"; initMs: number; delegate: string | null; library: string }
  | { type: "result"; id: number; frame: LandmarkFrame; procMs: number; libWarnings?: { normRectNoImageDims: number } }
  | { type: "dropped"; id: number; reason: DropReason }
  | { type: "error"; fatal: boolean; code: ErrorCode; message: string; id?: number };

/** Subset Worker yang dipakai (memudahkan tes dengan worker tiruan). */
export interface WorkerLike {
  postMessage(msg: ToWorker, transfer?: Transferable[]): void;
  terminate(): void;
  onmessage: ((e: MessageEvent<FromWorker>) => void) | null;
  onerror: ((e: ErrorEvent) => void) | null;
  onmessageerror: ((e: MessageEvent) => void) | null;
}
