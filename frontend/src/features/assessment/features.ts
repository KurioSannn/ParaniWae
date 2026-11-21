/**
 * Fitur gerak berbasis tubuh (murni, tanpa React). Semua jarak dinormalkan terhadap panjang tungkai/torso sehingga
 * tidak bergantung pada tinggi badan atau jarak ke kamera. Sudut tidak bergantung skala.
 * Konvensi ruang ukur: y ke BAWAH (gambar & world MediaPipe). Referensi 3D dikonversi ke konvensi yang sama.
 */
import type { FeatureId, MeasureFrame, Side, SideRule, Vec3 } from "@/features/assessment/types";

export const LM = {
  nose: 0, lEar: 7, rEar: 8, lSh: 11, rSh: 12, lEl: 13, rEl: 14, lWr: 15, rWr: 16,
  lHip: 23, rHip: 24, lKnee: 25, rKnee: 26, lAnk: 27, rAnk: 28, lHeel: 29, rHeel: 30, lFoot: 31, rFoot: 32,
} as const;

const idx = (s: Side, l: string, r: string) => (s === "L" ? (LM as Record<string, number>)[l] : (LM as Record<string, number>)[r]);
const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const len = (a: Vec3) => Math.hypot(a[0], a[1], a[2]);
const mid = (a: Vec3, b: Vec3): Vec3 => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
const DOWN: Vec3 = [0, 1, 0];

export function angleDeg(a: Vec3, b: Vec3): number {
  const la = len(a), lb = len(b);
  if (la < 1e-9 || lb < 1e-9) return NaN;
  return (Math.acos(Math.max(-1, Math.min(1, dot(a, b) / (la * lb)))) * 180) / Math.PI;
}

/** Sudut dalam pada titik b (a–b–c). */
export function jointAngle(a: Vec3, b: Vec3, c: Vec3): number {
  return angleDeg(sub(a, b), sub(c, b));
}

type Space = "image" | "world";

export function pts(f: MeasureFrame, space: Space): Vec3[] | null {
  return space === "world" ? f.world : f.image;
}

/** Ubah ruang 2D: hanya x,y (proyeksi bidang kamera); z diabaikan agar sudut 2D konsisten dengan referensi terproyeksi. */
function P(p: Vec3[], i: number, space: Space): Vec3 {
  const q = p[i];
  return space === "image" ? [q[0], q[1], 0] : q;
}

export function legLength(p: Vec3[], space: Space): number {
  const one = (s: Side) => len(sub(P(p, idx(s, "lHip", "rHip"), space), P(p, idx(s, "lKnee", "rKnee"), space)))
    + len(sub(P(p, idx(s, "lKnee", "rKnee"), space), P(p, idx(s, "lAnk", "rAnk"), space)));
  return (one("L") + one("R")) / 2;
}

export function torsoLength(p: Vec3[], space: Space): number {
  return len(sub(mid(P(p, LM.lSh, space), P(p, LM.rSh, space)), mid(P(p, LM.lHip, space), P(p, LM.rHip, space))));
}

/** Arah hadap pada tampak samping: +1 bila menghadap ke x positif gambar, −1 bila ke x negatif. */
export function facingSign(p: Vec3[]): number {
  const ears = mid(p[LM.lEar], p[LM.rEar]);
  const d = p[LM.nose][0] - ears[0];
  if (Math.abs(d) > 1e-4) return Math.sign(d);
  const toes = mid(p[LM.lFoot], p[LM.rFoot]), heels = mid(p[LM.lHeel], p[LM.rHeel]);
  return Math.sign(toes[0] - heels[0]) || 1;
}

/** Tentukan sisi konkret dari aturan sisi pada satu frame. */
export function resolveSide(rule: SideRule, p: Vec3[]): Side | "both" {
  if (rule === "L" || rule === "R") return rule;
  if (rule === "both_mean" || rule === "both_min") return "both";
  if (rule === "lifting" || rule === "supporting") {
    const lifted: Side = p[LM.lAnk][1] < p[LM.rAnk][1] ? "L" : "R"; // y ke bawah: lebih kecil = lebih tinggi
    return rule === "lifting" ? lifted : lifted === "L" ? "R" : "L";
  }
  const sgn = facingSign(p);
  const front: Side = (p[LM.lAnk][0] - p[LM.rAnk][0]) * sgn > 0 ? "L" : "R";
  return rule === "front" ? front : front === "L" ? "R" : "L";
}

