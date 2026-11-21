import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { assess, criterionScore, referenceFrames, subsequenceDTW, type ReferenceFrame, type ReferenceJson } from "@/features/assessment/engine";
import { featureValue, jointAngle } from "@/features/assessment/features";
import { lerpPose, synthFrame, synthSequence, type SynthPose } from "@/features/assessment/synthetic";
import type { MeasureFrame, Protocol } from "@/features/assessment/types";

// Uji SINTETIS: memeriksa matematika & integrasi mesin. Bukan bukti akurasi pada manusia/kamera nyata.
const FIX = join(__dirname, "__fixtures__");
const protocol = JSON.parse(readFileSync(join(FIX, "langkah-angkatan.protocol.json"), "utf-8")) as Protocol;

const stand: SynthPose = { view: "side", thighL: 2, thighR: 2, kneeL: 2, kneeR: 2, wristHip: 0.1 };
const high = (thigh = 90, knee = 90): SynthPose => ({ ...stand, thighL: thigh, kneeL: knee });
const placed: SynthPose = { ...stand, thighL: 5, kneeL: 25, footL: 0.45, footR: -0.25, hipShift: 0.12 };
const low = (flex = 30): SynthPose => ({ ...stand, thighL: flex * 0.75, kneeL: flex });

function sequence(o: { highThigh?: number; highKnee?: number; lowFlex?: number; skipLow?: boolean; speed?: number; visibility?: number } = {}) {
  const sp = o.speed ?? 1;
  const keys = [
    { pose: stand, hold: 0.7 / sp, move: 0 },
    { pose: high(o.highThigh ?? 90, o.highKnee ?? 90), hold: 0.9 / sp, move: 0.8 / sp },
    { pose: placed, hold: 0.8 / sp, move: 0.8 / sp },
    { pose: stand, hold: 0.5 / sp, move: 0.8 / sp },
    ...(o.skipLow ? [] : [{ pose: low(o.lowFlex ?? 30), hold: 0.8 / sp, move: 0.6 / sp }]),
    { pose: stand, hold: 0.7 / sp, move: 0.7 / sp },
  ];
  return synthSequence(keys, 15, { visibility: o.visibility });
}

/** Referensi sintetis berlabel keyframe (bentuknya sama dengan referensi 3D terproyeksi). */
function synthReference(): ReferenceFrame[] {
  const labels = ["kf-1", "kf-2", "kf-3", "kf-1", "kf-4", "kf-1"];
  const keys = [stand, high(), placed, stand, low(), stand];
  const out: ReferenceFrame[] = [];
  let t = 0;
  keys.forEach((pose, i) => {
    if (i > 0) {
      const n = 11;
      for (let s = 1; s <= n; s += 1) { out.push({ t, keyframe: s <= n / 2 ? labels[i - 1] : labels[i], frame: synthFrame(t, lerpPose(keys[i - 1], pose, s / n)) }); t += 1 / 15; }
    }
    for (let s = 0; s < 12; s += 1) { out.push({ t, keyframe: labels[i], frame: synthFrame(t, pose) }); t += 1 / 15; }
  });
  return out;
}

const REF = synthReference();

describe("matematika dasar", () => {
  it("sudut sendi & skor kriteria", () => {
    expect(jointAngle([0, 0, 0], [0, 1, 0], [1, 1, 0])).toBeCloseTo(90, 5);
    const c = { target: 90, tolerance: 10, falloff: 40 };
    expect(criterionScore(c, 85).score).toBe(100);
    expect(criterionScore(c, 60)).toEqual({ score: 50, dir: "below" });
    expect(criterionScore(c, 140).score).toBe(0);
    expect(criterionScore({ target_range: [10, 45], tolerance: 5, falloff: 25 }, 60)).toEqual({ score: 60, dir: "above" });
  });
  it("elevasi paha sintetis terukur sesuai parameter", () => {
    const f = sequence()[20];
    expect(Number.isFinite(featureValue("thigh_elevation", f.image!, "L", "image"))).toBe(true);
    const hi = sequence().find((x) => featureValue("thigh_elevation", x.image!, "L", "image") > 85);
    expect(hi).toBeDefined();
  });
  it("DTW menemukan referensi di tengah rekaman yang lebih panjang", () => {
    const ref = [[0], [0.5], [1], [0.5], [0]];
    const user = [[0], [0], [0], [0.5], [1], [1], [0.5], [0], [0]];
    const { path, cost } = subsequenceDTW(ref, user);
    expect(cost).toBeLessThan(0.05);
    expect(path[0][1]).toBeGreaterThanOrEqual(2);
  });
});

