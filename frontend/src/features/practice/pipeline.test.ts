import { describe, expect, it, vi } from "vitest";
import type { AdapterHandlers, AsyncLandmarkerAdapter } from "@/features/practice/async-adapter";
import { DEFAULT_INFERENCE_CONFIG } from "@/features/practice/config";
import { syntheticFrame } from "@/features/practice/fixtures";
import { FramePump } from "@/features/practice/pipeline";

class FakeAdapter implements AsyncLandmarkerAdapter {
  name = "fake"; h!: AdapterHandlers; submitted: number[] = []; paused = 0; resumed = 0;
  setHandlers(h: AdapterHandlers) { this.h = h; }
  async init() { return { initMs: 1, startupMs: 1, delegate: "CPU", library: "x" }; }
  submit(bm: ImageBitmap, _t: number, _i: number, id: number) { this.submitted.push(id); bm.close(); }
  pause() { this.paused++; } resume() { this.resumed++; }
  async dispose() {}
}
const bitmap = () => ({ close: vi.fn(), width: 640, height: 480 }) as unknown as ImageBitmap;

function setup(over: Partial<typeof DEFAULT_INFERENCE_CONFIG> = {}) {
  const adapter = new FakeAdapter();
  let clock = 0; const cbs: ((t: number) => void)[] = [];
  const bitmaps: ImageBitmap[] = [];
  const pump = new FramePump({
    adapter, source: { videoWidth: 640, videoHeight: 480, readyState: 4 }, config: { ...DEFAULT_INFERENCE_CONFIG, ...over },
    createBitmap: async () => { const b = bitmap(); bitmaps.push(b); return b; },
    now: () => clock, schedule: (cb) => { cbs.push(cb); return cbs.length; }, cancel: vi.fn(),
  });
  const tick = async (dt: number) => { clock += dt; const cb = cbs.pop(); cb?.(clock); await Promise.resolve(); await Promise.resolve(); };
  return { adapter, pump, tick, bitmaps, setClock: (t: number) => { clock = t; } };
}

describe("FramePump backpressure", () => {
  it("tidak mengirim frame baru selama engine penuh (maxInFlight=1) dan menghitung drop", async () => {
    const { adapter, pump, tick } = setup();
    pump.start();
    await tick(100); // kirim #1
    await tick(100); await tick(100); await tick(100); // engine masih sibuk
    expect(adapter.submitted).toEqual([1]);
    expect(pump.stats.droppedBackpressure).toBe(3);
    expect(pump.inFlightCount).toBe(1);
    adapter.h.onResult({ id: 1, frame: syntheticFrame(), procMs: 5 });
    await tick(100);
    expect(adapter.submitted).toEqual([1, 2]);
    expect(pump.stats.processed).toBe(1);
  });
  it("pembatasan frekuensi (minIntervalMs) bukan drop", async () => {
    const { adapter, pump, tick } = setup({ minIntervalMs: 100 });
    pump.start();
    await tick(100);
    adapter.h.onResult({ id: 1, frame: syntheticFrame(), procMs: 1 });
    await tick(30); await tick(30); // < 100ms sejak submit terakhir
    expect(adapter.submitted).toEqual([1]);
    expect(pump.stats.droppedBackpressure).toBe(0);
    await tick(60);
    expect(adapter.submitted).toEqual([1, 2]);
  });
  it("frame dibuang worker dihitung terpisah dan melepas slot", async () => {
    const { adapter, pump, tick } = setup();
    pump.start();
    await tick(100);
    adapter.h.onDropped({ id: 1, reason: "stale" });
    expect(pump.stats.droppedByWorker).toBe(1);
    expect(pump.inFlightCount).toBe(0);
  });
  it("frame hilang (tidak pernah kembali) dilepas oleh watchdog", async () => {
    const { adapter, pump, tick } = setup();
    pump.start();
    await tick(100);
    await tick(6000);
    expect(pump.stats.lost).toBe(1);
    expect(adapter.submitted.length).toBeGreaterThanOrEqual(1);
  });
  it("mencatat latensi, waktu proses, dan deteksi pose/tangan secara terpisah", async () => {
    const { adapter, pump, tick, setClock } = setup();
    pump.start();
    await tick(100);
    setClock(150);
    adapter.h.onResult({ id: 1, frame: syntheticFrame({ poses: [] }), procMs: 10 });
    expect(pump.latency.mean()).toBe(50);
    expect(pump.proc.mean()).toBe(10);
    expect(pump.stats.posesDetectedFrames).toBe(0);
  });
});

describe("FramePump lifecycle & memori", () => {
  it("tidak mengirim saat pause dan meneruskan pause/resume ke adapter", async () => {
    const { adapter, pump, tick } = setup();
    pump.start(); pump.setPaused(true);
    await tick(100);
    expect(adapter.submitted).toEqual([]);
    pump.setPaused(false);
    expect(adapter.paused).toBe(1); expect(adapter.resumed).toBe(1);
    await tick(100);
    expect(adapter.submitted).toEqual([1]);
  });
  it("ImageBitmap yang selesai dibuat setelah stop() ditutup (tanpa bocor) dan slot dilepas", async () => {
    const { adapter, pump, tick, bitmaps } = setup();
    pump.start();
    const p = tick(100);
    pump.stop(); // stop saat createBitmap belum selesai
    await p; await Promise.resolve();
    expect(adapter.submitted).toEqual([]);
    expect(bitmaps.every((b) => (b.close as ReturnType<typeof vi.fn>).mock.calls.length === 1)).toBe(true);
    expect(pump.inFlightCount).toBe(0);
  });
  it("stop idempoten dan tidak menjadwalkan ulang", async () => {
    const { pump } = setup();
    pump.start(); pump.stop(); pump.stop();
    expect(pump.isRunning).toBe(false);
  });
  it("error fatal menghentikan pompa dan diteruskan ke UI", () => {
    const adapter = new FakeAdapter(); const onFatal = vi.fn();
    const pump = new FramePump({ adapter, source: { videoWidth: 1, videoHeight: 1, readyState: 4 }, config: DEFAULT_INFERENCE_CONFIG,
      createBitmap: async () => bitmap(), now: () => 0, schedule: () => 1, cancel: vi.fn(), onFatal });
    pump.start();
    adapter.h.onError({ fatal: true, code: "WORKER_CRASH", message: "x" });
    expect(onFatal).toHaveBeenCalledWith({ code: "WORKER_CRASH", message: "x" });
    expect(pump.isRunning).toBe(false);
  });
  it("tidak mengirim bila video belum siap (readyState<2)", async () => {
    const adapter = new FakeAdapter(); let c = 0; const cbs: ((t: number) => void)[] = [];
    const pump = new FramePump({ adapter, source: { videoWidth: 0, videoHeight: 0, readyState: 0 }, config: DEFAULT_INFERENCE_CONFIG,
      createBitmap: async () => bitmap(), now: () => c, schedule: (cb) => { cbs.push(cb); return 1; }, cancel: vi.fn() });
    pump.start(); c = 100; cbs.pop()!(100); await Promise.resolve();
    expect(adapter.submitted).toEqual([]);
  });
});
