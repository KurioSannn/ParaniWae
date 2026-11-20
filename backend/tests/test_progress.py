import pytest
from sqlalchemy.exc import IntegrityError

from app.models import LessonProgress
from app.services.auth import now
from app.services.progress import compute_progress
from tests.factories import login, make_user, make_world


def _enroll(client, w):
    r = client.post(f"/api/v1/courses/{w['course'].slug}/enroll")
    assert r.status_code == 200, r.text
    return r.json()


def _put(client, lesson, status):
    return client.put(f"/api/v1/me/lessons/{lesson.id}/progress", json={"status": status})


def test_cannot_complete_without_enrollment(client, db):
    w = make_world(db)
    login(client, make_user(db))
    r = _put(client, w["lessons"][0], "completed")
    assert r.status_code == 403 and r.json()["error"]["code"] == "NOT_ENROLLED"
    assert db.query(LessonProgress).count() >= 0  # tidak ada baris untuk pelajaran ini
    assert db.query(LessonProgress).filter_by(lesson_id=w["lessons"][0].id).count() == 0


def test_cannot_complete_lesson_of_other_course(client, db):
    a, b = make_world(db), make_world(db)
    login(client, make_user(db))
    _enroll(client, a)
    assert _put(client, b["lessons"][0], "completed").status_code == 403
    assert _put(client, a["lessons"][0], "completed").status_code == 200


def test_unpublished_lesson_cannot_be_completed(client, db):
    w = make_world(db)
    login(client, make_user(db))
    _enroll(client, w)
    w["lessons"][0].status = "draft"
    db.flush()
    assert _put(client, w["lessons"][0], "completed").status_code == 404


def test_requires_login_and_csrf(client, db):
    w = make_world(db)
    assert client.post(f"/api/v1/courses/{w['course'].slug}/enroll").status_code == 401
    login(client, make_user(db))
    del client.headers["X-CSRF-Token"]
    assert client.post(f"/api/v1/courses/{w['course'].slug}/enroll").status_code == 403


def test_percent_complete_and_course_completion(client, db):
    w = make_world(db, n_lessons=3)
    login(client, make_user(db))
    assert _enroll(client, w)["progress"] == {"completed": 0, "total": 3, "percent": 0}
    p = _put(client, w["lessons"][0], "completed").json()["enrollment"]
    assert p["progress"] == {"completed": 1, "total": 3, "percent": 33}
    assert p["next_lesson_slug"] == w["lessons"][1].slug and p["status"] == "active"
    _put(client, w["lessons"][1], "completed")
    p = _put(client, w["lessons"][2], "completed").json()["enrollment"]
    assert p["progress"]["percent"] == 100 and p["status"] == "completed" and p["completed_at"]
    assert p["next_lesson_slug"] is None
    p = _put(client, w["lessons"][2], "incomplete").json()["enrollment"]
    assert p["progress"]["percent"] == 67 and p["status"] == "active" and p["completed_at"] is None


def test_completing_twice_is_idempotent_and_visit_does_not_uncomplete(client, db):
    w = make_world(db, n_lessons=2)
    login(client, make_user(db))
    _enroll(client, w)
    first = _put(client, w["lessons"][0], "completed").json()["completed_at"]
    again = _put(client, w["lessons"][0], "completed").json()
    assert again["completed_at"] == first and again["enrollment"]["progress"]["completed"] == 1
    visit = _put(client, w["lessons"][0], "in_progress").json()
    assert visit["status"] == "completed"


def test_resume_points_to_last_visited_and_next_incomplete(client, db):
    w = make_world(db, n_lessons=3)
    login(client, make_user(db))
    _enroll(client, w)
    _put(client, w["lessons"][0], "completed")
    st = _put(client, w["lessons"][1], "in_progress").json()["enrollment"]
    assert st["last_lesson_slug"] == w["lessons"][1].slug
    assert st["next_lesson_slug"] == w["lessons"][1].slug
    mine = client.get("/api/v1/me/enrollments").json()
    assert mine[0]["enrollment"]["next_lesson_slug"] == w["lessons"][1].slug


