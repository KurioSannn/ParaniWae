import type { LandmarkFrame } from "@/features/practice/landmarks";

/** Antarmuka model CV. Aplikasi hanya bergantung pada ini, bukan pada MediaPipe. */
export interface LandmarkerAdapter {
  readonly name: string;
  /** Delegasi komputasi yang benar-benar dipakai setelah init() (mis. "GPU" atau "CPU"). */
  delegate?: string;
  init(): Promise<void>;
  /** Deteksi satu frame video. Sinkron setelah init(). Nilai keluaran dalam koordinat 0..1. */
  detect(video: HTMLVideoElement, timestampMs: number, frameIndex: number): LandmarkFrame;
  dispose(): void;
}
