// Seluruh data pada tes ini adalah SYNTHETIC TEST FIXTURE (lihat fixtures.ts).
import { describe, expect, it } from "vitest";
import { syntheticFrame, syntheticHand, syntheticPose, SYNTHETIC_FIXTURE_NOTICE } from "@/features/practice/fixtures";
import { POSE_INDEX } from "@/features/practice/landmarks";
import {
  assessFrameQuality, DEFAULT_QUALITY_CONFIG, guidanceFor, QualityWindow, summarizeQuality,
} from "@/features/practice/quality-gate";

describe("fixture", () => {
  it("diberi label sintetis", () => expect(SYNTHETIC_FIXTURE_NOTICE).toMatch(/synthetic/));
});

describe("assessFrameQuality", () => {
  it("frame lengkap & terlihat -> usable", () => {
    const q = assessFrameQuality(syntheticFrame());
    expect(q).toMatchObject({ usable: true, reasons: [], requiredCoverage: 1 });
  });
  it("tanpa pose -> NO_POSE (bukan skor nol)", () => {
    const q = assessFrameQuality(syntheticFrame({ poses: [] }));
    expect(q.usable).toBe(false);
    expect(q.reasons).toEqual(["NO_POSE"]);
  });
  it("landmark kurang dari 33 -> TOO_FEW_LANDMARKS", () => {
    expect(assessFrameQuality(syntheticFrame({ poses: [syntheticPose({}, 20)] })).reasons).toEqual(["TOO_FEW_LANDMARKS"]);
  });
  it("visibilitas rendah pada landmark wajib -> LOW_VISIBILITY & cakupan < 1", () => {
    const q = assessFrameQuality(syntheticFrame({ poses: [syntheticPose({ [POSE_INDEX.leftKnee]: { visibility: 0.1 } })] }));
    expect(q.usable).toBe(false);
    expect(q.reasons).toEqual(["LOW_VISIBILITY"]);
    expect(q.requiredCoverage).toBeCloseTo(8 / 9);
  });
  it("visibility tidak diketahui (undefined) dianggap tidak terlihat", () => {
    const q = assessFrameQuality(syntheticFrame({ poses: [syntheticPose({ [POSE_INDEX.nose]: { visibility: undefined } })] }));
    expect(q.usable).toBe(false);
  });
  it("landmark di luar frame -> OUT_OF_FRAME", () => {
    const q = assessFrameQuality(syntheticFrame({ poses: [syntheticPose({ [POSE_INDEX.leftAnkle]: { y: 1.08 } })] }));
    expect(q.reasons).toEqual(["OUT_OF_FRAME"]);
  });
  it("batas margin: tepat di tepi dianggap di luar", () => {
    const q = assessFrameQuality(syntheticFrame({ poses: [syntheticPose({ [POSE_INDEX.nose]: { y: 0.0 } })] }));
    expect(q.reasons).toContain("OUT_OF_FRAME");
  });
  it("koordinat NaN/Infinity tidak dianggap valid", () => {
    const q = assessFrameQuality(syntheticFrame({ poses: [syntheticPose({ [POSE_INDEX.nose]: { x: NaN } })] }));
    expect(q.usable).toBe(false);
  });
  it("lebih dari satu orang -> MULTIPLE_PEOPLE (kecuali diizinkan)", () => {
    const f = syntheticFrame({ poses: [syntheticPose(), syntheticPose()] });
    expect(assessFrameQuality(f).reasons).toContain("MULTIPLE_PEOPLE");
    expect(assessFrameQuality(f, { ...DEFAULT_QUALITY_CONFIG, allowMultiplePeople: true }).usable).toBe(true);
  });
  it("tangan hanya dipersyaratkan bila requireHands", () => {
    const cfg = { ...DEFAULT_QUALITY_CONFIG, requireHands: true };
    expect(assessFrameQuality(syntheticFrame(), cfg).reasons).toEqual(["NO_HAND"]);
    expect(assessFrameQuality(syntheticFrame({ hands: [syntheticHand(0.2)] }), cfg).reasons).toEqual(["LOW_HAND_CONFIDENCE"]);
    expect(assessFrameQuality(syntheticFrame({ hands: [syntheticHand(0.9)] }), cfg).usable).toBe(true);
    expect(assessFrameQuality(syntheticFrame()).usable).toBe(true);
  });
  it("tidak ada keluaran skor/benar-salah gerakan", () => {
    const q = assessFrameQuality(syntheticFrame());
    expect(Object.keys(q).sort()).toEqual(["meanVisibility", "reasons", "requiredCoverage", "usable"]);
  });
});

describe("summarizeQuality", () => {
  const good = () => assessFrameQuality(syntheticFrame());
  const bad = () => assessFrameQuality(syntheticFrame({ poses: [] }));
  it("tanpa frame -> insufficient", () => expect(summarizeQuality([]).status).toBe("insufficient"));
  it("cukup frame & rasio tinggi -> sufficient", () => {
    const s = summarizeQuality([...Array(28).fill(0).map(good), ...Array(2).fill(0).map(bad)]);
    expect(s).toMatchObject({ frames: 30, status: "sufficient", dominantReason: null });
    expect(s.valid_frame_ratio).toBeCloseTo(28 / 30);
    expect(s.dropped_frame_ratio).toBeCloseTo(2 / 30);
  });
  it("terlalu sedikit frame -> insufficient walau semua bagus", () => {
    expect(summarizeQuality(Array(5).fill(0).map(good)).status).toBe("insufficient");
  });
  it("rasio rendah -> insufficient + alasan dominan", () => {
    const s = summarizeQuality([...Array(10).fill(0).map(good), ...Array(20).fill(0).map(bad)]);
    expect(s.status).toBe("insufficient");
    expect(s.dominantReason).toBe("NO_POSE");
  });
});

describe("QualityWindow & guidance", () => {
  it("stabil hanya setelah jendela penuh dan mayoritas layak", () => {
    const w = new QualityWindow(5);
    for (let i = 0; i < 4; i++) w.push(assessFrameQuality(syntheticFrame()));
    expect(w.stable).toBe(false);
    w.push(assessFrameQuality(syntheticFrame()));
    expect(w.stable).toBe(true);
    for (let i = 0; i < 3; i++) w.push(assessFrameQuality(syntheticFrame({ poses: [] })));
    expect(w.stable).toBe(false);
    w.reset();
    expect(w.length).toBe(0);
  });
  it("panduan berbahasa membantu, tanpa menyalahkan", () => {
    expect(guidanceFor({ usable: false, reasons: ["OUT_OF_FRAME"] })).toMatch(/belum terlihat penuh/);
    expect(guidanceFor({ usable: true, reasons: [] })).toMatch(/baik/);
  });
});
