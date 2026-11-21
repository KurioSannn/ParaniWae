"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, Camera, CameraOff, CheckCircle2, CircleDashed, RotateCcw, ShieldCheck, Square } from "lucide-react";
import { apiGet } from "@/lib/api";
import { clientRequest } from "@/lib/client-api";
import { assess, ENGINE_VERSION, referenceFrames, type ReferenceJson } from "@/features/assessment/engine";
import { positioningCheck, toMeasureFrame } from "@/features/assessment/capture";
import type { AssessmentOutcome, MeasureFrame, Protocol } from "@/features/assessment/types";
import type { AsyncLandmarkerAdapter } from "@/features/practice/async-adapter";
import { CAMERA_MESSAGES, CameraController, isStarted } from "@/features/practice/camera";
import { DEFAULT_INFERENCE_CONFIG, MEDIAPIPE_VERSION, type InferenceConfig } from "@/features/practice/config";
import type { LandmarkFrame } from "@/features/practice/landmarks";
import { nowMs } from "@/features/practice/metrics";
import { createFrameBitmap, FramePump, makeFrameScheduler } from "@/features/practice/pipeline";
import { drawSkeleton, fitVideoBox, LandmarkSmoother, type DrawCtx, type Size } from "@/features/practice/skeleton";
import { WorkerLandmarkerAdapter } from "@/features/practice/worker-adapter";

type Step = "intro" | "starting" | "positioning" | "countdown" | "recording" | "analyzing" | "result" | "error";
const btn = "inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 font-medium disabled:opacity-60";
const primary = `${btn} bg-forest-700 text-paper-50 hover:bg-forest-900`;
const secondary = `${btn} border border-line-200 bg-paper-50 hover:bg-parchment-100`;
const MIN_RECORD_S = 3;

