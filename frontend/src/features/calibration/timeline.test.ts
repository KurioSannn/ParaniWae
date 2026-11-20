import { describe, expect, it } from "vitest";
import { clampMs, FRAME_MS, formatTimeMs, markerNear, msToPct, posToMs, segmentAt, segments, sortMarkers, stepFrame } from "@/features/calibration/timeline";

const m = (id: string, t: number, label = id, phase: string | null = null) => ({ id, timestamp_ms: t, label, phase_id: phase });

describe("timeline calibration", () => {
  it("clampMs membatasi ke [0, durasi] dan menolak NaN/Infinity", () => {
    expect(clampMs(-5, 1000)).toBe(0);
    expect(clampMs(1500, 1000)).toBe(1000);
    expect(clampMs(Number.NaN, 1000)).toBe(0);
    expect(clampMs(Number.POSITIVE_INFINITY, 1000)).toBe(0);
    expect(clampMs(333.6, 1000)).toBe(334);
  });
  it("stepFrame maju/mundur satu langkah nominal dan tidak keluar rentang", () => {
    expect(stepFrame(0, -1, 1000)).toBe(0);
    expect(stepFrame(0, 1, 1000)).toBe(Math.round(FRAME_MS));
    expect(stepFrame(1000, 1, 1000)).toBe(1000);
  });
  it("sortMarkers stabil (waktu lalu id) dan tidak memutasi input", () => {
    const src = [m("b", 200), m("a", 200), m("c", 100)];
    expect(sortMarkers(src).map((x) => x.id)).toEqual(["c", "a", "b"]);
    expect(src.map((x) => x.id)).toEqual(["b", "a", "c"]);
  });
  it("markerNear memilih yang terdekat dalam toleransi, selain itu null", () => {
    const ms = [m("a", 100), m("b", 180)];
    expect(markerNear(ms, 150, 40)?.id).toBe("b");
    expect(markerNear(ms, 150, 10)).toBeNull();
    expect(markerNear([], 0)).toBeNull();
  });
  it("segments: penanda ke penanda berikutnya; terakhir sampai akhir klip; penanda di luar durasi diabaikan", () => {
    const s = segments([m("b", 3000, "dua"), m("a", 1000, "satu"), m("x", 99_999, "luar")], 6000);
    expect(s.map((x) => [x.fromMs, x.toMs, x.label])).toEqual([[1000, 3000, "satu"], [3000, 6000, "dua"]]);
    expect(segments([], 6000)).toEqual([]);
  });
  it("segmentAt: batas bawah inklusif, batas atas eksklusif; akhir klip masuk segmen terakhir", () => {
    const s = segments([m("a", 0, "satu"), m("b", 1000, "dua")], 2000);
    expect(segmentAt(s, 0)?.label).toBe("satu");
    expect(segmentAt(s, 999)?.label).toBe("satu");
    expect(segmentAt(s, 1000)?.label).toBe("dua");
    expect(segmentAt(s, 2000)?.label).toBe("dua");
    expect(segmentAt(s, 2001)).toBeNull();
  });
  it("formatTimeMs mm:ss.mmm", () => {
    expect(formatTimeMs(0)).toBe("00:00.000");
    expect(formatTimeMs(65_432)).toBe("01:05.432");
    expect(formatTimeMs(-3)).toBe("00:00.000");
  });
  it("posToMs / msToPct konsisten dan aman untuk lebar 0", () => {
    expect(posToMs(50, 100, 6000)).toBe(3000);
    expect(posToMs(-20, 100, 6000)).toBe(0);
    expect(posToMs(500, 100, 6000)).toBe(6000);
    expect(posToMs(10, 0, 6000)).toBe(0);
    expect(msToPct(1500, 6000)).toBe(25);
    expect(msToPct(10, 0)).toBe(0);
  });
});
