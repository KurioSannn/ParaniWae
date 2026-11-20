/**
 * REGRESI PRIVASI (statis): modul CV tidak boleh punya jalur untuk mengirim/menyimpan/mencatat frame atau landmark.
 * Pemindaian sumber — pelengkap tes jaringan Playwright (tidak ada request mutasi, tidak ada storage).
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const ROOT = join(__dirname);
const files = (dir: string): string[] =>
  readdirSync(dir).flatMap((f) => (statSync(join(dir, f)).isDirectory() ? files(join(dir, f)) : [join(dir, f)]))
    .filter((f) => /\.(ts|tsx)$/.test(f) && !/\.test\.tsx?$/.test(f));
const strip = (s: string) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

const FORBIDDEN: [RegExp, string][] = [
  [/\bfetch\s*\(/, "fetch()"], [/XMLHttpRequest/, "XMLHttpRequest"], [/sendBeacon/, "sendBeacon"],
  [/WebSocket/, "WebSocket"], [/EventSource/, "EventSource"],
  [/localStorage|sessionStorage|indexedDB|caches\./, "penyimpanan browser"],
  [/document\.cookie/, "cookie"], [/console\.(log|info|debug|error)/, "console.*"],
  [/toDataURL|toBlob|convertToBlob|MediaRecorder|captureStream/, "perekaman/ekspor frame"],
  [/FormData/, "FormData (unggahan)"], [/clientRequest|apiGet|apiBaseUrl/, "klien API aplikasi"],
];

describe("privasi modul CV (features/practice + CameraCheck)", () => {
  const targets = [...files(ROOT), join(ROOT, "../../components/CameraCheck.tsx"), join(ROOT, "../../components/BenchmarkRunner.tsx"), join(ROOT, "../../components/PracticeStudio.tsx")];
  for (const f of targets) {
    const name = f.replace(join(ROOT, "../../"), "");
    it(`${name} tidak memuat jalur kirim/simpan/log`, () => {
      let src: string;
      try { src = strip(readFileSync(f, "utf8")); } catch { return; } // berkas opsional
      // PracticeStudio boleh memakai HANYA lib/practice-api (metadata sesi); klien API generik tetap dilarang.
      const hits = FORBIDDEN.filter(([re]) => re.test(src)).map(([, n]) => n);
      // console.warn hanya diizinkan di worker (menghitung warning internal pustaka; tidak mencatat data)
      if (/console\.warn/.test(src) && !name.endsWith("landmarker.worker.ts")) hits.push("console.warn");
      expect(hits, `${name}: ${hits.join(", ")}`).toEqual([]);
    });
  }
  it("kamera selalu audio:false", () => {
    const src = readFileSync(join(ROOT, "camera.ts"), "utf8");
    expect(src).toMatch(/audio:\s*false/);
    expect(src).not.toMatch(/audio:\s*true/);
  });
  it("versi MediaPipe di config sinkron dengan package.json", () => {
    const pkg = JSON.parse(readFileSync(join(ROOT, "../../../package.json"), "utf8"));
    const cfg = readFileSync(join(ROOT, "config.ts"), "utf8");
    expect(cfg).toContain(`MEDIAPIPE_VERSION = "${pkg.dependencies["@mediapipe/tasks-vision"]}"`);
  });
  it("semua URL aset MediaPipe berupa path same-origin", () => {
    const cfg = readFileSync(join(ROOT, "config.ts"), "utf8");
    const urls = [...cfg.matchAll(/"(\/mediapipe\/[^"]+)"/g)].map((m) => m[1]);
    expect(urls.length).toBeGreaterThanOrEqual(4);
    expect(cfg).not.toMatch(/https?:\/\//);
  });
});

describe("batas data Practice Studio", () => {
  it("lib/practice-api hanya memanggil endpoint /practice-sessions dan tidak menerima landmark/frame", () => {
    const src = readFileSync(join(ROOT, "../../lib/practice-api.ts"), "utf8");
    const paths = [...src.matchAll(/"(\/[a-z-]+[^"]*)"|`(\/[a-z-]+[^`]*)`/g)].map((m) => m[1] ?? m[2]);
    expect(paths.length).toBeGreaterThan(0);
    for (const p of paths) expect(p.startsWith("/practice-sessions")).toBe(true);
    expect(src).not.toMatch(/landmark|frame:|bitmap|video/i);
  });
  it("PracticeStudio mengimpor klien jaringan HANYA lewat practice-api", () => {
    const src = readFileSync(join(ROOT, "../../components/PracticeStudio.tsx"), "utf8");
    expect(src).toMatch(/from "@\/lib\/practice-api"/);
    expect(src).not.toMatch(/client-api|from "@\/lib\/api"/);
  });
});
