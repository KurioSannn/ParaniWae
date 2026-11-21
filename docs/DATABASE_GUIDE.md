# Database Guide

## Penting: database bersifat lokal
Setiap laptop menjalankan PostgreSQL **sendiri** dengan volume `pgdata` sendiri. Database **tidak** tersinkron antaranggota. Yang disamakan lewat Git adalah **struktur** (migrasi Alembic) dan **data contoh** (seed DEMO di `backend/app/seed.py`). Jangan mengirim dump DB berisi data nyata lewat chat/Git.

## Database uji terpisah
pytest memakai `<POSTGRES_DB>_test` (dibuat otomatis di server yang sama, dimigrasi sampai head, guard nama `*_test`). E2E memakai stack Compose terpisah dengan DB tmpfs. Data uji lama di DB dev: `make test-data-list` / `make test-data-clean` (backup + konfirmasi).

## Skema (migrasi `d33c146c10f0` awal, `880a90406624` auth + konten + pembelajaran)
- **Auth:** `users` (peran learner/instructor/curator/admin, throttle login), `sessions` (hash token, csrf, kedaluwarsa, revoked).
- **Konten (alur kerja + provenance, lihat [CONTENT_WORKFLOW](CONTENT_WORKFLOW.md)):** `cultural_traditions`, `partners`, `instructors`, `tradition_partners`, `movements`, `movement_rubrics` (belum dipakai).
- **Pembelajaran:** `courses` → `course_modules` → `lessons` (+ `lesson_materials`); `enrollments`; `lesson_progress`.
- **Auth lanjutan (migrasi `b3f1c2d4e5a6`):** `users.email_verified_at`, `auth_tokens` (verifikasi/reset, hash, sekali pakai), `rate_limits` (kunci ter-hash), `outbox_emails` (sink dev). Akun yang sudah ada saat migrasi ditandai terverifikasi.
- **Practice Studio (migrasi `c7d2e9a1f3b4`):** `practice_sessions` — user, lesson, status (`in_progress|completed|abandoned|error`), `started_at`/`ended_at`, `active_duration_ms`, `paused_duration_ms`, `model_version`, `client_version`, `quality_summary` (JSONB agregat bertipe), `error_code`. **Tidak ada kolom video/frame/foto/landmark.** CHECK: `ended_at` terisi ⇔ sesi berakhir; durasi 0..24 jam; `ended_at ≥ started_at`. Sesi terbuka >6 jam ditandai `abandoned` (durasi 0, tidak dikarang).
- **Instructor & Partner Studio (migrasi `e5a1b7c9d3f2`):**
  - `partners`: `verification_status` ∈ `draft|pending_verification|verified|rejected|suspended` (lama: `unverified→draft`, `revoked→suspended`; `verified` **non-demo tanpa jejak penyetuju diturunkan ke `pending_verification`** dan `public_listing_consent` dimatikan), penanggung jawab, kontak, `verification_decided_by_user_id/_at`, `submitted_at`. CHECK: `verified` non-demo wajib penyetuju+waktu.
  - `partner_members` (manager|instructor; peran keanggotaan, bukan peran global), `partner_documents` (dokumen persetujuan PRIVAT: metadata + `storage_key`, sha256), `partner_verification_events` (riwayat), `instructors.user_id`.
  - `movement_documents` (satu baris per **versi** + mixin workflow + `needs_revision`, changelog, tinjauan kurator, konfirmasi mitra, `legacy_import`), `movement_phases` (fase berurutan; jumlah/definisi dari instruktur), `reference_media` (metadata + deklarasi hak + `consent_status` + `access_level` + retensi; file di volume privat `media_data`), `movement_annotations` (instructor reference annotation + provenance; fixture hanya `demo-synthetic`).
  - `movements` = identitas + penunjuk versi tayang (`published_document_id`, `published_version_no`, denormalisasi `level`, `safety_category`, `practice_mode`). Gerakan lama dimigrasi menjadi dokumen versi 1 (`legacy_import=true`, tanpa mengubah baris asal).
  - **Trigger DB** `movement_documents_immutable`: versi `pending_review/verified/published/archived` tidak dapat diubah isinya atau dihapus; `published` hanya boleh → `archived`; `archived` final. `movement_phases_immutable`: fase hanya berubah saat versi `draft/needs_revision/rejected`. Indeks unik parsial: maksimal satu versi `published` per gerakan.
  - Migrasi diuji base→head→base→head pada DB scratch dan `alembic check` bersih. Downgrade bersifat lossy untuk status mitra (`pending_verification→unverified`); selalu `make backup` dulu.
