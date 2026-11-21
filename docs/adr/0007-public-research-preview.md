# ADR-0007: Bagian publik "Riset" (pratinjau hasil riset berlabel draf)

> **Status: digantikan oleh ADR-0008 (2026-11-21).** Microsite `/riset` dihapus; isinya dilebur ke halaman utama dan URL lama dialihkan (308).

- Status: diterima atas arahan eksplisit pemilik produk (2026-11-21: "tampilkan semuanya, pastikan user real bisa lihat
  semua yang kita kerjakan")
- Tanggal: 2026-11-21

## Konteks

Hasil Sprint 9 (cakupan 38 provinsi, katalog, 43 gerakan, 23 animasi, kurikulum) berstatus draf dan hanya terlihat oleh
kurator/admin di Studio. Menandainya "terbit" akan memalsukan tinjauan kurator dan konfirmasi mitra, yang dicegah
oleh constraint DB dan dilarang CLAUDE.md (aturan 3 & 10).

## Keputusan

- Endpoint publik hanya-baca `GET /api/v1/research/*` membaca berkas `content/` dan `research/`, sumber yang sama
  dengan importer. Endpoint ini tidak menyentuh DB dan tidak mengubah status konten.
- Halaman publik `/riset` berisi ringkasan, gerakan & animasi, kurikulum, cakupan, serta sumber & inventaris, dan ditautkan
  di menu utama. Setiap halaman menampilkan banner **"Draf riset — belum divalidasi instruktur"**, label asal setiap
  klaim (dari sumber / tafsir editorial / perlu validasi), dan rujukan halaman.
- Konten riset ini tetap tidak masuk Akademi, Pustaka Gerakan, maupun Practice Studio. Ketiganya tetap hanya
  untuk konten yang sudah melewati alur tinjauan.
- Dikendalikan oleh `RESEARCH_PREVIEW_ENABLED` (default kode `false`; compose dev `true`). SVG disajikan dengan
  `Content-Security-Policy: default-src 'none'` dan `nosniff`, dan slug divalidasi sehingga path traversal tidak mungkin.

## Konsekuensi & risiko

- Materi budaya yang belum divalidasi kini terbaca publik. Mitigasinya: label jujur di setiap halaman, tidak ada klaim
  persetujuan, data kontak pribadi tidak ditampilkan, isi sumber berhak cipta hanya diparafrasa, dan teknik yang
  dilarang sumber tidak diuraikan.
- Sebelum dipakai di produksi, pemilik produk perlu memutuskan apakah pratinjau ini tetap publik atau dibatasi untuk
  pengguna yang login.
