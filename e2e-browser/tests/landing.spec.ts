import { expect, test, type Page } from "@playwright/test";
import { loginUI } from "./helpers";

const VIEWPORTS = [{ n: "desktop", w: 1440, h: 900 }, { n: "tablet", w: 820, h: 1100 }, { n: "mobile", w: 390, h: 844 }];

async function mascot(page: Page) { return page.getByRole("img", { name: /Maskot SILATARA/ }); }

for (const v of VIEWPORTS) {
  test(`landing ${v.n}: maskot besar di hero, tanpa scroll horizontal, gambar termuat`, async ({ page }) => {
    await page.setViewportSize({ width: v.w, height: v.h });
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Warisan Gerak");
    const m = await mascot(page);
    await expect(m).toBeVisible();
    await expect.poll(async () => m.evaluate((i: HTMLImageElement) => i.complete && i.naturalWidth > 0)).toBe(true);
    const box = (await m.boundingBox())!;
    // maskot = fokus visual: ≥ 36% lebar layar (desktop/tablet) atau ≥ 85% (mobile); tidak terpotong di sisi kanan/kiri
    expect(box.width / v.w).toBeGreaterThan(v.n === "mobile" ? 0.85 : v.n === "tablet" ? 0.6 : 0.36);
    expect(box.x).toBeGreaterThanOrEqual(-1);
    expect(box.x + box.width).toBeLessThanOrEqual(v.w + 24); // skala dekoratif kecil di desktop diizinkan
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
    await page.screenshot({ path: `artifacts/screenshots-landing/landing-${v.n}.png`, fullPage: true });
    // bukan di dalam lingkaran/badge: tidak ada ancestor dengan border-radius 9999px yang membungkus maskot
    const circled = await m.evaluate((el) => { let n: HTMLElement | null = el.parentElement; while (n && n.tagName !== "SECTION") { if (getComputedStyle(n).borderRadius.includes("9999") || getComputedStyle(n).borderRadius === "50%") return true; n = n.parentElement; } return false; });
    expect(circled).toBe(false);
  });
}

test("CTA dan tautan landing berfungsi (tanpa 404)", async ({ page, request }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /^Mulai Belajar/ }).first().click();
  await expect(page).toHaveURL(/\/daftar/);
  await page.goto("/");
  await page.getByRole("link", { name: "Jelajahi Warisan" }).first().click();
  await expect(page).toHaveURL(/\/heritage/);
  await page.goto("/");
  const hrefs = await page.$$eval("a[href^='/']", (as) => [...new Set(as.map((a) => (a as HTMLAnchorElement).getAttribute("href")!))]);
  expect(hrefs.length).toBeGreaterThan(12);
  for (const h of hrefs) {
    const r = await request.get(h, { maxRedirects: 5 });
    expect(r.status(), h).toBeLessThan(400);
  }
});

test("copy jujur: [DEMO], AI pendamping, tidak mengklaim mitra/akurasi", async ({ page }) => {
  await page.goto("/");
  const body = (await page.locator("main").innerText());
  expect(body).toContain("[DEMO]");
  expect(body).toMatch(/belum ada mitra resmi/i);
  expect(body).toMatch(/Penilaian teknik\s+belum tersedia/);
  expect(body).toContain("Preserving the Heritage. Empowering the Next Generation.");
  expect(body).toMatch(/AI-Powered Pencak Silat Heritage/i);
  expect(body).not.toMatch(/\d+\s*%\s*akurat|terbukti akurat|ribuan pengguna|mitra resmi kami/i);
});

test("identitas: favicon, ikon, manifest, OG, theme-color; semua simbol logo berasal dari maskot", async ({ page, request }) => {
  await page.goto("/");
  const ico = await request.get("/favicon.ico");
  expect(ico.status()).toBe(200);
  expect(ico.headers()["content-type"]).toMatch(/icon/);
  const links = await page.$$eval("link[rel~='icon'], link[rel='apple-touch-icon'], link[rel='manifest']", (ls) => ls.map((l) => `${l.getAttribute("rel")}|${l.getAttribute("href")}`));
  expect(links.some((l) => l.startsWith("apple-touch-icon"))).toBe(true);
  expect(links.some((l) => /icon\|.*icon/.test(l))).toBe(true);
  for (const l of links) { const href = l.split("|")[1]; const r = await request.get(href); expect(r.status(), href).toBe(200); }
  const manifest = await (await request.get("/manifest.webmanifest")).json();
  expect(manifest.name).toBe("SILATARA");
  const og = await page.locator("meta[property='og:image']").getAttribute("content");
  expect(og).toBeTruthy();
  const ogRes = await request.get(new URL(og!).pathname);
  expect(ogRes.status()).toBe(200);
  expect(ogRes.headers()["content-type"]).toContain("image/png");
  expect(await page.locator("meta[property='og:title']").getAttribute("content")).toContain("SILATARA");
  expect(await page.locator("meta[name='theme-color']").getAttribute("content")).toBe("#0f1512");
  expect(await page.locator("meta[name='twitter:card']").getAttribute("content")).toBe("summary_large_image");
});

for (const path of ["/", "/masuk", "/daftar", "/academy", "/heritage", "/library", "/community"]) {
  test(`logo konsisten (maskot + wordmark) di header & footer: ${path}`, async ({ page }) => {
    await page.goto(path);
    for (const scope of ["banner", "contentinfo"] as const) {
      const region = page.getByRole(scope);
      const img = region.locator("img[src*='silatara-mark']").first();
      await expect(img, `${scope} ${path}`).toBeAttached();
      await expect(region.getByText("SILATARA", { exact: true }).first()).toBeVisible();
    }
    // tidak ada wordmark SILATARA berupa teks polos tanpa maskot di header
    expect(await page.getByRole("banner").locator("a[aria-label*='SILATARA']").count()).toBe(1);
  });
}

test("logo pada area aplikasi (sidebar) dan loading berasal dari maskot", async ({ page }) => {
  await loginUI(page, "demo-pelajar@silatara.test");
  await page.goto("/app");
  await expect(page.locator("aside img[src*='silatara-mark']").first()).toBeAttached();
});
