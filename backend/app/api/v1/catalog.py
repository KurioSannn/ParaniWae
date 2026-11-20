import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import PageParams
from app.core.db import get_db
from app.core.errors import ApiError
from app.models import (
    Course,
    CulturalTradition,
    Instructor,
    Movement,
    Partner,
    TraditionPartner,
)
from app.schemas.common import Page
from app.schemas.public import (
    CourseSummary,
    InstructorOut,
    MovementOut,
    MovementSummary,
    PartnerDetail,
    PartnerSummary,
    TraditionDetail,
    TraditionSummary,
)
from app.schemas.studio import VersionPublicOut
from app.services import presenters as pr
from app.services import visibility as vis
from app.services.queries import apply_sort, paginate, search_cond

router = APIRouter(tags=["katalog publik"])


def _tradition_by_slug(db: Session, slug: str) -> CulturalTradition:
    obj = db.scalar(select(CulturalTradition).where(CulturalTradition.slug == slug,
                                                    vis.tradition_ok()))
    if not obj:
        raise ApiError(404, "NOT_FOUND", "Tradisi tidak ditemukan.")
    return obj


def _partner_by_slug(db: Session, slug: str) -> Partner:
    obj = db.scalar(select(Partner).where(Partner.slug == slug, vis.partner_ok()))
    if not obj:
        raise ApiError(404, "NOT_FOUND", "Perguruan tidak ditemukan.")
    return obj


def _courses(db: Session, *conds) -> list[dict]:
    rows = db.scalars(select(Course).where(vis.course_ok(), *conds).order_by(Course.title))
    return [pr.course_summary(db, c) for c in rows]


# ---- Tradisi ----
@router.get("/traditions", response_model=Page[TraditionSummary], summary="Katalog tradisi")
def list_traditions(
    q: str | None = None, region: str | None = None,
    sort: str | None = Query(None, description="name | -name | newest"),
    p: PageParams = Depends(), db: Session = Depends(get_db),
):
    T = CulturalTradition
    stmt = select(T).where(vis.tradition_ok())
    if (c := search_cond(q, T.name, T.local_name, T.public_summary)) is not None:
        stmt = stmt.where(c)
    if region:
        stmt = stmt.where(T.region == region)
    stmt = apply_sort(stmt, sort, {"name": [T.name], "-name": [T.name.desc()],
                                   "newest": [T.created_at.desc(), T.name]}, "name")
    return paginate(db, stmt, p.page, p.page_size, lambda t: pr.tradition_summary(db, t))


@router.get("/traditions/{slug}", response_model=TraditionDetail, summary="Detail tradisi")
def get_tradition(slug: str, db: Session = Depends(get_db)):
    t = _tradition_by_slug(db, slug)
    partner_ids = select(TraditionPartner.partner_id).where(TraditionPartner.tradition_id == t.id)
    partners = db.scalars(select(Partner).where(Partner.id.in_(partner_ids), vis.partner_ok())
                          .order_by(Partner.name))
    movements = db.scalars(select(Movement).where(Movement.tradition_id == t.id, vis.movement_ok())
                           .order_by(Movement.name_id))
    return {**pr.tradition_summary(db, t), "access_scope": t.access_scope,
            "partners": [pr.partner_summary(db, x) for x in partners],
            "courses": _courses(db, Course.tradition_id == t.id),
            "movements": [pr.movement_summary(db, m) for m in movements]}


# ---- Perguruan ----
@router.get("/partners", response_model=Page[PartnerSummary], summary="Katalog perguruan")
def list_partners(
    q: str | None = None, city: str | None = None, tradition: str | None = None,
    partner_type: str | None = None,
    sort: str | None = Query(None, description="name | -name | newest"),
    p: PageParams = Depends(), db: Session = Depends(get_db),
):
    P = Partner
    stmt = select(P).where(vis.partner_ok())
    if (c := search_cond(q, P.name, P.official_description, P.city)) is not None:
        stmt = stmt.where(c)
    if city:
        stmt = stmt.where(P.city == city)
    if partner_type:
        stmt = stmt.where(P.partner_type == partner_type)
    if tradition:
        stmt = stmt.where(P.id.in_(
            select(TraditionPartner.partner_id).join(CulturalTradition,
                CulturalTradition.id == TraditionPartner.tradition_id)
            .where(CulturalTradition.slug == tradition)))
    stmt = apply_sort(stmt, sort, {"name": [P.name], "-name": [P.name.desc()],
                                   "newest": [P.created_at.desc(), P.name]}, "name")
    return paginate(db, stmt, p.page, p.page_size, lambda x: pr.partner_summary(db, x))


@router.get("/partners/{slug}", response_model=PartnerDetail, summary="Detail perguruan")
def get_partner(slug: str, db: Session = Depends(get_db)):
    part = _partner_by_slug(db, slug)
    trad_ids = select(TraditionPartner.tradition_id).where(TraditionPartner.partner_id == part.id)
    trads = db.scalars(select(CulturalTradition).where(CulturalTradition.id.in_(trad_ids),
                                                       vis.tradition_ok())
                       .order_by(CulturalTradition.name))
    insts = db.scalars(select(Instructor).where(Instructor.partner_id == part.id,
                                                vis.instructor_ok()).order_by(Instructor.name))
    return {**pr.partner_summary(db, part),
            "traditions": [pr.tradition_summary(db, t) for t in trads],
            "instructors": [pr.instructor_out(db, i) for i in insts],
            "courses": _courses(db, Course.partner_id == part.id)}


