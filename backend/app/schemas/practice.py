"""Skema Practice Studio. `extra=forbid` + angka bertipe: payload tidak dapat memuat landmark/frame/foto."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Ms = Annotated[int, Field(ge=0, le=86_400_000)]
Cnt = Annotated[int, Field(ge=0, le=10_000_000)]
REASONS = ("NO_POSE", "MULTIPLE_PEOPLE", "TOO_FEW_LANDMARKS", "LOW_VISIBILITY", "OUT_OF_FRAME",
           "NO_HAND", "LOW_HAND_CONFIDENCE")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MsInState(_Strict):
    waiting_for_subject: Ms = 0
    detecting: Ms = 0
    partial_detection: Ms = 0
    insufficient_visibility: Ms = 0


class Reasons(_Strict):
    NO_POSE: Cnt = 0
    MULTIPLE_PEOPLE: Cnt = 0
    TOO_FEW_LANDMARKS: Cnt = 0
    LOW_VISIBILITY: Cnt = 0
    OUT_OF_FRAME: Cnt = 0
    NO_HAND: Cnt = 0
    LOW_HAND_CONFIDENCE: Cnt = 0


class QualitySummaryIn(_Strict):
    frames_total: Cnt
    processed_frames: Cnt
    dropped_frames: Cnt = 0
    valid_frame_ratio: Annotated[float, Field(ge=0, le=1)]
    ms_in_state: MsInState
    reasons: Reasons
    engine: Literal["worker", "synthetic"]
    delegate: Literal["GPU", "CPU"] | None = None
    simulated: bool = False


class StartIn(_Strict):
    lesson_id: uuid.UUID
    model_version: Annotated[str, Field(min_length=3, max_length=120, pattern=r"^[\w@./+\- ,:]+$")]
    client_version: Annotated[str, Field(max_length=40)] | None = None


class CompleteIn(_Strict):
    status: Literal["completed", "abandoned", "error"]
    active_duration_ms: Ms
    paused_duration_ms: Ms = 0
    quality_summary: QualitySummaryIn | None = None
    error_code: Annotated[str, Field(max_length=40, pattern=r"^[A-Z_]+$")] | None = None


class LessonBrief(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    course_slug: str
    course_title: str
    is_demo: bool
    verification_label: str


class PracticeSessionOut(BaseModel):
    id: uuid.UUID
    status: str
    started_at: datetime
    ended_at: datetime | None
    active_duration_ms: int | None
    paused_duration_ms: int | None
    model_version: str
    client_version: str | None
    quality_summary: dict | None
    error_code: str | None
    lesson: LessonBrief


class DayPoint(BaseModel):
    date: str
    sessions: int
    active_seconds: int


class PracticeSummary(BaseModel):
    total_sessions: int
    completed_sessions: int
    total_active_seconds: int
    sessions_last_7_days: int
    active_seconds_last_7_days: int
    days: list[DayPoint]
    last_session: PracticeSessionOut | None


class LessonPractice(BaseModel):
    available: bool
    reason: str | None = None
    is_demo: bool = False
    label: str
