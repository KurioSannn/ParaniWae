# Kontrak Penilaian Gerak

Mesin murni di `frontend/src/features/assessment/` (tanpa React). Protokol adalah **data** (`content/pencak-silat/assessments/*.protocol.json`); menambah gerakan = menulis protokol, bukan mengubah mesin.

**Protokol memuat:** movement_id, reference_id, tampak kamera wajib, landmark wajib & ambang visibilitas, fase (keyframe referensi), kriteria (fitur, sisi, target/rentang, toleransi, falloff, bobot, kepercayaan minimum, alasan, basis, sumber, umpan balik), persyaratan kepercayaan, rumus.

**Skor:** `total = round((Σ skor_kriteria×bobot + skor_fase×bobot_fase) / (Σ bobot kriteria terukur + bobot_fase))`; skor kriteria 100 di dalam toleransi lalu turun linier ke 0 pada toleransi+falloff. Kriteria yang tidak terukur dikeluarkan; bila >40% bobot tak terukur -> `not_assessable`.

**Alur:** kualitas input (rasio frame layak × visibilitas) -> cek tampak kamera -> penyelarasan subsequence-DTW terhadap urutan referensi 3D -> deteksi fase -> nilai tiap kriteria pada jendela fasenya -> saran = kehilangan poin berbobot terbesar (maks 3). Skor tidak pernah dihitung bila kualitas input kurang (`TOO_FEW_FRAMES`, `LOW_INPUT_QUALITY`, `KEY_LANDMARKS_MISSING`, `WRONG_CAMERA_VIEW`, `MOVEMENT_NOT_FOUND`, `TOO_MANY_UNMEASURED`).

**Protokol aktif (3):** `langkah-angkatan` (samping), `kuda-kuda-tengah` (depan), `kuda-kuda-depan` (samping). `readiness.json` memuat status untuk semua 43 gerakan beserta alasan (mis. bukan gerak solo pemula, pola langkah diukur di lantai, belum ada peraga). Target berasal dari uraian sumber, tafsir yang dicatat, atau rentang dari klip referensi; toleransi/falloff adalah parameter editorial v1 yang **belum dikalibrasi instruktur**.

**Privasi:** landmark hanya di memori perangkat dan dibuang setelah skor dihitung. `POST /api/v1/assessments` (login+CSRF) hanya menerima ringkasan; `extra=forbid` menolak landmark/video/frame; rincian kriteria hanya dengan persetujuan; versi protokol & referensi dicek (409 bila berubah). Riwayat milik sendiri: `GET /assessments`, `DELETE /assessments/{id}`.

**Pengujian:** 14 tes sintetis (matematika, DTW, ketergantungan metrik, determinisme, kualitas rendah, tampak salah, fase terlewat) + referensi 3D nyata (diri sendiri ≥90). **Tes sintetis bukan bukti akurasi pada manusia; belum ada uji webcam nyata dan tidak ada klaim akurasi.**
