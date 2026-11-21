from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.services.ops import media_storage

router = APIRouter(tags=["health"])


@router.get("/health")
def liveness() -> dict:
    """Liveness: proses API hidup. Tidak menyentuh database."""
    s = get_settings()
    return {"status": "ok", "service": s.app_name, "version": s.app_version}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)) -> dict:
    """Readiness: API dapat terhubung ke PostgreSQL dan migrasi sudah diterapkan."""
    try:
        db.execute(text("SELECT 1"))
        revision = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except Exception as exc:  # noqa: BLE001 - jangan bocorkan detail koneksi ke klien
        raise HTTPException(status_code=503, detail="database_unavailable") from exc
    media = media_storage()
    storage = "ok" if media["exists"] and media["writable"] else "unavailable"
    # 503 hanya bila DB mati. Penyimpanan media yang bermasalah = "degraded" (katalog tetap melayani; unggahan gagal).
    return {
        "status": "ok" if storage == "ok" else "degraded",
        "database": "ok",
        "media_storage": storage,
        "migration_revision": revision,
    }
