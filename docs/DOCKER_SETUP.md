# Docker Setup

## Arsitektur
```
Host (laptop)            Jaringan Docker "silatara"
 :3000 ─────────────►  frontend (Next.js dev, node user uid 1000)
 :8000 ─────────────►  backend  (uvicorn --reload, user app)   ──► db:5432
 :5432 ─────────────►  db       (postgres:16.6, volume pgdata)
```
- Antarlayanan memakai **nama service** (`db`, `backend`), bukan `localhost`. Frontend SSR memanggil `http://backend:8000` (`INTERNAL_API_URL`); browser memanggil `http://localhost:8000` (`NEXT_PUBLIC_API_URL`).
- Urutan start: `db` healthy → `backend` (jalankan `alembic upgrade head`, seed DEMO, lalu uvicorn) healthy → `frontend`.
- Healthcheck: db `pg_isready`; backend `GET /api/v1/health/ready` (cek koneksi DB + migrasi); frontend `GET /`.

## Layanan tambahan (Sprint 7–8)
| Service | Profil | Fungsi |
|---|---|---|
| `worker` | default | outbox, pemindaian, purge media, retensi (healthcheck heartbeat) |
| `clamav` | `scanner` | ClamAV (≈1 GB RAM); aktifkan `SCAN_PROVIDER=clamav` |
| `mailpit` | `mail` | mail sink SMTP lokal untuk uji pengiriman nyata (bukan produksi) |
Uji beban: `make loadtest` (DB scratch `silatara_load`, server kedua port 8099 di dalam container; tidak menyentuh DB dev).

## Volume
| Volume | Isi | Hapus oleh |
|---|---|---|
| `pgdata` | Data PostgreSQL | hanya `make reset-db` / `docker compose down -v` |
| `frontend_node_modules` | Dependency Linux (tidak bentrok dengan host macOS/Windows) | `reset-db` |
| `frontend_next_cache` | Cache `.next` | `reset-db` |
| bind `./backend`, `./frontend` | Kode sumber (hot reload) | — |
| `./backups` | Hasil `make backup` (gitignored) | manual |

Virtualenv Python berada di `/opt/venv` **di dalam image** (di luar bind mount), sehingga tidak ada `.venv` host yang bentrok.

## Hot reload
Backend: `uvicorn --reload` + `WATCHFILES_FORCE_POLLING=true`. Frontend: `next dev` + `WATCHPACK_POLLING=true`. Polling dipakai agar andal di bind mount macOS/Windows; bila CPU terasa tinggi di Linux native, hapus kedua variabel itu di `docker-compose.yml`.

## Dependency & lockfile
- Frontend: `package-lock.json` (Node 22). Menambah paket: `docker compose exec frontend npm install <paket> --save-exact`, commit `package.json` + `package-lock.json`. Anggota lain otomatis tersinkron saat container start.
- Backend: `requirements.txt` (versi top-level dipin tepat) + `constraints.txt` (seluruh transitif). Menambah paket: edit `requirements*.txt`, `make rebuild`, lalu regenerasi `constraints.txt`:
  ```bash
  docker compose run --rm --no-deps --entrypoint pip backend freeze 2>/dev/null | grep -E '^[A-Za-z0-9_.-]+==' > backend/constraints.txt
  ```
- Versi runtime: Node 22 (`node:22-bookworm-slim`), Python 3.12, PostgreSQL 16.6 — dipin di Dockerfile/Compose.

## Target multi-stage
`backend/Dockerfile`: `base` → `dev` (default Compose) / `prod`. `frontend/Dockerfile`: `deps` → `dev` / `build` → `prod` (standalone, non-root). Target `prod` dibuild dan diverifikasi non-root, tetapi **belum dijalankan/dideploy**; belum ada konfigurasi produksi (secret manager, reverse proxy, HTTPS).

