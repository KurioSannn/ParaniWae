/**
 * Konfigurasi inferensi. TIDAK ada penurunan resolusi/frame-rate diam-diam: `maxFrameWidth` null berarti
 * resolusi asli kamera dikirim ke worker apa adanya. Setiap perubahan default harus berdasarkan pengukuran
 * (lihat docs/AI_CV_FOUNDATION.md -> Benchmark) dan tercermin di panel metrik.
 */
export interface InferenceConfig {
  /** Jeda minimum antar frame yang DIKIRIM ke worker (ms). 66 ≈ 15 fps. Trade-off: kecil = responsif secara temporal tetapi CPU/baterai naik. */
  minIntervalMs: number;
  /** Maks frame yang sedang diproses worker. >1 hanya menambah antrean dan latensi tanpa menambah throughput (satu model). */
  maxInFlight: number;
  /** Frame yang menunggu di antrean worker lebih tua dari ini dibuang (ms). */
  maxFrameAgeMs: number;
  /** null = resolusi asli. Angka = lebar maks (frame diperkecil proporsional) — hanya bila diaktifkan eksplisit. */
  maxFrameWidth: number | null;
  maxPeople: number;
  hands: boolean;
  delegate: "auto" | "GPU" | "CPU";
  pauseWhenHidden: boolean;
  initTimeoutMs: number;
  /** "native" (default) atau "square-pad": frame diberi bingkai hitam menjadi persegi lalu koordinat dipetakan balik. Lihat docs/AI_CV_FOUNDATION.md (warning NORM_RECT). */
  inputShape: "native" | "square-pad";
}

export const DEFAULT_INFERENCE_CONFIG: InferenceConfig = {
  minIntervalMs: 66,
  maxInFlight: 1,
  maxFrameAgeMs: 500,
  maxFrameWidth: null,
  maxPeople: 2,
  hands: true,
  delegate: "auto",
  pauseWhenHidden: true,
  initTimeoutMs: 60_000,
  inputShape: "native",
};

/** Harus sama dengan versi di package.json (dijaga oleh tes). */
export const MEDIAPIPE_VERSION = "1.2.3";

export const MEDIAPIPE_PATHS = {
  wasm: "/mediapipe/wasm",
  pose: "/mediapipe/models/pose_landmarker_lite.task",
  hand: "/mediapipe/models/hand_landmarker.task",
  worker: "/mediapipe/worker/landmarker.worker.js",
} as const;
