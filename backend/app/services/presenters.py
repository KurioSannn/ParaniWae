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

LABEL_DEMO = "[DEMO] Contoh teknis — belum diverifikasi mitra"
LABEL_UNVERIFIED = "Belum diverifikasi mitra"
LABEL_VERIFIED = "Terverifikasi oleh mitra"


def provenance(db: Session, obj) -> dict:
    # "Terverifikasi oleh mitra" hanya bila: bukan demo, sudah verified/published,
    # dan ada bukti persetujuan tercatat.
    partner_verified = bool(
        not obj.is_demo
        and obj.status in ("verified", "published")
        and obj.approval_evidence_ref
        and obj.approved_by_user_id
    )
    label = LABEL_DEMO if obj.is_demo else (LABEL_VERIFIED if partner_verified else LABEL_UNVERIFIED)
    approver = db.get(User, obj.approved_by_user_id) if obj.approved_by_user_id else None
    return {
        "status": obj.status,
        "is_demo": obj.is_demo,
        "partner_verified": partner_verified,
        "verification_label": label,
        "source_citation": obj.source_citation,
        "source_url": obj.source_url,
        "approved_by_name": approver.display_name if approver else None,
        "approved_at": obj.approved_at,
    }


def tradition_summary(db: Session, t: CulturalTradition) -> dict:
    return {**_cols(t, "id slug name local_name region public_summary"),
            "provenance": provenance(db, t)}


def partner_summary(db: Session, p: Partner) -> dict:
    prov = provenance(db, p)
    # Status kemitraan ditentukan oleh keputusan verifikasi admin (bukti + identitas penyetuju), bukan alur konten.
    verified = bool(not p.is_demo and p.verification_status == "verified" and p.verification_decided_by_user_id)
    decider = db.get(User, p.verification_decided_by_user_id) if p.verification_decided_by_user_id else None
    prov.update(partner_verified=verified,
                verification_label=LABEL_DEMO if p.is_demo else (LABEL_VERIFIED if verified else LABEL_UNVERIFIED),
                approved_by_name=decider.display_name if decider else prov["approved_by_name"],
                approved_at=p.verification_decided_at or prov["approved_at"])
    return {**_cols(p, "id slug name partner_type region city official_description"), "provenance": prov}


def instructor_out(db: Session, i: Instructor) -> dict:
    partner = db.get(Partner, i.partner_id)
    return {**_cols(i, "id slug name bio preferred_attribution"),
            "partner_slug": partner.slug if partner else None,
            "provenance": provenance(db, i)}


def movement_summary(db: Session, m: Movement) -> dict:
    trad = db.get(CulturalTradition, m.tradition_id)
    part = db.get(Partner, m.partner_id)
    return {**_cols(m, "id slug name_id name_local practice_mode assessment_enabled level safety_category"),
            "version_no": m.published_version_no,
            "tradition_slug": trad.slug if trad else None, "tradition_name": trad.name if trad else None,
            "partner_slug": part.slug if part else None, "partner_name": part.name if part else None,
            "partner_verified": bool(part and not part.is_demo and part.verification_status == "verified"),
            "provenance": provenance(db, m)}


def movement_out(db: Session, m: Movement) -> dict:
    from app.services import movement_public as mp
    return {**movement_summary(db, m), "description": m.description, "safety_notes": m.safety_notes,
            "document": mp.document_out(db, m)}


def course_summary(db: Session, c: Course) -> dict:
    trad = db.get(CulturalTradition, c.tradition_id)
    part = db.get(Partner, c.partner_id)
    n = db.scalar(select(func.count()).select_from(Lesson)
                  .where(Lesson.course_id == c.id, vis.lesson_ok()))
    return {**_cols(c, "id slug title summary level estimated_minutes"),
            "tradition_slug": trad.slug if trad else None,
            "tradition_name": trad.name if trad else None,
            "partner_slug": part.slug if part else None,
            "partner_name": part.name if part else None,
            "lesson_count": n or 0, "provenance": provenance(db, c)}


def _cols(obj, names: str) -> dict:
    return {n: getattr(obj, n) for n in names.split()}
