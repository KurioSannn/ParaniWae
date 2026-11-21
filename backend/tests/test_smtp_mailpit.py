"""Pengiriman SMTP NYATA ke mail sink lokal (Mailpit). Opt-in: set MAILPIT_HOST (mis. `mailpit`) dan jalankan
`docker compose --profile mail up -d mailpit`. Membuktikan pesan benar-benar DITERIMA sink — BUKAN pengiriman email produksi."""

import os
import uuid

import httpx
import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models import NotificationOutbox
from app.services import notify, outbox

HOST = os.environ.get("MAILPIT_HOST")
pytestmark = pytest.mark.skipif(not HOST, reason="MAILPIT_HOST tidak diset (uji SMTP nyata opt-in)")


@pytest.fixture
def smtp_to_mailpit(monkeypatch):
    st = get_settings()
    monkeypatch.setattr(st, "mail_provider", "smtp")
    monkeypatch.setattr(st, "smtp_host", HOST)
    monkeypatch.setattr(st, "smtp_port", 1025)
    monkeypatch.setattr(st, "smtp_starttls", False)
    monkeypatch.setattr(st, "smtp_user", None)
    monkeypatch.setattr(st, "mail_from", "SILATARA <pilot@silatara.test>")
    httpx.delete(f"http://{HOST}:8025/api/v1/messages", timeout=5)
    return st


def messages():
    return httpx.get(f"http://{HOST}:8025/api/v1/messages", timeout=5).json()["messages"]


def test_outbox_delivers_to_real_smtp_sink_once_with_deterministic_message_id(db, smtp_to_mailpit):
    tag = uuid.uuid4().hex[:8]
    notify.enqueue(
        db,
        kind="smtp-test",
        to_email=f"peserta-{tag}@contoh.test",
        subject=f"[SILATARA] Uji {tag}",
        body="Isi uji",
        dedupe_key=f"smtp-{tag}",
    )
    res = outbox.deliver_due(db, worker_id="smtp-test")
    row = db.scalar(select(NotificationOutbox).where(NotificationOutbox.dedupe_key == f"smtp-{tag}"))
    assert res["sent"] >= 1 and row.status == "sent" and row.provider == "smtp" and row.sent_at
    got = [m for m in messages() if m["Subject"] == f"[SILATARA] Uji {tag}"]
    assert len(got) == 1 and got[0]["To"][0]["Address"] == f"peserta-{tag}@contoh.test"
    detail = httpx.get(f"http://{HOST}:8025/api/v1/message/{got[0]['ID']}/headers", timeout=5).json()
    assert detail["Message-Id"] == [f"<{row.id}@silatara.outbox>"]  # Message-ID deterministik = id baris outbox
    # pemrosesan ulang tidak mengirim lagi
    outbox.deliver_due(db, worker_id="smtp-test")
    assert len([m for m in messages() if m["Subject"] == f"[SILATARA] Uji {tag}"]) == 1


def test_unreachable_smtp_is_provider_unavailable_not_sent(db, smtp_to_mailpit, monkeypatch):
    monkeypatch.setattr(get_settings(), "smtp_port", 1)  # tidak ada pendengar
    monkeypatch.setattr(get_settings(), "smtp_timeout_s", 2)
    notify.enqueue(
        db,
        kind="smtp-test",
        to_email="x@contoh.test",
        subject="tak terkirim",
        body="b",
        dedupe_key=f"smtp-{uuid.uuid4().hex}",
    )
    res = outbox.deliver_due(db, worker_id="smtp-test")
    assert res["undeliverable"] >= 1 and res["sent"] == 0
    assert not [m for m in messages() if m["Subject"] == "tak terkirim"]
