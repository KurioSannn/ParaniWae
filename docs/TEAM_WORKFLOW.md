# Team Workflow (3 anggota)

Nama anggota belum ditetapkan di repo; gunakan peran **A/B/C** dan isi tabel di bawah dengan nama sebenarnya. Pembagian ini mengikuti [TEAM_WORKSTREAMS](../execution/TEAM_WORKSTREAMS.md) dan dapat diubah oleh tim.

## Prinsip
- Docker Compose berjalan **lokal di tiap laptop**; database tidak tersinkron. Struktur & data contoh disamakan lewat migrasi dan seed yang di-commit ([DATABASE_GUIDE](DATABASE_GUIDE.md)).
- Semua anggota selalu dapat menjalankan seluruh stack (`docker compose up`) walau hanya mengerjakan satu bagian.

## Ownership
| Peran | Area utama (owner) | Review silang |
|---|---|---|
| **A — Frontend & UX** | `frontend/src/app`, `frontend/src/components`, `frontend/src/features/{heritage,academy,progress,community}`, `DESIGN.md`, `execution/UI_*` | B untuk kontrak API |
| **B — Backend & Data** | `backend/`, `docs/DATA_MODEL.md`, `docs/API_CONTRACTS.md`, `docs/DATABASE_GUIDE.md` | A untuk kontrak, C untuk invarian budaya |
| **C — AI/CV & Konten Budaya** | `frontend/src/features/practice/`, `docs/AI_MOVEMENT_ASSESSMENT.md`, `docs/CULTURAL_PARTNER_PLAYBOOK.md`, `reference-materials/user-evidence/`, seed/konten budaya | A untuk UI kamera, B untuk penyimpanan hasil |
| **Bersama (perlu persetujuan ketiganya)** | `docker-compose.yml`, `*/Dockerfile`, `Makefile`, `scripts/`, `.env.example`, `CLAUDE.md`, `AGENTS.md`, `PRD.md`, `docs/adr/` | semua |

Bila perlu mengubah file milik orang lain: kecilkan perubahan, minta persetujuan pemilik di PR, atau minta pemilik yang melakukannya.
Isi nama: A = ____ , B = ____ , C = ____ . Salin `.github/CODEOWNERS.template` menjadi `.github/CODEOWNERS` dengan username GitHub nyata.

## Alur Git
1. **Pull sebelum mulai**: `git switch main && git pull --ff-only`, lalu `git switch -c feat/<area>-<deskripsi>`.
2. Satu branch = satu perubahan kecil; sync sering: `git fetch && git rebase origin/main` (branch pribadi saja; jangan rebase branch yang dipakai orang lain; **tidak ada force-push ke `main`**).
3. Sebelum push: `docker compose up -d` lalu `make test` dan `make smoke`.
4. Buka **Pull Request ke `main`**; minimal **1 review** dari anggota lain (2 untuk file "Bersama"). Gunakan template PR.
5. Squash-merge setelah review dan CI/tes lokal lulus. Hapus branch.
6. Setelah merge yang menyentuh `package-lock.json`, `requirements*`, `constraints.txt` atau `migrations/`: `git pull`, `make rebuild` (backend) — frontend menyinkron sendiri; migrasi diterapkan otomatis saat backend start.

## Commit convention (Conventional Commits)
`<type>(<scope>): <ringkasan imperatif>` — type: `feat fix docs refactor test chore ci build`; scope: `frontend backend cv content docker db`. Contoh: `feat(backend): tambah endpoint daftar tradisi`. Jangan commit secret, `.env`, video/foto mentah, atau materi budaya tanpa catatan izin.

## Checklist review
- Tes baru/diperbarui dan lulus; tidak ada tes dinonaktifkan.
- Migrasi ada bila skema berubah, sudah diperiksa manual, ada `downgrade`.
- Tidak ada klaim fitur/akurasi/kemitraan tanpa bukti; data contoh berlabel DEMO.
- Kamera: opt-in, bisa dihentikan, tidak ada video mentah yang tersimpan/terkirim.
- Teks UI Bahasa Indonesia, mengikuti DESIGN.md; aksesibilitas dasar (fokus, label, kontras).

## Integration testing
Sebelum merge fitur lintas area: dengan stack berjalan, jalankan `make smoke` dan `make test`, lalu uji manual alur terkait di browser. Uji kamera/AI hanya dianggap terverifikasi bila dijalankan di browser berkamera sungguhan (belum ada fitur kamera saat ini).

