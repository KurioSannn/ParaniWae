"""Riwayat hasil penilaian gerak (pengguna login). Hanya ringkasan; tidak ada video, gambar, atau landmark.

Skema `extra="forbid"`: field tak dikenal (mis. `landmarks`, `frames`, `video`) ditolak 422.
Breakdown kriteria/fase hanya disimpan bila `consent_breakdown=true`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, auth_required
from app.core.db import get_db
from app.core.errors import ApiError
from app.models import AssessmentAttempt
from app.services import assets3d, audit, ratelimit

router = APIRouter(prefix="/assessments", tags=["assessments"])


class CriterionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(max_length=60)
    label: str = Field(max_length=120)
    score: int | None = Field(None, ge=0, le=100)
    actual: float | None = None
    target: float | list[float] | None = None
    weight: float = Field(ge=0, le=100)
    status: Literal["ok", "below", "above", "unmeasured"]


class PhaseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keyframe: str = Field(max_length=20)
    label: str = Field(max_length=120)
    detected: bool
    score: int | None = Field(None, ge=0, le=100)


class AttemptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    movement_id: str = Field(max_length=120)
    lesson_ref: str | None = Field(None, max_length=200)
    protocol_id: str = Field(max_length=120)
    protocol_version: str = Field(max_length=20)
    reference_id: str = Field(max_length=160)
    engine_version: str = Field(max_length=20)
    model_version: str = Field(max_length=120)
    status: Literal["scored", "not_assessable"]
    not_assessable_reason: str | None = Field(None, max_length=60)
    total_score: int | None = Field(None, ge=0, le=100)
    input_quality: float | None = Field(None, ge=0, le=1)
    duration_ms: int | None = Field(None, ge=0, le=600_000)
    frames_analyzed: int | None = Field(None, ge=0, le=100_000)
    consent_breakdown: bool = False
    criteria: list[CriterionIn] | None = Field(None, max_length=20)
    phases: list[PhaseIn] | None = Field(None, max_length=12)
    feedback: list[str] | None = Field(None, max_length=3)

    @model_validator(mode="after")
    def _consistent(self):
        if (self.status == "scored") != (self.total_score is not None):
            raise ValueError("total_score wajib diisi tepat ketika status 'scored'")
        if not self.consent_breakdown and (self.criteria or self.phases):
            raise ValueError("rincian kriteria/fase hanya boleh dikirim dengan consent_breakdown=true")
        if self.feedback and any(len(f) > 400 for f in self.feedback):
            raise ValueError("saran terlalu panjang")
        return self


def _out(a: AssessmentAttempt) -> dict:
    return {
        "id": str(a.id), "created_at": a.created_at.isoformat(), "movement_id": a.movement_id, "lesson_ref": a.lesson_ref,
        "protocol_id": a.protocol_id, "protocol_version": a.protocol_version, "reference_id": a.reference_id,
        "engine_version": a.engine_version, "model_version": a.model_version, "status": a.status,
        "not_assessable_reason": a.not_assessable_reason, "total_score": a.total_score, "input_quality": a.input_quality,
        "duration_ms": a.duration_ms, "frames_analyzed": a.frames_analyzed, "consent_breakdown": a.consent_breakdown,
        "criteria": a.criteria, "phases": a.phases, "feedback": a.feedback,
    }


@router.post("", status_code=201, summary="Simpan ringkasan skor latihan (login; hanya angka ringkasan)")
def create(body: AttemptIn, request: Request, ctx: AuthContext = Depends(auth_required()), db: Session = Depends(get_db)):
    ratelimit.hit(db, "assessment:user", str(ctx.user.id), (60, 3600))
    proto = assets3d.protocol(body.movement_id)  # 404 bila gerakan tidak punya protokol
    if proto["protocol_id"] != body.protocol_id or proto["protocol_version"] != body.protocol_version:
        raise ApiError(409, "PROTOCOL_MISMATCH", "Versi protokol penilaian sudah berubah. Muat ulang halaman lalu coba lagi.")
    if proto["reference_id"] != body.reference_id:
        raise ApiError(409, "REFERENCE_MISMATCH", "Versi referensi gerak tidak cocok.")
    data = body.model_dump()
    a = AssessmentAttempt(user_id=ctx.user.id, created_at=datetime.now(UTC), protocol_status=proto["status"],
                          **{k: v for k, v in data.items() if k not in ("criteria", "phases")},
                          criteria=data["criteria"] if body.consent_breakdown else None,
                          phases=data["phases"] if body.consent_breakdown else None)
    db.add(a)
    audit.record(db, actor=ctx.user, action="assessment.save", entity_type="assessment_attempt", entity_id=None,
                 detail={"movement_id": body.movement_id, "status": body.status}, request_id=request.headers.get("x-request-id"))
    db.commit()
    return _out(a)


@router.get("", summary="Riwayat hasil latihan milik sendiri (+ tren per gerakan)")
def list_own(movement_id: str | None = Query(None, max_length=120), limit: int = Query(50, ge=1, le=200),
             ctx: AuthContext = Depends(auth_required()), db: Session = Depends(get_db)):
    q = select(AssessmentAttempt).where(AssessmentAttempt.user_id == ctx.user.id)
    if movement_id:
        q = q.where(AssessmentAttempt.movement_id == movement_id)
    rows = list(db.scalars(q.order_by(AssessmentAttempt.created_at.desc()).limit(limit)))
    summary = db.execute(
        select(AssessmentAttempt.movement_id, func.count(), func.max(AssessmentAttempt.total_score), func.avg(AssessmentAttempt.total_score))
        .where(AssessmentAttempt.user_id == ctx.user.id).group_by(AssessmentAttempt.movement_id)).all()
    return {
        "items": [_out(a) for a in rows],
        "by_movement": [{"movement_id": m, "attempts": n, "best_score": b, "average_score": round(float(av), 1) if av is not None else None}
                        for m, n, b, av in summary],
        "trend": [{"created_at": a.created_at.isoformat(), "total_score": a.total_score} for a in reversed(rows) if a.status == "scored"]
        if movement_id else [],
    }


@router.delete("/{attempt_id}", status_code=204, summary="Hapus satu hasil latihan milik sendiri")
def remove(attempt_id: uuid.UUID, ctx: AuthContext = Depends(auth_required()), db: Session = Depends(get_db)):
    n = db.execute(delete(AssessmentAttempt).where(AssessmentAttempt.id == attempt_id, AssessmentAttempt.user_id == ctx.user.id)).rowcount
    if not n:
        raise ApiError(404, "NOT_FOUND", "Tidak ditemukan.")
    db.commit()
