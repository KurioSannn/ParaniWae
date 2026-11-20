import { describe, expect, it } from "vitest";
import { syntheticFrame as fixtureFrame, syntheticPose } from "@/features/practice/fixtures";
import { squarePad, unpadLandmark } from "@/features/practice/letterbox";
import { drawSkeleton, fitVideoBox, HAND_CONNECTIONS, POSE_BODY_CONNECTIONS, POSE_DRAWN_POINTS, projectLandmark, strokeScale, type DrawCtx } from "@/features/practice/skeleton";
import { syntheticFrame, syntheticStandingPose } from "@/features/practice/synthetic-pose";

class RecCtx implements DrawCtx {
  strokeStyle = ""; fillStyle = ""; lineWidth = 0; lineCap: CanvasLineCap = "butt"; globalAlpha = 1;
  moves: [number, number][] = []; lines: [number, number][] = []; arcs: [number, number, number][] = []; cleared: number[][] = [];
  clearRect(x: number, y: number, w: number, h: number) { this.cleared.push([x, y, w, h]); }
  beginPath() {} stroke() {} fill() {} setLineDash() {}
  moveTo(x: number, y: number) { this.moves.push([x, y]); } lineTo(x: number, y: number) { this.lines.push([x, y]); }
  arc(x: number, y: number, r: number) { this.arcs.push([x, y, r]); }
}

describe("projectLandmark — koordinat tepat pada berbagai aspect ratio", () => {
  it.each([
    ["4:3", 640, 480], ["16:9", 1280, 720], ["1:1", 480, 480], ["9:16 (potret)", 360, 640], ["layar kecil", 320, 240],
  ])("%s: titik tengah & sudut jatuh pada piksel yang benar", (_n, w, h) => {
    expect(projectLandmark({ x: 0.5, y: 0.5 }, { width: w, height: h })).toEqual({ x: w / 2, y: h / 2 });
    expect(projectLandmark({ x: 0, y: 0 }, { width: w, height: h })).toEqual({ x: 0, y: 0 });
    expect(projectLandmark({ x: 1, y: 1 }, { width: w, height: h })).toEqual({ x: w, y: h });
    expect(projectLandmark({ x: 0.25, y: 0.75 }, { width: w, height: h })).toEqual({ x: w * 0.25, y: h * 0.75 });
  });
  it("mirror horizontal membalik x saja", () => {
    expect(projectLandmark({ x: 0.2, y: 0.3 }, { width: 100, height: 50 }, { mirror: true })).toEqual({ x: 80, y: 15 });
  });
  it("posisi relatif invarian terhadap ukuran viewport (perubahan ukuran tidak menggeser landmark)", () => {
    const l = { x: 0.37, y: 0.61 };
    for (const [w, h] of [[640, 480], [320, 240], [1280, 960], [800, 600]]) {
      const p = projectLandmark(l, { width: w, height: h });
      expect(p.x / w).toBeCloseTo(0.37); expect(p.y / h).toBeCloseTo(0.61);
    }
  });
});

describe("fitVideoBox — area video mengikuti rasio asli tanpa crop", () => {
  it.each([[640, 480], [1280, 720], [480, 640]])("rasio %ix%i dipertahankan dan tidak melebihi batas", (vw, vh) => {
    const b = fitVideoBox(vw, vh, 900, 500);
    expect(b.width / b.height).toBeCloseTo(vw / vh);
    expect(b.height).toBeLessThanOrEqual(500 + 1e-6); expect(b.width).toBeLessThanOrEqual(900 + 1e-6);
  });
  it("sebelum metadata video diketahui memakai 4:3 sementara", () => { expect(fitVideoBox(0, 0, 400, 500)).toEqual({ width: 400, height: 300 }); });
});

