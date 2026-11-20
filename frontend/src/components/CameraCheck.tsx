"use client";
import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { Camera, CameraOff, ShieldCheck } from "lucide-react";
import {
  CAMERA_MESSAGES, CameraController, cameraReducer, INITIAL_CAMERA_STATE, isStarted,
} from "@/features/practice/camera";
import type { AsyncLandmarkerAdapter, InitInfo } from "@/features/practice/async-adapter";
import { DEFAULT_INFERENCE_CONFIG, type InferenceConfig } from "@/features/practice/config";
import { POSE_CONNECTIONS } from "@/features/practice/landmarks";
import { nowMs } from "@/features/practice/metrics";
import { createFrameBitmap, FramePump, makeFrameScheduler } from "@/features/practice/pipeline";
import { assessFrameQuality, guidanceFor, QualityWindow, type FrameQuality } from "@/features/practice/quality-gate";
import { ResponsivenessMonitor } from "@/features/practice/responsiveness";
import { WorkerLandmarkerAdapter } from "@/features/practice/worker-adapter";
import { Sparkline } from "@/components/Sparkline";

type Detect = "off" | "loading" | "on" | "error";
type WorkerState = "loading" | "ready" | "paused" | "disposed" | null;

interface Snapshot {
  info: InitInfo | null;
  workerState: WorkerState;
  submitted: number; processed: number; droppedBackpressure: number; droppedByWorker: number; lost: number; errors: number;
  latency: { n: number; mean: number | null; median: number | null; p95: number | null; recent: number[] };
  procMean: number | null;
  posesFrames: number; handsFrames: number;
  gap: { max: number | null; p95: number | null; longTasks: number; longTaskSupported: boolean; lagMax: number | null; lagP95: number | null };
  video: { w: number | null; h: number | null };
}

const fmt = (n: number | null, d = 1) => (n === null ? "—" : n.toFixed(d));

