"""Fixture pytest. Tes memakai DATABASE TERPISAH `<POSTGRES_DB>_test` (dibuat & dimigrasi otomatis),
sehingga tidak pernah menyentuh database pengembangan sehari-hari."""

import os

_BASE_DB = os.environ.get("POSTGRES_DB", "silatara")
TEST_DB = _BASE_DB if _BASE_DB.endswith("_test") else f"{_BASE_DB}_test"
os.environ["POSTGRES_DB"] = TEST_DB  # harus sebelum app diimpor (settings di-cache)
os.environ.setdefault("APP_ENV", "development")

import psycopg  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.db import get_db, get_engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    s = get_settings()
    assert s.postgres_db.endswith("_test"), "Tes hanya boleh berjalan pada database *_test"
    admin = psycopg.connect(
        host=s.postgres_host,
        port=s.postgres_port,
        user=s.postgres_user,
        password=s.postgres_password,
        dbname="postgres",
        autocommit=True,
    )
    with admin.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (s.postgres_db,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{s.postgres_db}"')
    admin.close()
    command.upgrade(Config("alembic.ini"), "head")
    yield


@pytest.fixture
def db():
    """Sesi dalam transaksi luar yang selalu di-rollback -> tes tidak mengotori DB dev."""
    conn = get_engine().connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _demo_fixtures_visible(monkeypatch):
    """Fixture tes memakai data contoh (is_demo) — tetapkan eksplisit agar tidak bergantung pada env container dev
    (dev menyembunyikan data contoh dari halaman publik; ADR-0008). Tes yang menguji penyembunyian menimpanya sendiri."""
    monkeypatch.setattr(get_settings(), "expose_demo_data", True)


@pytest.fixture(autouse=True)
def _rate_limit_off_by_default(monkeypatch):
    """Rate limit dimatikan agar tes lain tidak saling menghalangi; tes keamanan menyalakannya sendiri."""
    monkeypatch.setattr(get_settings(), "rate_limit_enabled", False)
