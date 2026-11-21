# Kontrak bersama: Pilot & Impact Studio

Ditetapkan **sebelum** A/B/C bekerja paralel. Perubahan kontrak = PR yang sama dengan pembaruan `frontend/src/lib/types.ts`.

## 0. Prinsip (batas keras)
- Program pilot **tidak resmi** sampai disetujui pihak berwenang (admin, dengan bukti + identitas + waktu). Mitra belum terverifikasi hanya boleh membuat program **draf**; mengajukan/menyetujui hanya untuk mitra `verified` atau mitra/program `[DEMO]`.
- Memakai ulang: `partners`, `partner_members`, `instructors`, `courses`, `lessons`, `enrollments`, `lesson_progress`, `practice_sessions`, `audit_logs`. **Tidak ada** tabel enrollment/progres baru: bergabung ke cohort = membuat/memakai `enrollments` yang sama.
- Data penggunaan (usage), survei, dan catatan instruktur **dipisah** (tabel, endpoint, dan tampilan berbeda).
- Tidak ada raw video/biometrik. Aktivitas ≠ penguasaan teknik; dashboard tidak pernah menyimpulkan penguasaan.
- Survei = instrumen **draf, belum divalidasi secara akademik**; label itu wajib tampil.
- Notifikasi lewat outbox transaksional. Status "terkirim" hanya bila provider benar-benar mengirim; `dev_sink` = "disimpan di kotak surat dev", provider tak terkonfigurasi = "tertunda (belum ada pengirim)".
- Privasi k-anonimitas: agregat survei/penggunaan yang mencakup < `PILOT_MIN_RESPONDENTS` (default 5) orang **disembunyikan**.

## 1. Model data
| Tabel | Isi |
|---|---|
| `pilot_programs` | `partner_id`, `name`, `objective`, `description`, `responsible_user_id` (anggota mitra), `default_course_id?`, `start_date`, `end_date`, `capacity`, `status`, `is_demo`, `approved_by_user_id/approved_at/approval_evidence_ref`, `review_note`, `created_by_user_id` |
| `pilot_cohorts` | `program_id`, `name`, `course_id`, `instructor_user_id`, `start_date`, `end_date`, `capacity`, `status`(`draft|open|closed|completed`) |
| `cohort_sessions` | `cohort_id`, `title`, `starts_at`, `ends_at`, `location_note` (jadwal) |
| `cohort_members` | `cohort_id`, `program_id` (denormalisasi), `user_id`, `status`(`active|withdrawn|removed`), `joined_at`, `invitation_id`, `enrollment_id`. **Unik** `(cohort_id,user_id)` dan **unik parsial** `(program_id,user_id)` untuk `active` → tidak ada enrollment ganda per program |
| `cohort_invitations` | `cohort_id`, `email?`, `token_hash` (SHA-256; token mentah hanya sekali), `expires_at`, `accepted_by_user_id/accepted_at`, `revoked_at/revoked_by`, `created_by` |
| `pilot_announcements` | `program_id`, `cohort_id?`, `author_user_id`, `title`, `body` |
| `pilot_consents` | `program_id`, `user_id`, `scope`(`research_aggregate|publication_quote`), `granted`, `policy_version`, `decided_at` |
| `pilot_surveys` | `program_id`, `kind`(`baseline|endline|feedback_learner|feedback_instructor`), `title`, `status`(`draft|open|closed`), `questions` JSONB, `instrument_note` |
| `survey_responses` | `survey_id`, `cohort_id?`, `user_id?` (NULL setelah anonimisasi), `answers` JSONB, `submitted_at`. Unik `(survey_id,user_id)` |
| `instructor_notes` | `cohort_id`, `participant_user_id`, `author_user_id`, `note` — **bukan bagian analytics/ekspor** |
| `notification_outbox` | `kind`, `to_email`, `subject`, `body`, `status`, `attempts`, `next_attempt_at`, `last_error`, `dedupe_key` (unik), `sent_at` |

