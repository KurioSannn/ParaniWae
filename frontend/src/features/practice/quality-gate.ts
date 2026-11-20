/**
 * Quality gate AWAL — hanya menilai KELAYAKAN INPUT (apakah data landmark cukup untuk dianalisis).
 *
 * TIDAK ada penilaian benar/salah gerakan, skor teknik, koreksi postur, atau ambang biomekanik
 * di sini; semua itu menunggu rubrik yang disahkan instruktur mitra (CLAUDE.md #4–#6,
 * docs/AI_MOVEMENT_ASSESSMENT.md §6). Ambang pada DEFAULT_QUALITY_CONFIG adalah default teknis
 * penangkapan kamera, belum divalidasi lintas perangkat/tubuh, dan dapat berubah.
 */
import {
  FULL_BODY_REQUIRED, HAND_LANDMARK_COUNT, POSE_LANDMARK_COUNT,
  type Landmark, type LandmarkFrame,
} from "@/features/practice/landmarks";

export type QualityReason =
  | "NO_POSE" | "MULTIPLE_PEOPLE" | "TOO_FEW_LANDMARKS" | "LOW_VISIBILITY" | "OUT_OF_FRAME"
  | "NO_HAND" | "LOW_HAND_CONFIDENCE";

export interface QualityConfig {
  requiredIndices: readonly number[];
  /** visibility minimum agar sebuah landmark dianggap terlihat */
  minVisibility: number;
  /** margin dari tepi frame (fraksi) agar landmark dianggap di dalam frame */
  frameMargin: number;
  allowMultiplePeople: boolean;
  requireHands: boolean;
  minHandScore: number;
  /** untuk ringkasan sesi */
  minFrames: number;
  minValidFrameRatio: number;
}

export const DEFAULT_QUALITY_CONFIG: QualityConfig = {
  requiredIndices: FULL_BODY_REQUIRED,
  minVisibility: 0.5,
  frameMargin: 0.02,
  allowMultiplePeople: false,
  requireHands: false,
  minHandScore: 0.5,
  minFrames: 30,
  minValidFrameRatio: 0.8,
};

export interface FrameQuality {
  usable: boolean;
  reasons: QualityReason[];
  /** fraksi landmark wajib yang terlihat DAN di dalam frame (0..1) */
  requiredCoverage: number;
  meanVisibility: number | null;
}

const finite = (n: unknown): n is number => typeof n === "number" && Number.isFinite(n);
const validPoint = (l: Landmark | undefined): l is Landmark => !!l && finite(l.x) && finite(l.y) && finite(l.z);
const inFrame = (l: Landmark, m: number) => l.x >= m && l.x <= 1 - m && l.y >= m && l.y <= 1 - m;

export function assessFrameQuality(frame: LandmarkFrame, cfg: QualityConfig = DEFAULT_QUALITY_CONFIG): FrameQuality {
  const reasons = new Set<QualityReason>();
  const fail = (extra: Partial<FrameQuality> = {}): FrameQuality =>
    ({ usable: false, reasons: [...reasons], requiredCoverage: 0, meanVisibility: null, ...extra });

  if (frame.poses.length === 0) { reasons.add("NO_POSE"); return fail(); }
  if (frame.poses.length > 1 && !cfg.allowMultiplePeople) reasons.add("MULTIPLE_PEOPLE");

  const lm = frame.poses[0].landmarks;
  if (lm.length < POSE_LANDMARK_COUNT) {
    reasons.add("TOO_FEW_LANDMARKS");
    return fail();
  }

  let visibleInFrame = 0, visSum = 0, visCount = 0, anyLowVis = false, anyOut = false;
  for (const i of cfg.requiredIndices) {
    const p = lm[i];
    if (!validPoint(p)) { anyLowVis = true; continue; }
    const vis = finite(p.visibility) ? p.visibility : 0; // tak diketahui => dianggap tidak terlihat
    visSum += vis; visCount += 1;
    const seen = vis >= cfg.minVisibility;
    const inside = inFrame(p, cfg.frameMargin);
    if (!seen) anyLowVis = true;
    if (!inside) anyOut = true;
    if (seen && inside) visibleInFrame += 1;
  }
  const required = cfg.requiredIndices.length;
  const coverage = required ? visibleInFrame / required : 0;
  // Landmark di luar frame biasanya juga berkonfiden rendah: laporkan OUT_OF_FRAME terlebih dahulu.
  if (anyOut) reasons.add("OUT_OF_FRAME");
  else if (anyLowVis) reasons.add("LOW_VISIBILITY");

  if (cfg.requireHands) {
    const good = frame.hands.filter((h) => h.landmarks.length >= HAND_LANDMARK_COUNT && h.score >= cfg.minHandScore);
    if (frame.hands.length === 0) reasons.add("NO_HAND");
    else if (good.length === 0) reasons.add("LOW_HAND_CONFIDENCE");
  }

  const usable = reasons.size === 0 && coverage === 1;
  return { usable, reasons: [...reasons], requiredCoverage: coverage, meanVisibility: visCount ? visSum / visCount : null };
}

