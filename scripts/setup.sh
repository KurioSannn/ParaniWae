#!/bin/sh
# Membuat .env lokal (tidak menimpa yang sudah ada).
set -e
cd "$(dirname "$0")/.."
if [ -f .env ]; then echo ".env sudah ada — tidak diubah."; exit 0; fi
cp .env.example .env
pw="$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)"
sed_i() { if [ "$(uname)" = "Darwin" ]; then sed -i '' "$@"; else sed -i "$@"; fi; }
sed_i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$pw|" .env
sed_i "s|^HOST_UID=.*|HOST_UID=$(id -u)|" .env
sed_i "s|^HOST_GID=.*|HOST_GID=$(id -g)|" .env
echo ".env dibuat. Jika database lama sudah ada dengan sandi berbeda, jalankan: make reset-db (menghapus data lokal)."
