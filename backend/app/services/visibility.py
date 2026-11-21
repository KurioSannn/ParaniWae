"""Predikat visibilitas publik — SATU-SATUNYA tempat yang menentukan apa yang boleh tampil.

Aturan: hanya status `published`, tidak soft-deleted, data DEMO hanya bila EXPOSE_DEMO_DATA,
dan induknya (tradisi/mitra/kursus) juga publik. Draft/pending_review/verified tidak pernah bocor.

Public-first (ADR-0008): pengetahuan berbasis sumber (`content_basis='source_backed'`) yang TERBIT dapat dibaca semua
orang tanpa syarat mitra terverifikasi — terbitnya sudah melalui tinjauan editorial. Konten resmi/terbatas mitra tetap
mensyaratkan mitra terverifikasi & tampil publik.
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
from app.services import access

SOURCE_BACKED = "source_backed"


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
        or_(Movement.content_basis == SOURCE_BACKED, Movement.partner_id.in_(select(Partner.id).where(partner_ok()))),
    )


def movement_for_course(course):
    """Gerakan yang boleh ditampilkan dalam pelajaran kursus `course` (setelah akses kursus lolos).

    Kursus publik: aturan publik (`movement_ok`). Kursus privat: gerakan TERBIT yang ditautkan pengelola ke pelajaran —
    tidak mensyaratkan mitra/tradisi tampil publik (katalog publik tetap memakai `movement_ok`, jadi tidak bocor)."""
    if course.distribution_scope == access.PRIVATE:
        return and_(_published(Movement), Movement.partner_id == course.partner_id)
    return movement_ok()


def course_public_ok():
    """Kursus di katalog PUBLIK: cakupan `public` + tradisi & mitra tampil publik."""
    return and_(
        _published(Course),
        Course.distribution_scope == access.PUBLIC,
        Course.tradition_id.in_(select(CulturalTradition.id).where(tradition_ok())),
        or_(Course.content_basis == SOURCE_BACKED, Course.partner_id.in_(select(Partner.id).where(partner_ok()))),
    )


def course_ok(viewer=None, *, write: bool = False):
    """Kursus yang boleh dilihat `viewer` (None = anonim -> hanya publik; DEFAULT AMAN: privat tidak pernah bocor).

    Kursus privat TIDAK bergantung pada publikasi profil mitra/tradisi: hak akses berasal dari cohort program yang sah.
    `write=True` -> hanya hak belajar/tulis (program approved|active), bukan baca-saja historis.
    """
    pub = course_public_ok()
    if viewer is None:
        return pub
    private = and_(
        _published(Course),
        Course.distribution_scope == access.PRIVATE,
        access.private_course_clause(viewer, write=write),
    )
    return or_(pub, private) if not write else or_(pub, private)


def lesson_ok(viewer=None, *, write: bool = False):
    return and_(_published(Lesson), Lesson.course_id.in_(select(Course.id).where(course_ok(viewer, write=write))))
