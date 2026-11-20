import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._mixins import IdMixin, TimestampMixin
from app.models._workflow import WorkflowMixin, workflow_constraints


class Partner(WorkflowMixin, IdMixin, TimestampMixin, Base):
    """Perguruan/komunitas/maestro mitra.

    `verification_status` = verifikasi identitas mitra (terpisah dari status alur konten).
    Direktori publik non-demo hanya untuk mitra terverifikasi + berizin (DATA_MODEL invarian 5).
    """

    __tablename__ = "partners"
    __table_args__ = (
        CheckConstraint(
            "partner_type IN ('school','community','institution','individual_master')",
            name="ck_partners_type",
        ),
        CheckConstraint(
            "verification_status IN ('draft','pending_verification','verified','rejected','suspended')",
            name="ck_partners_verification",
        ),
        # Verifikasi wajib menyimpan identitas penyetuju + waktu keputusan (bukan sekadar mengisi formulir).
        CheckConstraint(
            "verification_status <> 'verified' OR is_demo OR "
            "(verification_decided_by_user_id IS NOT NULL AND verification_decided_at IS NOT NULL)",
            name="ck_partners_verified_has_decider",
        ),
        CheckConstraint(
            "NOT public_listing_consent OR verification_status = 'verified'",
            name="ck_partners_public_requires_verified",
        ),
        *workflow_constraints("partners"),
    )

    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    partner_type: Mapped[str] = mapped_column(String(32), nullable=False)
    region: Mapped[str | None] = mapped_column(String(120))
    city: Mapped[str | None] = mapped_column(String(120))
    official_description: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default="draft"
    )
    responsible_name: Mapped[str | None] = mapped_column(String(200))
    responsible_role: Mapped[str | None] = mapped_column(String(120))
    responsible_contact: Mapped[str | None] = mapped_column(String(320))
    contact_email: Mapped[str | None] = mapped_column(String(320))
    contact_phone: Mapped[str | None] = mapped_column(String(40))
    verification_decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    verification_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_note: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    public_listing_consent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
