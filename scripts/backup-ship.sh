#!/bin/sh
# Kirim cadangan ke tujuan OFF-SITE (S3-compatible). BELUM DIVERIFIKASI end-to-end di repo ini: tidak ada kredensial/bucket/CLI
# `aws` di lingkungan pengembangan. Skrip ini gagal keras bila prasyarat tidak ada dan TIDAK PERNAH menandai manifest "uploaded"
# sebelum membaca balik objek dan mencocokkan sha256.
#   Env (di luar repo): BACKUP_DESTINATION=s3://bucket/prefix  BACKUP_S3_ENDPOINT=https://...  (+ kredensial AWS_* / profil)
set -e
D="${1:?pakai: backup-ship.sh <direktori cadangan>}"
[ -n "$BACKUP_DESTINATION" ] || { echo "GAGAL: BACKUP_DESTINATION kosong"; exit 2; }
command -v aws >/dev/null || { echo "GAGAL: CLI 'aws' tidak terpasang — pengiriman off-site TIDAK dilakukan"; exit 3; }
EP=""; [ -n "$BACKUP_S3_ENDPOINT" ] && EP="--endpoint-url $BACKUP_S3_ENDPOINT"
DEST="$BACKUP_DESTINATION/$(basename "$D")"
aws $EP s3 cp "$D/" "$DEST/" --recursive --only-show-errors
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
aws $EP s3 cp "$DEST/manifest.json" "$TMP/manifest.json" --only-show-errors
cmp -s "$D/manifest.json" "$TMP/manifest.json" || { echo "GAGAL: manifest di tujuan berbeda"; exit 1; }
for f in $(cd "$D" && ls db.dump* media.tar*); do
  aws $EP s3 cp "$DEST/$f" "$TMP/$f" --only-show-errors
  [ "$(shasum -a 256 "$TMP/$f" | cut -d' ' -f1)" = "$(shasum -a 256 "$D/$f" | cut -d' ' -f1)" ] || { echo "GAGAL: sha256 $f di tujuan berbeda"; exit 1; }
done
echo "Terkirim dan terverifikasi (baca-balik sha256): $DEST"
