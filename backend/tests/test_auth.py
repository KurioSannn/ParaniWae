from datetime import timedelta

import pytest
from sqlalchemy import select, text

from app.models import Session as SessionRow
from app.services.auth import now
from app.services.users import create_admin
from tests.factories import PASSWORD, login, make_user, uid


def _register(client, **over):
    body = {"email": f"baru-{uid()}@uji.test", "password": PASSWORD, "display_name": "Pengguna Baru"}
    body.update(over)
    return client.post("/api/v1/auth/register", json=body), body


def test_register_returns_generic_202_without_session_and_creates_unverified_learner(client, db):
    r, body = _register(client)
    assert r.status_code == 202 and r.json()["status"] == "check_email"
    assert not r.headers.get_list("set-cookie")  # tidak ada sesi sebelum email diverifikasi
    row = db.execute(text("select role, email_verified_at, password_hash from users where email=:e"),
                     {"e": body["email"]}).one()
    assert row.role == "learner" and row.email_verified_at is None
    assert row.password_hash.startswith("$argon2id$") and body["password"] not in r.text


def test_register_cannot_choose_role_and_validates_input(client):
    r, _ = _register(client, role="admin")
    assert r.status_code == 422
    r, body = _register(client, password="pendek")
    assert r.status_code == 422 and "pendek" not in r.text
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert r.json()["error"]["request_id"]
    r, _ = _register(client, email="bukan-email")
    assert r.status_code == 422


def test_login_sets_httponly_cookie_for_verified_user(client, db):
    u = make_user(db)
    r = login(client, u)
    cookies = r.headers.get_list("set-cookie")
    sess = next(c for c in cookies if c.startswith("silatara_session="))
    assert "HttpOnly" in sess and "SameSite=lax" in sess and "Path=/" in sess
    assert "HttpOnly" not in next(c for c in cookies if c.startswith("silatara_csrf="))
    token = client.cookies.get("silatara_session")
    assert token and db.scalar(select(SessionRow).where(SessionRow.token_hash == token)) is None


def test_login_wrong_password_and_unknown_email_look_identical(client, db):
    u = make_user(db)
    a = client.post("/api/v1/auth/login", json={"email": u.email, "password": "salah-salah-123"})
    b = client.post("/api/v1/auth/login", json={"email": "tidak-ada@uji.test", "password": "x"})
    assert a.status_code == b.status_code == 401
    assert a.json()["error"]["message"] == b.json()["error"]["message"]


def test_lockout_after_repeated_failures(client, db):
    u = make_user(db)
    for _ in range(5):
        assert client.post("/api/v1/auth/login",
                           json={"email": u.email, "password": "salah-salah-123"}).status_code == 401
    r = client.post("/api/v1/auth/login", json={"email": u.email, "password": PASSWORD})
    assert r.status_code == 429 and r.json()["error"]["code"] == "ACCOUNT_LOCKED"


def test_me_requires_login_then_logout_revokes_session(client, db):
    assert client.get("/api/v1/auth/me").status_code == 401
    u = make_user(db)
    login(client, u)
    assert client.get("/api/v1/auth/me").json()["user"]["email"] == u.email
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_mutation_requires_csrf_header(client, db):
    u = make_user(db)
    login(client, u)
    del client.headers["X-CSRF-Token"]
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 403 and r.json()["error"]["code"] == "CSRF_FAILED"
    r = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": "salah"})
    assert r.status_code == 403
    assert client.get("/api/v1/auth/me").status_code == 200  # sesi masih hidup


@pytest.mark.parametrize("field,delta", [("expires_at", timedelta(seconds=-1)),
                                         ("last_seen_at", timedelta(hours=-25))])
def test_expired_sessions_rejected(client, db, field, delta):
    u = make_user(db)
    login(client, u)
    row = db.scalar(select(SessionRow).where(SessionRow.user_id == u.id))
    setattr(row, field, now() + delta if field == "expires_at" else now() + delta)
    db.flush()
    assert client.get("/api/v1/auth/me").status_code == 401


def test_suspended_user_cannot_use_existing_session(client, db):
    u = make_user(db)
    login(client, u)
    u.status = "suspended"
    db.flush()
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.post("/api/v1/auth/login",
                       json={"email": u.email, "password": PASSWORD}).status_code == 401


def test_cli_created_admin_can_log_in(client, db):
    """Kompatibilitas Argon2 antara CLI create-admin dan endpoint login."""
    email = f"cli-{uid()}@uji.test"
    create_admin(db, email, "kata-sandi-cli-12345", "Admin CLI")
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "kata-sandi-cli-12345"})
    assert r.status_code == 200 and r.json()["user"]["role"] == "admin"


def test_each_login_creates_new_session(client, db):
    u = make_user(db)
    login(client, u)
    first = client.cookies.get("silatara_session")
    login(client, u)
    assert client.cookies.get("silatara_session") != first
