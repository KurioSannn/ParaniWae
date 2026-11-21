# ADR-0006: Pemilik teknis draf konten riset (partner editorial internal)

> **Diubah oleh ADR-0008 (2026-11-21).** Partner internal redaksi tetap dipakai sebagai pemilik teknis baris `source_backed`. Konten ini kini dapat terbit lewat tinjauan editorial sumber, tanpa pemindahan ke mitra dan tanpa mengklaim konfirmasi mitra.

- Status: diusulkan (perlu persetujuan pemilik produk)
- Tanggal: 2026-11-20

## Konteks

`movements.partner_id` dan `courses.partner_id` wajib diisi (NOT NULL). Konten Sprint 9 berasal dari riset
pustaka, bukan dari mitra. CLAUDE.md melarang mengarang mitra atau instruktur, sehingga draf tidak boleh dipasang ke
perguruan nyata tanpa persetujuan perguruan tersebut.

## Keputusan

Importer membuat satu baris `partners` internal:

- slug `silatara-tim-editorial-internal`, nama "Tim Editorial SILATARA (internal — bukan mitra budaya)";
- `verification_status = draft`, `public_listing_consent = false`, `status = draft`;
- relasi `tradition_partners.relationship_type = research_partner`.

Partner ini **tidak** pernah diverifikasi, sehingga constraint dan aturan visibilitas yang ada mencegah kontennya
terbit atau tampil di direktori. Partner editorial hanya penampung teknis untuk draf.

## Konsekuensi

- Draf dapat ditinjau kurator di Studio. Akses mengikuti izin Studio yang ada untuk partner tersebut; admin dan kurator dapat melihat.
- Sebelum diverifikasi, kepemilikan draf **harus** dipindahkan ke mitra nyata. Belum ada perintah otomatis untuk ini;
  pemindahannya dilakukan manual oleh admin dan membutuhkan keputusan dengan mitra.
- Alternatif yang ditolak:
  1. Mengubah `partner_id` menjadi nullable: perubahan skema besar dan melemahkan invarian.
  2. Memakai partner demo: akan mencampur data riset dengan data `[DEMO]`.

## Yang perlu diputuskan pemilik

Setujui atau ganti nama partner internal. Tentukan juga apakah draf riset boleh dilihat instruktur mitra lain sebagai bahan diskusi.
