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
    args = p.parse_args(argv)

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
