# Status Validasi Konten (per 20 November 2026)

> **Pembaruan 2026-11-21 (ADR-0008):** konten riset kini tampil di halaman utama sebagai pengetahuan berbasis sumber (`source_backed`). Penerbitan di DB menunggu akun redaksi non-demo (lihat ADR-0008 bagian Konsekuensi). Status validasi instruktur di bawah tetap berlaku untuk klaim kurikulum resmi dan penilaian AI.

| Objek | Jumlah | Status konten | Validasi instruktur | Izin |
|---|---|---|---|---|
| Sumber (ledger) | 34 | — | — | 9 teks utuh, 3 halaman web, 20 cuplikan, 2 tak terjangkau |
| Entitas katalog | 80 | 61 research_supported, 19 needs_verification | — | belum diminta (semua `not_requested`) |
| Gerakan terdokumentasi (`mv.psdp.*`) | 43 | 32 draft, 11 needs_reference | **0** divalidasi | parafrasa; tanpa izin pemilik kurikulum |
| Nama gerak saja (inventaris, tradisi daerah) | 5 kelompok (Beksi 12, Cingkrik 16, Bandrong 5 baris, Kumango 13, Silek 4 konsep) | needs_reference | 0 | — |
| Animasi | 23 generated, 20 needs_reference | interpretasi editorial | **0** | dibuat sendiri (rig generik) |
| Kursus | 2 | draft | 0 | — |
| Pelajaran | 16 | draft | 0 | — |
| Baris DB hasil impor (dev) | 1 partner internal, 2 tradisi, 43 gerakan, 43 dokumen v1, 2 kursus, 9 modul, 16 pelajaran | **draft** semua | 0 | `license_type` kosong |

## Alur menuju terbit (memakai alur yang sudah ada; tidak ada jalan pintas)

1. Mitra budaya nyata diverifikasi lewat Partner Studio.
2. Kepemilikan draf dipindahkan dari partner internal ke mitra; ini keputusan manual dan belum ada otomasinya (ADR-0006).
3. Instruktur mitra merevisi dokumen gerakan: urutan fase, istilah, dan semua butir `basis: editorial`/`needs_validation`.
4. Kurator meninjau; mitra mengonfirmasi (`curator_reviewed_*`, `partner_confirmed_*`, `approval_evidence_ref`).
   Constraint DB memaksa langkah ini.
5. Animasi direvisi sesuai koreksi, lalu instruktur menyetujui atau menolaknya. Statusnya dicatat di `ANIMATION_NOTES.md`.
6. Practice Studio baru dibuka bila ada rubrik yang disetujui (aturan CLAUDE.md 4–5).

## Yang memerlukan konfirmasi instruktur (prioritas)

- Konflik uraian kuda-kuda tengah dan samping antara Nugroho dan Herdiana.
- Apakah hindaran dan elakan sah dilatih sebagai bentuk solo.
- Semua nilai tafsir animasi: panjang langkah, kedalaman kuda-kuda, tinggi angkatan, dan sisi pandang.
- Penomoran sikap pasang dan arah, serta kesesuaiannya dengan tradisi mitra.
