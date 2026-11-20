"""Domain Practice Studio: aturan boleh-dilatih, siklus sesi, ringkasan. Tidak pernah menyimpan data biometrik."""

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import Course, Lesson, Movement, PracticeSession, User
from app.schemas.practice import CompleteIn, StartIn
from app.services import audit
from app.services import presenters as pr
from app.services import progress as prog
from app.services import visibility as vis
from app.services.auth import now

STALE_AFTER = timedelta(hours=6)
WALL_TOLERANCE_MS = 5_000


def availability(db: Session, lesson: Lesson) -> dict:
    """Aturan server untuk tombol 'Mulai Latihan' (lihat docs/PRACTICE_STUDIO_CONTRACT.md §4)."""
    if lesson.is_demo:
        return {"available": True, "reason": None, "is_demo": True,
                "label": "[DEMO] Sesi latihan contoh — tanpa gerakan referensi; hanya menguji kamera dan "
                         "keterlihatan tubuh."}
    mv = None
    if lesson.movement_id:
        mv = db.scalar(select(Movement).where(Movement.id == lesson.movement_id, vis.movement_ok()))
    if mv and mv.practice_mode == "solo_beginner":
        return {"available": True, "reason": None, "is_demo": False,
                "label": "Latihan solo tingkat pemula."}
    return {"available": False, "reason": "PRACTICE_NOT_AVAILABLE", "is_demo": False,
            "label": "Pelajaran ini belum memiliki gerakan solo pemula yang disetujui mitra."}


def reap_stale(db: Session, user: User) -> None:
    """Sesi yang tak pernah ditutup (tab mati) ditandai abandoned; durasi tidak dikarang (diisi 0)."""
    t = now()
    rows = db.scalars(select(PracticeSession).where(
        PracticeSession.user_id == user.id, PracticeSession.status == "in_progress",
        PracticeSession.started_at < t - STALE_AFTER,
    ))
    for r in rows:
        r.status, r.ended_at, r.active_duration_ms, r.paused_duration_ms = "abandoned", r.started_at + STALE_AFTER, 0, 0
        r.error_code = "STALE"


def start(db: Session, user: User, body: StartIn, rid: str | None) -> PracticeSession:
    lesson = db.scalar(select(Lesson).where(Lesson.id == body.lesson_id, vis.lesson_ok()))
    if not lesson:
        raise ApiError(404, "NOT_FOUND", "Pelajaran tidak ditemukan.")
    enr = prog.get_enrollment(db, user.id, lesson.course_id)
    if enr is None or enr.status == "dropped":
        raise ApiError(403, "NOT_ENROLLED", "Daftar ke kurikulum ini terlebih dahulu untuk berlatih.")
    av = availability(db, lesson)
    if not av["available"]:
        raise ApiError(403, "PRACTICE_NOT_AVAILABLE", av["label"])
    reap_stale(db, user)
    # satu sesi aktif per pengguna: sesi lama yang masih berjalan dianggap ditinggalkan
    t = now()
    for old in db.scalars(select(PracticeSession).where(PracticeSession.user_id == user.id,
                                                        PracticeSession.status == "in_progress")):
        old.status, old.ended_at, old.active_duration_ms, old.paused_duration_ms = "abandoned", t, 0, 0
        old.error_code = "SUPERSEDED"
    s = PracticeSession(user_id=user.id, lesson_id=lesson.id, status="in_progress", started_at=t,
                        model_version=body.model_version, client_version=body.client_version)
    db.add(s)
    db.flush()
    audit.record(db, actor=user, action="practice.start", entity_type="practice_session",
                 entity_id=s.id, request_id=rid)
    return s


def get_own(db: Session, user: User, session_id) -> PracticeSession:
    s = db.get(PracticeSession, session_id)
    if not s or s.user_id != user.id:
        # 404 (bukan 403): tidak membocorkan keberadaan sesi milik orang lain
        raise ApiError(404, "NOT_FOUND", "Sesi latihan tidak ditemukan.")
    return s


def complete(db: Session, user: User, session_id, body: CompleteIn, rid: str | None) -> PracticeSession:
    s = get_own(db, user, session_id)
    if s.status != "in_progress":
        raise ApiError(409, "ALREADY_ENDED", "Sesi ini sudah berakhir.")
    t = now()
    wall_ms = int((t - s.started_at).total_seconds() * 1000)
    if body.active_duration_ms + body.paused_duration_ms > wall_ms + WALL_TOLERANCE_MS:
        raise ApiError(422, "DURATION_IMPOSSIBLE", "Durasi melebihi waktu nyata sejak sesi dimulai.",
                       {"wall_ms": wall_ms})
    qs = body.quality_summary
    if qs and qs.processed_frames > qs.frames_total:
        raise ApiError(422, "VALIDATION_ERROR", "processed_frames tidak boleh melebihi frames_total.")
    s.status, s.ended_at = body.status, t
    s.active_duration_ms, s.paused_duration_ms = body.active_duration_ms, body.paused_duration_ms
    s.quality_summary = qs.model_dump() if qs else None
    s.error_code = body.error_code
    audit.record(db, actor=user, action=f"practice.{body.status}", entity_type="practice_session",
                 entity_id=s.id, request_id=rid)
    return s


def to_out(db: Session, s: PracticeSession) -> dict:
    lesson = db.get(Lesson, s.lesson_id)
    course = db.get(Course, lesson.course_id)
    p = pr.provenance(db, lesson)
    return {
        "id": s.id, "status": s.status, "started_at": s.started_at, "ended_at": s.ended_at,
        "active_duration_ms": s.active_duration_ms, "paused_duration_ms": s.paused_duration_ms,
        "model_version": s.model_version, "client_version": s.client_version,
        "quality_summary": s.quality_summary, "error_code": s.error_code,
        "lesson": {"id": lesson.id, "slug": lesson.slug, "title": lesson.title, "course_slug": course.slug,
                   "course_title": course.title, "is_demo": lesson.is_demo,
                   "verification_label": p["verification_label"]},
    }


def summary(db: Session, user: User, tz_offset_min: int, days: int = 14) -> dict:
    reap_stale(db, user)
    t = now()
    offset = timedelta(minutes=tz_offset_min)
    today = (t + offset).date()
    rows = db.scalars(select(PracticeSession).where(PracticeSession.user_id == user.id,
                                                    PracticeSession.status != "in_progress")).all()
    total_s = sum((r.active_duration_ms or 0) for r in rows) // 1000
    per_day: dict[str, list[int]] = {}
    for r in rows:
        d = (r.started_at + offset).date()
        if (today - d).days < days:
            e = per_day.setdefault(d.isoformat(), [0, 0])
            e[0] += 1
            e[1] += (r.active_duration_ms or 0) // 1000
    series = []
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        c, sec = per_day.get(d, [0, 0])
        series.append({"date": d, "sessions": c, "active_seconds": sec})
    last7 = series[-7:]
    last = db.scalar(select(PracticeSession).where(PracticeSession.user_id == user.id,
                                                   PracticeSession.status != "in_progress")
                     .order_by(PracticeSession.started_at.desc()).limit(1))
    return {
        "total_sessions": len(rows), "completed_sessions": sum(1 for r in rows if r.status == "completed"),
        "total_active_seconds": total_s, "sessions_last_7_days": sum(x["sessions"] for x in last7),
        "active_seconds_last_7_days": sum(x["active_seconds"] for x in last7), "days": series,
        "last_session": to_out(db, last) if last else None,
    }


_ = func  # noqa: F841