def test_unpublished_lesson_excluded_from_total(client, db):
    w = make_world(db, n_lessons=2)
    login(client, make_user(db))
    _enroll(client, w)
    _put(client, w["lessons"][0], "completed")
    w["lessons"][1].status = "draft"
    db.flush()
    st = client.get(f"/api/v1/courses/{w['course'].slug}").json()["enrollment"]
    assert st["progress"] == {"completed": 1, "total": 1, "percent": 100}


def test_progress_is_private_per_user(client, db):
    w = make_world(db, n_lessons=1)
    u1, u2 = make_user(db), make_user(db)
    login(client, u1)
    _enroll(client, w)
    _put(client, w["lessons"][0], "completed")
    client.cookies.clear()
    login(client, u2)
    assert client.get("/api/v1/me/progress").json()["enrollments"] == []
    assert client.get(f"/api/v1/courses/{w['course'].slug}").json()["enrollment"] is None
    assert _put(client, w["lessons"][0], "completed").status_code == 403


def test_drop_and_reactivate_keeps_progress(client, db):
    w = make_world(db, n_lessons=2)
    login(client, make_user(db))
    _enroll(client, w)
    _put(client, w["lessons"][0], "completed")
    assert client.delete(f"/api/v1/courses/{w['course'].slug}/enroll").status_code == 204
    assert _put(client, w["lessons"][1], "completed").status_code == 403
    assert client.get("/api/v1/me/progress").json()["enrollments"] == []
    assert _enroll(client, w)["progress"]["completed"] == 1
    assert client.delete(f"/api/v1/courses/{w['course'].slug}/enroll").status_code == 204
    assert client.delete(f"/api/v1/courses/{w['course'].slug}/enroll").status_code == 404


def test_overall_progress_totals(client, db):
    a, b = make_world(db, n_lessons=2), make_world(db, n_lessons=2)
    login(client, make_user(db))
    _enroll(client, a)
    _enroll(client, b)
    _put(client, a["lessons"][0], "completed")
    _put(client, a["lessons"][1], "completed")
    r = client.get("/api/v1/me/progress").json()
    assert r["totals"] == {"completed": 2, "total": 4, "percent": 50}
    assert r["courses_completed"] == 1


def test_compute_progress_pure():
    class L:
        def __init__(self, i):
            self.id = i
    lessons = [(L(i), None) for i in range(3)]
    assert compute_progress(lessons, {0}) == {"completed": 1, "total": 3, "percent": 33}
    assert compute_progress(lessons, {0, 1, 2, 99}) == {"completed": 3, "total": 3, "percent": 100}
    assert compute_progress([], set()) == {"completed": 0, "total": 0, "percent": 0}


def test_db_rejects_progress_for_lesson_outside_enrolled_course(db):
    """Jaring pengaman DB: FK komposit menolak pelajaran dari kursus lain."""
    a, b = make_world(db), make_world(db)
    u = make_user(db)
    from app.models import Enrollment
    enr = Enrollment(user_id=u.id, course_id=a["course"].id, enrolled_at=now())
    db.add(enr)
    db.flush()
    db.add(LessonProgress(user_id=u.id, enrollment_id=enr.id, course_id=a["course"].id,
                          lesson_id=b["lessons"][0].id, status="in_progress", started_at=now()))
    with pytest.raises(IntegrityError):
        db.flush()


def test_db_rejects_completed_without_timestamp(db):
    a = make_world(db)
    u = make_user(db)
    from app.models import Enrollment
    enr = Enrollment(user_id=u.id, course_id=a["course"].id, enrolled_at=now())
    db.add(enr)
    db.flush()
    db.add(LessonProgress(user_id=u.id, enrollment_id=enr.id, course_id=a["course"].id,
                          lesson_id=a["lessons"][0].id, status="completed", started_at=now()))
    with pytest.raises(IntegrityError):
        db.flush()
