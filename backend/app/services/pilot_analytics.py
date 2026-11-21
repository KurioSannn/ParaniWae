"""Learning analytics Pilot: definisi metrik = docs/PILOT_STUDIO_CONTRACT.md §6. Semua angka dari query database nyata.

Tiga sumber DIPISAH: (1) usage (enrollment, lesson_progress, practice_sessions), (2) survei, (3) catatan instruktur
(tidak pernah masuk analytics/ekspor). Aktivitas ≠ penguasaan teknik. Agregat dengan n < K disembunyikan (`suppressed`).
"""

import csv
import io
import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    CohortInvitation,
    CohortMember,
    Course,
    LessonProgress,
    PilotCohort,
    PilotConsent,
    PilotProgram,
    PilotSurvey,
    PracticeSession,
    SurveyResponse,
    User,
)
from app.services import pilot as svc
from app.services import progress
from app.services.auth import now

NO_START_DAYS = 3
INACTIVE_DAYS = 7
DISCLAIMER = (
    "Metrik penggunaan mengukur aktivitas di aplikasi, bukan penguasaan teknik. Survei adalah instrumen draf yang belum "
    "divalidasi secara akademik; jawabannya adalah persepsi peserta."
)


def _k() -> int:
    return get_settings().pilot_min_respondents


def _sup(n: int) -> bool:
    return n < _k()


def _bounds(frm: date | None, to: date | None):
    lo = datetime.combine(frm, datetime.min.time(), UTC) if frm else None
    hi = datetime.combine(to + timedelta(days=1), datetime.min.time(), UTC) if to else None
    return lo, hi


def _between(col, lo, hi):
    conds = []
    if lo:
        conds.append(col >= lo)
    if hi:
        conds.append(col < hi)
    return conds


def scope_cohorts(db: Session, program: PilotProgram, cohort_id=None) -> list[PilotCohort]:
    stmt = select(PilotCohort).where(PilotCohort.program_id == program.id)
    if cohort_id:
        stmt = stmt.where(PilotCohort.id == cohort_id)
    return list(db.scalars(stmt.order_by(PilotCohort.created_at)))


def _member_ids(db, cohort_id) -> list:
    return list(
        db.scalars(
            select(CohortMember.user_id).where(CohortMember.cohort_id == cohort_id, CohortMember.status == "active")
        )
    )


def _lesson_ids(db, course_id) -> list:
    return [le.id for le, _ in progress.visible_lessons(db, course_id, system=True)]


def _events_subquery(users, course_id, lessons: list, lo=None, hi=None):
    """UNION ALL peristiwa aktivitas (progres pelajaran / sesi latihan) sebagai subquery (user_id, ts)."""
    q1 = select(LessonProgress.user_id.label("user_id"), LessonProgress.updated_at.label("ts")).where(
        LessonProgress.user_id.in_(users),
        LessonProgress.course_id == course_id,
        *_between(LessonProgress.updated_at, lo, hi),
    )
    q2 = select(PracticeSession.user_id.label("user_id"), PracticeSession.started_at.label("ts")).where(
        PracticeSession.user_id.in_(users),
        PracticeSession.lesson_id.in_(lessons or [uuid.uuid4()]),
        *_between(PracticeSession.started_at, lo, hi),
    )
    return q1.union_all(q2).subquery("ev")


def activity_summary(db: Session, users, course_id, lessons: list, lo=None, hi=None) -> dict:
    """{user_id: (jumlah_peristiwa, terakhir)} dihitung DI DATABASE (bukan memuat semua baris ke Python).
    `users` boleh subquery anggota aktif (select user_id ...)."""
    ev = _events_subquery(users, course_id, lessons, lo, hi)
    return {
        u: (n, last)
        for u, n, last in db.execute(select(ev.c.user_id, func.count(), func.max(ev.c.ts)).group_by(ev.c.user_id))
    }


def weekly_active(db: Session, users, course_id, lessons: list, start, weeks: int) -> dict[int, int]:
    """{pekan_ke(0..): jumlah pengguna aktif berbeda} dalam satu query."""
    ev = _events_subquery(users, course_id, lessons)
    wk = func.floor(func.extract("epoch", ev.c.ts - start) / 604800).label("wk")
    rows = db.execute(select(wk, func.count(func.distinct(ev.c.user_id))).where(ev.c.ts >= start).group_by(wk))
    return {int(k): n for k, n in rows if 0 <= int(k) < weeks}


