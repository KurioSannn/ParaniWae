#!/bin/sh
set -e
cd "$(dirname "$0")/.."
mkdir -p backups
f="backups/silatara_$(date +%Y%m%d_%H%M%S).sql.gz"
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' | gzip > "$f"
echo "Cadangan dibuat: $f"
