import { describe, expect, it } from "vitest";
import { unavailableEngine } from "@/features/practice/engine";
import { summarizeQuality } from "@/features/practice/quality-gate";

describe("unavailableEngine", () => {
  it("selalu not_assessable tanpa skor, apa pun kualitas inputnya", () => {
    const r = unavailableEngine.assess({ refs: null, quality: summarizeQuality([]) });
    expect(r).toMatchObject({ status: "not_assessable", overallScore: null, reason: "NO_APPROVED_RUBRIC" });
  });
});
