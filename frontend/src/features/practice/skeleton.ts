/**
 * Visualisasi kerangka di atas video. Landmark ternormalisasi terhadap FRAME INPUT (0..1) dan diproyeksikan ke
 * piksel CSS kanvas yang berukuran sama dengan area video (rasio mengikuti video, tanpa crop) — sehingga tidak
 * bergeser pada rasio 4:3, 16:9, maupun resolusi berbeda. Mirroring horizontal dilakukan lewat `mirror`
 * (atau lewat CSS pada pembungkus; jangan keduanya).
 */
import type { HandDetection, Landmark, LandmarkFrame } from "@/features/practice/landmarks";

/**
 * Koneksi tubuh resmi MediaPipe Pose (33 titik). Koneksi wajah detail (indeks 1–6, 9–10: mata/mulut) SENGAJA
 * tidak digambar: tidak diperlukan untuk latihan, mengurangi kekacauan visual, dan selaras dengan kebijakan
 * "tanpa pengenalan wajah / tanpa landmark wajah". Hidung (0) dan telinga (7, 8) tetap sebagai penanda kepala.
 */
export const POSE_BODY_CONNECTIONS: readonly [number, number][] = [
  [11, 12], [11, 13], [13, 15], [15, 17], [15, 19], [15, 21], [17, 19], [12, 14], [14, 16], [16, 18], [16, 20],
  [16, 22], [18, 20], [11, 23], [12, 24], [23, 24], [23, 25], [24, 26], [25, 27], [26, 28], [27, 29], [28, 30],
  [29, 31], [30, 32], [27, 31], [28, 32],
];
export const POSE_DRAWN_POINTS: readonly number[] = [0, 7, 8, ...Array.from({ length: 22 }, (_, i) => 11 + i)];

/** Koneksi resmi MediaPipe Hand (21 titik). */
export const HAND_CONNECTIONS: readonly [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16], [13, 17], [0, 17], [17, 18], [18, 19], [19, 20],
];

export interface Size { width: number; height: number }

export function projectLandmark(l: Pick<Landmark, "x" | "y">, size: Size, opts: { mirror?: boolean } = {}): { x: number; y: number } {
  const nx = opts.mirror ? 1 - l.x : l.x;
  return { x: nx * size.width, y: l.y * size.height };
}

/** Subset 2D context yang dipakai (memudahkan tes dengan context tiruan). */
export interface DrawCtx {
  clearRect(x: number, y: number, w: number, h: number): void;
  beginPath(): void; moveTo(x: number, y: number): void; lineTo(x: number, y: number): void;
  arc(x: number, y: number, r: number, a: number, b: number): void;
  stroke(): void; fill(): void; setLineDash(d: number[]): void;
  strokeStyle: string | CanvasGradient | CanvasPattern; fillStyle: string | CanvasGradient | CanvasPattern;
  lineWidth: number; lineCap: CanvasLineCap; globalAlpha: number;
}

export interface SkeletonOptions {
  mirror?: boolean;
  /** visibility minimum agar titik dianggap terlihat (selaras dengan quality gate). */
  minVisibility?: number;
  showHands?: boolean;
  /** Tampilkan hanya orang pertama (default). Orang lain digambar redup. */
  dimOthers?: boolean;
}

const BONE = "#B9854F", BONE_OUTLINE = "rgba(23,35,31,0.65)", JOINT = "#FCFBF7", HAND = "#9FB7A6";
const visible = (l: Landmark | undefined, min: number) => !!l && Number.isFinite(l.x) && Number.isFinite(l.y) && (l.visibility ?? 0) >= min;

/** Ukuran garis/titik mengikuti sisi terpendek agar proporsional di semua resolusi. */
export function strokeScale(size: Size): { bone: number; joint: number } {
  const m = Math.min(size.width, size.height);
  return { bone: Math.max(2, m / 150), joint: Math.max(3, m / 110) };
}

export function drawSkeleton(ctx: DrawCtx, frame: LandmarkFrame, size: Size, opts: SkeletonOptions = {}): { points: number; bones: number } {
  const min = opts.minVisibility ?? 0.5;
  const { bone, joint } = strokeScale(size);
  ctx.clearRect(0, 0, size.width, size.height);
  ctx.lineCap = "round";
  let points = 0, bones = 0;
  frame.poses.forEach((pose, idx) => {
    const lm = pose.landmarks;
    const alpha = idx === 0 || opts.dimOthers === false ? 1 : 0.35;
    const P = (i: number) => projectLandmark(lm[i], size, opts);
    for (const [a, b] of POSE_BODY_CONNECTIONS) {
      if (!lm[a] || !lm[b] || !visible(lm[a], min) || !visible(lm[b], min)) continue;
      const pa = P(a), pb = P(b);
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = BONE_OUTLINE; ctx.lineWidth = bone + 2;
      ctx.beginPath(); ctx.moveTo(pa.x, pa.y); ctx.lineTo(pb.x, pb.y); ctx.stroke();
      ctx.strokeStyle = BONE; ctx.lineWidth = bone;
      ctx.beginPath(); ctx.moveTo(pa.x, pa.y); ctx.lineTo(pb.x, pb.y); ctx.stroke();
      bones += 1;
    }
    for (const i of POSE_DRAWN_POINTS) {
      const l = lm[i];
      if (!l || !Number.isFinite(l.x) || !Number.isFinite(l.y)) continue;
      const p = P(i);
      ctx.globalAlpha = alpha * ((l.visibility ?? 0) >= min ? 1 : 0.45);
      ctx.beginPath(); ctx.arc(p.x, p.y, joint + 1, 0, Math.PI * 2); ctx.fillStyle = BONE_OUTLINE; ctx.fill();
      ctx.beginPath(); ctx.arc(p.x, p.y, joint, 0, Math.PI * 2); ctx.fillStyle = (l.visibility ?? 0) >= min ? JOINT : "rgba(252,251,247,0.35)"; ctx.fill();
      points += 1;
    }
  });
  if (opts.showHands) {
    for (const h of frame.hands) points += drawHand(ctx, h, size, opts, bone);
  }
  ctx.globalAlpha = 1;
  return { points, bones };
}

function drawHand(ctx: DrawCtx, h: HandDetection, size: Size, opts: SkeletonOptions, bone: number): number {
  ctx.globalAlpha = 0.9;
  ctx.strokeStyle = HAND; ctx.lineWidth = Math.max(1.5, bone * 0.6);
  for (const [a, b] of HAND_CONNECTIONS) {
    const la = h.landmarks[a], lb = h.landmarks[b];
    if (!la || !lb) continue;
    const pa = projectLandmark(la, size, opts), pb = projectLandmark(lb, size, opts);
    ctx.beginPath(); ctx.moveTo(pa.x, pa.y); ctx.lineTo(pb.x, pb.y); ctx.stroke();
  }
  let n = 0;
  ctx.fillStyle = JOINT;
  for (const l of h.landmarks) {
    const p = projectLandmark(l, size, opts);
    ctx.beginPath(); ctx.arc(p.x, p.y, Math.max(2, bone * 0.8), 0, Math.PI * 2); ctx.fill();
    n += 1;
  }
  return n;
}

/** Ukuran area video yang memuat rasio asli tanpa crop dan tidak melebihi `maxHeight`. */
export function fitVideoBox(videoW: number, videoH: number, availW: number, maxH: number): Size {
  if (!videoW || !videoH || availW <= 0) return { width: Math.max(0, availW), height: Math.max(0, availW * 0.75) };
  const ratio = videoW / videoH;
  const w = Math.min(availW, maxH * ratio);
  return { width: w, height: w / ratio };
}
