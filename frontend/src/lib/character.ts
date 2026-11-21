/** Tipe & helper murni peraga 3D (kontrak: docs/THREEJS_MOVEMENT_CONTRACT.md). */

export type ViewKey = "front" | "side" | "three_quarter";

export interface ClipPhase { phase_id: string | null; keyframe: string; label: string | null; caption: string | null; start: number; end: number }

export interface ClipMeta {
  movement_id: string; clip: string; animation_id: string; source_animation_id: string; title: string | null;
  duration_s: number; loop_interval_s: number; view_recommendation: "depan" | "samping"; source_view: "front" | "side";
  phases: ClipPhase[]; source_ids: string[]; validation_status: string; interpretation: string; checks_passed: boolean;
}

export interface CharacterManifest {
  character: {
    character_id: string; version: string; sha256: string; bytes: number; format: string; joint_count: number; finger_joints: number;
    license: string; costume: string; model_url: string; meshes: { name: string; features: string[] }[];
  };
  clips: ClipMeta[];
}

export const VIEW_LABEL: Record<ViewKey, string> = { front: "Depan", side: "Samping", three_quarter: "¾" };

/** Posisi kamera relatif terhadap pusat gerak. Karakter menghadap +Z; tampak samping = karakter menghadap ke kanan layar. */
export function viewCamera(v: ViewKey): [number, number, number] {
  if (v === "side") return [-4.7, 1.05, 0];
  if (v === "three_quarter") return [-3.3, 1.25, 3.4];
  return [0, 1.05, 4.7];
}

/** Fase yang aktif pada waktu t (detik). Rentang [start, end); waktu di ujung masuk fase terakhir. */
export function clipPhaseAt(clip: Pick<ClipMeta, "phases" | "duration_s">, t: number): ClipPhase | null {
  if (!clip.phases.length) return null;
  const tt = ((t % clip.duration_s) + clip.duration_s) % clip.duration_s;
  return clip.phases.find((p) => tt >= p.start && tt < p.end) ?? clip.phases[clip.phases.length - 1];
}

export function clipFor(manifest: CharacterManifest | null, movementId: string): ClipMeta | null {
  const c = manifest?.clips.find((x) => x.movement_id === movementId);
  return c && c.checks_passed ? c : null;
}

/** Cocokkan klip berdasarkan slug gerakan (id gerakan = mv.<tradisi>.<slug>). */
export function clipForSlug(manifest: CharacterManifest | null, slug: string): ClipMeta | null {
  const c = manifest?.clips.find((x) => x.movement_id.endsWith(`.${slug}`));
  return c && c.checks_passed ? c : null;
}
