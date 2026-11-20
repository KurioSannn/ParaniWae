import type { AdapterHandlers, AsyncLandmarkerAdapter, InitInfo } from "@/features/practice/async-adapter";
import { syntheticFrame, type SyntheticScenario } from "@/features/practice/synthetic-pose";

/** Engine SIMULASI: menghasilkan landmark sintetis menurut skenario. Tidak menjalankan model, tidak memproses gambar. */
export class SyntheticLandmarkAdapter implements AsyncLandmarkerAdapter {
  readonly name = "synthetic-simulation";
  private h: AdapterHandlers | null = null;
  private paused = false;
  private disposed = false;
  constructor(private readonly scenario: (i: number, t: number) => SyntheticScenario = (i) => (i < 6 ? "waiting" : "full"), private readonly delayMs = 20) {}
  setHandlers(h: AdapterHandlers): void { this.h = h; }
  async init(): Promise<InitInfo> { return { initMs: 1, startupMs: 0, delegate: null, library: "synthetic" }; }
  submit(bitmap: ImageBitmap, timestampMs: number, frameIndex: number, id: number): void {
    const w = bitmap.width, hgt = bitmap.height;
    bitmap.close(); // tidak ada gambar yang dipakai
    if (this.disposed) return;
    if (this.paused) { this.h?.onDropped({ id, reason: "paused" }); return; }
    setTimeout(() => {
      if (this.disposed) return;
      this.h?.onResult({ id, procMs: this.delayMs, frame: syntheticFrame(this.scenario(frameIndex, timestampMs), frameIndex, timestampMs, w, hgt) });
    }, this.delayMs);
  }
  pause(): void { this.paused = true; }
  resume(): void { this.paused = false; }
  async dispose(): Promise<void> { this.disposed = true; }
}
