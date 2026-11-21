"""Membangun objek respons publik (provenance, relasi) dari model."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Course,
    CulturalTradition,
    Instructor,
    Lesson,
    Movement,
    Partner,
    User,
)
from app.services import visibility as vis

LABEL_DEMO = "[DEMO] Contoh teknis — belum diverifikasi mitra"  # hanya muncul bila EXPOSE_DEMO_DATA (dev/tes)
LABEL_UNVERIFIED = "Belum dikonfirmasi mitra"
LABEL_VERIFIED = "Terverifikasi oleh mitra"
LABEL_SOURCE_BACKED = "Disusun Redaksi SILATARA dari sumber terbuka"
EDITORIAL_ATTRIBUTION = "Redaksi SILATARA"


def _is_source_backed(obj) -> bool:
    return getattr(obj, "content_basis", None) == "source_backed"


def _partner_ref(db: Session, obj, partner_id):
    """Pengetahuan berbasis sumber tidak diatribusikan ke mitra (partner internal redaksi bukan perguruan)."""
    if _is_source_backed(obj):
        return None
    return db.get(Partner, partner_id) if partner_id else None


def provenance(db: Session, obj) -> dict:
    # "Terverifikasi oleh mitra" hanya bila: bukan demo, sudah verified/published,
    # dan ada bukti persetujuan tercatat.
    partner_verified = bool(
        not obj.is_demo
        and obj.status in ("verified", "published")
        and obj.approval_evidence_ref
        and obj.approved_by_user_id
    )
    source_backed = _is_source_backed(obj) and not obj.is_demo
    if source_backed:
        partner_verified = False  # terbit lewat tinjauan editorial, bukan konfirmasi mitra
    label = (
        LABEL_DEMO
        if obj.is_demo
        else LABEL_SOURCE_BACKED
        if source_backed
        else (LABEL_VERIFIED if partner_verified else LABEL_UNVERIFIED)
    )
    approver = db.get(User, obj.approved_by_user_id) if obj.approved_by_user_id else None
    return {
        "status": obj.status,
        "is_demo": obj.is_demo,
        "content_basis": getattr(obj, "content_basis", None),
        "attribution": EDITORIAL_ATTRIBUTION if source_backed else None,
        "partner_verified": partner_verified,
        "verification_label": label,
        "source_citation": obj.source_citation,
        "source_url": obj.source_url,
        "approved_by_name": approver.display_name if approver else None,
        "approved_at": obj.approved_at,
    }


def tradition_summary(db: Session, t: CulturalTradition) -> dict:
    return {**_cols(t, "id slug name local_name region public_summary content_basis"), "provenance": provenance(db, t)}


def partner_summary(db: Session, p: Partner) -> dict:
    prov = provenance(db, p)
    # Status kemitraan ditentukan oleh keputusan verifikasi admin (bukti + identitas penyetuju), bukan alur konten.
    verified = bool(not p.is_demo and p.verification_status == "verified" and p.verification_decided_by_user_id)
    decider = db.get(User, p.verification_decided_by_user_id) if p.verification_decided_by_user_id else None
    prov.update(
        partner_verified=verified,
        verification_label=LABEL_DEMO if p.is_demo else (LABEL_VERIFIED if verified else LABEL_UNVERIFIED),
        approved_by_name=decider.display_name if decider else prov["approved_by_name"],
        approved_at=p.verification_decided_at or prov["approved_at"],
    )
    return {**_cols(p, "id slug name partner_type region city official_description"), "provenance": prov}


def instructor_out(db: Session, i: Instructor) -> dict:
    partner = db.get(Partner, i.partner_id)
    return {
        **_cols(i, "id slug name bio preferred_attribution"),
        "partner_slug": partner.slug if partner else None,
        "provenance": provenance(db, i),
    }


def movement_summary(db: Session, m: Movement) -> dict:
    trad = db.get(CulturalTradition, m.tradition_id)
    part = _partner_ref(db, m, m.partner_id)
    return {
        **_cols(m, "id slug name_id name_local practice_mode assessment_enabled level safety_category content_basis"),
        "version_no": m.published_version_no,
        "tradition_slug": trad.slug if trad else None,
        "tradition_name": trad.name if trad else None,
        "partner_slug": part.slug if part else None,
        "partner_name": part.name if part else None,
        "partner_verified": bool(part and not part.is_demo and part.verification_status == "verified"),
        "provenance": provenance(db, m),
    }


def movement_out(db: Session, m: Movement, viewer=None, course=None) -> dict:
    from app.services import movement_public as mp

    return {
        **movement_summary(db, m),
        "description": m.description,
        "safety_notes": m.safety_notes,
        "document": mp.document_out(db, m, viewer=viewer, course=course),
    }


def course_summary(db: Session, c: Course, viewer=None) -> dict:
    trad = db.get(CulturalTradition, c.tradition_id)
    part = _partner_ref(db, c, c.partner_id)
    n = db.scalar(select(func.count()).select_from(Lesson).where(Lesson.course_id == c.id, vis.lesson_ok(viewer)))
    return {
        **_cols(c, "id slug title summary level estimated_minutes distribution_scope content_basis"),
        "tradition_slug": trad.slug if trad else None,
        "tradition_name": trad.name if trad else None,
        "partner_slug": part.slug if part else None,
        "partner_name": part.name if part else None,
        "lesson_count": n or 0,
        "provenance": provenance(db, c),
    }


def _cols(obj, names: str) -> dict:
    return {n: getattr(obj, n) for n in names.split()}
