/** Pengukuran kinerja pipeline CV di perangkat pengguna (tidak ada angka yang dikarang). */
export interface CamMetrics {
  initMs: number | null;
  frames: number;
  meanMs: number | null;
  p95Ms: number | null;
  delegate: string | null;
  videoWidth: number | null;
  videoHeight: number | null;
}

export class FrameTimer {
  private samples: number[] = [];
  constructor(private readonly cap = 300) {}
  add(ms: number): void { this.samples.push(ms); if (this.samples.length > this.cap) this.samples.shift(); }
  get count(): number { return this.samples.length; }
  mean(): number | null {
    return this.samples.length ? this.samples.reduce((a, b) => a + b, 0) / this.samples.length : null;
  }
  p95(): number | null {
    if (!this.samples.length) return null;
    const s = [...this.samples].sort((a, b) => a - b);
    return s[Math.min(s.length - 1, Math.ceil(0.95 * s.length) - 1)];
  }
  reset(): void { this.samples = []; }
}

/** Jam monotonik untuk pengukuran (dipanggil dari event handler/loop, bukan saat render). */
export function nowMs(): number {
  return performance.now();
}
