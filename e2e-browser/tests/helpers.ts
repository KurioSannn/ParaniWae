import { expect, type Page, type APIRequestContext } from "@playwright/test";

export const DEMO_PW = process.env.DEMO_USER_PASSWORD ?? "demo-sandi-12345";
export const uniq = () => Math.random().toString(36).slice(2, 10);

export async function loginUI(page: Page, email: string, password = DEMO_PW, next?: string) {
  await page.goto(next ? `/masuk?next=${encodeURIComponent(next)}` : "/masuk");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Kata sandi").fill(password);
  await page.getByRole("button", { name: "Masuk" }).click();
  // Tunggu hasil: berpindah dari /masuk (sukses) ATAU pesan galat muncul (gagal). Mencegah race dengan goto berikutnya.
  await Promise.race([
    page.waitForURL((u) => !u.pathname.startsWith("/masuk"), { timeout: 15_000 }).catch(() => undefined),
    page.getByRole("alert").filter({ hasText: /\S/ }).first().waitFor({ timeout: 15_000 }).catch(() => undefined),
  ]);
}

/** Ambil token terbaru untuk email dari kotak surat DEV (sink). */
export async function latestToken(request: APIRequestContext, email: string, needle: string): Promise<string> {
  for (let i = 0; i < 10; i++) {
    const r = await request.get("/api/v1/dev/mailbox");
    expect(r.ok()).toBeTruthy();
    const mails = (await r.json()) as { to: string; body: string }[];
    const m = mails.find((x) => x.to === email && x.body.includes(needle));
    if (m) return /token=([\w-]+)/.exec(m.body)![1];
    await new Promise((res) => setTimeout(res, 300));
  }
  throw new Error(`email ke ${email} tidak ditemukan`);
}

/** Pantau error konsol & request gagal / 4xx-5xx / lintas-origin sepanjang test. */
export function watch(page: Page, origin: string) {
  const consoleErrors: string[] = [], badResponses: string[] = [], external: string[] = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
  page.on("pageerror", (e) => consoleErrors.push(`pageerror: ${e.message}`));
  page.on("requestfailed", (r) => badResponses.push(`FAILED ${r.url()} ${r.failure()?.errorText}`));
  page.on("response", (r) => { if (r.status() >= 400) badResponses.push(`${r.status()} ${r.url()}`); });
  page.on("request", (r) => { const u = new URL(r.url()); if (!["data:", "blob:"].includes(u.protocol) && u.origin !== origin) external.push(r.url()); });
  return { consoleErrors, badResponses, external };
}

/** Buat akun pelajar terverifikasi lewat API + kotak surat dev (state isolasi per run). */
export async function createVerifiedUser(request: APIRequestContext, prefix = "pw") {
  const email = `${prefix}-${uniq()}@uji.test`;
  const password = "kata-sandi-browser-123";
  const r = await request.post("/api/v1/auth/register", { data: { email, password, display_name: "Pelajar Browser" } });
  expect(r.status()).toBe(202);
  const token = await latestToken(request, email, "verifikasi-email");
  expect((await request.post("/api/v1/auth/verify-email", { data: { token } })).ok()).toBeTruthy();
  return { email, password };
}

/** Skrip init: merekam pemanggilan getUserMedia + semua stream agar status track dapat diperiksa. */
export const INSTRUMENT_CAMERA = () => {
  const w = window as unknown as { __gum: unknown[]; __streams: MediaStream[] };
  w.__gum = []; w.__streams = [];
  const md = navigator.mediaDevices;
  if (!md) return;
  const orig = md.getUserMedia.bind(md);
  md.getUserMedia = async (c?: MediaStreamConstraints) => {
    w.__gum.push(JSON.parse(JSON.stringify(c ?? {})));
    const s = await orig(c);
    w.__streams.push(s);
    return s;
  };
};

export async function trackStates(page: Page) {
  return page.evaluate(() => (window as unknown as { __streams: MediaStream[] }).__streams.flatMap((s) =>
    s.getTracks().map((t) => ({ kind: t.kind, state: t.readyState }))));
}
