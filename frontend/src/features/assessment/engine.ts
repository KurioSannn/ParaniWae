/**
 * Mesin penilaian gerak berbasis protokol (murni & deterministik; dapat diuji dengan fixture).
 *
 * Alur: frame terukur → kualitas input → cek sudut kamera → penyelarasan urutan (subsequence DTW) terhadap urutan
 * referensi → deteksi fase → nilai tiap kriteria di jendela fasenya → skor berbobot 0–100 + saran.
 * Skor TIDAK pernah dihitung bila kualitas input/landmark tidak memadai (status not_assessable).
 *   total_score = Σ(skor_kriteria × bobot) / Σ(bobot kriteria terukur)
 */
import {
  estimateView, featureLandmarks, featureValue, frameConfidence, legLength, LM, pts, resolveSide,
} from "@/features/assessment/features";
import type {
  AssessmentOutcome, CriterionResult, CriterionSpec, FeatureId, MeasureFrame, PhaseResult, Protocol, Side, Vec3,
} from "@/features/assessment/types";

export const ENGINE_VERSION = "1.0.0";

/** Parameter teknis mesin (bukan target gerak): ambang penyelarasan & deteksi fase. Terdokumentasi di kontrak. */
export const ENGINE_PARAMS = {
  maxAlignmentCost: 0.55,   // rata-rata biaya per langkah DTW di atas ini = gerakan tidak ditemukan
  maxPhaseCost: 0.45,       // rata-rata biaya frame fase di atas ini = fase dianggap tidak terlihat
  minPhaseFrames: 2,
  unusableCost: 0.6,        // biaya frame yang tidak lolos quality gate
} as const;

export interface ReferenceFrame { t: number; keyframe: string; frame: MeasureFrame }

// ---------------------------------------------------------------- penyelarasan
function alignVector(f: MeasureFrame, feats: FeatureId[]): number[] | null {
  const p = pts(f, "image");
  if (!p || !f.usable) return null;
  return feats.map((ft) => {
    const v = featureValue(ft, p, "both", "image");
    return Number.isFinite(v) ? (ft.endsWith("ratio") || ["knee_over_toe", "balance_center", "weight_forward", "step_length", "wrist_hip_height"].includes(ft) ? v : v / 90) : 0;
  });
}

function dist(a: number[], b: number[]): number {
  let s = 0;
  for (let i = 0; i < a.length; i += 1) s += Math.min(1, Math.abs(a[i] - b[i]));
  return s / a.length;
}

/** Subsequence DTW: referensi utuh (baris) dicocokkan ke bagian mana pun dari rekaman pengguna (kolom). */
export function subsequenceDTW(ref: (number[] | null)[], user: (number[] | null)[]): { path: [number, number][]; cost: number } {
  const n = ref.length, m = user.length;
  const INF = Number.POSITIVE_INFINITY;
  const D = Array.from({ length: n }, () => new Float64Array(m).fill(INF));
  const c = (i: number, j: number) => (ref[i] && user[j] ? dist(ref[i]!, user[j]!) : ENGINE_PARAMS.unusableCost);
  for (let j = 0; j < m; j += 1) D[0][j] = c(0, j);
  for (let i = 1; i < n; i += 1) {
    D[i][0] = D[i - 1][0] + c(i, 0);
    for (let j = 1; j < m; j += 1) D[i][j] = c(i, j) + Math.min(D[i - 1][j], D[i][j - 1], D[i - 1][j - 1]);
  }
  let end = 0;
  for (let j = 1; j < m; j += 1) if (D[n - 1][j] < D[n - 1][end]) end = j;
  const path: [number, number][] = [];
  let i = n - 1, j = end;
  path.push([i, j]);
  while (i > 0) {
    const opts: [number, number, number][] = [[i - 1, j, D[i - 1][j]]];
    if (j > 0) opts.push([i, j - 1, D[i][j - 1]], [i - 1, j - 1, D[i - 1][j - 1]]);
    opts.sort((a, b) => a[2] - b[2]);
    [i, j] = [opts[0][0], opts[0][1]];
    path.push([i, j]);
  }
  path.reverse();
  return { path, cost: D[n - 1][end] / path.length };
}

