# Kontrak bersama: Instructor & Partner Studio

Ditetapkan **sebelum** A/B/C bekerja paralel. Perubahan kontrak = PR yang sama dengan pembaruan tipe (`frontend/src/lib/types.ts`) dan dokumen ini.

## 0. Prinsip (batas keras)
- SILATARA **tidak** mengisi sejarah, filosofi, makna simbolik, asal-usul, atau teknik dengan teks buatan. Semua isi dokumentasi adalah **yang diketik instruktur**. Seed demo selalu `[DEMO]`.
- Membuat profil/mengisi formulir **tidak** menjadikan organisasi "mitra resmi". Status `verified` hanya lewat keputusan **admin** dengan **bukti** (rujukan + ≥1 dokumen persetujuan terunggah) dan menyimpan identitas + waktu.
- Kategori keselamatan = **klasifikasi administratif**, bukan sertifikasi keselamatan otomatis.
- Konten terpublikasi **tidak diubah diam-diam**: versi `published`/`archived` bersifat immutable (dijaga trigger DB). Perubahan = versi baru + changelog + review ulang.
- Tidak ada skor benar-salah, ambang biomekanik, similarity, atau koreksi otomatis. Anotasi = **instructor reference annotation**, bukan ground truth ilmiah dan bukan label akurasi.
- File mentah dan dokumen persetujuan **tidak** pernah lewat URL statis publik; selalu lewat endpoint terotorisasi.

## 1. Model data (ringkas)
Menggunakan ulang: `partners`, `instructors`, `tradition_partners`, `movements` (identitas + penunjuk versi tayang), `lessons.movement_id`, `audit_logs`, mesin `ACTIONS` workflow.

| Tabel | Isi |
|---|---|
| `partners` (+kolom) | `verification_status` ∈ `draft|pending_verification|verified|rejected|suspended`; penanggung jawab (`responsible_name/role/contact`), kontak (`contact_email/phone`), `verification_decided_by_user_id`, `verification_decided_at`, `verification_note`, `submitted_at` |
| `partner_members` | `partner_id, user_id, role(manager|instructor), status(active|removed)`; unik per pasangan. **Izin partner manager = peran keanggotaan, bukan peran global baru** |
| `partner_documents` | dokumen persetujuan/identitas **privat** (metadata + `storage_key`, sha256, mime, ukuran) |
| `partner_verification_events` | riwayat: aksi, dari→ke, aktor, catatan, `evidence_ref`, waktu |
| `instructors` (+`user_id`) | menghubungkan profil publik instruktur ke akun |
| `movements` (+kolom) | `published_document_id`, `published_version_no`, `level`, `safety_category` (denormalisasi dari versi tayang untuk filter & eligibility) |
| `movement_documents` | **satu baris per versi**: `movement_id, version_no`, mixin workflow (status…), isi dokumentasi, `changelog`, konfirmasi mitra, tinjauan kurator |
| `movement_phases` | fase berurutan per versi; jumlah/definisi ditentukan instruktur |
| `reference_media` | metadata media + deklarasi hak + status persetujuan + akses + retensi; file di storage privat |
| `movement_annotations` | anotasi referensi instruktur (timestamp/fase) + provenance |

## 2. Lifecycle
**Kemitraan (`partners.verification_status`):** `draft → (manager) submit → pending_verification → (admin) verify → verified | reject → rejected → (manager) reopen → draft | suspend → suspended → (admin) reinstate → pending_verification`. `submit` mensyaratkan: penanggung jawab + email kontak + ≥1 tradisi + ≥1 dokumen. `verify` mensyaratkan `evidence_ref` + ≥1 dokumen; mencatat identitas admin + waktu. Hanya `verified` + `public_listing_consent` yang tampil di direktori publik (non-demo).

**Dokumen gerakan (`movement_documents.status`):** `draft → submit → pending_review ⇄ needs_revision`; dari `pending_review`: `curator_review` (menandai kelengkapan+provenance ditinjau, status tetap), `confirm_partner` (manager mitra pemilik, bukan penulis), `request_revision` (→`needs_revision`, catatan wajib), `reject` (→`rejected`, catatan wajib), `approve` (→`verified`; butuh tinjauan kurator + konfirmasi mitra + `evidence_ref`; non-demo), `publish` (admin; `verified → published`; versi tayang lama → `archived`), `archive`. **Tidak ada `restore`**: versi `archived` final (trigger DB); untuk menghidupkan kembali isi lama, buat versi baru. `draft/needs_revision/rejected` dapat diedit; `pending_review/verified/published/archived` **tidak**.
**Aksi mitra (verifikasi):** `submit, verify, reject, suspend, reopen, reinstate, publish_listing, unlist`. Admin yang juga **anggota** mitra tidak boleh memutuskan verifikasi mitra itu (`SELF_APPROVAL`). `publish_listing` mensyaratkan `verified` + `public_listing_consent` (diberikan manager setelah terverifikasi).

