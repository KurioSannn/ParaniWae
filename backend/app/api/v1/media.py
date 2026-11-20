from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, optional_auth
from app.core.db import get_db
from app.core.errors import ApiError
from app.services import media as media_svc
from app.services import storage

router = APIRouter(tags=["media"])


@router.get(
    "/media/{media_id}/file", summary="Berkas media (terotorisasi; anonim hanya bila publik + izin terverifikasi)"
)
def media_file(media_id: str, ctx: AuthContext | None = Depends(optional_auth), db: Session = Depends(get_db)):
    r = media_svc.get(db, media_id)
    # 404 (bukan 403) bila tidak berhak: tidak membocorkan keberadaan media privat.
    if not media_svc.can_read_file(db, ctx.user if ctx else None, r):
        raise ApiError(404, "NOT_FOUND", "Media tidak ditemukan.")
    path = storage.path_for(r.storage_key)
    if not path.exists():
        raise ApiError(404, "NOT_FOUND", "Media tidak ditemukan.")
    return FileResponse(
        path,
        media_type=r.mime,
        content_disposition_type="inline",
        filename=r.original_filename,
        headers={
            "Cache-Control": "private, no-store" if r.access_level != "public" else "public, max-age=300",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
        },
    )
