# ADR-0004: Pilot privat — `distribution_scope` dan otorisasi akses materi

Status: diterima (20 November 2026) · Tipe: ARCHITECTURE-DECISION · Mengganti asumsi "publikasi mitra = prasyarat akses kursus"

## Masalah
`vis.course_ok()` mensyaratkan tradisi **dan mitra** tampil publik (status published + `public_listing_consent`). Akibatnya perguruan yang tidak ingin profilnya dipublikasikan tidak dapat menjalankan pilot: pelajar tidak dapat membuka kursusnya.

## Keputusan
1. Pisahkan **visibilitas profil** (direktori publik) dari **hak akses materi**. Tambah `courses.distribution_scope ∈ {public, pilot_private}` (default `public`; tidak ada duplikasi partner/course/enrollment/identitas).
2. Kursus `pilot_private` tidak pernah masuk katalog/pencarian/direktori publik. Aksesnya diturunkan dari relasi yang SAH: peserta **aktif** cohort yang memakai kursus itu, program berstatus `approved|active` (baca+tulis) atau `completed` (baca-saja historis). `draft|pending_approval|cancelled|archived`, undangan belum diterima, anggota keluar/dikeluarkan ⇒ **tidak ada akses** (404).
3. Otorisasi **terpusat**: `services/access.py` + `visibility.course_ok(viewer, write)` / `lesson_ok(viewer, write)`. Default tanpa `viewer` = hanya publik ⇒ aman-secara-default; seluruh jalur (katalog, detail, pelajaran, materi, progres, latihan, media, `/me/progress`, portal) memakai predikat yang sama.
4. Pengelola yang sah (pratinjau baca-saja): manager mitra pemilik, instruktur/penanggung jawab yang ditugaskan pada cohort/program yang memakai kursus, pembuat kursus, kurator & admin (review). Instruktur mitra tak ditugaskan & mitra lain ⇒ 404. Pratinjau tidak boleh mencatat progres (`PREVIEW_ONLY`).
5. Penerbitan: kursus privat butuh **mitra terverifikasi** (atau demo), bukan listing publik. Penerbitan gerakan studio juga tidak lagi memaksa listing publik; tampil di Pustaka publik tetap ditentukan `movement_ok()` (mitra+tradisi publik), sehingga mitra privat tidak bocor. Cakupan kursus tidak bisa diubah setelah terbit (aturan draft-only existing).
6. Media: level akses baru `pilot_cohort` (wajib izin terverifikasi + lolos pindai) untuk peserta cohort yang kursusnya memuat pelajaran terbit bertaut gerakan itu. **Pencabutan izin menutup akses untuk semua orang seketika** (termasuk staf) — mengubah perilaku sebelumnya (staf masih bisa membuka media yang dicabut).
7. Cache: seluruh respons `/api/v1` `Vary: Cookie`; permintaan ber-sesi/path privat `Cache-Control: private, no-store`.

## Konsekuensi / risiko
- Pelajar yang berhenti/dicabut kehilangan akses meski masih punya baris `enrollments` (progres tetap tersimpan, tidak terlihat).
- Admin/kurator dapat membuka semua kursus privat (pratinjau). Pemisahan tugas dipertahankan pada persetujuan (tidak ada self-approval), bukan pada akses baca.
- Pelajaran/kursus **publik** yang dipakai cohort tidak berubah.
- Frontend perlu menangani `distribution_scope`, kode galat baru, dan tidak menampilkan kursus privat di katalog (backend sudah memfilter). Lihat BACKEND_API_HANDOFF.
