# ADR-0001: Docker Compose dev environment, struktur `frontend/` + `backend/`

Status: diterima (19 November 2026) · Tipe: PRODUCT-DECISION

## Konteks
Tiga anggota tim, tiga laptop; harus konsisten tanpa instalasi Python/Node/PostgreSQL manual. Repo saat ini hanya berisi dokumentasi. `docs/TECHNICAL_ARCHITECTURE.md` menyarankan `apps/web` + `services/api` tetapi menyatakan struktur harus disesuaikan, dan permintaan tim menyebut `frontend/` dan `backend/`.

## Keputusan
- Struktur sederhana `frontend/` (Next.js 16, TypeScript, Tailwind 4) dan `backend/` (FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16). Bukan workspace monorepo (tidak ada paket bersama saat ini; `packages/assessment` dapat ditambahkan jika modul asesmen perlu dibagi).
- Docker Compose lokal per laptop, hanya 3 service (db, backend, frontend). Tidak ada Redis/Celery/broker/object storage (belum dibutuhkan MVP).
- Dependency dikunci: `package-lock.json`; `requirements*.txt` + `constraints.txt`. Runtime: Node 22, Python 3.12, PostgreSQL 16.6.
- Container non-root; port hanya di 127.0.0.1; venv di dalam image; `node_modules` di named volume.
- Inferensi CV dilakukan di browser (MediaPipe) pada tahap fitur kamera; backend tidak menerima video mentah.
- Font: system font stack dahulu (tanpa panggilan ke layanan pihak ketiga); font DESIGN.md di-host sendiri nanti.

## Belum diputuskan (perlu ADR sendiri)
Penyedia autentikasi & model sesi; format rubrik/asesmen; penyimpanan aset; telemetri/privasi; deployment.

## Konsekuensi
Onboarding satu perintah; perubahan dependency backend butuh rebuild image; database tidak tersinkron antar laptop (disamakan lewat migrasi + seed).
