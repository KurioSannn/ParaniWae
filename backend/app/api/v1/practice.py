import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, PageParams, auth_required
from app.core.db import get_db
from app.models import PracticeSession
from app.schemas.common import Page
from app.schemas.practice import CompleteIn, PracticeSessionOut, PracticeSummary, StartIn
from app.services import practice as svc
from app.services.queries import paginate

router = APIRouter(tags=["practice studio"])


def _rid(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@router.post("/practice-sessions", response_model=PracticeSessionOut, status_code=201,
             summary="Mulai sesi Practice Studio (metadata saja)")
def start_session(body: StartIn, request: Request, ctx: AuthContext = Depends(auth_required()),
                  db: Session = Depends(get_db)):
    s = svc.start(db, ctx.user, body, _rid(request))
    db.commit()
    return svc.to_out(db, s)


@router.post("/practice-sessions/{session_id}/complete", response_model=PracticeSessionOut,
             summary="Akhiri sesi (durasi + ringkasan agregat kualitas input)")
def complete_session(session_id: uuid.UUID, body: CompleteIn, request: Request,
                     ctx: AuthContext = Depends(auth_required()), db: Session = Depends(get_db)):
    s = svc.complete(db, ctx.user, session_id, body, _rid(request))
    db.commit()
    return svc.to_out(db, s)


@router.get("/practice-sessions/{session_id}", response_model=PracticeSessionOut, summary="Detail sesi milik sendiri")
def get_session(session_id: uuid.UUID, ctx: AuthContext = Depends(auth_required()), db: Session = Depends(get_db)):
    return svc.to_out(db, svc.get_own(db, ctx.user, session_id))


@router.get("/me/practice-sessions", response_model=Page[PracticeSessionOut], summary="Riwayat latihan saya")
def my_sessions(
    lesson: uuid.UUID | None = None,
    status: str | None = Query(None, pattern="^(in_progress|completed|abandoned|error)$"),
    p: PageParams = Depends(), ctx: AuthContext = Depends(auth_required()), db: Session = Depends(get_db),
):
    svc.reap_stale(db, ctx.user)
    db.commit()
    stmt = select(PracticeSession).where(PracticeSession.user_id == ctx.user.id)
    if lesson:
        stmt = stmt.where(PracticeSession.lesson_id == lesson)
    if status:
        stmt = stmt.where(PracticeSession.status == status)
    stmt = stmt.order_by(PracticeSession.started_at.desc())
    return paginate(db, stmt, p.page, p.page_size, lambda s: svc.to_out(db, s))


@router.get("/me/practice-summary", response_model=PracticeSummary, summary="Ringkasan & tren latihan saya")
def my_summary(tz_offset: int = Query(420, ge=-720, le=840, description="Offset zona waktu menit dari UTC (WIB=420)"),
               ctx: AuthContext = Depends(auth_required()), db: Session = Depends(get_db)):
    out = svc.summary(db, ctx.user, tz_offset)
    db.commit()
    return out
