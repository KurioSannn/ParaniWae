import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_INFERENCE_CONFIG, MEDIAPIPE_PATHS } from "@/features/practice/config";
import { syntheticFrame } from "@/features/practice/fixtures";
import { WorkerLandmarkerAdapter } from "@/features/practice/worker-adapter";
import type { FromWorker, ToWorker, WorkerLike } from "@/features/practice/worker/protocol";

class FakeWorker implements WorkerLike {
  onmessage: WorkerLike["onmessage"] = null; onerror: WorkerLike["onerror"] = null; onmessageerror: WorkerLike["onmessageerror"] = null;
  sent: { msg: ToWorker; transfer?: Transferable[] }[] = []; terminated = 0;
  postMessage(msg: ToWorker, transfer?: Transferable[]) { this.sent.push({ msg, transfer }); }
  terminate() { this.terminated++; }
  emit(m: FromWorker) { this.onmessage?.({ data: m } as MessageEvent<FromWorker>); }
}
const bitmap = () => ({ close: vi.fn(), width: 1, height: 1 }) as unknown as ImageBitmap & { close: ReturnType<typeof vi.fn> };

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("WorkerLandmarkerAdapter", () => {
  it("init mengirim konfigurasi same-origin & versi; resolve saat 'ready' dengan metrik startup", async () => {
    const w = new FakeWorker(); let t = 0;
    const a = new WorkerLandmarkerAdapter(DEFAULT_INFERENCE_CONFIG, () => w, () => t);
    const p = a.init();
    const init = w.sent[0].msg as Extract<ToWorker, { type: "init" }>;
    expect(init.config).toMatchObject({ wasmBase: MEDIAPIPE_PATHS.wasm, poseModel: MEDIAPIPE_PATHS.pose, handModel: MEDIAPIPE_PATHS.hand });
    for (const u of [init.config.wasmBase, init.config.poseModel, init.config.handModel]) expect(u.startsWith("/")).toBe(true); // same-origin
    t = 40; w.emit({ type: "status", state: "loading" });
    t = 900; w.emit({ type: "ready", initMs: 850, delegate: "CPU", library: "lib" });
    await expect(p).resolves.toMatchObject({ initMs: 850, startupMs: 40, delegate: "CPU" });
  });
  it("init gagal (error fatal dari worker) -> reject, handler dipanggil, worker dihentikan", async () => {
    const w = new FakeWorker(); const onError = vi.fn();
    const a = new WorkerLandmarkerAdapter(DEFAULT_INFERENCE_CONFIG, () => w);
    a.setHandlers({ onResult: vi.fn(), onDropped: vi.fn(), onError });
    const p = a.init();
    w.emit({ type: "error", fatal: true, code: "INIT_FAILED", message: "model tidak ada" });
    await expect(p).rejects.toThrow("model tidak ada");
    expect(onError).toHaveBeenCalledWith({ fatal: true, code: "INIT_FAILED", message: "model tidak ada" });
    expect(w.terminated).toBe(1);
  });
  it("timeout inisialisasi -> INIT_TIMEOUT dan worker dihentikan", async () => {
    const w = new FakeWorker(); const onError = vi.fn();
    const a = new WorkerLandmarkerAdapter({ ...DEFAULT_INFERENCE_CONFIG, initTimeoutMs: 1000 }, () => w);
    a.setHandlers({ onResult: vi.fn(), onDropped: vi.fn(), onError });
    const p = a.init(); const caught = p.catch((e) => e);
    await vi.advanceTimersByTimeAsync(1001);
    expect((await caught as Error).message).toMatch(/batas waktu/);
    expect(onError.mock.calls[0][0].code).toBe("INIT_TIMEOUT");
    expect(w.terminated).toBe(1);
  });
  it("worker crash saat berjalan (onerror) -> error fatal WORKER_CRASH ke UI, tanpa fallback sinkron", async () => {
    const w = new FakeWorker(); const onError = vi.fn();
    const a = new WorkerLandmarkerAdapter(DEFAULT_INFERENCE_CONFIG, () => w);
    a.setHandlers({ onResult: vi.fn(), onDropped: vi.fn(), onError });
    const p = a.init(); w.emit({ type: "ready", initMs: 1, delegate: null, library: "l" }); await p;
    w.onerror?.({ message: "boom" } as ErrorEvent);
    expect(onError).toHaveBeenCalledWith({ fatal: true, code: "WORKER_CRASH", message: "boom" });
    expect(w.terminated).toBe(1);
  });
  it("submit mentransfer ImageBitmap (zero-copy); frame hasil & drop diteruskan ke handler", async () => {
    const w = new FakeWorker(); const onResult = vi.fn(); const onDropped = vi.fn();
    const a = new WorkerLandmarkerAdapter(DEFAULT_INFERENCE_CONFIG, () => w);
    a.setHandlers({ onResult, onDropped, onError: vi.fn() });
    const p = a.init(); w.emit({ type: "ready", initMs: 1, delegate: null, library: "l" }); await p;
    const bm = bitmap(); a.submit(bm, 10, 3, 3);
    const last = w.sent.at(-1)!;
    expect(last.transfer).toEqual([bm]);
    expect(bm.close).not.toHaveBeenCalled(); // kepemilikan pindah ke worker
    w.emit({ type: "result", id: 3, frame: syntheticFrame(), procMs: 7 });
    w.emit({ type: "dropped", id: 4, reason: "stale" });
    expect(onResult).toHaveBeenCalledWith(expect.objectContaining({ id: 3, procMs: 7 }));
    expect(onDropped).toHaveBeenCalledWith({ id: 4, reason: "stale" });
  });
  it("dispose: kirim 'dispose', lepas handler, terminate, idempoten; submit setelah dispose menutup bitmap", async () => {
    const w = new FakeWorker();
    const a = new WorkerLandmarkerAdapter(DEFAULT_INFERENCE_CONFIG, () => w);
    const p = a.init(); w.emit({ type: "ready", initMs: 1, delegate: null, library: "l" }); await p;
    await a.dispose(); await a.dispose();
    expect(w.sent.some((s) => s.msg.type === "dispose")).toBe(true);
    expect(w.terminated).toBe(1);
    expect(w.onmessage).toBeNull(); expect(w.onerror).toBeNull();
    const bm = bitmap(); a.submit(bm, 1, 1, 1);
    expect(bm.close).toHaveBeenCalledTimes(1);
  });
  it("tidak dapat di-init dua kali (model hanya sekali per sesi)", async () => {
    const w = new FakeWorker();
    const a = new WorkerLandmarkerAdapter(DEFAULT_INFERENCE_CONFIG, () => w);
    const p = a.init(); w.emit({ type: "ready", initMs: 1, delegate: null, library: "l" }); await p;
    await expect(a.init()).rejects.toThrow();
  });
  it("pause/resume diteruskan sebagai perintah", async () => {
    const w = new FakeWorker();
    const a = new WorkerLandmarkerAdapter(DEFAULT_INFERENCE_CONFIG, () => w);
    const p = a.init(); w.emit({ type: "ready", initMs: 1, delegate: null, library: "l" }); await p;
    a.pause(); a.resume();
    expect(w.sent.slice(-2).map((s) => s.msg.type)).toEqual(["pause", "resume"]);
  });
});
