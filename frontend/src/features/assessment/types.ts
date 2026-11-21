/**
 * Kontrak protokol & hasil penilaian gerak (docs/MOVEMENT_ASSESSMENT_CONTRACT.md).
 * Protokol adalah DATA (content/pencak-silat/assessments/*.protocol.json); mesin tidak memuat angka target apa pun.
 */

export type Vec3 = [number, number, number];

/** Fitur terukur yang didukung mesin. Menambah gerakan baru = menulis protokol, bukan mengubah mesin. */
export type FeatureId =
  | "knee_angle"          // sudut dalam pinggul–lutut–pergelangan kaki (180 = lurus)
  | "knee_flexion"        // 180 − knee_angle
  | "thigh_elevation"     // sudut paha dari arah bawah (0 = menggantung, 90 = datar)
  | "torso_incline"       // sudut garis bahu-tengah→pinggul-tengah dari vertikal
  | "knee_over_toe"       // |x lutut − x ujung kaki| / panjang tungkai (tampak depan)
  | "balance_center"      // (x pinggul-tengah − x pergelangan-tengah) / lebar kuda-kuda (tampak depan)
  | "weight_forward"      // posisi pinggul-tengah antara kaki belakang (0) dan depan (1) (tampak samping)
  | "step_length"         // jarak horizontal kedua pergelangan kaki / panjang tungkai
  | "stance_width_ratio"  // jarak pergelangan kaki / jarak pinggul (tampak depan)
  | "wrist_hip_height"    // (y pinggul − y pergelangan tangan) / panjang torso (+ = di atas pinggul)
  | "hip_sway";           // simpangan baku tinggi pinggul / panjang tungkai selama jendela fase

export type Side = "L" | "R";
export type SideRule = "L" | "R" | "both_mean" | "both_min" | "lifting" | "supporting" | "front" | "rear";

export interface CriterionSpec {
  id: string;
  label: string;
  feature: FeatureId;
  side?: SideRule;
  /** keyframe referensi tempat kriteria dinilai (jendela tahan fase itu). */
  phase_keyframe: string;
  aggregate: "max" | "min" | "median" | "std";
  /** salah satu: nilai tunggal ± toleransi, atau rentang [min, max]. */
  target?: number;
  target_range?: [number, number];
  tolerance: number;
  /** jarak (di luar toleransi) tempat skor kriteria mencapai 0. */
  falloff: number;
  weight: number;
  min_confidence: number;
  /** fitur yang memerlukan world landmarks (kedalaman), mis. tekukan lutut dari tampak depan. */
  requires_world?: boolean;
  unit: "deg" | "ratio";
  rationale: string;
  basis: "source" | "source_interpreted" | "reference_illustration" | "technical";
  source_ids: string[];
  locator?: string;
  feedback: { below: string; above: string; ok: string; unmeasured?: string };
}

export interface PhaseRequirement {
  keyframe: string;
  label: string;
  /** fase wajib terdeteksi (penyelarasan berbiaya wajar & panjang minimal). */
  required: boolean;
}

export interface Protocol {
  schema: "silatara.assessment-protocol/v1";
  protocol_id: string;
  movement_id: string;
  protocol_version: string;
  status: "active" | "draft" | "retired";
  calibration: string;
  title: string;
  summary: string;
  reference_id: string;
  reference_animation_id: string;
  required_view: "front" | "side";
  required_landmarks: number[];
  min_visibility: number;
  body_positioning: string[];
  phases: PhaseRequirement[];
  phase_completion_weight: number;
  criteria: CriterionSpec[];
  alignment_features: FeatureId[];
  confidence_requirements: { min_valid_frame_ratio: number; min_frames: number; max_unmeasured_weight_ratio: number };
  scoring_formula: string;
  interpretation_notes: string[];
  source_ids: string[];
  disclaimer: string;
}

/** Satu frame terukur (koordinat gambar ternormalisasi + world opsional). Tidak pernah dikirim ke server. */
export interface MeasureFrame {
  t: number; // detik
  image: Vec3[] | null;                    // 33 titik: x dikali rasio lebar/tinggi, y ke bawah (0..1), z
  world: Vec3[] | null;                    // 33 titik meter (opsional)
  visibility: number[];                    // 33 nilai 0..1
  usable: boolean;                         // lolos quality gate
}

export interface CriterionResult {
  id: string; label: string; feature: FeatureId; unit: "deg" | "ratio";
  target: number | [number, number]; tolerance: number; actual: number | null; confidence: number;
  score: number | null; weight: number; status: "ok" | "below" | "above" | "unmeasured";
  feedback: string; basis: CriterionSpec["basis"]; phase_keyframe: string;
}

export interface PhaseResult { keyframe: string; label: string; detected: boolean; score: number | null; user_start: number | null; user_end: number | null; tempo_ratio: number | null }

export type AssessmentOutcome =
  | {
    status: "scored"; total_score: number; input_quality: number; criteria: CriterionResult[]; phases: PhaseResult[];
    best_phase: string | null; weakest_phase: string | null; suggestions: string[]; frames_analyzed: number; duration_s: number;
    protocol_id: string; protocol_version: string; reference_id: string; engine_version: string;
  }
  | {
    status: "not_assessable"; reason: NotAssessableReason; message: string; input_quality: number; frames_analyzed: number;
    protocol_id: string; protocol_version: string; reference_id: string; engine_version: string;
  };

export type NotAssessableReason =
  | "TOO_FEW_FRAMES" | "LOW_INPUT_QUALITY" | "MOVEMENT_NOT_FOUND" | "KEY_LANDMARKS_MISSING" | "WRONG_CAMERA_VIEW" | "TOO_MANY_UNMEASURED";
