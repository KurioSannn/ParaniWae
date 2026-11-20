from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import ApiError
from app.models import OutboxEmail

router = APIRouter(prefix="/dev", tags=["dev (hanya development)"])


@router.get("/mailbox", summary="Kotak surat DEV (sink): email tidak benar-benar terkirim")
def mailbox(db: Session = Depends(get_db)):
    s = get_settings()
    if s.app_env != "development" or s.mail_provider != "dev_sink":
        raise ApiError(404, "NOT_FOUND", "Tidak ditemukan.")
    rows = db.scalars(select(OutboxEmail).order_by(OutboxEmail.created_at.desc()).limit(30)).all()
    return jsonable_encoder([{"id": r.id, "to": r.to_email, "subject": r.subject, "body": r.body,
                              "created_at": r.created_at} for r in rows])