describe("penilaian langkah angkatan (sintetis)", () => {
  it("gerakan sesuai panduan mendapat skor tinggi", () => {
    const r = assess(protocol, REF, sequence());
    expect(r.status).toBe("scored");
    if (r.status !== "scored") return;
    expect(r.total_score).toBeGreaterThanOrEqual(90);
    expect(r.criteria.find((c) => c.id === "high_thigh")!.status).toBe("ok");
  });

  it("kaki terangkat terlalu rendah: skor kriteria turun sesuai metrik & umpan balik spesifik", () => {
    const r = assess(protocol, REF, sequence({ highThigh: 55, highKnee: 70 }));
    expect(r.status).toBe("scored");
    if (r.status !== "scored") return;
    const hc = r.criteria.find((c) => c.id === "high_thigh")!;
    expect(hc.status).toBe("below");
    expect(hc.actual!).toBeLessThan(65);
    // skor dari rumus, bukan angka tetap: 100 × (1 − (80 − aktual)/45)
    expect(hc.score).toBe(Math.max(0, Math.round(100 * (1 - (80 - hc.actual!) / 45))));
    expect(r.suggestions[0]).toContain("paha belum mendatar");
    const good = assess(protocol, REF, sequence());
    if (good.status === "scored") expect(r.total_score).toBeLessThan(good.total_score);
    // total = Σ skor×bobot / Σ bobot (dapat direproduksi dari breakdown)
    const m = r.criteria.filter((c) => c.score !== null);
    const req = r.phases.filter((p) => protocol.phases.find((q) => q.keyframe === p.keyframe)?.required);
    const comp = (req.filter((p) => p.detected).length / req.length) * 100;
    const expected = Math.round((m.reduce((a, c) => a + c.score! * c.weight, 0) + comp * protocol.phase_completion_weight) / (m.reduce((a, c) => a + c.weight, 0) + protocol.phase_completion_weight));
    expect(r.total_score).toBe(expected);
  });

  it("deterministik: fixture yang sama menghasilkan hasil identik", () => {
    const a = assess(protocol, REF, sequence({ highThigh: 70 }));
    const b = assess(protocol, REF, sequence({ highThigh: 70 }));
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });

  it("gerakan lebih cepat tetap diselaraskan (DTW) dengan skor serupa", () => {
    const n = assess(protocol, REF, sequence());
    const f = assess(protocol, REF, sequence({ speed: 1.6 }));
    expect(f.status).toBe("scored");
    if (n.status === "scored" && f.status === "scored") expect(Math.abs(n.total_score - f.total_score)).toBeLessThanOrEqual(10);
  });

  it("fase yang dilewati terdeteksi dan disebut di saran", () => {
    const r = assess(protocol, REF, sequence({ skipLow: true }));
    if (r.status === "scored") {
      expect(r.phases.find((p) => p.keyframe === "kf-4")!.detected).toBe(false);
      expect(r.criteria.find((c) => c.id === "low_lift")!.status).toBe("unmeasured");
    } else {
      expect(["MOVEMENT_NOT_FOUND", "TOO_MANY_UNMEASURED"]).toContain(r.reason);
    }
  });

  it("confidence rendah TIDAK menghasilkan skor palsu", () => {
    const r = assess(protocol, REF, sequence({ visibility: 0.3 }));
    expect(r.status).toBe("not_assessable");
    if (r.status === "not_assessable") expect(r.reason).toBe("KEY_LANDMARKS_MISSING");
  });

  it("sebagian besar frame tak layak → not_assessable", () => {
    const s = sequence().map((f, i): MeasureFrame => ({ ...f, usable: i % 3 === 0 }));
    const r = assess(protocol, REF, s);
    expect(r.status).toBe("not_assessable");
    if (r.status === "not_assessable") expect(r.reason).toBe("LOW_INPUT_QUALITY");
  });

  it("sudut kamera salah (tampak depan untuk protokol tampak samping) ditolak", () => {
    const front = sequence().map((f) => ({ ...f, image: f.image!.map(([x, y, z], i) => [i === 11 || i === 23 || i === 25 || i === 27 ? x + 0.1 : i === 12 || i === 24 || i === 26 || i === 28 ? x - 0.1 : x, y, z] as [number, number, number]) }));
    const r = assess(protocol, REF, front);
    expect(r.status).toBe("not_assessable");
    if (r.status === "not_assessable") expect(r.reason).toBe("WRONG_CAMERA_VIEW");
  });

  it("rekaman terlalu singkat ditolak", () => {
    const r = assess(protocol, REF, sequence().slice(0, 10));
    expect(r.status).toBe("not_assessable");
  });
});

describe("referensi 3D asli (klip SILATARA) sebagai masukan", () => {
  const ref = JSON.parse(readFileSync(join(FIX, "ref.langkah-angkatan.json"), "utf-8")) as ReferenceJson;
  const R = referenceFrames(ref, "side");
  it("referensi dinilai terhadap dirinya sendiri mendapat skor tinggi", () => {
    const user = R.map((r) => ({ ...r.frame, visibility: new Array(33).fill(0.9) }));
    const out = assess(protocol, R, user);
    expect(out.status).toBe("scored");
    if (out.status === "scored") expect(out.total_score).toBeGreaterThanOrEqual(90);
  });
  it("menurunkan angkatan paha pada referensi menurunkan skor kriteria tinggi angkatan", () => {
    // putar paha & tungkai bawah kaki yang terangkat 40° ke bawah di sekitar pinggul (bidang samping)
    const lower = (f: MeasureFrame): MeasureFrame => {
      const p = f.image!.map((q) => [...q] as [number, number, number]);
      const liftedL = p[27][1] < p[28][1];
      const [hip, knee, ank, heel, toe] = liftedL ? [23, 25, 27, 29, 31] : [24, 26, 28, 30, 32];
      if (featureValue("thigh_elevation", f.image!, liftedL ? "L" : "R", "image") < 45) return f;
      const a = (40 * Math.PI) / 180, s = Math.sign(p[knee][0] - p[hip][0]) || 1;
      for (const i of [knee, ank, heel, toe]) {
        const dx = p[i][0] - p[hip][0], dy = p[i][1] - p[hip][1];
        const c = Math.cos(a * s), sn = Math.sin(a * s);
        p[i] = [p[hip][0] + dx * c - dy * sn, p[hip][1] + dx * sn + dy * c, 0];
      }
      return { ...f, image: p };
    };
    const user = R.map((r) => lower({ ...r.frame, visibility: new Array(33).fill(0.9) }));
    const out = assess(protocol, R, user);
    expect(out.status).toBe("scored");
    if (out.status === "scored") {
      const hc = out.criteria.find((c) => c.id === "high_thigh")!;
      expect(hc.status).toBe("below");
      expect(hc.score!).toBeLessThan(80);
    }
  });
});
