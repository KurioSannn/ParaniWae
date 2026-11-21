import { expect, test } from "@playwright/test";
import { loginUI, uniq } from "./helpers";

// Batas unggahan 100 MB melalui proxy Next.js yang sama dengan produksi (frontend -> backend), bukan langsung ke backend.
test("unggahan media: 40 MB diterima, 100 MB + 1 byte ditolak 413 lewat proxy; berkas privat & belum dipindai tidak publik", async ({ page, browser }) => {
  test.setTimeout(240_000);
  await loginUI(page, "demo-instruktur@silatara.test");
  const csrf = (await page.context().cookies()).find((c) => c.name === "silatara_csrf")!.value;
  const H = { "X-CSRF-Token": csrf };
  const partners = await (await page.request.get("/api/v1/studio/partners", { headers: H })).json();
  const pa = partners.items.find((p: { name: string }) => p.name === "[DEMO] Perguruan Contoh A");
  const pd = await (await page.request.get(`/api/v1/studio/partners/${pa.id}`, { headers: H })).json();
  const mv = await (await page.request.post("/api/v1/studio/movements", { headers: H, data: { name_id: `Batas Unggah ${uniq()}`, partner_id: pa.id, tradition_id: pd.traditions[0].id } })).json();
  const WEBM = Buffer.from([0x1a, 0x45, 0xdf, 0xa3]);
  const form = (size: number) => ({
    title: "Uji batas", rights_holder: "Tim uji", source_description: "Dibuat uji", license_type: "instructor_owned", usage_scope: "uji teknis", declaration_confirmed: "true",
    file: { name: "besar.webm", mimeType: "video/webm", buffer: Buffer.concat([WEBM, Buffer.alloc(size - 4)]) },
  });
  const ok = await page.request.post(`/api/v1/studio/movements/${mv.id}/media`, { headers: H, multipart: form(40 * 1024 * 1024), timeout: 180_000 });
  expect(ok.status()).toBe(201);
  const m = await ok.json();
  expect(m.size_bytes).toBe(40 * 1024 * 1024);
  expect(m.scan_status).toBe("not_scanned"); // pemindai nonaktif di stack uji: jujur, bukan "clean"
  const over = await page.request.post(`/api/v1/studio/movements/${mv.id}/media`, { headers: H, multipart: form(100 * 1024 * 1024 + 1), timeout: 180_000 });
  expect(over.status()).toBe(413);
  expect((await over.json()).error.code).toBe("FILE_TOO_LARGE");
  // tepat 100 MB diterima
  const exact = await page.request.post(`/api/v1/studio/movements/${mv.id}/media`, { headers: H, multipart: form(100 * 1024 * 1024), timeout: 180_000 });
  expect(exact.status()).toBe(201);
  // anonim tidak dapat membuka; tidak dapat dijadikan publik tanpa pemindaian bersih
  const anon = await browser.newContext({ baseURL: page.url().split("/app")[0] });
  expect((await anon.request.get(m.url)).status()).toBe(404);
  await anon.close();
  const pub = await page.request.patch(`/api/v1/studio/media/${m.id}`, { headers: H, data: { access_level: "public" } });
  expect(pub.status()).toBe(409);
});
