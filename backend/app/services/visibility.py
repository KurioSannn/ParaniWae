"""Predikat visibilitas publik — SATU-SATUNYA tempat yang menentukan apa yang boleh tampil.

Aturan: hanya status `published`, tidak soft-deleted, data DEMO hanya bila EXPOSE_DEMO_DATA,
dan induknya (tradisi/mitra/kursus) juga publik. Draft/pending_review/verified tidak pernah bocor.
"""

from sqlalchemy import and_, or_, select

from app.core.config import get_settings
from app.models import (
    Course,
    CulturalTradition,
    Instructor,
    Lesson,
    Movement,
    Partner,
)


def _published(model):
    cond = and_(model.status == "published", model.deleted_at.is_(None))
    if not get_settings().expose_demo_data:
        cond = and_(cond, model.is_demo.is_(False))
    return cond


def tradition_ok():
    return and_(_published(CulturalTradition), CulturalTradition.access_scope == "public")


def partner_ok():
    return and_(
        _published(Partner),
        or_(
            Partner.is_demo.is_(True),
            and_(Partner.verification_status == "verified", Partner.public_listing_consent.is_(True)),
        ),
    )


def instructor_ok():
    return and_(
        _published(Instructor),
        Instructor.partner_id.in_(select(Partner.id).where(partner_ok())),
    )


def movement_ok():
    return and_(
        _published(Movement),
        Movement.tradition_id.in_(select(CulturalTradition.id).where(tradition_ok())),
        Movement.partner_id.in_(select(Partner.id).where(partner_ok())),
    )


def course_ok():
    return and_(
        _published(Course),
        Course.tradition_id.in_(select(CulturalTradition.id).where(tradition_ok())),
        Course.partner_id.in_(select(Partner.id).where(partner_ok())),
    )


def lesson_ok():
    return and_(_published(Lesson), Lesson.course_id.in_(select(Course.id).where(course_ok())))
