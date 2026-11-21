# Laporan load test backend (terukur, bukan target)

Alat: `make loadtest` (`backend/loadtest/`). DB scratch `silatara_load` (dibuat & dibuang otomatis; **tidak menyentuh DB dev**), data **sintetis**: 300 peserta, 3 cohort, kursus privat 12 pelajaran, ±1.800 progres, ±750 sesi latihan, 240 jawaban survei, 150 undangan. Server uvicorn kedua di container backend (`DEBUG_QUERY_STATS=true`, rate limit off). **Pembangkit beban berjalan di container yang sama** (8 vCPU Docker Desktop, macOS) ⇒ angka konservatif/tidak terisolasi; **satu kali run per konfigurasi** (varians tidak diukur). Bukan uji kapasitas produksi.

## Query per request (tidak tumbuh dengan jumlah peserta; tumbuh dengan jumlah cohort/pelajaran)
| Skenario | Query | Latensi 1 klien (p50 / p95) |
|---|---|---|
| validasi sesi (`/auth/me`) | 2 | 3,4 / 5,9 ms |
| kursus privat | 11 | 15,3 / 23,4 ms |
| pelajaran | 11 | 13,3 / 25,2 ms |
| progres (PUT) | ±10 | 11,4 / 19,4 ms |
| riwayat latihan | 5 | 5,8 / 12,4 ms |
| portal peserta | 10 | 11,8 / 21,4 ms |
| detail program | 19 (N+1 ringan per cohort) | 12,3 / 20,8 ms |
| daftar/detail cohort | 14 | 15,7 / 27,1 ms |
| dashboard cohort | 16–17 | 25,7 / 41,5 ms |
| analytics program (3 cohort) | 46 → 40 setelah optimasi | 72,8 / 113,7 ms |
| terima undangan | ±13 (maks 22) | 10,0 / 20,2 ms |
| login (Argon2) | 3 | 102 / 176 ms (≈ biaya hash, disengaja) |

## Beban 20 klien paralel, 1 worker uvicorn (12 dtk per skenario)
| Skenario | rps | p50 | p95 | p99 | error |
|---|---|---|---|---|---|
| validasi sesi | 193 | 80 ms | 252 ms | 437 ms | 0 |
| kursus privat | 33 | 328 ms | 2,2 s | 3,1 s | 0 |
| pelajaran | 44 | 365 ms | 976 ms | 1,1 s | 0 |
| portal | 49 | 344 ms | 759 ms | 905 ms | 0 |
| detail program | 52 | 317 ms | 685 ms | 1,3 s | 0 |
| dashboard cohort | 36 → 40,5 (setelah optimasi) | 536 → 478 ms | 767 → 655 ms | 895 → 783 ms | 0 |
| analytics | 12,5 → **17,5** | 1515 → **1078 ms** | 1964 → 1451 ms | 2046 → 1578 ms | 0 |

Dengan 4 worker (C=20): portal 224 rps (p50 53 ms), detail program 134 rps, sesi 375 rps; **tetapi ekor analytics/kursus memburuk (p95 4,5 s / 0,56 s)** — pembangkit beban dan 4 proses berebut CPU yang sama; tidak dapat disimpulkan skala linear.

## Koneksi DB
Maks 40–43 koneksi aktif pada C=20 (pool default 10 + overflow 20 per proses; diset lewat `DB_POOL_SIZE/DB_MAX_OVERFLOW`). Tidak ada `QueuePool timeout`/error selama run.

## Temuan & optimasi (berbasis hasil)
1. **CPU Python per-permintaan** (≈1 ms/query + overhead ORM) adalah batas utama; bukan lock DB. Latensi di bawah beban = antrean pada satu proses. → jalankan **≥2–4 worker** di produksi (`uvicorn --workers N`) dan ukur ulang pada host terisolasi.
2. **Analytics memuat semua baris aktivitas ke Python** (per peserta). **Diperbaiki:** agregasi `UNION ALL … GROUP BY` di database (aktivitas, pekan retensi, dashboard) → throughput +40 %, p50 −29 %, 46→40 query. Tes ekuivalensi angka (`test_pilot_analytics.py`) tetap lulus.
3. `program_detail` N+1 ringan per cohort (≈4 query/cohort): aman untuk puluhan cohort; refactor bila >50.
4. `analytics` tumbuh ≈15 query/cohort: untuk banyak cohort pakai filter `cohort_id` atau cache hasil (belum dibuat).
5. Indeks: query terukur memakai indeks FK/status yang ada; **tidak ditemukan indeks hilang** pada skenario ini (tidak ada `EXPLAIN` skala besar; data 300 peserta kecil bagi planner — evaluasi ulang pada data nyata).
6. `invitation_accept`: 51 dari 150 diterima; sisanya `409 CAPACITY_FULL` (kapasitas program seed 350) — perilaku benar, bukan galat.

## Belum diukur
Login serentak berat, unggahan media besar paralel, ClamAV di bawah beban, replikasi/failover DB, jaringan nyata/TLS/proxy, uji soak berjam-jam. Laporan JSON mentah: `artifacts/loadtest-*.json`.
