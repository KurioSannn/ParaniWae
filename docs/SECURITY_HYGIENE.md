# Hygiene Keamanan, Data Pribadi, dan Data Uji

## 1. Dokumen identitas dan surat pernyataan (root repo)
File `Lampiran 3–8 …docx` (surat pernyataan, **bukti KTP peserta**) berada di root repo. Status:
- `.gitignore` memuat `/Lampiran*.docx`. **Terverifikasi** dengan `git check-ignore -v` dan `git ls-files` pada salinan repo di direktori scratch (repo asli belum memakai Git): semua `Lampiran*.docx`, `.env`, `backups/*.sql.gz`, `artifacts/`, dan model `.task` terabaikan; tidak ada file sensitif yang akan terlacak.
- Isi dokumen **tidak pernah dibaca atau dicetak** oleh tooling/log. File belum dipindahkan atau dihapus (butuh keputusan Anda).
- **Langkah penyimpanan aman yang direkomendasikan:** (1) pindahkan ke folder di luar repo, mis. `~/Documents/BudayaGO-berkas-pribadi/`, enkripsi (FileVault/ volume terenkripsi/ pengelola berkas terenkripsi) dan batasi izin (`chmod 700`); (2) setelah repo punya Git, jalankan `git log --all -- 'Lampiran*'` — bila pernah ter-commit, **riwayat harus dibersihkan** (butuh persetujuan karena mengubah histori) dan dokumen dianggap telah terekspos; (3) jangan melampirkannya ke issue/PR/artefak CI; (4) bagikan antaranggota lewat saluran terenkripsi, bukan repo.
- Mungkin ada duplikat berkas publik di root (xlsx Riset, PDF Juknis, `gitingest.md`) yang juga ada di `reference-materials/`; aman, tetapi sebaiknya satu salinan saja.

## 2. Data uji vs data pengembangan
- **pytest** memakai database terpisah `<POSTGRES_DB>_test` (dibuat & dimigrasi otomatis; guard menolak berjalan di DB yang namanya tidak berakhiran `_test`).
- **E2E** (`make e2e`) berjalan di stack Compose terpisah (project `silatara-e2e`, DB di tmpfs, tanpa port host, tanpa volume bernama) dan dimatikan otomatis. Tidak menyentuh DB dev.
- **Data uji lama di DB dev** (dari `make e2e` versi sebelumnya): `make test-data-list` menampilkannya (read-only); `make test-data-clean` membuat backup, menampilkan, lalu meminta mengetik `HAPUS DATA UJI`. **Belum dijalankan** — menunggu persetujuan Anda. Akun `demo-*@silatara.test` dan seed `[DEMO]` tidak termasuk.

## 3. Akun demo & seed
- Akun `demo-*@silatara.test` hanya dibuat saat `APP_ENV=development`. Seed menolak berjalan di luar development (`RuntimeError`); staging butuh `ALLOW_DEMO_CONTENT_SEED=true` dan tetap **tanpa** akun demo.
- Produksi gagal start bila `EXPOSE_DEMO_DATA=true`, sandi DB default/lemah, cookie tidak Secure, atau `MAIL_PROVIDER=dev_sink`. Teruji (`tests/test_security.py`).
- **Sandi demo `demo-sandi-12345` bersifat publik** (ada di dokumentasi). Jangan pernah memakai sandi itu atau domain `.test` pada sistem yang terbuka ke internet. Bila `APP_ENV=development` terlanjur terpapar publik, anggap seluruh akun demo terkompromi.

## 4. Konfigurasi proxy tepercaya (rate limit per-IP)
`X-Forwarded-For` hanya dipercaya bila peer langsung ada di `TRUSTED_PROXY_CIDRS`; IP klien = entri ke-`TRUSTED_PROXY_HOPS` dari kanan. Contoh: di belakang satu load balancer → `TRUSTED_PROXY_CIDRS=<CIDR LB>`, `TRUSTED_PROXY_HOPS=1`; CDN + LB → hops=2. **Kosongkan** bila backend langsung terbuka ke internet. Verifikasi dengan permintaan ber-XFF palsu dan pastikan rate limit tetap per klien sebenarnya. **Jangan menganggap proxy Next.js tepercaya**: terbukti ia tidak menimpa XFF, sehingga XFF palsu lolos (sudah diperbaiki dengan default kosong; probe regresi ada di `backend/tests/e2e_flow.py`). Di dev, semua klien berbagi satu kunci (IP container frontend) → batas per-IP bersifat global; ini aman tetapi bukan per-klien.

