/** Seri sampel sederhana untuk mean/median/p95 (nearest-rank). Tidak ada angka yang dikarang. */
export class Series {
  private v: number[] = [];
  constructor(private readonly cap = 1000) {}
  add(x: number): void { this.v.push(x); if (this.v.length > this.cap) this.v.shift(); }
  get n(): number { return this.v.length; }
  mean(): number | null { return this.v.length ? this.v.reduce((a, b) => a + b, 0) / this.v.length : null; }
  pct(p: number): number | null {
    if (!this.v.length) return null;
    const s = [...this.v].sort((a, b) => a - b);
    return s[Math.min(s.length - 1, Math.max(0, Math.ceil(p * s.length) - 1))];
  }
  median(): number | null { return this.v.length ? this.pctMid() : null; }
  private pctMid(): number {
    const s = [...this.v].sort((a, b) => a - b);
    const m = s.length >> 1;
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  }
  p95(): number | null { return this.pct(0.95); }
  max(): number | null { return this.v.length ? Math.max(...this.v) : null; }
  last(n: number): number[] { return this.v.slice(-n); }
  reset(): void { this.v = []; }
  summary() { return { n: this.n, mean: this.mean(), median: this.median(), p95: this.p95(), max: this.max() }; }
}
