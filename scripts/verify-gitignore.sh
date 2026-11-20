#!/bin/sh
# Memverifikasi aturan .gitignore untuk berkas sensitif TANPA membuka/membaca/menyalin isi berkas apa pun.
# Hanya memakai NAMA berkas: membuat repo Git sementara di direktori temp berisi .gitignore asli + berkas KOSONG
# bernama sama, lalu menjalankan `git check-ignore` dan `git ls-files`. Repo asli tidak disentuh (tidak ada git init).
set -e
cd "$(dirname "$0")/.."
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cp .gitignore "$TMP/.gitignore"
# Nama berkas sensitif di root (hanya nama, dengan penanganan spasi)
find . -maxdepth 1 -type f \( -name 'Lampiran*' -o -name '.env' -o -name '.env.*' \) ! -name '.env.example' -print0 | while IFS= read -r -d '' f; do
  : > "$TMP/$(basename "$f")"
done 2>/dev/null || true
mkdir -p "$TMP/backups" "$TMP/artifacts" "$TMP/frontend/public/mediapipe/models"
: > "$TMP/backups/x.sql.gz"; : > "$TMP/artifacts/a.png"; : > "$TMP/frontend/public/mediapipe/models/m.task"; : > "$TMP/.env"
cd "$TMP"; git init -q; git -c user.email=a@b.c -c user.name=x add -A 2>/dev/null
echo "== Berkas sensitif yang AKAN terlacak Git (harus kosong):"
git ls-files | grep -vE '^\.gitignore$' || echo "(kosong — aman)"
echo "== Status ignore per berkas (nama saja):"
for f in $(ls -A | grep -v '^\.git$' | tr ' ' '?' ); do :; done
git status --ignored --short | sed 's/^/  /'
echo "== Contoh aturan yang cocok:"
git check-ignore -v -- .env backups/x.sql.gz artifacts/a.png frontend/public/mediapipe/models/m.task 2>/dev/null | cut -f1 | sed 's/^/  /'
