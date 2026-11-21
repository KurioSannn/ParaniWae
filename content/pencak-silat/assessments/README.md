# Protokol penilaian gerak

Sprint 10 (arahan pemilik produk 2026-11-21) meminta penilaian gerak 0–100 dengan kamera. Berkas `*.protocol.json`
di sini adalah DATA yang dibaca mesin penilaian (`frontend/src/features/assessment/engine.ts`). Mesin tidak
menyimpan angka target apa pun; menambah gerakan berarti menulis protokol baru (lihat
`docs/MOVEMENT_ASSESSMENT_CONTRACT.md`).

Aturan protokol:

- Target berasal dari uraian sumber (`basis: source`), tafsir uraian sumber yang dicatat (`source_interpreted`),
  ilustrasi sumber/klip referensi (`reference_illustration`), atau kriteria teknis pengukuran (`technical`).
  Tidak ada target yang dikarang untuk sekadar menghasilkan skor.
- Toleransi dan `falloff` adalah parameter editorial versi 1, **belum dikalibrasi instruktur** (`calibration`).
  Setiap perubahan menaikkan `protocol_version`.
- Hanya gerak solo tingkat pemula (aturan CLAUDE.md 16). Skor = kesesuaian dengan panduan gerak SILATARA,
  bukan sertifikasi atau penilaian resmi perguruan mana pun.
- `readiness.json` mencatat untuk setiap gerakan apakah protokol tersedia dan, bila tidak, alasannya.

Kuis pemahaman teori tetap berada di `lessons/*.json`.