## 4b. Log & cache (Sprint 8)
Log API/worker = JSON satu baris di stdout dengan `request_id`/`job_id`. **Query string tidak pernah dicatat** (tautan undangan memuat `?token=`; access log uvicorn dimatikan `--no-access-log` dan diganti access log sendiri dengan template rute). Filter redaksi menyamarkan token, sandi, cookie, `Authorization`, email, dan string 40+ karakter; kunci ekstra bernama `password|token|secret|cookie|authorization|landmark|body|answers|note` dimasking. Respons ber-sesi `Cache-Control: private, no-store`; semua `/api/v1` `Vary: Cookie`. Isi outbox yang sudah terkirim diredaksi (menyimpan tautan undangan). Cadangan: lihat PILOT_OPERATIONS_RUNBOOK §5 (terenkripsi; kunci di luar repo).

## 5. Rahasia
`.env` tidak di-commit; `.env.example` hanya berisi placeholder. Secret produksi di secret manager. Jangan menaruh secret di `NEXT_PUBLIC_*` atau artefak CI. Artefak CI (screenshot/laporan) hanya memuat data demo dan kredensial uji efemeral; trace Playwright (hanya saat gagal) dapat memuat sandi uji itu.

## 6. Dependensi, image, dan pemindaian (20 Nov 2026)
- `npm audit` (frontend, e2e-browser): 0 kerentanan; `pip-audit` pada `constraints.txt`: tidak ada kerentanan (basis data advisori saat dijalankan).
- **Image dasar di-pin ke digest** (index multi-arsitektur dari registry, diverifikasi `docker buildx imagetools inspect`; bukan tebakan): `python:3.12-slim`, `node:22-bookworm-slim`, `postgres:16.6-bookworm`, Playwright `v1.65.1-noble`, Trivy `0.76.2`. Perbarui lewat Dependabot/PR (digest basi = risiko patch tertinggal).
- **Trivy 0.76.2** (`make trivy`, gagal bila HIGH/CRITICAL yang SUDAH ADA perbaikannya): pada image produksi awal ditemukan 1 HIGH backend (`zlib1g`, perbaikan tersedia) dan 10 HIGH frontend (semua di npm CLI bawaan image Node, bukan kode aplikasi). **Diperbaiki:** `apt-get upgrade` di stage prod backend; npm/yarn dihapus dari stage prod frontend (runtime hanya `node server.js`; diverifikasi HTTP 200). Hasil akhir: **0 HIGH/CRITICAL yang dapat diperbaiki** di kedua image; misconfig Dockerfile: 0.
- **Temuan tanpa perbaikan upstream tetap ada dan tidak disembunyikan:** backend 106 HIGH `affected` + 1 `fix_deferred`; frontend 32 HIGH `affected` + 5 `fix_deferred` + 1 CRITICAL `will_not_fix` (`zlib1g CVE-2023-45853`, Debian 12; fungsi minizip `zipOpenNewFileInZip4` tidak dipakai Node). Ini **risiko yang diterima sementara** (kaji ulang tiap rilis base image; evaluasi base lebih ramping — B4). Mengatakan "image bersih" **tidak benar**.
- Pemindaian tidak mencakup: dependensi `dev`, image `dev`/Playwright, rahasia di repo (pemindaian `fs` tidak dijalankan agar tidak menyentuh dokumen identitas).

## 7. Verifikasi aturan ignore & dokumen identitas
`./scripts/verify-gitignore.sh` memverifikasi `.gitignore` memakai repo sementara berisi berkas KOSONG bernama sama (tanpa membuka isi dokumen, tanpa `git init` di repo asli). Hasil: semua `Lampiran*.docx`, `.env`, backup, model, artifacts terabaikan; 0 berkas sensitif terlacak. Berkas identitas saat ini berizin `-rw-r--r--` (terbaca semua pengguna lokal): disarankan `chmod 600` lalu **memindahkannya secara manual** ke penyimpanan terenkripsi di luar repo (langkah di §1). Agen tidak memindahkan/menghapus/membaca berkas tersebut.
