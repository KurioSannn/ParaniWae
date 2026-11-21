"""Login demo sekali klik: hanya aktif bila diizinkan & bukan produksi; hanya akun demo yang terdaftar."""

import pytest
from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.models import AuditLog, User


@pytest.fixture
def demo_on(monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_login_enabled", True)
    monkeypatch.setattr(get_settings(), "expose_demo_data", True)


def ensure_demo_user(db, email="demo-pelajar@silatara.test", role="learner"):
    u = db.scalar(select(User).where(User.email == email))
    if u is None:
        u = User(email=email, display_name="[DEMO] Uji", role=role, password_hash=hash_password("x" * 16))
        db.add(u)
        db.flush()
    return u


def test_disabled_by_default_returns_404(client, db, monkeypatch):
    assert Settings.model_fields["demo_login_enabled"].default is False  # default kode: mati
    monkeypatch.setattr(get_settings(), "demo_login_enabled", False)
    assert client.get("/api/v1/auth/demo-accounts").status_code == 404
    assert client.post("/api/v1/auth/demo-login", json={"key": "pelajar"}).status_code == 404


def test_lists_only_seeded_accounts_without_secrets(client, db, demo_on):
    ensure_demo_user(db)
    r = client.get("/api/v1/auth/demo-accounts")
    assert r.status_code == 200
    keys = {a["key"] for a in r.json()}
    assert "pelajar" in keys
    assert all(set(a) == {"key", "label", "description", "email"} for a in r.json())  # tidak ada kata sandi


def test_one_click_login_creates_session_and_audit(client, db, demo_on):
    u = ensure_demo_user(db, "demo-kurator@silatara.test", "curator")
    r = client.post("/api/v1/auth/demo-login", json={"key": "kurator"})
    assert r.status_code == 200 and r.json()["user"]["email"] == u.email
    assert get_settings().session_cookie_name in r.cookies
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200 and me.json()["user"]["role"] == "curator"
    assert db.scalar(select(AuditLog).where(AuditLog.action == "user.demo_login", AuditLog.entity_id == str(u.id)))


def test_unknown_key_or_non_demo_account_rejected(client, db, demo_on):
    assert client.post("/api/v1/auth/demo-login", json={"key": "superuser"}).status_code == 404
    assert client.post("/api/v1/auth/demo-login", json={"key": "pelajar", "email": "x@y.z"}).status_code == 422


def test_never_active_in_production():
    s = Settings(app_env="production", demo_login_enabled=True, expose_demo_data=True)
    assert s.demo_login_active is False
    assert any("DEMO_LOGIN_ENABLED" in p for p in s.production_problems())
