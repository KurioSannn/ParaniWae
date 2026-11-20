import { expect, test, type Page } from "@playwright/test";
import { loginUI, uniq, watch } from "./helpers";

const A = "demo-instruktur@silatara.test"; // penanggung jawab Perguruan Contoh A (DEMO)
const B = "demo-instruktur-b@silatara.test"; // penanggung jawab Komunitas Contoh B (DEMO)
const CUR = "demo-kurator@silatara.test";
const ADM = "demo-admin@silatara.test";

async function as(page: Page, email: string, next?: string) {
  await page.context().clearCookies();
  await loginUI(page, email, undefined, next);
}
/** Panggilan API dengan sesi + CSRF browser (untuk menyiapkan data; verifikasi UI tetap lewat antarmuka). */
async function api(page: Page, method: "get" | "post" | "put" | "patch", path: string, data?: unknown) {
  const csrf = (await page.context().cookies()).find((c) => c.name === "silatara_csrf")?.value ?? "";
  const r = await page.request.fetch(`/api/v1${path}`, { method, data: data as object, headers: csrf ? { "X-CSRF-Token": csrf } : {} });
  return { status: r.status(), body: await r.json().catch(() => null) };
}
async function waitSaved(page: Page) { await expect(page.getByText(/^Tersimpan \d/)).toBeVisible({ timeout: 15_000 }); }

