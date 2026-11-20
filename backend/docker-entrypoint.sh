#!/bin/sh
set -e
# Compose menjamin DB sehat (depends_on: service_healthy); retry singkat sebagai pengaman.
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  i=0
  until alembic upgrade head; do
    i=$((i+1)); [ "$i" -ge 10 ] && { echo "Migrasi gagal setelah 10 percobaan" >&2; exit 1; }
    echo "Migrasi belum berhasil, mengulang ($i/10)..." >&2; sleep 2
  done
fi
if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  python -m app.cli seed-demo
fi
exec "$@"
