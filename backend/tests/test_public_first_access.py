"""Regresi public-first (ADR-0008): pengetahuan umum terbaca anonim; konten privat & kewenangan tulis tetap terlindungi."""

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models import CulturalTradition, Movement, Partner
from tests.factories import login, make_movement, make_user, make_world


@pytest.fixture
def hidden_demo(monkeypatch):
    """Seperti lingkungan publik: data contoh disembunyikan."""
    monkeypatch.setattr(get_settings(), "expose_demo_data", False)


def _real(world):
    """Jadikan dunia uji non-demo (konten nyata) dengan jejak penyetuju."""
    for k in ("tradition", "partner", "course", *[]):
        world[k].is_demo = False
    for le in world["lessons"]:
        le.is_demo = False


def source_backed_world(db, editor):
    w = make_world(db)
    w["partner"].is_demo = False
    w["partner"].status, w["partner"].verification_status = "draft", "draft"  # partner redaksi: TIDAK diverifikasi
    for obj in (w["tradition"], w["course"], *w["lessons"]):
        obj.is_demo = False
        obj.content_basis = "source_backed"
        obj.approved_by_user_id, obj.approved_at = editor.id, obj.published_at
    mv = make_movement(
        db,
        w,
        is_demo=False,
        content_basis="source_backed",
        approved_by_user_id=editor.id,
        approved_at=w["course"].published_at,
    )
    db.flush()
    return w, mv


def test_anonymous_reads_source_backed_knowledge_without_verified_partner(client, db, hidden_demo):
    editor = make_user(db, role="curator")
    w, mv = source_backed_world(db, editor)
    c, le = w["course"], w["lessons"][0]
    # katalog & detail
    assert any(x["id"] == str(mv.id) for x in client.get("/api/v1/movements?page_size=100").json()["items"])
    assert client.get(f"/api/v1/movements/{mv.id}").status_code == 200
    assert any(x["slug"] == c.slug for x in client.get("/api/v1/courses?page_size=100").json()["items"])
    assert client.get(f"/api/v1/courses/{c.slug}").status_code == 200
    # pelajaran terbuka tanpa login
    r = client.get(f"/api/v1/courses/{c.slug}/lessons/{le.slug}")
    assert r.status_code == 200 and r.json()["enrolled"] is False and r.json()["lesson_status"] is None
    assert client.get(f"/api/v1/traditions/{w['tradition'].slug}").status_code == 200


def test_official_content_still_requires_verified_partner(client, db, hidden_demo):
    editor = make_user(db, role="curator")
    w = make_world(db)
    for obj in (w["tradition"], w["partner"], w["course"], *w["lessons"]):
        obj.is_demo = False
        obj.approved_by_user_id, obj.approved_at = editor.id, obj.published_at
    mv = make_movement(db, w, is_demo=False, approved_by_user_id=editor.id, approved_at=w["course"].published_at)  # official_curriculum (default) + mitra belum terverifikasi
    db.flush()
    assert mv.content_basis == "official_curriculum"
    assert client.get(f"/api/v1/movements/{mv.id}").status_code == 404
    assert client.get(f"/api/v1/courses/{w['course'].slug}").status_code == 404


def test_logged_in_learner_sees_same_public_content_and_can_track_progress(client, db, hidden_demo):
    editor = make_user(db, role="curator")
    w, _ = source_backed_world(db, editor)
    learner = make_user(db)
    login(client, learner)
    c, le = w["course"], w["lessons"][0]
    assert client.get(f"/api/v1/courses/{c.slug}/lessons/{le.slug}").status_code == 200
    assert client.post(f"/api/v1/courses/{c.slug}/enroll").status_code in (200, 201)
    r = client.get(f"/api/v1/courses/{c.slug}/lessons/{le.slug}")
    assert r.json()["enrolled"] is True


def test_private_pilot_course_lessons_stay_hidden_from_anonymous(client, db):
    w = make_world(db)
    w["course"].distribution_scope = "pilot_private"
    db.flush()
    c, le = w["course"], w["lessons"][0]
    assert client.get(f"/api/v1/courses/{c.slug}").status_code == 404
    assert client.get(f"/api/v1/courses/{c.slug}/lessons/{le.slug}").status_code == 404


@pytest.mark.parametrize(
    "method, path",
    [
        ("post", "/api/v1/studio/movements"),
        ("post", "/api/v1/manage/courses"),
        ("post", "/api/v1/studio/partners"),
        ("get", "/api/v1/studio/movements"),
        ("get", "/api/v1/admin/users"),
    ],
)
def test_anonymous_cannot_write_or_open_studio(client, method, path):
    r = getattr(client, method)(path, json={}) if method == "post" else client.get(path)
    assert r.status_code in (401, 403), (path, r.status_code)


def test_learner_cannot_publish_or_edit(client, db):
    editor = make_user(db, role="curator")
    w, mv = source_backed_world(db, editor)
    learner = make_user(db)
    login(client, learner)
    assert client.get("/api/v1/studio/movements").status_code == 403
    assert client.post("/api/v1/manage/courses", json={"title": "x"}).status_code == 403
    db.refresh(mv)
    assert mv.status == "published"
    _ = (select, CulturalTradition, Movement, Partner, _real)
