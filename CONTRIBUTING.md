# Contributing

Baca [docs/TEAM_WORKFLOW.md](docs/TEAM_WORKFLOW.md) (ownership, alur Git, commit convention, review) dan [CLAUDE.md](CLAUDE.md) (aturan non-negotiable proyek).

## Setup
`docker compose up --build` — hanya butuh Docker + Git. Detail di [README](README.md).

## Sebelum membuka PR
```bash
make test     # ruff + pytest, eslint + tsc + vitest
make smoke    # smoke test end-to-end
```
- Jangan menonaktifkan/menghapus tes agar build lulus.
- Jangan commit `.env`, secret, dump database, video/foto mentah.
- Perubahan skema = migrasi Alembic yang sudah diperiksa.
- Konten budaya: catat sumber, atribusi, izin, level akses, dan status review sebelum dipublikasikan; data contoh wajib berlabel DEMO.
- Jangan membuat klaim (fitur, akurasi AI, kemitraan, jumlah pengguna) tanpa bukti.
- Perubahan arsitektur/stack/data lifecycle: tambahkan ADR di `docs/adr/`.
