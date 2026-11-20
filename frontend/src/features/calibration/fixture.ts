/**
 * FIXTURE DEMO untuk Calibration Workspace — kerangka sintetis buatan kode, BUKAN rekaman manusia dan BUKAN gerakan
 * pencak silat. Dipakai hanya agar antarmuka (timeline, penanda, overlay) dapat diuji tanpa media berizin.
 */
import type { LandmarkFrame } from "@/features/practice/landmarks";
import { syntheticFrame } from "@/features/practice/synthetic-pose";

export const FIXTURE_KEY = "demo-synthetic" as const;
export const FIXTURE_DURATION_MS = 6000;
export const FIXTURE_LABEL = "[DEMO] Fixture sintetis — bukan rekaman manusia";
export const FIXTURE_MODEL_VERSION = "[DEMO] synthetic-fixture (tanpa model)";

export function fixtureFrame(ms: number): LandmarkFrame {
  return syntheticFrame("full", Math.round(ms / 33), ms, 640, 480);
}
