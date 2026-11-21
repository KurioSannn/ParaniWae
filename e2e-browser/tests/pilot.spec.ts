import { expect, test, type Page } from "@playwright/test";
import { createVerifiedUser, loginUI, uniq } from "./helpers";

const A = "demo-instruktur@silatara.test"; // manager Perguruan Contoh A (DEMO)
const B = "demo-instruktur-b@silatara.test"; // mitra lain
const ADM = "demo-admin@silatara.test";

async function as(page: Page, email: string, pw?: string, next?: string) { await page.context().clearCookies(); await loginUI(page, email, pw, next); }
async function api(page: Page, method: "get" | "post" | "put" | "patch" | "delete", path: string, data?: unknown) {
  const csrf = (await page.context().cookies()).find((c) => c.name === "silatara_csrf")?.value ?? "";
  const r = await page.request.fetch(`/api/v1${path}`, { method, data: data as object, headers: csrf ? { "X-CSRF-Token": csrf } : {} });
  return { status: r.status(), body: await r.json().catch(() => null), headers: r.headers() };
}

test("Pilot end-to-end: program -> persetujuan -> cohort -> undangan -> peserta -> belajar -> survei -> analytics -> CSV", async ({ page, browser }) => {
  test.setTimeout(240_000);
  const name = `Program Uji ${uniq()}`;

  // 1) instruktur membuat program (draf) + cohort lewat UI
  await as(page, A, undefined, "/app/pilot/manage/new");
  await page.getByLabel(/Perguruan penyelenggara/).selectOption({ label: "[DEMO] Perguruan Contoh A" });
  await page.getByLabel(/Nama program/).fill(name);
  await page.getByLabel("Tujuan", { exact: true }).fill("Menguji alur pilot");
  await page.locator("#start_date").fill("2026-12-01");
  await page.locator("#end_date").fill("2027-03-01");
  await page.getByRole("button", { name: "Simpan sebagai draf" }).click();
  await expect(page).toHaveURL(/\/app\/pilot\/manage\/[0-9a-f-]{36}$/);
  const pid = page.url().split("/").pop()!;
  await expect(page.getByText("Program ini BELUM resmi.")).toBeVisible();
  // belum lengkap -> ajukan ditolak dengan daftar kekurangan
  await page.getByRole("button", { name: "Ajukan untuk disetujui" }).click();
  await expect(page.getByRole("alert").filter({ hasText: /belum lengkap/i })).toBeVisible();
  await page.getByLabel("Instruktur penanggung jawab").selectOption({ label: "[DEMO] Instruktur" });
  await page.getByRole("button", { name: "Simpan", exact: true }).click();
  await expect(page.getByText("Program tersimpan.")).toBeVisible();
  await page.getByLabel("Nama cohort").fill("Cohort Uji");
  await page.getByLabel(/Kurikulum \(terbit/).selectOption({ label: "[DEMO] Kurikulum Contoh A" });
  await page.getByLabel("Instruktur cohort").selectOption({ label: "[DEMO] Instruktur" });
  await page.getByRole("button", { name: "Tambah cohort" }).click();
  await expect(page.getByText("Cohort dibuat.")).toBeVisible();
  await page.getByRole("button", { name: "Ajukan untuk disetujui" }).click();
  await expect(page.getByText("Ajukan untuk disetujui: berhasil.")).toBeVisible();
  await expect(page.getByText("Menunggu persetujuan").first()).toBeVisible();
  // penulis/anggota mitra tidak dapat menyetujui
  await expect(page.getByRole("button", { name: "Setujui program" })).toHaveCount(0);

  // mitra lain tidak melihat program ini (404)
  await as(page, B);
  expect((await api(page, "get", `/pilot/programs/${pid}`)).status).toBe(404);

  // 2) admin menyetujui; manager mengaktifkan; cohort dibuka
  await as(page, ADM, undefined, `/app/pilot/manage/${pid}`);
  await page.getByRole("button", { name: "Setujui program" }).click();
  await expect(page.getByText("Program ini resmi (disetujui).")).toBeVisible();
  await as(page, A, undefined, `/app/pilot/manage/${pid}`);
  await page.getByRole("button", { name: "Aktifkan program" }).click();
  await expect(page.getByText("Aktifkan program: berhasil.")).toBeVisible();
  await page.getByRole("link", { name: "Cohort Uji" }).click();
  await page.getByRole("button", { name: "Buka untuk undangan" }).click();
  await expect(page.getByText("Status cohort diperbarui.")).toBeVisible();
  await page.getByRole("button", { name: "Buat undangan" }).click();
  await expect(page.getByText("Tautan undangan (hanya ditampilkan sekali)")).toBeVisible();
  const link = (await page.locator("p.font-mono").innerText()).trim();
  expect(link).toContain("/undangan?token=");
  const cohortId = page.url().split("/").pop()!;
  // status undangan terlihat pengelola
  await expect(page.getByText("Menunggu").first()).toBeVisible();

  // 3) peserta: buka undangan tanpa login -> login -> terima
  const learner = await createVerifiedUser(page.request, "pilot");
  const lp = await browser.newPage({ baseURL: new URL(page.url()).origin });
  await lp.goto(new URL(link).pathname + new URL(link).search);
  await expect(lp.getByRole("heading", { level: 1 })).toContainText(name);
  await expect(lp.getByText("Status undangan:")).toBeVisible();
  await lp.locator("main").getByRole("link", { name: "Masuk" }).click();
  await lp.getByLabel("Email").fill(learner.email);
  await lp.getByLabel("Kata sandi").fill(learner.password);
  await lp.getByRole("button", { name: "Masuk" }).click();
  await expect(lp).toHaveURL(/\/undangan\?token=/);
  const accept = lp.getByRole("button", { name: /Terima undangan/ });
  await expect(accept).toBeDisabled(); // tanpa pengakuan data operasional
  await lp.getByLabel(/Wajib:/).check();
  await accept.click();
  await expect(lp).toHaveURL(/\/app\/pilot\/cohorts\//);
  await expect(lp.getByRole("heading", { level: 1 })).toContainText(name);
  await expect(lp.getByText(/Video dan data biometrik tidak pernah dikumpulkan/)).toBeVisible();
  // undangan sekali pakai
  await lp.context().clearCookies();
  await lp.goto(new URL(link).pathname + new URL(link).search);
  await expect(lp.getByText(/Status undangan:\s*Diterima/)).toBeVisible();
  await expect(lp.getByText(/tidak dapat dipakai saat ini/)).toBeVisible();

  // 4) peserta belajar (alur existing) -> terlihat di portal
  await loginUI(lp, learner.email, learner.password, "/app/pilot");
  await lp.getByRole("link", { name: new RegExp(name) }).click();
  await lp.getByRole("link", { name: /Orientasi/ }).click();
  await lp.getByRole("button", { name: "Tandai selesai" }).click();
  await expect(lp.getByText(/Progres kurikulum: 25%/)).toBeVisible();
  await lp.goto("/app/pilot");
  await expect(lp.getByText(/1\/4 pelajaran · 25%/)).toBeVisible();

  // 5) instruktur: dashboard cohort menampilkan peserta & aktivitas; pengumuman diantrekan jujur
  await as(page, A, undefined, `/app/pilot/manage/cohorts/${cohortId}`);
  await expect(page.getByRole("row", { name: /1\/4 \(25%\)/ })).toBeVisible();
  await page.goto(`/app/pilot/manage/${pid}`);
  await page.locator("#at").fill("Selamat datang");
  await page.locator("#ab").fill("Pertemuan pertama pekan depan");
  await page.getByRole("button", { name: "Buat pengumuman" }).click();
  await expect(page.getByText(/diantrekan.*BELUM terkirim/)).toBeVisible();
  // survei baseline dari templat -> dibuka
  await page.getByRole("button", { name: "Buat dari templat" }).first().click();
  await expect(page.getByText("Survei dibuat dari templat draf.")).toBeVisible();
  await page.getByRole("button", { name: "Buka", exact: true }).click();
  await expect(page.getByText("Survei dibuka.")).toBeVisible();

  // 6) peserta mengisi survei
  await lp.goto("/app/pilot");
  await lp.getByRole("link", { name: /Survei awal/ }).first().click();
  await expect(lp.getByText(/BELUM divalidasi/)).toBeVisible();
  await lp.getByRole("radio", { name: "Beberapa kali", exact: true }).check();
  await lp.locator("input[name='percaya_diri'][value='4']").check();
  await lp.getByRole("radio", { name: "Cukup mudah" }).check();
  await lp.getByRole("button", { name: "Kirim jawaban" }).click();
  await expect(lp).toHaveURL(/\/app\/pilot$/);

  // 7) analytics: 1 responden -> distribusi DISEMBUNYIKAN; usage peserta < 5 disembunyikan; CSV tanpa identitas
  await page.goto(`/app/pilot/manage/${pid}`);
  await expect(page.getByText(/1 responden dari 1/)).toBeVisible();
  await expect(page.getByText(/Distribusi jawaban disembunyikan/)).toBeVisible();
  await expect(page.getByText(/Disembunyikan: peserta aktif kurang dari 5/)).toBeVisible();
  const csv = await api(page, "get", `/pilot/programs/${pid}/report.csv`);
  expect(csv.headers["content-type"]).toContain("text/csv");
  const csvText = await (await page.request.get(`/api/v1/pilot/programs/${pid}/report.csv`)).text();
  expect(csvText).not.toContain(learner.email);
  expect(csvText).toContain("DISEMBUNYIKAN");
  await page.screenshot({ path: "artifacts/screenshots-pilot/program-analytics.png", fullPage: true });
  await lp.close();
});

test("Pilot: mitra belum terverifikasi hanya draf; undangan dicabut; aturan akses", async ({ page, request }) => {
  test.setTimeout(120_000);
  await as(page, A, undefined, "/app/studio/partners/new");
  await page.getByLabel(/Nama organisasi/).fill(`Org Pilot ${uniq()}`);
  await page.getByRole("button", { name: "Simpan sebagai draf" }).click();
  await expect(page).toHaveURL(/\/app\/studio\/partners\/[0-9a-f-]{36}$/);
  const partnerId = page.url().split("/").pop()!;
  const prog = await api(page, "post", "/pilot/programs", { partner_id: partnerId, name: "Program draf mitra baru", capacity: 10 });
  expect(prog.status).toBe(201);
  expect(prog.body.partner_verified).toBe(false);
  expect(prog.body.official).toBe(false);
  const sub = await api(page, "post", `/pilot/programs/${prog.body.id}/transition`, { action: "submit" });
  expect(sub.status).toBe(409);
  expect(sub.body.error.code).toBe("PARTNER_NOT_VERIFIED");
  // pelajar tidak dapat mengelola
  const u = await createVerifiedUser(request, "pilot-rbac");
  await as(page, u.email, u.password);
  expect((await api(page, "get", "/pilot/programs")).status).toBe(403);
  await page.goto("/app/pilot/manage");
  await expect(page).toHaveURL(/\/app\?akses=ditolak/);
  // pratinjau token palsu
  expect((await request.get("/api/v1/pilot/invitations/preview?token=" + "x".repeat(30))).status()).toBe(404);
});
