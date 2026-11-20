import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, PrimaryKeyConstraint, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._mixins import IdMixin, TimestampMixin


class Session(IdMixin, TimestampMixin, Base):
    """Sesi login. Hanya hash SHA-256 token yang disimpan."""

    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuthToken(IdMixin, TimestampMixin, Base):
    """Token sekali pakai untuk verifikasi email / reset sandi. Hanya hash SHA-256 yang disimpan."""

    __tablename__ = "auth_tokens"
    __table_args__ = (
        CheckConstraint("kind IN ('verify_email','reset_password')", name="ck_auth_tokens_kind"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RateLimit(Base):
    """Penghitung jendela tetap untuk rate limiting (kunci sudah di-hash; tanpa PII)."""

    __tablename__ = "rate_limits"
    __table_args__ = (PrimaryKeyConstraint("key", "window_start"),)

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    window_start: Mapped[int] = mapped_column(Integer, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class OutboxEmail(IdMixin, TimestampMixin, Base):
    """Kotak surat DEV (sink): email TIDAK dikirim ke mana pun. Hanya aktif saat APP_ENV=development."""

    __tablename__ = "outbox_emails"

    to_email: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
