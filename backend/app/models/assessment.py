"""Hasil penilaian gerak (docs/MOVEMENT_ASSESSMENT_CONTRACT.md).

Hanya RINGKASAN: skor total, breakdown per kriteria/fase, dan saran. Tidak ada kolom untuk video, frame, gambar,
atau landmark — skema API menolaknya. Breakdown hanya disimpan bila pengguna menyetujui (`consent_breakdown`).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._mixins import IdMixin


class AssessmentAttempt(IdMixin, Base):
    __tablename__ = "assessment_attempts"
    __table_args__ = (
        CheckConstraint("status IN ('scored','not_assessable')", name="ck_assess_status"),
        CheckConstraint("(status = 'scored') = (total_score IS NOT NULL)", name="ck_assess_score_iff_scored"),
        CheckConstraint("total_score IS NULL OR (total_score >= 0 AND total_score <= 100)", name="ck_assess_score_range"),
        CheckConstraint("input_quality IS NULL OR (input_quality >= 0 AND input_quality <= 1)", name="ck_assess_quality_range"),
        CheckConstraint("consent_breakdown OR (criteria IS NULL AND phases IS NULL)", name="ck_assess_breakdown_needs_consent"),
        Index("ix_assess_user_movement", "user_id", "movement_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    movement_id: Mapped[str] = mapped_column(String(120), nullable=False)
    lesson_ref: Mapped[str | None] = mapped_column(String(200))
    protocol_id: Mapped[str] = mapped_column(String(120), nullable=False)
    protocol_version: Mapped[str] = mapped_column(String(20), nullable=False)
    protocol_status: Mapped[str] = mapped_column(String(40), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(160), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(20), nullable=False)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    not_assessable_reason: Mapped[str | None] = mapped_column(String(60))
    total_score: Mapped[int | None] = mapped_column(Integer)
    input_quality: Mapped[float | None] = mapped_column(Float)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    frames_analyzed: Mapped[int | None] = mapped_column(Integer)
    consent_breakdown: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    criteria: Mapped[list | None] = mapped_column(JSONB(none_as_null=True))
    phases: Mapped[list | None] = mapped_column(JSONB(none_as_null=True))
    feedback: Mapped[list | None] = mapped_column(JSONB(none_as_null=True))
