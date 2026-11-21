/**
 * Tipe data landmark & frame — independen dari library CV (MediaPipe hanyalah satu adapter).
 * Koordinat ternormalisasi 0..1 relatif terhadap frame video (x ke kanan, y ke bawah).
 */
export interface Landmark {
  x: number;
  y: number;
  z: number;
  /** Peluang landmark terlihat (pose). 0..1; undefined diperlakukan sebagai tidak terlihat. */
  visibility?: number;
  /** Peluang landmark ada di dalam frame. 0..1 */
  presence?: number;
}

export interface PoseDetection {
  landmarks: Landmark[];
  /** World landmarks MediaPipe (meter, asal di tengah pinggul). Opsional; hanya dipakai di perangkat, tidak disimpan. */
  world?: Landmark[];
}

export interface HandDetection {
  handedness: "Left" | "Right" | "Unknown";
  /** Confidence klasifikasi tangan 0..1 */
  score: number;
  landmarks: Landmark[];
}

export interface FrameMetadata {
  timestampMs: number;
  width: number;
  height: number;
  frameIndex: number;
}

export interface LandmarkFrame {
  meta: FrameMetadata;
  poses: PoseDetection[];
  hands: HandDetection[];
}

/** MediaPipe Pose Landmarker (BlazePose) menghasilkan 33 titik; Hand Landmarker 21 titik. */
export const POSE_LANDMARK_COUNT = 33;
export const HAND_LANDMARK_COUNT = 21;

/** Indeks BlazePose yang dipakai: hidung, bahu, pinggul, lutut, pergelangan kaki. */
export const POSE_INDEX = {
  nose: 0, leftShoulder: 11, rightShoulder: 12, leftElbow: 13, rightElbow: 14,
  leftWrist: 15, rightWrist: 16, leftHip: 23, rightHip: 24, leftKnee: 25, rightKnee: 26,
  leftAnkle: 27, rightAnkle: 28,
} as const;

/** Himpunan landmark tubuh penuh untuk uji "subjek berada dalam frame". */
export const FULL_BODY_REQUIRED: readonly number[] = [
  POSE_INDEX.nose, POSE_INDEX.leftShoulder, POSE_INDEX.rightShoulder, POSE_INDEX.leftHip,
  POSE_INDEX.rightHip, POSE_INDEX.leftKnee, POSE_INDEX.rightKnee, POSE_INDEX.leftAnkle,
  POSE_INDEX.rightAnkle,
];

/** Sambungan sederhana untuk menggambar kerangka (visualisasi saja; bukan analisis). */
export const POSE_CONNECTIONS: readonly [number, number][] = [
  [11, 12], [11, 13], [13, 15], [12, 14], [14, 16], [11, 23], [12, 24], [23, 24],
  [23, 25], [25, 27], [24, 26], [26, 28],
];
