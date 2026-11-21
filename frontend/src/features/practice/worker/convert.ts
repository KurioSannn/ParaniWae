import type { HandDetection, Landmark, LandmarkFrame } from "@/features/practice/landmarks";

type RawLm = { x: number; y: number; z: number; visibility?: number; presence?: number };
type RawPose = { landmarks: RawLm[][]; worldLandmarks?: RawLm[][] };
type RawHand = { landmarks: RawLm[][]; handedness: { categoryName: string; score: number }[][] };

const plain = (l: RawLm): Landmark => ({ x: l.x, y: l.y, z: l.z, visibility: l.visibility, presence: l.presence });

/** Hasil MediaPipe -> `LandmarkFrame` (objek polos, aman di-clone antar thread). Murni & dapat diuji. */
export function toLandmarkFrame(
  pose: RawPose, hand: RawHand | null,
  meta: { timestampMs: number; width: number; height: number; frameIndex: number },
): LandmarkFrame {
  const hands: HandDetection[] = [];
  if (hand) {
    hand.landmarks.forEach((lm, i) => {
      const cat = hand.handedness[i]?.[0];
      hands.push({
        handedness: cat?.categoryName === "Left" || cat?.categoryName === "Right" ? cat.categoryName : "Unknown",
        score: cat?.score ?? 0, landmarks: lm.map(plain),
      });
    });
  }
  return {
    meta, hands,
    poses: pose.landmarks.map((l, i) => {
      const w = pose.worldLandmarks?.[i];
      return w ? { landmarks: l.map(plain), world: w.map(plain) } : { landmarks: l.map(plain) };
    }),
  };
}
