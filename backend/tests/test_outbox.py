"""Reliability outbox: klaim atomik, concurrency 2 worker, retry/backoff, dead-letter, pemulihan crash, idempotensi, purge."""

import smtplib
import threading
import uuid
from collections import Counter
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_engine
from app.models import AuditLog, NotificationOutbox, OutboxEmail
from app.services import notify, outbox


@pytest.fixture
def smtp_on(monkeypatch):
    st = get_settings()
    monkeypatch.setattr(st, "mail_provider", "smtp")
    monkeypatch.setattr(st, "smtp_host", "smtp.invalid.test")
    return st


class FakeSmtp:
    """Penyedia SMTP palsu: mencatat setiap pengiriman; dapat diprogram untuk gagal."""

    sent: list = []
    fail = None
    lock = threading.Lock()

    def send(self, to, subject, body, message_id=None):
        if FakeSmtp.fail:
            raise FakeSmtp.fail
        with FakeSmtp.lock:
            FakeSmtp.sent.append((to, message_id))


@pytest.fixture(autouse=True)
def _fake(monkeypatch):
    FakeSmtp.sent, FakeSmtp.fail = [], None
    monkeypatch.setattr(outbox.mail, "SmtpProvider", FakeSmtp)


def add(db, n=1, **kw):
    rows = []
    for i in range(n):
        r = NotificationOutbox(kind="t", to_email=f"u{i}@x.test", subject="s", body="isi rahasia", **kw)
        db.add(r)
        rows.append(r)
    db.flush()
    return rows


# ---------- status & dasar ----------
def test_success_marks_sent_redacts_body_and_uses_deterministic_message_id(db, smtp_on):
    (r,) = add(db)
    res = outbox.deliver_due(db, worker_id="w1")
    assert res["sent"] == 1 and r.status == "sent" and r.sent_at and r.provider == "smtp" and r.attempts == 1
    assert (
        r.body == outbox.REDACTED and r.body_redacted_at
    )  # isi (bisa memuat tautan undangan) tidak disimpan setelah terkirim
    assert FakeSmtp.sent == [("u0@x.test", str(r.id))]  # Message-ID deterministik = id baris


def test_dedupe_key_prevents_duplicate_rows(db):
    assert notify.enqueue(db, kind="k", to_email="a@x.test", subject="s", body="b", dedupe_key="dup-1") is True
    assert notify.enqueue(db, kind="k", to_email="a@x.test", subject="s", body="b", dedupe_key="dup-1") is False
    assert db.scalars(select(NotificationOutbox).where(NotificationOutbox.dedupe_key == "dup-1")).all().__len__() == 1


def test_no_provider_is_honest_undeliverable_and_never_sent(db, monkeypatch):
    monkeypatch.setattr(get_settings(), "mail_provider", "none")
    (r,) = add(db)
    res = outbox.deliver_due(db, worker_id="w1")
    assert (
        res["undeliverable"] == 1 and r.status == "undeliverable" and r.sent_at is None and r.attempts == 0
    )  # tidak menghabiskan jatah
    assert r.error_category == "provider_unavailable" and FakeSmtp.sent == []
    # terlalu lama tanpa provider -> dead-letter (tidak menumpuk selamanya)
    r.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)
    r.created_at = datetime.now(UTC) - timedelta(hours=get_settings().outbox_undeliverable_max_hours + 1)
    db.flush()
    outbox.deliver_due(db, worker_id="w1")
    assert r.status == "dead" and r.dead_at


def test_dev_sink_is_exactly_once_and_labelled_not_sent(db, monkeypatch):
    monkeypatch.setattr(get_settings(), "mail_provider", "dev_sink")
    (r,) = add(db)
    outbox.deliver_due(db, worker_id="w1")
    outbox.deliver_due(db, worker_id="w2")
    assert r.status == "dev_sink" and r.status != "sent"
    assert len(db.scalars(select(OutboxEmail).where(OutboxEmail.to_email == "u0@x.test")).all()) == 1


# ---------- retry / klasifikasi ----------
def test_transient_failure_backs_off_with_jitter_then_dead_letters(db, smtp_on):
    (r,) = add(db)
    FakeSmtp.fail = smtplib.SMTPResponseException(451, b"coba lagi nanti u0@x.test")
    t0 = datetime.now(UTC)
    outbox.deliver_due(db, worker_id="w1")
    base = get_settings().outbox_backoff_base_s
    delay = (r.next_attempt_at - t0).total_seconds()
    assert r.status == "pending" and r.attempts == 1 and r.error_category == "transient"
    assert base * 0.5 - 1 <= delay <= base + 1  # exponential (n=1) dengan jitter 0.5–1.0
    assert "u0@x.test" not in r.last_error and "<email>" in r.last_error  # galat disanitasi (tanpa alamat)
    delays = []
    for _ in range(get_settings().outbox_max_attempts - 1):
        r.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)
        db.flush()
        before = datetime.now(UTC)
        outbox.deliver_due(db, worker_id="w1")
        if r.status == "pending":
            delays.append((r.next_attempt_at - before).total_seconds())
    assert r.status == "dead" and r.attempts == get_settings().outbox_max_attempts and r.dead_at
    assert delays[-1] > delays[0]  # backoff bertambah


