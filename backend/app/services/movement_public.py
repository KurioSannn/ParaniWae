"""Penyajian publik dokumentasi gerakan (hanya versi `published` dari gerakan yang lolos visibilitas)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Instructor, Movement, MovementDocument, MovementPhase, Partner, ReferenceMedia
from app.services import visibility as vis


def published_doc(db: Session, m: Movement) -> MovementDocument | None:
    if not m.published_document_id:
        return None
    d = db.get(MovementDocument, m.published_document_id)
    return d if d and d.status == "published" and not d.deleted_at else None


def _authors(db, d) -> list[str]:
    if not d.created_by_user_id:
        return []
    rows = db.scalars(select(Instructor).where(Instructor.user_id == d.created_by_user_id, vis.instructor_ok()))
    return [i.preferred_attribution or i.name for i in rows]


def _media(db, m) -> list[dict]:
    stmt = select(ReferenceMedia).where(
        ReferenceMedia.movement_id == m.id,
        ReferenceMedia.access_level == "public",
        ReferenceMedia.consent_status == "verified",
    )
    if not get_settings().expose_demo_data:
        stmt = stmt.where(ReferenceMedia.is_demo.is_(False))
    return [
        {
            "id": r.id,
            "kind": r.kind,
            "title": r.title,
            "url": f"/api/v1/media/{r.id}/file",
            "rights_holder": r.rights_holder,
            "source_description": r.source_description,
            "usage_scope": r.usage_scope,
            "is_demo": r.is_demo,
        }
        for r in db.scalars(stmt.order_by(ReferenceMedia.created_at))
    ]


def document_out(db: Session, m: Movement) -> dict | None:
    d = published_doc(db, m)
    if not d:
        return None
    ph = db.scalars(select(MovementPhase).where(MovementPhase.document_id == d.id).order_by(MovementPhase.order_index))
    return {
        **{
            k: getattr(d, k)
            for k in (
                "id",
                "version_no",
                "name_id",
                "name_local",
                "level",
                "safety_category",
                "prerequisites",
                "learning_context",
                "description",
                "terminology_notes",
                "common_mistakes",
                "safety_guidance",
                "relevant_body_parts",
                "relevant_landmarks",
                "rights_holder",
                "license_type",
                "usage_scope",
                "changelog",
                "published_at",
            )
        },
        "phases": [
            {
                "id": p.id,
                "order_index": p.order_index,
                "name": p.name,
                "instruction": p.instruction,
                "body_focus": p.body_focus,
                "safety_note": p.safety_note,
                "start_ms": p.start_ms,
                "end_ms": p.end_ms,
            }
            for p in ph
        ],
        "media": _media(db, m),
        "authors": _authors(db, d),
    }


def versions_out(db: Session, m: Movement) -> list[dict]:
    rows = db.scalars(
        select(MovementDocument)
        .where(
            MovementDocument.movement_id == m.id,
            MovementDocument.deleted_at.is_(None),
            MovementDocument.status.in_(["published", "archived"]),
            MovementDocument.published_at.is_not(None),
        )
        .order_by(MovementDocument.version_no.desc())
    )
    return [
        {
            "version_no": d.version_no,
            "status": d.status,
            "changelog": d.changelog,
            "published_at": d.published_at,
            "is_current": d.id == m.published_document_id,
        }
        for d in rows
    ]


def partner_ref(db: Session, m: Movement) -> dict | None:
    p = db.get(Partner, m.partner_id)
    return {"slug": p.slug, "name": p.name} if p else None
