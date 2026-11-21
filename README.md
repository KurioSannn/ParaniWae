# SILATARA

Platform pembelajaran dan pelestarian pencak silat Nusantara yang dipandu mitra budaya. **Status: alur belajar dasar berjalan dengan konten contoh [DEMO].**

**Practice Studio (baru):** dari lesson, tekan *Mulai Latihan* → kamera + Web Worker MediaPipe → skeleton langsung di atas video → sesi dengan timer/jeda → ringkasan + riwayat (dasbor/progres). Hanya kualitas input; **tanpa penilaian gerakan**; hanya metadata sesi yang disimpan. Coba tanpa kamera: tambahkan `?sim=1` pada URL studio (mode SIMULASI, dev saja).

**Sudah ada dan teruji:** Docker dev environment; autentikasi (session cookie, RBAC learner/instructor/curator/admin); katalog tradisi, perguruan, kurikulum; pelajaran, enrollment, progres; alur konten draft → review → verified → published dengan provenance + audit; UI Bahasa Indonesia; fondasi kamera + MediaPipe + quality gate input.
**Belum ada / belum diverifikasi:** materi budaya resmi, kemitraan terkonfirmasi, penilaian gerakan AI (menunggu rubrik instruktur), uji kamera/MediaPipe di browser nyata, verifikasi email/reset sandi (lihat [Batasan saat ini](#batasan-saat-ini)).

### Coba alurnya (akun demo, hanya `APP_ENV=development`; sandi publik, jangan dipakai di luar dev)
Buka frontend → **Masuk** dengan `demo-pelajar@silatara.test` / `demo-sandi-12345` → Akademi → ikuti kurikulum → buka pelajaran → *Tandai selesai* → Progres. Peran lain: `demo-instruktur@` (penanggung jawab Perguruan Contoh A), `demo-instruktur-b@` (mitra lain), `demo-kurator@`, `demo-admin@`, `demo-admin-2@silatara.test` (sandi sama) → menu **Studio Instruktur** (dokumentasi gerakan, Partner Workspace, Calibration Workspace) dan **Kelola Konten**. Semua data Studio demo berlabel `[DEMO]`. Pilot demo: `demo-peserta-1…6@silatara.test` (sandi sama) tergabung di *[DEMO] Program Pilot Contoh*. Operasi: `make doctor` (kesiapan, hanya-baca), `make loadtest` (opt-in, DB scratch), runbook di `docs/PILOT_OPERATIONS_RUNBOOK.md`. Pemeliharaan: layanan `worker` (outbox email, pemindaian, purge, retensi); cadangan penuh `make backup-all`, uji restore `make restore-verify d=backups/full_…`. Dokumentasi API interaktif: `<backend>/docs`. Mendaftar akun baru? Email verifikasi muncul di **kotak surat dev**: `<frontend>/dev/mailbox` (email dev **tidak dikirim**).

Dokumen produk: [PROJECT_CONTEXT](PROJECT_CONTEXT.md) · [PRD](PRD.md) · [DESIGN](DESIGN.md) · [AGENTS](AGENTS.md) · [CLAUDE](CLAUDE.md). README paket awal tersimpan di [docs/STARTER_PACK_README.md](docs/STARTER_PACK_README.md).

## Prasyarat
Hanya **Docker** (Docker Desktop, atau Docker Engine + Compose v2) dan **Git**. Tidak perlu memasang Python, Node.js, atau PostgreSQL di laptop. `make` opsional (semua target hanyalah perintah `docker compose`). Windows: gunakan WSL2 dan clone di dalam filesystem WSL agar hot reload cepat.

## Mulai cepat
```bash
git clone <url-repo> && cd SILATARA
docker compose up --build        # pertama kali ±2–5 menit (unduh image)
```
Tidak perlu `.env`: semua nilai punya default aman-untuk-dev. (Opsional: `make setup` membuat `.env` dengan sandi acak dan UID/GID Anda; **wajib di Linux** bila UID Anda bukan 1000.)

| Service | URL host | Dalam jaringan Docker |
|---|---|---|
| Frontend (Next.js) | http://localhost:3000 | `frontend:3000` |
| Backend (FastAPI) | http://localhost:8000 · docs: `/docs` | `backend:8000` |
| PostgreSQL 16 | `localhost:5432` | `db:5432` |

Port terikat ke `127.0.0.1` saja (tidak terbuka ke Wi-Fi/LAN). Bila port bentrok, ubah `FRONTEND_PORT`/`BACKEND_PORT`/`DB_PORT` di `.env` — lihat [ENVIRONMENT_VARIABLES](docs/ENVIRONMENT_VARIABLES.md).

Cek berhasil: buka http://localhost:3000/status, atau `make smoke`.

## Perintah harian
| Tujuan | Perintah |
|---|---|
| Start (foreground / background) | `make up` / `make start` |
| Stop (data tetap) | `make stop` |
| Restart satu service | `make restart s=backend` |
| Build ulang tanpa cache | `make rebuild` |
| Log | `make logs s=backend` |
| Masuk container | `make shell-backend` · `make shell-frontend` · `make psql` |
| Migrasi | `make migrate` · `make migration m="deskripsi"` |
| Tes + lint + typecheck | `make test` |
| Smoke test infrastruktur | `make smoke` |
| **E2E terisolasi** (stack terpisah, DB tmpfs): API+SSR + Playwright/Chromium (kamera palsu, visual+axe+kontras, auth, belajar) | `make e2e` (`e2e-api`, `e2e-browser`) |
| Data uji lama di DB dev (tampil / hapus setelah backup+konfirmasi) | `make test-data-list` / `make test-data-clean` |
| Practice Studio simulasi (dev) | `…/lessons/<lesson>/practice?sim=1&scenario=full\|partial\|out_of_frame\|multiple\|waiting` |
| Benchmark A/B Worker vs main-thread (opsional) | `make bench` |
| Pindai image produksi (Trivy) | `make trivy` |
| Aksesibilitas statis cepat (tanpa CSS; yang otoritatif: spec visual Playwright) | `make a11y` |
| Unduh model MediaPipe | `make mediapipe-assets` |
| Buat akun admin lokal | `make create-admin email=anda@contoh.test` |
| Backup / restore DB | `make backup` · `make restore f=backups/<file>.sql.gz` |
| Bersihkan container/image (**data DB aman**) | `make clean` |
| **Hapus semua data lokal** (konfirmasi eksplisit) | `make reset-db` |

Tanpa `make`: lihat [Makefile](Makefile), setiap target berisi perintah `docker compose` yang bisa dijalankan langsung.

## Struktur repo
```
backend/          FastAPI, SQLAlchemy, Alembic (app/, migrations/, tests/)
frontend/         Next.js App Router + TypeScript + Tailwind (src/app, src/features, src/lib)
scripts/          setup, smoke-test, backup/restore, reset
docs/             arsitektur, data model, API, panduan operasional, ADR (docs/adr/)
execution/        handoff UI, workstream tim, checklist akseptasi
reference-materials/  sumber resmi & riset (jangan diubah)
docker-compose.yml  orkestrasi dev lokal
```

## Dokumentasi operasional
[DOCKER_SETUP](docs/DOCKER_SETUP.md) · [TEAM_WORKFLOW](docs/TEAM_WORKFLOW.md) · [ENVIRONMENT_VARIABLES](docs/ENVIRONMENT_VARIABLES.md) · [DATABASE_GUIDE](docs/DATABASE_GUIDE.md) · [API_ENDPOINTS](docs/API_ENDPOINTS.md) · [CONTENT_WORKFLOW](docs/CONTENT_WORKFLOW.md) · [AI_CV_FOUNDATION](docs/AI_CV_FOUNDATION.md) · [PRACTICE_STUDIO_CONTRACT](docs/PRACTICE_STUDIO_CONTRACT.md) · [PRIVACY_DATA_FLOW](docs/PRIVACY_DATA_FLOW.md) · [REVERSE_PROXY_READINESS](docs/REVERSE_PROXY_READINESS.md) · [Benchmark](docs/benchmarks/README.md) · [SECURITY_HYGIENE](docs/SECURITY_HYGIENE.md) · [QA kamera manual](docs/QA_MANUAL_CAMERA_CHECKLIST.md) · [TEAM_ISSUES](docs/TEAM_ISSUES.md) · [CONTRIBUTING](CONTRIBUTING.md) · [ADR-0001](docs/adr/0001-docker-dev-environment.md) · [ADR-0002](docs/adr/0002-authentication.md) · [ADR-0003](docs/adr/0003-auth-hardening.md)

## Troubleshooting singkat
- **`port is already allocated` / `address already in use`**: proses lain memakai port itu. Cari: `lsof -nP -iTCP:8000 -sTCP:LISTEN`. Hentikan proses tersebut atau ubah port di `.env`, dan sesuaikan `NEXT_PUBLIC_API_URL` serta `CORS_ORIGINS`.
- **Backend gagal login ke DB setelah mengganti `POSTGRES_PASSWORD`**: sandi hanya dipakai saat volume DB pertama dibuat. Ubah sandi di DB (`ALTER USER`) atau `make reset-db` (menghapus data lokal).
- **Linux: `Permission denied` pada file hasil container**: set `HOST_UID`/`HOST_GID` (`make setup`), lalu `make rebuild`.
- **Frontend tidak memuat dependency baru setelah `git pull`**: entrypoint menjalankan `npm ci` otomatis bila `package-lock.json` berubah; untuk backend jalankan `make rebuild` bila `requirements*.txt`/`constraints.txt` berubah.
- Lebih lengkap: [DOCKER_SETUP § Troubleshooting](docs/DOCKER_SETUP.md#troubleshooting).

## Kamera dan HTTPS
Pemrosesan pose/tangan direncanakan berjalan **di browser** (MediaPipe) sehingga video mentah tidak dikirim ke backend. Browser mengizinkan kamera pada `http://localhost` (dianggap secure context), jadi dev lokal tidak butuh HTTPS. Mengakses lewat IP LAN atau domain **memerlukan HTTPS** — lihat [DOCKER_SETUP § Kamera & HTTPS](docs/DOCKER_SETUP.md#kamera--https). Fitur kamera belum diimplementasikan.

## Batasan saat ini
- Rate limit dev bersifat **global** (bukan per-klien); reverse proxy produksi belum terbukti ([REVERSE_PROXY_READINESS](docs/REVERSE_PROXY_READINESS.md)). Image: 0 HIGH/CRITICAL yang dapat diperbaiki menurut Trivy, tetapi ada temuan tanpa perbaikan upstream ([SECURITY_HYGIENE §6](docs/SECURITY_HYGIENE.md)).
- Auth: verifikasi email, reset sandi, rate limit (PostgreSQL), anti-enumerasi, redirect aman sudah ada ([ADR-0003](docs/adr/0003-auth-hardening.md)); belum ada MFA/CAPTCHA, SMTP nyata belum diuji (dev memakai sink), konfigurasi proxy tepercaya produksi harus diisi.
- Konten: semua seed adalah **[DEMO] fiktif**. Persetujuan mitra dicatat sebagai teks bukti oleh kurator/admin; sistem tidak dapat memverifikasi keasliannya. Peran mitra berlingkup-mitra belum ada.
- Kamera/MediaPipe: inferensi berjalan di **Web Worker** (tanpa fallback main-thread); siklus hidup, pemuatan model, privasi, dan responsivitas teruji di Chromium dengan kamera PALSU. **Deteksi pose manusia, webcam fisik, dan Safari belum diverifikasi** ([checklist manual](docs/QA_MANUAL_CAMERA_CHECKLIST.md)). Benchmark headless sintetis (bukan kinerja perangkat nyata): [hasil](docs/AI_CV_FOUNDATION.md#benchmark-implementasi-lama-main-thread-vs-web-worker). Tidak ada penilaian gerakan.
- CI (`.github/workflows/ci.yml`) belum pernah dijalankan di GitHub (repo belum di-push); perintahnya sudah dijalankan lokal.
- Tenggat kelayakan BUDAYA GO! 2026 adalah 31 Maret 2026 (Juknis). Repo ini tidak boleh dipakai sebagai bukti kelayakan; jangan memanipulasi timestamp.