def test_permanent_failure_goes_straight_to_dead_letter(db, smtp_on):
    (r,) = add(db)
    FakeSmtp.fail = smtplib.SMTPRecipientsRefused({"u0@x.test": (550, b"no such user")})
    outbox.deliver_due(db, worker_id="w1")
    assert r.status == "dead" and r.error_category == "permanent" and r.attempts == 1


def test_provider_down_does_not_burn_attempts(db, smtp_on):
    (r,) = add(db)
    FakeSmtp.fail = ConnectionRefusedError("smtp mati")
    outbox.deliver_due(db, worker_id="w1")
    assert r.status == "undeliverable" and r.error_category == "provider_unavailable" and r.attempts == 0
    assert r.next_attempt_at > datetime.now(UTC)
    FakeSmtp.fail = None
    r.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)
    db.flush()
    outbox.deliver_due(db, worker_id="w1")
    assert r.status == "sent"


def test_classify_and_sanitize():
    assert outbox.classify(smtplib.SMTPResponseException(550, b"x")) == "permanent"
    assert outbox.classify(smtplib.SMTPResponseException(421, b"x")) == "transient"
    assert outbox.classify(smtplib.SMTPAuthenticationError(535, b"x")) == "provider_unavailable"
    assert outbox.classify(TimeoutError()) == "provider_unavailable"
    assert outbox.classify(ValueError("x")) == "transient"
    assert "<email>" in outbox.sanitize_error(Exception("gagal ke a.b@contoh.id"))


# ---------- crash recovery, lease, shutdown ----------
def test_crashed_worker_lease_expires_and_message_is_recovered(db, smtp_on):
    (r,) = add(db)
    ids = outbox.claim(db, "worker-mati")
    assert ids == [r.id] and r.status == "sending" and r.claimed_by == "worker-mati"
    # selama lease masih berlaku, worker lain TIDAK boleh mengambilnya
    assert outbox.claim(db, "worker-b") == []
    db.execute(
        text("UPDATE notification_outbox SET lease_expires_at = now() - interval '1 second' WHERE id = :i"), {"i": r.id}
    )
    db.expire_all()
    res = outbox.deliver_due(db, worker_id="worker-b")
    assert res["sent"] == 1 and r.status == "sent" and r.attempts == 2  # percobaan pertama (crash) dihitung


def test_worker_that_lost_its_lease_cannot_overwrite_new_owner(db, smtp_on):
    (r,) = add(db)
    outbox.claim(db, "lama")
    db.execute(
        text("UPDATE notification_outbox SET lease_expires_at = now() - interval '1 second' WHERE id = :i"), {"i": r.id}
    )
    db.expire_all()
    outbox.claim(db, "baru")  # lease habis -> diambil pemilik baru
    assert outbox.process_one(db, r.id, "lama") == "lost"  # pemilik lama tidak memproses/menimpa
    assert FakeSmtp.sent == []
    assert outbox.process_one(db, r.id, "baru") == "sent" and len(FakeSmtp.sent) == 1


def test_graceful_shutdown_releases_unprocessed_claims_and_refunds_attempts(db, smtp_on):
    rows = add(db, 3)
    calls = {"n": 0}

    def stop_after_first():
        calls["n"] += 1
        return calls["n"] > 1

    res = outbox.deliver_due(db, worker_id="w1", should_stop=stop_after_first)
    assert res["sent"] == 1 and res["released"] == 2
    left = [r for r in rows if r.status != "sent"]
    assert len(left) == 2 and all(r.status == "pending" and r.claimed_by is None and r.attempts == 0 for r in left)


# ---------- concurrency NYATA: dua koneksi DB terpisah ----------
def _cleanup(prefix):
    with Session(get_engine()) as s:
        s.execute(delete(NotificationOutbox).where(NotificationOutbox.kind == prefix))
        s.execute(delete(OutboxEmail).where(OutboxEmail.subject == prefix))
        s.commit()


def test_two_workers_never_claim_or_send_the_same_message(monkeypatch, smtp_on):
    prefix = f"ct-{uuid.uuid4().hex[:8]}"
    N = 60
    with Session(get_engine()) as s:
        s.add_all(
            [NotificationOutbox(kind=prefix, to_email=f"u{i}@x.test", subject=prefix, body="b") for i in range(N)]
        )
        s.commit()
    barrier = threading.Barrier(2)
    claimed: dict[str, list] = {"A": [], "B": []}

    def worker(name):
        with Session(get_engine()) as s:
            barrier.wait()
            while True:
                ids = outbox.claim(s, name, limit=7)
                if not ids:
                    break
                claimed[name] += ids
                for i in ids:
                    outbox.process_one(s, i, name)

    try:
        ts = [threading.Thread(target=worker, args=(n,)) for n in ("A", "B")]
        [t.start() for t in ts]
        [t.join() for t in ts]
        a, b = set(claimed["A"]), set(claimed["B"])
        assert not (a & b), "dua worker mengklaim baris yang sama"
        assert len(a | b) == N and a and b  # keduanya bekerja; semua terproses
        mine = [m for (_, m) in FakeSmtp.sent]
        assert len(mine) == N and len(set(mine)) == N, "ada pesan terkirim ganda"
        with Session(get_engine()) as s:
            st = Counter(
                r.status for r in s.scalars(select(NotificationOutbox).where(NotificationOutbox.kind == prefix))
            )
            assert st == {"sent": N}
    finally:
        _cleanup(prefix)


