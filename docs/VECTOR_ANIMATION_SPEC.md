# Spesifikasi Animasi Vektor

## Ringkas

- **Output utama:** `animation.svg`, yaitu SVG animasi SMIL (`<animateTransform>`/`<animate>`) yang berulang tanpa henti,
  tanpa JavaScript, tanpa font atau URL eksternal, dan dapat diputar di `<img>` maupun dibuka langsung.
- **Sumber yang diedit:** `keyframes.json` per gerakan. Generator (`tools/animation/silat_anim.py`, Python stdlib) membangun
  ulang semua berkas turunan.
- **Lokasi:** `content/pencak-silat/animations/<movement_id>/`, berisi `animation.svg`, `keyframes.json`, `rig.json`
  (salinan rig yang dipakai), `thumbnail.svg` (pose awal statis), `animation-manifest.json`, dan `ANIMATION_NOTES.md`.
- **Pratinjau** (alat pengembangan, bukan frontend): `content/pencak-silat/animations/index.html`.

## Rig (`tools/animation/rig.json`)

Karakter instruksional generik terpisah dari maskot. Pakaiannya gelap polos dengan sabuk polos, tanpa emblem atau warna tingkatan perguruan.
Wajahnya tidak realistis, dan warnanya diambil dari token DESIGN.md.

```
root(pelvis, translate) ─┬─ paha.L ─ tulang kering.L ─ telapak.L       (pivot: pinggul, lutut, pergelangan)
                         ├─ paha.R ─ tulang kering.R ─ telapak.R
                         └─ torso(rotate) ─┬─ leher/kepala(rotate)
                                           ├─ lengan atas.L ─ lengan bawah.L ─ tangan.L (kepal/terbuka)
                                           └─ lengan atas.R ─ lengan bawah.R ─ tangan.R
```

Ukuran segmen (px viewBox): torso 106, paha 84, tulang kering 82, lengan atas 56, lengan bawah 50, dan kepala r=21.
Kanvasnya 360×440 dengan garis lantai di y=404.

**IK kaki:** pose menentukan posisi pergelangan kaki (x, tinggi angkat). Generator lalu menyelesaikan sudut pinggul dan
lutut per frame dengan IK dua-ruas, sehingga telapak benar-benar menapak dan tidak melayang atau tergelincir. Pose yang
tak terjangkau (galat > 0,75 px) **ditolak**.

**Tampilan:**

- `side`: karakter menghadap kanan, sisi kiri karakter di depan (near). Dipakai untuk gerak maju-mundur.
- `front`: karakter menghadap penonton, jadi sisi kanan karakter tampak di **kiri** layar. Dipakai untuk kangkang dan menyamping.
- `top`: diagram langkah tampak atas untuk arah dan pola langkah.

## keyframes.json

```json
{
  "animation_id": "anim.psdp.kuda-kuda-depan.v1",
  "movement_id": "mv.psdp.kuda-kuda-depan",
  "animation_status": "generated",
  "view": "side",
  "keyframes": [
    {"id": "kf-1", "phase_id": "mv.psdp.kuda-kuda-depan#p1", "label": "Sikap tegak 2", "caption": "...",
     "pose": {"pelvis": [172, 0], "feet": {"L": [176, 0], "R": [168, 0]},
              "arms": {"L": [-28, 95], "R": [-24, 92]}, "hands": {"L": "fist", "R": "fist"}}}
  ],
  "sequence": [{"pose": "kf-1", "hold_ms": 1000}, {"pose": "kf-2", "move_ms": 1000, "hold_ms": 2000}],
  "return_ms": 1000
}
```

Konvensi parameter pose ada di `rig.json → conventions`. Timeline diinterpolasi dengan smoothstep, disampel 20 fps, dan
dikembalikan ke pose awal lewat `return_ms` agar loop tidak melompat. Keterangan fase tampil sesuai jendela waktu setiap
keyframe, dan pemetaan keyframe ke fase dicatat di `animation-manifest.json → phase_map`.

**Kecepatan:** `playback_rates` di manifest bersifat metadata. Pemutar dapat memakai `pauseAnimations()` atau
`setCurrentTime()`, atau membangun ulang dengan durasi lain.

## Validasi otomatis (`make animations-validate`, `make animations-test`)

- XML valid; root `<svg>` dengan `viewBox="0 0 360 440"`, `id` = animation_id, `data-movement-id` cocok, serta `<title>`/`<desc>`.
- Tidak ada `<script>`, `href`, `url()`, `<image>`, `<foreignObject>`, atau URL selain namespace SVG.
- Ada elemen animasi; semua `repeatCount="indefinite"`, `dur` sama di seluruh elemen, `keyTimes` monoton 0..1, dan jumlah nilai cocok.
- Loop: nilai pertama sama dengan nilai terakhir pada setiap animasi linear.
- Keyframe lengkap, ID unik, `phase_id` milik gerakan yang sama dan ada di dokumen gerakan, serta semua keyframe terpakai.
- Durasi 1,5–30 detik; ukuran ≤ 250 KB; hash keyframes dan SVG cocok dengan manifest.
- Tidak ada bagian tubuh keluar area aman kanvas. Untuk tampak atas, penanda dan teks diperiksa terhadap tepi kanvas.
- `needs_reference` wajib berisi `needs` dan tidak boleh memiliki SVG.

**Bukti di browser** (`make animations-browser-check`): Chromium dari image Playwright E2E membuka pratinjau, memastikan
semua `<img>` termuat tanpa error konsol, lalu mengukur bahwa transformasi berubah setelah 1,6 detik.

## Status kebenaran

Animasi adalah **interpretasi visual editorial** atas teks sumber. Sumber tidak menyebut panjang langkah, sudut lutut,
atau tinggi angkatan, sehingga nilai-nilai itu dicatat sebagai tafsir di `ANIMATION_NOTES.md`. Tidak ada animasi yang
boleh disebut demonstrasi resmi perguruan sebelum instruktur mitra menyetujuinya.
