import { expect, test } from "@playwright/test";
import { createVerifiedUser, loginUI } from "./helpers";

test("alur belajar penuh di browser: katalog -> kurikulum -> ikuti -> pelajaran -> selesai -> progres", async ({ page, request }) => {
  const u = await createVerifiedUser(request, "lrn");
  await loginUI(page, u.email, u.password);
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByText("Anda belum mengikuti kurikulum apa pun")).toBeVisible(); // empty state

  await page.goto("/academy");
  await page.getByLabel("Cari").fill("Contoh A");
  await page.getByRole("button", { name: "Terapkan" }).click();
  await expect(page).toHaveURL(/q=Contoh\+A/);
  await page.getByRole("link", { name: /Kurikulum Contoh A/ }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Kurikulum Contoh A");
  await page.getByRole("button", { name: "Ikuti kurikulum" }).click();
  await expect(page.getByText("Berhasil mendaftar")).toBeVisible();
  await expect(page.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0");

  await page.getByRole("link", { name: "Mulai belajar" }).click();
  await expect(page).toHaveURL(/lessons\/demo-orientasi/);
  await expect(page.getByText("Cara Memakai SILATARA").first()).toBeVisible();
  await page.getByRole("button", { name: "Tandai selesai" }).click();
  await expect(page.getByText(/Progres kurikulum: 25%/)).toBeVisible();
  await page.getByRole("link", { name: /Keselamatan dan Privasi/ }).click();
  await page.getByRole("button", { name: "Tandai selesai" }).click();
  await expect(page.getByText(/Progres kurikulum: 50%/)).toBeVisible();

  await page.goto("/app/progress");
  await expect(page.getByRole("progressbar").first()).toBeVisible();
  await expect(page.getByText(/2\/4 pelajaran · 50%/).first()).toBeVisible();
  await page.goto("/app");
  await page.getByRole("link", { name: "Lanjutkan" }).click(); // resume learning
  await expect(page).toHaveURL(/lessons\/demo-referensi/);
});

test("learner tidak dapat membuka Kelola Konten maupun Admin (UI & API)", async ({ page, request }) => {
  const u = await createVerifiedUser(request, "rbac");
  await loginUI(page, u.email, u.password);
  await expect(page.getByRole("link", { name: "Kelola Konten" })).toHaveCount(0);
  await page.goto("/app/manage");
  await expect(page).toHaveURL(/akses=ditolak/);
  await page.goto("/app/admin");
  await expect(page).toHaveURL(/akses=ditolak/);
  const r = await page.request.get("/api/v1/manage/courses");
  expect(r.status()).toBe(403);
});

test("kurator: buat draf -> ajukan; draf tidak tampil publik", async ({ page, browser }) => {
  await loginUI(page, "demo-kurator@silatara.test");
  await page.goto("/app/manage/traditions/new");
  const name = `Tradisi Browser ${Date.now()}`;
  await page.getByLabel(/Nama tradisi/).fill(name);
  await page.getByLabel("Cakupan akses").selectOption("public");
  await page.getByLabel(/Sumber \/ atribusi/).fill("Sumber uji browser");
  await page.getByRole("button", { name: "Simpan sebagai draf" }).click();
  await expect(page).toHaveURL(/\/app\/manage\/traditions\/[0-9a-f-]{36}/);
  await expect(page.getByText("Draf").first()).toBeVisible();
  await page.getByRole("button", { name: "Ajukan review" }).click();
  await expect(page.getByText(/Ajukan review: berhasil/)).toBeVisible();
  const anon = await browser.newContext();
  const pub = await (await anon.newPage()).request.get(`/api/v1/traditions?q=${encodeURIComponent(name)}`);
  expect((await pub.json()).total).toBe(0);
  await anon.close();
});
