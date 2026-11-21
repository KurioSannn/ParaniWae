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

### pilot & impact (kontrak: [PILOT_STUDIO_CONTRACT](PILOT_STUDIO_CONTRACT.md))

Sesi + CSRF. Non-anggota mitra → 404. Pelajar hanya `/me/*`, pratinjau/penerimaan undangan, dan pengisian survei.

| Method | Path | Ringkasan |
|---|---|---|
| GET/POST | `/api/v1/pilot/programs` | Daftar / buat program (draf) |
| GET/PATCH | `/api/v1/pilot/programs/{id}` | Detail / ubah (draf) |
| POST | `/api/v1/pilot/programs/{id}/transition` | `submit,approve,reject,activate,complete,cancel,archive` |
| POST | `/api/v1/pilot/programs/{id}/cohorts` | Buat cohort |
| GET/PATCH | `/api/v1/pilot/cohorts/{id}` | Detail (peserta, undangan) / ubah |
| POST | `/api/v1/pilot/cohorts/{id}/status` | `open,closed,completed` |
| PUT | `/api/v1/pilot/cohorts/{id}/sessions` | Ganti jadwal |
| DELETE | `/api/v1/pilot/cohorts/{id}/members/{user_id}` | Keluarkan peserta |
| POST | `/api/v1/pilot/cohorts/{id}/invitations` | Buat undangan (token sekali) |
| DELETE | `/api/v1/pilot/invitations/{id}` | Cabut undangan |
| GET | `/api/v1/pilot/invitations/preview?token=` | Pratinjau publik (tanpa data pribadi; rate-limited) |
| POST | `/api/v1/pilot/invitations/accept` | Terima (`operational_ack` wajib; consent opsional) |
| GET | `/api/v1/pilot/me/portal`, `/me/cohorts/{id}`, `/me/surveys` | Learner Pilot Portal |
| DELETE | `/api/v1/pilot/me/cohorts/{id}` | Keluar cohort |
| PUT | `/api/v1/pilot/me/programs/{id}/consents` | Ubah persetujuan opsional |
| GET/POST | `/api/v1/pilot/programs/{id}/announcements` | Pengumuman (+ antrean outbox) |
| GET/POST | `/api/v1/pilot/programs/{id}/surveys[/templates]` | Survei / dari templat draf |
| POST | `/api/v1/pilot/surveys/{id}/transition` · `/responses` | Buka/tutup · kirim jawaban |
| GET/POST | `/api/v1/pilot/cohorts/{id}/notes` | Catatan instruktur (terpisah dari analytics) |
| GET | `/api/v1/pilot/programs/{id}/analytics?cohort_id&from&to` | Analytics (usage, retensi, survei, consent) |
| GET | `/api/v1/pilot/cohorts/{id}/dashboard` | Instructor Cohort Dashboard |
| GET | `/api/v1/pilot/programs/{id}/report.csv` | Ekspor CSV agregat tanpa identitas (PDF: cetak dari peramban; tidak ada pustaka PDF) |

Media/dokumen: respons memuat `scan_status`; berkas `pending|infected|error` tidak dapat diakses siapa pun (404 media, 423 dokumen mitra); `not_scanned` hanya internal; publik wajib `clean`.

### operasional (admin, hanya-baca) & health

| Method | Path | Ringkasan |
|---|---|---|
| GET | `/api/v1/health` | Liveness (tanpa env/konfigurasi) |
| GET | `/api/v1/health/ready` | Readiness: DB (503 bila mati), `media_storage`, `migration_revision` |
| GET | `/api/v1/admin/ops/status` | DB, migrasi, media, scanner, worker, outbox, email, retensi (tanpa secret/path) |
| GET | `/api/v1/admin/ops/doctor?target=` | Kesiapan deployment: BLOCKER/WARNING/INFO |
| GET | `/api/v1/admin/ops/outbox?status=` | Ringkasan + daftar outbox untuk investigasi (email dimasker, tanpa isi) |

CLI: `python -m app.cli doctor|outbox-status|outbox-list|outbox-requeue|outbox-purge|media-purge|pilot-anonymize|retention-report|worker|worker-once|verify-media`. Perubahan kontrak untuk frontend: [BACKEND_API_HANDOFF](BACKEND_API_HANDOFF.md).

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

## Pembaruan 2026-11-21: public-first (ADR-0008)

| Endpoint | Akses | Catatan |
|---|---|---|
| `GET /api/v1/courses/{slug}/lessons/{lesson}` | **publik** untuk kursus publik; login menambah `enrolled`/`lesson_status` | sebelumnya wajib login; kursus privat tetap 404 |
| `GET /api/v1/research/summary` · `coverage` · `entities` · `sources` · `inventory` | publik | basis pengetahuan (berkas `content/` & `research/`) |
| `GET /api/v1/research/traditions` · `traditions/{slug}` | publik | tradisi beserta gerakan, kursus, dan entitas terkait |
| `GET /api/v1/research/movements` · `movements/{slug}` · `movements/{slug}/{animation.svg,thumbnail.svg}` | publik | SVG: `Content-Security-Policy: default-src 'none'`, `nosniff` |
| `GET /api/v1/research/courses/{slug}` · `curricula` · `curricula/{course}/{lesson}` | publik | struktur kursus dan isi pelajaran |
| `GET /api/v1/auth/demo-accounts` · `POST /api/v1/auth/demo-login` | hanya pengembangan (`DEMO_LOGIN_ENABLED`) | 404 di produksi |

Respons publik kini memuat `content_basis` dan `provenance.attribution` ("Redaksi SILATARA" untuk `source_backed`).
Untuk konten `source_backed`, `partner_name` dikosongkan.



## Sprint 10
- `/api/v1/directory/*`: `places`, `list`, `places/{slug}`, `facets`, `stats`, `heritage-areas`, `submissions` (POST publik; GET & `{id}/review` kurator/admin). Lihat `NATIONAL_DIRECTORY_CONTRACT.md`.
- `/api/v1/research/character`, `/character/model.glb`, `/character/reference/{movement_id}`, `/assessment/protocols[/{movement_id}]` (publik, baca saja).
- `/api/v1/assessments` (POST/GET, login) dan `DELETE /assessments/{id}`: ringkasan skor latihan; lihat `MOVEMENT_ASSESSMENT_CONTRACT.md`.
