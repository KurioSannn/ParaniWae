# Struktur Kurikulum

Kurikulum dipisah **per tradisi atau kerangka sumber**. Validator menolak pelajaran yang memakai gerakan dari tradisi lain.

```
content/pencak-silat/
  curricula/<course>.json   kursus + modul   (schema silatara.curriculum/v1)
  lessons/<course>.json     pelajaran        (schema silatara.lessons/v1)
  movements/*.json          dokumen gerakan  (dirujuk pelajaran lewat movement_ids)
```

Folder `modules/` yang diusulkan brief tidak dibuat terpisah. Modul disimpan di dalam berkas kursus agar urutan dan ID
tetap konsisten (`crs.x.m01`…).

## Kursus yang tersedia (draf)

### `crs.psdp-dasar`: Sikap & Gerak Dasar Pencak Silat (kerangka pendidikan jasmani)

| Modul | Pelajaran | Gerakan (status animasi) |
|---|---|---|
| m01 Pengenalan & keselamatan | l01 Warisan budaya, banyak tradisi · l02 Etika & keselamatan | pemusatan diri (✔) |
| m02 Sikap dasar berdiri | l03 Sikap tegak 1–4 · l04 Sikap istirahat | sikap tegak (✔), istirahat (✔) |
| m03 Kuda-kuda | l05 Depan & belakang · l06 Tengah & samping · l07 Menyamping & silang | 7 kuda-kuda (✔ semua) |
| m04 Sikap duduk | l08 Lima sikap duduk | 5 (needs_reference) |
| m05 Sikap pasang | l09 Pasang 1–4 · l10 Pasang 5–8 | pasang 1, 4, 6, 8 (✔); 2, 3, 5, 7 (needs_reference) |
| m06 Arah & cara melangkah | l11 Arah 8 penjuru · l12 Lima cara melangkah | arah 8 (✔), angkatan (✔), geseran (✔); putaran, lompatan, ingsutan (needs_reference) |
| m07 Pola langkah | l13 Pola langkah | lurus (✔), zig-zag (✔); ladam, segitiga, segiempat, huruf S (needs_reference) |
| m08 Pembelaan tanpa kontak (pengawasan) | l14 Hindaran & elakan | hindaran hadap, elak bawah/samping/belakang (✔, supervised_only); 4 lainnya needs_reference |

### `crs.silek-pengenalan`: Pengenalan Silek Minangkabau (teori)

| Modul | Pelajaran |
|---|---|
| m01 Silek sebagai pengetahuan | l01 Silek, sasaran, dan pewarisnya · l02 Baraja malangkah |

Kursus ini sengaja **tanpa latihan gerak**. Sumber terbuka hanya menjelaskan konsep langkah tigo, ampek, dan sambilan,
tidak menguraikan pelaksanaannya.

## Isi setiap pelajaran (21 butir brief)

Judul, deskripsi, tradisi/sumber, tujuan, kompetensi awal, durasi, peralatan, ruang, briefing keselamatan, teori,
penjelasan budaya, daftar gerakan, instruksi per fase*, animasi*, panduan latihan bertahap, kesalahan umum*, rangkuman,
refleksi, kuis teori (dengan `source_id` per soal), rujukan, dan status validasi instruktur.

\* Diambil importer dari dokumen gerakan, sehingga teks fase hanya ada di satu tempat.

## Pemetaan ke database

| Konten | Tabel | Catatan |
|---|---|---|
| kursus | `courses` | `status=draft`, mitra = Tim Editorial internal (ADR-0006) |
| modul | `course_modules` | berdasarkan `order_index` |
| pelajaran | `lessons` | `body` = markdown gabungan; `movement_id` = `primary_movement_id` |
| teori, budaya, kuis, rujukan | `lesson_materials` (`kind=text`) | `attribution_text` = daftar sumber |
| gerakan | `movements` + `movement_documents` (v1 draf) + `movement_phases` | lihat MOVEMENT_CONTENT_STANDARD |

## Tingkatan

Brief meminta tingkat pengenalan, beginner, fundamental, intermediate, dan advanced. Sumber yang terbaca hanya mendukung
**pengenalan + beginner** (dan sebagian intermediate, misalnya sikap pasang 8 dan lompatan, yang tidak dibuka untuk latihan
mandiri). Tingkat lanjut sengaja **tidak** disusun sampai ada mitra dan sumber yang memadai.
