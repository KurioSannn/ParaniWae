/**
 * Audit visual: screenshot semua halaman utama pada 3 viewport + axe-core DENGAN CSS ter-render
 * (termasuk kontras warna) + deteksi overflow horizontal + error konsol/jaringan.
 */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Browser, type BrowserContext } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { DEMO_PW, watch } from "./helpers";

const VIEWPORTS = { desktop: { width: 1440, height: 900 }, tablet: { width: 768, height: 1024 }, mobile: { width: 390, height: 844 } } as const;
type Role = "anon" | "learner" | "curator" | "admin";
const ACCOUNT: Record<Exclude<Role, "anon">, string> = { learner: "demo-pelajar@silatara.test", curator: "demo-kurator@silatara.test", admin: "demo-admin@silatara.test" };

const PAGES: { name: string; path: string; role: Role }[] = [
  { name: "home", path: "/", role: "anon" },
  { name: "masuk", path: "/masuk", role: "anon" },
  { name: "daftar", path: "/daftar", role: "anon" },
  { name: "lupa-sandi", path: "/lupa-sandi", role: "anon" },
  { name: "heritage", path: "/heritage", role: "anon" },
  { name: "heritage-empty", path: "/heritage?q=zzzzzz", role: "anon" },
  { name: "heritage-detail", path: "/heritage/demo-tradisi", role: "anon" },
  { name: "not-found", path: "/heritage/tidak-ada", role: "anon" },
  { name: "community", path: "/community", role: "anon" },
  { name: "community-detail", path: "/community/demo-perguruan-contoh", role: "anon" },
  { name: "academy", path: "/academy", role: "anon" },
  { name: "course-detail", path: "/academy/courses/demo-kurikulum-a", role: "anon" },
  { name: "status", path: "/status", role: "anon" },
  { name: "dashboard", path: "/app", role: "learner" },
  { name: "lesson", path: "/app/courses/demo-kurikulum-a/lessons/demo-referensi", role: "learner" },
  { name: "progress", path: "/app/progress", role: "learner" },
  { name: "camera-check", path: "/app/practice/camera-check", role: "learner" },
  { name: "manage-home", path: "/app/manage", role: "curator" },
  { name: "manage-list", path: "/app/manage/courses", role: "curator" },
  { name: "manage-new", path: "/app/manage/courses/new", role: "curator" },
  { name: "admin", path: "/app/admin", role: "admin" },
];

const states = new Map<Role, Awaited<ReturnType<BrowserContext["storageState"]>>>();
async function stateFor(browser: Browser, role: Role) {
  if (role === "anon") return undefined;
  if (!states.has(role)) {
    const c = await browser.newContext();
    const p = await c.newPage();
    const r = await p.request.post("/api/v1/auth/login", { data: { email: ACCOUNT[role], password: DEMO_PW } });
    expect(r.ok()).toBeTruthy();
    states.set(role, await c.storageState());
    await c.close();
  }
  return states.get(role);
}

for (const [vpName, vp] of Object.entries(VIEWPORTS)) {
  for (const pg of PAGES) {
    test(`${vpName} · ${pg.name}`, async ({ browser, baseURL }) => {
      const ctx = await browser.newContext({ viewport: vp, baseURL, storageState: await stateFor(browser, pg.role) });
      const page = await ctx.newPage();
      const w = watch(page, new URL(baseURL!).origin);
      const res = await page.goto(pg.path);
      await page.waitForLoadState("networkidle");
      mkdirSync(`artifacts/screenshots/${vpName}`, { recursive: true });
      await page.screenshot({ path: `artifacts/screenshots/${vpName}/${pg.name}.png`, fullPage: true });

      if (pg.name !== "not-found") expect(res!.status(), "status HTTP").toBe(200);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow, "overflow horizontal (px)").toBeLessThanOrEqual(0);
      const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
      const v = axe.violations.map((x) => `${x.id} [${x.impact}] x${x.nodes.length}: ${x.nodes.slice(0, 2).map((n) => n.target.join(" ")).join(" | ")}`);
      expect(v, "pelanggaran axe (CSS aktif, kontras diperiksa)").toEqual([]);
      // Halaman not-found sengaja 404; Chromium mencatat 404 dokumen sebagai error konsol.
      const errs = pg.name === "not-found" ? w.consoleErrors.filter((e) => !/status of 404/.test(e)) : w.consoleErrors;
      expect(errs, "error konsol").toEqual([]);
      expect(w.external, "request lintas-origin").toEqual([]);
      await ctx.close();
    });
  }
}

test("menu seluler terbuka (390px) dapat dioperasikan", async ({ browser, baseURL }) => {
  const ctx = await browser.newContext({ viewport: VIEWPORTS.mobile, baseURL });
  const page = await ctx.newPage();
  await page.goto("/");
  await page.getByLabel("Buka menu").click();
  await expect(page.getByRole("navigation", { name: "Utama (seluler)" })).toBeVisible();
  mkdirSync("artifacts/screenshots/mobile", { recursive: true });
  await page.screenshot({ path: "artifacts/screenshots/mobile/menu-open.png" });
  await page.getByRole("navigation", { name: "Utama (seluler)" }).getByRole("link", { name: "Akademi" }).click();
  await expect(page).toHaveURL(/\/academy/);
  await ctx.close();
});
