// Pemeriksaan aksesibilitas statis (axe-core) pada HTML hasil render server. Kontras warna TIDAK diperiksa
// (jsdom tidak merender CSS). Bukan pengganti uji manual dengan pembaca layar/keyboard.
import { JSDOM } from "jsdom";
import axe from "axe-core";

const base = process.env.A11Y_BASE_URL ?? "http://localhost:3000";
const login = await fetch(`${base}/api/v1/auth/login`, {
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "demo-kurator@silatara.test", password: process.env.DEMO_USER_PASSWORD ?? "demo-sandi-12345" }),
});
const cookie = login.headers.getSetCookie().map((c) => c.split(";")[0]).join("; ");
const pages = ["/", "/heritage", "/heritage/demo-tradisi", "/community", "/community/demo-perguruan-contoh", "/academy",
  "/academy/courses/demo-kurikulum-a", "/masuk", "/daftar", "/app", "/app/progress", "/app/courses/demo-kurikulum-a/lessons/demo-orientasi",
  "/app/manage", "/app/manage/courses", "/app/manage/courses/new", "/app/admin", "/app/practice/camera-check"];
let bad = 0;
for (const p of pages) {
  const res = await fetch(base + p, { headers: { cookie } });
  const html = await res.text();
  const dom = new JSDOM(html, { runScripts: "outside-only" });
  dom.window.eval(axe.source);
  const r = await dom.window.axe.run(dom.window.document, { rules: { "color-contrast": { enabled: false } } });
  const v = r.violations;
  console.log(`${v.length ? "FAIL" : "PASS"}  ${res.status} ${p}${v.length ? " :: " + v.map((x) => `${x.id}(${x.nodes.length})`).join(", ") : ""}`);
  bad += v.length;
}
process.exit(bad ? 1 : 0);
