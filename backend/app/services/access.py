"""Otorisasi akses konten PILOT PRIVAT — satu tempat, dipakai semua jalur (katalog, kursus, pelajaran, progres, latihan, media).

Prinsip (docs/PRIVATE_PILOT_ACCESS.md): visibilitas PROFIL mitra (direktori publik) terpisah dari HAK AKSES materi. Kursus
`pilot_private` hanya terlihat oleh:
  - peserta AKTIF cohort yang memakai kursus itu, selama program `approved|active` (baca+tulis) atau `completed` (baca saja);
  - pengelola yang sah: manager mitra pemilik kursus, instruktur/penanggung jawab yang ditugaskan pada cohort/program yang
    memakai kursus itu, pembuat kursus, serta kurator/admin (pratinjau & review) — hanya baca.
Undangan yang belum diterima, anggota yang keluar/dikeluarkan, program draft/pending/cancelled/archived TIDAK memberi akses.
"""

from sqlalchemy import ColumnElement, and_, or_, select, true

from app.models import CohortMember, Course, PartnerMember, PilotCohort, PilotProgram, User

PROGRAM_RW = ("approved", "active")  # peserta dapat belajar, mencatat progres, berlatih
PROGRAM_RO = ("completed",)  # akses historis baca-saja
PRIVATE = "pilot_private"
PUBLIC = "public"


def member_course_ids(viewer: User, *, write: bool = False):
    statuses = PROGRAM_RW if write else PROGRAM_RW + PROGRAM_RO
    return (
        select(PilotCohort.course_id)
        .join(CohortMember, CohortMember.cohort_id == PilotCohort.id)
        .join(PilotProgram, PilotProgram.id == PilotCohort.program_id)
        .where(CohortMember.user_id == viewer.id, CohortMember.status == "active", PilotProgram.status.in_(statuses))
    )


def private_course_clause(viewer: User, *, write: bool = False) -> ColumnElement[bool]:
    """Kondisi SQL: `viewer` berhak atas kursus privat (dipakai bersama `Course.distribution_scope == 'pilot_private'`)."""
    member = Course.id.in_(member_course_ids(viewer, write=write))
    if write:
        return member
    if viewer.role in ("admin", "curator"):
        return true()
    managed = select(PartnerMember.partner_id).where(
        PartnerMember.user_id == viewer.id, PartnerMember.role == "manager", PartnerMember.status == "active"
    )
    assigned = (
        select(PilotCohort.course_id)
        .join(PilotProgram, PilotProgram.id == PilotCohort.program_id)
        .where(or_(PilotCohort.instructor_user_id == viewer.id, PilotProgram.responsible_user_id == viewer.id))
    )
    return or_(member, Course.partner_id.in_(managed), Course.id.in_(assigned), Course.created_by_user_id == viewer.id)


def entitled_member_lesson_clause(viewer: User) -> ColumnElement[bool]:
    return and_(Course.distribution_scope == PRIVATE, Course.id.in_(member_course_ids(viewer)))
