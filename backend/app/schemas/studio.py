"""Skema Instructor & Partner Studio (docs/INSTRUCTOR_PARTNER_CONTRACT.md). `extra=forbid` pada semua input."""

import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.manage import Short, Slug, Text, Url

Level = Literal["beginner", "intermediate", "advanced"]
Safety = Literal["solo_beginner", "supervised_practice", "contact_practice", "weapon_related", "restricted"]
License = Literal["instructor_owned", "partner_permission", "other_written_permission"]
Note = Annotated[str, Field(max_length=2000)]
Opt200 = Annotated[str, Field(max_length=200)]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ---------- mitra ----------
class PartnerCreate(_In):
    name: Short
    slug: Slug | None = None
    partner_type: Literal["school", "community", "institution", "individual_master"]
    region: Opt200 | None = None
    city: Opt200 | None = None
    official_description: Text | None = None
    responsible_name: Opt200 | None = None
    responsible_role: Opt200 | None = None
    responsible_contact: Opt200 | None = None
    contact_email: Annotated[str, Field(max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")] | None = None
    contact_phone: Annotated[str, Field(max_length=40)] | None = None
    public_listing_consent: bool = False


class PartnerPatch(_In):
    name: Short | None = None
    partner_type: Literal["school", "community", "institution", "individual_master"] | None = None
    region: Opt200 | None = None
    city: Opt200 | None = None
    official_description: Text | None = None
    responsible_name: Opt200 | None = None
    responsible_role: Opt200 | None = None
    responsible_contact: Opt200 | None = None
    contact_email: Annotated[str, Field(max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")] | None = None
    contact_phone: Annotated[str, Field(max_length=40)] | None = None
    public_listing_consent: bool | None = None


class MemberIn(_In):
    email: Annotated[str, Field(max_length=320)]
    role: Literal["manager", "instructor"] = "instructor"


class PartnerAction(_In):
    action: Literal["submit", "verify", "reject", "suspend", "reopen", "reinstate", "publish_listing", "unlist"]
    note: Note | None = None
    evidence_ref: Annotated[str, Field(max_length=2000)] | None = None


# ---------- gerakan ----------
class PhaseIn(_In):
    name: Short
    instruction: Annotated[str, Field(min_length=1, max_length=5000)]
    body_focus: list[Annotated[str, Field(min_length=1, max_length=80)]] = Field(default_factory=list, max_length=20)
    safety_note: Annotated[str, Field(max_length=2000)] | None = None
    start_ms: Annotated[int, Field(ge=0, le=3_600_000)] | None = None
    end_ms: Annotated[int, Field(ge=0, le=3_600_000)] | None = None


class PhasesPut(_In):
    phases: list[PhaseIn] = Field(max_length=40)


class _DocFields(_In):
    name_id: Short | None = None
    name_local: Opt200 | None = None
    level: Level | None = None
    safety_category: Safety | None = None
    prerequisites: Text | None = None
    learning_context: Text | None = None
    description: Text | None = None
    terminology_notes: Text | None = None
    common_mistakes: list[Annotated[str, Field(min_length=1, max_length=1000)]] | None = Field(
        default=None, max_length=30
    )
    safety_guidance: Text | None = None
    relevant_body_parts: list[Annotated[str, Field(min_length=1, max_length=80)]] | None = Field(
        default=None, max_length=40
    )
    relevant_landmarks: list[Annotated[int, Field(ge=0, le=32)]] | None = Field(default=None, max_length=33)
    source_citation: Annotated[str, Field(max_length=2000)] | None = None
    source_url: Url | None = None
    author_declaration: bool | None = None
    rights_holder: Annotated[str, Field(max_length=300)] | None = None
    license_type: License | None = None
    usage_scope: Text | None = None
    changelog: Annotated[str, Field(max_length=4000)] | None = None

    @field_validator("relevant_landmarks")
    @classmethod
    def _uniq(cls, v):
        return sorted(set(v)) if v is not None else v


class DocumentPatch(_DocFields):
    pass


class MovementCreate(_DocFields):
    name_id: Short  # wajib
    tradition_id: uuid.UUID
    partner_id: uuid.UUID
    slug: Slug | None = None


class DocTransition(_In):
    action: Literal[
        "submit", "curator_review", "confirm_partner", "request_revision", "reject", "approve", "publish", "archive"
    ]
    note: Note | None = None
    evidence_ref: Annotated[str, Field(max_length=2000)] | None = None


class LessonLinkIn(_In):
    pass


# ---------- media ----------
class MediaPatch(_In):
    title: Short | None = None
    access_level: Literal["private", "reviewers", "public"] | None = None
    consent_status: Literal["verified", "rejected", "revoked"] | None = None
    permission_evidence_ref: Annotated[str, Field(max_length=2000)] | None = None
    retention_until: date | None = None


# ---------- anotasi ----------
class AnnotationIn(_In):
    media_id: uuid.UUID | None = None
    fixture_key: Literal["demo-synthetic"] | None = None
    phase_id: uuid.UUID | None = None
    kind: Literal["phase_marker", "note"] = "phase_marker"
    timestamp_ms: Annotated[int, Field(ge=0, le=3_600_000)]
    label: Short
    note: Annotated[str, Field(max_length=2000)] | None = None
    model_version: Annotated[str, Field(max_length=120)] | None = None
    source_note: Annotated[str, Field(max_length=2000)] | None = None


class AnnotationPatch(_In):
    label: Short | None = None
    note: Annotated[str, Field(max_length=2000)] | None = None
    phase_id: uuid.UUID | None = None
    timestamp_ms: Annotated[int, Field(ge=0, le=3_600_000)] | None = None
    review_status: Literal["accepted", "rejected", "pending"] | None = None


# ---------- output publik ----------
class PhaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    order_index: int
    name: str
    instruction: str
    body_focus: list
    safety_note: str | None
    start_ms: int | None = None
    end_ms: int | None = None


class PublicMediaOut(BaseModel):
    id: uuid.UUID
    kind: str
    title: str
    url: str
    rights_holder: str
    source_description: str
    usage_scope: str
    is_demo: bool


class DocumentOut(BaseModel):
    """Dokumentasi gerakan yang tayang (hanya isi yang ditulis instruktur)."""

    id: uuid.UUID
    version_no: int
    name_id: str
    name_local: str | None
    level: str | None
    safety_category: str | None
    prerequisites: str | None
    learning_context: str | None
    description: str | None
    terminology_notes: str | None
    common_mistakes: list
    safety_guidance: str | None
    relevant_body_parts: list
    relevant_landmarks: list
    phases: list[PhaseOut]
    media: list[PublicMediaOut]
    rights_holder: str | None
    license_type: str | None
    usage_scope: str | None
    changelog: str | None
    published_at: datetime | None
    authors: list[str]


class VersionPublicOut(BaseModel):
    version_no: int
    status: str
    changelog: str | None
    published_at: datetime | None
    is_current: bool
