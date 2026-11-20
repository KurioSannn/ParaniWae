"""Rate limit jendela-tetap di PostgreSQL: konsisten lintas worker/instance tanpa Redis."""

import hashlib
import random
import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError


def _key(scope: str, ident: str) -> str:
    return f"{scope}:{hashlib.sha256(ident.encode()).hexdigest()[:32]}"


def hit(db: Session, scope: str, ident: str, limit_window: tuple[int, int]) -> None:
    """Catat satu percobaan; lempar 429 (+Retry-After) bila melewati batas."""
    if not get_settings().rate_limit_enabled:
        return
    limit, window = limit_window
    now = int(time.time())
    start = now - now % window
    count = db.execute(
        text(
            "INSERT INTO rate_limits(key, window_start, count) VALUES (:k, :w, 1) "
            "ON CONFLICT (key, window_start) DO UPDATE SET count = rate_limits.count + 1 "
            "RETURNING count"
        ),
        {"k": _key(scope, ident), "w": start},
    ).scalar_one()
    if random.random() < 0.02:  # pembersihan oportunistik
        db.execute(text("DELETE FROM rate_limits WHERE window_start < :old"), {"old": now - 2 * 86400})
    db.commit()  # simpan hitungan walau request berikutnya gagal
    if count > limit:
        retry = start + window - now
        raise ApiError(429, "RATE_LIMITED", "Terlalu banyak percobaan. Coba lagi nanti.",
                       {"retry_after_seconds": retry}, headers={"Retry-After": str(retry)})
