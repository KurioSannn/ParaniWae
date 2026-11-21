"""Worker pemeliharaan (aman dijalankan >1 instans: outbox memakai klaim SKIP LOCKED + lease; retensi memakai advisory lock).

Putaran: heartbeat -> outbox -> pindai file karantina -> purge media kedaluwarsa -> retensi terjadwal.
- Setiap putaran punya `job_id`; log terstruktur membawa `job_id`, `worker`, dan hasil per langkah.
- Graceful shutdown: SIGTERM/SIGINT menghentikan putaran sesudah langkah berjalan; klaim outbox yang belum diproses dilepas.
- Kegagalan satu langkah tidak menghentikan langkah lain.
"""

import logging
import signal
import threading
import time
import uuid
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.db import get_engine
from app.core.logging import job_id_var, setup_logging
from app.services import jobs, outbox, retention, scanner
from app.services import media as media_svc
from app.services.auth import now

log = logging.getLogger("silatara.worker")
HEARTBEAT = "/tmp/worker-heartbeat"  # healthcheck compose (cepat, tanpa DB)
STOP = threading.Event()


def run_once(db: Session, should_stop=STOP.is_set) -> dict:
    jid = uuid.uuid4().hex[:12]
    token = job_id_var.set(jid)
    out: dict = {"job_id": jid}
    s = get_settings()
    try:
        jobs.heartbeat(db, "worker", outbox.WORKER_ID)
        for name, fn in (
            ("outbox", lambda: outbox.deliver_due(db, should_stop=should_stop)),
            ("scan", lambda: scanner.scan_pending(db)),
            ("purge_media", lambda: media_svc.purge_expired(db, dry_run=False, actor=None)),
            (
                "retention",
                lambda: (
                    retention.run_scheduled(db, interval_hours=s.retention_interval_hours)
                    if s.retention_auto_enabled
                    else {"skipped": "nonaktif"}
                ),
            ),
        ):
            if should_stop():
                out[name] = "dilewati (shutdown)"
                continue
            try:
                out[name] = fn()
                db.commit()
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                out[name] = f"GAGAL: {type(exc).__name__}"
                log.exception("langkah worker gagal", extra={"step": name, "error_class": type(exc).__name__})
        jobs.record(
            db,
            "worker_round",
            started=now(),
            status="ok",
            summary={k: v for k, v in out.items() if k != "job_id"},
            instance=outbox.WORKER_ID,
        )
    finally:
        job_id_var.reset(token)
    return out


def _install_signals() -> None:
    def handler(signum, _frame):
        log.info("sinyal %s diterima: shutdown anggun", signum)
        STOP.set()

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)


def loop() -> None:
    setup_logging()
    _install_signals()
    interval = get_settings().worker_interval_s
    factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    log.info("worker mulai", extra={"worker": outbox.WORKER_ID, "interval_s": interval})
    while not STOP.is_set():
        with factory() as db:
            res = run_once(db)
            log.info("putaran worker", extra={"result": res})
        Path(HEARTBEAT).touch()
        for _ in range(interval * 4):  # tidur dalam potongan agar shutdown responsif
            if STOP.is_set():
                break
            time.sleep(0.25)
    with factory() as db:  # lepaskan klaim yang tersisa milik worker ini
        from sqlalchemy import text

        db.execute(
            text(
                "UPDATE notification_outbox SET status='pending', claimed_by=NULL, lease_expires_at=NULL, attempts=GREATEST(attempts-1,0) "
                "WHERE claimed_by = :w AND status = 'sending'"
            ),
            {"w": outbox.WORKER_ID},
        )
        db.commit()
    log.info("worker berhenti bersih")