describe("drawSkeleton", () => {
  const size = { width: 640, height: 480 };
  it("menggambar tulang untuk titik terlihat pada koordinat proyeksi yang tepat", () => {
    const ctx = new RecCtx();
    const f = fixtureFrame({ poses: [syntheticPose()] });
    const r = drawSkeleton(ctx, f, size);
    expect(r.bones).toBe(POSE_BODY_CONNECTIONS.length);
    expect(ctx.cleared[0]).toEqual([0, 0, 640, 480]);
    const lm = f.poses[0].landmarks;
    const a = lm[11], b = lm[12]; // bahu kiri-kanan harus muncul sebagai garis moveTo/lineTo
    const has = (x: number, y: number, arr: [number, number][]) => arr.some(([px, py]) => Math.abs(px - x) < 1e-6 && Math.abs(py - y) < 1e-6);
    expect(has(a.x * 640, a.y * 480, ctx.moves)).toBe(true);
    expect(has(b.x * 640, b.y * 480, ctx.lines) || has(b.x * 640, b.y * 480, ctx.moves)).toBe(true);
  });
  it("mirror: x titik digambar terbalik, y tetap", () => {
    const ctx = new RecCtx();
    const f = syntheticFrame("full", 0, 0);
    drawSkeleton(ctx, f, size, { mirror: true });
    const nose = f.poses[0].landmarks[0];
    expect(ctx.arcs.some(([x, y]) => Math.abs(x - (1 - nose.x) * 640) < 1e-6 && Math.abs(y - nose.y * 480) < 1e-6)).toBe(true);
  });
  it("landmark berkonfiden rendah: tulang tidak digambar & titik redup (kualitas terlihat apa adanya)", () => {
    const ctx = new RecCtx();
    const r = drawSkeleton(ctx, syntheticFrame("partial", 0, 0), size);
    expect(r.bones).toBeLessThan(POSE_BODY_CONNECTIONS.length);
    expect(r.points).toBe(POSE_DRAWN_POINTS.length);
  });
  it("tanpa pose: hanya membersihkan kanvas", () => {
    const ctx = new RecCtx();
    expect(drawSkeleton(ctx, syntheticFrame("waiting", 0, 0), size)).toEqual({ points: 0, bones: 0 });
    expect(ctx.arcs).toHaveLength(0);
  });
  it("koordinat NaN tidak digambar (tidak merusak kanvas)", () => {
    const ctx = new RecCtx();
    const f = syntheticFrame("full", 0, 0);
    f.poses[0].landmarks[11] = { x: NaN, y: 0.2, z: 0, visibility: 1 };
    expect(() => drawSkeleton(ctx, f, size)).not.toThrow();
    expect(ctx.arcs.every(([x, y]) => Number.isFinite(x) && Number.isFinite(y))).toBe(true);
  });
  it("tangan hanya digambar bila diminta; titik/tulang tangan resmi (21)", () => {
    const f = syntheticFrame("full", 0, 0);
    f.hands = [{ handedness: "Left", score: 0.9, landmarks: Array.from({ length: 21 }, (_, i) => ({ x: 0.7, y: 0.4 + i * 0.005, z: 0 })) }];
    expect(drawSkeleton(new RecCtx(), f, size).points).toBe(POSE_DRAWN_POINTS.length);
    expect(drawSkeleton(new RecCtx(), f, size, { showHands: true }).points).toBe(POSE_DRAWN_POINTS.length + 21);
    expect(HAND_CONNECTIONS).toHaveLength(21);
  });
  it("orang tambahan digambar redup; ketebalan garis proporsional terhadap resolusi", () => {
    const a = strokeScale({ width: 640, height: 480 }), b = strokeScale({ width: 1920, height: 1080 });
    expect(b.bone).toBeGreaterThan(a.bone);
  });
  it("koneksi mengacu pada indeks MediaPipe yang valid (0..32) dan tidak memuat titik wajah rinci", () => {
    for (const [a, b] of POSE_BODY_CONNECTIONS) { expect(a).toBeGreaterThanOrEqual(11); expect(b).toBeLessThanOrEqual(32); }
    for (const i of POSE_DRAWN_POINTS) expect([1, 2, 3, 4, 5, 6, 9, 10]).not.toContain(i);
  });
});

describe("letterbox square-pad: pemetaan balik koordinat", () => {
  it("4:3 -> persegi: padding vertikal; titik tengah tetap di tengah", () => {
    expect(squarePad(640, 480)).toEqual({ size: 640, padX: 0, padY: 80 });
    const back = unpadLandmark({ x: 0.5, y: 0.5, z: 0 }, 640, 480);
    expect(back.x).toBeCloseTo(0.5); expect(back.y).toBeCloseTo(0.5);
  });
  it("tepi gambar asli memetakan tepat ke 0 dan 1", () => {
    const top = unpadLandmark({ x: 0, y: 80 / 640, z: 0 }, 640, 480), bottom = unpadLandmark({ x: 1, y: 560 / 640, z: 0 }, 640, 480);
    expect(top.y).toBeCloseTo(0); expect(bottom.y).toBeCloseTo(1); expect(bottom.x).toBeCloseTo(1);
  });
  it("potret & 16:9 juga benar; round-trip pad->unpad konsisten", () => {
    for (const [w, h] of [[360, 640], [1280, 720]]) {
      const { size, padX, padY } = squarePad(w, h);
      const orig = { x: 0.3, y: 0.8, z: 0 };
      const inSquare = { ...orig, x: (orig.x * w + padX) / size, y: (orig.y * h + padY) / size };
      const back = unpadLandmark(inSquare, w, h);
      expect(back.x).toBeCloseTo(orig.x); expect(back.y).toBeCloseTo(orig.y);
    }
  });
});

describe("synthetic-pose: data simulasi", () => {
  it("33 landmark, bergerak halus (tanpa NaN), skenario sesuai", () => {
    const p = syntheticStandingPose({ t: 1234 });
    expect(p.landmarks).toHaveLength(33);
    expect(p.landmarks.every((l) => Number.isFinite(l.x) && l.x >= 0 && l.x <= 1 && l.y >= 0 && l.y <= 1.2)).toBe(true);
    expect(syntheticFrame("multiple", 0, 0).poses).toHaveLength(2);
    expect(syntheticFrame("waiting", 0, 0).poses).toHaveLength(0);
  });
});
