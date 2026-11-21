import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.studio import DocumentOut


class Provenance(BaseModel):
    """Asal-usul & status verifikasi. `verification_label` tidak boleh menyiratkan mitra
    menyetujui bila belum ada bukti (data demo / tanpa approval_evidence_ref)."""

    status: str
    is_demo: bool
    partner_verified: bool
    verification_label: str
    source_citation: str | None = None
    source_url: str | None = None
    approved_by_name: str | None = None
    approved_at: datetime | None = None
    # ADR-0008: source_backed | official_curriculum | partner_restricted; `attribution` diisi untuk pengetahuan redaksi
    content_basis: str | None = None
    attribution: str | None = None


class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TraditionSummary(_Base):
    id: uuid.UUID
    slug: str
    name: str
    local_name: str | None
    region: str | None
    public_summary: str | None
    content_basis: str = "official_curriculum"
    provenance: Provenance


class PartnerSummary(_Base):
    id: uuid.UUID
    slug: str
    name: str
    partner_type: str
    region: str | None
    city: str | None
    official_description: str | None
    provenance: Provenance


class InstructorOut(_Base):
    id: uuid.UUID
    slug: str
    name: str
    bio: str | None
    preferred_attribution: str | None
    partner_slug: str | None = None
    provenance: Provenance


class MovementSummary(_Base):
    id: uuid.UUID
    slug: str
    name_id: str
    name_local: str | None
    practice_mode: str
    assessment_enabled: bool
    tradition_slug: str | None = None
    tradition_name: str | None = None
    partner_slug: str | None = None
    partner_name: str | None = None
    partner_verified: bool = False
    level: str | None = None
    safety_category: str | None = None
    version_no: int | None = None
    content_basis: str = "official_curriculum"
    provenance: Provenance


class MovementOut(MovementSummary):
    description: str | None
    safety_notes: str | None
    document: DocumentOut | None = None


class CourseSummary(_Base):
    id: uuid.UUID
    slug: str
    title: str
    summary: str | None
    level: str
    estimated_minutes: int | None
    distribution_scope: str = "public"  # public | pilot_private (privat hanya tampil bagi yang berhak)
    tradition_slug: str | None = None
    tradition_name: str | None = None
    partner_slug: str | None = None
    partner_name: str | None = None
    lesson_count: int = 0
    content_basis: str = "official_curriculum"
    provenance: Provenance


class LessonRef(_Base):
    id: uuid.UUID
    slug: str
    title: str
    order_index: int
    estimated_minutes: int | None
    completed: bool | None = None  # hanya diisi untuk pengguna yang mendaftar


class ModuleOut(_Base):
    id: uuid.UUID
    title: str
    summary: str | None
    order_index: int
    lessons: list[LessonRef] = Field(default_factory=list)


class CourseDetail(CourseSummary):
    safety_notes: str | None
    instructor: InstructorOut | None
    modules: list[ModuleOut]
    enrollment: "EnrollmentState | None" = None


class TraditionDetail(TraditionSummary):
    access_scope: str
    partners: list[PartnerSummary]
    courses: list[CourseSummary]
    movements: list[MovementSummary]


class PartnerDetail(PartnerSummary):
    traditions: list[TraditionSummary]
    instructors: list[InstructorOut]
    courses: list[CourseSummary]


class MaterialOut(_Base):
    id: uuid.UUID
    kind: str
    title: str
    content: str | None
    url: str | None
    attribution_text: str


class ProgressOut(BaseModel):
    completed: int
    total: int
    percent: int


class EnrollmentState(BaseModel):
    status: str
    enrolled_at: datetime
    completed_at: datetime | None
    progress: ProgressOut
    last_lesson_slug: str | None = None
    next_lesson_slug: str | None = None


class LessonDetail(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    objective: str | None
    body: str | None
    safety_notes: str | None
    estimated_minutes: int | None
    module_title: str
    course: CourseSummary
    movement: MovementOut | None
    materials: list[MaterialOut]
    prev_lesson: LessonRef | None
    next_lesson: LessonRef | None
    provenance: Provenance
    enrolled: bool
    lesson_status: str | None  # in_progress | completed | None
    practice: "LessonPractice"


class MyEnrollment(BaseModel):
    course: CourseSummary
    enrollment: EnrollmentState


class MyProgress(BaseModel):
    enrollments: list[MyEnrollment]
    totals: ProgressOut
    courses_completed: int


from app.schemas.practice import LessonPractice  # noqa: E402

LessonDetail.model_rebuild()
CourseDetail.model_rebuild()
