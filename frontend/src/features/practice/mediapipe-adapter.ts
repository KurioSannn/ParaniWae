import type { LandmarkFrame } from "@/features/practice/landmarks";
import type { LandmarkerAdapter } from "@/features/practice/adapter";
import { MEDIAPIPE_PATHS } from "@/features/practice/config";
import { toLandmarkFrame } from "@/features/practice/worker/convert";

export { MEDIAPIPE_PATHS };

type PoseLM = { detectForVideo(v: HTMLVideoElement, t: number): { landmarks: never[][] }; close(): void };
type HandLM = { detectForVideo(v: HTMLVideoElement, t: number): { landmarks: never[][]; handedness: never[][] }; close(): void };

/**
 * IMPLEMENTASI LAMA: inferensi SINKRON di main thread. Dipertahankan HANYA sebagai baseline benchmark
 * (docs/AI_CV_FOUNDATION.md) agar perbandingan dengan Worker dapat direproduksi. TIDAK dipakai oleh UI
 * produksi dan TIDAK boleh menjadi fallback diam-diam untuk Worker.
 */
export class MediaPipeAdapter implements LandmarkerAdapter {
  readonly name = "mediapipe-main-thread-baseline";
  delegate: string | undefined;
  private pose: PoseLM | null = null;
  private hand: HandLM | null = null;

  constructor(private readonly opts: { hands?: boolean; maxPeople?: number } = {}) {}

  async init(): Promise<void> {
    const { FilesetResolver, PoseLandmarker, HandLandmarker } = await import("@mediapipe/tasks-vision");
    const fileset = await FilesetResolver.forVisionTasks(MEDIAPIPE_PATHS.wasm);
    const make = async <T,>(create: (delegate: "GPU" | "CPU") => Promise<T>): Promise<T> => {
      try { const r = await create("GPU"); this.delegate = this.delegate ?? "GPU"; return r; }
      catch { this.delegate = "CPU"; return await create("CPU"); }
    };
    this.pose = (await make((delegate) => PoseLandmarker.createFromOptions(fileset, {
      baseOptions: { modelAssetPath: MEDIAPIPE_PATHS.pose, delegate }, runningMode: "VIDEO", numPoses: this.opts.maxPeople ?? 2,
    }))) as unknown as PoseLM;
    if (this.opts.hands) {
      this.hand = (await make((delegate) => HandLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: MEDIAPIPE_PATHS.hand, delegate }, runningMode: "VIDEO", numHands: 2,
      }))) as unknown as HandLM;
    }
  }

  detect(video: HTMLVideoElement, timestampMs: number, frameIndex: number): LandmarkFrame {
    if (!this.pose) throw new Error("MediaPipeAdapter belum diinisialisasi");
    const p = this.pose.detectForVideo(video, timestampMs);
    const h = this.hand ? this.hand.detectForVideo(video, timestampMs) : null;
    return toLandmarkFrame(p, h, { timestampMs, width: video.videoWidth, height: video.videoHeight, frameIndex });
  }

  dispose(): void {
    this.pose?.close(); this.hand?.close();
    this.pose = this.hand = null;
  }
}
