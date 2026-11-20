"""Instructor & Partner Studio. Lihat docs/INSTRUCTOR_PARTNER_CONTRACT.md.

Semua isi dokumentasi berasal dari instruktur; tidak ada kolom/teks yang dibuat sistem untuk sejarah/filosofi/teknik.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._mixins import IdMixin, TimestampMixin
from app.models._workflow import WorkflowMixin, workflow_constraints

LEVELS = ("beginner", "intermediate", "advanced")
SAFETY_CATEGORIES = ("solo_beginner", "supervised_practice", "contact_practice", "weapon_related", "restricted")
LICENSE_TYPES = ("instructor_owned", "partner_permission", "other_written_permission")
EMPTY_LIST = text("'[]'::jsonb")


class PartnerMember(IdMixin, TimestampMixin, Base):
    """Keanggotaan pengguna pada organisasi mitra. Peran `manager` = partner manager (bukan peran global)."""

    __tablename__ = "partner_members"
    __table_args__ = (
        UniqueConstraint("partner_id", "user_id", name="uq_partner_member"),
        CheckConstraint("role IN ('manager','instructor')", name="ck_partner_members_role"),
        CheckConstraint("status IN ('active','removed')", name="ck_partner_members_status"),
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(12), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default="active")
    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )


class PartnerDocument(IdMixin, TimestampMixin, Base):
    """Dokumen persetujuan/identitas organisasi. PRIVAT: hanya lewat endpoint terotorisasi."""

    __tablename__ = "partner_documents"
    __table_args__ = (CheckConstraint("kind IN ('approval_letter','identity','other')", name="ck_partner_docs_kind"),)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300))
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    mime: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )


class PartnerVerificationEvent(IdMixin, TimestampMixin, Base):
    __tablename__ = "partner_verification_events"
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(24))
    to_status: Mapped[str] = mapped_column(String(24), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(Text)
    evidence_ref: Mapped[str | None] = mapped_column(Text)


class MovementDocument(WorkflowMixin, IdMixin, TimestampMixin, Base):
    """Satu baris = satu VERSI dokumentasi gerakan. Versi `published`/`archived`/`pending_review`/`verified` immutable
    (trigger DB `movement_documents_immutable`)."""

    __tablename__ = "movement_documents"
    __table_args__ = (
        UniqueConstraint("movement_id", "version_no", name="uq_movement_doc_version"),
        CheckConstraint("version_no >= 1", name="ck_movement_doc_version_pos"),
        CheckConstraint(
            "level IS NULL OR level IN ('beginner','intermediate','advanced')", name="ck_movement_doc_level"
        ),
        CheckConstraint(
            "safety_category IS NULL OR safety_category IN "
            "('solo_beginner','supervised_practice','contact_practice','weapon_related','restricted')",
            name="ck_movement_doc_safety",
        ),
        CheckConstraint(
            "license_type IS NULL OR license_type IN "
            "('instructor_owned','partner_permission','other_written_permission')",
            name="ck_movement_doc_license",
        ),
        # verified/published non-demo wajib sudah ditinjau kurator dan dikonfirmasi mitra (jejak identitas + waktu)
        CheckConstraint(
            "is_demo OR legacy_import OR status NOT IN ('verified','published') OR "
            "(curator_reviewed_by_user_id IS NOT NULL AND curator_reviewed_at IS NOT NULL "
            "AND partner_confirmed_by_user_id IS NOT NULL AND partner_confirmed_at IS NOT NULL "
            "AND approval_evidence_ref IS NOT NULL)",
            name="ck_movement_doc_verified_has_reviews",
        ),
        *workflow_constraints("movement_documents"),
        # Paling banyak satu versi tayang per gerakan (dijaga DB).
        Index("uq_movement_one_published", "movement_id", unique=True,
              postgresql_where=text("status = 'published' AND deleted_at IS NULL")),
    )
    movement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    name_id: Mapped[str] = mapped_column(String(200), nullable=False)
    name_local: Mapped[str | None] = mapped_column(String(200))
    level: Mapped[str | None] = mapped_column(String(16))
    safety_category: Mapped[str | None] = mapped_column(String(24))
    prerequisites: Mapped[str | None] = mapped_column(Text)
    learning_context: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    terminology_notes: Mapped[str | None] = mapped_column(Text)
    common_mistakes: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=EMPTY_LIST)
    safety_guidance: Mapped[str | None] = mapped_column(Text)
    relevant_body_parts: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=EMPTY_LIST)
    relevant_landmarks: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=EMPTY_LIST)
    # True = baris hasil migrasi dari tabel movements lama (tinjauan kurator/konfirmasi mitra tidak pernah tercatat).
    legacy_import: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    author_declaration: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    rights_holder: Mapped[str | None] = mapped_column(String(300))
    license_type: Mapped[str | None] = mapped_column(String(30))
    usage_scope: Mapped[str | None] = mapped_column(Text)
    changelog: Mapped[str | None] = mapped_column(Text)
    curator_reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    curator_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    partner_confirmed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    partner_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    partner_confirmation_note: Mapped[str | None] = mapped_column(Text)


class MovementPhase(IdMixin, TimestampMixin, Base):
    """Fase berurutan; jumlah & definisi ditentukan instruktur (tidak ada fase bawaan)."""

    __tablename__ = "movement_phases"
    __table_args__ = (
        UniqueConstraint("document_id", "order_index", name="uq_phase_order"),
        CheckConstraint("order_index >= 0", name="ck_phase_order_nonneg"),
        CheckConstraint("start_ms IS NULL OR end_ms IS NULL OR end_ms >= start_ms", name="ck_phase_time_order"),
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movement_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    body_focus: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=EMPTY_LIST)
    safety_note: Mapped[str | None] = mapped_column(Text)
    start_ms: Mapped[int | None] = mapped_column(Integer)
    end_ms: Mapped[int | None] = mapped_column(Integer)


class ReferenceMedia(IdMixin, TimestampMixin, Base):
    """Metadata media referensi + deklarasi hak. File di storage privat; tidak pernah URL statis publik."""

    __tablename__ = "reference_media"
    __table_args__ = (
        CheckConstraint("kind IN ('video','image')", name="ck_media_kind"),
        CheckConstraint("declaration_confirmed", name="ck_media_declared"),
        CheckConstraint("consent_status IN ('declared','verified','rejected','revoked')", name="ck_media_consent"),
        CheckConstraint("access_level IN ('private','reviewers','public')", name="ck_media_access"),
        CheckConstraint(
            "license_type IN ('instructor_owned','partner_permission','other_written_permission')",
            name="ck_media_license",
        ),
        # media publik wajib sudah diverifikasi izinnya
        CheckConstraint("access_level <> 'public' OR consent_status = 'verified'", name="ck_media_public_verified"),
    )
    movement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploader_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    kind: Mapped[str] = mapped_column(String(8), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    mime: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    rights_holder: Mapped[str] = mapped_column(String(300), nullable=False)
    source_description: Mapped[str] = mapped_column(Text, nullable=False)
    license_type: Mapped[str] = mapped_column(String(30), nullable=False)
    usage_scope: Mapped[str] = mapped_column(Text, nullable=False)
    declaration_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    permission_evidence_ref: Mapped[str | None] = mapped_column(Text)
    consent_status: Mapped[str] = mapped_column(String(10), nullable=False, server_default="declared")
    access_level: Mapped[str] = mapped_column(String(10), nullable=False, server_default="private")
    retention_until: Mapped[date | None] = mapped_column(Date)
    decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))


class MovementAnnotation(IdMixin, TimestampMixin, Base):
    """Instructor reference annotation. BUKAN ground truth ilmiah, BUKAN label akurasi/sertifikasi teknik."""

    __tablename__ = "movement_annotations"
    __table_args__ = (
        CheckConstraint("kind IN ('phase_marker','note')", name="ck_annotation_kind"),
        CheckConstraint("review_status IN ('pending','accepted','rejected')", name="ck_annotation_review"),
        CheckConstraint("timestamp_ms >= 0", name="ck_annotation_ts"),
        CheckConstraint("(media_id IS NOT NULL) <> (fixture_key IS NOT NULL)", name="ck_annotation_target"),
        CheckConstraint("fixture_key IS NULL OR fixture_key = 'demo-synthetic'", name="ck_annotation_fixture"),
    )
    movement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reference_media.id", ondelete="CASCADE"), index=True
    )
    fixture_key: Mapped[str | None] = mapped_column(String(40))
    phase_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movement_phases.id", ondelete="SET NULL")
    )
    kind: Mapped[str] = mapped_column(String(14), nullable=False)
    timestamp_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    annotator_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    model_version: Mapped[str | None] = mapped_column(String(120))
    source_note: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(10), nullable=False, server_default="pending")
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
