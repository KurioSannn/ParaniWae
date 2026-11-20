"""Schema input manajemen konten. `extra=forbid` mencegah mass-assignment
(status, is_demo, approved_by, dst. tidak bisa diisi lewat create/patch)."""

import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

Slug = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=120)]
Url = Annotated[str, Field(pattern=r"^https?://", max_length=500)]
Text = Annotated[str, Field(max_length=20000)]
Short = Annotated[str, Field(min_length=1, max_length=200)]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _Source(_In):
    source_citation: Annotated[str, Field(max_length=2000)] | None = None
    source_url: Url | None = None


class TraditionIn(_Source):
    name: Short
    slug: Slug | None = None
    local_name: Annotated[str, Field(max_length=200)] | None = None
    region: Annotated[str, Field(max_length=120)] | None = None
    public_summary: Text | None = None
    access_scope: Literal["public", "community", "restricted"] = "restricted"


class PartnerIn(_Source):
    name: Short
    slug: Slug | None = None
    partner_type: Literal["school", "community", "institution", "individual_master"]
    region: Annotated[str, Field(max_length=120)] | None = None
    city: Annotated[str, Field(max_length=120)] | None = None
    official_description: Text | None = None
    # verification_status & public_listing_consent TIDAK dapat diisi lewat sini: verifikasi hanya lewat
    # Partner Workspace (/studio/partners/{id}/verification) dengan bukti + keputusan admin.


class InstructorIn(_Source):
    name: Short
    slug: Slug | None = None
    partner_id: uuid.UUID
    bio: Text | None = None
    preferred_attribution: Annotated[str, Field(max_length=300)] | None = None
    public_profile_consent: bool = False


class CourseIn(_Source):
    title: Short
    slug: Slug | None = None
    tradition_id: uuid.UUID
    partner_id: uuid.UUID
    instructor_id: uuid.UUID | None = None
    summary: Text | None = None
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    estimated_minutes: Annotated[int, Field(ge=1, le=100000)] | None = None
    safety_notes: Text | None = None


class LessonIn(_Source):
    title: Short
    slug: Slug | None = None
    course_id: uuid.UUID
    module_id: uuid.UUID
    movement_id: uuid.UUID | None = None
    objective: Text | None = None
    body: Text | None = None
    safety_notes: Text | None = None
    order_index: Annotated[int, Field(ge=0, le=10000)] = 0
    estimated_minutes: Annotated[int, Field(ge=1, le=100000)] | None = None


class ModuleIn(_In):
    course_id: uuid.UUID
    title: Short
    summary: Text | None = None
    order_index: Annotated[int, Field(ge=0, le=10000)] = 0


class MaterialIn(_In):
    lesson_id: uuid.UUID
    kind: Literal["text", "link"]
    title: Short
    content: Text | None = None
    url: Url | None = None
    attribution_text: Annotated[str, Field(min_length=1, max_length=500)]
    permission_ref: Annotated[str, Field(max_length=2000)] | None = None
    order_index: Annotated[int, Field(ge=0, le=10000)] = 0


def make_patch(cls: type[BaseModel]) -> type[BaseModel]:
    fields = {}
    for n, f in cls.model_fields.items():
        ann = Annotated[f.annotation, *f.metadata] if f.metadata else f.annotation
        fields[n] = (ann | None, None)
    return create_model(cls.__name__ + "Patch", __base__=_In, **fields)  # type: ignore[call-overload]


class TransitionIn(_In):
    action: Literal["submit", "approve", "reject", "publish", "unpublish", "archive", "restore"]
    note: Annotated[str, Field(max_length=2000)] | None = None
    approval_evidence_ref: Annotated[str, Field(max_length=2000)] | None = None


class AdminUserPatch(_In):
    role: Literal["learner", "instructor", "curator", "admin"] | None = None
    status: Literal["active", "suspended"] | None = None