export function AssessmentPractice({ protocol, movementTitle, loggedIn, lessonRef, createAdapter }: {
  protocol: Protocol; movementTitle: string; loggedIn: boolean; lessonRef?: string;
  createAdapter?: (cfg: InferenceConfig) => AsyncLandmarkerAdapter;
}) {
  const [step, setStep] = useState<Step>("intro");
  const [consent, setConsent] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [posMsg, setPosMsg] = useState("Menyiapkan kamera…");
  const [count, setCount] = useState(3);
  const [elapsed, setElapsed] = useState(0);
  const [mirror, setMirror] = useState(true);
  const [box, setBox] = useState<Size>({ width: 640, height: 480 });
  const [result, setResult] = useState<AssessmentOutcome | null>(null);
  const [saveBreakdown, setSaveBreakdown] = useState(true);
  const [saved, setSaved] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const stepRef = useRef<Step>("intro");
  const stageRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctrl = useRef<CameraController | null>(null);
  const adapter = useRef<AsyncLandmarkerAdapter | null>(null);
  const pump = useRef<FramePump | null>(null);
  const frames = useRef<MeasureFrame[]>([]);
  const recStart = useRef(0);
  const okSince = useRef<number | null>(null);
  const reference = useRef<ReferenceJson | null>(null);
  const smoother = useRef(new LandmarkSmoother());
  const boxRef = useRef(box);
  const mirrorRef = useRef(mirror);
  const libRef = useRef("");
  const cfg: InferenceConfig = { ...DEFAULT_INFERENCE_CONFIG, hands: true };
  const refDuration = useRef(10);
  const maxRecord = () => Math.min(40, Math.max(8, refDuration.current * 2.2));
  const go = (s: Step) => { stepRef.current = s; setStep(s); };

  const render = useCallback((frame: LandmarkFrame | null) => {
    const c = canvasRef.current, g = c?.getContext("2d");
    if (!c || !g) return;
    const dpr = window.devicePixelRatio || 1;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (!frame) { g.clearRect(0, 0, boxRef.current.width, boxRef.current.height); return; }
    drawSkeleton(g as unknown as DrawCtx, smoother.current.smooth(frame), boxRef.current, { mirror: mirrorRef.current, showHands: true });
  }, []);

  useEffect(() => { boxRef.current = box; mirrorRef.current = mirror; }, [box, mirror]);

  const teardown = useCallback(async () => {
    pump.current?.stop(); pump.current = null;
    const a = adapter.current; adapter.current = null;
    await a?.dispose();
    ctrl.current?.stop();
    if (videoRef.current) videoRef.current.srcObject = null;
    smoother.current.reset();
    render(null);
  }, [render]);

  // pastikan kamera & worker berhenti saat keluar halaman
  useEffect(() => {
    const onHide = () => { void teardown(); };
    window.addEventListener("pagehide", onHide);
    return () => { window.removeEventListener("pagehide", onHide); void teardown(); };
  }, [teardown]);

  // ukuran video tanpa crop
  const live = step === "starting" || step === "positioning" || step === "countdown" || step === "recording";
  useEffect(() => {
    const el = stageRef.current;
    if (!el || !live) return;
    const update = () => {
      const v = videoRef.current;
      setBox(fitVideoBox(v?.videoWidth || 640, v?.videoHeight || 480, el.clientWidth, Math.max(240, window.innerHeight * 0.62)));
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    videoRef.current?.addEventListener("loadedmetadata", update);
    return () => ro.disconnect();
  }, [live]);
  useEffect(() => {
    const c = canvasRef.current;
    if (!c) return;
    const dpr = window.devicePixelRatio || 1;
    c.width = Math.round(box.width * dpr); c.height = Math.round(box.height * dpr);
  }, [box]);

  const onFrame = useCallback((frame: LandmarkFrame) => {
    render(frame);
    const s = stepRef.current;
    const t = nowMs() / 1000;
    const mf = toMeasureFrame(frame, t);
    if (s === "positioning") {
      const p = positioningCheck(mf, protocol.required_view);
      setPosMsg(p.message);
      if (p.ok) {
        okSince.current ??= t;
        if (t - okSince.current > 1.2) { okSince.current = null; setCount(3); go("countdown"); }
      } else okSince.current = null;
    } else if (s === "recording") {
      frames.current.push(mf);
    }
  }, [protocol.required_view, render]);

  async function start() {
    setMessage(null); setResult(null); setSaved("idle"); frames.current = [];
    go("starting");
    try {
      if (!reference.current) {
        const r = await apiGet<ReferenceJson>(`/research/character/reference/${encodeURIComponent(protocol.movement_id)}`);
        if (!r.ok) throw new Error("Referensi gerak tidak dapat dimuat.");
        reference.current = r.data;
        refDuration.current = r.data.frames.length ? r.data.frames[r.data.frames.length - 1].t : 10;
      }
      ctrl.current ??= new CameraController();
      const cam = await ctrl.current.start();
      if (!isStarted(cam)) {
        const text = cam.type === "denied" ? CAMERA_MESSAGES.denied : cam.type === "unavailable" ? CAMERA_MESSAGES[cam.reason] : cam.type === "error" ? cam.message : "Kamera tidak dapat dimulai.";
        throw new Error(text);
      }
      const video = videoRef.current!;
      video.srcObject = cam.stream;
      await video.play().catch(() => undefined);
      const a = createAdapter ? createAdapter(cfg) : new WorkerLandmarkerAdapter(cfg);
      adapter.current = a;
      const sched = makeFrameScheduler(video);
      const p = new FramePump({
        adapter: a, source: video, config: cfg, createBitmap: createFrameBitmap, now: nowMs, schedule: sched.schedule, cancel: sched.cancel,
        onResult: ({ frame }) => onFrame(frame),
        onFatal: ({ message: m }) => { void teardown().then(() => { setMessage(m); go("error"); }); },
      });
      pump.current = p;
      const info = await a.init();
      libRef.current = `${info.library ?? `@mediapipe/tasks-vision@${MEDIAPIPE_VERSION}`}/pose_landmarker_lite+hand_landmarker`;
      p.start();
      setPosMsg("Atur posisi Anda…");
      go("positioning");
    } catch (e) {
      await teardown();
      setMessage(e instanceof Error ? e.message : "Kamera atau mesin deteksi gagal dimuat.");
      go("error");
    }
  }

  // hitung mundur → rekam
  useEffect(() => {
    if (step !== "countdown") return;
    let n = 3;
    const id = setInterval(() => {
      n -= 1;
      if (n <= 0) { clearInterval(id); frames.current = []; recStart.current = nowMs(); setElapsed(0); go("recording"); }
      else setCount(n);
    }, 1000);
    return () => clearInterval(id);
  }, [step]);

  const finish = useCallback(async () => {
    if (stepRef.current !== "recording") return;
    go("analyzing");
    const captured = frames.current;
    frames.current = [];
    await teardown(); // kamera mati SEBELUM analisis; frame hanya ada di memori
    const ref = reference.current!;
    const t0 = captured.length ? captured[0].t : 0;
    const out = assess(protocol, referenceFrames(ref, protocol.required_view), captured.map((f) => ({ ...f, t: f.t - t0 })));
    setResult(out);
    go("result");
  }, [protocol, teardown]);

  useEffect(() => {
    if (step !== "recording") return;
    const id = setInterval(() => {
      const s = (nowMs() - recStart.current) / 1000;
      setElapsed(s);
      if (s >= maxRecord()) void finish();
    }, 200);
    return () => clearInterval(id);
  }, [step, finish]);

  async function stopAll() { await teardown(); frames.current = []; go("intro"); }

  async function save() {
    if (!result) return;
    setSaved("saving");
    const scored = result.status === "scored";
    const body = {
      movement_id: protocol.movement_id, lesson_ref: lessonRef, protocol_id: result.protocol_id, protocol_version: result.protocol_version,
      reference_id: result.reference_id, engine_version: ENGINE_VERSION, model_version: libRef.current || "mediapipe",
      status: result.status, not_assessable_reason: scored ? null : result.reason, total_score: scored ? result.total_score : null,
      input_quality: result.input_quality, duration_ms: scored ? Math.round(result.duration_s * 1000) : null, frames_analyzed: result.frames_analyzed,
      consent_breakdown: scored && saveBreakdown,
      criteria: scored && saveBreakdown ? result.criteria.map((c) => ({ id: c.id, label: c.label, score: c.score, actual: c.actual, target: c.target, weight: c.weight, status: c.status })) : null,
      phases: scored && saveBreakdown ? result.phases.map((p) => ({ keyframe: p.keyframe, label: p.label, detected: p.detected, score: p.score })) : null,
      feedback: scored ? result.suggestions.slice(0, 3) : null,
    };
    const r = await clientRequest("POST", "/assessments", body);
    setSaved(r.ok ? "saved" : "error");
  }

  // ---------------------------------------------------------------- tampilan
  if (step === "intro" || step === "error") {
    return (
      <section aria-labelledby="mulai" className="space-y-4 rounded-2xl border border-line-200 bg-paper-50 p-5" data-testid="assess" data-step={step}>
        <h2 id="mulai" className="flex items-center gap-2 font-serif text-2xl text-forest-900"><ShieldCheck aria-hidden className="h-5 w-5 text-forest-700" />Sebelum mencoba</h2>
        {message && <p role="alert" className="flex items-start gap-2 rounded-xl border border-clay-600/40 bg-clay-600/5 p-3 text-sm"><AlertTriangle aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-clay-600" />{message}</p>}
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
          {protocol.body_positioning.map((b) => <li key={b}>{b}</li>)}
          <li>Kamera hanya menyala setelah Anda setuju dan <strong>dapat dihentikan kapan saja</strong>. Mikrofon tidak digunakan.</li>
          <li>Gambar diproses <strong>di perangkat Anda</strong>. Video dan posisi tubuh tidak direkam atau dikirim. Data gerak dihapus dari memori setelah skor dihitung.</li>
          <li>Hentikan latihan bila terasa nyeri atau tidak nyaman.</li>
        </ul>
        <label className="flex items-start gap-3 text-sm">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1 h-4 w-4" />
          <span>Saya memahami hal di atas dan <strong>setuju kamera dinyalakan</strong> untuk latihan {movementTitle}.</span>
        </label>
        <button onClick={() => void start()} disabled={!consent} className={primary}><Camera aria-hidden className="h-4 w-4" />Coba Latihan Sekarang</button>
      </section>
    );
  }

  if (step === "result" && result) return <ResultView result={result} protocol={protocol} loggedIn={loggedIn} onRetry={() => void start()}
    saveBreakdown={saveBreakdown} setSaveBreakdown={setSaveBreakdown} saved={saved} onSave={() => void save()} />;

  return (
    <section aria-label="Latihan kamera" className="space-y-3" data-testid="assess" data-step={step}>
      <div ref={stageRef} className="w-full">
        <div className="relative mx-auto overflow-hidden rounded-2xl bg-ink-950" style={{ width: box.width, height: box.height }}>
          <video ref={videoRef} playsInline muted className="absolute inset-0 h-full w-full object-contain" style={{ transform: mirror ? "scaleX(-1)" : undefined }} />
          <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" aria-hidden />
          <div aria-live="polite" className="absolute inset-x-0 top-0 bg-ink-950/60 p-2 text-center text-sm text-paper-50">
            {step === "starting" && "Menyalakan kamera dan memuat model deteksi…"}
            {step === "positioning" && posMsg}
            {step === "countdown" && `Bersiap… ${count}`}
            {step === "recording" && `Lakukan gerakan: ${protocol.phases.map((p) => p.label).join(" → ")} · ${Math.floor(elapsed)} dtk`}
            {step === "analyzing" && "Menganalisis gerakan…"}
          </div>
          {step === "countdown" && <div className="absolute inset-0 grid place-items-center font-serif text-8xl text-paper-50">{count}</div>}
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-2">
        {step === "recording" && (
          <button onClick={() => void finish()} disabled={elapsed < MIN_RECORD_S} className={primary}><Square aria-hidden className="h-4 w-4" />Selesai, nilai gerakan</button>
        )}
        <button onClick={() => void stopAll()} className={secondary}><CameraOff aria-hidden className="h-4 w-4" />Hentikan kamera</button>
        <label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={mirror} onChange={(e) => setMirror(e.target.checked)} />Tampilan cermin</label>
      </div>
    </section>
  );
}

function ResultView({ result, protocol, loggedIn, onRetry, saveBreakdown, setSaveBreakdown, saved, onSave }: {
  result: AssessmentOutcome; protocol: Protocol; loggedIn: boolean; onRetry: () => void;
  saveBreakdown: boolean; setSaveBreakdown: (v: boolean) => void; saved: "idle" | "saving" | "saved" | "error"; onSave: () => void;
}) {
  if (result.status === "not_assessable") {
    return (
      <section className="space-y-4 rounded-2xl border border-line-200 bg-paper-50 p-5" data-testid="assess" data-step="result" data-status="not_assessable">
        <h2 className="font-serif text-2xl text-forest-900">Gerakan belum dapat dinilai</h2>
        <p>{result.message}</p>
        <p className="text-sm text-slate-600">Kualitas masukan: {Math.round(result.input_quality * 100)}%. Skor tidak diberikan agar tidak menyesatkan.</p>
        <button onClick={onRetry} className={primary}><RotateCcw aria-hidden className="h-4 w-4" />Coba lagi</button>
      </section>
    );
  }
  const tone = result.total_score >= 80 ? "text-forest-700" : result.total_score >= 50 ? "text-bronze-700" : "text-clay-600";
  const fmt = (v: number | null, unit: string) => (v === null ? "—" : unit === "deg" ? `${Math.round(v)}°` : v.toFixed(2).replace(".", ","));
  const fmtT = (t: number | [number, number], unit: string) => (Array.isArray(t) ? `${fmt(t[0], unit)}–${fmt(t[1], unit)}` : fmt(t, unit));
  return (
    <section className="space-y-6" data-testid="assess" data-step="result" data-status="scored">
      <div className="grid gap-4 rounded-2xl border border-line-200 bg-paper-50 p-5 sm:grid-cols-[auto_1fr] sm:items-center">
        <div className="text-center">
          <p className="text-sm text-slate-600">Skor kesesuaian</p>
          <p className={`font-serif text-6xl ${tone}`} data-testid="total-score">{result.total_score}</p>
          <p className="text-xs text-slate-600">dari 100</p>
        </div>
        <div className="space-y-2">
          <h2 className="font-serif text-2xl text-forest-900">Saran perbaikan</h2>
          <ol className="list-decimal space-y-1 pl-5">{result.suggestions.map((s) => <li key={s}>{s}</li>)}</ol>
          <p className="text-xs text-slate-600">
            {result.best_phase && <>Fase terbaik: <strong>{result.best_phase}</strong>. </>}
            {result.weakest_phase && <>Perlu diperbaiki: <strong>{result.weakest_phase}</strong>. </>}
            Kualitas masukan {Math.round(result.input_quality * 100)}% · {result.frames_analyzed} frame · {result.duration_s.toString().replace(".", ",")} dtk.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-line-200 bg-paper-50">
        <table className="w-full min-w-[34rem] text-sm">
          <caption className="p-3 text-left font-semibold">Rincian per kriteria</caption>
          <thead className="text-left text-slate-600"><tr><th className="p-3">Kriteria</th><th className="p-3">Panduan</th><th className="p-3">Terukur</th><th className="p-3">Bobot</th><th className="p-3">Skor</th></tr></thead>
          <tbody>
            {result.criteria.map((c) => (
              <tr key={c.id} className="border-t border-line-200">
                <td className="p-3">
                  <span className="flex items-center gap-2">{c.status === "ok" ? <CheckCircle2 aria-hidden className="h-4 w-4 text-forest-700" /> : c.status === "unmeasured" ? <CircleDashed aria-hidden className="h-4 w-4 text-slate-600" /> : <AlertTriangle aria-hidden className="h-4 w-4 text-bronze-700" />}{c.label}</span>
                  <span className="block text-xs text-slate-600">{c.feedback}</span>
                </td>
                <td className="p-3 tabular-nums">{fmtT(c.target, c.unit)} (±{fmt(c.tolerance, c.unit)})</td>
                <td className="p-3 tabular-nums">{fmt(c.actual, c.unit)}</td>
                <td className="p-3 tabular-nums">{c.weight}</td>
                <td className="p-3 tabular-nums">{c.score ?? "tidak terukur"}</td>
              </tr>
            ))}
            <tr className="border-t border-line-200"><td className="p-3">Kelengkapan fase</td><td className="p-3" colSpan={2}>{result.phases.filter((p) => p.detected).length}/{result.phases.length} fase terlihat</td><td className="p-3">{protocol.phase_completion_weight}</td><td className="p-3" /></tr>
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap gap-2 text-sm">
        {result.phases.map((p) => (
          <span key={p.keyframe} className={`rounded-full border px-3 py-1 ${p.detected ? "border-forest-700/40" : "border-clay-600/40 text-clay-600"}`}>
            {p.label}: {p.detected ? (p.score !== null ? `${p.score}` : "terlihat") : "belum terlihat"}{p.tempo_ratio ? ` · tempo ${p.tempo_ratio.toString().replace(".", ",")}×` : ""}
          </span>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button onClick={onRetry} className={primary}><RotateCcw aria-hidden className="h-4 w-4" />Coba lagi</button>
        {loggedIn ? (
          <>
            <label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={saveBreakdown} onChange={(e) => setSaveBreakdown(e.target.checked)} />Simpan juga rincian per kriteria</label>
            <button onClick={onSave} disabled={saved === "saving" || saved === "saved"} className={secondary}>{saved === "saved" ? "Tersimpan di riwayat" : saved === "saving" ? "Menyimpan…" : "Simpan ke riwayat"}</button>
            {saved === "saved" && <Link className="text-sm underline" href="/app/latihan/riwayat">Lihat riwayat</Link>}
            {saved === "error" && <span role="alert" className="text-sm text-clay-600">Gagal menyimpan. Coba lagi.</span>}
          </>
        ) : (
          <p className="text-sm text-slate-600"><Link className="underline" href="/masuk">Masuk</Link> untuk menyimpan riwayat dan melihat perkembangan Anda.</p>
        )}
      </div>
      <p className="text-xs text-slate-600">{protocol.disclaimer} Protokol {result.protocol_version} · mesin {result.engine_version}.</p>
    </section>
  );
}
