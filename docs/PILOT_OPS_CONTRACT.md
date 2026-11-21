# Kontrak teknis & ownership — Sprint 8 (Pilot Operations & Production Readiness)

**Larangan:** tidak ada perubahan di `frontend/` (milik Anggota A). Perubahan kontrak API untuk frontend didokumentasikan di [BACKEND_API_HANDOFF](BACKEND_API_HANDOFF.md); frontend mengintegrasikannya sendiri.

## Audit blocker sebelumnya (S-11 … S-19), kondisi di awal sprint → akhir sprint
| ID | Blocker | Awal | Akhir | Bukti |
|---|---|---|---|---|
| S-11 | Pilot/kemitraan nyata masih `[DEMO]` | terbuka | **terbuka (butuh pemilik/mitra nyata)**; yang dapat dilakukan backend: pilot privat tanpa listing publik | PRIVATE_PILOT_ACCESS.md |
| S-12 | Survei draf belum divalidasi akademik | terbuka | **terbuka (keputusan riset)** — label tetap wajib | — |
| S-13 | Pembersihan outbox + CLI anonimisasi | terbuka | **selesai** | `outbox-purge`, `pilot-anonymize`, `tests/test_outbox.py`, `tests/test_retention_cli.py` |
| S-14 | SMTP produksi belum dikonfigurasi | terbuka | **terbuka**; pengiriman SMTP **nyata ke mail sink (Mailpit) terbukti**; status jujur tetap | `tests/test_smtp_mailpit.py` (opt-in) |
| S-15 | ClamAV ±1 GB RAM | terbuka | **dievaluasi + dipantau**; fail-closed, retry/backoff terbatas, health | `scanner.health`, doctor, tes pemindai |
| S-16 | PDF laporan | terbuka | **terbuka** (tidak ada pustaka PDF; cetak dari peramban) | — |
| S-17 | Kursus pilot hanya terlihat bila mitra publik | terbuka | **selesai** (distribution scope) | `tests/test_private_access.py` (10 tes) |
| S-18 | Uji beban | belum | **selesai (baseline terukur, 1 mesin)**; bukan sertifikasi kapasitas | LOAD_TEST_REPORT.md |
| S-19 | Backup belum terenkripsi/off-site | terbuka | **enkripsi selesai & teruji**; **off-site: skrip ada, BELUM terverifikasi** (tanpa kredensial/bucket/aws CLI) | scripts/backup-*.sh |

## Ownership (file) — B backend, C infra/data
- **B:** `backend/app/services/{access,visibility,progress,practice,media,manage,movement_studio,movement_public,pilot,retention,notify,backup_check}.py`, `models/{learning,studio,pilot}.py`, migrasi `a3d9c5e7b2f1`, `schemas/{manage,public,studio}.py`, `api/v1/{academy,admin}.py`, `tests/test_private_access.py`, `test_retention_cli.py`, `test_media_security.py`.
- **C:** `backend/app/services/{outbox,jobs,ops,scanner,pilot_analytics}.py`, `worker.py`, `ops_cli.py`, `cli.py`, `core/{logging,cache_headers,query_stats,errors,config,db}.py`, `api/v1/health.py`, `loadtest/**`, `scripts/{backup-all,restore-verify,backup-ship}.sh`, `docker-compose*.yml`, `Makefile`, `tests/test_outbox.py`, `test_observability.py`, `test_smtp_mailpit.py`.
- **Bersama (butuh dua pihak):** `core/config.py` (variabel baru), `pyproject.toml`, `docs/*`.

## Rencana berdasar risiko
1. Kebocoran materi/profil privat (risiko tertinggi, blok pilot) → distribution scope + otorisasi terpusat + tes matriks.
2. Kehilangan/duplikasi notifikasi → outbox berlease + idempotensi + DLQ.
3. Pelanggaran privasi (data tidak dianonimkan, log bocor token) → CLI retensi aman + redaksi log + tanpa query string.
4. Pemulihan bencana → backup terenkripsi + restore terverifikasi.
5. Media berbahaya → fail-closed pemindai, validasi isi, purge aman.
6. Kesiapan operasional → doctor, health bertingkat, load test.