**Tidak ada persetujuan sendiri:** penulis dokumen tidak dapat melakukan `curator_review`, `confirm_partner`, `approve`, atau `publish` atas dokumennya — **termasuk admin** (khusus gerakan).

## 3. Matriks izin
| Aksi | learner | instructor (anggota mitra) | partner manager | curator | admin |
|---|---|---|---|---|---|
| Baca konten `published` | ✓ | ✓ | ✓ | ✓ | ✓ |
| Buat profil mitra (draft, jadi manager) | – | ✓ | – | ✓ | ✓ |
| Ubah profil mitra (draft/rejected) | – | – | ✓ | – | ✓ |
| Kelola anggota, unggah dokumen persetujuan, ajukan verifikasi | – | – | ✓ | – | ✓ |
| Lihat dokumen persetujuan mitra | – | – | ✓ | ✓ | ✓ |
| Verifikasi / tolak / tangguhkan mitra | – | – | – | – | ✓ |
| Buat & edit dokumentasi gerakan mitranya | – | ✓ | ✓ | ✓ (semua) | ✓ (semua) |
| Ajukan review | – | ✓ (penulis/anggota) | ✓ | ✓ | ✓ |
| `curator_review`, `request_revision`, `reject`, `approve` | – | – | `request_revision`, `confirm_partner` | ✓ | ✓ |
| `publish` | – | – | – | – | ✓ |
| Unggah media (dgn deklarasi hak) | – | ✓ | ✓ | ✓ | ✓ |
| Setujui media / ubah akses | – | – | ✓ (mitranya) | ✓ | ✓ |
| Akses file media | – | `private`: uploader · `reviewers`: semua anggota mitra | ✓ (semua) | ✓ | ✓ |
| Anotasi referensi | – | ✓ | ✓ | ✓ | ✓ |
Lintas organisasi: anggota mitra A **tidak** dapat melihat/mengubah dokumen, media, atau dokumen persetujuan mitra B (404).

## 4. API (prefix `/api/v1`; sesi + CSRF; pagination `{items,page,page_size,total,total_pages}`; galat `{error:{code,message,details,request_id}}`)
**Mitra:** `GET/POST /studio/partners`, `GET/PATCH /studio/partners/{id}`, `POST /studio/partners/{id}/members`, `DELETE …/members/{user_id}`, `PUT|DELETE …/traditions/{tradition_id}`, `POST/GET …/documents`, `GET /studio/partner-documents/{id}/file`, `POST …/verification {action,note,evidence_ref}`, `GET …/history`.
**Gerakan:** `GET/POST /studio/movements`, `GET /studio/movements/{id}`, `PATCH /studio/documents/{doc_id}`, `PUT /studio/documents/{doc_id}/phases`, `POST /studio/movements/{id}/versions`, `POST /studio/documents/{doc_id}/transition {action,note,evidence_ref}`, `GET /studio/movements/{id}/history`, `PUT|DELETE /studio/movements/{id}/lessons/{lesson_id}`, `GET /studio/dashboard`.
**Media:** `POST /studio/movements/{id}/media` (multipart), `GET /studio/movements/{id}/media`, `PATCH /studio/media/{id}`, `DELETE /studio/media/{id}`, `GET /media/{id}/file` (terotorisasi; anonim hanya bila `public` + `approved` + gerakan `published`).
**Anotasi:** `GET/POST /studio/movements/{id}/annotations`, `PATCH|DELETE /studio/annotations/{id}`.
**Publik:** `GET /movements` (filter `q, tradition, partner, level, safety_category, partner_verified, page`), `GET /movements/{id}` (dokumentasi tayang + fase + sumber + versi), `GET /movements/{id}/versions` (riwayat publik: versi tayang + changelog), `GET /partners` (hanya verified+publik atau demo berlabel), lesson detail → `movement` diperkaya.

