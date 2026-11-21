"""Tes hardening autentikasi: verifikasi email, reset sandi, anti-enumerasi, rate limit, IP klien,
cookie aman, konfigurasi produksi, dan penjaga seed demo."""

import re
from datetime import timedelta

import pytest
from sqlalchemy import literal_column, select, text
from starlette.requests import Request

from app.core.config import Settings, get_settings
from app.core.netinfo import client_ip
from app.models import AuthToken, OutboxEmail, User
from app.models import Session as SessionRow
from app.seed import seed_demo
from app.services.auth import now
from tests.factories import PASSWORD, login, make_user, uid


def mails(db, to):
    # Dalam satu transaksi tes, now() identik untuk semua baris -> created_at saja bukan urutan yang stabil.
    # ctid (posisi sisip fisik) menjadi tie-breaker deterministik. (Di produksi tiap request punya transaksi sendiri.)
    return list(db.scalars(select(OutboxEmail).where(OutboxEmail.to_email == to)
                           .order_by(OutboxEmail.created_at, literal_column("ctid"))))


def token_in(mail) -> str:
    return re.search(r"token=([\w-]+)", mail.body).group(1)


def register(client, email=None, password=PASSWORD):
    email = email or f"r-{uid()}@uji.test"
    return client.post("/api/v1/auth/register",
                       json={"email": email, "password": password, "display_name": "Uji"}), email


# ---------- verifikasi email ----------
def test_email_verification_flow(client, db):
    r, email = register(client)
    assert r.status_code == 202
    (m,) = mails(db, email)
    raw = token_in(m)
    # login sebelum verifikasi ditolak (kredensial benar tetapi email belum diverifikasi)
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 403 and r.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"
    assert client.post("/api/v1/auth/verify-email", json={"token": raw}).json() == {"status": "verified"}
    assert client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200
    # sekali pakai + hash tersimpan, bukan token mentah
    again = client.post("/api/v1/auth/verify-email", json={"token": raw})
    assert again.status_code == 400 and again.json()["error"]["code"] == "INVALID_TOKEN"
    assert db.scalar(select(AuthToken).where(AuthToken.token_hash == raw)) is None


def test_registration_is_not_enumerable(client, db):
    existing = make_user(db)
    r1, new_email = register(client)
    r2, _ = register(client, email=existing.email)
    assert r1.status_code == r2.status_code == 202
    assert r1.json() == r2.json()  # badan respons identik
    assert "set-cookie" not in r1.headers and "set-cookie" not in r2.headers
    # pemilik email yang sudah ada diberi tahu lewat email, bukan lewat respons
    (notice,) = mails(db, existing.email)
    assert "sudah ada" in notice.body
    assert db.scalar(select(User).where(User.email == existing.email)).id == existing.id


def test_login_and_reset_messages_do_not_reveal_accounts(client, db):
    u = make_user(db)
    a = client.post("/api/v1/auth/password-reset/request", json={"email": u.email})
    b = client.post("/api/v1/auth/password-reset/request", json={"email": f"tidak-ada-{uid()}@uji.test"})
    assert a.status_code == b.status_code == 202 and a.json() == b.json()
    assert len(mails(db, u.email)) == 1  # hanya akun nyata yang menerima email
    assert db.scalar(select(OutboxEmail).where(OutboxEmail.to_email.like("tidak-ada-%"))) is None


def test_resend_verification_generic_and_only_for_unverified(client, db):
    r, email = register(client)
    first = mails(db, email)[0]
    ok = client.post("/api/v1/auth/resend-verification", json={"email": email})
    unknown = client.post("/api/v1/auth/resend-verification", json={"email": f"x-{uid()}@uji.test"})
    assert ok.status_code == unknown.status_code == 202 and ok.json() == unknown.json()
    second = mails(db, email)[-1]
    assert second.id != first.id
    # token lama dibatalkan saat token baru diterbitkan
    assert client.post("/api/v1/auth/verify-email", json={"token": token_in(first)}).status_code == 400
    assert client.post("/api/v1/auth/verify-email", json={"token": token_in(second)}).status_code == 200


