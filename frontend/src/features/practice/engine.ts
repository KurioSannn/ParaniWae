/**
 * Kontrak mesin asesmen. Implementasi nyata MENUNGGU rubrik, referensi, toleransi, dan
 * umpan balik yang disetujui instruktur mitra. Sampai itu ada, satu-satunya implementasi
 * adalah `unavailableEngine`, yang selalu mengembalikan `not_assessable`.
 */
import type { QualitySummary } from "@/features/practice/quality-gate";
import type { PracticeResult, VersionRefs } from "@/features/practice/assessment-types";

export interface AssessmentInput {
  refs: VersionRefs | null;
  quality: QualitySummary;
}

export interface AssessmentEngine {
  readonly id: string;
  assess(input: AssessmentInput): PracticeResult;
}

const NO_REFS: VersionRefs = {
  movementId: "", partnerStyleId: "", rubricVersionId: "", referenceVersionId: "", clientAssessmentVersion: "0.0.0-unavailable",
};

export const unavailableEngine: AssessmentEngine = {
  id: "unavailable",
  assess({ refs }) {
    return { status: "not_assessable", overallScore: null, reason: "NO_APPROVED_RUBRIC", refs: refs ?? NO_REFS };
  },
};