def activity_events(db, users: list, course_id, lessons: list, lo=None, hi=None) -> dict:
    """{user_id: [datetime,...]} — peristiwa aktivitas (progres pelajaran / sesi latihan)."""
    ev: dict = defaultdict(list)
    if not users:
        return ev
    q = select(LessonProgress.user_id, LessonProgress.updated_at).where(
        LessonProgress.user_id.in_(users),
        LessonProgress.course_id == course_id,
        *_between(LessonProgress.updated_at, lo, hi),
    )
    for u, t in db.execute(q):
        ev[u].append(t)
    if lessons:
        q = select(PracticeSession.user_id, PracticeSession.started_at).where(
            PracticeSession.user_id.in_(users),
            PracticeSession.lesson_id.in_(lessons),
            *_between(PracticeSession.started_at, lo, hi),
        )
        for u, t in db.execute(q):
            ev[u].append(t)
    return ev


def cohort_usage(db: Session, c: PilotCohort, lo=None, hi=None) -> dict:
    members = _member_ids(db, c.id)
    lessons = _lesson_ids(db, c.course_id)
    n, L = len(members), len(lessons)
    sup = _sup(n)
    done = 0
    if members and lessons:
        done = (
            db.scalar(
                select(func.count())
                .select_from(LessonProgress)
                .where(
                    LessonProgress.user_id.in_(members),
                    LessonProgress.lesson_id.in_(lessons),
                    LessonProgress.status == "completed",
                    *_between(LessonProgress.completed_at, lo, hi),
                )
            )
            or 0
        )
    sess = {"completed": 0, "abandoned": 0, "error": 0, "in_progress": 0}
    active_ms = 0
    if members and lessons:
        for st, cnt, ms in db.execute(
            select(PracticeSession.status, func.count(), func.coalesce(func.sum(PracticeSession.active_duration_ms), 0))
            .where(
                PracticeSession.user_id.in_(members),
                PracticeSession.lesson_id.in_(lessons),
                *_between(PracticeSession.started_at, lo, hi),
            )
            .group_by(PracticeSession.status)
        ):
            sess[st] = cnt
            active_ms += ms or 0
    total_sess = sum(sess.values())
    active_users = len(activity_summary(db, members, c.course_id, lessons, lo, hi)) if members else 0
    base = {"cohort_id": c.id, "cohort_name": c.name, "active_members": n, "lessons_total": L, "suppressed": sup}
    if sup:
        return {
            **base,
            "completion_rate": None,
            "lessons_completed": None,
            "practice": None,
            "active_participants": None,
            "note": f"Disembunyikan: peserta aktif kurang dari {_k()}.",
        }
    return {
        **base,
        "lessons_completed": done,
        "completion_rate": round(done / (n * L), 4) if n and L else None,
        "active_participants": active_users,
        "active_rate": round(active_users / n, 4) if n else None,
        "practice": {
            "sessions": total_sess,
            "by_status": sess,
            "active_minutes": round(active_ms / 60000, 1),
            "sessions_per_active_participant": round(total_sess / active_users, 2) if active_users else None,
        },
    }


def retention(db: Session, c: PilotCohort, weeks: int = 12) -> dict:
    members = _member_ids(db, c.id)
    n = len(members)
    if _sup(n):
        return {"cohort_id": c.id, "suppressed": True, "weeks": []}
    start = (
        datetime.combine(c.start_date, datetime.min.time(), UTC)
        if c.start_date
        else min(
            [t for t in db.scalars(select(CohortMember.joined_at).where(CohortMember.cohort_id == c.id))] or [now()]
        )
    )
    end = datetime.combine(c.end_date + timedelta(days=1), datetime.min.time(), UTC) if c.end_date else now()
    per_week = weekly_active(db, members, c.course_id, _lesson_ids(db, c.course_id), start, weeks)
    out, k = [], 0
    while k < weeks:
        a = start + timedelta(weeks=k)
        if a > min(end, now()):
            break
        act = per_week.get(k, 0)
        out.append({"week": k + 1, "active": act, "rate": round(act / n, 4)})
        k += 1
    return {
        "cohort_id": c.id,
        "suppressed": False,
        "weeks": out,
        "definition": "Aktif = ≥1 progres pelajaran atau sesi latihan pada pekan itu.",
    }


