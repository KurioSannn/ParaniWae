import { expect, test } from "@playwright/test";
import { loginUI } from "./helpers";

test("[izin] tanpa izin di headless (prompt tak bisa dijawab) -> UI keluar dari 'meminta izin' ke pesan galat, tidak macet, tanpa stream", async ({ page }, info) => {
  await page.addInitScript(() => {
    const md = navigator.mediaDevices, orig = md.getUserMedia.bind(md);
    md.getUserMedia = (c) => orig(c).catch((e: Error) => { (window as unknown as { __err: string }).__err = e.name; throw e; });
  });
  await loginUI(page, "demo-pelajar@silatara.test");
  await page.goto("/app/practice/camera-check");
  await page.getByRole("button", { name: /nyalakan kamera/ }).click();
  await expect(page.getByRole("button", { name: /Hentikan kamera/ })).toHaveCount(0);
  await expect(page.getByText(/Izin kamera ditolak|Kamera tidak dapat dimulai|tidak ditemukan/)).toBeVisible();
  await expect(page.getByRole("button", { name: /nyalakan kamera/ })).toBeVisible();
  const name = await page.evaluate(() => (window as unknown as { __err?: string }).__err);
  info.annotations.push({ type: "browser-error-name", description: String(name) });
  console.log(`error asli dari browser tanpa izin (headless): ${name}`);
});

// CATATAN: Chromium headless tidak dapat menekan "Blokir" pada prompt asli; penolakan DISIMULASIKAN dengan
// NotAllowedError yang sama seperti yang dilempar browser saat pengguna menolak.
test("[izin] izin ditolak (NotAllowedError, simulasi) -> pesan jelas, tidak ada stream, tombol mulai tersedia lagi", async ({ page }) => {
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = () => Promise.reject(Object.assign(new Error("Permission denied"), { name: "NotAllowedError" }));
  });
  await loginUI(page, "demo-pelajar@silatara.test");
  await page.goto("/app/practice/camera-check");
  await page.getByRole("button", { name: /nyalakan kamera/ }).click();
  await expect(page.getByText(/Izin kamera ditolak/)).toBeVisible();
  await expect(page.getByRole("button", { name: /nyalakan kamera/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Hentikan kamera/ })).toHaveCount(0);
});

test("[error] kamera tidak ditemukan (NotFoundError) -> pesan kamera tidak ditemukan", async ({ page }) => {
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = () => Promise.reject(Object.assign(new Error("x"), { name: "NotFoundError" }));
  });
  await loginUI(page, "demo-pelajar@silatara.test");
  await page.goto("/app/practice/camera-check");
  await page.getByRole("button", { name: /nyalakan kamera/ }).click();
  await expect(page.getByText(/Kamera tidak ditemukan/)).toBeVisible();
});

test("[error] kamera dipakai aplikasi lain (NotReadableError) -> pesan bantuan", async ({ page }) => {
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = () => Promise.reject(Object.assign(new Error("x"), { name: "NotReadableError" }));
  });
  await loginUI(page, "demo-pelajar@silatara.test");
  await page.goto("/app/practice/camera-check");
  await page.getByRole("button", { name: /nyalakan kamera/ }).click();
  await expect(page.getByText(/sedang dipakai aplikasi lain/)).toBeVisible();
});
