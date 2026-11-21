"""Health/readiness, doctor (hanya-baca), log terstruktur tanpa rahasia, header cache privat."""

import json
import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.logging import JsonFormatter, job_id_var, redact
from app.models import AuditLog, JobRun, NotificationOutbox, User
from app.services import jobs, ops
from tests.factories import login, make_user, make_world


def as_(client, user):
    client.cookies.clear()
    client.headers.pop("X-CSRF-Token", None)
    login(client, user)


# ---------- health ----------
def test_liveness_and_readiness_leak_nothing_internal(client):
    live = client.get("/api/v1/health").json()
    assert set(live) == {"status", "service", "version"}  # tanpa env
    ready = client.get("/api/v1/health/ready")
    body = ready.json()
    assert ready.status_code == 200 and set(body) == {"status", "database", "media_storage", "migration_revision"}
    txt = json.dumps(body) + json.dumps(live)
    s = get_settings()
    for secret in (s.postgres_password, s.postgres_host, s.media_dir, s.postgres_user, "/data", "@"):
        assert secret not in txt


def test_readiness_degrades_when_media_unavailable_but_stays_200(client, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "media_dir", str(tmp_path / "tidak-ada"))
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200 and r.json()["status"] == "degraded" and r.json()["media_storage"] == "unavailable"
    assert str(tmp_path) not in r.text  # path lokal tidak bocor


def test_ops_endpoints_require_admin_and_contain_no_secrets(client, db):
    assert client.get("/api/v1/admin/ops/status").status_code == 401
    for role in ("learner", "instructor", "curator"):
        as_(client, make_user(db, role))
        for path in ("/status", "/doctor", "/outbox"):
            assert client.get(f"/api/v1/admin/ops{path}").status_code == 403, (role, path)
    as_(client, make_user(db, "admin"))
    st = client.get("/api/v1/admin/ops/status")
    assert st.status_code == 200
    j = st.json()
    assert {"database", "migration", "media_storage", "scanner", "worker", "outbox", "email", "retention"} <= set(j)
    s = get_settings()
    blob = json.dumps(j, default=str)
    for secret in (s.postgres_password, s.postgres_host, s.media_dir, s.smtp_password or "\0", "/data/media"):
        assert secret not in blob
    assert client.get("/api/v1/admin/ops/doctor", params={"target": "salah"}).status_code == 422
    assert client.get("/api/v1/admin/ops/outbox", params={"status": "bogus"}).status_code == 422


# ---------- doctor ----------
def test_doctor_is_read_only_and_separates_blocker_warning_info(db):
    before = (
        db.scalar(select(func.count()).select_from(AuditLog)),
        db.scalar(select(func.count()).select_from(User)),
        db.scalar(select(func.count()).select_from(NotificationOutbox)),
        db.scalar(select(func.count()).select_from(JobRun)),
    )
    f_cur = ops.doctor(db, target="current", backups_dir="/tidak/ada")
    f_prod = ops.doctor(db, target="production", backups_dir="/tidak/ada")
    after = (
        db.scalar(select(func.count()).select_from(AuditLog)),
        db.scalar(select(func.count()).select_from(User)),
        db.scalar(select(func.count()).select_from(NotificationOutbox)),
        db.scalar(select(func.count()).select_from(JobRun)),
    )
    assert before == after  # tidak mengubah state
    sev = {f.id: f.severity for f in f_prod}
    # gerbang produksi: konfigurasi dev TIDAK lolos
    for blocker in ("scanner", "smtp", "worker", "backup_encryption", "backup_recent", "public_base_url"):
        assert sev.get(blocker) == ops.BLOCKER, blocker
    assert any(f.id.startswith("config.") and f.severity == ops.BLOCKER for f in f_prod)
    # evaluasi saat ini (dev) lebih longgar: tidak ada BLOCKER konfigurasi demo, tetapi masalah tetap terlihat sebagai WARNING/INFO
    sev_cur = {f.id: f.severity for f in f_cur}
    assert sev_cur["scanner"] == ops.WARNING and sev_cur["smtp"] == ops.WARNING and sev_cur["worker"] == ops.WARNING
    assert not [f for f in f_cur if f.severity == ops.BLOCKER and f.id not in {"migration", "database", "media"}]
    assert all(f.severity in {ops.BLOCKER, ops.WARNING, ops.INFO} for f in f_prod)
    summ = ops.summarize(f_prod)
    assert set(summ) == {ops.BLOCKER, ops.WARNING, ops.INFO} and summ[ops.BLOCKER]


def test_doctor_flags_demo_accounts_and_stale_worker_in_production_target(db):
    make_user(db, "learner", **{})  # akun uji @uji.test: bukan demo
    db.add(
        User(email=f"demo-{uuid.uuid4().hex[:6]}@silatara.test", display_name="d", role="learner", password_hash="x")
    )
    db.flush()
    f = {x.id: x for x in ops.doctor(db, target="production", backups_dir="/tidak/ada")}
    assert f["demo_accounts"].severity == ops.BLOCKER
    jobs.heartbeat(db, "worker", "w-test")
    assert {x.id: x.severity for x in ops.doctor(db, target="production", backups_dir="/tidak/ada")}[
        "worker"
    ] == ops.INFO
    row = jobs.last(db, "worker")
    row.heartbeat_at = datetime.now(UTC) - timedelta(hours=1)
    db.flush()
    assert {x.id: x.severity for x in ops.doctor(db, target="production", backups_dir="/tidak/ada")}[
        "worker"
    ] == ops.BLOCKER


