/**
 * Mesin status Practice Studio. HANYA kualitas input & keterdeteksian landmark — tidak ada skor teknik,
 * kemiripan gerakan, koreksi postur, penghitung repetisi, atau prediksi kemampuan.
 */
import type { FrameQuality, QualityReason } from "@/features/practice/quality-gate";

export type DetectionState = "waiting_for_subject" | "detecting" | "partial_detection" | "insufficient_visibility";
export type StudioState =
  | "intro" | "initializing" | "ready" | DetectionState | "paused" | "completed" | "error";

export function deriveDetectionState(q: Pick<FrameQuality, "usable" | "reasons" | "requiredCoverage">): DetectionState {
  if (q.reasons.includes("NO_POSE")) return "waiting_for_subject";
  if (q.usable) return "detecting";
  if (q.reasons.includes("MULTIPLE_PEOPLE") || q.reasons.includes("TOO_FEW_LANDMARKS")) return "insufficient_visibility";
  return q.requiredCoverage >= 0.5 ? "partial_detection" : "insufficient_visibility";
}

export const STATE_LABEL: Record<StudioState, string> = {
  intro: "Persiapan", initializing: "Menyiapkan kamera dan mesin", ready: "Siap",
  waiting_for_subject: "Menunggu tubuh terdeteksi", detecting: "Tubuh terdeteksi",
  partial_detection: "Sebagian tubuh terdeteksi", insufficient_visibility: "Tubuh belum terlihat cukup",
  paused: "Dijeda", completed: "Selesai", error: "Terjadi masalah",
};

/** Panduan memperbaiki penangkapan (nada membantu, bukan menyalahkan). */
export function studioGuidance(state: DetectionState, reasons: readonly QualityReason[]): { title: string; hint: string } {
  const has = (r: QualityReason) => reasons.includes(r);
  switch (state) {
    case "waiting_for_subject":
      return { title: "Posisi tubuh belum terdeteksi", hint: "Berdirilah di depan kamera dengan cahaya yang cukup." };
    case "detecting":
      return { title: "Tubuh terdeteksi dengan baik", hint: "Pertahankan posisi ini. Anda dapat berlatih." };
    case "partial_detection":
      return has("OUT_OF_FRAME")
        ? { title: "Mundur sedikit agar tubuh terlihat", hint: "Sebagian tubuh berada di luar bingkai." }
        : { title: "Pastikan kamera tidak terhalang", hint: "Tambah cahaya dan hindari penghalang di depan tubuh." };
    case "insufficient_visibility":
      if (has("MULTIPLE_PEOPLE")) return { title: "Pastikan hanya satu orang di kamera", hint: "Orang lain di area kamera membuat deteksi tidak jelas." };
      if (has("OUT_OF_FRAME")) return { title: "Posisikan seluruh tubuh di dalam kamera", hint: "Mundur hingga kepala sampai kaki terlihat." };
      return { title: "Pastikan kamera tidak terhalang", hint: "Tubuh belum terlihat cukup jelas; periksa cahaya dan posisi kamera." };
  }
}

/** Menahan perubahan status sampai kandidat sama muncul `n` kali berturut-turut (anti-kedip). */
export class StateSmoother {
  private shown: DetectionState = "waiting_for_subject";
  private cand: DetectionState | null = null;
  private run = 0;
  constructor(private readonly n = 5) {}
  get current(): DetectionState { return this.shown; }
  push(c: DetectionState): DetectionState {
    if (c === this.shown) { this.cand = null; this.run = 0; return this.shown; }
    if (c === this.cand) this.run += 1; else { this.cand = c; this.run = 1; }
    if (this.run >= this.n) { this.shown = c; this.cand = null; this.run = 0; }
    return this.shown;
  }
  reset(): void { this.shown = "waiting_for_subject"; this.cand = null; this.run = 0; }
}

