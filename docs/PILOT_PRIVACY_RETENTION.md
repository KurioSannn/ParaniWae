# Pilot & Impact Studio — privasi, consent, retensi, penghapusan

Berlaku untuk program pilot (`/api/v1/pilot`). Kebijakan versi `PILOT_POLICY_VERSION` (default `2026-11`).

## 1. Dua jenis dasar pemrosesan
| | Wajib untuk mengikuti pilot (operasional) | Opsional (dapat dicabut kapan saja) |
|---|---|---|
| Data | keikutsertaan di cohort, progres pelajaran, **metadata** sesi Practice Studio (waktu, durasi, status), jawaban survei, status undangan | `research_aggregate`: data boleh masuk laporan agregat riset · `publication_quote`: kutipan jawaban terbuka boleh dipublikasikan tanpa nama |
| Dasar | pengakuan eksplisit `operational_ack` saat menerima undangan (wajib; tanpa itu tidak bisa bergabung) | persetujuan terpisah, default **tidak**; disimpan per program + versi kebijakan + waktu |
| Efek pencabutan | keluar dari cohort (`DELETE /pilot/me/cohorts/{id}`): progres belajar tetap milik akun | dikecualikan dari ekspor/laporan riset berikutnya |

**Tidak pernah dikumpulkan:** video mentah, frame, landmark, data biometrik. Practice Studio tetap memproses di perangkat; yang tersimpan hanya metadata sesi (sprint 5).

## 2. Pemisahan data
- **Usage** (sistem): `enrollments`, `lesson_progress`, `practice_sessions` → analytics penggunaan.
- **Survei**: `pilot_surveys`, `survey_responses` → analytics survei (persepsi, bukan penguasaan).
- **Catatan instruktur**: `instructor_notes` → privat, tidak masuk analytics, laporan, maupun ekspor.

## 3. Perlindungan sel kecil
Agregat yang mencakup < `PILOT_MIN_RESPONDENTS` (default 5) orang disembunyikan (`suppressed`) di API, UI, dan CSV (`DISEMBUNYIKAN`). Ekspor hanya agregat tanpa nama/email. Teks terbuka tidak masuk analytics umum maupun CSV. CSV memakai pencegahan formula-injection. Dashboard cohort per peserta adalah **alat operasional instruktur** (dasar operasional), bukan ekspor.

## 4. Retensi dan anonimisasi
- Setelah program berstatus `completed` + `PILOT_RETENTION_DAYS` (default 365), worker menjalankan `anonymize_program`: `survey_responses.user_id` → `NULL` (agregat tetap), `instructor_notes` dihapus, `cohort_invitations` dihapus, `pilot_programs.anonymized_at` diisi, audit `pilot.anonymize`. Idempoten.
- Token undangan disimpan sebagai SHA-256; token mentah hanya tampil sekali.
- Media referensi: `retention_until` per berkas; worker menjalankan `purge_expired` (hapus berkas + baris).
- `notification_outbox`: isi pesan **diredaksi setelah terkirim**; `sent/dev_sink` > 30 hari dan `dead` > 180 hari dibersihkan lewat `outbox-purge` (dry-run default; pending/sending/undeliverable tak pernah dihapus).
- Log audit **tidak** memuat isi jawaban survei maupun token.

## 5. Penghapusan
- Pengguna menarik diri: keluar cohort + cabut persetujuan opsional (UI portal).
- Penghapusan akun: FK `survey_responses.user_id` `ON DELETE SET NULL`, `cohort_members` `ON DELETE CASCADE` → jawaban menjadi anonim, keanggotaan hilang.
- Permintaan penghapusan data program: `python -m app.cli pilot-anonymize` (dry-run default; `--early --reason`; konfirmasi, operator admin, bukti backup, verifikasi, audit tanpa PII). Lihat [PILOT_OPERATIONS_RUNBOOK](PILOT_OPERATIONS_RUNBOOK.md) §4 dan [ADR-0005](adr/0005-pilot-data-lifecycle-outbox-retention.md) (termasuk konflik yang belum diputuskan: usage per-akun).

## 6. Yang tidak boleh disimpulkan
Aktivitas (jumlah pelajaran, sesi, durasi) **bukan** bukti penguasaan teknik. Survei = instrumen draf **belum divalidasi akademik**; hasilnya persepsi peserta. Dashboard menampilkan pernyataan ini.

## 7. Backup dan restore
`make backup-all` (DB `pg_dump -Fc` + arsip `media_data` + manifest sha256; urutan DB dahulu lalu media) dan `make restore-verify d=backups/full_…` (restore ke DB scratch + migrasi maju + verifikasi sha256 setiap berkas media). Berkas media bernama acak & immutable, sehingga arsip yang diambil setelah dump memuat semua berkas yang direferensikan dump (kecuali dihapus/purge di antara keduanya — dilaporkan sebagai "berkas hilang"). Berkas tanpa baris DB dilaporkan sebagai "yatim". Cadangan berisi data pribadi: simpan terenkripsi dan batasi akses (di luar cakupan repo).
