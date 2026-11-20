from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import new_token, token_digest
from app.models import AuthToken, User
from app.services.auth import now


def issue(db: Session, user: User, kind: str, ttl: timedelta) -> str:
    """Terbitkan token baru; token lama sejenis yang belum dipakai dibatalkan."""
    t = now()
    for old in db.scalars(select(AuthToken).where(AuthToken.user_id == user.id, AuthToken.kind == kind,
                                                  AuthToken.used_at.is_(None))):
        old.used_at = t
    raw = new_token()  # 256-bit entropi
    db.add(AuthToken(user_id=user.id, kind=kind, token_hash=token_digest(raw), expires_at=t + ttl))
    db.flush()
    return raw


def consume(db: Session, raw: str, kind: str) -> User:
    """Tandai token terpakai (sekali pakai). Pesan galat sama untuk salah/kedaluwarsa/terpakai."""
    err = ApiError(400, "INVALID_TOKEN", "Tautan tidak valid atau sudah kedaluwarsa.")
    row = db.scalar(select(AuthToken).where(AuthToken.token_hash == token_digest(raw[:200]),
                                            AuthToken.kind == kind))
    t = now()
    if not row or row.used_at is not None or row.expires_at <= t:
        raise err
    user = db.get(User, row.user_id)
    if not user or user.status != "active":
        raise err
    row.used_at = t
    return user