## Contoh kerja paralel
- **A** membangun halaman `/heritage` terhadap `GET /api/v1/traditions` (sudah ada, data DEMO).
- **B** menambah migrasi + endpoint `learning-paths` sesuai kontrak; A memakai data seed.
- **C** membangun modul `features/practice` (kualitas landmark, tipe hasil) secara terisolasi dengan tes unit; tidak menunggu UI. Aturan: tidak ada rubrik/ambang gerakan tanpa persetujuan instruktur mitra tertulis.

## Pembagian kerja sprint "Cultural Learning System" (A/B/C)
| | Fokus | Folder utama | Kontrak yang dipegang |
|---|---|---|---|
| **A — Frontend & UX** | design system, halaman akademi/warisan/perguruan, pemutar pelajaran, dasbor, UI kelola konten | `frontend/src/app`, `frontend/src/components`, `frontend/src/lib/{format,validation,manage-config}.ts` | konsumen `frontend/src/lib/types.ts` |
| **B — Backend & Data** | auth, RBAC, model konten, API, workflow, progres | `backend/app`, `backend/migrations`, `backend/tests` | **pemilik** OpenAPI (`/docs`) + `docs/API_ENDPOINTS.md` + `frontend/src/lib/types.ts` (harus diperbarui bersamaan bila schema berubah) |
| **C — AI/CV & konten budaya** | kamera, MediaPipe, quality gate, tipe AI, tes | `frontend/src/features/practice`, `frontend/src/components/CameraCheck.tsx`, `docs/AI_CV_FOUNDATION.md`, seed/konten | antarmuka `LandmarkerAdapter`, `AssessmentEngine`, `PracticeResult` |

**Bekerja paralel tanpa konflik**
- B mengubah schema → perbarui `types.ts` + `docs/API_ENDPOINTS.md` (regenerasi dari OpenAPI) dalam PR yang sama; A meninjau PR itu.
- A tidak mengedit `backend/`; B tidak mengedit `components/`/`app/` kecuali `types.ts`. C hanya menyentuh `features/practice` dan `CameraCheck`.
- Satu PR = satu area. Perubahan lintas area dipecah, atau minta persetujuan pemilik kedua area.
- **Migrasi:** hanya satu migrasi baru per PR; `git pull` + `make rebuild` sebelum membuat migrasi agar `down_revision` benar. Bila dua migrasi bercabang ("multiple heads"), yang merge belakangan menjalankan `alembic merge` (lihat DATABASE_GUIDE). Jangan mengedit migrasi yang sudah di-merge.
- Seed dikelola B; konten budaya baru ditambahkan lewat UI kelola/PR terpisah dengan catatan sumber & izin, bukan dengan mengisi seed.
- Sebelum PR: `make test`, `make e2e`, `make a11y` (stack hidup).

## Sprint kualitas (QA/keamanan) — kepemilikan, issue, dan pengujian
- Daftar issue spesifik per anggota + kriteria penerimaan: [TEAM_ISSUES](TEAM_ISSUES.md).
- Peran: **A** frontend & visual QA; **B** backend, auth, database, keamanan; **C** kamera, MediaPipe, Computer Vision.
- Sebelum PR (stack dev hidup untuk `make test`; `make e2e*` memakai stack terisolasi sendiri):
  ```bash
  make test          # backend ruff+pytest (DB *_test), frontend eslint+tsc+vitest
  make e2e           # E2E terisolasi: API+SSR lalu Playwright/Chromium (kamera palsu, visual+axe+kontras, auth, belajar)
  make smoke         # infrastruktur dev (read-only)
  make trivy         # pindai image prod (Trivy ter-pin); gagal bila ada HIGH/CRITICAL yang dapat diperbaiki
  make bench         # (opsional, ±6 menit) benchmark A/B main-thread vs Worker, kamera PALSU
  ```
  Setelah mengubah `worker/landmarker.worker.ts`: `docker compose exec frontend npm run build:worker`.
- **Data uji tidak boleh masuk DB dev.** pytest memakai `<db>_test`; E2E memakai stack terpisah (tmpfs). Jangan menulis skrip yang membuat akun/konten uji di DB dev; gunakan `make test-data-list` untuk memeriksa sisa lama.
- Laporan manual kamera: [QA_MANUAL_CAMERA_CHECKLIST](QA_MANUAL_CAMERA_CHECKLIST.md) → `docs/qa-reports/`. **Jangan menyimpan video/foto pribadi.**
- Migrasi: satu migrasi per PR; CI menjalankan up → down(base) → up. `git pull` + `make rebuild` sebelum membuat revisi.
- Perubahan kontrak API: perbarui `frontend/src/lib/types.ts` dan `docs/API_ENDPOINTS.md` (regenerasi dari OpenAPI) di PR yang sama; A meninjau.
