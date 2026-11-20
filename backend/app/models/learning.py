import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._mixins import IdMixin, TimestampMixin
from app.models._workflow import WorkflowMixin, workflow_constraints

LEVELS = ("beginner", "intermediate", "advanced")


class Course(WorkflowMixin, IdMixin, TimestampMixin, Base):
    """Kurikulum / kelas. Terikat ke satu tradisi dan mitra (tidak diratakan lintas aliran)."""

    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("level IN ('beginner','intermediate','advanced')", name="ck_courses_level"),
        *workflow_constraints("courses"),
    )

    tradition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cultural_traditions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partners.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    instructor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instructors.id", ondelete="SET NULL")
    )
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(16), nullable=False, server_default="beginner")
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)
    safety_notes: Mapped[str | None] = mapped_column(Text)


class CourseModule(IdMixin, TimestampMixin, Base):
    """Modul dalam kurikulum. Tidak punya alur sendiri; mengikuti status kursus induknya."""

    __tablename__ = "course_modules"
    __table_args__ = (
        UniqueConstraint("id", "course_id", name="uq_modules_id_course"),
        UniqueConstraint("course_id", "order_index", name="uq_modules_course_order"),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)


class Lesson(WorkflowMixin, IdMixin, TimestampMixin, Base):
    """Pelajaran. Modul dan kursus dijamin konsisten lewat FK komposit."""

    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint("id", "course_id", name="uq_lessons_id_course"),
        UniqueConstraint("course_id", "slug", name="uq_lessons_course_slug"),
        ForeignKeyConstraint(
            ["module_id", "course_id"],
            ["course_modules.id", "course_modules.course_id"],
            name="fk_lessons_module_course",
            ondelete="CASCADE",
        ),
        *workflow_constraints("lessons"),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    movement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movements.id", ondelete="SET NULL")
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    safety_notes: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)


class LessonMaterial(IdMixin, TimestampMixin, Base):
    """Materi pendukung. Atribusi wajib; tidak ada media yang di-host tanpa izin tercatat."""

    __tablename__ = "lesson_materials"
    __table_args__ = (
        CheckConstraint("kind IN ('text','link')", name="ck_materials_kind"),
        CheckConstraint("kind <> 'link' OR url IS NOT NULL", name="ck_materials_link_has_url"),
    )

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(8), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(500))
    attribution_text: Mapped[str] = mapped_column(String(500), nullable=False)
    permission_ref: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class Enrollment(IdMixin, TimestampMixin, Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_enrollment_user_course"),
        UniqueConstraint("id", "course_id", name="uq_enrollments_id_course"),
        CheckConstraint("status IN ('active','completed','dropped')", name="ck_enrollments_status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default="active")
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="SET NULL")
    )


class LessonProgress(IdMixin, TimestampMixin, Base):
    """Progres per pelajaran. FK komposit menjamin pelajaran milik kursus yang diikuti user."""

    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_progress_user_lesson"),
        CheckConstraint("status IN ('in_progress','completed')", name="ck_progress_status"),
        CheckConstraint(
            "status <> 'completed' OR completed_at IS NOT NULL", name="ck_progress_completed_at"
        ),
        ForeignKeyConstraint(
            ["enrollment_id", "course_id"],
            ["enrollments.id", "enrollments.course_id"],
            name="fk_progress_enrollment_course",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["lesson_id", "course_id"],
            ["lessons.id", "lessons.course_id"],
            name="fk_progress_lesson_course",
            ondelete="CASCADE",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    enrollment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    lesson_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