def invitations_summary(db, cohort_ids) -> dict:
    out = {"total": 0, "accepted": 0, "pending": 0, "revoked": 0, "expired": 0}
    for inv in db.scalars(select(CohortInvitation).where(CohortInvitation.cohort_id.in_(cohort_ids))):
        out["total"] += 1
        out[svc.invite_status(inv)] += 1
    return out


def survey_analysis(
    db: Session, program: PilotProgram, cohort_ids: list, lo=None, hi=None, *, include_text: bool
) -> list[dict]:
    out = []
    members = (
        db.scalar(
            select(func.count())
            .select_from(CohortMember)
            .where(
                CohortMember.program_id == program.id,
                CohortMember.status == "active",
                CohortMember.cohort_id.in_(cohort_ids),
            )
        )
        or 0
    )
    for s in db.scalars(
        select(PilotSurvey).where(PilotSurvey.program_id == program.id).order_by(PilotSurvey.created_at)
    ):
        rows = list(
            db.scalars(
                select(SurveyResponse).where(
                    SurveyResponse.survey_id == s.id,
                    SurveyResponse.cohort_id.in_(cohort_ids),
                    *_between(SurveyResponse.submitted_at, lo, hi),
                )
            )
        )
        n = len(rows)
        denom = members if s.kind != "feedback_instructor" else len(cohort_ids)
        item = {
            "survey_id": s.id,
            "kind": s.kind,
            "title": s.title,
            "status": s.status,
            "responses": n,
            "eligible": denom,
            "response_rate": round(n / denom, 4) if denom else None,
            "instrument_note": s.instrument_note,
            "suppressed": _sup(n),
            "questions": [],
        }
        if _sup(n):
            item["note"] = f"Distribusi jawaban disembunyikan: responden kurang dari {_k()}."
            out.append(item)
            continue
        for q in s.questions:
            vals = [r.answers.get(q["id"]) for r in rows if r.answers.get(q["id"]) not in (None, "")]
            qa = {"id": q["id"], "text": q["text"], "type": q["type"], "answered": len(vals)}
            if q["type"] == "single_choice":
                qa["distribution"] = {o: sum(1 for v in vals if v == o) for o in q.get("options") or []}
            elif q["type"] == "rating":
                lo_, hi_ = q.get("scale_min", 1), q.get("scale_max", 5)
                qa["mean"] = round(sum(vals) / len(vals), 2) if vals else None
                qa["distribution"] = {str(i): sum(1 for v in vals if v == i) for i in range(lo_, hi_ + 1)}
            elif include_text:
                qa["texts"] = [v for v in vals][:100]  # tanpa identitas
            item["questions"].append(qa)
        out.append(item)
    return out


def program_analytics(
    db: Session,
    program: PilotProgram,
    cohort_id=None,
    frm: date | None = None,
    to: date | None = None,
    *,
    include_text: bool = False,
) -> dict:
    cohorts = scope_cohorts(db, program, cohort_id)
    ids = [c.id for c in cohorts]
    lo, hi = _bounds(frm, to)
    enrollment = []
    for c in cohorts:
        counts = dict(
            db.execute(
                select(CohortMember.status, func.count())
                .where(CohortMember.cohort_id == c.id)
                .group_by(CohortMember.status)
            ).all()
        )
        enrollment.append(
            {
                "cohort_id": c.id,
                "cohort_name": c.name,
                "capacity": c.capacity,
                "active": counts.get("active", 0),
                "withdrawn": counts.get("withdrawn", 0),
                "removed": counts.get("removed", 0),
                "status": c.status,
            }
        )
    return {
        "program": {"id": program.id, "name": program.name, "status": program.status, "is_demo": program.is_demo},
        "filters": {"cohort_id": cohort_id, "from": frm, "to": to},
        "min_respondents": _k(),
        "disclaimer": DISCLAIMER,
        "generated_at": now(),
        "enrollment": {
            "cohorts": enrollment,
            "invitations": invitations_summary(db, ids),
            "active_total": sum(e["active"] for e in enrollment),
            "capacity_total": program.capacity,
        },
        "usage": {
            "cohorts": [cohort_usage(db, c, lo, hi) for c in cohorts],
            "retention": [retention(db, c) for c in cohorts],
            "definitions": "Lihat PILOT_STUDIO_CONTRACT.md §6.",
        },
        "surveys": survey_analysis(db, program, ids, lo, hi, include_text=include_text),
        "consent": consent_summary(db, program),
    }


