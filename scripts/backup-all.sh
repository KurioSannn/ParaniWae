#!/bin/sh
# Cadangan KONSISTEN + (opsional) TERENKRIPSI: database (pg_dump -Fc) + volume media_data (tar) + manifest.
#   Urutan: DB dahulu, media sesudahnya -> setiap baris dump punya berkas di arsip (kecuali dihapus/purge di antara keduanya;
#   restore-verify melaporkannya). Berkas media immutable & bernama acak.
#   Enkripsi: set BACKUP_ENCRYPTION_KEY_FILE=<berkas passphrase, chmod 600, DI LUAR repo>; BACKUP_KEY_ID=<label bebas>.
#   AES-256-CBC + PBKDF2-SHA256 (600k iterasi) via `openssl enc`; integritas = sha256 ciphertext + sha256 plaintext + HMAC manifest.
#   Tanpa kunci -> cadangan POLOS (manifest mencatat encryption.enabled=false; `make doctor` menandainya).
#   BACKUP_DESTINATION=local (default) | s3://bucket/prefix  (pengiriman: scripts/backup-ship.sh; TIDAK dianggap berhasil tanpa verifikasi).
set -e
cd "$(dirname "$0")/.."
DC="${DC:-docker compose}"   # uji terisolasi: DC="docker compose -f docker-compose.e2e.yml"
TS="$(date +%Y%m%d_%H%M%S)"
ID="full_${TS}_$(LC_ALL=C tr -dc 'a-f0-9' </dev/urandom | head -c6)"
D="backups/$ID"
mkdir -p "$D"; chmod 700 "$D"
T0="$(date +%s)"
sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
ENC=0; EXT=""
if [ -n "$BACKUP_ENCRYPTION_KEY_FILE" ]; then
  [ -f "$BACKUP_ENCRYPTION_KEY_FILE" ] || { echo "GAGAL: BACKUP_ENCRYPTION_KEY_FILE tidak ditemukan" >&2; exit 2; }
  PERM="$(stat -f %Lp "$BACKUP_ENCRYPTION_KEY_FILE" 2>/dev/null || stat -c %a "$BACKUP_ENCRYPTION_KEY_FILE")"
  case "$PERM" in 400|600) ;; *) echo "GAGAL: izin berkas kunci harus 400/600 (sekarang $PERM)" >&2; exit 2;; esac
  openssl version | grep -q "OpenSSL 3" || { echo "GAGAL: butuh OpenSSL 3.x (bukan LibreSSL) di PATH" >&2; exit 2; }
  ENC=1; EXT=".enc"
else
  echo "PERINGATAN: BACKUP_ENCRYPTION_KEY_FILE tidak diset -> cadangan TIDAK terenkripsi" >&2
fi
encrypt() { if [ "$ENC" = 1 ]; then openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass "file:$BACKUP_ENCRYPTION_KEY_FILE"; else cat; fi; }
echo "== 1/3 dump database"
$DC exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner' > "$D/db.dump.plain"
DB_PLAIN_SHA="$(sha "$D/db.dump.plain")"
REV="$($DC exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "select version_num from alembic_version"' | tr -d '\r')"
COUNTS="$($DC exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "select (select count(*) from reference_media)||\",\"||(select count(*) from partner_documents)"' | tr -d '\r')"
echo "== 2/3 arsip media (/data/media)"
$DC exec -T backend tar -C /data/media -cf - . > "$D/media.tar.plain"
MEDIA_PLAIN_SHA="$(sha "$D/media.tar.plain")"
NFILES="$(tar -tf "$D/media.tar.plain" | grep -vc '/$' || true)"
encrypt < "$D/db.dump.plain" > "$D/db.dump$EXT"
encrypt < "$D/media.tar.plain" > "$D/media.tar$EXT"
rm -f "$D/db.dump.plain" "$D/media.tar.plain"
echo "== 3/3 manifest"
KEYID="${BACKUP_KEY_ID:-}"
cat > "$D/manifest.body" <<JSON
{"format":2,"backup_id":"$ID","created_at":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","alembic_revision":"$REV","db_dump":"db.dump$EXT","db_sha256":"$(sha "$D/db.dump$EXT")","db_plain_sha256":"$DB_PLAIN_SHA","media_tar":"media.tar$EXT","media_sha256":"$(sha "$D/media.tar$EXT")","media_plain_sha256":"$MEDIA_PLAIN_SHA","media_files":$NFILES,"db_media_rows":"$COUNTS","consistency":"db-first-then-media","encryption":{"enabled":$([ $ENC = 1 ] && echo true || echo false),"algorithm":"$([ $ENC = 1 ] && echo aes-256-cbc || echo none)","kdf":"$([ $ENC = 1 ] && echo pbkdf2-sha256 || echo none)","iterations":$([ $ENC = 1 ] && echo 600000 || echo 0),"key_id":"$KEYID"},"destination":{"type":"local","uploaded":false},"duration_seconds":$(( $(date +%s) - T0 ))}
JSON
if [ "$ENC" = 1 ]; then
  MK="$(printf 'silatara-manifest-v1:%s' "$(cat "$BACKUP_ENCRYPTION_KEY_FILE")" | openssl dgst -sha256 -binary | xxd -p -c 64)"
  HM="$(openssl dgst -sha256 -hmac "$MK" "$D/manifest.body" | awk '{print $NF}')"
  sed "s/}\$/,\"manifest_hmac\":\"$HM\"}/" "$D/manifest.body" > "$D/manifest.json"
else
  cp "$D/manifest.body" "$D/manifest.json"
fi
rm -f "$D/manifest.body"
chmod 600 "$D/manifest.json" "$D"/db.dump* "$D"/media.tar*
echo "Cadangan penuh: $D (terenkripsi: $([ $ENC = 1 ] && echo ya || echo TIDAK))"
cat "$D/manifest.json"; echo
