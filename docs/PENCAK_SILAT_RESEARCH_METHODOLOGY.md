# Metodologi Riset Pencak Silat (Sprint 9)

## 1. Pertanyaan riset

1. Tradisi, aliran, perguruan, tempat latihan, dan organisasi apa saja yang **dapat dibuktikan** dari sumber yang dapat
   dibuka, dan di provinsi mana?
2. Gerak solo apa yang terdokumentasi cukup rinci untuk diajarkan dan dianimasikan tanpa mengarang?
3. Apa yang belum diketahui (gap), dan siapa yang perlu ditanya?

## 2. Hierarki sumber

Mengikuti CLAUDE.md dan brief sprint:

1. UNESCO ICH, yaitu halaman elemen 01391, keputusan 14.COM 10.B.15, berkas nominasi, dan ekstrak inventaris.
2. Inventaris WBTb nasional. Portal tidak dapat diakses, jadi kode pencatatan diambil dari ekstrak inventaris dalam berkas UNESCO.
3. Publikasi akademik dengan teks utuh (jurnal UNY, Unimed, prosiding UGM Digital Press).
4. Buku yang identitas penerbitnya jelas (Herdiana 2008, ISBN; hak cipta dilindungi, jadi hanya parafrasa fakta).
5. Sumber tersier (Wikipedia) **hanya** untuk nama, dengan label tersier.
6. Cuplikan hasil pencarian **hanya** untuk menandai keberadaan entitas di suatu provinsi (`needs_verification`). Cuplikan
   **tidak pernah** dipakai untuk uraian gerak; importer menolak gerakan yang bersandar pada sumber `search_snippet`.

## 3. Prosedur

1. **Penemuan:** pencarian web sistematis per kelompok wilayah, dalam bahasa Indonesia dan Inggris, memakai nama lokal dari
   berkas UNESCO (silek, kuntau, langga, amanca, pakuttau, mencak, dan lainnya).
2. **Pembacaan utuh:** PDF/DOC diunduh ke folder sementara, lalu teksnya diekstrak di kontainer sekali pakai (pypdf) atau
   dengan `textutil` (macOS). Salinan berkas **tidak** disimpan di repo. Data kontak pribadi dalam berkas UNESCO tidak disalin.
3. **Ekstraksi:** setiap klaim dicatat beserta `source_id` dan `locator` (halaman atau bagian). Parafrasa dibuat singkat,
   tanpa menyalin paragraf.
4. **Klasifikasi:** setiap entitas diberi kategori: tradisi, aliran, perguruan, tempat latihan, organisasi, komunitas,
   atau sebutan lokal. Perguruan tidak otomatis dianggap aliran. Alias dan cabang digabung dalam satu entitas; misalnya
   dua alamat Tapak Suci adalah satu perguruan dengan dua lokasi.
5. **Konflik antarsumber** dicatat dan **tidak** direkonsiliasi diam-diam. Contoh: uraian kuda-kuda tengah versi Nugroho
   berbeda dari Herdiana, dan keduanya disimpan sebagai varian.
6. **Penilaian kelayakan animasi:** gerak dianimasikan hanya bila posisi tubuh di setiap fase terbaca dari teks. Bila tidak,
   status animasinya `needs_reference` dan kebutuhannya ditulis.

## 4. Batasan yang diketahui

- Portal WBTb dan buku PJOK Kemendikbud tidak dapat diakses (DNS gagal pada 2026-11-20). Akibatnya, penetapan WBTb setelah
  2018 per provinsi belum ditelusuri.
- Sejumlah jurnal mengembalikan HTTP 403 atau tidak dapat diunduh (UPI, Untirta, core.ac.uk).
- Diagram dalam PDF berupa gambar, sehingga pola langkah selain lurus dan zig-zag tidak dapat dibaca andal dari teks.
- Penelusuran dilakukan oleh satu agen dalam satu sesi. Ini **bukan** survei lapangan dan bukan sensus perguruan.
  IPSI melaporkan ratusan perguruan, sedangkan katalog ini hanya memuat yang muncul di sumber yang dibaca.
- Penomoran sikap pasang dan arah 8 penjuru berasal dari Januarno (1989), buku terbitan Yayasan Setia Hati Terate yang
  dikutip Nugroho. Ini bukan bukti kurikulum PSHT saat ini.

## 5. Etika

- Tidak ada nama orang, kontak, atau foto dari berkas sumber yang dipublikasikan ulang.
- Teknik yang menurut sumber **tidak boleh didokumentasikan** (Kumango: kuncian kaki, tusukan, patukan) dicatat sebagai
  `restricted` tanpa uraian.
- Tidak ada konten yang diklaim divalidasi instruktur. Semua berstatus `draft`/`needs_reference` dan
  `instructor_validation: not_validated`.
