import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._mixins import IdMixin, TimestampMixin

MAX_MS = 86_400_000  # 24 jam


class PracticeSession(IdMixin, TimestampMixin, Base):
    """Sesi Practice Studio. HANYA metadata minimal + ringkasan agregat kualitas input.

    Tidak ada kolom untuk video, frame, foto, atau landmark — dan skema API menolak data semacam itu.
    """

    __tablename__ = "practice_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('in_progress','completed','abandoned','error')", name="ck_practice_status"),
        # ended_at terisi <=> sesi sudah berakhir
        CheckConstraint("(status = 'in_progress') = (ended_at IS NULL)", name="ck_practice_ended_iff_done"),
        CheckConstraint(
            f"active_duration_ms IS NULL OR (active_duration_ms >= 0 AND active_duration_ms <= {MAX_MS})",
            name="ck_practice_active_range",
        ),
        CheckConstraint(
            f"paused_duration_ms IS NULL OR (paused_duration_ms >= 0 AND paused_duration_ms <= {MAX_MS})",
            name="ck_practice_paused_range",
        ),
        CheckConstraint("status = 'in_progress' OR active_duration_ms IS NOT NULL",
                        name="ck_practice_done_has_duration"),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ck_practice_time_order"),
        Index("ix_practice_user_started", "user_id", "started_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="in_progress")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active_duration_ms: Mapped[int | None] = mapped_column(Integer)
    paused_duration_ms: Mapped[int | None] = mapped_column(Integer)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    client_version: Mapped[str | None] = mapped_column(String(40))
    quality_summary: Mapped[dict | None] = mapped_column(JSONB)
    error_code: Mapped[str | None] = mapped_column(String(40))


_ = text  # noqa: F841