# ---------- reset sandi ----------
def _reset_token(client, db, user):
    client.post("/api/v1/auth/password-reset/request", json={"email": user.email})
    return token_in(mails(db, user.email)[-1])


def test_password_reset_lifecycle(client, db):
    u = make_user(db)
    login(client, u)  # sesi lama
    old = dict(client.cookies)
    client.cookies.clear()
    raw = _reset_token(client, db, u)
    stored = db.scalar(select(AuthToken).where(AuthToken.user_id == u.id, AuthToken.kind == "reset_password"))
    assert stored.token_hash != raw and len(raw) >= 40 and len(stored.token_hash) == 64
    r = client.post("/api/v1/auth/password-reset/confirm", json={"token": raw, "new_password": "sandi-baru-yang-panjang"})
    assert r.status_code == 200
    # sesi lama dicabut; sandi lama tidak berlaku; sandi baru berlaku
    client.cookies.update(old)
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.clear()
    assert client.post("/api/v1/auth/login", json={"email": u.email, "password": PASSWORD}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": u.email, "password": "sandi-baru-yang-panjang"}).status_code == 200
    # sekali pakai
    r = client.post("/api/v1/auth/password-reset/confirm", json={"token": raw, "new_password": "sandi-lain-yang-panjang1"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "INVALID_TOKEN"


def test_reset_token_expiry_wrong_token_kind_mismatch_and_reissue(client, db):
    u = make_user(db)
    raw = _reset_token(client, db, u)
    row = db.scalar(select(AuthToken).where(AuthToken.user_id == u.id))
    row.expires_at = now() - timedelta(seconds=1)
    db.flush()
    pw = "sandi-baru-yang-panjang"
    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": raw, "new_password": pw}).status_code == 400
    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": "x" * 43, "new_password": pw}).status_code == 400
    # permintaan baru membatalkan token lama
    t1 = _reset_token(client, db, u)
    t2 = _reset_token(client, db, u)
    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": t1, "new_password": pw}).status_code == 400
    # token verifikasi tidak dapat dipakai sebagai token reset
    r, email = register(client)
    vtoken = token_in(mails(db, email)[0])
    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": vtoken, "new_password": pw}).status_code == 400
    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": t2, "new_password": pw}).status_code == 200


def test_reset_rejects_weak_new_password_and_unlocks_account(client, db):
    u = make_user(db, failed_logins=0)
    u.locked_until = now() + timedelta(minutes=10)
    db.flush()
    raw = _reset_token(client, db, u)
    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": raw, "new_password": "pendek"}).status_code == 422
    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": raw, "new_password": "sandi-baru-yang-panjang"}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": u.email, "password": "sandi-baru-yang-panjang"}).status_code == 200


def test_email_features_unavailable_when_mail_not_configured(client, db, monkeypatch):
    monkeypatch.setattr(get_settings(), "mail_provider", "none")
    r, _ = register(client)
    assert r.status_code == 503 and r.json()["error"]["code"] == "FEATURE_UNAVAILABLE"
    assert client.post("/api/v1/auth/password-reset/request", json={"email": "a@b.id"}).status_code == 503


def test_dev_sink_refused_outside_development(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "app_env", "staging")  # mail_provider tetap dev_sink
    assert get_settings().mail_configured is False
    r, _ = register(client)
    assert r.status_code == 503
    assert client.get("/api/v1/dev/mailbox").status_code == 404


# ---------- rate limit ----------
def test_login_rate_limit_per_ip_with_retry_after(client, db, monkeypatch):
    monkeypatch.setattr("app.services.ratelimit.time.time", lambda: 1_000_000.5)  # jam beku: tanpa pergantian jendela di tengah tes
    s = get_settings()
    monkeypatch.setattr(s, "rate_limit_enabled", True)
    monkeypatch.setattr(s, "rl_login_ip", (3, 600))
    u = make_user(db)
    for _ in range(3):
        assert client.post("/api/v1/auth/login", json={"email": f"x{uid()}@uji.test", "password": "salah"}).status_code == 401
    r = client.post("/api/v1/auth/login", json={"email": u.email, "password": PASSWORD})
    assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0
    assert r.json()["error"]["code"] == "RATE_LIMITED"


def test_register_and_reset_rate_limits(client, db, monkeypatch):
    monkeypatch.setattr("app.services.ratelimit.time.time", lambda: 1_000_000.5)
    s = get_settings()
    monkeypatch.setattr(s, "rate_limit_enabled", True)
    monkeypatch.setattr(s, "rl_register_ip", (2, 3600))
    monkeypatch.setattr(s, "rl_reset_email", (2, 3600))
    assert register(client)[0].status_code == 202
    assert register(client)[0].status_code == 202
    assert register(client)[0].status_code == 429
    email = f"rl-{uid()}@uji.test"
    for _ in range(2):
        assert client.post("/api/v1/auth/password-reset/request", json={"email": email}).status_code == 202
    assert client.post("/api/v1/auth/password-reset/request", json={"email": email}).status_code == 429
    # email lain tidak terpengaruh batas per-email
    assert client.post("/api/v1/auth/password-reset/request", json={"email": f"lain-{uid()}@uji.test"}).status_code == 202


def test_rate_limit_keys_contain_no_plain_pii(client, db, monkeypatch):
    monkeypatch.setattr("app.services.ratelimit.time.time", lambda: 1_000_000.5)
    monkeypatch.setattr(get_settings(), "rate_limit_enabled", True)
    email = f"pii-{uid()}@uji.test"
    client.post("/api/v1/auth/password-reset/request", json={"email": email})
    keys = [r[0] for r in db.execute(text("select key from rate_limits"))]
    assert keys and not any("pii-" in k or "@" in k for k in keys)


# ---------- IP klien / proxy tepercaya ----------
def _req(peer, xff=None):
    headers = [(b"x-forwarded-for", xff.encode())] if xff else []
    return Request({"type": "http", "headers": headers, "client": (peer, 1234), "method": "GET", "path": "/"})


def test_client_ip_ignores_xff_from_untrusted_peer(monkeypatch):
    monkeypatch.setattr(get_settings(), "trusted_proxy_cidrs", "10.0.0.0/8")
    assert client_ip(_req("203.0.113.9", "1.2.3.4")) == "203.0.113.9"
    assert client_ip(_req("203.0.113.9")) == "203.0.113.9"


def test_client_ip_uses_rightmost_hop_from_trusted_proxy(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "trusted_proxy_cidrs", "10.0.0.0/8")
    monkeypatch.setattr(s, "trusted_proxy_hops", 1)
    # klien memalsukan entri kiri; proxy kita menambahkan IP asli di kanan
    assert client_ip(_req("10.1.2.3", "6.6.6.6, 198.51.100.7")) == "198.51.100.7"
    monkeypatch.setattr(s, "trusted_proxy_hops", 2)
    assert client_ip(_req("10.1.2.3", "6.6.6.6, 198.51.100.7, 10.9.9.9")) == "198.51.100.7"
    # rantai lebih pendek dari hop, atau bukan IP -> jatuh ke peer
    assert client_ip(_req("10.1.2.3", "198.51.100.7")) == "10.1.2.3"
    monkeypatch.setattr(s, "trusted_proxy_hops", 1)
    assert client_ip(_req("10.1.2.3", "bukan-ip")) == "10.1.2.3"


def test_no_trusted_proxies_by_default():
    assert Settings().trusted_proxy_cidrs == ""


# ---------- cookie, sesi, konfigurasi ----------
def test_cookies_are_secure_outside_development(client, db, monkeypatch):
    u = make_user(db)
    monkeypatch.setattr(get_settings(), "app_env", "staging")
    r = client.post("/api/v1/auth/login", json={"email": u.email, "password": PASSWORD})
    assert all("Secure" in c for c in r.headers.get_list("set-cookie"))


def test_sessions_revoked_when_user_suspended_or_password_reset(client, db):
    u = make_user(db)
    login(client, u)
    assert db.scalar(select(SessionRow).where(SessionRow.user_id == u.id, SessionRow.revoked_at.is_(None)))
    u.status = "suspended"
    db.flush()
    assert client.get("/api/v1/auth/me").status_code == 401


def test_production_config_fails_closed():
    bad = Settings(app_env="production", expose_demo_data=True)  # isolasi dari env container dev
    with pytest.raises(RuntimeError) as e:
        bad.validate_runtime()
    msg = str(e.value)
    assert "EXPOSE_DEMO_DATA" in msg and "POSTGRES_PASSWORD" in msg and "dev_sink" in msg and "SCAN_PROVIDER" in msg
    good = Settings(app_env="production", expose_demo_data=False, postgres_password="x" * 24,
                    mail_provider="smtp", smtp_host="smtp.example.test", cookie_secure=True, scan_provider="clamav",
                    demo_user_password=None, seed_demo_data=False, demo_login_enabled=False)  # isolasi dari env container dev
    good.validate_runtime()  # tidak melempar
    assert good.mail_configured and good.use_secure_cookies


def test_demo_seed_refused_outside_development(db, monkeypatch):
    monkeypatch.setattr(get_settings(), "app_env", "production")
    monkeypatch.delenv("ALLOW_DEMO_CONTENT_SEED", raising=False)
    with pytest.raises(RuntimeError):
        seed_demo(db)


def test_demo_users_not_created_in_staging_even_with_content_seed(db, monkeypatch):
    monkeypatch.setattr(get_settings(), "app_env", "staging")
    monkeypatch.setenv("ALLOW_DEMO_CONTENT_SEED", "true")
    before = db.scalar(select(User.id).where(User.email == "demo-admin@silatara.test"))
    seed_demo(db)
    after = db.scalar(select(User.id).where(User.email == "demo-admin@silatara.test"))
    assert before == after  # tidak ada akun demo baru di luar development


def test_production_refuses_demo_credentials_and_demo_seed():
    base = dict(app_env="production", expose_demo_data=False, postgres_password="x" * 24,
                mail_provider="smtp", smtp_host="smtp.example.test", cookie_secure=True, scan_provider="clamav")
    clean = dict(demo_user_password=None, seed_demo_data=False, demo_login_enabled=False)
    for extra in ({"demo_user_password": "demo-sandi-12345", "seed_demo_data": False, "demo_login_enabled": False},
                  {"demo_user_password": None, "seed_demo_data": True, "demo_login_enabled": False},
                  {"demo_user_password": None, "seed_demo_data": False, "demo_login_enabled": True}):
        with pytest.raises(RuntimeError) as e:
            Settings(**base, **extra).validate_runtime()
        assert "DEMO" in str(e.value).upper()
    Settings(**base, **clean).validate_runtime()  # tanpa kredensial/seed demo -> aman


def test_api_has_no_video_or_frame_upload_surface(client):
    """Privasi: kontrak API tidak boleh menerima unggahan media/frame (raw video tidak pernah dikirim ke backend)."""
    spec = client.get("/openapi.json").json()
    # Satu-satunya unggahan: materi referensi dari instruktur & dokumen persetujuan mitra (Studio, perlu peran
    # instruktur/kurator/admin + deklarasi hak). Tidak ada endpoint latihan/pelajar yang menerima media, frame, atau landmark.
    allowed = {("POST", "/api/v1/studio/movements/{movement_id}/media"),
               ("POST", "/api/v1/studio/partners/{partner_id}/documents")}
    seen = set()
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            content = (op.get("requestBody") or {}).get("content", {})
            if any(ct.startswith(("multipart/", "video/", "image/", "application/octet-stream")) for ct in content):
                seen.add((method.upper(), path))
                assert path.startswith("/api/v1/studio/"), f"{method.upper()} {path} menerima media: {list(content)}"
                continue
            low = f"{path} {op.get('summary', '')}".lower()
            assert not any(w in low for w in ("upload", "frame", "landmark", "biometric")), f"{path} mencurigakan"
            if "practice" in path:
                assert not content.keys() - {"application/json"}, path
    assert seen == allowed
