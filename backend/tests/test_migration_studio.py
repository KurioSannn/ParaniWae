"""Migrasi Studio (e5a1b7c9d3f2) pada DB scratch terpisah dengan data legacy: mapping status, dokumen v1, trigger immutability."""

import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

from app.core.config import get_settings

BACKEND = Path(__file__).resolve().parent.parent
SCRATCH = "silatara_test_migrasi_studio"


def _conn(db: str):
    s = get_settings()
    return psycopg.connect(host=s.postgres_host, port=s.postgres_port, user=s.postgres_user,
                           password=s.postgres_password, dbname=db, autocommit=True)


def _alembic(*args: str):
    env = {**os.environ, "POSTGRES_DB": SCRATCH}
    r = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]


@pytest.fixture
def scratch():
    with _conn("postgres") as c:
        c.execute(f'DROP DATABASE IF EXISTS "{SCRATCH}"')
        c.execute(f'CREATE DATABASE "{SCRATCH}"')
    yield
    with _conn("postgres") as c:
        c.execute(f'DROP DATABASE IF EXISTS "{SCRATCH}"')


def test_studio_migration_maps_legacy_data_and_installs_guards(scratch):
    _alembic("upgrade", "c7d2e9a1f3b4")
    with _conn(SCRATCH) as c:
        c.execute("insert into users(id,email,password_hash,display_name,role,email_verified_at) values "
                  "('00000000-0000-0000-0000-0000000000a1','a@x.test','x','A','admin',now())")
        c.execute("insert into cultural_traditions(id,slug,name,status,is_demo) values "
                  "('00000000-0000-0000-0000-0000000000b1','t','T','draft',true)")
        c.execute("insert into partners(id,slug,name,partner_type,verification_status,status,is_demo,published_at) values "
                  "('00000000-0000-0000-0000-0000000000c1','p1','P1','school','unverified','published',true,now()),"
                  "('00000000-0000-0000-0000-0000000000c2','p2','P2','school','verified','draft',false,null),"
                  "('00000000-0000-0000-0000-0000000000c3','p3','P3','school','revoked','draft',false,null)")
        c.execute("update partners set public_listing_consent = true where slug = 'p2'")
        c.execute("insert into movements(id,tradition_id,partner_id,slug,name_id,practice_mode,status,is_demo,published_at) values "
                  "('00000000-0000-0000-0000-0000000000d1','00000000-0000-0000-0000-0000000000b1','00000000-0000-0000-0000-0000000000c1','m1','M1','solo_beginner','published',true,now()),"
                  "('00000000-0000-0000-0000-0000000000d2','00000000-0000-0000-0000-0000000000b1','00000000-0000-0000-0000-0000000000c1','m2','M2','not_for_practice','draft',true,null)")
    _alembic("upgrade", "head")
    with _conn(SCRATCH) as c:
        # status mitra: unverified->draft, revoked->suspended; verified non-demo TANPA penyetuju tidak dianggap resmi
        got = dict(c.execute("select slug, verification_status from partners").fetchall())
        assert got == {"p1": "draft", "p2": "pending_verification", "p3": "suspended"}
        assert c.execute("select public_listing_consent from partners where slug='p2'").fetchone()[0] is False
        # setiap gerakan lama -> dokumen versi 1 (legacy_import), gerakan tayang menunjuk versinya
        rows = c.execute("select m.slug, m.published_version_no, m.safety_category, d.status, d.legacy_import, d.version_no "
                         "from movements m join movement_documents d on d.movement_id = m.id order by m.slug").fetchall()
        assert rows == [("m1", 1, "solo_beginner", "published", True, 1), ("m2", None, None, "draft", True, 1)]
        # trigger immutability
        for sql in ("update movement_documents set name_id='X' where status='published'",
                    "update movement_documents set status='draft' where status='published'",
                    "delete from movement_documents where status='published'",
                    "insert into movement_phases(document_id,order_index,name,instruction) "
                    "select id,0,'a','b' from movement_documents where status='published'"):
            with pytest.raises(psycopg.errors.IntegrityConstraintViolation):
                c.execute(sql)
        c.execute("insert into movement_phases(document_id,order_index,name,instruction) select id,0,'a','b' from movement_documents where status='draft'")
        c.execute("update movement_documents set name_id='ok' where status='draft'")
    # turun lalu naik lagi (idempoten pada skema)
    _alembic("downgrade", "c7d2e9a1f3b4")
    _alembic("upgrade", "head")
    _alembic("check")
