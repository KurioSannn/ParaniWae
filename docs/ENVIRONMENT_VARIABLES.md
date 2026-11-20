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
| `MAIL_PROVIDER` | `dev_sink` | backend | `dev_sink` (hanya development; email disimpan di DB, **tidak dikirim**) \| `smtp` \| `none`. Produksi wajib `smtp`. |
| `MAIL_FROM` `SMTP_HOST` `SMTP_PORT` `SMTP_USER` `SMTP_PASSWORD` `SMTP_STARTTLS` | — / 587 / true | backend | Konfigurasi SMTP. Tanpa ini fitur email → `503`. |
| `PUBLIC_BASE_URL` | `http://localhost:${FRONTEND_PORT}` | backend | Origin frontend untuk tautan di email. |
| `TRUSTED_PROXY_CIDRS` / `TRUSTED_PROXY_HOPS` | *(kosong)* / 1 | backend | Proxy yang boleh menyuplai `X-Forwarded-For`; IP klien = entri ke-N dari kanan. **Produksi: isi sesuai topologi nyata** ([SECURITY_HYGIENE](SECURITY_HYGIENE.md) §4). Default kode: kosong (tidak ada proxy tepercaya). |
| `RATE_LIMIT_ENABLED`, `RL_*` | true | backend | Batas percobaan (jumlah, detik) per cakupan; lihat `core/config.py`. Format `RL_LOGIN_IP=[30,900]`. |
| `VERIFY_TOKEN_TTL_HOURS` / `RESET_TOKEN_TTL_MINUTES` | 48 / 30 | backend | Masa berlaku token email. |
| `ALLOW_DEMO_CONTENT_SEED` | — | backend | Hanya staging: izinkan seed konten `[DEMO]` (tetap tanpa akun demo). |
| `ADMIN_PASSWORD` | — | CLI `create-admin` | Opsional (non-interaktif); bila tidak diset, CLI meminta kata sandi. Min. 12 karakter. |

Aturan: jangan commit `.env`, kunci, atau kredensial; jangan menampilkan secret di log/PR; secret produksi disimpan di secret manager, bukan di file repo.
