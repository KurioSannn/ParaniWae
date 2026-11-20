#!/bin/sh
# Mengidentifikasi data uji yang tertinggal di DB DEV (hasil `make e2e` lama).
#   list  : hanya menampilkan (aman, read-only)
#   clean : backup dulu, tampilkan, minta konfirmasi eksplisit, lalu hapus
# Pola data uji: akun *@uji.test (e2e-*, e2e2-*, rst-*, ui-*, lrn-*, rbac-*, pw-*) dan konten "E2E ..."/"Tradisi Browser ...".
set -e
cd "$(dirname "$0")/.."
Q() { docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -tA -U "$POSTGRES_USER" -d "$POSTGRES_DB"' ; }
list() {
  echo "== Akun uji (*@uji.test) di DB dev"; echo "SELECT email, role, created_at::date FROM users WHERE email LIKE '%@uji.test' ORDER BY created_at;" | Q
  echo "== Konten uji"; echo "SELECT 'traditions', slug, status FROM cultural_traditions WHERE name LIKE 'E2E %' OR name LIKE 'Tradisi Browser %';" | Q
  echo "== Baris audit terkait akun/konten uji"
  echo "SELECT count(*) FROM audit_logs WHERE actor_user_id IN (SELECT id FROM users WHERE email LIKE '%@uji.test') OR entity_id IN (SELECT id::text FROM cultural_traditions WHERE name LIKE 'E2E %' OR name LIKE 'Tradisi Browser %') OR entity_id IN (SELECT id::text FROM users WHERE email LIKE '%@uji.test');" | Q
  echo "== TIDAK dihapus: akun demo-*@silatara.test dan seed [DEMO]"
}
case "${1:-list}" in
  list) list ;;
  clean)
    list
    ./scripts/db-backup.sh
    printf "Hapus data uji di atas dari DB DEV? Ketik 'HAPUS DATA UJI': "; read -r a
    [ "$a" = "HAPUS DATA UJI" ] || { echo "Dibatalkan. Tidak ada yang dihapus."; exit 1; }
    Q <<'SQL'
BEGIN;
DELETE FROM audit_logs WHERE actor_user_id IN (SELECT id FROM users WHERE email LIKE '%@uji.test')
   OR entity_id IN (SELECT id::text FROM users WHERE email LIKE '%@uji.test')
   OR entity_id IN (SELECT id::text FROM cultural_traditions WHERE name LIKE 'E2E %' OR name LIKE 'Tradisi Browser %');
UPDATE cultural_traditions SET approved_by_user_id = NULL WHERE approved_by_user_id IN (SELECT id FROM users WHERE email LIKE '%@uji.test');
DELETE FROM cultural_traditions WHERE name LIKE 'E2E %' OR name LIKE 'Tradisi Browser %';
DELETE FROM users WHERE email LIKE '%@uji.test';
COMMIT;
SQL
    echo "Selesai. Cadangan sebelum penghapusan ada di ./backups." ;;
  *) echo "Pakai: $0 [list|clean]"; exit 2 ;;
esac