## 5. Struktur dokumentasi (isi hanya dari instruktur)
`name_id`, `name_local?`, `level` (`beginner|intermediate|advanced`), `safety_category` (`solo_beginner|supervised_practice|contact_practice|weapon_related|restricted`), `prerequisites?`, `learning_context?`, `description` (ditulis instruktur), `terminology_notes?` (variasi/istilah lokal), `common_mistakes[]` (menurut instruktur), `safety_guidance`, `relevant_body_parts[]` (teks bebas) + `relevant_landmarks[]` (indeks MediaPipe 0–32, opsional), `source_citation`, `source_url?`, **hak**: `author_declaration` (bool), `rights_holder`, `license_type` (`instructor_owned|partner_permission|other_written_permission`), `usage_scope`, `changelog`. **Fase:** `{order_index, name, instruction, body_focus[], safety_note?, start_ms?, end_ms?}`.
Kelengkapan untuk `submit`: nama, tradisi, mitra, level, kategori, deskripsi, ≥1 fase (dengan nama+instruksi), arahan keselamatan, sumber, deklarasi hak; `solo_beginner` juga wajib `prerequisites` + `learning_context`; versi >1 wajib `changelog`.
Pemetaan eligibility Practice Studio (aturan existing dipertahankan): kategori `solo_beginner` → `practice_mode=solo_beginner`; `supervised_practice` → `supervised_only`; lainnya → `not_for_practice`. `assessment_enabled` tetap `false`.

## 6. Media
Upload hanya setelah **deklarasi**: `rights_holder`, `source_description`, `license_type`, `usage_scope`, `declaration_confirmed=true`. Tipe: mp4/webm/jpeg/png/webp (diverifikasi magic bytes, bukan hanya ekstensi), maks 100 MB (video) / 10 MB (gambar). Disimpan di storage privat dengan nama acak; metadata: sha256, ukuran, mime, `access_level` (`private|reviewers|public`, default `private`), `consent_status` (`declared|verified|rejected|revoked`), `retention_until`. Tidak ada pengambilan media dari internet. Dokumentasi tekstual tanpa media tetap sah.

## 7. Anotasi referensi (Calibration Workspace)
`{id, movement_id, media_id | fixture_key("demo-synthetic"), phase_id?, kind(phase_marker|note), timestamp_ms, label, note, annotator_user_id, model_version?, source_note, review_status(pending|accepted|rejected), created_at}`. Selalu berlabel **instructor reference annotation**. Overlay MediaPipe dihitung di browser (tidak disimpan); yang disimpan hanya timestamp + provenance + versi model.

## 8. Pembagian file
- **A:** `frontend/src/app/app/studio/**`, `frontend/src/app/library/**`, `components/Studio*`, `components/Library*`, integrasi lesson/academy, nav, `lib/studio-api.ts`.
- **B:** `backend/app/{models/studio.py,schemas/studio.py,services/{storage,studio_perm,partner_studio,movement_studio,media,annotations}.py,api/v1/{studio_partners,studio_movements,media}.py}`, migrasi, seed, `backend/tests/test_studio*.py`, `lib/types.ts` (bagian studio), docs API.
- **C:** `frontend/src/features/calibration/**`, `components/CalibrationWorkspace.tsx`, halaman `…/calibration`, tes unit terkait.

## 9. Kriteria penerimaan (sprint ini)
Instruktur dapat: membuat mitra draft; menambah anggota; mendokumentasikan satu gerakan lengkap (fase, keselamatan, sumber, hak); menghubungkannya ke lesson; mengajukan review; menerima keputusan (revisi/tolak/setuju) dengan catatan; menerbitkan versi pertama dan versi baru dengan changelog tanpa menghapus jejak; melihat gerakan di library dan lesson; dan hanya gerakan `solo_beginner` terbit yang membuka Practice Studio. Media hanya dengan deklarasi; file privat tidak terbuka; lintas organisasi 404.

## 10. Perubahan terhadap rancangan awal (dicatat saat implementasi)
- `needs_revision` ditambahkan ke constraint status **semua** tabel workflow (traditions, partners, instructors, movements, courses, lessons, movement_documents); alur lama tidak berubah.
- Jenis `movements` dihapus dari `/manage` (satu mekanisme approval gerakan = Studio); celah `PartnerIn.verification_status/public_listing_consent` ditutup.
- Media `private` = uploader + manager mitra + kurator/admin; `reviewers` = semua anggota mitra + kurator/admin; `public` = siapa pun **hanya** bila izin `verified` + gerakan terbit + belum lewat retensi. Pencabutan izin menutup akses segera.
- Verifikasi izin media tidak boleh oleh pengunggahnya sendiri; tinjauan anotasi tidak boleh oleh pembuatnya.
- `audit_logs.created_at` kini diisi waktu aplikasi (bukan `now()` transaksi) agar urutan riwayat stabil.
- Seed `[DEMO]`: 5 akun (pelajar, 2 instruktur, kurator, 2 admin); dokumentasi demo pada status draft/pending_review/needs_revision/rejected/verified/published/archived + versi 1 diarsipkan & versi 2 tayang; 3 penanda fixture `demo-synthetic`.