def consent_summary(db, program) -> dict:
    members = (
        db.scalar(
            select(func.count())
            .select_from(CohortMember)
            .where(CohortMember.program_id == program.id, CohortMember.status == "active")
        )
        or 0
    )
    out = {"members": members}
    for scope in ("research_aggregate", "publication_quote"):
        g = (
            db.scalar(
                select(func.count())
                .select_from(PilotConsent)
                .where(
                    PilotConsent.program_id == program.id, PilotConsent.scope == scope, PilotConsent.granted.is_(True)
                )
            )
            or 0
        )
        out[scope] = None if _sup(members) else g
    return out


def cohort_dashboard(db: Session, c: PilotCohort, program: PilotProgram) -> dict:
    """Dashboard operasional instruktur: tingkat peserta (dasar: operasional; bukan ekspor)."""
    members = list(
        db.execute(
            select(CohortMember, User)
            .join(User, User.id == CohortMember.user_id)
            .where(CohortMember.cohort_id == c.id, CohortMember.status == "active")
            .order_by(User.display_name)
        )
    )
    uids = [u.id for _, u in members]
    lessons = _lesson_ids(db, c.course_id)
    L = len(lessons)
    ev = activity_summary(db, uids, c.course_id, lessons)
    done_map: dict = defaultdict(int)
    if uids and lessons:
        for u, cnt in db.execute(
            select(LessonProgress.user_id, func.count())
            .where(
                LessonProgress.user_id.in_(uids),
                LessonProgress.lesson_id.in_(lessons),
                LessonProgress.status == "completed",
            )
            .group_by(LessonProgress.user_id)
        ):
            done_map[u] = cnt
    prac: dict = defaultdict(lambda: [0, 0])
    if uids and lessons:
        for u, cnt, ms in db.execute(
            select(
                PracticeSession.user_id, func.count(), func.coalesce(func.sum(PracticeSession.active_duration_ms), 0)
            )
            .where(PracticeSession.user_id.in_(uids), PracticeSession.lesson_id.in_(lessons))
            .group_by(PracticeSession.user_id)
        ):
            prac[u] = [cnt, ms or 0]
    surveyed = {
        sid: set(db.scalars(select(SurveyResponse.user_id).where(SurveyResponse.survey_id == sid)))
        for sid in db.scalars(
            select(PilotSurvey.id).where(PilotSurvey.program_id == program.id, PilotSurvey.status != "draft")
        )
    }
    t = now()
    rows, attention = [], 0
    for m, u in members:
        n_events, last = ev.get(u.id, (0, None))
        started = n_events > 0
        reasons = []
        d_join = (t - m.joined_at).days
        if not started and d_join >= NO_START_DAYS:
            reasons.append(f"belum memulai ≥{NO_START_DAYS} hari sejak bergabung")
        elif started and L and done_map[u.id] < L and program.status == "active" and (t - last).days >= INACTIVE_DAYS:
            reasons.append(f"tanpa aktivitas ≥{INACTIVE_DAYS} hari")
        attention += 1 if reasons else 0
        rows.append(
            {
                "user_id": u.id,
                "name": u.display_name,
                "joined_at": m.joined_at,
                "started": started,
                "last_activity_at": last,
                "lessons_completed": done_map[u.id],
                "lessons_total": L,
                "completion": round(done_map[u.id] / L, 4) if L else None,
                "practice_sessions": prac[u.id][0],
                "practice_minutes": round(prac[u.id][1] / 60000, 1),
                "needs_attention": bool(reasons),
                "attention_reasons": reasons,
                "surveys_pending": sum(1 for sid, who in surveyed.items() if u.id not in who),
            }
        )
    return {
        "cohort": svc.cohort_out(db, c),
        "program": {"id": program.id, "name": program.name, "status": program.status},
        "summary": {
            "members": len(rows),
            "not_started": sum(1 for r in rows if not r["started"]),
            "needs_attention": attention,
            "lessons_total": L,
            "completed_all": sum(1 for r in rows if r["completion"] == 1.0),
        },
        "thresholds": {"no_start_days": NO_START_DAYS, "inactive_days": INACTIVE_DAYS},
        "participants": rows,
        "disclaimer": DISCLAIMER,
    }


