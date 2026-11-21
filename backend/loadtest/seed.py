"""Seed SINTETIS untuk load test pilot (database scratch `silatara_load`; JANGAN pernah dijalankan pada DB dev/produksi).
Menolak berjalan bila nama DB tidak diawali `silatara_load`."""

import hashlib
import random
import sys
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_engine
from app.core.security import hash_password
from app.models import (
    CohortMember,
    Course,
    CourseModule,
    CulturalTradition,
    Enrollment,
    Lesson,
    LessonProgress,
    Partner,
    PartnerMember,
    PilotCohort,
    PilotProgram,
    PilotSurvey,
    PracticeSession,
    SurveyResponse,
    User,
)
from app.models import (
    Session as AuthSession,
)
from app.services import pilot as pilot_svc

LEARNERS = int(sys.argv[1]) if len(sys.argv) > 1 else 300
COHORTS = 3
LESSONS = 12


def main():
    s = get_settings()
    assert s.postgres_db.startswith("silatara_load"), "seed load test hanya untuk DB silatara_load*"
    rnd = random.Random(7)
    now = datetime.now(UTC)
    pw = hash_password("sandi-load-test-123")
    tokens: dict[str, str] = {}
    with Session(get_engine()) as db:
        def user(email, role, name):
            u = User(email=email, display_name=name, role=role, password_hash=pw, email_verified_at=now)
            db.add(u)
            return u

        admin, mgr, ins = user("lt-admin@load.test", "admin", "LT Admin"), user("lt-mgr@load.test", "instructor", "LT Mgr"), user("lt-ins@load.test", "instructor", "LT Ins")
        db.flush()
        partner = Partner(slug="lt-mitra", name="LT Mitra Privat", partner_type="school", verification_status="verified", status="draft",
                          verification_decided_by_user_id=admin.id, verification_decided_at=now, public_listing_consent=False, is_demo=True)
        trad = CulturalTradition(slug="lt-tradisi", name="LT Tradisi", access_scope="restricted", status="published", is_demo=True,
                                 source_citation="sintetis", published_at=now)
        db.add_all([partner, trad])
        db.flush()
        db.add_all([PartnerMember(partner_id=partner.id, user_id=mgr.id, role="manager"), PartnerMember(partner_id=partner.id, user_id=ins.id, role="instructor")])
        course = Course(slug="lt-kursus", title="LT Kursus Privat", tradition_id=trad.id, partner_id=partner.id, distribution_scope="pilot_private",
                        status="published", is_demo=True, source_citation="sintetis", published_at=now)
        db.add(course)
        db.flush()
        mod = CourseModule(course_id=course.id, title="Modul", order_index=1)
        db.add(mod)
        db.flush()
        lessons = []
        for i in range(LESSONS):
            le = Lesson(course_id=course.id, module_id=mod.id, slug=f"lt-l{i}", title=f"Pelajaran {i}", body="isi", order_index=i, status="published",
                        is_demo=True, source_citation="sintetis", published_at=now)
            db.add(le)
            lessons.append(le)
        prog = PilotProgram(partner_id=partner.id, name="LT Program", objective="load", start_date=(now - timedelta(days=30)).date(),
                            end_date=(now + timedelta(days=60)).date(), capacity=LEARNERS + 50, status="active", is_demo=True,
                            responsible_user_id=ins.id, created_by_user_id=ins.id)
        db.add(prog)
        db.flush()
        cohorts = []
        for k in range(COHORTS):
            c = PilotCohort(program_id=prog.id, name=f"LT Cohort {k}", course_id=course.id, instructor_user_id=ins.id, capacity=LEARNERS, status="open",
                            start_date=prog.start_date, end_date=prog.end_date)
            db.add(c)
            cohorts.append(c)
        survey = PilotSurvey(program_id=prog.id, kind="baseline", title="LT Survei", status="open", questions=[
            {"id": "q1", "type": "rating", "text": "q1", "required": True, "scale_min": 1, "scale_max": 5},
            {"id": "q2", "type": "single_choice", "text": "q2", "required": True, "options": ["a", "b", "c"]}])
        db.add(survey)
        db.flush()
        for i in range(LEARNERS):
            u = user(f"lt-l{i}@load.test", "learner", f"LT Peserta {i}")
            db.flush()
            c = cohorts[i % COHORTS]
            enr = Enrollment(user_id=u.id, course_id=course.id, status="active", enrolled_at=now - timedelta(days=20))
            db.add(enr)
            db.flush()
            db.add(CohortMember(cohort_id=c.id, program_id=prog.id, user_id=u.id, joined_at=now - timedelta(days=20), enrollment_id=enr.id))
            for le in lessons[: rnd.randint(0, LESSONS)]:
                db.add(LessonProgress(user_id=u.id, enrollment_id=enr.id, course_id=course.id, lesson_id=le.id, status="completed",
                                      started_at=now - timedelta(days=rnd.randint(1, 15)), completed_at=now - timedelta(days=rnd.randint(0, 14))))
            for _ in range(rnd.randint(0, 5)):
                st = now - timedelta(days=rnd.randint(0, 14), minutes=10)
                db.add(PracticeSession(user_id=u.id, lesson_id=lessons[0].id, status="completed", started_at=st, ended_at=st + timedelta(minutes=5),
                                       active_duration_ms=rnd.randint(60_000, 400_000), paused_duration_ms=0, model_version="lt"))
            if rnd.random() < 0.8:
                db.add(SurveyResponse(survey_id=survey.id, cohort_id=c.id, user_id=u.id, submitted_at=now, answers={"q1": rnd.randint(1, 5), "q2": rnd.choice("abc")}))
        db.flush()
        # sesi login sintetis (token dikenal) agar load test tidak dibatasi biaya Argon2 pada login
        for email in ["lt-admin@load.test", "lt-mgr@load.test", "lt-ins@load.test"] + [f"lt-l{i}@load.test" for i in range(LEARNERS)]:
            u = db.query(User).filter_by(email=email).one()
            tok = uuid.uuid4().hex + uuid.uuid4().hex
            db.add(AuthSession(user_id=u.id, token_hash=hashlib.sha256(tok.encode()).hexdigest(), csrf_token="csrf-" + uuid.uuid4().hex[:16],
                               expires_at=now + timedelta(days=1), last_seen_at=now))
            tokens[email] = tok
        # undangan untuk uji accept: learner baru yang belum anggota
        inv_tokens = []
        from app.core.security import new_token, token_digest
        from app.models import CohortInvitation
        from app.services.pilot import invite_status  # noqa: F401
        for i in range(150):
            raw = new_token()
            db.add(CohortInvitation(cohort_id=cohorts[0].id, token_hash=token_digest(raw), expires_at=now + timedelta(days=7), created_by_user_id=ins.id))
            inv_tokens.append(raw)
            nu = user(f"lt-new{i}@load.test", "learner", f"LT Baru {i}")
            db.flush()
            tok = uuid.uuid4().hex + uuid.uuid4().hex
            db.add(AuthSession(user_id=nu.id, token_hash=hashlib.sha256(tok.encode()).hexdigest(), csrf_token="csrf-" + uuid.uuid4().hex[:16],
                               expires_at=now + timedelta(days=1), last_seen_at=now))
            tokens[f"lt-new{i}@load.test"] = tok
        db.commit()
        import json
        csrf = {x.user_id: x.csrf_token for x in db.query(AuthSession).all()}
        uid = {u.email: str(u.id) for u in db.query(User).filter(User.email.like("%@load.test"))}
        out = {"tokens": tokens, "csrf": {e: csrf[uuid.UUID(uid[e])] for e in tokens}, "program_id": str(prog.id), "cohort_ids": [str(c.id) for c in cohorts],
               "course_slug": "lt-kursus", "lesson_ids": [str(le.id) for le in lessons], "lesson_slugs": [le.slug for le in lessons], "invites": inv_tokens, "learners": LEARNERS}
        open("/tmp/loadtest-seed.json", "w").write(json.dumps(out))
        print(f"seed selesai: {LEARNERS} peserta, {COHORTS} cohort, {LESSONS} pelajaran, {len(inv_tokens)} undangan")
        _ = pilot_svc


main()