/** Indeks landmark yang dipakai fitur (untuk confidence). */
export function featureLandmarks(feature: FeatureId, side: Side | "both"): number[] {
  const S = side === "both" ? (["L", "R"] as Side[]) : [side];
  const per = (s: Side): number[] => {
    switch (feature) {
      case "knee_angle": case "knee_flexion": return [idx(s, "lHip", "rHip"), idx(s, "lKnee", "rKnee"), idx(s, "lAnk", "rAnk")];
      case "thigh_elevation": return [idx(s, "lHip", "rHip"), idx(s, "lKnee", "rKnee")];
      case "knee_over_toe": return [idx(s, "lKnee", "rKnee"), idx(s, "lFoot", "rFoot")];
      case "wrist_hip_height": return [idx(s, "lWr", "rWr"), idx(s, "lHip", "rHip"), LM.lSh, LM.rSh];
      default: return [];
    }
  };
  const body: Partial<Record<FeatureId, number[]>> = {
    torso_incline: [LM.lSh, LM.rSh, LM.lHip, LM.rHip],
    balance_center: [LM.lHip, LM.rHip, LM.lAnk, LM.rAnk],
    weight_forward: [LM.lHip, LM.rHip, LM.lAnk, LM.rAnk, LM.nose],
    step_length: [LM.lAnk, LM.rAnk, LM.lHip, LM.rHip, LM.lKnee, LM.rKnee],
    stance_width_ratio: [LM.lAnk, LM.rAnk, LM.lHip, LM.rHip],
    hip_sway: [LM.lHip, LM.rHip, LM.lKnee, LM.rKnee, LM.lAnk, LM.rAnk],
  };
  return body[feature] ?? [...new Set(S.flatMap(per))];
}

/** Nilai fitur pada satu frame (NaN bila tidak dapat dihitung). `hip_sway` dihitung per jendela, bukan per frame. */
export function featureValue(feature: FeatureId, p: Vec3[], side: Side | "both", space: Space): number {
  const one = (s: Side): number => {
    const hip = P(p, idx(s, "lHip", "rHip"), space), knee = P(p, idx(s, "lKnee", "rKnee"), space), ank = P(p, idx(s, "lAnk", "rAnk"), space);
    switch (feature) {
      case "knee_angle": return jointAngle(hip, knee, ank);
      case "knee_flexion": return 180 - jointAngle(hip, knee, ank);
      case "thigh_elevation": return angleDeg(sub(knee, hip), DOWN);
      case "knee_over_toe": return Math.abs(knee[0] - P(p, idx(s, "lFoot", "rFoot"), space)[0]) / legLength(p, space);
      case "wrist_hip_height": return (hip[1] - P(p, idx(s, "lWr", "rWr"), space)[1]) / torsoLength(p, space);
      default: return NaN;
    }
  };
  switch (feature) {
    case "torso_incline": {
      const sh = mid(P(p, LM.lSh, space), P(p, LM.rSh, space)), hp = mid(P(p, LM.lHip, space), P(p, LM.rHip, space));
      return angleDeg(sub(sh, hp), [0, -1, 0]);
    }
    case "balance_center": {
      const hp = mid(P(p, LM.lHip, space), P(p, LM.rHip, space)), am = mid(P(p, LM.lAnk, space), P(p, LM.rAnk, space));
      const w = Math.max(Math.abs(P(p, LM.lAnk, space)[0] - P(p, LM.rAnk, space)[0]), 0.25 * legLength(p, space));
      return Math.abs(hp[0] - am[0]) / w;
    }
    case "weight_forward": {
      const sgn = facingSign(p);
      const a = P(p, LM.lAnk, space)[0] * sgn, b = P(p, LM.rAnk, space)[0] * sgn;
      const front = Math.max(a, b), rear = Math.min(a, b);
      if (front - rear < 0.05 * legLength(p, space)) return NaN; // kaki sejajar: tidak terdefinisi
      const h = mid(P(p, LM.lHip, space), P(p, LM.rHip, space))[0] * sgn;
      return (h - rear) / (front - rear);
    }
    case "step_length": return Math.abs(P(p, LM.lAnk, space)[0] - P(p, LM.rAnk, space)[0]) / legLength(p, space);
    case "stance_width_ratio": {
      const hw = Math.abs(P(p, LM.lHip, space)[0] - P(p, LM.rHip, space)[0]);
      return hw < 1e-4 ? NaN : Math.abs(P(p, LM.lAnk, space)[0] - P(p, LM.rAnk, space)[0]) / hw;
    }
    default:
      if (side === "both") {
        const a = one("L"), b = one("R");
        return Math.max(a, b);
      }
      return one(side);
  }
}

export function frameConfidence(f: MeasureFrame, lms: number[]): number {
  if (!lms.length) return 0;
  return Math.min(...lms.map((i) => f.visibility[i] ?? 0));
}

/** Tampak kamera dari rasio lebar bahu/panjang torso (2D): lebar = depan, sempit = samping. */
export function estimateView(p: Vec3[]): "front" | "side" | "unknown" {
  const sw = Math.abs(p[LM.lSh][0] - p[LM.rSh][0]) / Math.max(torsoLength(p, "image"), 1e-6);
  if (sw > 0.45) return "front";
  if (sw < 0.3) return "side";
  return "unknown";
}
