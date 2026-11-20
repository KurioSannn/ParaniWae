from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._mixins import IdMixin, TimestampMixin

ROLES = ("learner", "instructor", "curator", "admin")


class User(IdMixin, TimestampMixin, Base):
    """Pengguna. Peran: learner, instructor, curator, admin (docs/adr/0002-authentication.md)."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('learner','instructor','curator','admin')", name="ck_users_role"
        ),
        CheckConstraint("status IN ('active','suspended')", name="ck_users_status"),
    )

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), nullable=False, server_default="learner")
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="active")
    failed_logins: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
