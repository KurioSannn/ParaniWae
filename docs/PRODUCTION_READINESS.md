# Kesiapan produksi/pilot — audit & daftar periksa

Status: **siap untuk pilot terbatas SETELAH** blocker di bawah dikonfigurasi/diputuskan. Tidak ada deployment dilakukan. Verifikasi dengan `make doctor T=production` (harus 0 BLOCKER).

## Sudah teruji di repo
Akses privat terpusat (10 tes matriks) · outbox berlease + concurrency 2 koneksi nyata + SMTP nyata ke Mailpit · anonimisasi CLI aman + scheduler berkunci · backup terenkripsi + restore terverifikasi (sha256/HMAC/dekripsi/media) · karantina + ClamAV nyata (EICAR) + fail-closed · log JSON tanpa rahasia/query-string · health bertingkat + doctor · load test baseline.

## Daftar periksa deployment (pemilik: infra/DevOps; belum dilakukan)
| Area | Persyaratan | Status |
|---|---|---|
| Reverse proxy & XFF | proxy yang **menimpa** `X-Forwarded-For`; isi `TRUSTED_PROXY_CIDRS` + `TRUSTED_PROXY_HOPS`; verifikasi probe XFF palsu (`tests/e2e_flow.py`) | belum (topologi belum ada) |
| HTTPS & cookie | TLS di proxy; `COOKIE_SECURE=true`; `PUBLIC_BASE_URL=https://…`; HSTS di proxy | belum |
| Batas body proxy | `proxy_client_max_body_size ≥ 110 MB` pada reverse proxy (selain Next `proxyClientMaxBodySize`) | belum diuji pada topologi produksi |
| SMTP | server nyata + SPF/DKIM/DMARC domain pengirim; `MAIL_PROVIDER=smtp`; uji kirim ke kotak nyata | belum (pengiriman nyata hanya ke Mailpit) |
| ClamAV | `SCAN_PROVIDER=clamav`; ≥1 GB RAM (+ signature DB persisten `clamav_db`); pantau `doctor` | siap (compose profile `scanner`) |
| PostgreSQL | sandi kuat (≥16), jaringan privat, backup terenkripsi terjadwal (cron memanggil `make backup-all`), uji restore berkala | skrip siap; penjadwalan & off-site belum |
| Media | volume `media_data` izin tulis user app, bukan `o+w`, ruang cukup; backup bersama DB | siap |
| Worker | ≥1 instans `worker`; healthcheck; log retensi | siap |
| Secret | di secret manager/env, bukan repo/`.env.example`; kunci backup terpisah dari cadangan | belum |
| Rate limit | `RATE_LIMIT_ENABLED=true` (default) + XFF benar | siap bersyarat proxy |
| Log & monitoring | kumpulkan stdout JSON (retensi sesuai kebijakan; tanpa PII); alarm: 5xx, `doctor`, outbox dead/backlog, worker heartbeat | log siap; pengumpul/alarm belum |
| Akun & peran | tanpa akun demo (`doctor` BLOCKER bila ada); provisioning admin via `create-admin` | siap |
| Skala | ≥2–4 worker uvicorn; ukur ulang pada host terisolasi | belum (baseline 1 mesin: LOAD_TEST_REPORT) |

## Risiko tersisa / butuh keputusan pemilik
1. Mitra/peserta/persetujuan nyata + validasi survei (S-11, S-12). 2. Keputusan data usage per-akun setelah retensi (ADR-0005). 3. Penyedia SMTP & domain. 4. Lokasi off-site backup & pengelola kunci. 5. Kebijakan hukum insiden/UU PDP. 6. PDF laporan (S-16). 7. Admin/kurator dapat membuka semua kursus privat untuk review — konfirmasi kebijakan.