Pemindaian file: `reference_media` & `partner_documents` + `scan_status` (`pending|clean|infected|error|not_scanned`), `scanned_at`, `scan_detail`.

## 2. Lifecycle program
`draft → submit → pending_approval → approve (admin) → approved → activate → active → complete → completed → archive → archived`; `reject` (pending→draft + catatan wajib); `cancel` dari `draft|pending_approval|approved|active`; `archive` dari `completed|cancelled`.
- `submit`: pembuat/manager/penanggung jawab; mitra harus `verified` (atau demo); wajib nama, tujuan, periode, kapasitas, penanggung jawab, ≥1 cohort dengan kurikulum terbit.
- `approve`: **admin** yang bukan penulis dan bukan anggota mitra; non-demo wajib `evidence_ref`.
- `activate`: admin atau manager mitra. Undangan baru hanya diterima saat program `approved|active`.

## 3. Lifecycle undangan
`pending → accepted | revoked | expired`. Token acak 32 byte url-safe, hash di DB, kedaluwarsa (default 14 hari, maks 60), sekali pakai, dapat dicabut. Bila `email` diisi, hanya akun dengan **email terverifikasi yang sama** yang dapat menerima. Penerimaan wajib `operational_ack=true`; persetujuan riset opsional terpisah. Gagal bila kohort penuh, tidak `open`, program tidak aktif/disetujui, atau pengguna sudah aktif di program yang sama (409).

## 4. Matriks izin
| Aksi | learner | instruktur cohort | manager mitra | admin |
|---|---|---|---|---|
| Lihat program/cohort sendiri, jadwal, pengumuman, isi survei | ✓ | ✓ | ✓ | ✓ |
| Buat/ubah program (draf), cohort, sesi, undangan | – | ✓ (mitranya) | ✓ | ✓ |
| Ajukan program | – | ✓ | ✓ | ✓ |
| Setujui/aktifkan/tolak program | – | – | aktifkan | ✓ (setujui bukan anggota) |
| Pengumuman | – | ✓ | ✓ | ✓ |
| Dashboard cohort (partisipan) | – | ✓ | ✓ | ✓ |
| Catatan instruktur | – | ✓ (cohort-nya) | ✓ | ✓ |
| Analytics program + ekspor | – | cohort-nya | ✓ | ✓ |
| Isi survei | ✓ (anggota aktif) | umpan balik instruktur | – | – |
Non-anggota → 404.

## 5. API (`/api/v1/pilot`, sesi + CSRF)
Program: `GET/POST /programs`, `GET/PATCH /programs/{id}`, `POST /programs/{id}/transition {action,note,evidence_ref}`.
Cohort: `POST /programs/{id}/cohorts`, `GET/PATCH /cohorts/{id}`, `PUT /cohorts/{id}/sessions` (ganti jadwal), `GET /cohorts/{id}/members`, `DELETE /cohorts/{id}/members/{user_id}`.
Undangan: `POST /cohorts/{id}/invitations {email?,days}` (mengembalikan token **sekali**), `GET /cohorts/{id}/invitations`, `DELETE /invitations/{id}` (cabut), `GET /invitations/preview?token=` (publik; tanpa data pribadi), `POST /invitations/accept {token,operational_ack,research_aggregate,publication_quote}`.
Portal: `GET /me/portal`, `GET /me/cohorts/{id}`, `DELETE /me/cohorts/{id}` (keluar), `PUT /me/programs/{id}/consents`.
Pengumuman: `GET/POST /programs/{id}/announcements`.
Survei: `GET/POST /programs/{id}/surveys`, `POST /surveys/{id}/transition {open|close}`, `GET /me/surveys`, `POST /surveys/{id}/responses`, `POST /programs/{id}/surveys/templates` (buat dari templat draf).
Catatan: `GET/POST /cohorts/{id}/notes`.
Analytics: `GET /programs/{id}/analytics?cohort_id&from&to`, `GET /cohorts/{id}/dashboard`, `GET /programs/{id}/report.csv?…`. (PDF tidak tersedia: tidak ada pustaka PDF di dependensi; halaman laporan memakai cetak-ke-PDF peramban.)
Operasional: worker `python -m app.cli worker` (outbox, purge media kedaluwarsa, pemindaian, anonimisasi).

