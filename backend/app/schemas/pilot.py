"""Skema Pilot & Impact Studio. `extra=forbid` pada semua input."""

import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Short = Annotated[str, Field(min_length=1, max_length=200)]
LongText = Annotated[str, Field(max_length=10000)]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProgramCreate(_In):
    partner_id: uuid.UUID
    name: Short
    objective: LongText | None = None
    description: LongText | None = None
    responsible_user_id: uuid.UUID | None = None
    default_course_id: uuid.UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    capacity: Annotated[int, Field(ge=1, le=5000)] = 30


class ProgramPatch(_In):
    name: Short | None = None
    objective: LongText | None = None
    description: LongText | None = None
    responsible_user_id: uuid.UUID | None = None
    default_course_id: uuid.UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    capacity: Annotated[int, Field(ge=1, le=5000)] | None = None


class ProgramAction(_In):
    action: Literal["submit", "approve", "reject", "activate", "complete", "cancel", "archive"]
    note: Annotated[str, Field(max_length=2000)] | None = None
    evidence_ref: Annotated[str, Field(max_length=2000)] | None = None


class CohortCreate(_In):
    name: Short
    course_id: uuid.UUID
    instructor_user_id: uuid.UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    capacity: Annotated[int, Field(ge=1, le=2000)] = 30


class CohortPatch(_In):
    name: Short | None = None
    course_id: uuid.UUID | None = None
    instructor_user_id: uuid.UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    capacity: Annotated[int, Field(ge=1, le=2000)] | None = None


class CohortStatus(_In):
    status: Literal["open", "closed", "completed"]


class SessionIn(_In):
    title: Short
    starts_at: datetime
    ends_at: datetime | None = None
    location_note: Annotated[str, Field(max_length=300)] | None = None


class SessionsPut(_In):
    sessions: list[SessionIn] = Field(max_length=100)


class InviteCreate(_In):
    email: Annotated[str, Field(max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")] | None = None
    days: Annotated[int, Field(ge=1, le=60)] = 14


class InviteAccept(_In):
    token: Annotated[str, Field(min_length=20, max_length=200)]
    operational_ack: bool
    research_aggregate: bool = False
    publication_quote: bool = False


class ConsentPut(_In):
    research_aggregate: bool | None = None
    publication_quote: bool | None = None


class AnnouncementIn(_In):
    title: Short
    body: Annotated[str, Field(min_length=1, max_length=5000)]
    cohort_id: uuid.UUID | None = None
    notify: bool = True


class NoteIn(_In):
    participant_user_id: uuid.UUID
    note: Annotated[str, Field(min_length=1, max_length=4000)]


class Question(_In):
    id: Annotated[str, Field(pattern=r"^[a-z0-9_]{1,40}$")]
    type: Literal["single_choice", "rating", "open_text"]
    text: Annotated[str, Field(min_length=1, max_length=500)]
    required: bool = True
    options: list[Annotated[str, Field(min_length=1, max_length=200)]] | None = Field(default=None, max_length=12)
    scale_min: Annotated[int, Field(ge=0, le=1)] = 1
    scale_max: Annotated[int, Field(ge=2, le=10)] = 5
    min_label: Annotated[str, Field(max_length=60)] | None = None
    max_label: Annotated[str, Field(max_length=60)] | None = None


class SurveyCreate(_In):
    kind: Literal["baseline", "endline", "feedback_learner", "feedback_instructor"]
    title: Short
    questions: list[Question] = Field(min_length=1, max_length=40)


class SurveyTemplate(_In):
    kind: Literal["baseline", "endline", "feedback_learner", "feedback_instructor"]


class SurveyAction(_In):
    action: Literal["open", "close"]


class SurveySubmit(_In):
    answers: dict[str, str | int | None]
