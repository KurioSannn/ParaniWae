# Handoff API backend → frontend (Sprint 8)

**Tidak ada file `frontend/` yang diubah sprint ini.** Berikut perubahan kontrak yang perlu diintegrasikan Anggota A. Semua tetap `/api/v1`, sesi cookie + `X-CSRF-Token` untuk mutasi, galat `{error:{code,message,details,request_id}}`.

## 1. Pilot privat
- `CourseSummary` (dan respons kursus/pelajaran/progres) kini memuat **`distribution_scope: "public" | "pilot_private"`** (tambah di `lib/types.ts`).
- **Katalog `/courses`, `/traditions/{slug}`, `/partners`, `/movements` tidak pernah memuat kursus/mitra/gerakan privat.** Peserta menemukan kursus privat lewat `GET /pilot/me/portal` → `course_slug`, lalu `GET /courses/{slug}` dan `GET /courses/{slug}/lessons/{lesson}` (200 bila berhak; **404** bila tidak — tampilkan "tidak ditemukan/tidak punya akses", jangan bedakan).
- `POST /courses/{slug}/enroll` kursus privat: peserta tidak self-enroll (404 bila tak berhak). Enrollment dibuat oleh `POST /pilot/invitations/accept`.
- Galat baru: `403 PROGRAM_READ_ONLY` (program selesai: materi baca-saja; sembunyikan tombol "Tandai selesai"/"Mulai Latihan"), `403 PREVIEW_ONLY` (pengelola pratinjau), `409 NOT_SCANNED`, `423 QUARANTINED` (unduh dokumen mitra yang masih dipindai), `409 PARTNER_NOT_VERIFIED` (terbit kursus privat).
- Program `cancelled/archived`: `/pilot/me/portal` tidak memuat lagi; `/pilot/me/cohorts/{id}` → 404. `completed`: tetap ada, baca-saja (`program_status_label`).
- `POST /manage/courses` & `PATCH` menerima `distribution_scope` (hanya draf/ditolak).
- Media: `PATCH /studio/media/{id}` `access_level` ∈ `private|reviewers|pilot_cohort|public`; item media memuat **`scan_status`** (`pending|clean|infected|error|not_scanned`) + `scan_label`. Media `pending/infected/error` atau izin `revoked/rejected`: `GET /media/{id}/file` → 404 untuk semua orang. Dokumen mitra memuat `scan_status`.
- Header: semua `/api/v1` `Vary: Cookie`; respons ber-sesi `Cache-Control: private, no-store` (jangan menaruh respons ini di cache bersama/SW).

## 2. Admin/ops (read-only, admin saja)
`GET /admin/ops/status` · `GET /admin/ops/doctor?target=current|production` (→ `{BLOCKER:[], WARNING:[], INFO:[]}` tiap item `{id,severity,title,detail,fix}`) · `GET /admin/ops/outbox?status=` (→ `{summary:{by_status,oldest_pending_at}, rows:[…]}`; email dimasker, tanpa isi pesan). Cocok untuk halaman "Operasional" admin.

## 3. Health
`GET /health` → `{status,service,version}` (tanpa `env`). `GET /health/ready` → `{status:"ok"|"degraded", database, media_storage:"ok"|"unavailable", migration_revision}`; 503 hanya bila DB mati.

## 4. Perilaku berubah yang perlu diketahui UI
- Pencabutan izin media sekarang menutup akses untuk staf juga (sebelumnya staf masih dapat membuka).
- Penerbitan gerakan studio tidak lagi mensyaratkan mitra tampil publik (hanya mitra terverifikasi); tampil di Pustaka publik tetap butuh mitra+tradisi publik.
- Pengumuman/undangan: status outbox lebih kaya (`sending`, `dead`) — `GET /pilot/programs/{id}/announcements` tidak berubah; ringkasan pengiriman memakai `pending|sending|sent|dev_sink|dead|undeliverable`.
- Contoh kode galat untuk pesan UI: lihat daftar di atas; semua pesan sudah berbahasa Indonesia.

## 5. Sprint 9 — konten riset pencak silat (tanpa endpoint baru)
- Tidak ada endpoint atau perubahan skema. Konten riset masuk sebagai **draf** lewat `make content-import X=1` dan hanya
  terlihat di Studio (kurator/admin) melalui endpoint Studio yang sudah ada. Katalog publik tidak berubah.
- Gerakan impor: `practice_mode=not_for_practice`, `assessment_enabled=false`, `safety_category` dipetakan
  (lihat `docs/PENCAK_SILAT_CONTENT_CONTRACT.md` §3). Teks `description`, `learning_context`, dan `safety_guidance`
  berupa teks polos/markdown ringan berlabel `[DRAF RISET …]`.
- Animasi berupa **berkas statis** di `content/pencak-silat/animations/<movement_id>/animation.svg` (SMIL, aman tanpa
  skrip). Animasi belum disajikan API mana pun. Bila nanti dipakai UI, sajikan sebagai `<img>`, tampilkan label "interpretasi
  editorial — belum divalidasi instruktur", dan hormati `prefers-reduced-motion` (mis. tampilkan `thumbnail.svg`).

## 6. Pratinjau riset publik (ADR-0007)
- `GET /api/v1/research/{summary,coverage,entities,sources,inventory,movements,movements/{slug},curricula,curricula/{course}/{lesson}}`
  dan `GET /api/v1/research/movements/{slug}/{animation.svg|thumbnail.svg}`. Semua hanya-baca dan publik, dan mengembalikan 404 bila
  `RESEARCH_PREVIEW_ENABLED=false`. Frontend: `/riset/*`, dengan tautan "Riset" di header.
- Login demo sekali klik: `GET /api/v1/auth/demo-accounts`, `POST /api/v1/auth/demo-login {key}` (`DEMO_LOGIN_ENABLED`).
