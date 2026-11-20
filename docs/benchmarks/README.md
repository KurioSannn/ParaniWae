# Benchmark mesin landmark (main thread vs Web Worker)

Berkas hasil mentah di folder ini adalah **keluaran `make bench`** (reproduksi: `make bench`; opsi `BENCH_FRAMES`, `BENCH_REPEATS`). Setiap berkas memuat lingkungan, konfigurasi, seluruh run, dan ringkasan median.

**Aturan membaca:** sumber `synthetic=true` berarti kamera PALSU Chromium (pola uji, bukan manusia) → hanya memvalidasi jalur komputasi dan responsivitas. **Bukan** benchmark pose manusia, **bukan** ukuran akurasi, **bukan** FPS produk. Angka hanya berlaku untuk lingkungan yang tercatat. Benchmark pose manusia hanya dapat dibuat dengan webcam fisik + subjek nyata (lihat `../QA_MANUAL_CAMERA_CHECKLIST.md`, halaman `/app/practice/benchmark`).

| Berkas | Lingkungan | Sumber | Status |
|---|---|---|---|
| `2026-11-20-headless-synthetic.json` | Chromium 159 headless, container Linux (Docker Desktop), 8 thread, delegasi dilaporkan "GPU" (WebGL perangkat lunak) | SINTETIS (`fake_device_0`) | otomatis |
| *(isi oleh Anggota C)* `AAAA-MM-DD-<perangkat>-<browser>.json` | perangkat nyata | webcam fisik | **belum ada** |
