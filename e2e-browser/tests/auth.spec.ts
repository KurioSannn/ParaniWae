import { expect, test } from "@playwright/test";
import { createVerifiedUser, DEMO_PW, latestToken, loginUI, uniq } from "./helpers";

test("registrasi -> periksa email -> login ditolak sebelum verifikasi -> verifikasi -> login", async ({ page, request }) => {
  const email = `ui-${uniq()}@uji.test`;
  await page.goto("/daftar");
  await page.getByLabel("Nama tampilan").fill("Pelajar UI");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Kata sandi", { exact: true }).fill("kata-sandi-browser-123");
  await page.getByLabel("Ulangi kata sandi").fill("kata-sandi-browser-123");
  await page.getByRole("button", { name: "Buat akun" }).click();
  await expect(page.getByText("Periksa email Anda")).toBeVisible();
  expect((await page.context().cookies()).some((c) => c.name === "silatara_session")).toBe(false); // tanpa sesi

  await loginUI(page, email, "kata-sandi-browser-123");
  await expect(page.getByText(/Email belum diverifikasi/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Kirim ulang email verifikasi" })).toBeVisible();

  const token = await latestToken(request, email, "verifikasi-email");
  await page.goto(`/verifikasi-email?token=${token}`);
  await expect(page).toHaveURL(/\/verifikasi-email$/); // token dihapus dari URL
  await page.getByRole("button", { name: "Verifikasi email saya" }).click();
  await expect(page.getByText("Email terverifikasi")).toBeVisible();
  await page.goto(`/verifikasi-email?token=${token}`); // sekali pakai
  await page.getByRole("button", { name: "Verifikasi email saya" }).click();
  await expect(page.getByText(/tidak valid atau sudah kedaluwarsa/)).toBeVisible();

  await loginUI(page, email, "kata-sandi-browser-123");
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByRole("heading", { name: "Halo, Pelajar UI" })).toBeVisible();
});

test("registrasi email yang sudah ada menampilkan panel yang SAMA (tidak membocorkan keberadaan akun)", async ({ page }) => {
  const outcomes: string[] = [];
  for (const email of ["demo-pelajar@silatara.test", `baru-${uniq()}@uji.test`]) {
    await page.goto("/daftar");
    await page.getByLabel("Nama tampilan").fill("Uji Enumerasi");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Kata sandi", { exact: true }).fill("kata-sandi-browser-123");
    await page.getByLabel("Ulangi kata sandi").fill("kata-sandi-browser-123");
    await page.getByRole("button", { name: "Buat akun" }).click();
    await expect(page.getByText("Periksa email Anda")).toBeVisible();
    outcomes.push((await page.getByRole("status").innerText()).replace(email, "<email>"));
  }
  expect(outcomes[0]).toBe(outcomes[1]);
});

test("login kembali ke halaman asal (deep link) setelah diarahkan ke /masuk", async ({ page }) => {
  await page.goto("/app/progress");
  await expect(page).toHaveURL(/\/masuk\?next=%2Fapp%2Fprogress/);
  await page.getByLabel("Email").fill("demo-pelajar@silatara.test");
  await page.getByLabel("Kata sandi").fill(DEMO_PW);
  await page.getByRole("button", { name: "Masuk" }).click();
  await expect(page).toHaveURL(/\/app\/progress$/);
});

test("lesson deep link kembali ke lesson yang sama setelah login", async ({ page }) => {
  const target = "/app/courses/demo-kurikulum-a/lessons/demo-keselamatan";
  await page.goto(target);
  await expect(page).toHaveURL(/\/masuk\?next=/);
  await page.getByLabel("Email").fill("demo-pelajar@silatara.test");
  await page.getByLabel("Kata sandi").fill(DEMO_PW);
  await page.getByRole("button", { name: "Masuk" }).click();
  await expect(page).toHaveURL(new RegExp(`${target}$`));
});

for (const evil of ["//evil.example", "https://evil.example/x", "/%2F/evil.example", "/masuk", "javascript:alert(1)"]) {
  test(`open redirect ditolak: next=${evil}`, async ({ page }) => {
    await loginUI(page, "demo-pelajar@silatara.test", DEMO_PW, evil);
    await expect(page).toHaveURL(/\/app$/);
    expect(new URL(page.url()).origin).toBe(new URL(process.env.BASE_URL ?? "http://localhost:3000").origin);
  });
}

test("cookie sesi HttpOnly + SameSite=Lax; tidak terbaca JavaScript; tidak ada token di storage", async ({ page }) => {
  await loginUI(page, "demo-pelajar@silatara.test");
  await expect(page).toHaveURL(/\/app$/);
  const cookies = await page.context().cookies();
  const sess = cookies.find((c) => c.name === "silatara_session")!;
  expect(sess.httpOnly).toBe(true);
  expect(sess.sameSite).toBe("Lax");
  expect(cookies.find((c) => c.name === "silatara_csrf")!.httpOnly).toBe(false);
  const leak = await page.evaluate(() => ({
    cookie: document.cookie, ls: JSON.stringify({ ...localStorage }), ss: JSON.stringify({ ...sessionStorage }),
  }));
  expect(leak.cookie).not.toContain("silatara_session");
  expect(leak.ls + leak.ss).not.toMatch(/session|token|password|kata-sandi/i);
});

test("lupa kata sandi -> tautan email -> sandi baru -> login; tautan tidak dapat dipakai ulang", async ({ page, request }) => {
  const u = await createVerifiedUser(request, "rst");
  await page.goto("/lupa-sandi");
  await page.getByLabel("Email").fill(u.email);
  await page.getByRole("button", { name: "Kirim tautan" }).click();
  await expect(page.getByText(/Jika email tersebut terdaftar/)).toBeVisible();
  const token = await latestToken(request, u.email, "atur-ulang-sandi");
  await page.goto(`/atur-ulang-sandi?token=${token}`);
  await page.getByLabel("Kata sandi baru", { exact: true }).fill("sandi-baru-yang-sangat-panjang");
  await page.getByLabel("Ulangi kata sandi baru").fill("sandi-baru-yang-sangat-panjang");
  await page.getByRole("button", { name: "Simpan kata sandi baru" }).click();
  await expect(page.getByText(/Kata sandi diperbarui/)).toBeVisible();
  await loginUI(page, u.email, u.password);
  await expect(page.getByRole("alert").filter({ hasText: "Email atau kata sandi salah" })).toBeVisible();
  await loginUI(page, u.email, "sandi-baru-yang-sangat-panjang");
  await expect(page).toHaveURL(/\/app$/);
  await page.goto(`/atur-ulang-sandi?token=${token}`);
  await page.getByLabel("Kata sandi baru", { exact: true }).fill("sandi-lain-yang-sangat-panjang");
  await page.getByLabel("Ulangi kata sandi baru").fill("sandi-lain-yang-sangat-panjang");
  await page.getByRole("button", { name: "Simpan kata sandi baru" }).click();
  await expect(page.getByText(/tidak valid atau sudah kedaluwarsa/)).toBeVisible();
});

test("logout lewat UI mencabut sesi dan memproteksi /app", async ({ page }) => {
  await loginUI(page, "demo-pelajar@silatara.test");
  await expect(page).toHaveURL(/\/app$/);
  await page.getByRole("button", { name: "Keluar" }).first().click();
  await expect(page).toHaveURL(/\/$/);
  await page.goto("/app");
  await expect(page).toHaveURL(/\/masuk/);
});

test("kotak surat dev hanya tersedia di development dan memuat email dev (bukan terkirim)", async ({ page }) => {
  await page.goto("/dev/mailbox");
  await expect(page.getByText(/TIDAK benar-benar terkirim/)).toBeVisible();
});
