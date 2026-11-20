import { describe, expect, it } from "vitest";
import { FrameTimer } from "@/features/practice/metrics";

describe("FrameTimer", () => {
  it("kosong -> null", () => { const t = new FrameTimer(); expect(t.mean()).toBeNull(); expect(t.p95()).toBeNull(); });
  it("mean dan p95 (nearest-rank)", () => {
    const t = new FrameTimer();
    for (let i = 1; i <= 100; i++) t.add(i);
    expect(t.mean()).toBe(50.5);
    expect(t.p95()).toBe(95);
  });
  it("membatasi jumlah sampel", () => {
    const t = new FrameTimer(3);
    [1, 2, 3, 4].forEach((x) => t.add(x));
    expect(t.count).toBe(3);
    expect(t.mean()).toBe(3);
  });
});
