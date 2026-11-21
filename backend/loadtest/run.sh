#!/bin/sh
# Load test backend-only pada DB scratch `silatara_load` (TERISOLASI; tidak menyentuh DB dev). Pakai: make loadtest [N=300 D=20 C=20 W=1]
# Menjalankan uvicorn kedua di dalam container backend (port 8099) dengan DEBUG_QUERY_STATS=true dan rate limit dimatikan.
set -e
cd "$(dirname "$0")/../.."
N="${N:-300}"; DUR="${D:-20}"; CONC="${C:-20}"; WORKERS="${W:-1}"
DC="docker compose"
$DC exec -T db sh -c "psql -U \"\$POSTGRES_USER\" -d postgres -c 'DROP DATABASE IF EXISTS silatara_load'" >/dev/null
$DC exec -T db sh -c "psql -U \"\$POSTGRES_USER\" -d postgres -c 'CREATE DATABASE silatara_load'" >/dev/null
ENVS="-e PYTHONPATH=/app -e POSTGRES_DB=silatara_load -e RATE_LIMIT_ENABLED=false -e DEBUG_QUERY_STATS=true -e RUN_MIGRATIONS=false"
$DC exec -T $ENVS backend alembic upgrade head >/dev/null 2>&1
$DC exec -T $ENVS backend python loadtest/seed.py "$N"
$DC exec -d $ENVS backend sh -c "echo \$\$ > /tmp/lt.pid; exec uvicorn app.main:app --host 127.0.0.1 --port 8099 --workers $WORKERS --no-access-log > /tmp/loadtest-server.log 2>&1"
for i in $(seq 1 30); do $DC exec -T backend python -c "import httpx;httpx.get('http://127.0.0.1:8099/api/v1/health',timeout=2).raise_for_status()" >/dev/null 2>&1 && break; sleep 1; done
$DC exec -T $ENVS backend python loadtest/drive.py http://127.0.0.1:8099 "$DUR" "$CONC"
mkdir -p artifacts
$DC exec -T backend cat /tmp/loadtest-report.json > "artifacts/loadtest-$(date +%Y%m%d_%H%M%S)-w${WORKERS}.json"
$DC exec -T backend sh -c 'kill $(cat /tmp/lt.pid) 2>/dev/null || true'; sleep 3
$DC exec -T db sh -c "psql -U \"\$POSTGRES_USER\" -d postgres -c 'DROP DATABASE IF EXISTS silatara_load'" >/dev/null
echo "Selesai; DB scratch dibuang."
