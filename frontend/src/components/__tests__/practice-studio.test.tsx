// @vitest-environment jsdom
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PracticeStudio, type StudioLesson } from "@/components/PracticeStudio";
import type { AdapterHandlers, AsyncLandmarkerAdapter } from "@/features/practice/async-adapter";
import { syntheticFrame } from "@/features/practice/synthetic-pose";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, refresh: vi.fn() }) }));
const start = vi.fn(); const complete = vi.fn();
vi.mock("@/lib/practice-api", () => ({ startPracticeSession: (...a: unknown[]) => start(...a), completePracticeSession: (...a: unknown[]) => complete(...a) }));

const lesson: StudioLesson = { id: "L1", title: "[DEMO] Pelajaran", slug: "demo-1", courseSlug: "kur", courseTitle: "[DEMO] Kurikulum", isDemo: true,
  practiceLabel: "[DEMO] Sesi latihan contoh", verificationLabel: "[DEMO] Contoh teknis — belum diverifikasi mitra", objective: "Tujuan contoh", safetyNotes: null };

function stream() { const stop = vi.fn(); const t = { stop, label: "Kamera uji", getSettings: () => ({ deviceId: "d" }) }; return { s: { getTracks: () => [t], getVideoTracks: () => [t] } as unknown as MediaStream, stop }; }
function mockCamera(s: MediaStream) {
  const g = vi.fn().mockResolvedValue(s);
  Object.defineProperty(navigator, "mediaDevices", { value: { getUserMedia: g, enumerateDevices: vi.fn().mockResolvedValue([]) }, configurable: true });
  Object.defineProperty(window, "isSecureContext", { value: true, configurable: true });
  Object.defineProperty(HTMLMediaElement.prototype, "play", { value: () => Promise.resolve(), configurable: true });
  return g;
}

/** Adapter tiruan: mengembalikan hasil sintetis untuk setiap frame yang dikirim. */
function fakeAdapter(scenario: Parameters<typeof syntheticFrame>[0] = "full", over: Partial<AsyncLandmarkerAdapter> = {}) {
  let h!: AdapterHandlers;
  const a = {
    name: "fake", setHandlers: (x: AdapterHandlers) => { h = x; }, init: vi.fn().mockResolvedValue({ initMs: 5, startupMs: 1, delegate: "CPU", library: "@mediapipe/tasks-vision@1.2.3" }),
    submit: vi.fn((bm: ImageBitmap, t: number, i: number, id: number) => { bm.close(); setTimeout(() => h.onResult({ id, procMs: 1, frame: syntheticFrame(scenario, i, t) }), 0); }),
    pause: vi.fn(), resume: vi.fn(), dispose: vi.fn().mockResolvedValue(undefined), ...over,
  };
  return a as unknown as AsyncLandmarkerAdapter & { init: ReturnType<typeof vi.fn>; dispose: ReturnType<typeof vi.fn>; pause: ReturnType<typeof vi.fn>; resume: ReturnType<typeof vi.fn>; submit: ReturnType<typeof vi.fn> };
}

beforeEach(() => {
  push.mockReset(); start.mockReset(); complete.mockReset();
  // jsdom tidak punya createImageBitmap/ResizeObserver/canvas
  vi.stubGlobal("createImageBitmap", async () => ({ close: vi.fn(), width: 640, height: 480 }));
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} unobserve() {} });
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({ clearRect: vi.fn(), setTransform: vi.fn(), beginPath: vi.fn(), moveTo: vi.fn(), lineTo: vi.fn(), stroke: vi.fn(), fill: vi.fn(), arc: vi.fn(), setLineDash: vi.fn() })) as never;
  vi.stubGlobal("requestAnimationFrame", (cb: (t: number) => void) => setTimeout(() => cb(performance.now()), 20) as unknown as number);
  vi.stubGlobal("cancelAnimationFrame", (h: number) => clearTimeout(h));
  Object.defineProperty(HTMLVideoElement.prototype, "readyState", { get: () => 4, configurable: true });
  Object.defineProperty(HTMLVideoElement.prototype, "videoWidth", { get: () => 640, configurable: true });
  Object.defineProperty(HTMLVideoElement.prototype, "videoHeight", { get: () => 480, configurable: true });
});
afterEach(() => vi.unstubAllGlobals());

const consent = async () => { await userEvent.click(screen.getByRole("checkbox", { name: /setuju kamera dinyalakan/ })); await userEvent.click(screen.getByRole("button", { name: /nyalakan kamera/ })); };