// ---------------------------------------------------------------- nilai kriteria
function aggregate(vals: number[], how: CriterionSpec["aggregate"]): number {
  const v = vals.filter(Number.isFinite).sort((a, b) => a - b);
  if (!v.length) return NaN;
  if (how === "max") return v[v.length - 1];
  if (how === "min") return v[0];
  if (how === "std") {
    const m = v.reduce((a, b) => a + b, 0) / v.length;
    return Math.sqrt(v.reduce((a, b) => a + (b - m) ** 2, 0) / v.length);
  }
  return v[Math.floor(v.length / 2)];
}

export function criterionScore(c: Pick<CriterionSpec, "target" | "target_range" | "tolerance" | "falloff">, actual: number): { score: number; dir: "ok" | "below" | "above" } {
  const [lo, hi] = c.target_range ?? [c.target! - c.tolerance, c.target! + c.tolerance];
  const lo2 = c.target_range ? lo - c.tolerance : lo, hi2 = c.target_range ? hi + c.tolerance : hi;
  if (actual >= lo2 && actual <= hi2) return { score: 100, dir: "ok" };
  const err = actual < lo2 ? lo2 - actual : actual - hi2;
  return { score: Math.max(0, Math.round(100 * (1 - err / c.falloff))), dir: actual < lo2 ? "below" : "above" };
}

function windowValues(frames: MeasureFrame[], c: CriterionSpec): { vals: number[]; conf: number } {
  const space = c.requires_world ? "world" : "image";
  const vals: number[] = [];
  const confs: number[] = [];
  const hips: number[] = [];
  for (const f of frames) {
    const p = pts(f, space), pImg = pts(f, "image");
    if (!p || !pImg || !f.usable) continue;
    if (c.feature === "hip_sway") {
      const y = (p[LM.lHip][1] + p[LM.rHip][1]) / 2 / legLength(p, space);
      hips.push(y);
      confs.push(frameConfidence(f, featureLandmarks("hip_sway", "both")));
      continue;
    }
    const sideRule = c.side ?? "both_mean";
    const side = resolveSide(sideRule, pImg);
    let v: number;
    if (side === "both") {
      const a = featureValue(c.feature, p, "L", space), b = featureValue(c.feature, p, "R", space);
      v = sideRule === "both_min" ? Math.min(a, b) : (a + b) / 2;
    } else v = featureValue(c.feature, p, side, space);
    vals.push(v);
    confs.push(frameConfidence(f, featureLandmarks(c.feature, side)));
  }
  if (c.feature === "hip_sway") return { vals: hips.length > 2 ? [aggregate(hips, "std")] : [], conf: confs.length ? confs.reduce((a, b) => a + b, 0) / confs.length : 0 };
  return { vals, conf: confs.length ? confs.reduce((a, b) => a + b, 0) / confs.length : 0 };
}