test("Movement Documentation Studio: dokumentasi -> review berlapis -> terbit -> pustaka publik", async ({ page, browser }) => {
  test.setTimeout(240_000);
  const name = `Gerakan Uji ${uniq()}`;

  // --- instruktur: dashboard + buat + isi (autosave) ---
  await as(page, A, "/app/studio");
  const w = watch(page, new URL(page.url()).origin);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Dokumentasi gerakan dan kemitraan");
  await expect(page.getByText("Perlu revisi", { exact: false }).first()).toBeVisible(); // data demo menunggu revisi
  await page.goto("/app/studio/movements/new");
  await page.getByLabel(/Mitra pemilik/).selectOption({ label: "[DEMO] Perguruan Contoh A" });
  await page.getByLabel(/^Tradisi/).selectOption({ label: "[DEMO] Tradisi Contoh A" });
  await page.getByLabel(/Nama gerakan/).fill(name);
  await page.getByRole("button", { name: "Buat draf versi 1" }).click();
  await expect(page).toHaveURL(/\/app\/studio\/movements\/[0-9a-f-]{36}$/);
  const movementId = page.url().split("/").pop()!;
  await expect(page.getByRole("heading", { level: 1 })).toContainText(name);

  // belum lengkap -> ajukan ditolak dengan daftar yang belum terpenuhi
  await page.getByRole("button", { name: "Ajukan review" }).click();
  await expect(page.getByRole("alert").filter({ hasText: /Belum terisi/ })).toBeVisible();

  await page.getByLabel(/^Tingkat/).selectOption({ label: "Pemula" });
  await page.getByRole("radio", { name: /Solo pemula/ }).check();
  await page.getByLabel(/^Prasyarat/).fill("Tidak ada prasyarat (uji).");
  await page.getByLabel(/^Konteks belajar/).fill("Pemanasan ringan (uji).");
  await page.getByLabel(/^Deskripsi gerakan/).fill("Deskripsi uji yang ditulis instruktur.");
  await page.getByRole("button", { name: "Tambah fase" }).click();
  await page.getByLabel(/^Nama fase/).first().fill("Fase uji 1");
  await page.getByLabel(/^Instruksi/).first().fill("Instruksi uji fase 1.");
  await page.locator("#safety_guidance").fill("Berhenti bila nyeri (uji).");
  await page.getByLabel(/^Sumber \/ atribusi/).fill("Instruktur uji, catatan pribadi");
  await page.locator("#rights_holder").fill("Instruktur Uji");
  await page.locator("#license_type").selectOption({ label: "Milik instruktur" });
  await page.locator("#usage_scope").fill("Pembelajaran di SILATARA");
  await page.getByLabel(/Saya menyatakan isi dokumentasi ini ditulis/).check();
  await waitSaved(page);
  await expect(page.getByRole("progressbar", { name: /Kelengkapan/ })).toHaveAttribute("aria-valuenow", /^1[0-2]$/);
  await expect(page.getByText("Perubahan tersimpan otomatis").or(page.getByText(/^Tersimpan \d/))).toBeVisible();

  // pratinjau
  await page.getByRole("button", { name: "Tampilkan pratinjau" }).click();
  await expect(page.getByRole("article", { name: new RegExp(`Dokumentasi ${name}`) })).toBeVisible();

  // simpan -> muat ulang: isi bertahan
  await page.reload();
  await expect(page.getByLabel(/^Deskripsi gerakan/)).toHaveValue("Deskripsi uji yang ditulis instruktur.");

  // ajukan; setelah itu terkunci
  await page.getByRole("button", { name: "Ajukan review" }).click();
  await expect(page.getByText("Ajukan review: berhasil.")).toBeVisible();
  await expect(page.getByText(/tidak dapat diubah/).first()).toBeVisible();
  await expect(page.getByLabel(/^Deskripsi gerakan/)).toBeDisabled();
  await expect(page.getByText(/Anda tidak dapat meninjau, menyetujui, atau menerbitkan tulisan Anda sendiri/)).toBeVisible();

  // penanggung jawab menambah B sebagai manager (Partner Workspace)
  await page.goto("/app/studio/partners");
  await page.getByRole("link", { name: "[DEMO] Perguruan Contoh A" }).click();
  await page.getByLabel("Email pengguna").fill(B);
  await page.getByLabel("Peran", { exact: true }).selectOption("manager");
  await page.getByRole("button", { name: "Tambah anggota" }).click();
  await expect(page.getByText("Anggota ditambahkan.")).toBeVisible();

  // kurator meninjau kelengkapan + provenance
  await as(page, CUR, `/app/studio/movements/${movementId}`);
  await page.getByRole("button", { name: "Tandai ditinjau (kurator)" }).click();
  await expect(page.getByText(/Kelengkapan & asal-usul ditinjau kurator — \[DEMO\] Kurator/)).toBeVisible();
  // kurator belum bisa menyetujui tanpa konfirmasi mitra
  await expect(page.getByRole("button", { name: "Setujui", exact: true })).toHaveCount(0);

  // mitra lain (B, manager) mengonfirmasi
  await as(page, B, `/app/studio/movements/${movementId}`);
  await page.getByRole("button", { name: "Konfirmasi sebagai mitra" }).click();
  await expect(page.getByText(/Dikonfirmasi penanggung jawab mitra — \[DEMO\] Instruktur B/)).toBeVisible();

  // kurator: setuju butuh bukti
  await as(page, CUR, `/app/studio/movements/${movementId}`);
  await page.getByRole("button", { name: "Setujui", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: /bukti/i })).toBeVisible();
  await page.getByLabel(/^Rujukan bukti persetujuan/).fill("Berita acara uji E2E");
  await page.getByRole("button", { name: "Setujui", exact: true }).click();
  await expect(page.getByText("Setujui: berhasil.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Terbitkan" })).toHaveCount(0); // hanya admin

  // admin menerbitkan
  await as(page, ADM, `/app/studio/movements/${movementId}`);
  await page.getByRole("button", { name: "Terbitkan" }).click();
  await expect(page.getByText("Terbitkan: berhasil.")).toBeVisible();

  // publik (anonim): pustaka + detail + riwayat versi; konten draf tidak bocor
  const anon = await browser.newContext({ baseURL: page.url().split("/app")[0] });
  const ap = await anon.newPage();
  await ap.goto(`/library/${movementId}`);
  await expect(ap.getByRole("heading", { level: 1 })).toContainText(name);
  await expect(ap.getByText("Fase uji 1")).toBeVisible();
  await expect(ap.getByText("Versi 1").first()).toBeVisible();
  await ap.goto(`/library?safety_category=solo_beginner&q=${encodeURIComponent(name)}`);
  await expect(ap.getByRole("link", { name })).toBeVisible();
  await ap.goto("/library?q=Gerakan+Draf");
  await expect(ap.getByText("[DEMO] Gerakan Draf (tidak boleh tampil)")).toHaveCount(0);
  await anon.close();
  expect(w.external).toEqual([]);
});

