#!/bin/sh
# Pindai image produksi dengan Trivy (versi + digest ter-pin). Gagal (exit 1) bila ada HIGH/CRITICAL yang SUDAH ADA
# perbaikannya (--ignore-unfixed). Temuan tanpa perbaikan upstream tetap dilaporkan terpisah (tidak menggagalkan, tidak disembunyikan).
set -e
cd "$(dirname "$0")/.."
TRIVY="aquasec/trivy:0.76.2@sha256:8f6bb947dbc528902e11f2f5be52f7b519f6a39d5d148f41166f2040499768fb"
mkdir -p artifacts/trivy
docker build -q --target prod -t silatara-backend:scan backend >/dev/null
docker build -q --target prod -t silatara-frontend:scan frontend >/dev/null
rc=0
for img in silatara-backend:scan silatara-frontend:scan; do
  echo "== $img"
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache "$TRIVY" image --quiet \
    --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 "$img" || rc=1
  echo "-- (info) temuan TANPA perbaikan upstream, tidak menggagalkan:"
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache "$TRIVY" image --quiet \
    --severity HIGH,CRITICAL --format json --output /dev/stdout "$img" 2>/dev/null | python3 -c "
import json,sys,collections
d=json.load(sys.stdin); c=collections.Counter((v['Severity'],v.get('Status','')) for r in d.get('Results',[]) for v in (r.get('Vulnerabilities') or []))
print(dict(c) or 0)"
done
[ $rc -eq 0 ] && echo "Trivy: tidak ada HIGH/CRITICAL yang dapat diperbaiki." || echo "Trivy: GAGAL (ada HIGH/CRITICAL yang dapat diperbaiki)."
exit $rc
