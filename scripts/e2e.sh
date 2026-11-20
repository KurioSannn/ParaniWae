#!/bin/sh
# E2E TERISOLASI: stack terpisah (project silatara-e2e, DB tmpfs, tanpa port host).
# Tidak menyentuh stack/volume/database pengembangan.   Pakai: ./scripts/e2e.sh [api|browser|all]   Env: KEEP=1, PW_ARGS="--project=camera-fake"
set -e
cd "$(dirname "$0")/.."
MODE="${1:-all}"
F="-f docker-compose.e2e.yml"
mkdir -p artifacts
[ -f frontend/public/mediapipe/models/pose_landmarker_lite.task ] || ./scripts/fetch-mediapipe-assets.sh
cleanup() { docker compose $F --profile browser down --remove-orphans >/dev/null 2>&1 || true; }
[ -n "$KEEP" ] || trap cleanup EXIT INT TERM   # KEEP=1: biarkan stack hidup untuk iterasi (matikan: make e2e-down)
echo "== membangun & menjalankan stack E2E terisolasi (project silatara-e2e)"
docker compose $F up -d --build --wait --wait-timeout 600
rc=0
if [ "$MODE" = "api" ] || [ "$MODE" = "all" ]; then
  echo "== E2E API+SSR (python)"
  docker compose $F exec -T backend python tests/e2e_flow.py || rc=1
fi
if [ "$MODE" = "browser" ] || [ "$MODE" = "all" ]; then
  echo "== E2E browser (Playwright/Chromium)"
  docker compose $F --profile browser run --rm browser || rc=1
fi
exit $rc