def test_expired_lease_recovered_by_other_worker_under_real_connections(smtp_on):
    prefix = f"ct-{uuid.uuid4().hex[:8]}"
    with Session(get_engine()) as s:
        s.add(NotificationOutbox(kind=prefix, to_email="x@x.test", subject=prefix, body="b"))
        s.commit()
    try:
        with Session(get_engine()) as a, Session(get_engine()) as b:
            ids = outbox.claim(a, "mati")  # worker "mati": klaim lalu tidak pernah menyelesaikan
            assert len(ids) == 1 and outbox.claim(b, "hidup") == []
            a.execute(
                text("UPDATE notification_outbox SET lease_expires_at = now() - interval '1 second' WHERE kind = :k"),
                {"k": prefix},
            )
            a.commit()
            assert outbox.deliver_due(b, worker_id="hidup")["sent"] == 1
    finally:
        _cleanup(prefix)


# ---------- retensi / purge / investigasi ----------
def test_purge_dry_run_default_never_touches_open_work_and_audits_execution(db):
    t = datetime.now(UTC)
    old, recent = t - timedelta(days=400), t - timedelta(days=1)
    rows = {
        "sent_old": NotificationOutbox(
            kind="a", to_email="1@x.test", subject="s", body="b", status="sent", sent_at=old
        ),
        "sent_new": NotificationOutbox(
            kind="a", to_email="2@x.test", subject="s", body="b", status="sent", sent_at=recent
        ),
        "dead_old": NotificationOutbox(
            kind="b", to_email="3@x.test", subject="s", body="b", status="dead", dead_at=old
        ),
        "dead_mid": NotificationOutbox(
            kind="b", to_email="4@x.test", subject="s", body="b", status="dead", dead_at=t - timedelta(days=60)
        ),
        "pending_old": NotificationOutbox(
            kind="c", to_email="5@x.test", subject="s", body="b", status="pending", created_at=old
        ),
        "undeliv_old": NotificationOutbox(
            kind="c", to_email="6@x.test", subject="s", body="b", status="undeliverable", created_at=old
        ),
        "sending_old": NotificationOutbox(
            kind="c", to_email="7@x.test", subject="s", body="b", status="sending", created_at=old
        ),
    }
    db.add_all(rows.values())
    db.flush()
    rep = outbox.purge(db)  # default = dry-run
    assert rep["dry_run"] is True and rep["deleted"] == 0 and rep["eligible_total"] == 2
    assert rep["eligible"]["sent_or_dev_sink"] == {"a": 1} and rep["eligible"]["dead"] == {"b": 1}
    assert db.scalar(
        select(NotificationOutbox.id).where(NotificationOutbox.id == rows["sent_old"].id)
    )  # belum terhapus
    rep = outbox.purge(db, dry_run=False)
    assert rep["deleted"] == 2
    left = {k for k, r in rows.items() if db.scalar(select(NotificationOutbox.id).where(NotificationOutbox.id == r.id))}
    assert left == {
        "sent_new",
        "dead_mid",
        "pending_old",
        "undeliv_old",
        "sending_old",
    }  # yang masih dibutuhkan tidak dihapus
    a = db.scalar(select(AuditLog).where(AuditLog.action == "outbox.purge").order_by(AuditLog.created_at.desc()))
    assert a.detail["deleted"] == 2 and "1@x.test" not in str(a.detail)  # audit: jumlah saja


def test_investigation_listing_masks_address_and_hides_body_and_requeue_rules(db):
    r = NotificationOutbox(
        kind="k",
        to_email="budi.santoso@contoh.id",
        subject="s",
        body="tautan?token=RAHASIA",
        status="dead",
        dead_at=datetime.now(UTC),
        error_category="permanent",
        last_error="SMTPRecipientsRefused: <email>",
    )
    sent = NotificationOutbox(
        kind="k",
        to_email="x@x.test",
        subject="s",
        body=outbox.REDACTED,
        status="dead",
        dead_at=datetime.now(UTC),
        body_redacted_at=datetime.now(UTC),
    )
    db.add_all([r, sent])
    db.flush()
    rows = outbox.list_rows(db, "dead")
    txt = str(rows)
    assert "budi.santoso" not in txt and "RAHASIA" not in txt and "b***@contoh.id" in txt
    assert outbox.requeue(db, r.id) is True and r.status == "pending" and r.attempts == 0
    assert outbox.requeue(db, sent.id) is False  # isi sudah diredaksi: tidak bisa dikirim ulang
