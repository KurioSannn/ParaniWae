/**
 * DATA SINTETIS untuk demo/tes Practice Studio — kerangka buatan kode (BUKAN manusia, BUKAN gerakan pencak silat).
 * Hanya dipakai pada mode simulasi yang diberi spanduk jelas; tidak pernah mengklaim deteksi tubuh pengguna.
 */
import type { Landmark, LandmarkFrame, PoseDetection } from "@/features/practice/landmarks";

const BASE: Record<number, [number, number]> = {
  0: [0.5, 0.13], 1: [0.52, 0.115], 2: [0.53, 0.115], 3: [0.54, 0.115], 4: [0.48, 0.115], 5: [0.47, 0.115], 6: [0.46, 0.115],
  7: [0.56, 0.13], 8: [0.44, 0.13], 9: [0.52, 0.16], 10: [0.48, 0.16],
  11: [0.58, 0.26], 12: [0.42, 0.26], 13: [0.65, 0.4], 14: [0.35, 0.4], 15: [0.68, 0.54], 16: [0.32, 0.54],
  17: [0.69, 0.57], 18: [0.31, 0.57], 19: [0.7, 0.56], 20: [0.3, 0.56], 21: [0.69, 0.55], 22: [0.31, 0.55],
  23: [0.55, 0.54], 24: [0.45, 0.54], 25: [0.56, 0.74], 26: [0.44, 0.74], 27: [0.57, 0.92], 28: [0.43, 0.92],
  29: [0.58, 0.95], 30: [0.42, 0.95], 31: [0.61, 0.97], 32: [0.39, 0.97],
};

export function syntheticStandingPose(opts: { t?: number; visibility?: number; hide?: number[]; outOfFrame?: boolean } = {}): PoseDetection {
  const t = opts.t ?? 0;
  const sway = Math.sin(t / 700) * 0.02; // gerak kecil agar overlay terlihat "hidup"
  const lm: Landmark[] = Array.from({ length: 33 }, (_, i) => {
    const [x, y] = BASE[i];
    const arm = i === 15 || i === 16 || (i >= 17 && i <= 22) ? sway : 0;
    return { x: x + arm, y: (opts.outOfFrame && i >= 25 ? y + 0.2 : y) + (arm ? sway : 0), z: 0, visibility: opts.hide?.includes(i) ? 0.1 : opts.visibility ?? 0.95, presence: 0.95 };
  });
  return { landmarks: lm };
}

export type SyntheticScenario = "waiting" | "full" | "partial" | "out_of_frame" | "multiple";

export function syntheticFrame(scenario: SyntheticScenario, i: number, t: number, w = 640, h = 480): LandmarkFrame {
  const meta = { timestampMs: t, width: w, height: h, frameIndex: i };
  switch (scenario) {
    case "waiting": return { meta, poses: [], hands: [] };
    case "full": return { meta, poses: [syntheticStandingPose({ t })], hands: [] };
    case "partial": return { meta, poses: [syntheticStandingPose({ t, hide: [25, 26, 27, 28] })], hands: [] };
    case "out_of_frame": return { meta, poses: [syntheticStandingPose({ t, outOfFrame: true })], hands: [] };
    case "multiple": return { meta, poses: [syntheticStandingPose({ t }), syntheticStandingPose({ t: t + 500 })], hands: [] };
  }
}
