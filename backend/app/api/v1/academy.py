import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, auth_required, optional_auth
from app.core.db import get_db
from app.core.errors import ApiError
from app.models import (
    Course,
    Enrollment,
    Instructor,
    LessonMaterial,
    LessonProgress,
    Movement,
)
from app.schemas.public import CourseDetail, EnrollmentState, LessonDetail, MyEnrollment, MyProgress
from app.services import practice as practice_svc
from app.services import presenters as pr
from app.services import progress as prog
from app.services import visibility as vis

router = APIRouter(tags=["akademi & progres"])


def _rid(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _course(db: Session, slug: str) -> Course:
    c = db.scalar(select(Course).where(Course.slug == slug, vis.course_ok()))
    if not c:
        raise ApiError(404, "NOT_FOUND", "Kurikulum tidak ditemukan.")
    return c


def _lesson_ref(lesson, done: set | None):
    return {"id": lesson.id, "slug": lesson.slug, "title": lesson.title,
            "order_index": lesson.order_index, "estimated_minutes": lesson.estimated_minutes,
            "completed": (lesson.id in done) if done is not None else None}


@router.get("/courses/{slug}", response_model=CourseDetail, summary="Detail kurikulum")
def get_course(slug: str, ctx: AuthContext | None = Depends(optional_auth),
               db: Session = Depends(get_db)):
    c = _course(db, slug)
    enr = prog.get_enrollment(db, ctx.user.id, c.id) if ctx else None
    active = enr is not None and enr.status != "dropped"
    done = prog.completed_ids(db, ctx.user.id, c.id) if active else None
    modules: dict = {}
    for lesson, module in prog.visible_lessons(db, c.id):
        m = modules.setdefault(module.id, {"id": module.id, "title": module.title,
                                           "summary": module.summary,
                                           "order_index": module.order_index, "lessons": []})
        m["lessons"].append(_lesson_ref(lesson, done))
    inst = db.scalar(select(Instructor).where(Instructor.id == c.instructor_id,
                                              vis.instructor_ok())) if c.instructor_id else None
    return {**pr.course_summary(db, c), "safety_notes": c.safety_notes,
            "instructor": pr.instructor_out(db, inst) if inst else None,
            "modules": list(modules.values()),
            "enrollment": prog.enrollment_state(db, enr) if active else None}


@router.post("/courses/{slug}/enroll", response_model=EnrollmentState, summary="Daftar kurikulum")
def enroll(slug: str, request: Request, ctx: AuthContext = Depends(auth_required()),
           db: Session = Depends(get_db)):
    c = _course(db, slug)
    enr = prog.enroll(db, ctx.user, c, _rid(request))
    db.commit()
    return prog.enrollment_state(db, enr)


@router.delete("/courses/{slug}/enroll", status_code=204, summary="Berhenti mengikuti kurikulum")
def unenroll(slug: str, request: Request, ctx: AuthContext = Depends(auth_required()),
             db: Session = Depends(get_db)):
    prog.drop(db, ctx.user, _course(db, slug), _rid(request))
    db.commit()


@router.get("/courses/{slug}/lessons/{lesson_slug}", response_model=LessonDetail,
            summary="Isi pelajaran (perlu login)")
def get_lesson(slug: str, lesson_slug: str, ctx: AuthContext = Depends(auth_required()),
               db: Session = Depends(get_db)):
    c = _course(db, slug)
    lessons = prog.visible_lessons(db, c.id)
    idx = next((i for i, (lesson, _) in enumerate(lessons) if lesson.slug == lesson_slug), None)
    if idx is None:
        raise ApiError(404, "NOT_FOUND", "Pelajaran tidak ditemukan.")
    lesson, module = lessons[idx]
    enr = prog.get_enrollment(db, ctx.user.id, c.id)
    enrolled = enr is not None and enr.status != "dropped"
    done = prog.completed_ids(db, ctx.user.id, c.id) if enrolled else None
    status = None
    if enrolled:
        status = db.scalar(select(LessonProgress.status).where(
            LessonProgress.user_id == ctx.user.id, LessonProgress.lesson_id == lesson.id))
    movement = None
    if lesson.movement_id:
        m = db.scalar(select(Movement).where(Movement.id == lesson.movement_id,
                                             vis.movement_ok()))
        movement = pr.movement_out(db, m) if m else None
    materials = db.scalars(select(LessonMaterial).where(LessonMaterial.lesson_id == lesson.id)
                           .order_by(LessonMaterial.order_index, LessonMaterial.title)).all()
    return {
        "id": lesson.id, "slug": lesson.slug, "title": lesson.title, "objective": lesson.objective,
        "body": lesson.body, "safety_notes": lesson.safety_notes,
        "estimated_minutes": lesson.estimated_minutes, "module_title": module.title,
        "course": pr.course_summary(db, c), "movement": movement, "materials": materials,
        "prev_lesson": _lesson_ref(lessons[idx - 1][0], done) if idx > 0 else None,
        "next_lesson": _lesson_ref(lessons[idx + 1][0], done) if idx + 1 < len(lessons) else None,
        "provenance": pr.provenance(db, lesson), "enrolled": enrolled, "lesson_status": status,
        "practice": practice_svc.availability(db, lesson),
    }


class ProgressIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["in_progress", "completed", "incomplete"]


@router.put("/me/lessons/{lesson_id}/progress", summary="Catat progres pelajaran")
def put_progress(lesson_id: uuid.UUID, body: ProgressIn, request: Request,
                 ctx: AuthContext = Depends(auth_required()), db: Session = Depends(get_db)):
    """`completed` menandai selesai; `incomplete` membatalkan; `in_progress` hanya mencatat
    kunjungan (untuk fitur lanjutkan belajar). Wajib terdaftar di kurikulum induk."""
    result = prog.set_lesson_progress(db, ctx.user, lesson_id, body.status)
    db.commit()
    return result


@router.get("/me/progress", response_model=MyProgress, summary="Ringkasan progres belajar saya")
def my_progress(ctx: AuthContext = Depends(auth_required()), db: Session = Depends(get_db)):
    rows = db.scalars(select(Enrollment).where(Enrollment.user_id == ctx.user.id,
                                               Enrollment.status != "dropped")
                      .order_by(Enrollment.enrolled_at.desc())).all()
    items, done_total, lesson_total = [], 0, 0
    for enr in rows:
        course = db.get(Course, enr.course_id)
        if not db.scalar(select(Course.id).where(Course.id == course.id, vis.course_ok())):
            continue  # kursus yang sudah tidak publik disembunyikan
        state = prog.enrollment_state(db, enr)
        items.append({"course": pr.course_summary(db, course), "enrollment": state})
        done_total += state["progress"]["completed"]
        lesson_total += state["progress"]["total"]
    return {
        "enrollments": items,
        "totals": {"completed": done_total, "total": lesson_total,
                   "percent": round(100 * done_total / lesson_total) if lesson_total else 0},
        "courses_completed": sum(1 for i in items if i["enrollment"]["status"] == "completed"),
    }


@router.get("/me/enrollments", response_model=list[MyEnrollment], summary="Kurikulum yang diikuti")
def my_enrollments(ctx: AuthContext = Depends(auth_required()), db: Session = Depends(get_db)):
    return my_progress(ctx, db)["enrollments"]