def report_csv(db: Session, program: PilotProgram, cohort_id=None, frm=None, to=None) -> str:
    """CSV AGREGAT tanpa identitas. Sel dengan n < K diberi 'DISEMBUNYIKAN'."""
    a = program_analytics(db, program, cohort_id, frm, to, include_text=False)
    buf = io.StringIO()
    _w = csv.writer(buf)

    class _Safe:
        """Cegah CSV/formula injection: sel teks diawali = + - @ diberi apostrof."""

        @staticmethod
        def writerow(row):
            _w.writerow(
                [
                    ("'" + c) if isinstance(c, str) and c[:1] in ("=", "+", "-", "@") and not c.startswith("#") else c
                    for c in row
                ]
            )

    w = _Safe()
    w.writerow(["# SILATARA Pilot report", program.name, f"dibuat {a['generated_at']:%Y-%m-%d %H:%M} UTC"])
    w.writerow(["# " + DISCLAIMER])
    w.writerow([f"# Agregat dengan responden/peserta < {_k()} disembunyikan."])
    w.writerow(["group", "metric", "cohort", "value", "n", "note"])
    for e in a["enrollment"]["cohorts"]:
        w.writerow(
            ["enrollment", "active_members", e["cohort_name"], e["active"], e["active"], f"kapasitas {e['capacity']}"]
        )
    for k, v in a["enrollment"]["invitations"].items():
        w.writerow(["invitations", k, "semua", v, v, ""])
    for u in a["usage"]["cohorts"]:
        if u["suppressed"]:
            w.writerow(["usage", "ringkasan", u["cohort_name"], "DISEMBUNYIKAN", u["active_members"], u["note"]])
            continue
        w.writerow(
            [
                "usage",
                "lesson_completion_rate",
                u["cohort_name"],
                u["completion_rate"],
                u["active_members"],
                "selesai/(anggota×pelajaran)",
            ]
        )
        w.writerow(
            ["usage", "active_participants", u["cohort_name"], u["active_participants"], u["active_members"], ""]
        )
        p = u["practice"]
        w.writerow(
            ["usage", "practice_sessions", u["cohort_name"], p["sessions"], u["active_members"], "metadata saja"]
        )
        w.writerow(["usage", "practice_active_minutes", u["cohort_name"], p["active_minutes"], u["active_members"], ""])
    for r in a["usage"]["retention"]:
        if r["suppressed"]:
            w.writerow(["retention", "weekly_active_rate", "", "DISEMBUNYIKAN", "", f"kurang dari {_k()}"])
        for wk in r["weeks"]:
            w.writerow(["retention", f"weekly_active_rate_w{wk['week']}", r["cohort_id"], wk["rate"], wk["active"], ""])
    for s in a["surveys"]:
        w.writerow(
            ["survey", "responses", s["title"], s["responses"], s["eligible"], f"response_rate={s['response_rate']}"]
        )
        if s["suppressed"]:
            w.writerow(["survey", "jawaban", s["title"], "DISEMBUNYIKAN", s["responses"], s.get("note", "")])
            continue
        for q in s["questions"]:
            if q["type"] == "rating":
                w.writerow(["survey", f"mean:{q['id']}", s["title"], q.get("mean"), q["answered"], q["text"]])
            for opt, cnt in (q.get("distribution") or {}).items():
                w.writerow(["survey", f"dist:{q['id']}={opt}", s["title"], cnt, q["answered"], ""])
    return buf.getvalue()


_ = Course