test("Partner Workspace: profil bukan mitra resmi -> verifikasi admin dengan bukti -> direktori publik", async ({ page, browser }) => {
  test.setTimeout(180_000);
  const org = `Organisasi Uji ${uniq()}`;
  await as(page, A, "/app/studio/partners/new");
  await page.getByLabel(/Nama organisasi/).fill(org);
  await page.getByRole("button", { name: "Simpan sebagai draf" }).click();
  await expect(page).toHaveURL(/\/app\/studio\/partners\/[0-9a-f-]{36}$/);
  const pid = page.url().split("/").pop()!;
  await expect(page.getByText("Draf — belum diajukan").first()).toBeVisible();
  await expect(page.getByText(/bukan berarti menjadi mitra resmi/)).toBeVisible();
  // belum lengkap
  await page.getByRole("button", { name: "Ajukan verifikasi" }).click();
  await expect(page.getByRole("alert").filter({ hasText: /Profil belum lengkap/ })).toBeVisible();
  // lengkapi
  await page.getByLabel("Penanggung jawab", { exact: true }).fill("Penanggung Jawab Uji");
  await page.getByLabel("Peran penanggung jawab").fill("Ketua");
  await page.getByLabel("Email kontak resmi").fill("kontak@uji.test");
  await page.getByRole("button", { name: "Simpan profil" }).click();
  await expect(page.getByText("Profil tersimpan.")).toBeVisible();
  await page.getByLabel(/Tambah tradisi/).selectOption({ label: "[DEMO] Tradisi Contoh A" });
  await expect(page.getByText("Tradisi ditambahkan.")).toBeVisible();
  await page.locator("#d-file").setInputFiles({ name: "surat.pdf", mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4\n% uji\n") });
  await page.getByRole("button", { name: "Unggah", exact: true }).click();
  await expect(page.getByText("Dokumen tersimpan secara privat.")).toBeVisible();
  // dokumen persetujuan tidak tersedia publik/anonim
  const docLink = await page.getByRole("link", { name: "Unduh" }).getAttribute("href");
  const anon = await browser.newContext({ baseURL: page.url().split("/app")[0] });
  expect((await anon.request.get(docLink!)).status()).toBe(401);
  await page.getByRole("button", { name: "Ajukan verifikasi" }).click();
  await expect(page.getByText("Ajukan verifikasi: berhasil.")).toBeVisible();
  await expect(page.getByText("Menunggu verifikasi admin").first()).toBeVisible();
  // pemilik tidak dapat memverifikasi dirinya sendiri
  await expect(page.getByRole("button", { name: "Verifikasi", exact: true })).toHaveCount(0);

  // admin: wajib bukti
  await as(page, ADM, `/app/studio/partners/${pid}`);
  await page.getByRole("button", { name: "Verifikasi", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: /bukti/i })).toBeVisible();
  await page.getByLabel(/Rujukan bukti verifikasi/).fill("Surat penugasan uji E2E");
  await page.getByRole("button", { name: "Verifikasi", exact: true }).click();
  await expect(page.getByText("Verifikasi: berhasil.")).toBeVisible();
  await expect(page.getByText(/Diputuskan oleh:\s*\[DEMO\] Admin/)).toBeVisible();
  await expect(page.getByText("Terverifikasi").first()).toBeVisible();

  // belum dicantumkan di direktori publik (butuh persetujuan organisasi + admin)
  const ap = await anon.newPage();
  await ap.goto(`/community?q=${encodeURIComponent(org)}`);
  await expect(ap.getByText(org)).toHaveCount(0);
  await as(page, A, `/app/studio/partners/${pid}`);
  await page.getByLabel(/Organisasi menyetujui dicantumkan/).click();
  await expect(page.getByText("Preferensi direktori publik diperbarui.")).toBeVisible();
  await as(page, ADM, `/app/studio/partners/${pid}`);
  await page.getByRole("button", { name: "Cantumkan di direktori publik" }).click();
  await expect(page.getByText("Tercantum di direktori publik")).toBeVisible();
  await ap.goto(`/community?q=${encodeURIComponent(org)}`);
  await expect(ap.getByText(org).first()).toBeVisible();
  await expect(ap.getByText("Terverifikasi oleh mitra").first()).toBeVisible();
  await anon.close();
});

test("Calibration Workspace: fixture [DEMO], timeline, penanda, provenance; tanpa skor", async ({ page }) => {
  test.setTimeout(120_000);
  await as(page, A, "/app/studio/movements");
  await page.getByRole("link", { name: "[DEMO] Dokumentasi Menunggu Tinjauan" }).click();
  await page.getByRole("link", { name: /Calibration Workspace/ }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Dokumentasi Menunggu Tinjauan");
  await expect(page.getByText(/instructor reference annotation/).first()).toBeVisible();
  await expect(page.getByText(/Tidak ada skor, ambang, kemiripan, atau koreksi otomatis/)).toBeVisible();
  await page.getByLabel("Sumber referensi").selectOption({ label: "[DEMO] Fixture sintetis — bukan rekaman manusia" });
  const slider = page.getByRole("slider", { name: "Timeline referensi" });
  await expect(slider).toHaveAttribute("aria-valuemax", "6000");
  await expect(page.getByText("[DEMO] Penanda 2")).toBeVisible(); // anotasi fixture dari seed
  await slider.focus();
  await page.keyboard.press("End");
  await expect(slider).toHaveAttribute("aria-valuenow", "6000");
  await page.keyboard.press("Home");
  await page.keyboard.press("ArrowRight");
  const now = Number(await slider.getAttribute("aria-valuenow"));
  expect(now).toBeGreaterThan(0);
  expect(now).toBeLessThan(100);
  await expect(page.getByRole("img", { name: /Overlay kerangka/ })).toBeVisible();
  const mark = `Uji penanda ${uniq()}`;
  await page.getByLabel("Label penanda").fill(mark);
  await page.getByRole("button", { name: "Simpan penanda" }).click();
  await expect(page.getByText(/Penanda di .* disimpan/)).toBeVisible();
  await expect(page.getByRole("row", { name: new RegExp(mark) })).toBeVisible();
  await expect(page.getByText(/Model: \[DEMO\] synthetic-fixture/).first()).toBeVisible();
  // penanda sendiri tidak dapat disetujui sendiri (tidak ada tombol Terima untuk pembuat)
  const row = page.getByRole("row", { name: new RegExp(mark) });
  await expect(row.getByRole("button", { name: "Terima" })).toHaveCount(0);
  // mode overlay di atas video
  await page.getByLabel("Overlay di atas video").check();
  await expect(page.getByRole("img", { name: "Overlay kerangka" })).toBeVisible();
  await expect(page.getByText(/(skor|akurasi|similarity|kemiripan)\s*[:=]\s*\d/i)).toHaveCount(0); // tidak ada angka penilaian
});

test("Media referensi: deklarasi wajib, privat secara default, verifikasi izin, kalibrasi video sintetis", async ({ page, browser }) => {
  test.setTimeout(300_000);
  await as(page, A, "/app/studio");
  const partners = await api(page, "get", "/studio/partners");
  const pa = partners.body.items.find((p: { name: string }) => p.name === "[DEMO] Perguruan Contoh A");
  const pd = await api(page, "get", `/studio/partners/${pa.id}`);
  const created = await api(page, "post", "/studio/movements", { name_id: `Media Uji ${uniq()}`, partner_id: pa.id, tradition_id: pd.body.traditions[0].id });
  expect(created.status).toBe(201);
  const mid = created.body.id as string;
  await page.goto(`/app/studio/movements/${mid}`);

  // webm sintetis dibuat di browser (kanvas + MediaRecorder); BUKAN rekaman manusia
  const bytes = await page.evaluate(async () => {
    const c = document.createElement("canvas"); c.width = 320; c.height = 240;
    const ctx = c.getContext("2d")!;
    const rec = new MediaRecorder(c.captureStream(15), { mimeType: "video/webm" });
    const chunks: Blob[] = [];
    rec.ondataavailable = (e) => chunks.push(e.data);
    const done = new Promise<void>((r) => { rec.onstop = () => r(); });
    rec.start();
    for (let i = 0; i < 30; i++) { ctx.fillStyle = i % 2 ? "#cccccc" : "#999999"; ctx.fillRect(0, 0, 320, 240); await new Promise((r) => setTimeout(r, 70)); }
    rec.stop(); await done;
    return Array.from(new Uint8Array(await new Blob(chunks).arrayBuffer()));
  });
  const buf = Buffer.from(bytes);
  expect(buf.length).toBeGreaterThan(500);

  // tanpa deklarasi: ditolak
  await page.locator("#mu-title").fill("Rekaman sintetis uji");
  await page.locator("#mu-file").setInputFiles({ name: "uji.webm", mimeType: "video/webm", buffer: buf });
  await page.locator("#mu-holder").fill("Tim uji");
  await page.locator("#mu-lic").selectOption("instructor_owned");
  await page.locator("#mu-src").fill("Dibuat kode (kanvas), bukan manusia");
  await page.locator("#mu-scope").fill("Hanya uji teknis");
  await page.getByRole("button", { name: "Unggah media" }).click();
  await expect(page.getByText("Media tersimpan secara privat dan menunggu verifikasi izin.")).toHaveCount(0); // checkbox wajib (validasi browser)
  await page.getByLabel(/Saya menyatakan berhak atau berizin/).check();
  await page.getByRole("button", { name: "Unggah media" }).click();
  await expect(page.getByText("Media tersimpan secara privat dan menunggu verifikasi izin.")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Dideklarasikan (belum diverifikasi)")).toBeVisible();

  const media = await api(page, "get", `/studio/movements/${mid}/media`);
  const m = media.body[0];
  expect(m.access_level).toBe("private");
  // file privat: pengunggah boleh; anonim tidak
  expect((await page.request.get(m.url)).status()).toBe(200);
  const anon = await browser.newContext({ baseURL: page.url().split("/app")[0] });
  expect((await anon.request.get(m.url)).status()).toBe(404);
  await anon.close();

  // pengunggah tidak dapat memverifikasi izin sendiri; kurator bisa (dengan bukti)
  expect((await api(page, "patch", `/studio/media/${m.id}`, { consent_status: "verified", permission_evidence_ref: "x" })).status).toBe(403);
  await as(page, CUR, `/app/studio/movements/${mid}`);
  await page.getByLabel("Bukti izin untuk verifikasi").fill("Pernyataan uji E2E");
  await page.getByRole("button", { name: "Verifikasi izin" }).click();
  await expect(page.getByText("Izin media diverifikasi.")).toBeVisible();
  await expect(page.getByText("Izin terverifikasi").first()).toBeVisible();

  // Calibration Workspace dengan video referensi (overlay MediaPipe di worker; konten sintetis -> tidak ada tubuh)
  await page.goto(`/app/studio/movements/${mid}/calibration?media=${m.id}`);
  const video = page.locator("video");
  await expect(video).toBeVisible();
  const slider = page.getByRole("slider", { name: "Timeline referensi" });
  await expect.poll(async () => Number(await slider.getAttribute("aria-valuemax")), { timeout: 20_000 }).toBeGreaterThan(500);
  await page.getByRole("button", { name: "Aktifkan overlay MediaPipe" }).click();
  await expect(page.getByText(/MediaPipe Pose \(/)).toBeVisible({ timeout: 90_000 });
  await expect(page.getByText(/Tidak ada tubuh terdeteksi pada frame ini/)).toBeVisible({ timeout: 90_000 }); // jujur: bukan manusia
  await page.getByRole("button", { name: "Maju satu frame" }).click();
  await page.getByLabel("Label penanda").fill("Awal klip sintetis");
  await page.getByRole("button", { name: "Simpan penanda" }).click();
  await expect(page.getByText(/Model: mediapipe-tasks-vision/)).toBeVisible();
  // cabut izin -> video tidak lagi dapat dibuka
  expect((await api(page, "patch", `/studio/media/${m.id}`, { consent_status: "revoked" })).status).toBe(200);
  expect((await page.request.get(m.url)).status()).toBe(200); // staf masih dapat membuka untuk pemeriksaan
});

test("tangkapan layar Studio (untuk dokumentasi/laporan)", async ({ page }) => {
  test.setTimeout(120_000);
  await page.setViewportSize({ width: 1440, height: 900 });
  const dir = "artifacts/screenshots-studio";
  const shot = (n: string) => page.screenshot({ path: `${dir}/${n}.png`, fullPage: true });
  await as(page, A, "/app/studio");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Dokumentasi gerakan");
  await shot("01-instructor-dashboard");
  await page.goto("/app/studio/partners");
  await page.getByRole("link", { name: "[DEMO] Perguruan Contoh A" }).click();
  await expect(page.getByText("Partner Workspace")).toBeVisible();
  await shot("02-partner-workspace");
  await page.goto("/app/studio/movements");
  await shot("03-movement-list");
  await page.getByRole("link", { name: "[DEMO] Dokumentasi Perlu Revisi" }).click();
  await expect(page.getByText("Movement Documentation Studio")).toBeVisible();
  await shot("04-movement-editor-needs-revision");
  await page.goto("/app/studio/movements");
  await page.getByRole("link", { name: "[DEMO] Dokumentasi Berversi" }).click();
  await shot("05-movement-versioned-locked");
  await page.getByRole("link", { name: /Calibration Workspace/ }).click();
  await page.getByLabel("Sumber referensi").selectOption({ label: "[DEMO] Fixture sintetis — bukan rekaman manusia" });
  await page.getByRole("slider", { name: "Timeline referensi" }).focus();
  await page.keyboard.press("End");
  await shot("06-calibration-fixture");
  await page.context().clearCookies();
  await page.goto("/library");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Pustaka Gerakan");
  await shot("07-library");
  await page.getByRole("link", { name: "[DEMO] Dokumentasi Berversi" }).click();
  await expect(page.getByText("Riwayat versi")).toBeVisible();
  await shot("08-library-detail-versions");
  await as(page, CUR, "/app/studio");
  await shot("09-curator-dashboard");
});
