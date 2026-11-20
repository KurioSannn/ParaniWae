# API Endpoints (v1)

Dihasilkan dari OpenAPI backend (`/docs` interaktif, `/openapi.json`). Konvensi:
- Pagination: `?page=1&page_size=12` → `{items, page, page_size, total, total_pages}` (page_size maks 100).
- Error: `{"error": {"code", "message", "details", "request_id"}}`; header `X-Request-ID`; `429` menyertakan `Retry-After`.
- Autentikasi: cookie sesi HttpOnly + header `X-CSRF-Token` untuk mutasi ([ADR-0002](adr/0002-authentication.md), [ADR-0003](adr/0003-auth-hardening.md)).
- `POST /auth/register` selalu `202` dengan badan identik (anti-enumerasi) dan **tidak** membuat sesi; login memerlukan email terverifikasi.
- Endpoint email (register, verify, reset) mengembalikan `503 FEATURE_UNAVAILABLE` bila email belum dikonfigurasi. `/dev/mailbox` hanya ada saat `APP_ENV=development`.
- Dari browser gunakan path relatif `/api/v1/...` (diproksikan Next.js).
- Practice Studio: hanya metadata sesi + ringkasan agregat; skema `extra=forbid` menolak landmark/frame/foto ([kontrak](PRACTICE_STUDIO_CONTRACT.md)). Semua milik sendiri (data orang lain → 404).

### health

| Method | Path | Ringkasan |
|---|---|---|
| GET | `/api/v1/health` | Liveness |
| GET | `/api/v1/health/ready` | Readiness |

### auth

| Method | Path | Ringkasan |
|---|---|---|
| POST | `/api/v1/auth/register` | Daftar akun pelajar (verifikasi email) |
| POST | `/api/v1/auth/verify-email` | Verifikasi email dengan token sekali pakai |
| POST | `/api/v1/auth/resend-verification` | Kirim ulang email verifikasi |
| POST | `/api/v1/auth/password-reset/request` | Minta tautan reset kata sandi |
| POST | `/api/v1/auth/password-reset/confirm` | Tetapkan kata sandi baru dengan token reset |
| POST | `/api/v1/auth/login` | Masuk |
| POST | `/api/v1/auth/logout` | Keluar (mencabut sesi) |
| GET | `/api/v1/auth/me` | Identitas pengguna saat ini |

### katalog publik

| Method | Path | Ringkasan |
|---|---|---|
| GET | `/api/v1/traditions` | Katalog tradisi |
| GET | `/api/v1/traditions/{slug}` | Detail tradisi |
| GET | `/api/v1/partners` | Katalog perguruan |
| GET | `/api/v1/partners/{slug}` | Detail perguruan |
| GET | `/api/v1/instructors` | Daftar instruktur |
| GET | `/api/v1/instructors/{slug}` | Detail instruktur |
| GET | `/api/v1/movements` | Referensi gerakan |
| GET | `/api/v1/movements/{movement_id}` | Detail gerakan |
| GET | `/api/v1/courses` | Katalog kurikulum/akademi |

### akademi & progres

| Method | Path | Ringkasan |
|---|---|---|
| GET | `/api/v1/courses/{slug}` | Detail kurikulum |
| POST | `/api/v1/courses/{slug}/enroll` | Daftar kurikulum |
| DELETE | `/api/v1/courses/{slug}/enroll` | Berhenti mengikuti kurikulum |
| GET | `/api/v1/courses/{slug}/lessons/{lesson_slug}` | Isi pelajaran (perlu login) |
| PUT | `/api/v1/me/lessons/{lesson_id}/progress` | Catat progres pelajaran |
| GET | `/api/v1/me/progress` | Ringkasan progres belajar saya |
| GET | `/api/v1/me/enrollments` | Kurikulum yang diikuti |

### manajemen konten

| Method | Path | Ringkasan |
|---|---|---|
| POST | `/api/v1/manage/modules` | Buat modul kurikulum |
| PATCH | `/api/v1/manage/modules/{module_id}` | Ubah modul |
| DELETE | `/api/v1/manage/modules/{module_id}` | Hapus modul (harus tanpa pelajaran) |
| POST | `/api/v1/manage/materials` | Tambah materi pendukung pelajaran |
| DELETE | `/api/v1/manage/materials/{material_id}` | Hapus materi pendukung |
| GET | `/api/v1/manage/kinds` | Jenis konten yang boleh saya kelola |
| GET | `/api/v1/manage/{kind}` | Daftar konten (semua status; instruktur hanya miliknya) |
| POST | `/api/v1/manage/{kind}` | Buat konten (selalu berstatus draft) |
| GET | `/api/v1/manage/{kind}/{obj_id}` | Detail konten + riwayat audit |
| PATCH | `/api/v1/manage/{kind}/{obj_id}` | Ubah konten (hanya draft/ditolak) |
| DELETE | `/api/v1/manage/{kind}/{obj_id}` | Hapus lunak konten |
| POST | `/api/v1/manage/{kind}/{obj_id}/transition` | Ubah status alur kerja |

