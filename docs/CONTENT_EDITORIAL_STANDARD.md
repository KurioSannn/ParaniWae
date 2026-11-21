# Standar Editorial Konten

Berlaku untuk semua konten publik SILATARA. Sumber kebenaran kebijakan: `CLAUDE.md` dan ADR-0008.

## 1. Tiga dasar konten

| `content_basis` | Contoh | Jalur terbit | Siapa yang dapat membaca |
|---|---|---|---|
| `source_backed` | Tradisi dalam berkas UNESCO, gerak dasar dari literatur kepelatihan, peta 38 provinsi | Validasi berkas (`make content-validate`) lalu tinjauan editorial sumber (`--publish --operator <redaksi>`) | Semua orang, tanpa login |
| `official_curriculum` | Kurikulum resmi sebuah perguruan | Instruktur menulis, kurator meninjau, mitra mengonfirmasi, admin menerbitkan | Publik bila mitra terverifikasi dan menyetujui listing |
| `partner_restricted` | Materi khusus anggota, media berlisensi terbatas, program pilot | Sesuai izin pemilik | Hanya pihak yang berhak |

Satu-satunya cara menulis klaim resmi atas nama sebuah perguruan adalah lewat `official_curriculum`.

## 2. Syarat pengetahuan berbasis sumber

- Setiap klaim memiliki `source_id` dan `locator` (halaman atau bagian). Uraian gerak hanya boleh bersandar pada sumber
  yang dibaca utuh; cuplikan hasil pencarian hanya untuk menandai keberadaan.
- Isi diparafrasa. Gambar, lambang, dan media sumber tidak diambil.
- Hal yang tidak ada di sumber tidak dikarang. Celah ditulis secara wajar ("Tidak dirinci dalam sumber; tanyakan kepada pelatih").
- Teknik yang menurut sumber atau guru tidak boleh didokumentasikan tidak diuraikan.
- Saran latihan dari redaksi (tempo, repetisi, ruang) diberi penanda ringan "Saran redaksi".

## 3. Gaya tulisan publik

- Ditujukan kepada pengunjung, bukan pengembang. Hindari: `[DEMO]`, "tahap pengembangan", "contoh teknis", "belum
  divalidasi", "menunggu validasi", "placeholder", nama status internal, dan istilah alur kerja.
- Halaman yang kosong disembunyikan atau diganti ajakan yang berguna, bukan "Belum ada …".
- Rujukan disajikan sebagai bagian "Rujukan" di akhir halaman.
- Catatan kerja internal pada data riset (`notes`) tidak dikirim ke publik. Yang tampil di publik adalah `public_note`,
  `public_localities`, dan `public_aliases`.

## 4. Integrasi ke halaman utama

| Konten | Halaman kanonik |
|---|---|
| Tradisi, sebutan lokal, aliran, persebaran 38 provinsi, nama jurus daerah | `/heritage`, `/heritage/<slug>` |
| Rujukan | `/heritage/referensi` |
| Gerakan dan animasi | `/library`, `/library/<slug>` |
| Kursus dan pelajaran | `/academy`, `/academy/courses/<slug>`, `/academy/courses/<slug>/lessons/<slug>` |
| Perguruan, padepokan, dan organisasi dalam catatan | `/community` (dipisah dari "Mitra SILATARA") |

Tidak boleh ada microsite paralel. URL lama `/riset/*` dialihkan dengan 308.

## 5. Pemeriksaan wajib sebelum rilis konten

`make content-validate` · `make animations-validate` · tes backend · `e2e-browser/scripts/link-check.mjs` (0 masalah,
tanpa teks terlarang) · pemeriksaan browser sebagai tamu dan sebagai pengguna login.
