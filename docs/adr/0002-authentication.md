# ADR-0002: Autentikasi — session server-side + cookie HttpOnly

Status: diterima (19 November 2026) · Tipe: PRODUCT-DECISION · Mengganti: "auth belum diputuskan" di ADR-0001

## Konteks
Frontend Next.js (App Router, SSR) + backend FastAPI + PostgreSQL. MVP, tiga pengembang, tanpa penyedia eksternal (OAuth/SSO/berbayar belum diputuskan). Kebutuhan: register, login, logout, identitas, proteksi halaman & endpoint, RBAC (learner, instructor, curator, admin), Argon2 kompatibel dengan CLI `create-admin`, kredensial tidak di localStorage, kedaluwarsa & pencabutan sesi (PRIVACY §6).

## Opsi
| | Session server-side (opaque token di cookie) | JWT (access + refresh) |
|---|---|---|
| Pencabutan (logout, ganti peran, suspend) | Seketika: hapus/revoke baris sesi | Sulit: perlu denylist/refresh rotation + penyimpanan state juga |
| Penyimpanan di browser | Cookie HttpOnly (tak terbaca JS) | Access token di memori + refresh di cookie, atau token di JS (risiko XSS) |
| SSR Next.js | Teruskan cookie ke API; sederhana | Perlu refresh di server & klien |
| Kompleksitas | Rendah: 1 tabel | Lebih tinggi: rotasi, reuse-detection, kunci penandatangan |
| Skala | Satu lookup DB per request (cukup untuk MVP) | Stateless (tidak dibutuhkan MVP) |

## Keputusan
**Session server-side di PostgreSQL.**
- Token acak 256-bit (`secrets.token_urlsafe(32)`) dikirim sebagai cookie `silatara_session`; DB hanya menyimpan **SHA-256** token (kebocoran DB tidak membocorkan sesi aktif).
- Cookie: `HttpOnly`, `SameSite=Lax`, `Path=/`, `Secure` otomatis aktif bila `APP_ENV != development` (dapat di-override `COOKIE_SECURE`).
- Kedaluwarsa: absolut 7 hari (`SESSION_TTL_HOURS=168`) dan idle 24 jam (`SESSION_IDLE_HOURS=24`). Login selalu membuat sesi baru (anti session-fixation); logout & perubahan status/peran pengguna mencabut sesi.
- **Same-origin lewat proxy**: browser memanggil `/api/v1/*` pada origin frontend; Next.js `rewrites` meneruskan ke `backend:8000`. Akibatnya cookie first-party, tanpa CORS-with-credentials, dan `NEXT_PUBLIC_API_URL` default kosong (relatif). SSR meneruskan header `cookie` ke `INTERNAL_API_URL`.
- **CSRF**: setiap sesi punya `csrf_token` (disimpan di DB, dikirim juga sebagai cookie `silatara_csrf` yang dapat dibaca JS). Semua request mutasi (POST/PUT/PATCH/DELETE) yang memakai sesi wajib menyertakan header `X-CSRF-Token` yang sama (dibandingkan constant-time). Ditambah `SameSite=Lax` dan CORS origin eksplisit tanpa credentials.
- **Password**: Argon2id (`argon2-cffi`, parameter default library, rehash otomatis bila parameter naik) — sama dengan CLI `create-admin`, jadi akun CLI dapat login. Minimal 12 karakter.
- **Brute force**: 5 kegagalan berturut-turut mengunci akun 15 menit (kolom `failed_logins`, `locked_until`); respons kegagalan untuk email tak dikenal identik dengan sandi salah, dan verifikasi dummy dilakukan agar waktu respons mirip.
- **Peran** (`users.role`): `learner` (default semua registrasi), `instructor`, `curator`, `admin`. Peran lain hanya dapat diberikan oleh admin (diaudit) atau CLI. Migrasi memetakan peran lama: `platform_admin→admin`, `content_editor→curator`, `partner_admin→instructor`.
- Otorisasi di server pada setiap endpoint (dependency `require_roles`, cek kepemilikan objek). Frontend hanya menyembunyikan UI; bukan batas keamanan.

## Konsekuensi / trade-off
- Satu query DB per request terautentikasi; dapat di-cache bila perlu.
- Mengakses API lintas-origin langsung (mis. Swagger `/docs` di port backend) tetap bisa memakai cookie, tetapi mutasi perlu header CSRF manual.
- Rewrites Next.js: pada build produksi tujuan proxy tertanam saat build; produksi sebaiknya memakai reverse proxy yang menyatukan `/` dan `/api` pada satu domain (HTTPS wajib, cookie `Secure`).
- Registrasi duplikat mengembalikan 409 (membuka enumerasi email); diterima untuk MVP, perlu verifikasi email + rate limit IP sebelum produksi.
- Belum ada: verifikasi email, reset sandi, MFA, rate limit per-IP, rotasi sesi berkala — dicatat sebagai backlog, bukan klaim.

## Ditolak
JWT (kompleksitas pencabutan tanpa keuntungan MVP); OAuth/SSO/layanan berbayar (belum ada keputusan eksplisit).


---
**Pembaruan 19 Nov 2026:** registrasi tidak lagi mengembalikan sesi dan kini memerlukan verifikasi email; lihat [ADR-0003](0003-auth-hardening.md) untuk verifikasi email, reset sandi, rate limit, dan IP klien. Item "belum ada" di atas yang sudah ditangani di ADR-0003: verifikasi email, reset sandi, rate limit per-IP, enumerasi saat registrasi.
