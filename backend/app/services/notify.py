"""Outbox transaksional untuk notifikasi email (tabel `notification_outbox`).

Penjadwalan (enqueue) terjadi DI TRANSAKSI YANG SAMA dengan perubahan datanya; pengiriman dilakukan worker terpisah.
Status jujur: `sent` hanya bila SMTP benar-benar menerima pesan; `dev_sink` = disimpan di kotak surat DEV (tidak dikirim);
`undeliverable` = tidak ada provider yang terkonfigurasi (pesan tetap `pending` tertahan, tidak diklaim terkirim).
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import NotificationOutbox, Partner, PartnerMember, User

MAX_ATTEMPTS = 6


def enqueue(db: Session, *, kind: str, to_email: str, subject: str, body: str, dedupe_key: str | None = None) -> bool:
    """Tambah ke outbox. `dedupe_key` mencegah pesan ganda. Mengembalikan True bila baris baru dibuat."""
    if dedupe_key and db.scalar(select(NotificationOutbox.id).where(NotificationOutbox.dedupe_key == dedupe_key)):
        return False
    try:
        with db.begin_nested():
            db.add(
                NotificationOutbox(
                    kind=kind, to_email=to_email, subject=subject[:300], body=body, dedupe_key=dedupe_key
                )
            )
            db.flush()
    except IntegrityError:
        return False
    return True


def staff_emails(db: Session) -> list[str]:
    return [
        e for (e,) in db.execute(select(User.email).where(User.role.in_(["curator", "admin"]), User.status == "active"))
    ]


def partner_manager_emails(db: Session, partner_id) -> list[str]:
    return [
        e
        for (e,) in db.execute(
            select(User.email)
            .join(PartnerMember, PartnerMember.user_id == User.id)
            .where(
                PartnerMember.partner_id == partner_id,
                PartnerMember.role == "manager",
                PartnerMember.status == "active",
                User.status == "active",
            )
        )
    ]


def notify_review_queue(db: Session, *, doc_id, title: str, version: int, partner_id, action: str) -> int:
    """Antrean review: pengajuan -> kurator/admin + manager mitra; keputusan lain tidak dikirim di sini."""
    base = get_settings().public_base_url.rstrip("/")
    n = 0
    partner = db.get(Partner, partner_id)
    pname = partner.name if partner else "mitra"
    for email in sorted(set(staff_emails(db) + partner_manager_emails(db, partner_id))):
        if enqueue(
            db,
            kind="review_queue",
            to_email=email,
            dedupe_key=f"review:{doc_id}:{action}:{email}",
            subject=f"[SILATARA] Dokumentasi menunggu tinjauan: {title} (v{version})",
            body=f'Dokumentasi "{title}" versi {version} milik {pname} diajukan dan menunggu tinjauan.\n\n'
            f"Buka: {base}/app/studio\n\nEmail ini dikirim otomatis oleh SILATARA.",
        ):
            n += 1
    return n


def deliver_due(db: Session, limit: int = 50) -> dict[str, int]:
    """Kompatibilitas: satu putaran pengiriman memakai mesin outbox berlease (lihat services/outbox.py)."""
    from app.services import outbox

    return outbox.deliver_due(db, limit=limit)


def status_summary(db: Session) -> dict[str, int]:
    from sqlalchemy import func

    return dict(db.execute(select(NotificationOutbox.status, func.count()).group_by(NotificationOutbox.status)).all())
