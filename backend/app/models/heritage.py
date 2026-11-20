import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._mixins import IdMixin, TimestampMixin
from app.models._workflow import WorkflowMixin, workflow_constraints


class CulturalTradition(WorkflowMixin, IdMixin, TimestampMixin, Base):
    """Tradisi/aliran. Tidak diratakan menjadi satu standar universal (CLAUDE.md aturan 4)."""

    __tablename__ = "cultural_traditions"
    __table_args__ = (
        CheckConstraint(
            "access_scope IN ('public','community','restricted')", name="ck_traditions_access"
        ),
        *workflow_constraints("traditions"),
    )

    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    local_name: Mapped[str | None] = mapped_column(String(200))
    region: Mapped[str | None] = mapped_column(String(120))
    public_summary: Mapped[str | None] = mapped_column(Text)
    access_scope: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="restricted"
    )


class Instructor(WorkflowMixin, IdMixin, TimestampMixin, Base):
    """Instruktur/maestro. Profil publik hanya dengan persetujuan (public_profile_consent)."""

    __tablename__ = "instructors"
    __table_args__ = (
        CheckConstraint(
            "NOT (status = 'published' AND NOT is_demo) OR public_profile_consent",
            name="ck_instructors_published_needs_consent",
        ),
        *workflow_constraints("instructors"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partners.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Menghubungkan profil publik instruktur ke akun (opsional; unik).
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), unique=True
    )
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    preferred_attribution: Mapped[str | None] = mapped_column(String(300))
    public_profile_consent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )


class TraditionPartner(IdMixin, TimestampMixin, Base):
    """Relasi tradisi <-> mitra (siapa pemegang/pengajar)."""

    __tablename__ = "tradition_partners"
    __table_args__ = (
        UniqueConstraint("tradition_id", "partner_id", name="uq_tradition_partner"),
        CheckConstraint(
            "relationship_type IN ('custodian','teaching_partner','research_partner')",
            name="ck_tradition_partners_type",
        ),
    )

    tradition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cultural_traditions.id", ondelete="CASCADE"), index=True
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), index=True
    )
    relationship_type: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default="teaching_partner"
    )


class Movement(WorkflowMixin, IdMixin, TimestampMixin, Base):
    """Gerakan. Hanya `solo_beginner` yang boleh untuk latihan AI tanpa pengawasan."""

    __tablename__ = "movements"
    __table_args__ = (
        UniqueConstraint("tradition_id", "slug", name="uq_movements_tradition_slug"),
        CheckConstraint(
            "practice_mode IN ('solo_beginner','supervised_only','not_for_practice')",
            name="ck_movements_practice_mode",
        ),
        # Invarian 3 (docs/DATA_MODEL.md): penilaian AI hanya untuk solo_beginner yang disetujui.
        CheckConstraint(
            "NOT assessment_enabled OR (practice_mode = 'solo_beginner' "
            "AND status IN ('verified','published'))",
            name="ck_movements_assessment_requires_safe_approved",
        ),
        *workflow_constraints("movements"),
    )

    tradition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cultural_traditions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    name_local: Mapped[str | None] = mapped_column(String(200))
    name_id: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    safety_notes: Mapped[str | None] = mapped_column(Text)
    practice_mode: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default="not_for_practice"
    )
    assessment_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    # Penunjuk ke versi dokumentasi yang TAYANG + denormalisasi untuk filter/eligibility (disinkronkan saat publish).
    published_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movement_documents.id", ondelete="SET NULL", use_alter=True,
                                       name="fk_movements_published_document")
    )
    published_version_no: Mapped[int | None] = mapped_column(Integer)
    level: Mapped[str | None] = mapped_column(String(16))
    safety_category: Mapped[str | None] = mapped_column(String(24))


class MovementRubric(IdMixin, Base):
    """Rubrik bertingkat versi (belum dipakai; menunggu persetujuan instruktur mitra)."""

    __tablename__ = "movement_rubrics"
    __table_args__ = (
        UniqueConstraint("movement_id", "version", name="uq_rubrics_movement_version"),
        CheckConstraint(
            "status IN ('draft','in_review','approved','retired')", name="ck_rubrics_status"
        ),
        CheckConstraint(
            "status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL "
            "AND approval_evidence_ref IS NOT NULL)",
            name="ck_rubrics_approved_has_evidence",
        ),
    )

    movement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movements.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="draft")
    approved_by: Mapped[str | None] = mapped_column(String(200))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_evidence_ref: Mapped[str | None] = mapped_column(Text)
