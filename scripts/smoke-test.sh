#!/bin/sh
# Smoke test: frontend, backend health, koneksi DB, migrasi, komunikasi frontend->backend.
cd "$(dirname "$0")/.."
# Baca port dari .env bila ada (env shell tetap menang)
[ -f .env ] && for k in FRONTEND_PORT BACKEND_PORT; do v=$(grep -E "^$k=" .env | cut -d= -f2); eval "[ -n \"\${$k:-}\" ] || { [ -z \"$v\" ] || $k=$v; }"; done
FE="http://localhost:${FRONTEND_PORT:-3000}"; BE="http://localhost:${BACKEND_PORT:-8000}"
fail=0
check() { # nama, perintah
  if sh -c "$2" >/dev/null 2>&1; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi
}
check "frontend dapat diakses ($FE)"            "curl -fsS $FE/"
check "backend liveness ($BE/api/v1/health)"    "curl -fsS $BE/api/v1/health | grep -q '\"status\":\"ok\"'"
check "backend -> PostgreSQL (health/ready)"    "curl -fsS $BE/api/v1/health/ready | grep -q '\"database\":\"ok\"'"
check "migrasi diterapkan (alembic_version)"    "curl -fsS $BE/api/v1/health/ready | grep -q 'migration_revision\":\"[0-9a-z_]'"
check "frontend -> backend via jaringan Docker" "curl -fsS $FE/status | grep -q 'API backend' && curl -fsS $FE/status | grep -q 'Tersambung'"
check "CORS: origin frontend diizinkan"         "curl -fsSI -H 'Origin: $FE' $BE/api/v1/health | grep -qi 'access-control-allow-origin: $FE'"
check "CORS: origin asing ditolak"              "! curl -fsSI -H 'Origin: http://evil.example' $BE/api/v1/health | grep -qi 'access-control-allow-origin'"
check "semua service healthy"                   "! docker compose ps --format '{{.Health}}' | grep -vq healthy"
[ $fail -eq 0 ] && echo "Semua smoke test lulus." || { echo "Ada smoke test gagal."; exit 1; }
