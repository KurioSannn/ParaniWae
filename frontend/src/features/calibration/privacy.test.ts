/**
 * REGRESI PRIVASI/INTEGRITAS (statis): Calibration Workspace tidak menyimpan/mengirim landmark atau frame;
 * hanya timestamp + provenance anotasi yang dikirim lewat klien API, dan tidak ada skor/ambang/akurasi.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const strip = (s: string) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");
const dir = __dirname;
const all = (d: string): string[] => readdirSync(d).flatMap((f) => (statSync(join(d, f)).isDirectory() ? all(join(d, f)) : [join(d, f)])).filter((f) => /\.(ts|tsx)$/.test(f) && !/\.test\.tsx?$/.test(f));
const component = join(dir, "../../components/CalibrationWorkspace.tsx");

describe("privasi Calibration Workspace", () => {
  for (const f of [...all(dir), component]) {
    const name = f.replace(join(dir, "../../"), "");
    it(`${name}: tanpa ekspor frame, penyimpanan browser, atau pengiriman jaringan langsung`, () => {
      const src = strip(readFileSync(f, "utf8"));
      const hits = [
        [/toDataURL|toBlob|convertToBlob|MediaRecorder|captureStream/, "ekspor/perekaman frame"],
        [/localStorage|sessionStorage|indexedDB|caches\./, "penyimpanan browser"],
        [/\bfetch\s*\(|XMLHttpRequest|sendBeacon|WebSocket/, "jaringan langsung"],
        [/FormData/, "unggahan"], [/console\.(log|info|debug|error)/, "console.*"],
      ].filter(([re]) => (re as RegExp).test(src)).map(([, n]) => n);
      expect(hits, `${name}: ${hits.join(", ")}`).toEqual([]);
    });
  }
  it("komponen hanya memanggil klien API untuk anotasi; payload tidak memuat landmark/frame/poses", () => {
    const src = strip(readFileSync(component, "utf8"));
    const calls = [...src.matchAll(/await clientRequest(?:<[^>]*>)?\(([^;]*?)\);/g)].map((m) => m[1]);
    expect(calls.length).toBeGreaterThan(0);
    for (const c of calls) expect(c).not.toMatch(/landmark|poses|\bframe\b|bitmap/i);
    for (const c of calls) expect(c).toMatch(/\/studio\/(movements\/\$\{movementId\}\/annotations|annotations\/)/);
  });
  it("tidak ada skor, ambang, kemiripan, atau koreksi otomatis di kode kalibrasi", () => {
    for (const f of [...all(dir), component]) {
      const src = strip(readFileSync(f, "utf8"));
      expect(src, f).not.toMatch(/\b(score|similarity|threshold|accuracy|akurasi_skor|ground_truth)\b/i);
    }
  });
});
