import { describe, expect, it } from "vitest";
import { QualityAggregator, SessionClock, StateSmoother, deriveDetectionState, studioGuidance, STATE_LABEL } from "@/features/practice/studio-state";
import { assessFrameQuality } from "@/features/practice/quality-gate";
import { syntheticFrame } from "@/features/practice/synthetic-pose";

const q = (sc: Parameters<typeof syntheticFrame>[0]) => assessFrameQuality(syntheticFrame(sc, 0, 0));

describe("deriveDetectionState (hanya kualitas input)", () => {
  it.each([
    ["waiting", "waiting_for_subject"], ["full", "detecting"], ["partial", "partial_detection"],
    ["out_of_frame", "partial_detection"], ["multiple", "insufficient_visibility"],
  ] as const)("skenario %s -> %s", (sc, expected) => expect(deriveDetectionState(q(sc))).toBe(expected));
  it("cakupan rendah -> insufficient_visibility", () => {
    expect(deriveDetectionState({ usable: false, reasons: ["LOW_VISIBILITY"], requiredCoverage: 0.2 })).toBe("insufficient_visibility");
  });
  it("tidak ada keluaran skor/penilaian gerakan pada status maupun panduan", () => {
    for (const s of ["waiting_for_subject", "detecting", "partial_detection", "insufficient_visibility"] as const) {
      const g = studioGuidance(s, ["OUT_OF_FRAME"]);
      expect(`${g.title} ${g.hint}`).not.toMatch(/\b(skor|nilai|benar|salah|akurasi|kemiripan|jurus|teknik)\b/i);
    }
    for (const l of Object.values(STATE_LABEL)) expect(l).not.toMatch(/\b(skor|nilai|benar|salah|akurasi)\b/i);
  });
  it("panduan sesuai alasan", () => {
    expect(studioGuidance("insufficient_visibility", ["OUT_OF_FRAME"]).title).toBe("Posisikan seluruh tubuh di dalam kamera");
    expect(studioGuidance("partial_detection", ["OUT_OF_FRAME"]).title).toBe("Mundur sedikit agar tubuh terlihat");
    expect(studioGuidance("partial_detection", ["LOW_VISIBILITY"]).title).toBe("Pastikan kamera tidak terhalang");
    expect(studioGuidance("waiting_for_subject", ["NO_POSE"]).title).toBe("Posisi tubuh belum terdeteksi");
    expect(studioGuidance("insufficient_visibility", ["MULTIPLE_PEOPLE"]).title).toMatch(/satu orang/);
  });
});

describe("StateSmoother", () => {
  it("baru berubah setelah n hasil berurutan sama; satu glitch tidak mengubah status", () => {
    const s = new StateSmoother(3);
    expect(s.current).toBe("waiting_for_subject");
    s.push("detecting"); s.push("detecting");
    expect(s.current).toBe("waiting_for_subject");
    expect(s.push("detecting")).toBe("detecting");
    s.push("partial_detection"); // glitch
    expect(s.push("detecting")).toBe("detecting");
    s.push("insufficient_visibility"); s.push("insufficient_visibility");
    expect(s.push("insufficient_visibility")).toBe("insufficient_visibility");
  });
  it("kandidat berbeda mereset hitungan", () => {
    const s = new StateSmoother(3);
    s.push("detecting"); s.push("detecting"); s.push("partial_detection"); s.push("detecting"); s.push("detecting");
    expect(s.current).toBe("waiting_for_subject");
  });
});

describe("SessionClock (timer aktif vs jeda)", () => {
  it("waktu aktif dan jeda dipisah; stop menghentikan penambahan", () => {
    let t = 0; const c = new SessionClock(() => t);
    c.start(); t = 4000; c.pause(); t = 7000; c.resume(); t = 8000;
    expect(c.read()).toEqual({ activeMs: 5000, pausedMs: 3000 });
    t = 9000; const r = c.stop();
    expect(r).toEqual({ activeMs: 6000, pausedMs: 3000 });
    t = 20000; expect(c.read()).toEqual(r);
  });
  it("pause/resume ganda tidak merusak hitungan; sebelum start = 0", () => {
    let t = 0; const c = new SessionClock(() => t);
    expect(c.read()).toEqual({ activeMs: 0, pausedMs: 0 });
    c.start(); t = 1000; c.pause(); c.pause(); t = 2000; c.resume(); c.resume(); t = 3000;
    expect(c.read()).toEqual({ activeMs: 2000, pausedMs: 1000 });
  });
});

describe("QualityAggregator", () => {
  it("mengagregasi waktu per status, rasio valid, dan alasan; jeda tidak dihitung; tanpa landmark", () => {
    const a = new QualityAggregator();
    a.start(0);
    a.record("waiting_for_subject", q("waiting"), 1000);
    a.record("detecting", q("full"), 2000);   // 1000 ms diatribusikan ke status frame sebelumnya (waiting)
    a.record("detecting", q("full"), 3000);
    a.pause(3500);
    a.resume(10_000);                          // 6500 ms jeda tidak dihitung
    a.record("partial_detection", q("partial"), 11_000);
    const s = a.snapshot(12_000, { dropped: 5, engine: "synthetic", delegate: null, simulated: true });
    expect(s.processed_frames).toBe(4); expect(s.frames_total).toBe(9); expect(s.dropped_frames).toBe(5);
    expect(s.valid_frame_ratio).toBeCloseTo(2 / 4);
    expect(s.ms_in_state.waiting_for_subject).toBe(2000);   // 0→1000 (awal) + 1000→2000
    // Semantik: selang waktu diatribusikan ke status frame TERAKHIR yang diketahui sebelum frame baru tiba.
    expect(s.ms_in_state.detecting).toBe(2500);             // 2000→3000 + 3000→3500 + (resume 10000→11000, status terakhir masih detecting)
    expect(s.ms_in_state.partial_detection).toBe(1000);     // 11000→12000 (snapshot)
    expect(s.reasons.NO_POSE).toBe(1); expect(s.reasons.LOW_VISIBILITY).toBeGreaterThanOrEqual(1);
    expect(JSON.stringify(s)).not.toMatch(/"landmarks?"|"x"\s*:|"y"\s*:|"z"\s*:|"visibility"\s*:|"presence"\s*:/);
    expect(Object.keys(s).sort()).toEqual(["delegate", "dropped_frames", "engine", "frames_total", "ms_in_state", "processed_frames", "reasons", "simulated", "valid_frame_ratio"]);
  });
  it("sesi tanpa frame: rasio 0, tidak membagi nol", () => {
    const a = new QualityAggregator(); a.start(0);
    expect(a.snapshot(1000, { dropped: 0, engine: "worker", delegate: "CPU", simulated: false }).valid_frame_ratio).toBe(0);
  });
});
