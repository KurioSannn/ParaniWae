# Alur Konten Budaya, Provenance, dan Verifikasi

## Status (satu mesin status untuk tradisi, mitra, instruktur, gerakan, kurikulum, pelajaran)
```
draft ──submit──▶ pending_review ──approve──▶ verified ──publish──▶ published
  ▲                   │ reject                                         │ unpublish
  └─── rejected ◀─────┘                                                ▼ (kembali draft; persetujuan dihapus)
archived ◀── archive (dari status mana pun)      restore ──▶ draft
```
- **Hanya `published`** yang tampil di API/katalog publik. draft, pending_review, rejected, verified, archived tidak pernah bocor (diuji di `tests/test_public_catalog.py` dan `tests/e2e_flow.py`).
- Visibilitas dihitung di satu tempat: `backend/app/services/visibility.py`. Turunan ikut tersembunyi bila induknya tidak publik (kursus ← tradisi & mitra; pelajaran ← kursus).
- Edit hanya pada `draft`/`rejected`. Konten terbit harus ditarik dulu (`unpublish`) agar bisa diubah, sehingga perubahan selalu melewati review ulang.
- Konten dibuat selalu `draft`, `is_demo=false`. Field status/approval/is_demo **tidak dapat diisi lewat API** (schema `extra=forbid`).

## Peran
| Peran | Boleh |
|---|---|
| learner | membaca katalog publik, mengikuti kurikulum, mencatat progres sendiri |
| instructor | membuat/mengedit/mengajukan **draf miliknya** untuk gerakan, kurikulum, pelajaran (+modul, materi); tidak dapat menyetujui/menerbitkan; tidak melihat milik orang lain |
| curator | semua jenis konten; submit/approve/reject/publish/unpublish/archive; **tidak dapat menyetujui konten buatannya sendiri** |
| admin | seperti curator (dapat menyetujui konten sendiri; dicatat di audit) + kelola pengguna/peran + lihat audit |

## Provenance & label verifikasi
- Setiap konten memiliki `source_citation` (wajib sebelum `submit`), `source_url`, `approved_by_user_id`, `approved_at`, `approval_evidence_ref`.
- Konten **non-demo** wajib `approval_evidence_ref` saat `approve` (bukti persetujuan mitra, mis. berita acara). CHECK constraint DB: status verified/published non-demo wajib punya penyetuju + waktu + sumber.
- Label UI: `Terverifikasi oleh mitra` **hanya** bila non-demo, verified/published, ada penyetuju **dan** bukti persetujuan. Data demo: `[DEMO] Contoh teknis — belum diverifikasi mitra`. Selain itu: `Belum diverifikasi mitra`.
- Direktori mitra non-demo hanya bila `verification_status=verified` **dan** `public_listing_consent`. Profil instruktur non-demo hanya bila `public_profile_consent`.
- Tradisi non-demo hanya dapat diterbitkan dengan `access_scope=public` (community/restricted tidak pernah tampil di katalog publik).
- Ketergantungan terbit: kurikulum butuh tradisi+mitra(+instruktur) terbit; pelajaran butuh kurikulum (+gerakan) terbit.

## Audit trail
`audit_logs` mencatat: `content.create/update/delete/submit/approve/reject/publish/unpublish/archive/restore`, `content.module_create`, `content.material_create`, `user.register/login/login_failed/logout/update`, `enrollment.*` — dengan aktor, entitas, detail (status asal/tujuan, catatan), dan `request_id`. Riwayat per konten tampil di halaman Kelola; admin dapat melihat log global.

## Menyiapkan satu mitra mengelola tradisinya sendiri (belum diimplementasikan)
Skema sudah memisahkan `partners`, `instructors`, `tradition_partners`, dan `approval_evidence_ref`. Yang belum ada (menunggu mekanisme kemitraan): peran `partner_admin` berlingkup-mitra, relasi user↔mitra, dan aturan bahwa persetujuan budaya harus datang dari instruktur mitra (bukan sekadar kurator platform). Sampai itu ada, kurator/admin platform yang menekan "setujui", dan **bukti persetujuan mitra harus dicantumkan manual** — sistem tidak dapat memverifikasi keaslian bukti tersebut.

## Data demo
Seed `[DEMO]` (backend/app/seed.py) fiktif/placeholder: tidak memuat sejarah, filosofi, teknik, nama maestro, atau klaim kemitraan. Ada draf/pending sengaja untuk menguji tidak bocor. Akun demo (hanya `APP_ENV=development`): `demo-{pelajar,instruktur,kurator,admin}@silatara.test`, sandi `DEMO_USER_PASSWORD` (default `demo-sandi-12345`).
