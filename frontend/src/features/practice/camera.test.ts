import { describe, expect, it, vi } from "vitest";
import {
  CameraController, cameraReducer, classifyCameraError, INITIAL_CAMERA_STATE, isStarted,
  type CameraState, type MediaDevicesLike,
} from "@/features/practice/camera";

function fakeStream() {
  const stop = vi.fn();
  const track = { stop, label: "Kamera uji", getSettings: () => ({ deviceId: "dev1" }) };
  return { stream: { getTracks: () => [track, track], getVideoTracks: () => [track] } as unknown as MediaStream, stop };
}
const devicesWith = (impl: MediaDevicesLike["getUserMedia"]): MediaDevicesLike => ({
  getUserMedia: impl,
  enumerateDevices: async () => [{ kind: "videoinput", deviceId: "a", label: "A" }, { kind: "audioinput", deviceId: "m", label: "M" }] as MediaDeviceInfo[],
});

describe("cameraReducer", () => {
  it("transisi dasar", () => {
    let s: CameraState = INITIAL_CAMERA_STATE;
    s = cameraReducer(s, { type: "request" });
    expect(s.status).toBe("requesting");
    s = cameraReducer(s, { type: "granted", deviceId: "d", label: "l" });
    expect(s).toMatchObject({ status: "active", deviceId: "d" });
    s = cameraReducer(s, { type: "stop" });
    expect(s.status).toBe("stopped");
    expect(cameraReducer(INITIAL_CAMERA_STATE, { type: "stop" }).status).toBe("idle");
    expect(cameraReducer(s, { type: "denied" }).status).toBe("denied");
  });
});

describe("classifyCameraError", () => {
  it.each([
    ["NotAllowedError", "denied"], ["SecurityError", "denied"], ["NotFoundError", "unavailable"],
    ["OverconstrainedError", "unavailable"], ["NotReadableError", "error"], ["AbortError", "error"],
  ])("%s -> %s", (name, type) => expect(classifyCameraError({ name }).type).toBe(type));
});

describe("CameraController", () => {
  it("start -> stream aktif; stop menghentikan semua track dan idempoten", async () => {
    const { stream, stop } = fakeStream();
    const c = new CameraController(devicesWith(async () => stream), true);
    const r = await c.start();
    expect(isStarted(r) && r.deviceId).toBe("dev1");
    expect(c.active).toBe(true);
    c.stop(); c.stop();
    expect(stop).toHaveBeenCalledTimes(2); // 2 track, hanya sekali berhenti
    expect(c.active).toBe(false);
  });
  it("start ulang menghentikan stream sebelumnya (tanpa stream ganda)", async () => {
    const a = fakeStream(), b = fakeStream();
    const queue = [a.stream, b.stream];
    const c = new CameraController(devicesWith(async () => queue.shift()!), true);
    await c.start();
    await c.start();
    expect(a.stop).toHaveBeenCalled();
    expect(b.stop).not.toHaveBeenCalled();
  });
  it("tidak pernah meminta audio", async () => {
    const spy = vi.fn().mockResolvedValue(fakeStream().stream);
    await new CameraController(devicesWith(spy), true).start();
    expect(spy.mock.calls[0][0].audio).toBe(false);
  });
  it("izin ditolak -> aksi denied dan tidak ada stream", async () => {
    const c = new CameraController(devicesWith(async () => { throw Object.assign(new Error("x"), { name: "NotAllowedError" }); }), true);
    expect(await c.start()).toEqual({ type: "denied" });
    expect(c.active).toBe(false);
  });
  it("konteks tidak aman / API tidak ada -> unavailable", async () => {
    expect(await new CameraController(devicesWith(async () => fakeStream().stream), false).start()).toEqual({ type: "unavailable", reason: "INSECURE_CONTEXT" });
    expect(await new CameraController(undefined, true).start()).toEqual({ type: "unavailable", reason: "NO_API" });
  });
  it("daftar perangkat hanya videoinput", async () => {
    const list = await new CameraController(devicesWith(async () => fakeStream().stream), true).listVideoDevices();
    expect(list.map((d) => d.deviceId)).toEqual(["a"]);
  });
});