## 6. Definisi metrik (sumber → rumus)
- **Anggota aktif** = `cohort_members.status='active'`.
- **Penyelesaian pelajaran** = Σ `lesson_progress.completed` (pelajaran terbit pada kurikulum cohort) ÷ (anggota aktif × jumlah pelajaran terbit). Per-peserta: selesai/total.
- **Belum mulai** = anggota aktif tanpa satu pun `lesson_progress` dan tanpa `practice_sessions`.
- **Aktif pada pekan k** = ≥1 `lesson_progress.updated_at` atau `practice_sessions.started_at` dalam pekan ke-k sejak `cohort.start_date`. **Retensi pekan k** = aktif_k ÷ anggota aktif.
- **Perlu perhatian** = (a) belum mulai ≥3 hari sejak bergabung, atau (b) tidak ada aktivitas ≥7 hari padahal belum selesai dan program `active`. Ambang tercantum di UI; ini sinyal operasional, bukan penilaian.
- **Praktik** = jumlah sesi, jumlah selesai/ditinggalkan, total durasi aktif, rata-rata sesi per peserta aktif (dari `practice_sessions`; **hanya metadata**).
- **Respons survei** = jumlah `survey_responses`; **response rate** = respons ÷ anggota aktif saat ini. Pilihan ganda → distribusi; rating → rata-rata + distribusi; terbuka → hanya jumlah + kutipan tanpa identitas untuk pengelola.
- Semua agregat dengan n < K ditandai `suppressed=true` dan nilainya `null`.

## 7. Skema pertanyaan survei
`{id, type: single_choice|rating|open_text, text, required, options?: string[], scale?: {min,max,min_label,max_label}}`; id unik, 1–40 pertanyaan; `rating` skala 1–5 default; jawaban divalidasi terhadap pertanyaan (opsi valid, rentang, panjang ≤ 2000).

## 8. Consent & retensi
Operasional (wajib untuk ikut): data enrollment, progres, metadata sesi Practice Studio, jawaban survei dasar — diakui lewat `operational_ack`. Opsional terpisah: `research_aggregate` (boleh masuk ekspor agregat riset), `publication_quote` (kutipan terbuka boleh dipublikasikan). Dapat dicabut kapan saja; pencabutan mengeluarkan dari ekspor riset berikutnya. Retensi: `PILOT_RETENTION_DAYS` (default 365) setelah program `completed`: jawaban survei dianonimkan (`user_id=NULL`), `instructor_notes` dihapus, undangan dihapus. Detail: `docs/PILOT_PRIVACY_RETENTION.md`.

## 9. Pembagian file
- **A:** `frontend/src/app/page.tsx`, `components/Brand.tsx`, `components/landing/**`, `frontend/src/app/app/pilot/**`, `app/undangan/**`, `components/pilot/**`, `lib/pilot-api.ts`.
- **B:** `backend/app/{models/pilot.py,schemas/pilot.py,services/{pilot,pilot_invites,notify,scanner,retention}.py,api/v1/pilot.py}`, migrasi, `cli.py`, `scripts/{backup-all,restore-verify}.sh`, compose worker/scanner, `tests/test_pilot*.py`, `tests/test_ops*.py`.
- **C:** `backend/app/services/pilot_analytics.py`, `api` bagian analytics/report, `components/pilot/Analytics*.tsx`, `tests/test_pilot_analytics.py`.

## 10. Kriteria penerimaan
Admin membuat program dari mitra terverifikasi → persetujuan → cohort → undangan → peserta menerima (registrasi/login) → belajar (progres + sesi latihan) → survei baseline/endline → dashboard instruktur → laporan CSV yang menyembunyikan sel kecil; semua tercatat di audit; undangan single-use, kedaluwarsa, dapat dicabut; enrollment ganda ditolak; outbox jujur; file belum dipindai tidak pernah publik; backup mencakup DB + media dan restore terverifikasi.
