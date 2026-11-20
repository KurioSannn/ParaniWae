from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import AuditLog, User


def record(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: object | None = None,
    detail: dict | None = None,
    request_id: str | None = None,
) -> None:
    """Menambah baris audit pada transaksi berjalan (caller yang commit)."""
    db.add(
        AuditLog(
            created_at=datetime.now(UTC),  # waktu aplikasi (bukan now() transaksi) agar urutan riwayat stabil
            actor_user_id=actor.id if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            detail=detail,
            request_id=request_id,
        )
    )
