import { Series } from "@/features/practice/stats";

export interface ResponsivenessSummary {
  /** Jeda event-loop (setTimeout 10 ms vs aktual): mengukur PEMBLOKIRAN MAIN THREAD, terpisah dari compositor. */
  loopLag: { n: number; p95Ms: number | null; maxMs: number | null };
  frames: number;
  meanGapMs: number | null;
  p95GapMs: number | null;
  maxGapMs: number | null;
  longTasks: { count: number; totalMs: number; supported: boolean };
}

const PROBE_MS = 10;
type Raf = (cb: (t: number) => void) => number;
type CancelRaf = (h: number) => void;

/**
 * Mengukur responsivitas dengan TIGA sinyal berbeda (jangan dicampur):
 * 1. jarak antar requestAnimationFrame (≈16,7 ms bila lancar) — mencerminkan kehalusan visual; dapat membesar
 *    karena main thread terblokir ATAU compositor/GPU kewalahan (mis. WebGL software di headless);
 * 2. jeda event-loop (setTimeout) — hanya membesar bila MAIN THREAD terblokir;
 * 3. Long Tasks (>50 ms) bila browser mendukung.
 */
export class ResponsivenessMonitor {
  private gaps = new Series(5000);
  private last: number | null = null;
  private handle: number | null = null;
  private lt = { count: 0, totalMs: 0 };
  private observer: PerformanceObserver | null = null;
  private ltSupported = false;
  private lag = new Series(20000);
  private lagTimer: ReturnType<typeof setTimeout> | null = null;
  private lastProbe: number | null = null;

  constructor(
    private readonly raf: Raf = (cb) => requestAnimationFrame(cb),
    private readonly cancel: CancelRaf = (h) => cancelAnimationFrame(h),
    private readonly setT: (cb: () => void, ms: number) => ReturnType<typeof setTimeout> = (cb, ms) => setTimeout(cb, ms),
    private readonly clearT: (h: ReturnType<typeof setTimeout>) => void = (h) => clearTimeout(h),
    private readonly clock: () => number = () => performance.now(),
  ) {}

  start(): void {
    if (this.handle !== null) return;
    this.gaps.reset(); this.last = null; this.lt = { count: 0, totalMs: 0 };
    try {
      this.observer = new PerformanceObserver((list) => {
        for (const e of list.getEntries()) { this.lt.count += 1; this.lt.totalMs += e.duration; }
      });
      this.observer.observe({ entryTypes: ["longtask"] });
      this.ltSupported = true;
    } catch {
      this.ltSupported = false;
    }
    const tick = (t: number) => {
      if (this.last !== null) this.gaps.add(t - this.last);
      this.last = t;
      this.handle = this.raf(tick);
    };
    this.handle = this.raf(tick);
    this.lag.reset(); this.lastProbe = null;
    const probe = () => {
      const t = this.clock();
      if (this.lastProbe !== null) this.lag.add(Math.max(0, t - this.lastProbe - PROBE_MS));
      this.lastProbe = t;
      this.lagTimer = this.setT(probe, PROBE_MS);
    };
    this.lagTimer = this.setT(probe, PROBE_MS);
  }

  stop(): ResponsivenessSummary {
    if (this.handle !== null) this.cancel(this.handle);
    this.handle = null;
    if (this.lagTimer !== null) this.clearT(this.lagTimer);
    this.lagTimer = null;
    this.observer?.disconnect();
    this.observer = null;
    return this.summary();
  }

  summary(): ResponsivenessSummary {
    return {
      loopLag: { n: this.lag.n, p95Ms: this.lag.p95(), maxMs: this.lag.max() },
      frames: this.gaps.n, meanGapMs: this.gaps.mean(), p95GapMs: this.gaps.p95(), maxGapMs: this.gaps.max(),
      longTasks: { ...this.lt, supported: this.ltSupported },
    };
  }
}
