import { describe, expect, it } from "vitest";
import { ResponsivenessMonitor } from "@/features/practice/responsiveness";
import { Series } from "@/features/practice/stats";

describe("Series", () => {
  it("kosong -> null", () => { const s = new Series(); expect(s.mean()).toBeNull(); expect(s.median()).toBeNull(); expect(s.p95()).toBeNull(); });
  it("mean/median/p95 (nearest-rank), genap & ganjil", () => {
    const s = new Series(); for (let i = 1; i <= 100; i++) s.add(i);
    expect(s.mean()).toBe(50.5); expect(s.median()).toBe(50.5); expect(s.p95()).toBe(95); expect(s.max()).toBe(100);
    const o = new Series(); [5, 1, 3].forEach((x) => o.add(x)); expect(o.median()).toBe(3);
  });
  it("membatasi memori (cap)", () => { const s = new Series(3); [1, 2, 3, 4].forEach((x) => s.add(x)); expect(s.n).toBe(3); expect(s.mean()).toBe(3); });
});

describe("ResponsivenessMonitor", () => {
  it("menghitung jarak antar rAF dan melaporkan gap maks (simulasi main thread terblokir)", () => {
    const q: ((t: number) => void)[] = [];
    const m = new ResponsivenessMonitor((cb) => { q.push(cb); return q.length; }, () => undefined);
    m.start();
    for (const t of [0, 16, 33, 1233, 1250]) q.shift()!(t); // satu gap 1200 ms
    const s = m.stop();
    expect(s.frames).toBe(4);
    expect(s.maxGapMs).toBe(1200);
    expect(s.p95GapMs).toBe(1200);
  });
  it("probe event-loop: lag = selisih aktual dengan jadwal (blokir main thread), terpisah dari rAF", () => {
    const timers: (() => void)[] = []; let now = 0;
    const m = new ResponsivenessMonitor(() => 1, () => undefined, (cb) => { timers.push(cb); return timers.length as unknown as ReturnType<typeof setTimeout>; }, () => undefined, () => now);
    m.start();
    for (const t of [10, 20, 30, 530, 540]) { now = t; timers.shift()!(); } // satu blokir ±490 ms
    const s = m.stop();
    expect(s.loopLag.n).toBe(4);
    expect(s.loopLag.maxMs).toBe(490);
    expect(s.loopLag.p95Ms).toBe(490);
  });
  it("stop idempoten", () => { const m = new ResponsivenessMonitor(() => 1, () => undefined); m.start(); m.stop(); expect(() => m.stop()).not.toThrow(); });
});
