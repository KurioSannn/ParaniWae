# Standar Konten Gerakan

Berlaku untuk `content/pencak-silat/movements/*.json` (schema `silatara.movements/v1`). Aturan di bawah ditegakkan oleh
`python -m app.cli content-validate` (`make content-validate`) dan importer. Kontrak ID ada di
[PENCAK_SILAT_CONTENT_CONTRACT.md](PENCAK_SILAT_CONTENT_CONTRACT.md).

## Struktur satu gerakan

| Bagian | Isi | Aturan |
|---|---|---|
| A. Identitas | `id`, `slug`, `names{primary, local, aliases, pronunciation}`, `category`, `level`, `safety_class`, `solo_form_status`, `content_status`, `evidence_tier`, `instructor_validation`, `permission_status` | `content_status` ∈ {draft, needs_reference}; `instructor_validation` = not_validated |
| B. Konteks budaya | `cultural_context{context, purpose, meaning, terminology, variants, differs_from}` | setiap teks punya `source_ids`/`locator` atau `basis` (gap/editorial). Makna/filosofi hanya bila sumber menyatakannya |
| C. Prasyarat | `prerequisites{abilities, physical_prep, *_ref}` | ruang/permukaan/batasan dirujuk dari `catalog/common.json` (editorial, dilabeli) |
| D. Anatomi | `anatomy{head … orientation}` (13 kunci) | tiap kunci punya `basis`: `source` (dengan `source_ids`), `editorial`, atau `needs_validation`; kunci yang tak diisi otomatis ditulis "Tidak dirinci sumber — perlu validasi instruktur" |
| E. Fase | `phases[]` dengan `id = <mv>#p<n>`, `order`, `name`, `start_position`, `change`, `body_parts`, `direction`, `end_position`, `mistakes`, `safety`, `tempo`, `keyframe_ref`, `basis`, `source_ids`, `locator` | berurutan dari 1; jumlah fase mengikuti gerak; fase `basis: source` wajib punya `source_ids` |
| F. Panduan latihan | `practice{start, sequence, tempo, repetitions, easier, progression, stop_when_ref, cooldown}` | tempo & repetisi yang tidak dari sumber diberi `basis: editorial_unvalidated` |
| G. Kesalahan umum | `common_mistakes[]` + `common_mistakes_gap` | **hanya** yang disebut sumber; bila tidak ada, kosong + penjelasan |
| H. Rujukan | `references[]{source_id, locator, supports}` | wajib ≥1; sumber `search_snippet`/`unreachable` ditolak |
| — | `gaps[]`, `landmarks[]`, `animation{animation_id, status, needs}` | `needs` wajib bila status `needs_reference` |

## Kelas keselamatan

`solo_beginner · solo_intermediate · solo_advanced · supervised_only · partner_required · restricted`.

- `solo_*` hanya boleh bila `solo_form_status = documented_solo`. Jika sumber membingkai gerak sebagai jawaban atas
  serangan dan tidak menyatakan bentuk solonya (hindaran, elakan), kelasnya `supervised_only` dengan status
  `inferred_not_documented`.
- Sesuai CLAUDE.md, importer **selalu** menulis `practice_mode = not_for_practice` dan `assessment_enabled = false`.
  Membuka Practice Studio butuh rubrik yang disetujui instruktur mitra lewat alur yang sudah ada.

## Yang tidak boleh

- Menamai atau menggabungkan gerak lintas perguruan.
- Menurunkan uraian gerak dari nama jurus. Nama saja masuk inventaris (`research/pencak-silat/movement-inventory`).
- Mengubah latihan berpasangan menjadi solo lalu mengklaimnya asli.
- Menyalin paragraf sumber. Gunakan parafrasa singkat dengan halaman.