### studio instruktur & mitra (peran instruktur/kurator/admin; kontrak: [INSTRUCTOR_PARTNER_CONTRACT](INSTRUCTOR_PARTNER_CONTRACT.md))

Sesi + CSRF; pagination `{items,page,page_size,total,total_pages}`; non-anggota mitra mendapat **404** (bukan 403) agar keberadaan mitra/dokumen lain tidak bocor.

| Method | Path | Ringkasan |
|---|---|---|
| GET | `/api/v1/studio/dashboard` | Instructor Dashboard: perlu perhatian, mitra, hitungan status, cakupan tradisi, aktivitas |
| GET/POST | `/api/v1/studio/partners` | Daftar mitra saya / buat profil mitra (draf; pembuat menjadi manager) |
| GET/PATCH | `/api/v1/studio/partners/{id}` | Partner Workspace / ubah profil (draf atau ditolak) |
| POST/DELETE | `/api/v1/studio/partners/{id}/members[/{user_id}]` | Tambah / keluarkan anggota (manager/instruktur) |
| PUT/DELETE | `/api/v1/studio/partners/{id}/traditions/{tradition_id}` | Cakupan tradisi |
| POST | `/api/v1/studio/partners/{id}/documents` | Unggah dokumen persetujuan (multipart; privat) |
| GET/DELETE | `/api/v1/studio/partner-documents/{id}[/file]` | Unduh (manager/kurator/admin) / hapus |
| POST | `/api/v1/studio/partners/{id}/verification` | `submit,verify,reject,suspend,reopen,reinstate,publish_listing,unlist` |
| GET | `/api/v1/studio/partners/{id}/history` | Riwayat verifikasi |
| GET/POST | `/api/v1/studio/movements` | Daftar (filter `q,status,tradition_id,partner_id,safety_category,level`) / buat gerakan + versi 1 |
| GET | `/api/v1/studio/movements/{id}` | Detail: versi aktif, versi, pelajaran tertaut, media, kelengkapan |
| GET/POST | `/api/v1/studio/movements/{id}/versions[/{no}]` | Satu versi / buat versi baru dari versi tayang |
| PATCH | `/api/v1/studio/documents/{doc_id}` | Ubah isi (hanya draf/revisi/ditolak; dipakai autosave) |
| PUT | `/api/v1/studio/documents/{doc_id}/phases` | Ganti seluruh fase berurutan |
| POST | `/api/v1/studio/documents/{doc_id}/transition` | `submit,curator_review,confirm_partner,request_revision,reject,approve,publish,archive` |
| GET | `/api/v1/studio/movements/{id}/history` | Riwayat keputusan & perubahan (audit) |
| GET/PUT/DELETE | `/api/v1/studio/movements/{id}/lessons[/{lesson_id}]` | Pelajaran yang dapat ditautkan / tautkan / lepas |
| GET/POST | `/api/v1/studio/movements/{id}/media` | Daftar / unggah media (multipart + deklarasi hak) |
| PATCH/DELETE | `/api/v1/studio/media/{id}` | Verifikasi izin, akses, retensi / hapus |
| GET/POST | `/api/v1/studio/movements/{id}/annotations` | Anotasi referensi instruktur |
| PATCH/DELETE | `/api/v1/studio/annotations/{id}` | Ubah/tinjau / hapus anotasi |
| GET | `/api/v1/media/{id}/file` | Berkas media terotorisasi (anonim hanya bila publik + izin terverifikasi + gerakan terbit) |

Publik tambahan: `GET /api/v1/movements` kini menerima `partner, level, safety_category, partner_verified`; `GET /api/v1/movements/{id}` memuat `document` (versi tayang: fase, sumber, media publik, penyusun); `GET /api/v1/movements/{id}/versions` = riwayat versi publik (changelog). **Dihapus:** jenis `movements` dari `/manage/*`; `PartnerIn` tidak lagi menerima `verification_status`/`public_listing_consent` (verifikasi hanya lewat Partner Workspace).

### admin

| Method | Path | Ringkasan |
|---|---|---|
| GET | `/api/v1/admin/users` | Daftar pengguna |
| PATCH | `/api/v1/admin/users/{user_id}` | Ubah peran/status pengguna (diaudit) |
| GET | `/api/v1/admin/audit-logs` | Jejak audit |

### dev (hanya development)

| Method | Path | Ringkasan |
|---|---|---|
| GET | `/api/v1/dev/mailbox` | Kotak surat DEV (sink): email tidak benar-benar terkirim |

### practice studio

| Method | Path | Ringkasan |
|---|---|---|
| POST | `/api/v1/practice-sessions` | Mulai sesi Practice Studio (metadata saja) |
| POST | `/api/v1/practice-sessions/{session_id}/complete` | Akhiri sesi (durasi + ringkasan agregat kualitas input) |
| GET | `/api/v1/practice-sessions/{session_id}` | Detail sesi milik sendiri |
| GET | `/api/v1/me/practice-sessions` | Riwayat latihan saya |
| GET | `/api/v1/me/practice-summary` | Ringkasan & tren latihan saya |

Total: 47 operasi.