export function CameraCheck({ createAdapter, config }: { createAdapter?: (cfg: InferenceConfig) => AsyncLandmarkerAdapter; config?: Partial<InferenceConfig> }) {
  const cfg: InferenceConfig = { ...DEFAULT_INFERENCE_CONFIG, ...config };
  const cfgRef = useRef(cfg);
  const [state, dispatch] = useReducer(cameraReducer, INITIAL_CAMERA_STATE);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [deviceId, setDeviceId] = useState("");
  const [detect, setDetect] = useState<Detect>("off");
  const [detectError, setDetectError] = useState<string | null>(null);
  const [quality, setQuality] = useState<{ q: FrameQuality; stable: boolean } | null>(null);
  const [snap, setSnap] = useState<Snapshot | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctrl = useRef<CameraController | null>(null);
  const adapter = useRef<AsyncLandmarkerAdapter | null>(null);
  const pump = useRef<FramePump | null>(null);
  const monitor = useRef<ResponsivenessMonitor | null>(null);
  const win = useRef(new QualityWindow(15));
  const infoRef = useRef<InitInfo | null>(null);
  const workerStateRef = useRef<WorkerState>(null);
  const generation = useRef(0); // membatalkan init yang tertunda bila pengguna berhenti/keluar
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const getCtrl = () => (ctrl.current ??= new CameraController());

  const stopDetection = useCallback(async () => {
    generation.current += 1;
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    pump.current?.stop();
    pump.current = null;
    monitor.current?.stop();
    monitor.current = null;
    const a = adapter.current;
    adapter.current = null;
    await a?.dispose(); // menghentikan worker + melepas handler
    infoRef.current = null;
    workerStateRef.current = null;
    win.current.reset();
    canvasRef.current?.getContext("2d")?.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    setSnap(null); setQuality(null); setDetect("off");
  }, []);

  const stopAll = useCallback(async () => {
    await stopDetection();
    getCtrl().stop();
    if (videoRef.current) videoRef.current.srcObject = null;
  }, [stopDetection]);

  // Hentikan worker + kamera saat keluar halaman / tab ditutup / komponen dilepas.
  useEffect(() => {
    const onHide = () => { void stopAll(); dispatch({ type: "stop" }); };
    // Jeda inferensi (bukan kamera) saat tab tidak terlihat; lanjutkan saat terlihat.
    const onVisibility = () => { if (cfgRef.current.pauseWhenHidden) pump.current?.setPaused(document.hidden); };
    window.addEventListener("pagehide", onHide);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener("pagehide", onHide);
      document.removeEventListener("visibilitychange", onVisibility);
      void stopAll();
    };
  }, [stopAll]);

  async function start() {
    dispatch({ type: "request" });
    const r = await getCtrl().start(deviceId || undefined);
    if (!isStarted(r)) return dispatch(r);
    if (videoRef.current) { videoRef.current.srcObject = r.stream; await videoRef.current.play().catch(() => undefined); }
    dispatch({ type: "granted", deviceId: r.deviceId, label: r.label });
    setDevices(await getCtrl().listVideoDevices());
  }

  function stop() { void stopAll(); dispatch({ type: "stop" }); }

  function draw(lm: { x: number; y: number }[], w: number, h: number) {
    const c = canvasRef.current;
    const ctx = c?.getContext("2d");
    if (!c || !ctx) return;
    c.width = w; c.height = h;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = "#B9854F"; ctx.fillStyle = "#FCFBF7"; ctx.lineWidth = 3;
    for (const [a, b] of POSE_CONNECTIONS) {
      if (!lm[a] || !lm[b]) continue;
      ctx.beginPath(); ctx.moveTo(lm[a].x * w, lm[a].y * h); ctx.lineTo(lm[b].x * w, lm[b].y * h); ctx.stroke();
    }
    for (const p of lm) { ctx.beginPath(); ctx.arc(p.x * w, p.y * h, 4, 0, Math.PI * 2); ctx.fill(); }
  }

  async function toggleDetect() {
    if (detect === "on" || detect === "loading") return stopDetection();
    const video = videoRef.current;
    if (!video) return;
    const gen = ++generation.current;
    setDetect("loading"); setDetectError(null);
    const a = createAdapter ? createAdapter(cfg) : new WorkerLandmarkerAdapter(cfg);
    adapter.current = a;
    const sched = makeFrameScheduler(video);
    const p = new FramePump({
      adapter: a, source: video, config: cfg, createBitmap: createFrameBitmap, now: nowMs,
      schedule: sched.schedule, cancel: sched.cancel,
      onResult: ({ frame }) => {
        const q = assessFrameQuality(frame);
        win.current.push(q);
        setQuality({ q, stable: win.current.stable });
        draw(frame.poses[0]?.landmarks ?? [], frame.meta.width, frame.meta.height);
      },
      onState: (s) => { workerStateRef.current = s; },
      onNonFatalError: () => undefined,
      onFatal: ({ message }) => {
        // Worker gagal/crash: tampilkan error. TIDAK ada fallback sinkron di main thread.
        setDetectError(message);
        void stopDetection().then(() => { setDetectError(message); setDetect("error"); });
      },
    });
    pump.current = p;
    try {
      const info = await a.init();
      if (gen !== generation.current) { await a.dispose(); return; } // dibatalkan saat memuat
      infoRef.current = info;
      workerStateRef.current = "ready";
      const m = new ResponsivenessMonitor();
      m.start(); monitor.current = m;
      p.start();
      setDetect("on");
      timer.current = setInterval(() => {
        const g = m.summary();
        setSnap({
          info: infoRef.current, workerState: workerStateRef.current,
          ...p.stats,
          latency: { n: p.latency.n, mean: p.latency.mean(), median: p.latency.median(), p95: p.latency.p95(), recent: p.latency.last(60) },
          procMean: p.proc.mean(), posesFrames: p.stats.posesDetectedFrames, handsFrames: p.stats.handsDetectedFrames,
          gap: { max: g.maxGapMs, p95: g.p95GapMs, longTasks: g.longTasks.count, longTaskSupported: g.longTasks.supported, lagMax: g.loopLag.maxMs, lagP95: g.loopLag.p95Ms },
          video: { w: video.videoWidth || null, h: video.videoHeight || null },
        });
      }, 500);
    } catch (e) {
      if (gen !== generation.current) return;
      await stopDetection();
      setDetectError(e instanceof Error ? e.message : "Model gagal dimuat.");
      setDetect("error");
    }
  }

  const active = state.status === "active";
  const label = state.status === "active" ? state.label : null;
  const synthetic = !!label && /fake|virtual|synthetic/i.test(label);
  return (
    <div className="space-y-6">
      <section aria-labelledby="privasi" className="rounded-2xl border border-line-200 bg-paper-50 p-5">
        <h2 id="privasi" className="mb-2 flex items-center gap-2 font-semibold"><ShieldCheck aria-hidden className="h-5 w-5 text-forest-700" />Sebelum menyalakan kamera</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
          <li>Kamera hanya menyala setelah Anda menekan tombol di bawah, dan dapat dihentikan kapan saja.</li>
          <li>Gambar diproses <strong>di perangkat Anda</strong> (di thread latar peramban). Video dan frame <strong>tidak direkam, disimpan, atau dikirim</strong> ke server.</li>
          <li>Halaman ini hanya memeriksa apakah tubuh Anda terlihat cukup jelas. <strong>Ini bukan penilaian gerakan</strong> dan bukan pengganti instruktur.</li>
          <li>Tidak ada pengenalan wajah. Mikrofon tidak digunakan.</li>
          <li>Pastikan area di sekitar Anda aman dan hentikan bila merasa tidak nyaman.</li>
        </ul>
      </section>

      <div className="relative aspect-[4/3] max-w-2xl overflow-hidden rounded-2xl bg-ink-950">
        <video ref={videoRef} muted playsInline aria-label="Pratinjau kamera" className="h-full w-full -scale-x-100 object-cover" />
        <canvas ref={canvasRef} aria-hidden className="pointer-events-none absolute inset-0 h-full w-full -scale-x-100 object-cover" />
        {!active && <div className="absolute inset-0 flex items-center justify-center p-6 text-center text-paper-50"><CameraOff aria-hidden className="mr-2 h-6 w-6" />Kamera mati</div>}
      </div>

      <div role="status" aria-live="polite" className="max-w-2xl text-sm">
        {state.status === "requesting" && "Meminta izin kamera…"}
        {state.status === "denied" && <span className="text-clay-600">{CAMERA_MESSAGES.denied}</span>}
        {state.status === "unavailable" && <span className="text-clay-600">{CAMERA_MESSAGES[state.reason]}</span>}
        {state.status === "error" && <span className="text-clay-600">{state.message}</span>}
        {state.status === "stopped" && "Kamera dihentikan."}
        {active && !quality && detect === "off" && "Kamera aktif. Deteksi landmark belum dinyalakan."}
        {detect === "loading" && "Memuat model di thread latar… (halaman tetap dapat dipakai)"}
        {detect === "error" && <span className="text-clay-600" role="alert">Mesin landmark gagal: {detectError ?? "kesalahan tak dikenal"}. Kamera tetap dapat dipakai; coba nyalakan deteksi lagi atau muat ulang halaman. Tidak ada pemrosesan cadangan di thread utama.</span>}
        {quality && (
          <p>
            <strong>{quality.q.usable ? (quality.stable ? "Siap dianalisis" : "Menstabilkan…") : "Belum dapat dianalisis"}</strong>
            {" — "}{guidanceFor(quality.q)} <span className="text-slate-600">(cakupan landmark wajib: {Math.round(quality.q.requiredCoverage * 100)}%)</span>
          </p>
        )}
      </div>

      {snap && (
        <section aria-labelledby="metrik" data-testid="cam-metrics"
          data-engine="worker" data-worker-state={snap.workerState ?? ""}
          data-init-ms={snap.info?.initMs ?? ""} data-startup-ms={snap.info?.startupMs ?? ""} data-delegate={snap.info?.delegate ?? ""}
          data-submitted={snap.submitted} data-frames={snap.processed} data-dropped-bp={snap.droppedBackpressure} data-dropped-worker={snap.droppedByWorker}
          data-errors={snap.errors} data-latency-mean={snap.latency.mean ?? ""} data-latency-median={snap.latency.median ?? ""} data-latency-p95={snap.latency.p95 ?? ""}
          data-proc-mean={snap.procMean ?? ""} data-gap-max={snap.gap.max ?? ""} data-gap-p95={snap.gap.p95 ?? ""} data-lag-max={snap.gap.lagMax ?? ""} data-lag-p95={snap.gap.lagP95 ?? ""} data-long-tasks={snap.gap.longTasks}
          data-video={`${snap.video.w ?? ""}x${snap.video.h ?? ""}`} data-poses-frames={snap.posesFrames} data-hands-frames={snap.handsFrames}
          className="max-w-2xl space-y-2 rounded-xl border border-line-200 bg-paper-50 p-4 text-sm">
          <h2 id="metrik" className="font-semibold">Metrik teknis (pengujian di perangkat ini, sesi ini)</h2>
          <p className="rounded-lg bg-parchment-100 p-2 text-xs text-slate-600">
            {synthetic ? "Sumber kamera SINTETIS (" + label + "): hanya memvalidasi jalur komputasi, bukan deteksi manusia. " : "Sumber: " + (label ?? "kamera") + " — kehadiran manusia di frame tidak diverifikasi otomatis. "}
            Angka berikut hanya berlaku untuk perangkat, peramban, dan kondisi saat ini; bukan FPS produk dan bukan ukuran akurasi.
          </p>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1">
            <dt className="text-slate-600">Mesin / status</dt><dd>Web Worker · {snap.workerState ?? "—"}{snap.workerState === "paused" ? " (dijeda)" : ""}</dd>
            <dt className="text-slate-600">Inisialisasi model</dt><dd>{snap.info ? `${Math.round(snap.info.initMs)} ms` : "—"}</dd>
            <dt className="text-slate-600">Startup worker</dt><dd>{snap.info ? `${Math.round(snap.info.startupMs)} ms` : "—"}</dd>
            <dt className="text-slate-600">Delegasi</dt><dd>{snap.info?.delegate ?? "—"}</dd>
            <dt className="text-slate-600">Resolusi video</dt><dd>{snap.video.w ?? "—"}×{snap.video.h ?? "—"}{cfg.maxFrameWidth ? ` (diperkecil ke lebar ${cfg.maxFrameWidth})` : " (asli, tidak diperkecil)"}</dd>
            <dt className="text-slate-600">Frame diproses / dikirim</dt><dd>{snap.processed} / {snap.submitted}</dd>
            <dt className="text-slate-600">Frame video dilewati (engine sibuk)</dt><dd>{snap.droppedBackpressure}</dd>
            <dt className="text-slate-600">Dibuang worker / hilang</dt><dd>{snap.droppedByWorker} / {snap.lost}</dd>
            <dt className="text-slate-600">Error</dt><dd>{snap.errors}</dd>
            <dt className="text-slate-600">Latensi frame (n={snap.latency.n})</dt><dd>rata-rata {fmt(snap.latency.mean)} · median {fmt(snap.latency.median)} · p95 {fmt(snap.latency.p95)} ms</dd>
            <dt className="text-slate-600">Waktu inferensi di worker</dt><dd>rata-rata {fmt(snap.procMean)} ms</dd>
            <dt className="text-slate-600">Responsivitas UI</dt><dd>jeda rAF terbesar {fmt(snap.gap.max, 0)} ms (p95 {fmt(snap.gap.p95, 0)}) · jeda event-loop terbesar {fmt(snap.gap.lagMax, 0)} ms (p95 {fmt(snap.gap.lagP95, 0)}) · long task {snap.gap.longTaskSupported ? snap.gap.longTasks : "tidak didukung"}</dd>
            <dt className="text-slate-600">Frame berpose / bertangan</dt><dd>{snap.posesFrames} / {snap.handsFrames} dari {snap.processed}</dd>
          </dl>
          <Sparkline values={snap.latency.recent} label="Tren latensi 60 frame terakhir" />
          <p className="text-xs text-slate-600">
            Cara membaca responsivitas: <strong>jeda event-loop</strong> besar = thread utama benar-benar terblokir; <strong>jeda rAF</strong> besar tetapi event-loop kecil dan long task 0 = tampilan tersendat karena compositor/GPU (mis. rendering perangkat lunak), bukan karena inferensi memblokir halaman.
          </p>
          <p className="text-xs text-slate-600">
            Konfigurasi aktif: interval minimum {cfg.minIntervalMs} ms (≈{Math.round(1000 / cfg.minIntervalMs)} fps maks), in-flight maks {cfg.maxInFlight}, usia frame maks {cfg.maxFrameAgeMs} ms,
            hingga {cfg.maxPeople} orang, tangan {cfg.hands ? "aktif" : "mati"}, delegasi {cfg.delegate}, jeda saat tab tersembunyi {cfg.pauseWhenHidden ? "ya" : "tidak"}.
          </p>
        </section>
      )}

      <div className="flex flex-wrap items-end gap-3">
        {!active && <button onClick={start} disabled={state.status === "requesting"} className="inline-flex items-center gap-2 rounded-xl bg-forest-700 px-5 py-3 font-medium text-paper-50 hover:bg-forest-900 disabled:opacity-60"><Camera aria-hidden className="h-4 w-4" />Saya mengerti, nyalakan kamera</button>}
        {active && <button onClick={stop} className="inline-flex items-center gap-2 rounded-xl bg-clay-600 px-5 py-3 font-medium text-paper-50"><CameraOff aria-hidden className="h-4 w-4" />Hentikan kamera</button>}
        {active && <button onClick={toggleDetect} className="rounded-xl border border-line-200 px-5 py-3 font-medium hover:bg-parchment-100">{detect === "on" || detect === "loading" ? "Matikan deteksi landmark" : "Nyalakan deteksi landmark"}</button>}
        {devices.length > 1 && (
          <div><label htmlFor="cam" className="mb-1 block text-sm font-medium">Pilih kamera</label>
            <select id="cam" value={deviceId} onChange={(e) => setDeviceId(e.target.value)} className="rounded-xl border border-line-200 bg-paper-50 px-3 py-2.5">
              <option value="">Bawaan</option>{devices.map((d) => <option key={d.deviceId} value={d.deviceId}>{d.label || d.deviceId}</option>)}</select>
            <p className="mt-1 text-xs text-slate-600">{active ? "Hentikan lalu nyalakan kembali untuk berganti kamera." : ""}</p></div>)}
      </div>
    </div>
  );
}
