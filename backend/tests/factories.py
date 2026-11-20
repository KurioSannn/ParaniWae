"""Pembuat data uji. Semua slug unik per pemanggilan agar tidak bentrok dengan seed dev."""

import uuid
from datetime import UTC, datetime

from app.core.security import hash_password
from app.models import (
    Course,
    CourseModule,
    CulturalTradition,
    Lesson,
    Movement,
    Partner,
    User,
)

PASSWORD = "uji-sandi-panjang-123"
_HASH = hash_password(PASSWORD)  # satu kali; Argon2 sengaja lambat


def uid() -> str:
    return uuid.uuid4().hex[:8]


def make_user(db, role="learner", **kw) -> User:
    u = User(email=f"{role}-{uid()}@uji.test", display_name=f"Uji {role}", role=role,
             password_hash=_HASH,
             email_verified_at=datetime.now(UTC), **kw)
    db.add(u)
    db.flush()
    return u


def login(client, user, password=PASSWORD):
    r = client.post("/api/v1/auth/login", json={"email": user.email, "password": password})
    assert r.status_code == 200, r.text
    client.headers["X-CSRF-Token"] = r.json()["csrf_token"]
    return r


def published(**extra) -> dict:
    return {"status": "published", "published_at": datetime.now(UTC), "is_demo": True,
            "source_citation": "[TES] sumber uji", **extra}


def make_world(db, status="published", n_lessons=3, creator=None):
    """Tradisi + mitra + kursus (1 modul) + n pelajaran, semua `status` (demo=True)."""
    wf = published() if status == "published" else {"status": status, "is_demo": True,
                                                  "source_citation": "[TES] sumber uji"}
    if creator:
        wf["created_by_user_id"] = creator.id
    s = uid()
    t = CulturalTradition(slug=f"t-{s}", name=f"Tradisi {s}", access_scope="public", **wf)
    p = Partner(slug=f"p-{s}", name=f"Mitra {s}", partner_type="school", **wf)
    db.add_all([t, p])
    db.flush()
    c = Course(slug=f"c-{s}", title=f"Kurikulum {s}", tradition_id=t.id, partner_id=p.id, **wf)
    db.add(c)
    db.flush()
    m = CourseModule(course_id=c.id, title="Modul 1", order_index=1)
    db.add(m)
    db.flush()
    lessons = []
    for i in range(1, n_lessons + 1):
        lesson = Lesson(course_id=c.id, module_id=m.id, slug=f"l{i}-{s}", title=f"Pelajaran {i}",
                        body="isi", order_index=i, **wf)
        db.add(lesson)
        lessons.append(lesson)
    db.flush()
    return {"tradition": t, "partner": p, "course": c, "module": m, "lessons": lessons, "wf": wf}


def make_movement(db, world, **extra):
    kw = {"practice_mode": "not_for_practice", **world["wf"]}
    kw.update(extra)
    mv = Movement(tradition_id=world["tradition"].id, partner_id=world["partner"].id,
                  slug=f"m-{uid()}", name_id="Gerakan uji", **kw)
    db.add(mv)
    db.flush()
    return mv
