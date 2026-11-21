# Provenance Konten

## Tiga tingkat informasi

| Tingkat | Arti | Di mana tercatat |
|---|---|---|
| `research_supported` | Didukung sumber resmi atau akademik yang **dibaca utuh** | `evidence_tier`; `basis: source` + `source_ids` + `locator` |
| `instructor_confirmed` | Dikonfirmasi instruktur atau pengelola perguruan yang berwenang | **belum ada** satu pun |
| `editorially_prepared` | Disusun tim SILATARA tetapi belum disetujui instruktur | kursus & pelajaran; `basis: editorial` / `editorial_unvalidated` |

## Yang disimpan untuk setiap klaim

- `source_id` → `research/pencak-silat/sources/sources.json`: judul, penulis/penerbit, tahun, URL/DOI/ISBN,
  tanggal akses (2026-11-20), `read_status`, dan lisensi.
- `locator`: halaman atau bagian.
- `supports`: fakta yang didukung sumber itu.
- `gaps`: informasi yang tidak ada di sumber.
- `permission_status`: semua materi berupa **parafrasa sumber terbit** tanpa media, dan belum ada izin pemilik kurikulum.
- Tingkat keyakinan diwakili oleh `read_status` sumber dan `basis`. Tidak ada skor numerik yang dikarang.

## Di database

- `source_citation` dan `source_url` pada tradisi, gerakan, dokumen, kursus, dan pelajaran.
- `movement_documents.usage_scope`: pernyataan draf riset internal.
- `license_type = NULL`. Belum ada lisensi, jadi tidak boleh diisi `instructor_owned`/`partner_permission`.
- `review_note`: tag "Impor konten riset SILATARA" beserta status konten.
- `audit_logs.action = content.import`: hitungan setiap eksekusi importer.

## Hak cipta

| Sumber | Lisensi | Perlakuan |
|---|---|---|
| Ediwar dkk. 2023 | CC BY 4.0 | parafrasa + atribusi |
| Wikipedia "Cingkrik" | CC BY-SA 4.0 | nama saja, berlabel tersier |
| Herdiana 2008 | hak cipta dilindungi | hanya fakta teknik diparafrasa singkat dengan halaman; ilustrasi **tidak** dipakai |
| Nugroho 2005, Siswantoyo 2005, Putri & Nusri 2022 | jurnal tanpa pernyataan lisensi terbuka | parafrasa; gambar/lambang **tidak** direproduksi |
| Berkas UNESCO | dokumen publik | parafrasa; data kontak pribadi **tidak** disalin |

## Animasi

Animasi dibuat dari nol oleh generator dengan rig generik. Tidak ada video, foto, atau ilustrasi sumber yang dipakai.
Setiap folder memuat `ANIMATION_NOTES.md` yang memisahkan apa yang dari sumber dan apa yang tafsir editorial.

## Dasar konten & jalur publikasi (ADR-0008, 2026-11-21)

- Konten riset bertanda `content_basis=source_backed`. Konten ini terbit lewat **tinjauan editorial sumber**: peninjau
  bukan akun demo (`approved_by_user_id`, `curator_reviewed_by_user_id`) dengan `approval_evidence_ref` yang merujuk
  ADR-0008. Konten ini **tidak** pernah mengisi `partner_confirmed_*` dan tidak tampil sebagai materi resmi perguruan.
- Di publik, provenance disajikan sebagai bagian "Rujukan" (penulis, tahun, judul, halaman) dan atribusi "Disusun
  Redaksi SILATARA". Label status internal tidak ditampilkan.
- Catatan kerja (`notes`, anotasi seperti `needs_verification`) tetap tersimpan di `research/` untuk tim. API publik
  hanya mengirim `public_note`, `public_localities`, dan `public_aliases`.