def test_doctor_backup_checks(db, tmp_path, monkeypatch):
    d = tmp_path / "full_x"
    d.mkdir()
    (d / "manifest.json").write_text(
        json.dumps(
            {
                "created_at": (datetime.now(UTC) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "encryption": {"enabled": False},
                "destination": {"uploaded": False},
            }
        )
    )
    sev = {f.id: f.severity for f in ops.doctor(db, target="production", backups_dir=str(tmp_path))}
    assert (
        sev["backup_recent"] == ops.INFO
        and sev["backup_plaintext"] == ops.BLOCKER
        and sev["backup_offsite"] == ops.WARNING
    )
    key = tmp_path / "k"
    key.write_text("x")
    key.chmod(0o644)
    monkeypatch.setenv("BACKUP_ENCRYPTION_KEY_FILE", str(key))
    assert {f.id: f.severity for f in ops.doctor(db, target="production", backups_dir=str(tmp_path))}[
        "backup_encryption"
    ] == ops.BLOCKER  # izin longgar
    key.chmod(0o600)
    assert {f.id: f.severity for f in ops.doctor(db, target="production", backups_dir=str(tmp_path))}[
        "backup_encryption"
    ] == ops.INFO


def test_doctor_reports_outbox_dead_letters_and_backlog(db):
    db.add(
        NotificationOutbox(
            kind="k", to_email="a@x.test", subject="s", body="b", status="dead", dead_at=datetime.now(UTC)
        )
    )
    db.add(
        NotificationOutbox(
            kind="k",
            to_email="b@x.test",
            subject="s",
            body="b",
            status="pending",
            created_at=datetime.now(UTC) - timedelta(hours=3),
        )
    )
    db.flush()
    ids = {f.id for f in ops.doctor(db, target="current", backups_dir="/tidak/ada")}
    assert {"outbox_dead", "outbox_backlog"} <= ids


# ---------- log: terstruktur & tanpa rahasia ----------
def test_redaction_masks_tokens_passwords_cookies_and_emails():
    t = (
        "login ok token=abc123 password=hunter2 Cookie: silatara_session=XYZ budi@contoh.id Authorization: Bearer abc.def "
        + "A" * 43
    )
    r = redact(t)
    for leak in ("abc123", "hunter2", "XYZ", "budi@contoh.id", "abc.def", "A" * 43):
        assert leak not in r, leak


def test_json_formatter_has_correlation_ids_and_redacts_extras():
    rec = logging.LogRecord("x", logging.INFO, __file__, 1, "pesan token=RAHASIA", (), None)
    rec.password, rec.landmarks, rec.step = "p", [1, 2], "outbox"
    tok = job_id_var.set("job-1")
    try:
        doc = json.loads(JsonFormatter().format(rec))
    finally:
        job_id_var.reset(tok)
    assert doc["job_id"] == "job-1" and doc["step"] == "outbox" and "RAHASIA" not in json.dumps(doc)
    assert doc["password"] == "[REDACTED]" and doc["landmarks"] == "[REDACTED]"


def test_access_log_has_no_query_string_tokens_or_credentials_and_correlates_request_id(client, db, caplog):
    secret_token = "TOKEN-RAHASIA-" + "z" * 30
    pwd = "sandi-rahasia-12345"
    u = make_user(db, "learner")
    with caplog.at_level(logging.INFO, logger="silatara.access"):
        r1 = client.get("/api/v1/pilot/invitations/preview", params={"token": secret_token})
        r2 = client.post("/api/v1/auth/login", json={"email": u.email, "password": pwd})
    assert r1.status_code == 404 and r2.status_code == 401
    text = "\n".join(JsonFormatter().format(rec) for rec in caplog.records)
    assert secret_token not in text and pwd not in text and u.email not in text and "silatara_session" not in text
    recs = [rec for rec in caplog.records if rec.name == "silatara.access"]
    assert recs and all(hasattr(rec, "status") and hasattr(rec, "duration_ms") for rec in recs)
    assert {rec.request_id for rec in recs} >= {r1.headers["x-request-id"], r2.headers["x-request-id"]}
    assert all("?" not in rec.path for rec in recs)  # path tanpa query


def test_access_log_uses_route_template_not_raw_ids(client, db, caplog):
    u = make_user(db, "admin")
    as_(client, u)
    with caplog.at_level(logging.INFO, logger="silatara.access"):
        client.get(f"/api/v1/pilot/programs/{uuid.uuid4()}")
    paths = [rec.path for rec in caplog.records if rec.name == "silatara.access"]
    assert paths and all("-" not in p.split("/")[-1] or p.endswith("}") for p in paths)  # id mentah tidak tercatat


# ---------- cache ----------
def test_authenticated_and_private_paths_are_not_cacheable_and_all_api_varies_on_cookie(client, db):
    w = make_world(db, "published")
    pub = client.get(f"/api/v1/courses/{w['course'].slug}")
    assert pub.status_code == 200 and "Cookie" in pub.headers["vary"]
    assert "no-store" not in pub.headers.get(
        "cache-control", ""
    )  # katalog publik anonim boleh dicache publik oleh infrastruktur
    as_(client, make_user(db, "learner"))
    for path in (
        "/api/v1/auth/me",
        f"/api/v1/courses/{w['course'].slug}",
        "/api/v1/me/progress",
        "/api/v1/pilot/me/portal",
    ):
        r = client.get(path)
        assert r.headers["cache-control"] == "private, no-store", path
    client.cookies.clear()
    assert (
        client.get("/api/v1/me/progress").headers["cache-control"] == "private, no-store"
    )  # path privat walau anonim (401)
