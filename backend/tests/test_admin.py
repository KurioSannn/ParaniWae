from sqlalchemy import select

from app.models import AuditLog
from tests.factories import login, make_user


def test_admin_endpoints_forbidden_for_other_roles(client, db):
    for role in ("learner", "instructor", "curator"):
        client.cookies.clear()
        login(client, make_user(db, role))
        assert client.get("/api/v1/admin/users").status_code == 403
        assert client.get("/api/v1/admin/audit-logs").status_code == 403


def test_admin_changes_role_revokes_sessions_and_audits(client, db):
    target = make_user(db, "learner")
    login(client, target)
    assert client.get("/api/v1/auth/me").status_code == 200
    target_cookie = dict(client.cookies)
    client.cookies.clear()
    admin = make_user(db, "admin")
    login(client, admin)
    r = client.patch(f"/api/v1/admin/users/{target.id}", json={"role": "curator"})
    assert r.status_code == 200 and r.json()["role"] == "curator"
    assert db.scalar(select(AuditLog).where(AuditLog.action == "user.update",
                                            AuditLog.entity_id == str(target.id)))
    # sesi lama target dicabut -> hak baru berlaku lewat login ulang
    client.cookies.clear()
    client.cookies.update(target_cookie)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_admin_cannot_change_self_and_invalid_role_rejected(client, db):
    admin = make_user(db, "admin")
    login(client, admin)
    assert client.patch(f"/api/v1/admin/users/{admin.id}", json={"role": "learner"}).status_code == 409
    other = make_user(db, "learner")
    assert client.patch(f"/api/v1/admin/users/{other.id}", json={"role": "root"}).status_code == 422
    assert client.patch(f"/api/v1/admin/users/{other.id}", json={"is_admin": True}).status_code == 422


def test_admin_user_list_search_and_pagination(client, db):
    admin = make_user(db, "admin")
    login(client, admin)
    r = client.get("/api/v1/admin/users", params={"q": admin.email, "page_size": 5})
    assert r.status_code == 200 and r.json()["total"] == 1
    assert "password_hash" not in r.text
    assert client.get("/api/v1/admin/audit-logs", params={"entity_type": "user"}).status_code == 200
