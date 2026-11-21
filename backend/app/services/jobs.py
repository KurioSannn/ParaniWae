"""Status pekerjaan worker/berkala di PostgreSQL (`job_runs`): heartbeat, hasil terakhir, dan kunci anti-paralel."""

import hashlib

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import JobRun
from app.services.auth import now


def _row(db: Session, name: str) -> JobRun:
    r = db.scalar(select(JobRun).where(JobRun.name == name))
    if r is None:
        r = JobRun(name=name)
        db.add(r)
        db.flush()
    return r


def heartbeat(db: Session, name: str, instance: str) -> None:
    r = _row(db, name)
    r.heartbeat_at, r.instance = now(), instance
    db.commit()


def record(db: Session, name: str, *, started, status: str, summary: dict | None, instance: str | None = None) -> None:
    r = _row(db, name)
    r.last_started_at, r.last_finished_at, r.last_status, r.last_summary = started, now(), status, summary
    if instance:
        r.instance = instance
    db.commit()


def last(db: Session, name: str) -> JobRun | None:
    return db.scalar(select(JobRun).where(JobRun.name == name))


def try_lock(db: Session, key: str) -> bool:
    """Advisory lock tingkat TRANSAKSI: hanya satu worker yang menjalankan pekerjaan `key` pada satu waktu.
    Dilepas otomatis saat commit/rollback (aman terhadap crash)."""
    k = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big", signed=True)
    return bool(db.execute(text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": k}).scalar())
