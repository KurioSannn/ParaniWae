/**
 * Helper murni untuk timeline Calibration Workspace. Tidak ada penilaian: hanya waktu, penanda, dan segmen.
 * Anotasi = "instructor reference annotation" (bukan ground truth, bukan label akurasi).
 */
export const FRAME_MS = 1000 / 30; // langkah frame nominal (perkiraan 30 fps; tidak memeriksa fps klip)

export interface MarkerLike { id: string; timestamp_ms: number; label: string; phase_id: string | null }
export interface Segment { fromMs: number; toMs: number; label: string; phaseId: string | null; startMarkerId: string }

export function clampMs(ms: number, durationMs: number): number {
  if (!Number.isFinite(ms)) return 0;
  return Math.min(Math.max(0, Math.round(ms)), Math.max(0, Math.floor(durationMs)));
}
export function stepFrame(ms: number, dir: 1 | -1, durationMs: number, frameMs = FRAME_MS): number {
  return clampMs(ms + dir * frameMs, durationMs);
}
export function sortMarkers<T extends MarkerLike>(m: readonly T[]): T[] {
  return [...m].sort((a, b) => a.timestamp_ms - b.timestamp_ms || a.id.localeCompare(b.id));
}
/** Penanda terdekat dalam toleransi (ms) dari waktu `ms`; null bila tidak ada. */
export function markerNear<T extends MarkerLike>(markers: readonly T[], ms: number, toleranceMs = 80): T | null {
  let best: T | null = null, bd = Infinity;
  for (const m of markers) { const d = Math.abs(m.timestamp_ms - ms); if (d <= toleranceMs && d < bd) { best = m; bd = d; } }
  return best;
}
/** Segmen = rentang dari satu penanda ke penanda berikutnya (penanda terakhir -> akhir klip). */
export function segments<T extends MarkerLike>(markers: readonly T[], durationMs: number): Segment[] {
  const s = sortMarkers(markers.filter((m) => m.timestamp_ms <= durationMs));
  return s.map((m, i) => ({ fromMs: m.timestamp_ms, toMs: i + 1 < s.length ? s[i + 1].timestamp_ms : durationMs, label: m.label, phaseId: m.phase_id, startMarkerId: m.id }));
}
export function segmentAt(segs: readonly Segment[], ms: number): Segment | null {
  return segs.find((s) => ms >= s.fromMs && ms < s.toMs) ?? (segs.length && ms === segs[segs.length - 1].toMs ? segs[segs.length - 1] : null);
}
/** mm:ss.mmm */
export function formatTimeMs(ms: number): string {
  const t = Math.max(0, Math.round(ms));
  const m = Math.floor(t / 60000), s = Math.floor((t % 60000) / 1000), r = t % 1000;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(r).padStart(3, "0")}`;
}
export function posToMs(x: number, width: number, durationMs: number): number {
  if (width <= 0) return 0;
  return clampMs((Math.min(Math.max(x, 0), width) / width) * durationMs, durationMs);
}
export function msToPct(ms: number, durationMs: number): number {
  return durationMs > 0 ? Math.min(100, Math.max(0, (ms / durationMs) * 100)) : 0;
}
