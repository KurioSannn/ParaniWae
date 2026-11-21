"""Pilot & Impact Studio (docs/PILOT_STUDIO_CONTRACT.md). Memakai ulang enrollments/lesson_progress/practice_sessions."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
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

PROGRAM_STATUSES = ("draft", "pending_approval", "approved", "active", "completed", "cancelled", "archived")
_PS = ",".join(f"'{s}'" for s in PROGRAM_STATUSES)


def _uid(fk: str, *, null: bool = False, ondelete: str = "CASCADE", **kw):
    return mapped_column(UUID(as_uuid=True), ForeignKey(fk, ondelete=ondelete), nullable=null, **kw)


class PilotProgram(IdMixin, TimestampMixin, Base):
    __tablename__ = "pilot_programs"
    __table_args__ = (
        CheckConstraint(f"status IN ({_PS})", name="ck_pilot_programs_status"),
        CheckConstraint("capacity >= 1 AND capacity <= 5000", name="ck_pilot_programs_capacity"),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date", name="ck_pilot_programs_period"
        ),
        # Program non-demo yang disetujui/aktif/selesai wajib punya jejak penyetuju + waktu + bukti.
        CheckConstraint(
            "is_demo OR status NOT IN ('approved','active','completed') OR "
            "(approved_by_user_id IS NOT NULL AND approved_at IS NOT NULL AND approval_evidence_ref IS NOT NULL)",
            name="ck_pilot_programs_approved_has_approver",
        ),
    )
    partner_id: Mapped[uuid.UUID] = _uid("partners.id", ondelete="RESTRICT", index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    responsible_user_id: Mapped[uuid.UUID | None] = _uid("users.id", null=True, ondelete="SET NULL")
    default_course_id: Mapped[uuid.UUID | None] = _uid("courses.id", null=True, ondelete="SET NULL")
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="draft", index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    review_note: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID | None] = _uid("users.id", null=True, ondelete="SET NULL")
    approved_by_user_id: Mapped[uuid.UUID | None] = _uid("users.id", null=True, ondelete="RESTRICT")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_evidence_ref: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    anonymized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PilotCohort(IdMixin, TimestampMixin, Base):
    __tablename__ = "pilot_cohorts"
    __table_args__ = (
        CheckConstraint("status IN ('draft','open','closed','completed')", name="ck_pilot_cohorts_status"),
        CheckConstraint("capacity >= 1 AND capacity <= 2000", name="ck_pilot_cohorts_capacity"),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date", name="ck_pilot_cohorts_period"
        ),
        UniqueConstraint("program_id", "name", name="uq_pilot_cohort_name"),
    )
    program_id: Mapped[uuid.UUID] = _uid("pilot_programs.id", index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    course_id: Mapped[uuid.UUID] = _uid("courses.id", ondelete="RESTRICT")
    instructor_user_id: Mapped[uuid.UUID | None] = _uid("users.id", null=True, ondelete="SET NULL")
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default="draft")


class CohortSession(IdMixin, TimestampMixin, Base):
    __tablename__ = "cohort_sessions"
    __table_args__ = (CheckConstraint("ends_at IS NULL OR ends_at >= starts_at", name="ck_cohort_sessions_time"),)
    cohort_id: Mapped[uuid.UUID] = _uid("pilot_cohorts.id", index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    location_note: Mapped[str | None] = mapped_column(String(300))


class CohortInvitation(IdMixin, TimestampMixin, Base):
    __tablename__ = "cohort_invitations"
    __table_args__ = (
        CheckConstraint("(accepted_at IS NULL) = (accepted_by_user_id IS NULL)", name="ck_invite_accept_pair"),
    )
    cohort_id: Mapped[uuid.UUID] = _uid("pilot_cohorts.id", index=True)
    email: Mapped[str | None] = mapped_column(String(320))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_by_user_id: Mapped[uuid.UUID | None] = _uid("users.id", null=True, ondelete="SET NULL")
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by_user_id: Mapped[uuid.UUID | None] = _uid("users.id", null=True, ondelete="SET NULL")
    created_by_user_id: Mapped[uuid.UUID | None] = _uid("users.id", null=True, ondelete="SET NULL")


class CohortMember(IdMixin, TimestampMixin, Base):
    __tablename__ = "cohort_members"
    __table_args__ = (
        UniqueConstraint("cohort_id", "user_id", name="uq_cohort_member"),
        CheckConstraint("status IN ('active','withdrawn','removed')", name="ck_cohort_members_status"),
        # Satu peserta hanya boleh AKTIF di satu cohort per program (perlindungan enrollment ganda).
        Index(
            "uq_program_active_member", "program_id", "user_id", unique=True, postgresql_where=text("status = 'active'")
        ),
    )
    cohort_id: Mapped[uuid.UUID] = _uid("pilot_cohorts.id", index=True)
    program_id: Mapped[uuid.UUID] = _uid("pilot_programs.id", index=True)
    user_id: Mapped[uuid.UUID] = _uid("users.id", index=True)
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default="active")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    invitation_id: Mapped[uuid.UUID | None] = _uid("cohort_invitations.id", null=True, ondelete="SET NULL")
    enrollment_id: Mapped[uuid.UUID | None] = _uid("enrollments.id", null=True, ondelete="SET NULL")


class PilotAnnouncement(IdMixin, TimestampMixin, Base):
    __tablename__ = "pilot_announcements"
    program_id: Mapped[uuid.UUID] = _uid("pilot_programs.id", index=True)
    cohort_id: Mapped[uuid.UUID | None] = _uid("pilot_cohorts.id", null=True)
    author_user_id: Mapped[uuid.UUID | None] = _uid("users.id", null=True, ondelete="SET NULL")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)


class PilotConsent(IdMixin, TimestampMixin, Base):
    __tablename__ = "pilot_consents"
    __table_args__ = (
        UniqueConstraint("program_id", "user_id", "scope", name="uq_pilot_consent"),
        CheckConstraint("scope IN ('research_aggregate','publication_quote')", name="ck_pilot_consents_scope"),
    )
    program_id: Mapped[uuid.UUID] = _uid("pilot_programs.id", index=True)
    user_id: Mapped[uuid.UUID] = _uid("users.id", index=True)
    scope: Mapped[str] = mapped_column(String(24), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(20), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PilotSurvey(IdMixin, TimestampMixin, Base):
    __tablename__ = "pilot_surveys"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('baseline','endline','feedback_learner','feedback_instructor')", name="ck_pilot_surveys_kind"
        ),
        CheckConstraint("status IN ('draft','open','closed')", name="ck_pilot_surveys_status"),
        UniqueConstraint("program_id", "kind", name="uq_pilot_survey_kind"),
    )
    program_id: Mapped[uuid.UUID] = _uid("pilot_programs.id", index=True)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default="draft")
    questions: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    instrument_note: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="Instrumen draf untuk uji coba; BELUM divalidasi secara akademik."
    )


class SurveyResponse(IdMixin, TimestampMixin, Base):
    __tablename__ = "survey_responses"
    __table_args__ = (UniqueConstraint("survey_id", "user_id", name="uq_survey_response_user"),)
    survey_id: Mapped[uuid.UUID] = _uid("pilot_surveys.id", index=True)
    cohort_id: Mapped[uuid.UUID | None] = _uid("pilot_cohorts.id", null=True, ondelete="SET NULL")
    user_id: Mapped[uuid.UUID | None] = _uid("users.id", null=True, ondelete="SET NULL")  # NULL setelah anonimisasi
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InstructorNote(IdMixin, TimestampMixin, Base):
    """Catatan instruktur: BUKAN bagian analytics/ekspor."""

    __tablename__ = "instructor_notes"
    cohort_id: Mapped[uuid.UUID] = _uid("pilot_cohorts.id", index=True)
    participant_user_id: Mapped[uuid.UUID] = _uid("users.id")
    author_user_id: Mapped[uuid.UUID | None] = _uid("users.id", null=True, ondelete="SET NULL")
    note: Mapped[str] = mapped_column(Text, nullable=False)


class NotificationOutbox(IdMixin, TimestampMixin, Base):
    """Outbox transaksional dengan lease. status: pending | sending | sent | dev_sink | dead | undeliverable.

    - `sending` = diklaim worker (`claimed_by`, `lease_expires_at`); lease habis -> dapat diklaim ulang (pemulihan crash).
    - `dead` = gagal terminal (dead-letter): kegagalan permanen atau percobaan habis; dapat diinvestigasi/diantre ulang admin.
    - `undeliverable` = tidak ada provider yang terkonfigurasi/terjangkau; dicoba lagi tanpa menghabiskan jatah percobaan.
    - `error_category`: transient | permanent | provider_unavailable (tanpa isi pesan/secret).
    """

    __tablename__ = "notification_outbox"
    __table_args__ = (
        CheckConstraint("status IN ('pending','sending','sent','dev_sink','dead','undeliverable')", name="ck_outbox_status"),
        CheckConstraint(
            "error_category IS NULL OR error_category IN ('transient','permanent','provider_unavailable')",
            name="ck_outbox_error_category",
        ),
        Index("ix_outbox_due", "status", "next_attempt_at"),
    )
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    to_email: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(14), nullable=False, server_default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    error_category: Mapped[str | None] = mapped_column(String(24))
    provider: Mapped[str | None] = mapped_column(String(20))
    claimed_by: Mapped[str | None] = mapped_column(String(80))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dead_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    body_redacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dedupe_key: Mapped[str | None] = mapped_column(String(200), unique=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class JobRun(IdMixin, TimestampMixin, Base):
    """Status pekerjaan berkala/worker (satu baris per nama) — heartbeat, hasil terakhir, dan kunci jadwal retensi."""

    __tablename__ = "job_runs"
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    instance: Mapped[str | None] = mapped_column(String(80))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[str | None] = mapped_column(String(20))
    last_summary: Mapped[dict | None] = mapped_column(JSONB)