describe("PracticeStudio", () => {
  it("intro: instruksi, privasi, keselamatan, label DEMO; kamera TIDAK diminta dan tombol terkunci sampai persetujuan", () => {
    const g = mockCamera(stream().s);
    render(<PracticeStudio lesson={lesson} createAdapter={() => fakeAdapter()} />);
    expect(screen.getByText(/tidak direkam, disimpan, atau dikirim/)).toBeTruthy();
    expect(screen.getByText(/tidak menilai gerakan/)).toBeTruthy();
    expect(screen.getByText(/latihan solo tingkat pemula/)).toBeTruthy();
    expect(screen.getByText(/sparring, teknik senjata, bantingan/)).toBeTruthy();
    expect(screen.getAllByText(/belum diverifikasi mitra/).length).toBeGreaterThan(0);
    expect((screen.getByRole("button", { name: /nyalakan kamera/ }) as HTMLButtonElement).disabled).toBe(true);
    expect(g).not.toHaveBeenCalled();
  });

  it("alur penuh: persetujuan -> kamera+engine siap -> mulai -> jeda -> lanjut -> hentikan -> simpan metadata -> ringkasan", async () => {
    const cam = stream(); const g = mockCamera(cam.s);
    const adapter = fakeAdapter("full");
    start.mockResolvedValue({ ok: true, data: { id: "S1" } });
    complete.mockResolvedValue({ ok: true, data: { id: "S1" } });
    render(<PracticeStudio lesson={lesson} createAdapter={() => adapter} />);
    await consent();
    expect(g).toHaveBeenCalledTimes(1);
    expect(g.mock.calls[0][0].audio).toBe(false); // tanpa audio
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("ready"));
    expect(adapter.init).toHaveBeenCalledTimes(1);
    expect(start).not.toHaveBeenCalled(); // pratinjau belum merekam sesi apa pun

    await userEvent.click(screen.getByRole("button", { name: /Mulai latihan/ }));
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("running"));
    expect(start).toHaveBeenCalledWith("L1", expect.stringContaining("@mediapipe/tasks-vision@1.2.3"));
    expect(screen.getByTestId("session-indicator").textContent).toContain("Sesi aktif");

    await userEvent.click(screen.getByRole("button", { name: /Jeda/ }));
    expect(screen.getByTestId("studio").getAttribute("data-state")).toBe("paused");
    expect(adapter.pause).toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: /Lanjutkan/ }));
    expect(adapter.resume).toHaveBeenCalled();

    await userEvent.click(screen.getByRole("button", { name: /Hentikan latihan/ }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/app/practice/sessions/S1"));
    const [id, body] = complete.mock.calls[0];
    expect(id).toBe("S1");
    expect(body.status).toBe("completed");
    expect(Object.keys(body).sort()).toEqual(["active_duration_ms", "error_code", "paused_duration_ms", "quality_summary", "status"]);
    expect(JSON.stringify(body)).not.toMatch(/"landmarks?"|"x"\s*:|"visibility"\s*:/); // hanya agregat
    expect(body.quality_summary.engine).toBe("worker");
    // kamera + worker dihentikan saat sesi berakhir
    expect(cam.stop).toHaveBeenCalled();
    expect(adapter.dispose).toHaveBeenCalled();
  });

  it("status deteksi mengikuti kualitas input: skenario sebagian tubuh -> panduan 'Pastikan kamera tidak terhalang'", async () => {
    mockCamera(stream().s);
    render(<PracticeStudio lesson={lesson} createAdapter={() => fakeAdapter("partial")} />);
    await consent();
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("ready"));
    start.mockResolvedValue({ ok: true, data: { id: "S2" } });
    await userEvent.click(screen.getByRole("button", { name: /Mulai latihan/ }));
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-state")).toBe("partial_detection"), { timeout: 5000 });
    expect(screen.getByTestId("guidance-title").textContent).toBe("Pastikan kamera tidak terhalang");
    expect(screen.getByTestId("state-chip").textContent).toBe("Sebagian tubuh terdeteksi");
  });

  it("tidak ada teks penilaian gerakan di studio (skor/benar/salah/akurasi/repetisi)", async () => {
    mockCamera(stream().s);
    const { container } = render(<PracticeStudio lesson={lesson} createAdapter={() => fakeAdapter("full")} />);
    await consent();
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("ready"));
    expect(container.textContent).not.toMatch(/\b(skor|benar|salah|akurasi|repetisi|rep|kemiripan)\b/i);
  });

  it("kamera ditolak -> galat jelas, tanpa sesi di server, tombol coba lagi", async () => {
    const g = vi.fn().mockRejectedValue(Object.assign(new Error("x"), { name: "NotAllowedError" }));
    Object.defineProperty(navigator, "mediaDevices", { value: { getUserMedia: g, enumerateDevices: vi.fn().mockResolvedValue([]) }, configurable: true });
    Object.defineProperty(window, "isSecureContext", { value: true, configurable: true });
    render(<PracticeStudio lesson={lesson} createAdapter={() => fakeAdapter()} />);
    await consent();
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Izin kamera ditolak");
    expect(within(alert).getByRole("button", { name: "Coba lagi" })).toBeTruthy();
    expect(start).not.toHaveBeenCalled();
  });

  it("engine gagal inisialisasi -> galat, kamera dilepas, worker di-dispose, tanpa fallback", async () => {
    const cam = stream(); mockCamera(cam.s);
    const adapter = fakeAdapter("full", { init: vi.fn().mockRejectedValue(new Error("model tidak dapat dimuat")) });
    render(<PracticeStudio lesson={lesson} createAdapter={() => adapter} />);
    await consent();
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("model tidak dapat dimuat");
    expect(adapter.dispose).toHaveBeenCalled();
    expect(cam.stop).toHaveBeenCalled();
    expect(adapter.submit).not.toHaveBeenCalled();
  });

  it("server menolak memulai sesi (mis. belum terdaftar) -> pesan galat, sesi tidak berjalan", async () => {
    mockCamera(stream().s);
    start.mockResolvedValue({ ok: false, error: "Daftar ke kurikulum ini terlebih dahulu untuk berlatih.", code: "NOT_ENROLLED", status: 403 });
    render(<PracticeStudio lesson={lesson} createAdapter={() => fakeAdapter()} />);
    await consent();
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("ready"));
    await userEvent.click(screen.getByRole("button", { name: /Mulai latihan/ }));
    expect((await screen.findAllByText(/Daftar ke kurikulum ini/)).length).toBeGreaterThan(0);
    expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("ready");
  });

  it("gagal menyimpan: kamera sudah dilepas, ada 'Coba simpan lagi' yang memakai data yang sama", async () => {
    const cam = stream(); mockCamera(cam.s);
    start.mockResolvedValue({ ok: true, data: { id: "S3" } });
    complete.mockResolvedValueOnce({ ok: false, error: "Jaringan putus", code: "NETWORK_ERROR", status: 0 }).mockResolvedValueOnce({ ok: true, data: { id: "S3" } });
    render(<PracticeStudio lesson={lesson} createAdapter={() => fakeAdapter("full")} />);
    await consent();
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("ready"));
    await userEvent.click(screen.getByRole("button", { name: /Mulai latihan/ }));
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("running"));
    await userEvent.click(screen.getByRole("button", { name: /Hentikan latihan/ }));
    await userEvent.click(await screen.findByRole("button", { name: "Coba simpan lagi" }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/app/practice/sessions/S3"));
    expect(complete).toHaveBeenCalledTimes(2);
    expect(complete.mock.calls[1][1]).toEqual(complete.mock.calls[0][1]);
    expect(cam.stop).toHaveBeenCalled();
  });

  it("keluar halaman (unmount) saat sesi berjalan: sesi ditandai abandoned (keepalive tidak diperlukan) dan resource dilepas", async () => {
    const cam = stream(); mockCamera(cam.s);
    const adapter = fakeAdapter("full");
    start.mockResolvedValue({ ok: true, data: { id: "S4" } });
    complete.mockResolvedValue({ ok: true, data: { id: "S4" } });
    const { unmount } = render(<PracticeStudio lesson={lesson} createAdapter={() => adapter} />);
    await consent();
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("ready"));
    await userEvent.click(screen.getByRole("button", { name: /Mulai latihan/ }));
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("running"));
    unmount();
    await waitFor(() => expect(complete).toHaveBeenCalled());
    expect(complete.mock.calls[0][1].status).toBe("abandoned");
    await waitFor(() => expect(adapter.dispose).toHaveBeenCalled());
    expect(cam.stop).toHaveBeenCalled();
  });

  it("pagehide saat sesi berjalan memakai keepalive", async () => {
    mockCamera(stream().s);
    start.mockResolvedValue({ ok: true, data: { id: "S5" } });
    complete.mockResolvedValue({ ok: true, data: { id: "S5" } });
    render(<PracticeStudio lesson={lesson} createAdapter={() => fakeAdapter("full")} />);
    await consent();
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("ready"));
    await userEvent.click(screen.getByRole("button", { name: /Mulai latihan/ }));
    await waitFor(() => expect(screen.getByTestId("studio").getAttribute("data-phase")).toBe("running"));
    window.dispatchEvent(new Event("pagehide"));
    await waitFor(() => expect(complete).toHaveBeenCalled());
    expect(complete.mock.calls[0][2]).toEqual({ keepalive: true });
  });
});
