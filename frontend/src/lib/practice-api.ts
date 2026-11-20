import { clientRequest } from "@/lib/client-api";
import type { ApiResult } from "@/lib/api";
import type { PracticeSession, QualitySummaryPayload } from "@/lib/types";

/** SATU-SATUNYA tempat Practice Studio berbicara dengan backend: metadata sesi + agregat kualitas input. */
export function startPracticeSession(lessonId: string, modelVersion: string): Promise<ApiResult<PracticeSession>> {
  return clientRequest<PracticeSession>("POST", "/practice-sessions", { lesson_id: lessonId, model_version: modelVersion, client_version: "studio-1" });
}

export interface CompleteBody {
  status: "completed" | "abandoned" | "error";
  active_duration_ms: number;
  paused_duration_ms: number;
  quality_summary: QualitySummaryPayload | null;
  error_code?: string;
}

export function completePracticeSession(id: string, body: CompleteBody, opts: { keepalive?: boolean } = {}): Promise<ApiResult<PracticeSession>> {
  return clientRequest<PracticeSession>("POST", `/practice-sessions/${id}/complete`, body, opts);
}
