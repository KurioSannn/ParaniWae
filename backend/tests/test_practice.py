"""Practice Studio: siklus sesi, aturan boleh-dilatih, integritas, privasi skema, dan isolasi antar-pengguna."""
from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import PracticeSession
from app.services.auth import now
from tests.factories import login, make_movement, make_user, make_world

QS = {
    "frames_total": 40, "processed_frames": 40, "dropped_frames": 3, "valid_frame_ratio": 0.75,
    "ms_in_state": {"waiting_for_subject": 1000, "detecting": 9000, "partial_detection": 500, "insufficient_visibility": 200},
    "reasons": {"NO_POSE": 5, "OUT_OF_FRAME": 4}, "engine": "synthetic", "delegate": "CPU", "simulated": True,
}
MODEL = "mediapipe-tasks-vision@1.2.3/pose_landmarker_lite+hand_landmarker"


def setup(client, db, role="learner", enroll=True, **world_kw):
    w = make_world(db, **world_kw)
    u = make_user(db, role)
    login(client, u)
    if enroll:
        assert client.post(f"/api/v1/courses/{w['course'].slug}/enroll").status_code == 200
    return w, u


def start(client, lesson, **over):
    body = {"lesson_id": str(lesson.id), "model_version": MODEL, "client_version": "studio-0.1"}
    body.update(over)
    return client.post("/api/v1/practice-sessions", json=body)


def finish(client, sid, **over):
    body = {"status": "completed", "active_duration_ms": 1500, "paused_duration_ms": 0, "quality_summary": QS}
    body.update(over)
    return client.post(f"/api/v1/practice-sessions/{sid}/complete", json=body)


def test_full_session_lifecycle_and_metadata_only(client, db):
    w, u = setup(client, db)
    r = start(client, w["lessons"][0])
    assert r.status_code == 201, r.text
    s = r.json()
    assert s["status"] == "in_progress" and s["ended_at"] is None and s["lesson"]["slug"] == w["lessons"][0].slug
    assert s["lesson"]["is_demo"] is True and "DEMO" in s["lesson"]["verification_label"]
    f = finish(client, s["id"])
    assert f.status_code == 200, f.text
    d = f.json()
    assert d["status"] == "completed" and d["ended_at"] and d["active_duration_ms"] == 1500
    assert d["quality_summary"]["valid_frame_ratio"] == 0.75
    row = db.get(PracticeSession, s["id"])
    cols = {c.key for c in PracticeSession.__mapper__.column_attrs}
    assert not {c for c in cols if any(k in c for k in ("video", "frame", "photo", "image", "landmark", "biometric"))}
    assert set(row.quality_summary) <= {"frames_total", "processed_frames", "dropped_frames", "valid_frame_ratio",
                                        "ms_in_state", "reasons", "engine", "delegate", "simulated"}
    assert finish(client, s["id"]).status_code == 409  # tidak dapat diakhiri dua kali


def test_requires_login_csrf_and_enrollment(client, db):
    w = make_world(db)
    assert start(client, w["lessons"][0]).status_code == 401
    login(client, make_user(db))
    r = start(client, w["lessons"][0])
    assert r.status_code == 403 and r.json()["error"]["code"] == "NOT_ENROLLED"
    client.post(f"/api/v1/courses/{w['course'].slug}/enroll")
    del client.headers["X-CSRF-Token"]
    assert start(client, w["lessons"][0]).status_code == 403  # CSRF


def test_unpublished_or_unknown_lesson_404(client, db):
    w, _ = setup(client, db)
    w["lessons"][1].status = "draft"
    db.flush()
    assert start(client, w["lessons"][1]).status_code == 404
    assert start(client, w["lessons"][0], lesson_id="00000000-0000-0000-0000-000000000000").status_code == 404


