"""Mesin pengiriman outbox: klaim atomik berlease, retry exponential backoff + jitter, dead-letter, pemulihan crash.

Garansi (jujur):
- KLAIM ATOMIK: `UPDATE ... WHERE id IN (SELECT ... FOR UPDATE SKIP LOCKED)` — dua worker tidak pernah mengklaim baris yang sama.
- LEASE: baris `sending` yang lease-nya habis (worker mati) diklaim ulang -> pemulihan otomatis. Penyelesaian memakai
  `WHERE claimed_by = :worker` sehingga worker yang kehilangan lease tidak menimpa hasil pemiliknya.
- DELIVERY AT-LEAST-ONCE untuk SMTP: bila worker mati TEPAT setelah SMTP menerima pesan dan sebelum status `sent` tersimpan,
  pesan dikirim ulang. Dimitigasi: `Message-ID` deterministik per baris (MTA/penerima dapat mendeduplikasi) dan status ditulis
  segera setelah kirim. `dev_sink` bersifat exactly-once (insert kotak surat + status dalam satu transaksi).
- Status jujur: `sent` hanya bila SMTP menerima; `dev_sink` = hanya kotak surat dev; `undeliverable` = provider tak terkonfigurasi/terjangkau.
"""

import logging
import os
import random
import re
import smtplib
import socket
import uuid
from datetime import timedelta

from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import NotificationOutbox, OutboxEmail
from app.services import audit, mail
from app.services.auth import now

log = logging.getLogger("silatara.outbox")
REDACTED = "[dihapus setelah terkirim]"
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

WORKER_ID = f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:6]}"


def sanitize_error(exc: BaseException) -> str:
    """Kelas galat + pesan singkat tanpa alamat email/secret (tidak pernah memuat isi pesan)."""
    msg = _EMAIL.sub("<email>", str(exc))[:180]
    return f"{type(exc).__name__}: {msg}"


def classify(exc: BaseException) -> str:
    """transient | permanent | provider_unavailable."""
    if isinstance(exc, (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused)):
        return "permanent"
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return "provider_unavailable"  # konfigurasi kredensial: bukan salah pesan
    if isinstance(exc, smtplib.SMTPResponseException):
        return "permanent" if 500 <= exc.smtp_code < 600 else "transient"
    if isinstance(
        exc, (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, ConnectionError, TimeoutError, socket.gaierror)
    ):
        return "provider_unavailable"
    if isinstance(exc, OSError):
        return "provider_unavailable"
    return "transient"


def backoff_seconds(attempt: int) -> float:
    """Exponential backoff + jitter penuh-sebagian: base*2^(n-1) terpotong cap, dikali 0.5..1.0."""
    s = get_settings()
    raw = min(s.outbox_backoff_cap_s, s.outbox_backoff_base_s * (2 ** max(0, attempt - 1)))
    return raw * random.uniform(0.5, 1.0)  # noqa: S311 - jitter, bukan kriptografi


def claim(
    db: Session, worker_id: str, limit: int | None = None, lease_s: int | None = None, *, attempt_increment: int = 1
) -> list:
    """Klaim atomik baris yang jatuh tempo (+ baris `sending` yang lease-nya habis). Commit di dalam fungsi."""
    s = get_settings()
    rows = db.execute(
        text(
            """
            WITH due AS (
                SELECT id FROM notification_outbox
                WHERE (status IN ('pending','undeliverable') AND next_attempt_at <= clock_timestamp())
                   OR (status = 'sending' AND lease_expires_at < clock_timestamp())
                ORDER BY next_attempt_at, created_at
                FOR UPDATE SKIP LOCKED
                LIMIT :n
            )
            UPDATE notification_outbox o
               SET status = 'sending', claimed_by = :w,
                   lease_expires_at = clock_timestamp() + make_interval(secs => :lease),
                   attempts = o.attempts + :inc,
                   first_attempt_at = COALESCE(o.first_attempt_at, clock_timestamp()),
                   updated_at = clock_timestamp()
              FROM due WHERE o.id = due.id
            RETURNING o.id
            """
        ),
        {
            "n": limit or s.outbox_batch_size,
            "w": worker_id,
            "lease": float(lease_s or s.outbox_lease_seconds),
            "inc": attempt_increment,
        },
    ).all()
    db.commit()
    return [r[0] for r in rows]


def release(db: Session, worker_id: str, ids: list, *, refund_attempt: bool = True) -> int:
    """Kembalikan klaim yang belum diproses (mis. shutdown): status pending, percobaan dikembalikan."""
    if not ids:
        return 0
    res = db.execute(
        update(NotificationOutbox)
        .where(
            NotificationOutbox.id.in_(ids),
            NotificationOutbox.claimed_by == worker_id,
            NotificationOutbox.status == "sending",
        )
        .values(
            status="pending",
            claimed_by=None,
            lease_expires_at=None,
            attempts=NotificationOutbox.attempts - (1 if refund_attempt else 0),
        )
    )
    db.commit()
    return res.rowcount


