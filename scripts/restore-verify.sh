#!/bin/sh
# Verifikasi restore di lingkungan SCRATCH (database sementara + direktori sementara). TIDAK PERNAH menyentuh DB/volume dev.
# Pakai: ./scripts/restore-verify.sh backups/full_...   (cadangan terenkripsi: set BACKUP_ENCRYPTION_KEY_FILE)
# Langkah: sha256 ciphertext -> HMAC manifest -> dekripsi -> sha256 plaintext -> restore scratch -> migrasi maju -> sha256 tiap media.
set -e
cd "$(dirname "$0")/.."
DC="${DC:-docker compose}"
D="${1:?pakai: restore-verify.sh <direktori cadangan penuh>}"
SCRATCH="silatara_restore_verify"
T0="$(date +%s)"
sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
field() { sed -n "s/.*\"$1\":\"\\([^\"]*\\)\".*/\\1/p" "$D/manifest.json" | head -1; }
ENCFLAG="$(sed -n 's/.*"encryption":{"enabled":\([a-z]*\).*/\1/p' "$D/manifest.json")"
echo "== cek integritas berkas cadangan (sha256 sebagaimana tersimpan)"
[ "$(sha "$D/$(field db_dump)")" = "$(field db_sha256)" ] || { echo "GAGAL: sha256 dump tidak cocok"; exit 1; }
[ "$(sha "$D/$(field media_tar)")" = "$(field media_sha256)" ] || { echo "GAGAL: sha256 arsip media tidak cocok"; exit 1; }
TMP="$(mktemp -d)"; chmod 700 "$TMP"
cleanup() {
  $DC exec -T db sh -c "psql -U \"\$POSTGRES_USER\" -d postgres -c 'DROP DATABASE IF EXISTS $SCRATCH'" >/dev/null 2>&1 || true
  $DC exec -T backend rm -rf /tmp/restore-media >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT
cleanup; TMP="$(mktemp -d)"; chmod 700 "$TMP"
if [ "$ENCFLAG" = "true" ]; then
  [ -n "$BACKUP_ENCRYPTION_KEY_FILE" ] && [ -f "$BACKUP_ENCRYPTION_KEY_FILE" ] || { echo "GAGAL: cadangan terenkripsi, set BACKUP_ENCRYPTION_KEY_FILE"; exit 2; }
  HM="$(field manifest_hmac)"
  if [ -n "$HM" ]; then
    MK="$(printf 'silatara-manifest-v1:%s' "$(cat "$BACKUP_ENCRYPTION_KEY_FILE")" | openssl dgst -sha256 -binary | xxd -p -c 64)"
    sed "s/,\"manifest_hmac\":\"[0-9a-f]*\"}\$/}/" "$D/manifest.json" > "$TMP/body"
    [ "$(openssl dgst -sha256 -hmac "$MK" "$TMP/body" | awk '{print $NF}')" = "$HM" ] || { echo "GAGAL: HMAC manifest tidak cocok (manifest diubah atau kunci salah)"; exit 1; }
    echo "   HMAC manifest OK"
  fi
  echo "== dekripsi ke direktori sementara (chmod 700)"
  dec() { openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -pass "file:$BACKUP_ENCRYPTION_KEY_FILE" -in "$1" -out "$2" || { echo "GAGAL: dekripsi (kunci salah/berkas rusak)"; exit 1; }; }
  dec "$D/$(field db_dump)" "$TMP/db.dump"; dec "$D/$(field media_tar)" "$TMP/media.tar"
  [ "$(sha "$TMP/db.dump")" = "$(field db_plain_sha256)" ] || { echo "GAGAL: sha256 plaintext dump"; exit 1; }
  [ "$(sha "$TMP/media.tar")" = "$(field media_plain_sha256)" ] || { echo "GAGAL: sha256 plaintext media"; exit 1; }
else
  cp "$D/$(field db_dump)" "$TMP/db.dump"; cp "$D/$(field media_tar)" "$TMP/media.tar"
fi
echo "== restore ke database scratch '$SCRATCH'"
$DC exec -T db sh -c "psql -U \"\$POSTGRES_USER\" -d postgres -c 'CREATE DATABASE $SCRATCH'" >/dev/null
$DC exec -T db sh -c "pg_restore -U \"\$POSTGRES_USER\" -d $SCRATCH --no-owner --exit-on-error" < "$TMP/db.dump"
echo "== migrasi maju pada salinan scratch (cadangan lama -> skema terbaru)"
$DC exec -T -e POSTGRES_DB="$SCRATCH" backend alembic upgrade head 2>&1 | tail -2
echo "== ekstrak media ke /tmp/restore-media (scratch)"
$DC exec -T backend sh -c 'rm -rf /tmp/restore-media && mkdir -p /tmp/restore-media && tar -C /tmp/restore-media -xf -' < "$TMP/media.tar"
echo "== verifikasi konsistensi DB <-> media (sha256 setiap berkas)"
$DC exec -T -e POSTGRES_DB="$SCRATCH" backend python -m app.cli verify-media --root /tmp/restore-media
echo "Restore-verify selesai dalam $(( $(date +%s) - T0 )) detik (diukur; bukan janji RTO)"
