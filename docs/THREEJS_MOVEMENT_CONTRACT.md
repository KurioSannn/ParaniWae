# Kontrak Peraga 3D (Three.js)

**Karakter:** model dasar Quaternius "Universal Base Characters" (CC0 1.0), rig UE 65 sendi (tiap jari 3 ruas = 30 tulang jari), rambut statis dipasang ke tulang `Head`. Baju, celana, sabuk dibuat SILATARA dari permukaan tubuh yang sama (bobot skin disalin). Satu berkas: `content/pencak-silat/character/silatara-instructor.glb` (±3 MB, tekstur JPEG). Lisensi: `THIRD_PARTY_ASSETS.md`. Karakter ini bukan maskot dan tidak mewakili perguruan mana pun.

**Klip:** 21 (idle + 20 gerakan) dari `content/pencak-silat/animations/*/keyframes.json` yang sama dengan animasi 2D, sehingga fase & waktu identik. Pipeline: `tools/character/animate.py` (sumber) -> `build_quaternius.py` (retarget rotasi delta dunia; lengan/tangan/jari dikoreksi A->T-pose; tungkai IK dua ruas ke pergelangan sumber).
Validasi otomatis per klip (`validation.json`): galat pergelangan <10 mm, kaki tumpu tidak meluncur <4 mm, tidak menembus lantai, jarak tangan-badan >4 mm, loop tertutup.

**API:** `GET /api/v1/research/character` (manifest + klip + penanda fase), `/character/model.glb` (ETag), `/character/reference/{movement_id}` (urutan titik tubuh referensi berindeks MediaPipe, untuk penilaian).

**Pemutar** (`Movement3DPlayer`): jeda/putar/ulang, kecepatan 0,25–1,5×, fase sebelumnya/berikutnya, linimasa dengan penanda fase, tampak depan/samping/¾/orbit 360°, reset kamera; memuat saat terlihat; `prefers-reduced-motion` mulai dalam keadaan jeda; jatuh ke ilustrasi 2D bila WebGL tidak ada. Klip yang gagal validasi tidak ditawarkan.

**Belum:** `.blend` sumber tidak ada (Blender tidak tersedia; sumber yang dapat diperbaiki = skrip Python). Gerak adalah tafsir editorial atas uraian sumber, bukan rekaman instruktur. 20 gerakan lain masih tanpa peraga.
