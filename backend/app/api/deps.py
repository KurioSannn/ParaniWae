from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import ApiError
from app.core.security import constant_time_equals, token_digest
from app.models import Session, User
from app.services.auth import now

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


@dataclass
class AuthContext:
    user: User
    session: Session


def load_auth(request: Request, db: DbSession) -> AuthContext | None:
    s = get_settings()
    token = request.cookies.get(s.session_cookie_name)
    if not token:
        return None
    row = db.scalar(select(Session).where(Session.token_hash == token_digest(token)))
    t = now()
    if (
        not row
        or row.revoked_at
        or row.expires_at <= t
        or row.last_seen_at < t - timedelta(hours=s.session_idle_hours)
    ):
        return None
    user = db.get(User, row.user_id)
    if not user or user.status != "active":
        return None
    if row.last_seen_at < t - timedelta(minutes=5):
        row.last_seen_at = t
        db.commit()
    return AuthContext(user=user, session=row)


def optional_auth(request: Request, db: DbSession = Depends(get_db)) -> AuthContext | None:
    return load_auth(request, db)


def auth_required(*roles: str):
    """Dependency: wajib login; mutasi wajib CSRF; opsional pembatasan peran."""

    def dep(request: Request, db: DbSession = Depends(get_db)) -> AuthContext:
        ctx = load_auth(request, db)
        if ctx is None:
            raise ApiError(401, "UNAUTHENTICATED", "Silakan masuk terlebih dahulu.")
        if request.method not in SAFE_METHODS:
            sent = request.headers.get("x-csrf-token", "")
            if not sent or not constant_time_equals(sent, ctx.session.csrf_token):
                raise ApiError(403, "CSRF_FAILED", "Token CSRF tidak valid atau tidak ada.")
        if roles and ctx.user.role not in roles:
            raise ApiError(403, "FORBIDDEN", "Anda tidak memiliki izin untuk tindakan ini.")
        return ctx

    return dep


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, le=10_000),
        page_size: int = Query(12, ge=1, le=100),
    ):
        self.page, self.page_size = page, page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
