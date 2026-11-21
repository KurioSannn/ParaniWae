# Environment Variables

Sumber: `docker-compose.yml` (default dev) ← `.env` (override lokal, **tidak di-commit**) ← `.env.example` (template yang di-commit; tanpa secret nyata).

| Variabel | Default | Dipakai oleh | Keterangan |
|---|---|---|---|
| `APP_ENV` | `development` | backend | Penanda lingkungan. |
| `POSTGRES_USER` / `POSTGRES_DB` | `silatara` | db, backend | Dibuat saat volume pertama kali diinisialisasi. |
| `POSTGRES_PASSWORD` | `silatara_dev_password` | db, backend | **Hanya dev.** Berlaku saat volume dibuat; mengubahnya kemudian tidak mengubah sandi DB yang ada. `make setup` membuat sandi acak. |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `db` / `5432` | backend | Diset di Compose; nama service, bukan localhost. |
| `FRONTEND_PORT` `BACKEND_PORT` `DB_PORT` | 3000 / 8000 / 5432 | Compose | Port di host (terikat 127.0.0.1). |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | backend | Dipisah koma. Harus memuat origin frontend persis (termasuk port). `*` diabaikan. |
| `RUN_MIGRATIONS` | `true` | backend | Jalankan `alembic upgrade head` saat start. |
| `SEED_DEMO_DATA` | `true` | backend | Muat data **[DEMO]** fiktif (idempotent). |
| `EXPOSE_DEMO_DATA` | `true` | backend | Bila `false`, endpoint publik tidak mengembalikan data DEMO. **Wajib `false` di luar dev.** |
| `INTERNAL_API_URL` | `http://backend:8000` | frontend (server) | Diset di Compose. |
| `NEXT_PUBLIC_API_URL` | *(kosong)* | frontend (browser) | Kosong = relatif (`/api/v1`) lewat proxy Next → cookie first-party (disarankan). Isi hanya bila API di origin lain (butuh CORS+credentials). **Jangan taruh secret** di `NEXT_PUBLIC_*`. Tertanam saat build prod. |
| `HOST_UID` / `HOST_GID` | 1000 | build backend | UID/GID user non-root di container. Linux: isi `id -u`/`id -g`. |
| `SESSION_TTL_HOURS` / `SESSION_IDLE_HOURS` | 168 / 24 | backend | Masa berlaku absolut / idle sesi login. |
| `COOKIE_SECURE` | otomatis | backend | Kosong: `Secure` aktif bila `APP_ENV != development`. Wajib HTTPS di luar dev. |
| `DEMO_USER_PASSWORD` | `demo-sandi-12345` | backend (seed) | Sandi akun demo; akun hanya dibuat saat `APP_ENV=development`. |
| `DEMO_LOGIN_ENABLED` | `true` (compose dev) · `false` (default kode) | backend | Tombol "Masuk cepat dengan akun demo" di `/masuk` (`GET /auth/demo-accounts`, `POST /auth/demo-login`). Aktif hanya bila bukan produksi dan `EXPOSE_DEMO_DATA=true`; di produksi menjadi BLOCKER `doctor`. |
| `RESEARCH_PREVIEW_ENABLED` | `true` (compose dev) · `false` (default kode) | backend | Bagian publik `/riset` + API `GET /api/v1/research/*` (hasil riset berlabel draf; ADR-0007). |
| `RESEARCH_REPO_DIR` | `/repo` | backend | Lokasi mount `content/` & `research/` (compose: hanya-baca). |
| `MAIL_PROVIDER` | `dev_sink` | backend | `dev_sink` (hanya development; email disimpan di DB, **tidak dikirim**) \| `smtp` \| `none`. Produksi wajib `smtp`. |
| `MAIL_FROM` `SMTP_HOST` `SMTP_PORT` `SMTP_USER` `SMTP_PASSWORD` `SMTP_STARTTLS` | — / 587 / true | backend | Konfigurasi SMTP. Tanpa ini fitur email → `503`. |
| `PUBLIC_BASE_URL` | `http://localhost:${FRONTEND_PORT}` | backend | Origin frontend untuk tautan di email. |
| `TRUSTED_PROXY_CIDRS` / `TRUSTED_PROXY_HOPS` | *(kosong)* / 1 | backend | Proxy yang boleh menyuplai `X-Forwarded-For`; IP klien = entri ke-N dari kanan. **Produksi: isi sesuai topologi nyata** ([SECURITY_HYGIENE](SECURITY_HYGIENE.md) §4). Default kode: kosong (tidak ada proxy tepercaya). |
| `RATE_LIMIT_ENABLED`, `RL_*` | true | backend | Batas percobaan (jumlah, detik) per cakupan; lihat `core/config.py`. Format `RL_LOGIN_IP=[30,900]`. |
| `VERIFY_TOKEN_TTL_HOURS` / `RESET_TOKEN_TTL_MINUTES` | 48 / 30 | backend | Masa berlaku token email. |
| `SCAN_PROVIDER` | `disabled` | backend/worker | `clamav` = unggahan masuk karantina dan dipindai via clamd (`SCAN_HOST`/`SCAN_PORT`, default `clamav:3310`; jalankan `docker compose --profile scanner up -d clamav`). `disabled` = berkas `not_scanned` (internal saja, tidak pernah publik). **Wajib `clamav` di produksi.** |
| `MEDIA_DIR` / `MEDIA_MAX_VIDEO_MB` / `MEDIA_MAX_IMAGE_MB` / `PARTNER_DOC_MAX_MB` | `/data/media` / 100 / 10 / 10 | backend | Penyimpanan privat dan batas unggahan (ditegakkan saat streaming → 413). |
| `OUTBOX_BATCH_SIZE` / `OUTBOX_LEASE_SECONDS` / `OUTBOX_MAX_ATTEMPTS` | 20 / 120 / 6 | worker | Klaim per putaran, durasi lease (pemulihan crash), batas percobaan transient. |
| `OUTBOX_BACKOFF_BASE_S` / `OUTBOX_BACKOFF_CAP_S` | 30 / 3600 | worker | Exponential backoff (jitter 0,5–1,0). |
| `OUTBOX_UNDELIVERABLE_MAX_HOURS` | 72 | worker | Provider tak tersedia lebih lama dari ini → `dead`. |
| `OUTBOX_PURGE_SENT_DAYS` / `OUTBOX_PURGE_DEAD_DAYS` | 30 / 180 | CLI | Retensi baris outbox terkirim / dead-letter (pending/sending/undeliverable tak pernah dihapus). |
| `SMTP_TIMEOUT_S` | 15 | backend | Timeout koneksi SMTP. |
| `RETENTION_AUTO_ENABLED` / `RETENTION_INTERVAL_HOURS` | true / 24 | worker | Retensi terjadwal berkunci. |
| `MEDIA_PURGE_ENABLED` | true | worker | Purge media kedaluwarsa otomatis (hanya retensi habis). |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` / `DB_POOL_TIMEOUT_S` | 10 / 20 / 30 | backend | Pool koneksi per proses. |
| `DEBUG_QUERY_STATS` | false | backend | Header `X-DB-Queries` (hanya load test). |
| `LOG_LEVEL` | INFO | backend/worker | Log JSON terstruktur. |
| `BACKUP_ENCRYPTION_KEY_FILE` / `BACKUP_KEY_ID` / `BACKUP_DESTINATION` / `BACKUP_S3_ENDPOINT` | — | skrip backup | Berkas kunci (chmod 600, di luar repo); label kunci; tujuan off-site (belum diverifikasi). |
| `MAILPIT_HOST` | — | uji | Mengaktifkan `tests/test_smtp_mailpit.py`. |
| `PILOT_MIN_RESPONDENTS` | 5 | backend | Ambang k-anonimitas analytics pilot. |
| `PILOT_RETENTION_DAYS` | 365 | backend/worker | Hari setelah program selesai sebelum survei dianonimkan dan catatan/undangan dihapus. |
| `WORKER_INTERVAL_S` | 60 | worker | Jeda putaran worker (outbox, pemindaian, purge media, retensi). |
| `ALLOW_DEMO_CONTENT_SEED` | — | backend | Hanya staging: izinkan seed konten `[DEMO]` (tetap tanpa akun demo). |
| `ADMIN_PASSWORD` | — | CLI `create-admin` | Opsional (non-interaktif); bila tidak diset, CLI meminta kata sandi. Min. 12 karakter. |

Aturan: jangan commit `.env`, kunci, atau kredensial; jangan menampilkan secret di log/PR; secret produksi disimpan di secret manager, bukan di file repo.
