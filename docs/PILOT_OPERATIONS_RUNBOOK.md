# Runbook operasi pilot

Semua perintah dari root repo; `$DC` = `docker compose` (produksi: sesuaikan). **Jangan** `down -v`. Perintah destruktif punya dry-run default.

## 1. Onboarding perguruan untuk pilot privat (tanpa listing publik)
1. Admin menetapkan peran `instructor` untuk pengelola perguruan (Admin → pengguna).
2. Pengelola membuat profil mitra (Studio Instruktur) → menambah anggota, tradisi, dokumen persetujuan → ajukan verifikasi. **Jangan** mencentang persetujuan direktori publik.
3. Admin lain (bukan anggota mitra) memverifikasi dengan bukti (`evidence_ref`).
4. Buat kursus dengan `distribution_scope=pilot_private`, terbitkan (kurator → admin). Buat program (draf) → cohort → ajukan → admin menyetujui → manager mengaktifkan → buka cohort.
5. Undang peserta (tautan sekali pakai; email opsional terikat). Peserta registrasi/login → menerima (wajib pengakuan data operasional).
6. Pantau: dashboard cohort, `doctor`, outbox.

## 2. Worker
`$DC up -d worker` — putaran tiap `WORKER_INTERVAL_S` (60): heartbeat → outbox → pemindaian → purge media kedaluwarsa → retensi terjadwal. Aman >1 instans. Henti anggun: `docker stop` (SIGTERM) melepas klaim outbox yang belum diproses. Healthcheck memeriksa `/tmp/worker-heartbeat` < 3 menit; `doctor` memeriksa heartbeat di DB. Log JSON (`job_id`) di `docker compose logs worker`.

## 3. Outbox
```
$DC exec backend python -m app.cli outbox-status
$DC exec backend python -m app.cli outbox-list --status dead      # tanpa isi pesan; email dimasker
$DC exec backend python -m app.cli outbox-requeue --id <uuid>      # hanya dead yang isinya belum diredaksi
$DC exec backend python -m app.cli outbox-purge                    # DRY-RUN; --execute untuk menghapus
```
Status: `pending` (menunggu/retry), `sending` (diklaim; lease habis → dipulihkan), `sent` (SMTP menerima), `dev_sink` (hanya kotak surat dev), `undeliverable` (provider tak tersedia; tidak menghabiskan percobaan; >72 jam → dead), `dead` (terminal). Insiden "pesan tak terkirim": `outbox-status` → `doctor` (smtp/worker) → `outbox-list --status dead` (kategori galat) → perbaiki provider → pesan `undeliverable` otomatis terkirim; `dead` diantre ulang manual.
Uji SMTP lokal: `$DC --profile mail up -d mailpit` lalu `docker compose exec -e MAILPIT_HOST=mailpit backend pytest tests/test_smtp_mailpit.py`.

## 4. Anonimisasi & retensi
```
$DC exec backend python -m app.cli retention-report
$DC exec backend python -m app.cli pilot-anonymize [--program ID] [--cohort ID] [--completed-before 2026-01-01]   # DRY-RUN default
# eksekusi (setelah make backup-all):
$DC exec backend python -m app.cli pilot-anonymize --program ID --execute --operator admin@domain \
    --confirm "ANONIMKAN 1 PROGRAM" --backup-manifest /backups/full_.../manifest.json
```
Di luar jadwal retensi: `--early --reason "permintaan penghapusan peserta"` (tercatat). Verifikasi otomatis pasca-operasi; audit `pilot.anonymize` (operator + jumlah). Kebijakan & batasan: PILOT_PRIVACY_RETENTION, ADR-0005.

## 5. Backup & restore
```
export BACKUP_ENCRYPTION_KEY_FILE=/rahasia/silatara-backup.key   # chmod 600, DI LUAR repo; BACKUP_KEY_ID=label
make backup-all                                    # DB + media + manifest (+HMAC)
make restore-verify d=backups/full_<id>            # scratch: sha256 → HMAC → dekripsi → restore → migrasi maju → sha256 tiap media
BACKUP_DESTINATION=s3://bucket/prefix BACKUP_S3_ENDPOINT=... ./scripts/backup-ship.sh backups/full_<id>   # BELUM diverifikasi di repo ini
```
- **Kunci:** buat `openssl rand -base64 32 > key; chmod 600 key`; simpan salinan di pengelola rahasia terpisah dari cadangan (kehilangan kunci = cadangan tak terbaca). **Rotasi:** buat kunci baru → cadangan baru memakai kunci baru (manifest `key_id`) → pertahankan kunci lama selama cadangan lama masih dalam retensi → verifikasi `restore-verify` dengan kunci masing-masing → baru hapus kunci lama. Cadangan lama tidak dienkripsi ulang otomatis.
- **Restore ke produksi** (manual, di luar skrip otomatis): hentikan app+worker → `restore-verify` pada cadangan yang sama di scratch → `pg_restore` ke DB kosong baru → ekstrak media ke volume baru → `alembic upgrade head` → `doctor` → arahkan app. Jangan menimpa DB berjalan.
- **Kegagalan restore-verify:** `sha256 tidak cocok` = berkas rusak/diubah (pakai cadangan sebelumnya); `HMAC` = manifest diubah/kunci salah; `dekripsi` = kunci salah; `berkas hilang` = media dihapus/purge di antara dump dan arsip (jalankan ulang backup); `yatim` = informasi saja.
- **Terukur (dataset dev kecil):** backup 2,2 dtk; restore-verify 5,5 dtk (dump 168 KB, media 0 berkas). Dengan 140 MB media (stack uji) restore-verify selesai sukses; **RPO/RTO produksi belum diukur** — ukur pada ukuran data nyata sebelum menjanjikan angka.

## 6. Media & pemindai
`SCAN_PROVIDER=clamav` + `$DC --profile scanner up -d clamav` (≈1 GB RAM, unduh signature saat start). Unggahan → karantina (`pending`, tak dapat diakses siapa pun) → worker memindai (`clean` dipindah; `infected` dihapus; clamd mati/timeout → tetap `pending` dengan backoff, setelah 8 percobaan `error`; keduanya TIDAK pernah bersih). Purge: `python -m app.cli media-purge` (dry-run; `--execute`) hanya media yang `retention_until`-nya lewat; **berkas yatim hanya dilaporkan**.

## 7. Doctor & health
`make doctor` / `make doctor T=production` (BLOCKER → exit 1). Admin API: `GET /api/v1/admin/ops/{status,doctor,outbox}`. Publik: `/api/v1/health` (liveness), `/health/ready` (DB; media `degraded` bila tak tersedia).

## 8. Insiden keamanan / kebocoran data (ringkas)
1. **Contain:** cabut sesi terdampak (Admin → suspend pengguna), cabut undangan (`DELETE /pilot/invitations/{id}`), `consent_status=revoked` pada media, matikan akses jaringan bila perlu.
2. **Nilai:** audit log (`audit_logs`), log JSON (`request_id`), `outbox-list`; tentukan data & subjek terdampak (jumlah saja di laporan).
3. **Pulihkan:** rotasi secret (DB, SMTP, kunci backup); verifikasi dengan `doctor`.
4. **Beritahu:** pemilik proyek + perguruan mitra segera; pemberitahuan kepada subjek data/otoritas sesuai hukum yang berlaku (UU PDP) — **keputusan & wording di luar repo (hukum)**.
5. **Pasca-insiden:** catat di TEAM_ISSUES, tambah tes regresi.