/** Ringkasan kualitas — nama bidang mengikuti `quality_summary` di docs/API_CONTRACTS.md. */
export interface QualitySummary {
  frames: number;
  valid_frame_ratio: number;
  required_landmark_coverage: number;
  dropped_frame_ratio: number;
  /** "sufficient" hanya berarti DATA CUKUP untuk dianalisis, bukan gerakan benar. */
  status: "sufficient" | "insufficient";
  dominantReason: QualityReason | null;
}

export function summarizeQuality(qualities: FrameQuality[], cfg: QualityConfig = DEFAULT_QUALITY_CONFIG): QualitySummary {
  const n = qualities.length;
  if (n === 0) {
    return { frames: 0, valid_frame_ratio: 0, required_landmark_coverage: 0, dropped_frame_ratio: 0, status: "insufficient", dominantReason: "NO_POSE" };
  }
  const valid = qualities.filter((q) => q.usable).length;
  const dropped = qualities.filter((q) => q.reasons.includes("NO_POSE")).length;
  const coverage = qualities.reduce((s, q) => s + q.requiredCoverage, 0) / n;
  const tally = new Map<QualityReason, number>();
  for (const q of qualities) for (const r of q.reasons) tally.set(r, (tally.get(r) ?? 0) + 1);
  const dominant = [...tally.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
  const ratio = valid / n;
  return {
    frames: n, valid_frame_ratio: ratio, required_landmark_coverage: coverage, dropped_frame_ratio: dropped / n,
    status: n >= cfg.minFrames && ratio >= cfg.minValidFrameRatio ? "sufficient" : "insufficient",
    dominantReason: ratio >= cfg.minValidFrameRatio ? null : dominant,
  };
}

/** Panduan memperbaiki penangkapan. Nada: membantu, bukan menyalahkan (DESIGN.md §8). */
export const QUALITY_GUIDANCE: Record<QualityReason, string> = {
  NO_POSE: "Tubuh belum terdeteksi. Pastikan Anda berada di depan kamera dengan cahaya cukup.",
  MULTIPLE_PEOPLE: "Terdeteksi lebih dari satu orang. Pastikan hanya Anda yang berada di area kamera.",
  TOO_FEW_LANDMARKS: "Data landmark belum lengkap. Coba atur ulang posisi atau mulai ulang kamera.",
  LOW_VISIBILITY: "Sebagian tubuh kurang terlihat. Tambah cahaya atau hindari penghalang di depan tubuh.",
  OUT_OF_FRAME: "Tubuh belum terlihat penuh. Mundur sedikit atau atur ulang kamera agar kepala hingga kaki masuk frame.",
  NO_HAND: "Tangan belum terdeteksi. Tunjukkan tangan Anda ke kamera.",
  LOW_HAND_CONFIDENCE: "Tangan kurang jelas. Tambah cahaya dan jauhkan tangan dari latar yang serupa warna kulit.",
};

export function guidanceFor(q: Pick<FrameQuality, "usable" | "reasons">): string {
  if (q.usable) return "Posisi terlihat baik untuk dianalisis.";
  return QUALITY_GUIDANCE[q.reasons[0] ?? "NO_POSE"];
}

/** Jendela geser untuk indikator langsung (menghindari kedip akibat satu frame buruk). */
export class QualityWindow {
  private items: FrameQuality[] = [];
  constructor(private readonly size = 15, private readonly cfg: QualityConfig = DEFAULT_QUALITY_CONFIG) {}
  push(q: FrameQuality): void { this.items.push(q); if (this.items.length > this.size) this.items.shift(); }
  reset(): void { this.items = []; }
  get length(): number { return this.items.length; }
  /** Stabil hanya bila jendela terisi penuh dan >= minValidFrameRatio frame layak. */
  get stable(): boolean {
    return this.items.length >= this.size && this.items.filter((q) => q.usable).length / this.items.length >= this.cfg.minValidFrameRatio;
  }
  get latest(): FrameQuality | null { return this.items[this.items.length - 1] ?? null; }
  summary(): QualitySummary { return summarizeQuality(this.items, { ...this.cfg, minFrames: this.size }); }
}