- **Pilot & Impact Studio (migrasi `f2c8a4d6e1b9`):** `pilot_programs` (+lifecycle, penyetuju non-demo wajib bukti), `pilot_cohorts`, `cohort_sessions`, `cohort_members` (unik parsial `(program_id,user_id)` untuk `active` → tanpa enrollment ganda; memakai `enrollments` existing), `cohort_invitations` (token ter-hash), `pilot_announcements`, `pilot_consents`, `pilot_surveys`, `survey_responses` (`user_id` NULL setelah anonimisasi), `instructor_notes`, `notification_outbox` (transaksional; `dedupe_key` unik). `reference_media`/`partner_documents` + `scan_status` (`pending|clean|infected|error|not_scanned`; berkas lama = `not_scanned`, media publik lama diturunkan ke private; CHECK: publik ⇒ `clean`). Migrasi diuji pada **salinan data dev** (restore-verify) dan base→head→base→head.
- **Sprint 8 (migrasi `a3d9c5e7b2f1`):** `courses.distribution_scope` (`public|pilot_private`); `reference_media.access_level` + `pilot_cohort` (kolom 14 karakter; CHECK: wajib `verified`+`clean`), `scan_attempts`/`scan_next_at` (media & dokumen mitra); `notification_outbox` → lease (`claimed_by`, `lease_expires_at`), `provider`, `error_category`, `first_attempt_at`, `dead_at`, `body_redacted_at`, status `sending|dead` (`failed`→`dead`; pesan terkirim lama diredaksi); tabel `job_runs` (heartbeat worker + hasil retensi). Diuji up/down/up + `alembic check` + migrasi maju pada salinan data dev (restore-verify).
- **Audit:** `audit_logs`.
- Soft delete (`deleted_at`) pada tabel konten. Index pada FK, `status`.

Invarian yang ditegakkan di DB (CHECK/FK; diuji):
- status konten ∈ {draft, pending_review, needs_revision, rejected, verified, published, archived}; non-demo verified/published wajib penyetuju+waktu+sumber; published wajib `published_at`;
- penilaian AI (`assessment_enabled`) hanya `solo_beginner` + verified/published; rubrik `approved` wajib bukti;
- mitra `public_listing_consent` wajib `verified`; instruktur non-demo terbit wajib `public_profile_consent`;
- **FK komposit:** pelajaran harus berada di modul dari kursus yang sama; `lesson_progress` hanya dapat menunjuk pelajaran **dari kursus yang diikuti** (enrollment) — selain dicek di service, DB menolaknya;
- `completed` wajib `completed_at`; unique (user, course) dan (user, lesson).
Invarian lintas tabel lain (mis. asesmen butuh rubrik disetujui) masih akan ditegakkan di service saat fitur asesmen dibuat.

**Migrasi dari data lama:** `880a90406624` memetakan peran (`platform_admin→admin`, `content_editor→curator`, `partner_admin→instructor`) dan status (`approved→verified` bila demo, `→pending_review` bila non-demo karena tidak ada identitas penyetuju; `in_review→pending_review`; `restricted→draft`; `retired→archived`). Diuji upgrade→downgrade→upgrade pada salinan DB dengan data legacy. Selalu `make backup` sebelum migrasi pada DB berisi data penting.

## Migrasi
```bash
# 1) ubah model di backend/app/models/
make migration m="tambah tabel lessons"      # autogenerate
# 2) PERIKSA berkas di backend/migrations/versions/ (autogenerate tidak sempurna: CHECK, rename, data)
make migrate                                  # terapkan (juga otomatis saat backend start)
make test                                     # test_migrations_applied_to_head
```
Aturan: satu migrasi per PR; jangan mengedit migrasi yang sudah di-merge ke `main` (buat migrasi baru); migrasi harus punya `downgrade` yang masuk akal.

**Konflik "multiple heads"** (dua anggota membuat migrasi dari revisi yang sama): setelah merge, jalankan `docker compose exec backend alembic heads`, lalu `alembic merge -m "merge heads" <rev1> <rev2>` dan commit.

## Seed
`SEED_DEMO_DATA=true` menjalankan `python -m app.cli seed-demo` setiap start (idempotent). Semua baris bertanda `is_demo=true` dan nama berawalan `[DEMO]`. Dilarang memasukkan nama perguruan, instruktur, foto, video, atau materi budaya nyata tanpa izin tercatat. Seed tidak boleh membuat gerakan dengan `assessment_enabled=true`.

## Backup & restore
```bash
make backup                                  # -> backups/silatara_YYYYMMDD_HHMMSS.sql.gz (gitignored)
make restore f=backups/silatara_....sql.gz   # menimpa DB lokal, meminta konfirmasi 'ya'
```
Restore diuji: data yang dihapus kembali setelah restore. Untuk memulai dari kosong: `make reset-db`.

## Akses
`make psql` · atau klien GUI ke `localhost:5432` (user/db/sandi dari `.env`).

## Akun admin lokal
`make create-admin email=anda@contoh.test` (minta kata sandi, min. 12 karakter, hash Argon2 yang sama dengan endpoint login). Peran lain: `docker compose exec backend python -m app.cli create-admin --email x --role curator`.