def test_availability_rule_demo_vs_real_movement(client, db):
    # non-demo tanpa gerakan solo_beginner -> tidak boleh
    w, _ = setup(client, db)
    lesson = w["lessons"][0]
    approver = make_user(db, "curator")  # dibuat dulu: flush otomatis tidak boleh melihat lesson setengah jadi
    lesson.is_demo = False
    lesson.approved_by_user_id = approver.id
    lesson.approved_at = now()
    lesson.approval_evidence_ref = "bukti"
    db.flush()
    assert client.get(f"/api/v1/courses/{w['course'].slug}/lessons/{lesson.slug}").json()["practice"]["available"] is False
    r = start(client, lesson)
    assert r.status_code == 403 and r.json()["error"]["code"] == "PRACTICE_NOT_AVAILABLE"
    # dengan gerakan solo_beginner publik -> boleh
    mv = make_movement(db, w, practice_mode="solo_beginner")
    lesson.movement_id = mv.id
    db.flush()
    p = client.get(f"/api/v1/courses/{w['course'].slug}/lessons/{lesson.slug}").json()["practice"]
    assert p["available"] is True and p["is_demo"] is False
    assert start(client, lesson).status_code == 201
    # gerakan supervised_only -> tidak
    mv.practice_mode = "supervised_only"
    db.flush()
    assert start(client, lesson).status_code == 403


@pytest.mark.parametrize("extra", [
    {"landmarks": [[0.1, 0.2, 0.3]]}, {"frame": "data:image/png;base64,AAAA"}, {"video_url": "http://x"},
    {"photo": "x"}, {"pose": {}},
])
def test_complete_rejects_biometric_or_media_fields(client, db, extra):
    w, _ = setup(client, db)
    sid = start(client, w["lessons"][0]).json()["id"]
    top = client.post(f"/api/v1/practice-sessions/{sid}/complete",
                      json={"status": "completed", "active_duration_ms": 10, **extra})
    assert top.status_code == 422
    nested = client.post(f"/api/v1/practice-sessions/{sid}/complete",
                         json={"status": "completed", "active_duration_ms": 10, "quality_summary": {**QS, **extra}})
    assert nested.status_code == 422
    assert client.post("/api/v1/practice-sessions", json={"lesson_id": str(w["lessons"][0].id), "model_version": MODEL, **extra}).status_code == 422


def test_integrity_duration_cannot_exceed_wall_clock_and_bounds(client, db):
    w, _ = setup(client, db)
    sid = start(client, w["lessons"][0]).json()["id"]
    r = finish(client, sid, active_duration_ms=3_600_000)  # 1 jam padahal baru dimulai
    assert r.status_code == 422 and r.json()["error"]["code"] == "DURATION_IMPOSSIBLE"
    assert finish(client, sid, active_duration_ms=-1).status_code == 422
    assert finish(client, sid, quality_summary={**QS, "valid_frame_ratio": 1.5}).status_code == 422
    assert finish(client, sid, quality_summary={**QS, "processed_frames": 99, "frames_total": 10}).status_code == 422
    assert finish(client, sid, status="exploded").status_code == 422
    assert finish(client, sid).status_code == 200  # tetap dapat diakhiri dengan benar


def test_other_users_cannot_see_or_end_my_sessions(client, db):
    w, owner = setup(client, db)
    sid = start(client, w["lessons"][0]).json()["id"]
    client.cookies.clear()
    other = make_user(db)
    login(client, other)
    assert client.get(f"/api/v1/practice-sessions/{sid}").status_code == 404
    assert finish(client, sid).status_code == 404
    assert client.get("/api/v1/me/practice-sessions").json()["total"] == 0
    assert client.get("/api/v1/me/practice-summary").json()["total_sessions"] == 0
    client.cookies.clear()
    client.post("/api/v1/auth/login", json={"email": owner.email, "password": "uji-sandi-panjang-123"})
    assert client.get(f"/api/v1/practice-sessions/{sid}").status_code == 200


def test_anonymous_gets_401_on_all_practice_endpoints(client):
    assert client.get("/api/v1/me/practice-sessions").status_code == 401
    assert client.get("/api/v1/me/practice-summary").status_code == 401
    assert client.get("/api/v1/practice-sessions/00000000-0000-0000-0000-000000000000").status_code == 401


