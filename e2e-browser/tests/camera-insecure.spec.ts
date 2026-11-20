import { expect, test } from "@playwright/test";
import { loginUI } from "./helpers";

// Tanpa flag secure-context: http://frontend:3000 bukan localhost/HTTPS -> browser memblokir kamera.
test("[error] konteks tidak aman (http non-localhost) -> pesan HTTPS/localhost, kamera tidak diminta", async ({ page }) => {
  await loginUI(page, "demo-pelajar@silatara.test");
  await page.goto("/app/practice/camera-check");
  expect(await page.evaluate(() => window.isSecureContext)).toBe(false);
  await page.getByRole("button", { name: /nyalakan kamera/ }).click();
  await expect(page.getByText(/koneksi aman \(HTTPS\) atau localhost/)).toBeVisible();
});