// ---------------------------------------------------------------- penilaian utama
export function assess(protocol: Protocol, reference: ReferenceFrame[], user: MeasureFrame[]): AssessmentOutcome {
  const base = { protocol_id: protocol.protocol_id, protocol_version: protocol.protocol_version, reference_id: protocol.reference_id, engine_version: ENGINE_VERSION };
  const usable = user.filter((f) => f.usable);
  const req = protocol.required_landmarks;
  const meanVis = usable.length ? usable.reduce((a, f) => a + req.reduce((s, i) => s + (f.visibility[i] ?? 0), 0) / req.length, 0) / usable.length : 0;
  const inputQuality = Math.round((user.length ? usable.length / user.length : 0) * meanVis * 100) / 100;
  const cr = protocol.confidence_requirements;
  const na = (reason: Extract<AssessmentOutcome, { status: "not_assessable" }>["reason"], message: string): AssessmentOutcome =>
    ({ status: "not_assessable", reason, message, input_quality: inputQuality, frames_analyzed: user.length, ...base });

  if (user.length < cr.min_frames) return na("TOO_FEW_FRAMES", "Rekaman terlalu singkat untuk dinilai. Lakukan seluruh rangkaian gerak dari awal sampai kembali ke sikap awal.");
  if (usable.length / user.length < cr.min_valid_frame_ratio) {
    return na("LOW_INPUT_QUALITY", "Tubuh belum terlihat jelas pada sebagian besar rekaman. Pastikan seluruh badan, termasuk kaki, berada di dalam bingkai dan cahaya cukup.");
  }
  if (meanVis < protocol.min_visibility) return na("KEY_LANDMARKS_MISSING", "Beberapa titik tubuh penting tidak terdeteksi dengan yakin. Mundurlah sedikit dari kamera dan hindari benda yang menutupi tubuh.");
  const views = usable.map((f) => estimateView(f.image!)).filter((v) => v !== "unknown");
  const share = views.filter((v) => v === protocol.required_view).length / Math.max(1, views.length);
  if (views.length >= 5 && share < 0.5) {
    return na("WRONG_CAMERA_VIEW", protocol.required_view === "side"
      ? "Gerakan ini diukur dari samping. Putar badan sehingga sisi tubuh menghadap kamera, lalu ulangi."
      : "Gerakan ini diukur dari depan. Hadapkan badan ke kamera, lalu ulangi.");
  }

  // penyelarasan
  const feats = protocol.alignment_features;
  const refVec = reference.map((r) => alignVector(r.frame, feats));
  const userVec = user.map((f) => alignVector(f, feats));
  const { path, cost } = subsequenceDTW(refVec, userVec);
  if (cost > ENGINE_PARAMS.maxAlignmentCost) {
    return na("MOVEMENT_NOT_FOUND", "Rangkaian gerak belum terdeteksi sesuai urutan panduan. Tonton peraga sekali lagi, lalu lakukan seluruh fase dengan jelas.");
  }
  const userByKf = new Map<string, number[]>();
  const costByKf = new Map<string, number[]>();
  for (const [ri, uj] of path) {
    const kf = reference[ri].keyframe;
    if (!userByKf.has(kf)) { userByKf.set(kf, []); costByKf.set(kf, []); }
    const arr = userByKf.get(kf)!;
    if (arr[arr.length - 1] !== uj) arr.push(uj);
    costByKf.get(kf)!.push(refVec[ri] && userVec[uj] ? dist(refVec[ri]!, userVec[uj]!) : ENGINE_PARAMS.unusableCost);
  }
  const refSpan = (kf: string) => {
    const ts = reference.filter((r) => r.keyframe === kf).map((r) => r.t);
    return ts.length ? Math.max(...ts) - Math.min(...ts) : 0;
  };

  const phases: PhaseResult[] = protocol.phases.map((ph) => {
    const us = userByKf.get(ph.keyframe) ?? [];
    const cs = costByKf.get(ph.keyframe) ?? [];
    const meanCost = cs.length ? cs.reduce((a, b) => a + b, 0) / cs.length : 1;
    const detected = us.length >= ENGINE_PARAMS.minPhaseFrames && meanCost <= ENGINE_PARAMS.maxPhaseCost;
    const t0 = us.length ? user[us[0]].t : null, t1 = us.length ? user[us[us.length - 1]].t : null;
    const rs = refSpan(ph.keyframe);
    return { keyframe: ph.keyframe, label: ph.label, detected, score: null, user_start: t0, user_end: t1,
      tempo_ratio: detected && t0 !== null && t1 !== null && rs > 0.2 ? Math.round(((t1 - t0) / rs) * 100) / 100 : null };
  });

  // kriteria
  const criteria: CriterionResult[] = protocol.criteria.map((c) => {
    const frames = (userByKf.get(c.phase_keyframe) ?? []).map((j) => user[j]);
    const phaseOk = phases.find((p) => p.keyframe === c.phase_keyframe)?.detected ?? false;
    const { vals, conf } = windowValues(frames, c);
    const actual = aggregate(vals, c.feature === "hip_sway" ? "median" : c.aggregate);
    const target = c.target_range ?? c.target!;
    const common = { id: c.id, label: c.label, feature: c.feature, unit: c.unit, target, tolerance: c.tolerance, weight: c.weight, basis: c.basis, phase_keyframe: c.phase_keyframe };
    if (!phaseOk || !Number.isFinite(actual) || conf < c.min_confidence || (c.requires_world && !frames.some((f) => f.world))) {
      return { ...common, actual: null, confidence: Math.round(conf * 100) / 100, score: null, status: "unmeasured" as const,
        feedback: c.feedback.unmeasured ?? (phaseOk ? "Bagian tubuh yang diperlukan tidak terukur dengan yakin pada fase ini." : "Fase ini belum terlihat dalam rekaman.") };
    }
    const { score, dir } = criterionScore(c, actual);
    return { ...common, actual: Math.round(actual * 100) / 100, confidence: Math.round(conf * 100) / 100, score,
      status: dir, feedback: dir === "ok" ? c.feedback.ok : dir === "below" ? c.feedback.below : c.feedback.above };
  });

  const measured = criteria.filter((c) => c.score !== null);
  const wAll = criteria.reduce((a, c) => a + c.weight, 0) + protocol.phase_completion_weight;
  const wUnmeasured = criteria.filter((c) => c.score === null).reduce((a, c) => a + c.weight, 0);
  if (wUnmeasured / wAll > cr.max_unmeasured_weight_ratio) {
    return na("TOO_MANY_UNMEASURED", "Sebagian besar kriteria belum dapat diukur dari rekaman ini. Atur posisi kamera sesuai petunjuk dan ulangi seluruh gerakan.");
  }
  const required = phases.filter((p) => protocol.phases.find((q) => q.keyframe === p.keyframe)?.required);
  const completion = required.length ? (required.filter((p) => p.detected).length / required.length) * 100 : 100;
  const num = measured.reduce((a, c) => a + c.score! * c.weight, 0) + completion * protocol.phase_completion_weight;
  const den = measured.reduce((a, c) => a + c.weight, 0) + protocol.phase_completion_weight;
  const total = Math.round(num / den);

  for (const ph of phases) {
    const cs = measured.filter((c) => c.phase_keyframe === ph.keyframe);
    ph.score = cs.length ? Math.round(cs.reduce((a, c) => a + c.score! * c.weight, 0) / cs.reduce((a, c) => a + c.weight, 0)) : null;
  }
  const scored = phases.filter((p) => p.score !== null);
  const best = scored.length ? scored.reduce((a, b) => (b.score! > a.score! ? b : a)) : null;
  const weakest = scored.length ? scored.reduce((a, b) => (b.score! < a.score! ? b : a)) : null;

  // saran paling relevan = kehilangan poin berbobot terbesar
  const suggestions = measured.filter((c) => c.score! < 85)
    .sort((a, b) => (100 - b.score!) * b.weight - (100 - a.score!) * a.weight).slice(0, 3).map((c) => c.feedback);
  for (const p of phases) if (!p.detected && suggestions.length < 3) suggestions.push(`Fase "${p.label}" belum terlihat. Lakukan fase ini dengan jelas dan tahan sejenak.`);
  if (!suggestions.length) suggestions.push("Semua kriteria yang terukur sudah sesuai panduan. Pertahankan, dan mintalah pelatih memeriksa detail teknik Anda.");

  return {
    status: "scored", total_score: total, input_quality: inputQuality, criteria, phases,
    best_phase: best && weakest && best !== weakest ? best.label : best?.label ?? null,
    weakest_phase: weakest && best && weakest !== best && weakest.score! < 90 ? weakest.label : null,
    suggestions, frames_analyzed: user.length, duration_s: user.length ? Math.round((user[user.length - 1].t - user[0].t) * 10) / 10 : 0, ...base,
  };
}

// ---------------------------------------------------------------- referensi
export interface ReferenceJson {
  reference_id: string; fps: number; view: "front" | "side";
  frames: { t: number; keyframe: string; pose: Vec3[] }[];
}

/** Proyeksikan urutan referensi 3D (Y ke atas, menghadap +Z) ke ruang ukur sesuai tampak kamera protokol. */
export function referenceFrames(ref: ReferenceJson, view: "front" | "side"): ReferenceFrame[] {
  return ref.frames.map((fr) => {
    const image = fr.pose.map((p): Vec3 => (view === "side" ? [p[2], -p[1], 0] : [p[0], -p[1], 0]));
    const world = fr.pose.map((p): Vec3 => [p[0], -p[1], p[2]]);
    return { t: fr.t, keyframe: fr.keyframe, frame: { t: fr.t, image, world, visibility: new Array(33).fill(1), usable: true } };
  });
}

export type { Side };