# ---- Instruktur ----
@router.get("/instructors", response_model=Page[InstructorOut], summary="Daftar instruktur")
def list_instructors(q: str | None = None, partner: str | None = None,
                     p: PageParams = Depends(), db: Session = Depends(get_db)):
    I = Instructor  # noqa: E741
    stmt = select(I).where(vis.instructor_ok())
    if (c := search_cond(q, I.name, I.bio)) is not None:
        stmt = stmt.where(c)
    if partner:
        stmt = stmt.where(I.partner_id.in_(select(Partner.id).where(Partner.slug == partner)))
    stmt = stmt.order_by(I.name)
    return paginate(db, stmt, p.page, p.page_size, lambda x: pr.instructor_out(db, x))


@router.get("/instructors/{slug}", response_model=InstructorOut, summary="Detail instruktur")
def get_instructor(slug: str, db: Session = Depends(get_db)):
    i = db.scalar(select(Instructor).where(Instructor.slug == slug, vis.instructor_ok()))
    if not i:
        raise ApiError(404, "NOT_FOUND", "Instruktur tidak ditemukan.")
    return pr.instructor_out(db, i)


# ---- Gerakan ----
@router.get("/movements", response_model=Page[MovementSummary], summary="Referensi gerakan")
def list_movements(q: str | None = None, tradition: str | None = None, partner: str | None = None,
                   practice_mode: str | None = None, level: str | None = None,
                   safety_category: str | None = None, partner_verified: bool | None = None,
                   p: PageParams = Depends(), db: Session = Depends(get_db)):
    """Perpustakaan gerakan: hanya versi `published`. Filter: tradisi, perguruan, tingkat, kategori keselamatan,
    status verifikasi mitra."""
    M = Movement
    stmt = select(M).where(vis.movement_ok())
    if (c := search_cond(q, M.name_id, M.name_local, M.description)) is not None:
        stmt = stmt.where(c)
    if practice_mode:
        stmt = stmt.where(M.practice_mode == practice_mode)
    if level:
        stmt = stmt.where(M.level == level)
    if safety_category:
        stmt = stmt.where(M.safety_category == safety_category)
    if partner:
        stmt = stmt.where(M.partner_id.in_(select(Partner.id).where(Partner.slug == partner)))
    if partner_verified is not None:
        ver = select(Partner.id).where(Partner.verification_status == "verified", Partner.is_demo.is_(False))
        stmt = stmt.where(M.partner_id.in_(ver) if partner_verified else M.partner_id.not_in(ver))
    if tradition:
        stmt = stmt.where(M.tradition_id.in_(
            select(CulturalTradition.id).where(CulturalTradition.slug == tradition)))
    stmt = stmt.order_by(M.name_id)
    return paginate(db, stmt, p.page, p.page_size, lambda x: pr.movement_summary(db, x))


def get_movement_row(db: Session, movement_id: str) -> Movement:
    try:
        mid = uuid.UUID(movement_id)
    except ValueError as exc:
        raise ApiError(404, "NOT_FOUND", "Gerakan tidak ditemukan.") from exc
    m = db.scalar(select(Movement).where(Movement.id == mid, vis.movement_ok()))
    if not m:
        raise ApiError(404, "NOT_FOUND", "Gerakan tidak ditemukan.")
    return m


@router.get("/movements/{movement_id}", response_model=MovementOut, summary="Detail gerakan (versi tayang)")
def get_movement(movement_id: str, db: Session = Depends(get_db)):
    return pr.movement_out(db, get_movement_row(db, movement_id))


@router.get("/movements/{movement_id}/versions", response_model=list[VersionPublicOut],
            summary="Riwayat versi publik (changelog)")
def movement_versions(movement_id: str, db: Session = Depends(get_db)):
    from app.services import movement_public as mp
    return mp.versions_out(db, get_movement_row(db, movement_id))


# ---- Kurikulum (daftar) ----
@router.get("/courses", response_model=Page[CourseSummary], summary="Katalog kurikulum/akademi")
def list_courses(
    q: str | None = None, level: str | None = None, tradition: str | None = None,
    partner: str | None = None,
    sort: str | None = Query(None, description="title | -title | newest | shortest"),
    p: PageParams = Depends(), db: Session = Depends(get_db),
):
    C = Course
    stmt = select(C).where(vis.course_ok())
    if (c := search_cond(q, C.title, C.summary)) is not None:
        stmt = stmt.where(c)
    if level:
        stmt = stmt.where(C.level == level)
    if tradition:
        stmt = stmt.where(C.tradition_id.in_(
            select(CulturalTradition.id).where(CulturalTradition.slug == tradition)))
    if partner:
        stmt = stmt.where(C.partner_id.in_(select(Partner.id).where(Partner.slug == partner)))
    stmt = apply_sort(stmt, sort, {
        "title": [C.title], "-title": [C.title.desc()],
        "newest": [C.created_at.desc(), C.title],
        "shortest": [C.estimated_minutes.asc().nulls_last(), C.title]}, "title")
    return paginate(db, stmt, p.page, p.page_size, lambda x: pr.course_summary(db, x))
