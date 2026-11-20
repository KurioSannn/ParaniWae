/**
 * Kontrak tipe hasil latihan (docs/API_CONTRACTS.md §4, docs/AI_MOVEMENT_ASSESSMENT.md).
 * HANYA tipe. Tidak ada ambang, bobot, atau logika skor di sini: semuanya harus berasal dari
 * rubrik yang disetujui instruktur mitra (CLAUDE.md aturan 4–6). Belum ada implementasi asesmen.
 */
export type ScoreStatus = "valid" | "not_assessable" | "error";

export type NotAssessableReason =
  | "LOW_BODY_VISIBILITY"
  | "MULTIPLE_PEOPLE"
  | "LOW_LIGHT"
  | "INSUFFICIENT_FRAMES"
  | "NO_APPROVED_RUBRIC";

export interface VersionRefs {
  movementId: string;
  partnerStyleId: string;
  rubricVersionId: string;
  referenceVersionId: string;
  clientAssessmentVersion: string;
}

/** Skor wajib null bila status bukan "valid". */
export type PracticeResult =
  | { status: "valid"; overallScore: number; refs: VersionRefs }
  | { status: "not_assessable"; overallScore: null; reason: NotAssessableReason; refs: VersionRefs }
  | { status: "error"; overallScore: null; refs: VersionRefs };