def _finalize(db: Session, row_id, worker_id: str, **values) -> bool:
    res = db.execute(
        update(NotificationOutbox)
        .where(
            NotificationOutbox.id == row_id,
            NotificationOutbox.claimed_by == worker_id,
            NotificationOutbox.status == "sending",
        )
        .values(claimed_by=None, lease_expires_at=None, **values)
    )
    return res.rowcount == 1


def process_one(db: Session, row_id, worker_id: str) -> str:
    """Proses satu baris yang sudah diklaim. Mengembalikan status akhir (atau 'lost' bila lease hilang)."""
    s = get_settings()
    row = db.scalar(
        select(NotificationOutbox).where(
            NotificationOutbox.id == row_id,
            NotificationOutbox.claimed_by == worker_id,
            NotificationOutbox.status == "sending",
        )
    )
    if row is None:
        db.rollback()
        return "lost"
    t = now()
    # provider tidak dikonfigurasi: jangan kirim, jangan klaim terkirim, jangan menghabiskan jatah percobaan
    if not s.mail_configured:
        age_h = (t - row.created_at).total_seconds() / 3600
        if age_h > s.outbox_undeliverable_max_hours:
            ok = _finalize(
                db,
                row.id,
                worker_id,
                status="dead",
                dead_at=t,
                error_category="provider_unavailable",
                last_error="Provider email tidak dikonfigurasi hingga batas usia pesan.",
                attempts=row.attempts - 1,
            )
            db.commit()
            return "dead" if ok else "lost"
        ok = _finalize(
            db,
            row.id,
            worker_id,
            status="undeliverable",
            error_category="provider_unavailable",
            attempts=row.attempts - 1,
            last_error="Provider email belum dikonfigurasi.",
            next_attempt_at=t + timedelta(seconds=backoff_seconds(3) + 300),
        )
        db.commit()
        return "undeliverable" if ok else "lost"
    provider = "dev_sink" if s.mail_provider == "dev_sink" else "smtp"
    try:
        if provider == "dev_sink":
            # exactly-once: kotak surat dev + status `dev_sink` dalam SATU transaksi
            db.add(OutboxEmail(to_email=row.to_email, subject=row.subject, body=row.body))
            ok = _finalize(
                db,
                row.id,
                worker_id,
                status="dev_sink",
                provider=provider,
                sent_at=t,
                last_error=None,
                error_category=None,
                body=REDACTED,
                body_redacted_at=t,
            )
            if not ok:
                db.rollback()
                return "lost"
            db.commit()
            return "dev_sink"
        mail.SmtpProvider().send(row.to_email, row.subject, row.body, message_id=str(row.id))
    except Exception as exc:  # noqa: BLE001 - provider eksternal; semua galat diklasifikasi, tidak pernah ditelan diam-diam
        db.rollback()
        cat = classify(exc)
        err = sanitize_error(exc)
        attempts = row.attempts
        if cat == "permanent" or (cat == "transient" and attempts >= s.outbox_max_attempts):
            ok = _finalize(
                db, row.id, worker_id, status="dead", dead_at=t, error_category=cat, last_error=err, provider=provider
            )
            status = "dead"
        elif cat == "provider_unavailable":
            age_h = (t - row.created_at).total_seconds() / 3600
            if age_h > s.outbox_undeliverable_max_hours:
                ok = _finalize(
                    db,
                    row.id,
                    worker_id,
                    status="dead",
                    dead_at=t,
                    error_category=cat,
                    last_error=err,
                    provider=provider,
                )
                status = "dead"
            else:
                ok = _finalize(
                    db,
                    row.id,
                    worker_id,
                    status="undeliverable",
                    error_category=cat,
                    last_error=err,
                    provider=provider,
                    attempts=attempts - 1,
                    next_attempt_at=t + timedelta(seconds=backoff_seconds(3)),
                )
                status = "undeliverable"
        else:
            ok = _finalize(
                db,
                row.id,
                worker_id,
                status="pending",
                error_category=cat,
                last_error=err,
                provider=provider,
                next_attempt_at=t + timedelta(seconds=backoff_seconds(attempts)),
            )
            status = "pending"
        db.commit()
        log.warning("outbox %s -> %s (%s, percobaan %s)", row.id, status, cat, attempts)
        return status if ok else "lost"
    ok = _finalize(
        db,
        row.id,
        worker_id,
        status="sent",
        provider=provider,
        sent_at=now(),
        last_error=None,
        error_category=None,
        body=REDACTED,
        body_redacted_at=now(),
    )
    db.commit()
    return "sent" if ok else "lost"


