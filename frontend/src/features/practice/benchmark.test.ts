import { describe, expect, it } from "vitest";
import { summarizeRuns, type RunResult } from "@/features/practice/benchmark";

const s = (median: number) => ({ n: 10, mean: median, median, p95: median * 1.2, max: median * 2 });
const run = (engine: RunResult["engine"], i: number, over: Partial<RunResult> = {}): RunResult => ({
  engine, run: i, initMs: 1000 + i, workerStartupMs: engine === "worker" ? 20 : null, durationMs: 5000, submitted: 40, processed: 40,
  droppedBackpressure: engine === "worker" ? 5 : null, droppedByWorker: engine === "worker" ? 0 : null,
  latency: s(engine === "worker" ? 90 : 1200), inference: s(80), posesDetectedFrames: 0, handsDetectedFrames: 0,
  responsiveness: { loopLag: { n: 100, p95Ms: engine === "worker" ? 2 : 1190, maxMs: engine === "worker" ? 8 : 1250 }, frames: 100, meanGapMs: 20, p95GapMs: engine === "worker" ? 25 : 1250, maxGapMs: engine === "worker" ? 60 : 1300, longTasks: { count: engine === "worker" ? 1 : 30, totalMs: 100, supported: true } },
  mainHeapMB: { before: 10, after: 11 }, error: null, ...over,
});

describe("summarizeRuns", () => {
  it("median antar-run per mesin", () => {
    const r = summarizeRuns([run("main-thread-baseline", 1), run("worker", 1), run("main-thread-baseline", 2), run("worker", 2), run("main-thread-baseline", 3), run("worker", 3)]);
    const w = r.find((x) => x.engine === "worker")!, m = r.find((x) => x.engine === "main-thread-baseline")!;
    expect(w.medianOfRuns.maxUiGapMs).toBe(60); expect(m.medianOfRuns.maxUiGapMs).toBe(1300);
    expect(w.medianOfRuns.maxLoopLagMs).toBe(8); expect(m.medianOfRuns.maxLoopLagMs).toBe(1250);
    expect(w.medianOfRuns.latencyMedianMs).toBe(90); expect(m.medianOfRuns.initMs).toBe(1002);
    expect(m.medianOfRuns.droppedBackpressure).toBeNull(); // baseline tidak dapat melewati frame
    expect(w.okRuns).toBe(3);
  });
  it("run yang error tidak ikut median namun tetap dihitung", () => {
    const r = summarizeRuns([run("worker", 1), run("worker", 2, { error: "gagal", processed: 0 }), run("worker", 3)]);
    expect(r[0]).toMatchObject({ runs: 3, okRuns: 2 });
  });
  it("tanpa run valid -> semua null (tidak ada angka dikarang)", () => {
    const r = summarizeRuns([run("worker", 1, { error: "x", processed: 0 })]);
    expect(r[0].medianOfRuns.latencyMedianMs).toBeNull();
  });
});
