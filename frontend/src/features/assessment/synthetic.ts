/**
 * Pembuat frame SINTETIS untuk uji mesin penilaian (bukan data manusia, bukan kamera).
 * Figur 2D sederhana dengan parameter sendi yang bisa diatur, keluaran 33 landmark berindeks MediaPipe.
 */
import type { MeasureFrame, Vec3 } from "@/features/assessment/types";

export interface SynthPose {
  view: "side" | "front";
  /** elevasi paha kaki kiri/kanan dari arah bawah (°). */
  thighL: number; thighR: number;
  /** tekukan lutut (°, 0 = lurus). */
  kneeL: number; kneeR: number;
  /** posisi horizontal pergelangan kaki relatif pinggul (satuan panjang tungkai) — kuda-kuda/langkah. */
  footL?: number; footR?: number;
  torso?: number; // condong (°)
  hipShift?: number; // geser pinggul horizontal (satuan tungkai)
  wristHip?: number; // tinggi pergelangan tangan relatif pinggul (satuan torso, + = di atas)
}

const LEG = 0.2, SHIN = 0.2, TORSO = 0.26;

function rotDown(angleDeg: number, sign = 1): [number, number] {
  const a = (angleDeg * Math.PI) / 180;
  return [Math.sin(a) * sign, Math.cos(a)]; // y ke bawah
}

/** Satu frame landmark sintetis. Tampak samping: menghadap +x. */
export function synthLandmarks(p: SynthPose): Vec3[] {
  const pts: Vec3[] = Array.from({ length: 33 }, () => [0.5, 0.5, 0] as Vec3);
  const hx = 0.5 + (p.hipShift ?? 0) * (LEG + SHIN), hy = 0.55;
  const t = ((p.torso ?? 0) * Math.PI) / 180;
  const shx = hx + Math.sin(t) * TORSO, shy = hy - Math.cos(t) * TORSO;
  const half = p.view === "front" ? 0.06 : 0.008;
  const shHalf = p.view === "front" ? 0.09 : 0.01;
  const leg = (side: 1 | -1, thigh: number, knee: number, foot?: number) => {
    const hip: [number, number] = [hx + side * half, hy];
    let kneeP: [number, number], ank: [number, number];
    if (p.view === "side") {
      const d1 = rotDown(thigh);
      kneeP = [hip[0] + d1[0] * LEG, hip[1] + d1[1] * LEG];
      const d2 = rotDown(thigh - knee);
      ank = [kneeP[0] + d2[0] * SHIN, kneeP[1] + d2[1] * SHIN];
      if (foot !== undefined && thigh < 20) { // kaki menapak: letakkan pergelangan sesuai posisi kaki
        ank = [hx + foot * (LEG + SHIN), hy + (LEG + SHIN) * Math.cos((knee * Math.PI) / 360)];
        kneeP = [(hip[0] + ank[0]) / 2 + Math.sin((knee * Math.PI) / 360) * 0.06, (hip[1] + ank[1]) / 2];
      }
    } else {
      const ax = foot !== undefined ? hx + foot * (LEG + SHIN) : hip[0];
      const drop = (LEG + SHIN) * Math.cos((knee * Math.PI) / 360);
      ank = [ax, hy + drop];
      kneeP = [(hip[0] + ank[0]) / 2, (hip[1] + ank[1]) / 2];
    }
    return { hip, knee: kneeP, ank };
  };
  const L = leg(p.view === "front" ? 1 : 1, p.thighL, p.kneeL, p.footL);
  const R = leg(p.view === "front" ? -1 : 1, p.thighR, p.kneeR, p.footR);
  const set = (i: number, x: number, y: number) => { pts[i] = [x, y, 0]; };
  set(23, ...L.hip); set(24, ...R.hip); set(25, ...L.knee); set(26, ...R.knee); set(27, ...L.ank); set(28, ...R.ank);
  const toe = p.view === "side" ? 0.05 : 0;
  set(29, L.ank[0] - toe * 0.4, L.ank[1] + 0.02); set(30, R.ank[0] - toe * 0.4, R.ank[1] + 0.02);
  set(31, L.ank[0] + toe, L.ank[1] + 0.02); set(32, R.ank[0] + toe, R.ank[1] + 0.02);
  set(11, shx + shHalf, shy); set(12, shx - shHalf, shy);
  const wy = hy - (p.wristHip ?? 0.1) * TORSO;
  set(13, shx + shHalf, (shy + wy) / 2); set(14, shx - shHalf, (shy + wy) / 2); set(15, hx + shHalf * 1.2, wy); set(16, hx - shHalf * 1.2, wy);
  const headY = shy - 0.1;
  set(0, shx + (p.view === "side" ? 0.03 : 0), headY); set(7, shx + (p.view === "front" ? 0.03 : -0.01), headY); set(8, shx - (p.view === "front" ? 0.03 : 0.01), headY);
  return pts;
}

export function synthFrame(t: number, p: SynthPose, visibility = 0.95, usable = true): MeasureFrame {
  return { t, image: synthLandmarks(p), world: null, visibility: new Array(33).fill(visibility), usable };
}

/** Urutan fase dengan durasi tahan & transisi (detik), sampel pada fps. */
export function lerpPose(a: SynthPose, b: SynthPose, u: number): SynthPose {
  const r = { ...a } as Record<string, unknown>;
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)]) as Set<keyof SynthPose>) {
    const va = a[k] ?? (k === "footL" || k === "footR" ? undefined : 0), vb = b[k] ?? va;
    if (typeof va === "number" && typeof vb === "number") r[k] = va + (vb - va) * u;
    else if (vb !== undefined) r[k] = u < 0.5 ? va : vb;
  }
  return r as unknown as SynthPose;
}

export function synthSequence(keys: { pose: SynthPose; hold: number; move: number }[], fps = 15, opts: { visibility?: number } = {}): MeasureFrame[] {
  const out: MeasureFrame[] = [];
  let t = 0;
  const lerp = lerpPose;
  for (let i = 0; i < keys.length; i += 1) {
    const k = keys[i];
    if (i > 0 && k.move > 0) {
      const n = Math.max(1, Math.round(k.move * fps));
      for (let s = 1; s <= n; s += 1) { out.push(synthFrame(t, lerp(keys[i - 1].pose, k.pose, s / n), opts.visibility)); t += 1 / fps; }
    }
    const h = Math.max(1, Math.round(k.hold * fps));
    for (let s = 0; s < h; s += 1) { out.push(synthFrame(t, k.pose, opts.visibility)); t += 1 / fps; }
  }
  return out;
}
