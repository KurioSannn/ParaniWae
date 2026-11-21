# Kontrak Konten Pencak Silat (Sprint 9)

Kontrak ini mengikat Anggota B (riset, dokumentasi, kurikulum, importer) dan Anggota C (rig, generator animasi,
validasi aset). Anggota A (frontend) **tidak** disentuh; frontend membaca hasil lewat API yang sudah ada setelah konten
melewati review.

## 1. Identitas (ID) — stabil, tidak pernah dipakai ulang

| Objek | Pola | Contoh |
|---|---|---|
| Sumber | `src.<penulis-atau-lembaga>.<tahun-atau-kode>[.<bagian>]` | `src.nugroho.2005` |
| Entitas katalog | `ent.<kategori>.<slug>` | `ent.perguruan.tapak-suci` |
| Tradisi konten | `trd.<kode>` | `trd.psdp` |
| Gerakan | `mv.<kode-tradisi>.<slug>` | `mv.psdp.kuda-kuda-depan` |
| Fase | `<id-gerakan>#p<n>` (n mulai 1, berurutan) | `mv.psdp.kuda-kuda-depan#p2` |
| Animasi | `anim.<kode-tradisi>.<slug>.v<versi>` | `anim.psdp.kuda-kuda-depan.v1` |
| Keyframe | `kf-<n>` di dalam satu animasi | `kf-3` |
| Kursus | `crs.<kode>` | `crs.psdp-dasar` |
| Modul | `<id-kursus>.m<nn>` | `crs.psdp-dasar.m02` |
| Pelajaran | `<id-kursus>.l<nn>` | `crs.psdp-dasar.l05` |

Regex resmi ada di `backend/app/content_import.py` (`ID_RE`) untuk konten dan di `tools/animation/validate_anim.py`
untuk animasi. Pemeriksaannya dijalankan lewat `make content-validate`, `make animations-validate`, dan importer.

Slug DB = bagian terakhir ID (`kuda-kuda-depan`). Slug unik per tradisi (constraint `uq_movements_tradition_slug`).

## 2. Status

- `content_status` (alur konten): `draft | needs_reference | pending_review | needs_revision | verified | published | archived`.
  Semua konten hasil riset sprint ini **`draft` atau `needs_reference`**. Importer menolak status lain.
- `evidence_tier`: `research_supported | instructor_confirmed | editorially_prepared`. Belum ada `instructor_confirmed`.
- `instructor_validation`: `not_validated` (satu-satunya nilai yang dipakai sprint ini).
- `animation_status`: `generated | needs_reference`. `generated` hanya berarti aset dibuat dan lolos validasi teknis;
  **bukan** berarti gerakan benar menurut instruktur.

## 3. Kelas keselamatan (content) → kolom DB

| `safety_class` (konten) | `movement_documents.safety_category` (DB) | Practice Studio |
|---|---|---|
| `solo_beginner` | `solo_beginner` | tetap `not_for_practice` sampai instruktur menyetujui |
| `solo_intermediate`, `solo_advanced`, `supervised_only` | `supervised_practice` | tidak |
| `partner_required` | `contact_practice` | tidak |
| `restricted` | `restricted` | tidak; nama saja, tanpa uraian |

Importer selalu menulis `movements.practice_mode = 'not_for_practice'` dan `assessment_enabled = false`.

## 4. Hubungan fase ↔ animasi

Setiap keyframe animasi wajib menunjuk `phase_id` milik gerakan yang sama. Setiap fase yang memiliki
`keyframe_ref` wajib muncul di animasi. Validator memeriksa keduanya.

## 5. Kepemilikan berkas

- B: `research/pencak-silat/**`, `content/pencak-silat/{catalog,curricula,lessons,movements,assessments}/**`,
  `backend/app/content_import.py`, tes importer, dokumen riset/kurikulum/provenance.
- C: `tools/animation/**`, `content/pencak-silat/animations/**`, `docs/VECTOR_ANIMATION_SPEC.md`.
- Berkas animasi `keyframes.json` ditulis C, tetapi `phase_id`-nya mengikuti dokumen gerakan milik B.