## Kamera & HTTPS
- Kamera dibuka oleh **browser di host**, bukan container; tidak ada device passthrough Docker yang diperlukan.
- `http://localhost:*` adalah *secure context* sehingga `getUserMedia` berfungsi tanpa HTTPS.
- `http://192.168.x.x:3000` (uji dari HP/laptop lain) **tidak** diberi kamera oleh browser. Untuk itu gunakan HTTPS (mis. tunnel/dev cert lokal).
- Produksi/staging: HTTPS wajib (TLS di reverse proxy/hosting), cookie `Secure`, dan `Permissions-Policy: camera=(self)` (sudah diset di `next.config.ts`).

## CORS
Backend hanya mengizinkan origin di `CORS_ORIGINS` (default `localhost:3000` & `127.0.0.1:3000`), tanpa wildcard dan tanpa credentials. Nilai `*` diabaikan. Diuji di `backend/tests` dan `scripts/smoke-test.sh`.

## Stack E2E terisolasi
`docker-compose.e2e.yml` (project `silatara-e2e`): db di **tmpfs**, backend + frontend **build produksi**, tanpa port host dan tanpa volume bernama; runner Playwright (profile `browser`, image `mcr.microsoft.com/playwright:v1.65.1-noble`) berbagi network namespace dengan frontend sehingga origin `http://localhost:3000` adalah secure context nyata. `make e2e` / `e2e-api` / `e2e-browser` membangun, menjalankan, lalu mematikan stack itu (`KEEP=1` untuk iterasi, `make e2e-down` untuk mematikan). Tidak menyentuh stack/volume/DB dev. Hasil: `artifacts/` (gitignored): screenshot 3 viewport, laporan HTML, `camera-metrics.json`.

## Image di-pin ke digest
`python:3.12-slim`, `node:22-bookworm-slim`, `postgres:16.6-bookworm`, dan Playwright di-pin `@sha256:` (index multi-arsitektur; diverifikasi dari registry). Memperbarui: ambil digest baru dengan `docker buildx imagetools inspect <tag>` lalu ganti di Dockerfile/compose dalam PR (Dependabot melakukannya otomatis). Stage `prod` frontend tidak menyertakan npm/yarn; stage `prod` backend menjalankan `apt-get upgrade` agar patch keamanan Debian terbawa. `make trivy` memindai keduanya.

## Menambah service baru
1. Tambahkan blok di `docker-compose.yml`, pada network `silatara`, dengan `healthcheck` dan port `127.0.0.1:...`.
2. Layanan opsional (mis. pgAdmin, penyimpanan S3 lokal) → beri `profiles: ["tools"]` agar tidak jalan default; aktifkan `docker compose --profile tools up`.
3. Redis/Celery/broker/object storage **tidak termasuk MVP**; tambahkan hanya dengan alasan tertulis (ADR) dan sebagai profile opsional.
4. Dokumentasikan variabel baru di `.env.example` dan [ENVIRONMENT_VARIABLES](ENVIRONMENT_VARIABLES.md).

## Troubleshooting
| Gejala | Penyebab / solusi |
|---|---|
| `address already in use` | Port host dipakai proses lain → ubah `*_PORT` di `.env` (dan `NEXT_PUBLIC_API_URL`, `CORS_ORIGINS`). |
| Backend `unhealthy`, log `password authentication failed` | Sandi `.env` ≠ sandi di volume lama. Lihat README. |
| `Migrasi gagal setelah 10 percobaan` | `make logs s=backend`; biasanya error migrasi (konflik revisi setelah merge, lihat DATABASE_GUIDE). |
| Frontend `Cannot find module` | `docker compose restart frontend` (entrypoint menjalankan `npm ci` bila lockfile berubah). |
| Perubahan kode tidak terdeteksi | Pastikan repo ada di filesystem yang di-share Docker (WSL2 filesystem di Windows). |
| Mulai dari nol | `make reset-db` lalu `docker compose up --build` (**menghapus data lokal**). |
