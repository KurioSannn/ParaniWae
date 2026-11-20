#!/bin/sh
# DESTRUKTIF: menghapus database lokal & cache dependency. Hanya atas konfirmasi eksplisit.
set -e
cd "$(dirname "$0")/.."
echo "PERINGATAN: menghapus SEMUA volume lokal (database, node_modules, cache .next)."
echo "Buat cadangan dulu bila perlu: make backup"
printf "Ketik 'HAPUS DATA' untuk lanjut: "; read -r a
[ "$a" = "HAPUS DATA" ] || { echo "Dibatalkan."; exit 1; }
docker compose down -v --remove-orphans
echo "Selesai. Jalankan 'docker compose up --build' untuk memulai ulang dari kosong."
