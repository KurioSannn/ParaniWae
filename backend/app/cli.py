"""CLI operasional: python -m app.cli <perintah>."""

import argparse
import getpass
import os
import sys

from sqlalchemy.orm import sessionmaker

from app.core.db import get_engine
from app.seed import seed_demo
from app.services.users import create_admin


def _session():
    return sessionmaker(bind=get_engine(), expire_on_commit=False)()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="app.cli")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("create-admin", help="Buat akun platform_admin (lokal/dev)")
    a.add_argument("--email", required=True)
    a.add_argument("--name", default="Admin Lokal")
    a.add_argument("--role", default="admin", choices=["learner", "instructor", "curator", "admin"])
    sub.add_parser("seed-demo", help="Muat data DEMO (fiktif, bukan data budaya autentik)")
    v = sub.add_parser("verify-media", help="Verifikasi baris DB <-> berkas media (restore-verify)")
    v.add_argument("--root", required=True)
    d = sub.add_parser("doctor", help="Pemeriksaan kesiapan deployment (hanya-baca). Exit 1 bila ada BLOCKER")
    d.add_argument("--target", choices=["current", "production"], default="current")
    d.add_argument("--json", action="store_true")
    d.add_argument("--backups-dir", default=None)
    sub.add_parser("outbox-status", help="Ringkasan outbox")
    o2 = sub.add_parser("outbox-list", help="Daftar baris outbox untuk investigasi (tanpa isi pesan)")
    o2.add_argument("--status", default="dead")
    o3 = sub.add_parser("outbox-requeue", help="Antre ulang satu pesan dead-letter")
    o3.add_argument("--id", required=True)
    o4 = sub.add_parser("outbox-purge", help="Bersihkan outbox lama (DRY-RUN kecuali --execute)")
    o4.add_argument("--sent-days", type=int, default=None)
    o4.add_argument("--dead-days", type=int, default=None)
    o4.add_argument("--execute", action="store_true")
    m1 = sub.add_parser(
        "media-purge", help="Purge media kedaluwarsa retensi (DRY-RUN kecuali --execute) + laporan yatim"
    )
    m1.add_argument("--execute", action="store_true")
    r1 = sub.add_parser(
        "pilot-anonymize", help="Anonimisasi data pilot (DRY-RUN default). Lihat docs/PILOT_PRIVACY_RETENTION.md"
    )
    r1.add_argument("--program")
    r1.add_argument("--cohort")
    r1.add_argument("--completed-before", help="YYYY-MM-DD")
    r1.add_argument("--early", action="store_true", help="di luar jadwal retensi (butuh --reason)")
    r1.add_argument("--reason")
    r1.add_argument("--operator", help="email admin operator (wajib saat --execute)")
    r1.add_argument("--execute", action="store_true")
    r1.add_argument("--confirm", help='teks persis: "ANONIMKAN <N> PROGRAM"')
    r1.add_argument("--backup-manifest", help="manifest.json cadangan terbaru (wajib saat --execute)")
    r1.add_argument("--max-backup-age-hours", type=int, default=24)
    r1.add_argument("--accept-no-backup", action="store_true", help="TIDAK DIREKOMENDASIKAN; dicatat di audit")
    sub.add_parser("retention-report", help="Laporan retensi: eligible / diproses / gagal (tanpa PII)")
    sub.add_parser("worker", help="Worker pemeliharaan: outbox, pemindaian, purge media kedaluwarsa, retensi")
    sub.add_parser("worker-once", help="Satu putaran worker (untuk tes/cron)")
    c1 = sub.add_parser("content-validate", help="Validasi berkas konten riset pencak silat (tanpa DB)")
    c1.add_argument("--repo", default="/repo", help="akar repo yang memuat content/ dan research/")
    c2 = sub.add_parser(
        "content-import", help="Impor konten riset sebagai DRAF (DRY-RUN kecuali --execute; tidak pernah menerbitkan)"
    )
    c2.add_argument("--repo", default="/repo")
    c2.add_argument("--execute", action="store_true")
    c2.add_argument("--operator", help="email admin/kurator yang dicatat sebagai pembuat/peninjau editorial")
    c2.add_argument(
        "--publish",
        action="store_true",
        help="terbitkan sebagai pengetahuan berbasis sumber (tinjauan editorial; ADR-0008)",
    )
    c3 = sub.add_parser("directory-import", help="Impor direktori tempat pencak silat (DRY-RUN kecuali --execute; tidak menghapus)")
    c3.add_argument("--repo", default="/repo")
    c3.add_argument("--execute", action="store_true")
    args = p.parse_args(argv)

    if args.cmd == "content-validate":
        from pathlib import Path

        from app.content_import import load_bundle, validate_bundle

        b = load_bundle(Path(args.repo))
        errs = validate_bundle(b)
        for e in errs:
            print("ERROR", e)
        gen = sum(1 for m in b.movements if m["animation"]["status"] == "generated")
        print(
            f"{len(b.sources)} sumber · {len(b.movements)} gerakan ({gen} beranimasi) · {len(b.courses)} kursus · "
            f"{sum(len(v) for v in b.lessons.values())} pelajaran · {len(errs)} galat"
        )
        return 1 if errs else 0

    with _session() as db:
        if args.cmd == "create-admin":
            password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Kata sandi: ")
            try:
                user = create_admin(db, args.email, password, args.name, args.role)
            except ValueError as exc:
                print(f"Gagal: {exc}", file=sys.stderr)
                return 1
            print(f"Pengguna dibuat: {user.email} ({user.role})")
        elif args.cmd == "seed-demo":
            print(f"Seed DEMO: {seed_demo(db)}")
        elif args.cmd == "verify-media":
            from pathlib import Path

            from app.services.retention import verify_media

            r = verify_media(db, Path(args.root))
            print(
                f"Diperiksa: {r['checked']} berkas | masalah: {len(r['problems'])} | yatim (tidak direferensikan DB): {r['orphans']}"
            )
            for p_ in r["problems"]:
                print("  GAGAL", p_)
            return 1 if r["problems"] else 0
        elif args.cmd in {
            "doctor",
            "outbox-status",
            "outbox-list",
            "outbox-requeue",
            "outbox-purge",
            "media-purge",
            "pilot-anonymize",
            "retention-report",
        }:
            from app.ops_cli import run

            return run(args, db)
        elif args.cmd == "worker-once":
            from app.worker import run_once

            print(run_once(db))
        elif args.cmd == "content-import":
            import json
            from pathlib import Path

            from app.content_import import ContentError, run_import

            try:
                out = run_import(
                    db, Path(args.repo), execute=args.execute, operator_email=args.operator, publish=args.publish
                )
            except ContentError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            print(json.dumps(out, ensure_ascii=False, indent=2))
        elif args.cmd == "directory-import":
            import json
            from pathlib import Path

            from app.directory_import import DirectoryImportError
            from app.directory_import import run as run_dir

            try:
                out = run_dir(db, Path(args.repo), execute=args.execute)
            except DirectoryImportError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            print(json.dumps(out, ensure_ascii=False, indent=2))
    if args.cmd == "worker":
        from app.worker import loop

        loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
