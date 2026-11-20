# Kesiapan reverse proxy & rate limit (status: BELUM SIAP produksi)

Dokumen ini mencatat apa yang **terbukti** dan apa yang **belum** — tidak ada konfigurasi produksi yang dikarang.

## Terbukti
- Rate limit disimpan di PostgreSQL, konsisten lintas worker/instance.
- IP klien: `X-Forwarded-For` hanya dipercaya bila peer langsung ada di `TRUSTED_PROXY_CIDRS`; IP = entri ke-`TRUSTED_PROXY_HOPS` dari **kanan**. Default **kosong** (aman). Diuji unit (`tests/test_security.py`) dan pada rantai proxy nyata di stack E2E terisolasi.
- **Proxy rewrite Next.js TIDAK menimpa XFF secara tepercaya** (terbukti): konfigurasi awal yang mempercayai CIDR privat membuat XFF palsu klien menghasilkan kunci rate-limit sendiri. Sudah diperbaiki (default kosong) + regresi di `backend/tests/e2e_flow.py`.
- Probe black-box `backend/tests/probe_forwarded_headers.py` pada stack E2E terisolasi: dengan XFF acak, 429 tetap muncul (request ke-456 pada batas 500 bersama) → **lulus** untuk topologi "Next → backend, tanpa proxy tepercaya".

## Rate limit di development bersifat GLOBAL, bukan per-klien
Karena tidak ada proxy tepercaya, kunci per-IP = IP container frontend untuk **semua** klien. Aman (tidak dapat dipalsukan) tetapi satu klien yang agresif dapat menghabiskan batas untuk semua orang (DoS terhadap login di dev). Itu perilaku dev yang disengaja, bukan fitur produksi.

## Belum terbukti / belum ada (jangan diklaim siap)
- Topologi produksi nyata (LB/CDN/reverse proxy) **belum diuji**. Tidak ada konfigurasi Nginx/Caddy/LB di repo karena belum ada keputusan hosting.
- Syarat yang harus dipenuhi dan **diuji ulang** pada topologi nyata:
  1. Proxy terdepan **menimpa** (bukan menambah) `X-Forwarded-For` dengan IP socket klien, dan menghapus nilai kiriman klien.
  2. Backend **tidak** terbuka langsung ke internet (hanya proxy yang dapat menjangkaunya); bila terbuka, `TRUSTED_PROXY_CIDRS` harus kosong.
  3. `TRUSTED_PROXY_CIDRS` = CIDR proxy sebenarnya; `TRUSTED_PROXY_HOPS` = jumlah proxy yang menambah XFF di depan backend.
  4. HTTPS wajib (cookie `Secure`), `/` dan `/api` satu domain.
  5. Jalankan `python backend/tests/probe_forwarded_headers.py https://<staging> <N di atas batas>` terhadap **staging** (bukan DB dev bersama; probe menghabiskan batas login) → harus **LULUS**; tinjau juga bahwa XFF akhir yang dilihat backend adalah IP klien nyata.
- Tugas: B2 di [TEAM_ISSUES](TEAM_ISSUES.md).
