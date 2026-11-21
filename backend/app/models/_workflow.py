"""Kolom & constraint alur kerja konten (draft -> pending_review -> verified -> published).

Dipakai bersama oleh tradisi, mitra, instruktur, gerakan, kurikulum, dan pelajaran.
Hanya status `published` yang boleh tampil di katalog publik. `is_demo` menandai data contoh.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

STATUSES = ("draft", "pending_review", "needs_revision", "rejected", "verified", "published", "archived")
_STATUS_SQL = ",".join(f"'{s}'" for s in STATUSES)


def workflow_constraints(prefix: str) -> list[CheckConstraint]:
    return [
        CheckConstraint(f"status IN ({_STATUS_SQL})", name=f"ck_{prefix}_status"),
        # Provenance + pihak penyetuju wajib untuk konten non-demo yang verified/published.
        CheckConstraint(
            "is_demo OR status NOT IN ('verified','published') OR "
            "(approved_by_user_id IS NOT NULL AND approved_at IS NOT NULL "
            "AND source_citation IS NOT NULL)",
            name=f"ck_{prefix}_verified_has_provenance",
        ),
        CheckConstraint(
            "status <> 'published' OR published_at IS NOT NULL",
            name=f"ck_{prefix}_published_has_timestamp",
        ),
    ]


class WorkflowMixin:
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="draft", index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    source_citation: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(500))
    review_note: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_evidence_ref: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


#: Dasar konten (ADR-0008): membedakan pengetahuan umum berbasis sumber, kurikulum resmi mitra, dan materi terbatas.
CONTENT_BASES = ("source_backed", "official_curriculum", "partner_restricted")


def content_basis_check(table: str) -> CheckConstraint:
    return CheckConstraint(
        "content_basis IN (" + ",".join(f"'{b}'" for b in CONTENT_BASES) + ")", name=f"ck_{table}_content_basis"
    )


class ContentBasisMixin:
    content_basis: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default="official_curriculum", index=True
    )