def deliver_due(
    db: Session, worker_id: str | None = None, limit: int | None = None, should_stop=lambda: False
) -> dict[str, int]:
    """Satu putaran: klaim -> proses berurutan -> (shutdown: lepaskan sisa klaim)."""
    s = get_settings()
    wid = worker_id or WORKER_ID
    out: dict[str, int] = {
        "sent": 0,
        "dev_sink": 0,
        "pending": 0,
        "undeliverable": 0,
        "dead": 0,
        "lost": 0,
        "released": 0,
    }
    ids = claim(db, wid, limit, attempt_increment=1)
    for i, rid in enumerate(ids):
        if should_stop():
            out["released"] += release(db, wid, ids[i:])
            break
        out[process_one(db, rid, wid)] += 1
    _ = s
    return out


# ---------- operasi administrator ----------
def status_summary(db: Session) -> dict:
    rows = db.execute(text("SELECT status, count(*), min(created_at) FROM notification_outbox GROUP BY status")).all()
    oldest_pending = next((r[2] for r in rows if r[0] in ("pending", "undeliverable")), None)
    return {"by_status": {r[0]: r[1] for r in rows}, "oldest_pending_at": oldest_pending}


def list_rows(db: Session, status: str, limit: int = 50) -> list[dict]:
    """Daftar untuk investigasi: tanpa isi pesan; alamat email dimasker."""
    out = []
    for r in db.scalars(
        select(NotificationOutbox)
        .where(NotificationOutbox.status == status)
        .order_by(NotificationOutbox.created_at.desc())
        .limit(limit)
    ):
        local, _, dom = r.to_email.partition("@")
        out.append(
            {
                "id": str(r.id),
                "kind": r.kind,
                "to": f"{local[:1]}***@{dom}",
                "attempts": r.attempts,
                "category": r.error_category,
                "error": r.last_error,
                "created_at": r.created_at,
                "dead_at": r.dead_at,
            }
        )
    return out


def requeue(db: Session, row_id, actor=None) -> bool:
    row = db.get(NotificationOutbox, row_id)
    if not row or row.status != "dead" or row.body_redacted_at:
        return False
    row.status, row.attempts, row.next_attempt_at, row.last_error, row.dead_at = "pending", 0, now(), None, None
    audit.record(
        db,
        actor=actor,
        action="outbox.requeue",
        entity_type="notification_outbox",
        entity_id=row.id,
        detail={},
        request_id=None,
    )
    return True


def purge(
    db: Session, *, sent_days: int | None = None, dead_days: int | None = None, dry_run: bool = True, actor=None
) -> dict:
    """Bersihkan outbox LAMA yang aman: terkirim (sent/dev_sink) > sent_days, dead-letter > dead_days.
    TIDAK PERNAH menyentuh pending / sending / undeliverable. dry_run (default) hanya menghitung."""
    s = get_settings()
    sd, dd = sent_days or s.outbox_purge_sent_days, dead_days or s.outbox_purge_dead_days
    t = now()
    cond_sent = (
        NotificationOutbox.status.in_(["sent", "dev_sink"]),
        NotificationOutbox.sent_at < t - timedelta(days=sd),
    )
    cond_dead = (NotificationOutbox.status == "dead", NotificationOutbox.dead_at < t - timedelta(days=dd))
    from sqlalchemy import delete, func

    report: dict = {
        "dry_run": dry_run,
        "sent_older_than_days": sd,
        "dead_older_than_days": dd,
        "eligible": {},
        "deleted": 0,
    }
    for label, cond in (("sent_or_dev_sink", cond_sent), ("dead", cond_dead)):
        rows = db.execute(
            select(NotificationOutbox.kind, func.count()).where(*cond).group_by(NotificationOutbox.kind)
        ).all()
        report["eligible"][label] = {k: n for k, n in rows}
    total = sum(n for v in report["eligible"].values() for n in v.values())
    report["eligible_total"] = total
    if not dry_run and total:
        n = 0
        for _, cond in (("s", cond_sent), ("d", cond_dead)):
            n += db.execute(delete(NotificationOutbox).where(*cond)).rowcount
        report["deleted"] = n
        audit.record(
            db,
            actor=actor,
            action="outbox.purge",
            entity_type="notification_outbox",
            entity_id=None,
            detail={"deleted": n, "sent_days": sd, "dead_days": dd, "by_kind": report["eligible"]},
            request_id=None,
        )
    return report
