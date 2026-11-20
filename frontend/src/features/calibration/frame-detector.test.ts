import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ReferenceFrameDetector } from "@/features/calibration/frame-detector";
import type { AdapterHandlers, AsyncLandmarkerAdapter } from "@/features/practice/async-adapter";
import { DEFAULT_INFERENCE_CONFIG } from "@/features/practice/config";
import type { LandmarkFrame } from "@/features/practice/landmarks";

const frame = (i: number): LandmarkFrame => ({ meta: { timestampMs: i, width: 10, height: 10, frameIndex: i }, poses: [], hands: [] });

class FakeAdapter implements AsyncLandmarkerAdapter {
  name = "fake"; h!: AdapterHandlers; submitted: number[] = []; disposed = false;
  setHandlers(h: AdapterHandlers) { this.h = h; }
  async init() { return { initMs: 1, startupMs: 0, delegate: null, library: "fake" }; }
  submit(bm: ImageBitmap, _t: number, _i: number, id: number) { this.submitted.push(id); bm.close(); }
  pause() {} resume() {}
  async dispose() { this.disposed = true; }
  reply(id: number) { this.h.onResult({ id, frame: frame(id), procMs: 1 }); }
}
const bitmap = () => ({ close: vi.fn(), width: 10, height: 10 }) as unknown as ImageBitmap;
const src = (t = 0) => ({ videoWidth: 10, videoHeight: 10, readyState: 4, currentTime: t });
const flush = () => new Promise((r) => setTimeout(r, 0));

describe("ReferenceFrameDetector", () => {
  beforeEach(() => vi.useRealTimers());
  afterEach(() => vi.useRealTimers());

  it("hanya satu frame in-flight; permintaan saat sibuk dijalankan SEKALI setelahnya (tanpa antrean menumpuk)", async () => {
    const a = new FakeAdapter(), got: [number, number][] = [];
    const bms: ImageBitmap[] = [];
    const d = new ReferenceFrameDetector(a, (f, t) => got.push([f.meta.frameIndex, t]), undefined, async () => { const b = bitmap(); bms.push(b); return b; });
    const s = src(1.5);
    await d.detect(s, DEFAULT_INFERENCE_CONFIG);
    await d.detect(s, DEFAULT_INFERENCE_CONFIG); // sibuk
    await d.detect(s, DEFAULT_INFERENCE_CONFIG); // sibuk (digabung)
    expect(a.submitted).toEqual([1]);
    a.reply(1);
    await flush();
    expect(got[0]).toEqual([1, 1500]); // waktu video terekam untuk frame yang diminta
    expect(a.submitted).toEqual([1, 2]);
    a.reply(2); await flush();
    expect(a.submitted).toEqual([1, 2]); // tidak ada permintaan ketiga
    expect(d.busy).toBe(false);
  });
  it("tidak mengirim bila video belum siap", async () => {
    const a = new FakeAdapter();
    const d = new ReferenceFrameDetector(a, () => undefined, undefined, async () => bitmap());
    await d.detect({ ...src(), readyState: 1 }, DEFAULT_INFERENCE_CONFIG);
    expect(a.submitted).toEqual([]);
  });
  it("bitmap ditutup bila detector di-dispose saat bitmap dibuat (tanpa kebocoran) dan adapter dilepas", async () => {
    const a = new FakeAdapter();
    let release!: (b: ImageBitmap) => void;
    const bm = bitmap();
    const d = new ReferenceFrameDetector(a, () => undefined, undefined, () => new Promise<ImageBitmap>((r) => { release = r; }));
    const p = d.detect(src(), DEFAULT_INFERENCE_CONFIG);
    await d.dispose();
    release(bm); await p;
    expect(bm.close).toHaveBeenCalled();
    expect(a.submitted).toEqual([]);
    expect(a.disposed).toBe(true);
  });
  it("watchdog: engine yang tak menjawab dilepas dan galatnya dilaporkan (bukan disembunyikan)", async () => {
    vi.useFakeTimers();
    const a = new FakeAdapter();
    const d = new ReferenceFrameDetector(a, () => undefined, undefined, async () => bitmap());
    await d.detect(src(), DEFAULT_INFERENCE_CONFIG);
    expect(d.busy).toBe(true);
    await vi.advanceTimersByTimeAsync(20_100);
    expect(d.busy).toBe(false);
    expect(d.lastError).toMatch(/tidak merespons/);
  });
  it("galat fatal engine melepas slot in-flight dan menyimpan pesan", async () => {
    const a = new FakeAdapter();
    const d = new ReferenceFrameDetector(a, () => undefined, undefined, async () => bitmap());
    await d.detect(src(), DEFAULT_INFERENCE_CONFIG);
    a.h.onError({ fatal: true, code: "WORKER_CRASH", message: "worker mati" });
    expect(d.busy).toBe(false);
    expect(d.lastError).toBe("worker mati");
  });
});
