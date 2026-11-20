"""Pengiriman email lewat antarmuka provider (tidak terkunci pada vendor).

- dev_sink: HANYA development; email disimpan ke tabel outbox_emails, TIDAK dikirim ke mana pun.
- smtp: SMTP standar (host/port/starttls/user/password dari env).
- Bila tidak terkonfigurasi: fitur terkait mengembalikan 503 (tidak berpura-pura terkirim).
"""

import smtplib
from email.message import EmailMessage
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError
from app.models import OutboxEmail


class MailProvider(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class DevSinkProvider:
    def __init__(self, db: Session):
        self.db = db

    def send(self, to: str, subject: str, body: str) -> None:
        self.db.add(OutboxEmail(to_email=to, subject=subject, body=body))
        self.db.flush()


class SmtpProvider:
    def send(self, to: str, subject: str, body: str) -> None:
        s = get_settings()
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = s.mail_from, to, subject
        msg.set_content(body)
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15) as smtp:
            if s.smtp_starttls:
                smtp.starttls()
            if s.smtp_user:
                smtp.login(s.smtp_user, s.smtp_password or "")
            smtp.send_message(msg)


def mail_available() -> bool:
    return get_settings().mail_configured


def get_mailer(db: Session) -> MailProvider:
    s = get_settings()
    if not s.mail_configured:
        raise ApiError(503, "FEATURE_UNAVAILABLE",
                       "Fitur email belum dikonfigurasi pada server ini, sehingga tidak tersedia.")
    return DevSinkProvider(db) if s.mail_provider == "dev_sink" else SmtpProvider()


def link(path: str, token: str) -> str:
    return f"{get_settings().public_base_url.rstrip('/')}{path}?token={token}"
