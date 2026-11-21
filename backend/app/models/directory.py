"""Direktori nasional tempat & organisasi pencak silat (docs/NATIONAL_DIRECTORY_CONTRACT.md).

Prinsip: setiap tempat punya sumber terstruktur; koordinat tidak ditebak (`location_precision` membedakan titik
aktual dari penanda wilayah); data historis tidak dihapus otomatis (riwayat + status, bukan DELETE).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._mixins import IdMixin, TimestampMixin

PLACE_CATEGORIES = (
    "perguruan_branch", "perguruan_center", "padepokan", "training_center", "ipsi", "organization_office",
    "campus_unit", "community", "sports_venue", "cultural_center", "cultural_landmark",
)
PRECISIONS = ("exact", "district", "regency", "province")
PUBLIC_ACCESS = ("open", "members", "restricted", "unknown")
OPERATIONAL = ("active_unverified", "active_confirmed", "inactive", "closed", "unknown")
PUBLICATION = ("published", "review", "hidden")
SUBMISSION_KINDS = ("new_place", "correction", "contact_update", "schedule_update", "closed_report")
SUBMISSION_STATUS = (
    "submitted", "duplicate_check", "source_check", "coordinate_check", "awaiting_manager",
    "approved", "published", "rejected", "duplicate",
)


def _in(col: str, values: tuple[str, ...]) -> str:
    return f"{col} IN (" + ",".join(f"'{v}'" for v in values) + ")"


class DirectoryRegion(Base):
    """Wilayah administrasi (Kepmendagri 2025): provinsi & kabupaten/kota. Poligon tidak disimpan di DB."""

    __tablename__ = "directory_regions"
    __table_args__ = (CheckConstraint("kind IN ('provinsi','kabupaten','kota')", name="ck_dir_region_kind"),)

    code: Mapped[str] = mapped_column(String(13), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    province_code: Mapped[str | None] = mapped_column(String(2), index=True)
    capital: Mapped[str | None] = mapped_column(String(120))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)


class DirectoryOrganization(IdMixin, TimestampMixin, Base):
    __tablename__ = "directory_organizations"

    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    official_name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(80))
    organization_type: Mapped[str] = mapped_column(String(40), nullable=False)
    parent_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("directory_organizations.id", ondelete="SET NULL"))
    entity_id: Mapped[str | None] = mapped_column(String(120))
    official_website: Mapped[str | None] = mapped_column(String(500))
    sources: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")


class DirectoryPlace(IdMixin, TimestampMixin, Base):
    __tablename__ = "directory_places"
    __table_args__ = (
        CheckConstraint(_in("place_category", PLACE_CATEGORIES), name="ck_dir_place_category"),
        CheckConstraint(_in("location_precision", PRECISIONS), name="ck_dir_place_precision"),
        CheckConstraint(_in("public_access", PUBLIC_ACCESS), name="ck_dir_place_access"),
        CheckConstraint(_in("operational_status", OPERATIONAL), name="ck_dir_place_operational"),
        CheckConstraint(_in("publication_status", PUBLICATION), name="ck_dir_place_publication"),
        CheckConstraint("latitude BETWEEN -11.5 AND 6.5 AND longitude BETWEEN 94.5 AND 141.5", name="ck_dir_place_in_id"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_dir_place_confidence"),
        Index("ix_dir_place_latlng", "latitude", "longitude"),
        Index("ix_dir_place_region", "province_code", "regency_code"),
        Index("uq_dir_place_dedupe", text("lower(official_name)"), "regency_code",
              text("round(latitude::numeric, 3)"), text("round(longitude::numeric, 3)"), unique=True),
    )

    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    external_key: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    official_name: Mapped[str] = mapped_column(String(240), nullable=False)
    display_name: Mapped[str] = mapped_column(String(240), nullable=False)
    aliases: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    place_category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    organization_type: Mapped[str | None] = mapped_column(String(40))
    parent_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("directory_organizations.id", ondelete="SET NULL"), index=True)
    tradition_ids: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    style_ids: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    entity_id: Mapped[str | None] = mapped_column(String(120))
    province_code: Mapped[str] = mapped_column(String(2), ForeignKey("directory_regions.code"), nullable=False)
    regency_code: Mapped[str] = mapped_column(String(13), ForeignKey("directory_regions.code"), nullable=False)
    district: Mapped[str | None] = mapped_column(String(120))
    village: Mapped[str | None] = mapped_column(String(120))
    locality_text: Mapped[str | None] = mapped_column(String(240))
    full_address: Mapped[str | None] = mapped_column(String(400))
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location_precision: Mapped[str] = mapped_column(String(16), nullable=False)
    coordinate_check: Mapped[str | None] = mapped_column(String(60))
    venue_type: Mapped[str | None] = mapped_column(String(40))
    is_training_location: Mapped[bool | None] = mapped_column(Boolean)
    is_organization_office: Mapped[bool | None] = mapped_column(Boolean)
    practice_schedule: Mapped[list | None] = mapped_column(JSONB(none_as_null=True))  # hanya bila bersumber: [{day, time, note, source_id}]
    contact_phone: Mapped[str | None] = mapped_column(String(40))
    contact_email: Mapped[str | None] = mapped_column(String(200))
    contact_source: Mapped[str | None] = mapped_column(String(160))
    official_website: Mapped[str | None] = mapped_column(String(500))
    public_social_links: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    training_levels: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    training_categories: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    sports_listed: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    facilities: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    accessibility_information: Mapped[str | None] = mapped_column(Text)
    public_access: Mapped[str] = mapped_column(String(16), nullable=False, server_default="unknown")
    operational_status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="active_unverified")
    publication_status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="published")
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    data_conflicts: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    missing_from_latest_build: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    last_import_job: Mapped[str | None] = mapped_column(String(60))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    record_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sources: Mapped[list["DirectoryPlaceSource"]] = relationship(
        back_populates="place", cascade="all, delete-orphan", order_by="DirectoryPlaceSource.position")
    organization: Mapped[DirectoryOrganization | None] = relationship()


class DirectoryPlaceSource(IdMixin, Base):
    __tablename__ = "directory_place_sources"

    place_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("directory_places.id", ondelete="CASCADE"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(160))
    url: Mapped[str | None] = mapped_column(String(600))
    title: Mapped[str | None] = mapped_column(String(400))
    publisher: Mapped[str | None] = mapped_column(String(240))
    year: Mapped[int | None] = mapped_column(Integer)
    license: Mapped[str | None] = mapped_column(String(240))
    attribution: Mapped[str | None] = mapped_column(String(240))
    read_status: Mapped[str | None] = mapped_column(String(40))
    retrieved_at: Mapped[str | None] = mapped_column(String(20))
    supports: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")

    place: Mapped[DirectoryPlace] = relationship(back_populates="sources")


class DirectoryHeritageArea(IdMixin, TimestampMixin, Base):
    __tablename__ = "directory_heritage_areas"

    entity_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    regency_codes: Mapped[list] = mapped_column(JSONB, nullable=False)
    points: Mapped[list] = mapped_column(JSONB, nullable=False)
    locality_text: Mapped[str | None] = mapped_column(String(400))
    public_note: Mapped[str | None] = mapped_column(Text)
    sources: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")


class DirectoryImportJob(IdMixin, Base):
    __tablename__ = "directory_import_jobs"

    job_id: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(20), nullable=False)
    built_at: Mapped[str | None] = mapped_column(String(40))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    imported_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    stages: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    errors: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    result: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    import_counts: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")


class DirectoryPlaceHistory(IdMixin, Base):
    __tablename__ = "directory_place_history"

    place_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("directory_places.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    change_type: Mapped[str] = mapped_column(String(40), nullable=False)
    changes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    job_id: Mapped[str | None] = mapped_column(String(60))
    submission_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))


class DirectorySubmission(IdMixin, TimestampMixin, Base):
    """Kiriman publik/pengelola. Tidak pernah terbit otomatis; `contact_email` pengirim privat (tidak tampil publik)."""

    __tablename__ = "directory_submissions"
    __table_args__ = (
        CheckConstraint(_in("kind", SUBMISSION_KINDS), name="ck_dir_sub_kind"),
        CheckConstraint(_in("status", SUBMISSION_STATUS), name="ck_dir_sub_status"),
        CheckConstraint("submitter_relation IN ('pengelola','anggota','publik')", name="ck_dir_sub_relation"),
        CheckConstraint("kind = 'new_place' OR place_id IS NOT NULL", name="ck_dir_sub_place_required"),
    )

    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="submitted", index=True)
    place_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("directory_places.id", ondelete="SET NULL"), index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(600))
    submitter_relation: Mapped[str] = mapped_column(String(16), nullable=False)
    submitter_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    contact_email: Mapped[str | None] = mapped_column(String(200))
    duplicate_candidates: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    checks: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
