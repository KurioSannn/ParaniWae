import { defineConfig } from "@playwright/test";

const BASE = process.env.BASE_URL ?? "http://localhost:3000";
const FAKE_DEVICE = "--use-fake-device-for-media-stream";
const FAKE_UI = "--use-fake-ui-for-media-stream";

// Kamera di sini = perangkat PALSU Chromium (pola uji sintetis, bukan manusia). Hanya menguji siklus hidup.
export default defineConfig({
  testDir: "./tests",
  timeout: 90_000,
  expect: { timeout: 15_000 },
  retries: 0,
  workers: 1,
  reporter: [["list"], ["html", { outputFolder: "artifacts/playwright-report", open: "never" }], ["json", { outputFile: "artifacts/results.json" }]],
  outputDir: "artifacts/test-results",
  use: { baseURL: BASE, locale: "id-ID", trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    { name: "app", testMatch: /(auth|learning|visual|studio)\.spec\.ts/ },
    { name: "camera-fake", testMatch: /(camera(-benchmark|-roi)?|practice)\.spec\.ts/, use: { launchOptions: { args: [FAKE_DEVICE, FAKE_UI] }, permissions: ["camera"] } },
    { name: "camera-denied", testMatch: /camera-denied\.spec\.ts/, use: { launchOptions: { args: [FAKE_DEVICE] } } },
    { name: "camera-insecure", testMatch: /camera-insecure\.spec\.ts/, use: { baseURL: process.env.INSECURE_BASE_URL ?? "http://frontend:3000" } },
  ],
});