/** Jam sesi: waktu aktif vs waktu jeda. `now` dapat diinjeksi untuk tes. */
export class SessionClock {
  private startedAt: number | null = null;
  private pausedAt: number | null = null;
  private active = 0;
  private paused = 0;
  private last = 0;
  constructor(private readonly now: () => number = () => performance.now()) {}
  get running(): boolean { return this.startedAt !== null && this.pausedAt === null && !this.stopped; }
  get isPaused(): boolean { return this.pausedAt !== null && !this.stopped; }
  private stopped = false;
  start(): void { this.startedAt = this.last = this.now(); this.active = this.paused = 0; this.pausedAt = null; this.stopped = false; }
  private roll(): void {
    const t = this.now();
    if (this.stopped || this.startedAt === null) return;
    if (this.pausedAt === null) this.active += t - this.last; else this.paused += t - this.last;
    this.last = t;
  }
  pause(): void { if (!this.running) return; this.roll(); this.pausedAt = this.last; }
  resume(): void { if (!this.isPaused) return; this.roll(); this.pausedAt = null; }
  stop(): { activeMs: number; pausedMs: number } { this.roll(); this.stopped = true; return this.read(); }
  read(): { activeMs: number; pausedMs: number } {
    if (this.startedAt === null) return { activeMs: 0, pausedMs: 0 };
    if (!this.stopped) this.roll();
    return { activeMs: Math.round(this.active), pausedMs: Math.round(this.paused) };
  }
}

export interface AggregateExtra { dropped: number; engine: "worker" | "synthetic"; delegate: "GPU" | "CPU" | null; simulated: boolean }
const REASONS: QualityReason[] = ["NO_POSE", "MULTIPLE_PEOPLE", "TOO_FEW_LANDMARKS", "LOW_VISIBILITY", "OUT_OF_FRAME", "NO_HAND", "LOW_HAND_CONFIDENCE"];

/** Mengagregasi kualitas input selama sesi (waktu per status, hitungan alasan). Tidak menyimpan landmark apa pun. */
export class QualityAggregator {
  private frames = 0;
  private valid = 0;
  private ms: Record<DetectionState, number> = { waiting_for_subject: 0, detecting: 0, partial_detection: 0, insufficient_visibility: 0 };
  private reasons: Record<string, number> = Object.fromEntries(REASONS.map((r) => [r, 0]));
  private lastT: number | null = null;
  private lastState: DetectionState = "waiting_for_subject";
  private paused = false;

  start(t: number): void { this.lastT = t; this.paused = false; }
  private attribute(t: number): void {
    if (this.lastT !== null && !this.paused) this.ms[this.lastState] += Math.max(0, t - this.lastT);
    this.lastT = t;
  }
  record(state: DetectionState, q: Pick<FrameQuality, "usable" | "reasons">, t: number): void {
    if (this.paused) return;
    this.attribute(t);
    this.lastState = state;
    this.frames += 1;
    if (q.usable) this.valid += 1;
    for (const r of q.reasons) this.reasons[r] = (this.reasons[r] ?? 0) + 1;
  }
  pause(t: number): void { this.attribute(t); this.paused = true; }
  resume(t: number): void { this.paused = false; this.lastT = t; }
  snapshot(t: number, extra: AggregateExtra) {
    this.attribute(t);
    const r = (k: string) => this.reasons[k] ?? 0;
    return {
      frames_total: this.frames + extra.dropped, processed_frames: this.frames, dropped_frames: extra.dropped,
      valid_frame_ratio: this.frames ? this.valid / this.frames : 0,
      ms_in_state: Object.fromEntries(Object.entries(this.ms).map(([k, v]) => [k, Math.round(v)])) as Record<DetectionState, number>,
      reasons: { NO_POSE: r("NO_POSE"), MULTIPLE_PEOPLE: r("MULTIPLE_PEOPLE"), TOO_FEW_LANDMARKS: r("TOO_FEW_LANDMARKS"), LOW_VISIBILITY: r("LOW_VISIBILITY"), OUT_OF_FRAME: r("OUT_OF_FRAME"), NO_HAND: r("NO_HAND"), LOW_HAND_CONFIDENCE: r("LOW_HAND_CONFIDENCE") },
      engine: extra.engine, delegate: extra.delegate, simulated: extra.simulated,
    };
  }
}
