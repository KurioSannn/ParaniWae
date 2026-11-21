# Akses pilot privat — keputusan, matriks izin, siklus hidup, kontrak API

Keputusan arsitektur: [ADR-0004](adr/0004-private-pilot-distribution-scope.md). Implementasi: `backend/app/services/access.py`, `visibility.py`; tes: `backend/tests/test_private_access.py`.

## 1. Model
`courses.distribution_scope`: `public` (default) | `pilot_private`. Profil mitra (listing publik) **tidak** menentukan akses materi privat. Tidak ada tabel baru; akses diturunkan dari `partner_members`, `pilot_programs.status`, `pilot_cohorts`, `cohort_members` (status `active`), `enrollments`.

## 2. Siapa melihat kursus `pilot_private` (baca) dan siapa menulis (progres/latihan)
| Aktor | Lihat kursus/pelajaran | Catat progres / Practice | Catatan |
|---|---|---|---|
| Anonim | 404 | – | tidak ada kebocoran lewat katalog/direktori/tradisi/gerakan |
| Pelajar asing / undangan belum diterima | 404 | 404 | undangan tidak memberi akses sebelum `accept` |
| Peserta aktif cohort — program `approved|active` | ✓ | ✓ | |
| Peserta aktif — program `completed` | ✓ (baca-saja) | 403 `PROGRAM_READ_ONLY` | akses historis |
| Peserta — `cancelled|archived|draft|pending_approval` | 404 | 404 | ditutup; pulih bila program kembali sah |
| Peserta keluar/dikeluarkan | 404 | 404 | progres tersimpan, tak terlihat |
| Instruktur ditugaskan (cohort/penanggung jawab program) | ✓ pratinjau | 403 `PREVIEW_ONLY` | dashboard/roster hanya cohort-nya |
| Instruktur anggota mitra, tak ditugaskan | 404 | – | dapat melihat program mitranya (existing) |
| Manager mitra pemilik | ✓ pratinjau | 403 `PREVIEW_ONLY` | semua program/cohort mitranya |
| Pembuat kursus | ✓ pratinjau | – | |
| Kurator | ✓ pratinjau (review) | – | tidak memutuskan verifikasi mitra/penerbitan |
| Admin | ✓ pratinjau | – | separation of duties pada persetujuan tetap (bukan anggota mitra, bukan penulis) |
| Pengguna mitra lain | 404 (semua: program, cohort, analytics, CSV, catatan, media) | – | |

## 3. Siklus hidup akses (status program)
`draft/pending_approval` → tidak ada akses peserta (belum ada peserta; undangan hanya saat `approved|active`) · `approved/active` → penuh · `completed` → baca-saja historis · `cancelled/archived` → tertutup. Akses **tidak** diasumsikan aktif selamanya: dihitung per-permintaan dari status program + keanggotaan.

## 4. Media referensi (`reference_media.access_level`)
`private` (uploader+manager+staf) · `reviewers` (anggota mitra+staf) · **`pilot_cohort`** (peserta aktif cohort yang kursusnya memuat pelajaran terbit bertaut gerakan; wajib izin `verified` + `scan_status=clean`; juga anggota mitra/staf) · `public` (anonim; wajib `verified` + `clean` + gerakan tayang publik). `pending|infected|error` dan izin `rejected|revoked` ⇒ **404 untuk semua orang**. Respons media privat: `Cache-Control: private, no-store`, `nosniff`, `CSP: sandbox`.

## 5. Cache
Semua `/api/v1/*`: `Vary: Cookie`. Permintaan dengan cookie sesi atau path `pilot|studio|me|media|manage|admin|practice|auth|…/lessons/…`: `Cache-Control: private, no-store` (kecuali endpoint menetapkan sendiri, mis. media publik).

## 6. Kontrak API untuk frontend (lihat juga BACKEND_API_HANDOFF)
- Kursus: `distribution_scope` ada di `CourseSummary` (respons detail kursus/pelajaran/progres). **Katalog `/courses` tidak pernah memuat kursus privat**; peserta menemukannya lewat `/pilot/me/portal` (`course_slug`) lalu `/courses/{slug}` (200 hanya bila berhak, selain itu 404).
- `POST /courses/{slug}/enroll` pada kursus privat: 404 bila tak berhak (enrollment dibuat otomatis oleh `POST /pilot/invitations/accept`).
- Galat baru: `PROGRAM_READ_ONLY` (403), `PREVIEW_ONLY` (403), `NOT_SCANNED` (409), `QUARANTINED` (423, dokumen mitra).
- `/pilot/me/portal` dan `/pilot/me/cohorts/{id}` kini hanya memuat/menerima program `approved|active|completed`.
- Pembuatan kursus privat: `POST /manage/courses` menerima `distribution_scope` (`public|pilot_private`); terbit privat butuh mitra `verified` (`PARTNER_NOT_VERIFIED`).
- Media: `PATCH /studio/media/{id}` menerima `access_level: pilot_cohort`; `GET /courses/{slug}/lessons/{lesson}` → `movement.document.media` memuat media `pilot_cohort` untuk peserta sah.

## Hubungan dengan model public-first (ADR-0008, 2026-11-21)

Pengetahuan umum (`content_basis=source_backed`, `distribution_scope=public`) dapat dibaca siapa saja, termasuk isi
pelajaran tanpa login. Kursus `pilot_private` **tidak berubah**: anonim dan non-peserta tetap mendapat 404 untuk
kursus maupun pelajarannya (sebelumnya pelajaran anonim mengembalikan 401; kini 404 agar keberadaannya tidak bocor).
Status program (approved/active/completed/cancelled) tetap menentukan hak baca dan tulis peserta. Lihat
`tests/test_private_access.py` dan `tests/test_public_first_access.py`.

