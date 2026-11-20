/**
 * SYNTHETIC TEST FIXTURES — data sintetis buatan kode, BUKAN hasil deteksi gerakan manusia
 * sungguhan dan BUKAN representasi gerakan pencak silat apa pun. Hanya untuk menguji logika
 * quality gate (jumlah landmark, visibilitas, batas frame).
 */
import {
  HAND_LANDMARK_COUNT, POSE_LANDMARK_COUNT,
  type HandDetection, type Landmark, type LandmarkFrame, type PoseDetection,
} from "@/features/practice/landmarks";

export const SYNTHETIC_FIXTURE_NOTICE = "synthetic test fixture — bukan data manusia nyata";

export function syntheticPose(overrides: Partial<Record<number, Partial<Landmark>>> = {}, count = POSE_LANDMARK_COUNT): PoseDetection {
  const landmarks: Landmark[] = Array.from({ length: count }, (_, i) => ({
    x: 0.3 + (i % 5) * 0.1, y: 0.1 + (i % 9) * 0.1, z: 0, visibility: 0.9, presence: 0.9,
  }));
  for (const [idx, o] of Object.entries(overrides)) landmarks[Number(idx)] = { ...landmarks[Number(idx)], ...o };
  return { landmarks };
}

export function syntheticHand(score = 0.9, count = HAND_LANDMARK_COUNT): HandDetection {
  return { handedness: "Unknown", score, landmarks: Array.from({ length: count }, (_, i) => ({ x: 0.5, y: 0.2 + i * 0.01, z: 0 })) };
}

export function syntheticFrame(opts: { poses?: PoseDetection[]; hands?: HandDetection[]; i?: number } = {}): LandmarkFrame {
  const i = opts.i ?? 0;
  return {
    meta: { timestampMs: i * 33, width: 640, height: 480, frameIndex: i },
    poses: opts.poses ?? [syntheticPose()],
    hands: opts.hands ?? [],
  };
}
