"""Izin Studio berbasis keanggotaan mitra. Peran `manager` adalah peran keanggotaan (bukan peran global)."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import Movement, Partner, PartnerMember, User

STAFF = {"curator", "admin"}
STUDIO_ROLES = ("instructor", "curator", "admin")


def is_staff(user: User) -> bool:
    return user.role in STAFF


def member_role(db: Session, user: User, partner_id) -> str | None:
    return db.scalar(
        select(PartnerMember.role).where(
            PartnerMember.partner_id == partner_id, PartnerMember.user_id == user.id, PartnerMember.status == "active"
        )
    )


def my_partner_ids(db: Session, user: User) -> list[uuid.UUID]:
    return list(
        db.scalars(
            select(PartnerMember.partner_id).where(PartnerMember.user_id == user.id, PartnerMember.status == "active")
        )
    )


def is_manager(db: Session, user: User, partner_id) -> bool:
    return member_role(db, user, partner_id) == "manager"


def can_see_partner(db: Session, user: User, partner_id) -> bool:
    return is_staff(user) or member_role(db, user, partner_id) is not None


def can_edit_partner(db: Session, user: User, partner_id) -> bool:
    return user.role == "admin" or is_manager(db, user, partner_id)


def parse_id(value, what: str = "Data") -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise ApiError(404, "NOT_FOUND", f"{what} tidak ditemukan.") from exc


def get_partner(db: Session, user: User, partner_id, *, edit: bool = False) -> Partner:
    """404 (bukan 403) untuk non-anggota agar keberadaan mitra lain tidak bocor."""
    p = db.get(Partner, parse_id(partner_id, "Mitra"))
    if not p or p.deleted_at or not can_see_partner(db, user, p.id):
        raise ApiError(404, "NOT_FOUND", "Mitra tidak ditemukan.")
    if edit and not can_edit_partner(db, user, p.id):
        raise ApiError(403, "FORBIDDEN", "Hanya penanggung jawab (manager) mitra atau admin yang dapat melakukannya.")
    return p


def get_movement(db: Session, user: User, movement_id) -> Movement:
    m = db.get(Movement, parse_id(movement_id, "Gerakan"))
    if not m or m.deleted_at or not can_see_partner(db, user, m.partner_id):
        raise ApiError(404, "NOT_FOUND", "Gerakan tidak ditemukan.")
    return m
