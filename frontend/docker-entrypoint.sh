#!/bin/sh
set -e
# node_modules ada di named volume. Bila package-lock.json berubah (mis. setelah git pull),
# sinkronkan otomatis agar tidak perlu rebuild image.
LOCK_HASH="$(sha256sum package-lock.json | cut -d' ' -f1)"
STAMP="node_modules/.lock-hash"
if [ ! -f "$STAMP" ] || [ "$(cat "$STAMP")" != "$LOCK_HASH" ]; then
  echo "[frontend] package-lock.json berubah -> npm ci"
  npm ci
  echo "$LOCK_HASH" > "$STAMP"
fi
# wasm MediaPipe di-host sendiri (offline copy dari paket npm)
mkdir -p public/mediapipe/wasm && cp -u node_modules/@mediapipe/tasks-vision/wasm/* public/mediapipe/wasm/ 2>/dev/null || true
# worker landmark (classic IIFE) dibangun dari sumber; jalankan ulang `npm run build:worker` setelah mengubahnya
npm run build:worker >/dev/null 2>&1 || echo "[frontend] PERINGATAN: build:worker gagal"
exec "$@"