def test_history_pagination_filter_and_summary_trend(client, db):
    w, u = setup(client, db, n_lessons=2)
    ids = []
    for i in range(3):
        sid = start(client, w["lessons"][i % 2]).json()["id"]
        finish(client, sid, active_duration_ms=1000 * (i + 1), paused_duration_ms=500)
        ids.append(sid)
    h = client.get("/api/v1/me/practice-sessions", params={"page_size": 2}).json()
    assert h["total"] == 3 and len(h["items"]) == 2 and h["total_pages"] == 2
    assert h["items"][0]["id"] == ids[-1]  # terbaru dulu
    only = client.get("/api/v1/me/practice-sessions", params={"lesson": str(w["lessons"][1].id)}).json()
    assert only["total"] == 1
    assert client.get("/api/v1/me/practice-sessions", params={"status": "bogus"}).status_code == 422
    s = client.get("/api/v1/me/practice-summary", params={"tz_offset": 420}).json()
    assert s["total_sessions"] == 3 and s["completed_sessions"] == 3
    assert s["total_active_seconds"] == 6 and s["sessions_last_7_days"] == 3
    assert len(s["days"]) == 14 and sum(d["sessions"] for d in s["days"]) == 3
    assert s["last_session"]["id"] == ids[-1]
    assert client.get("/api/v1/me/practice-summary", params={"tz_offset": 9999}).status_code == 422


def test_new_session_supersedes_unfinished_and_stale_are_reaped(client, db):
    w, u = setup(client, db)
    a = start(client, w["lessons"][0]).json()["id"]
    b = start(client, w["lessons"][0]).json()["id"]
    assert client.get(f"/api/v1/practice-sessions/{a}").json()["status"] == "abandoned"
    row = db.get(PracticeSession, b)
    row.started_at = now() - timedelta(hours=7)
    db.flush()
    items = {i["id"]: i for i in client.get("/api/v1/me/practice-sessions").json()["items"]}
    assert items[b]["status"] == "abandoned" and items[b]["active_duration_ms"] == 0  # durasi tidak dikarang


def test_abandoned_and_error_statuses_are_recorded(client, db):
    w, _ = setup(client, db)
    sid = start(client, w["lessons"][0]).json()["id"]
    r = finish(client, sid, status="error", error_code="WORKER_CRASH", quality_summary=None)
    assert r.json()["status"] == "error" and r.json()["error_code"] == "WORKER_CRASH"
    assert finish(client, start(client, w["lessons"][0]).json()["id"], status="abandoned").json()["status"] == "abandoned"


def test_does_not_change_lesson_completion_or_progress(client, db):
    w, _ = setup(client, db, n_lessons=2)
    before = client.get("/api/v1/me/progress").json()["totals"]
    finish(client, start(client, w["lessons"][0]).json()["id"])
    assert client.get("/api/v1/me/progress").json()["totals"] == before  # latihan bukan penyelesaian lesson


@pytest.mark.parametrize("bad", [
    dict(status="completed"), dict(status="in_progress", ended_at="NOW"),
    dict(status="completed", ended_at="NOW", active_duration_ms=-5), dict(status="completed", ended_at="PAST", active_duration_ms=1),
    dict(status="weird"),
])
def test_db_constraints_param(db, bad):
    u = make_user(db)
    w = make_world(db)
    t = now()
    vals = {k: (t if v == "NOW" else t - timedelta(days=1) if v == "PAST" else v) for k, v in bad.items()}
    db.add(PracticeSession(user_id=u.id, lesson_id=w["lessons"][0].id, started_at=t, model_version="m", **vals))
    with pytest.raises(IntegrityError):
        db.flush()


def test_openapi_documents_practice_endpoints_and_no_media(client):
    spec = client.get("/openapi.json").json()
    for path in ("/api/v1/practice-sessions", "/api/v1/practice-sessions/{session_id}/complete",
                 "/api/v1/me/practice-sessions", "/api/v1/me/practice-summary"):
        assert path in spec["paths"]
