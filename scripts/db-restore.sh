#!/bin/sh
set -e
cd "$(dirname "$0")/.."
f="$1"
[ -f "$f" ] || { echo "Gunakan: make restore f=backups/<berkas>.sql.gz"; exit 1; }
printf "Ini MENIMPA isi database lokal dengan %s. Ketik 'ya' untuk lanjut: " "$f"; read -r a
[ "$a" = "ya" ] || { echo "Dibatalkan."; exit 1; }
gunzip -c "$f" | docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
echo "Pemulihan selesai."
