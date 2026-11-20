"""Enrollment & progres belajar. Aturan persentase tunggal:

    persen = round(100 * selesai / total), dengan total = jumlah pelajaran PUBLISHED yang
    terlihat publik di kursus itu, dan selesai = jumlah di antaranya yang status progresnya
    `completed`. Pelajaran yang di-unpublish tidak dihitung (baik pembilang maupun penyebut).
    Total 0 -> 0%.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import (
    Course,
    CourseModule,
    Enrollment,
    Lesson,
    LessonProgress,
    User,
)
from app.services import audit
from app.services import visibility as vis
from app.services.auth import now


def visible_lessons(db: Session, course_id) -> list[tuple[Lesson, CourseModule]]:
    stmt = (
        select(Lesson, CourseModule)
        .join(CourseModule, CourseModule.id == Lesson.module_id)
        .where(Lesson.course_id == course_id, vis.lesson_ok())
        .order_by(CourseModule.order_index, Lesson.order_index, Lesson.title)
    )
    return [(row[0], row[1]) for row in db.execute(stmt)]


def completed_ids(db: Session, user_id, course_id) -> set:
    return set(db.scalars(select(LessonProgress.lesson_id).where(
        LessonProgress.user_id == user_id, LessonProgress.course_id == course_id,
        LessonProgress.status == "completed")))


def compute_progress(lessons: list, done: set) -> dict:
    total = len(lessons)
    completed = sum(1 for lesson, _ in lessons if lesson.id in done)
    percent = round(100 * completed / total) if total else 0
    return {"completed": completed, "total": total, "percent": percent}


def get_enrollment(db: Session, user_id, course_id) -> Enrollment | None:
    return db.scalar(select(Enrollment).where(Enrollment.user_id == user_id,
                                              Enrollment.course_id == course_id))


def enrollment_state(db: Session, enr: Enrollment) -> dict:
    lessons = visible_lessons(db, enr.course_id)
    done = completed_ids(db, enr.user_id, enr.course_id)
    nxt = next((lesson for lesson, _ in lessons if lesson.id not in done), None)
    last = db.get(Lesson, enr.last_lesson_id) if enr.last_lesson_id else None
    return {
        "status": enr.status, "enrolled_at": enr.enrolled_at, "completed_at": enr.completed_at,
        "progress": compute_progress(lessons, done),
        "last_lesson_slug": last.slug if last else None,
        "next_lesson_slug": nxt.slug if nxt else None,
    }


def _sync_completion(db: Session, enr: Enrollment) -> None:
    lessons = visible_lessons(db, enr.course_id)
    prog = compute_progress(lessons, completed_ids(db, enr.user_id, enr.course_id))
    full = prog["total"] > 0 and prog["completed"] == prog["total"]
    if enr.status == "active" and full:
        enr.status, enr.completed_at = "completed", now()
    elif enr.status == "completed" and not full:
        enr.status, enr.completed_at = "active", None


def enroll(db: Session, user: User, course: Course, rid: str | None) -> Enrollment:
    enr = get_enrollment(db, user.id, course.id)
    if enr is None:
        enr = Enrollment(user_id=user.id, course_id=course.id, status="active", enrolled_at=now())
        db.add(enr)
        db.flush()
        audit.record(db, actor=user, action="enrollment.create", entity_type="course",
                     entity_id=course.id, request_id=rid)
    elif enr.status == "dropped":
        enr.status = "active"
        audit.record(db, actor=user, action="enrollment.reactivate", entity_type="course",
                     entity_id=course.id, request_id=rid)
    _sync_completion(db, enr)
    return enr


def drop(db: Session, user: User, course: Course, rid: str | None) -> None:
    enr = get_enrollment(db, user.id, course.id)
    if enr is None or enr.status == "dropped":
        raise ApiError(404, "NOT_ENROLLED", "Anda belum terdaftar di kurikulum ini.")
    enr.status, enr.completed_at = "dropped", None
    audit.record(db, actor=user, action="enrollment.drop", entity_type="course",
                 entity_id=course.id, request_id=rid)


def set_lesson_progress(db: Session, user: User, lesson_id, status: str) -> dict:
    lesson = db.scalar(select(Lesson).where(Lesson.id == lesson_id, vis.lesson_ok()))
    if not lesson:
        raise ApiError(404, "NOT_FOUND", "Pelajaran tidak ditemukan.")
    enr = get_enrollment(db, user.id, lesson.course_id)
    if enr is None or enr.status == "dropped":
        raise ApiError(403, "NOT_ENROLLED",
                       "Daftar ke kurikulum ini terlebih dahulu untuk mencatat progres.")
    t = now()
    row = db.scalar(select(LessonProgress).where(LessonProgress.user_id == user.id,
                                                 LessonProgress.lesson_id == lesson.id))
    if row is None:
        row = LessonProgress(user_id=user.id, enrollment_id=enr.id, course_id=lesson.course_id,
                             lesson_id=lesson.id, status="in_progress", started_at=t)
        db.add(row)
    if status == "completed":
        if row.status != "completed":
            row.status, row.completed_at = "completed", t
    elif status == "incomplete":
        row.status, row.completed_at = "in_progress", None
    # status == "in_progress": hanya "kunjungan"; tidak menurunkan pelajaran yang sudah selesai
    enr.last_lesson_id = lesson.id
    db.flush()
    _sync_completion(db, enr)
    return {"lesson_id": lesson.id, "status": row.status, "completed_at": row.completed_at,
            "enrollment": enrollment_state(db, enr)}
