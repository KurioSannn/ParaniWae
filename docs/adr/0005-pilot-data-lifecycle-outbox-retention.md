# ADR-0005: Siklus hidup data pilot (retensi/anonimisasi) dan outbox notifikasi

Status: diterima (20 November 2026) · Tipe: ARCHITECTURE-DECISION + PRODUCT-DECISION (butuh peninjauan pemilik)

## Konflik/ambiguitas yang ditemukan di kebijakan existing (tidak diubah diam-diam)
1. `PILOT_PRIVACY_RETENTION.md` menyatakan anonimisasi setelah `completed` + 365 hari, namun yang dianonimkan hanya **jawaban survei, catatan instruktur, undangan**. Data **penggunaan** (`cohort_members`, `lesson_progress`, `practice_sessions`) tetap terikat akun (dihapus bersama akun). Persetujuan opsional (`pilot_consents`) juga tetap sebagai catatan persetujuan.
2. Kebijakan tidak mendefinisikan program `cancelled` (tidak punya `completed_at`).
3. Dokumen sebelumnya menyebut "perintah CLI anonimisasi manual: backlog".

## Keputusan
- **Retensi 365 hari TIDAK diubah.** Jalur terjadwal tetap hanya untuk `completed|archived` yang `completed_at` melewati `PILOT_RETENTION_DAYS`.
- Data penggunaan **tetap** terikat akun setelah anonimisasi survei (perilaku existing, dipertahankan agar agregat usage tetap dapat dihitung). **Keputusan pemilik dibutuhkan:** apakah usage per-akun juga harus dilepas dari identitas setelah retensi (mis. pseudonimisasi `cohort_members.user_id`)? Sementara itu hak hapus diwujudkan lewat penghapusan akun (FK `CASCADE`/`SET NULL`).
- Program `cancelled`: tidak otomatis eligible. Penghapusan dini memakai **`--early --reason`** (eksplisit, tercatat di audit) — bukan jalur otomatis.
- Persetujuan riset/publikasi opsional **tidak diperluas**: hanya menentukan masuk-tidaknya data ke laporan agregat riset/kutipan; tidak memberi izin penggunaan lain, dan tidak membuat data operasional menjadi "milik riset".
- **CLI `pilot-anonymize`:** dry-run default; filter program/cohort/`--completed-before`; konfirmasi persis `ANONIMKAN <N> PROGRAM`; operator harus admin aktif; **bukti backup** (`--backup-manifest` valid: umur ≤24 jam, revisi skema sama, sha256 cocok) kecuali `--accept-no-backup` (tercatat); transaksi per-program (savepoint) + verifikasi pasca-operasi; idempoten; audit memuat operator + jumlah saja.
- **Worker retensi terjadwal** memakai `pg_try_advisory_xact_lock` + tabel `job_runs` (interval default 24 jam) → satu eksekusi pada satu waktu; laporan eligible/diproses/gagal tanpa PII. Dapat dimatikan (`RETENTION_AUTO_ENABLED=false`).

## Outbox
- Klaim atomik `FOR UPDATE SKIP LOCKED` + **lease**; status `sending`; pemulihan crash otomatis; penyelesaian dikunci `claimed_by`.
- Retry exponential backoff + jitter (base 30 dtk, cap 1 jam, 6 percobaan); klasifikasi `transient | permanent | provider_unavailable`; provider tak tersedia **tidak** menghabiskan jatah percobaan tetapi dibatasi usia (72 jam → `dead`).
- `dead` = dead-letter terstruktur (`dead_at`, kategori, galat tersanitasi tanpa alamat/isi). Antre-ulang hanya bila isi belum diredaksi.
- Pesan yang sudah terkirim di-**redaksi** isinya (tautan undangan mengandung token). **Garansi: at-least-once untuk SMTP** (crash tepat setelah SMTP menerima ⇒ kirim ulang), dimitigasi `Message-ID` deterministik; `dev_sink` exactly-once.
- Pembersihan: `sent/dev_sink` > 30 hari, `dead` > 180 hari (konfigurasi); **tidak pernah** `pending|sending|undeliverable`; dry-run default; audit jumlah saja.
