"""Pilot & Impact Studio: program, cohort, undangan, portal, pengumuman/outbox, survei, consent, izin."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models import (
    AuditLog,
    CohortInvitation,
    CohortMember,
    Enrollment,
    InstructorNote,
    NotificationOutbox,
    OutboxEmail,
    Partner,
    PartnerMember,
    SurveyResponse,
    User,
)
from app.services import notify, retention
from tests.factories import login, make_user, make_world, uid


def as_(client, user):
    client.cookies.clear()
    client.headers.pop("X-CSRF-Token", None)
    login(client, user)
    return user


def api(client, method, path, **kw):
    return getattr(client, method)(f"/api/v1/pilot{path}", **kw)


def ok(r, code=200):
    assert r.status_code == code, r.text
    return r.json()


class P:
    pass


def verify_partner(db, partner, admin):
    aid = admin.id  # baca dahulu agar tidak memicu autoflush di tengah perubahan
    partner.is_demo = False
    partner.verification_status = "verified"
    partner.public_listing_consent = (
        True  # kursus hanya terlihat pelajar bila mitra tampil publik (aturan visibilitas existing)
    )
    partner.verification_decided_by_user_id, partner.verification_decided_at = aid, datetime.now(UTC)
    partner.approved_by_user_id, partner.approved_at = aid, datetime.now(UTC)
    db.flush()


@pytest.fixture
def w(client, db):
    o = P()
    o.world = make_world(db, "published", n_lessons=3)
    o.partner, o.course = o.world["partner"], o.world["course"]
    o.mgr, o.ins, o.other_ins = make_user(db, "instructor"), make_user(db, "instructor"), make_user(db, "instructor")
    o.adm, o.adm2, o.cur = make_user(db, "admin"), make_user(db, "admin"), make_user(db, "curator")
    for u, role in ((o.mgr, "manager"), (o.ins, "instructor")):
        db.add(PartnerMember(partner_id=o.partner.id, user_id=u.id, role=role))
    db.flush()
    o.client, o.db = client, db
    return o


def mk_program(w, **over):
    as_(w.client, w.mgr)
    body = {
        "partner_id": str(w.partner.id),
        "name": f"Program {uid()}",
        "objective": "Uji coba belajar",
        "start_date": "2026-12-01",
        "end_date": "2027-02-28",
        "capacity": 20,
        "responsible_user_id": str(w.ins.id),
    }
    body.update(over)
    return ok(api(w.client, "post", "/programs", json=body), 201)


def mk_cohort(w, pid, **over):
    body = {
        "name": f"Cohort {uid()}",
        "course_id": str(w.course.id),
        "instructor_user_id": str(w.ins.id),
        "capacity": 10,
    }
    body.update(over)
    return ok(api(w.client, "post", f"/programs/{pid}/cohorts", json=body), 201)


def approve_and_open(w, pid, cid, partner_verified=True):
    if partner_verified:
        verify_partner(w.db, w.partner, w.adm)
    as_(w.client, w.mgr)
    ok(api(w.client, "post", f"/programs/{pid}/transition", json={"action": "submit"}))
    as_(w.client, w.adm)
    ok(api(w.client, "post", f"/programs/{pid}/transition", json={"action": "approve", "evidence_ref": "SK uji"}))
    as_(w.client, w.mgr)
    ok(api(w.client, "post", f"/programs/{pid}/transition", json={"action": "activate"}))
    ok(api(w.client, "post", f"/cohorts/{cid}/status", json={"status": "open"}))


def invite(w, cid, email=None, days=14):
    as_(w.client, w.ins)
    return ok(
        api(
            w.client,
            "post",
            f"/cohorts/{cid}/invitations",
            json={"email": email, "days": days} if email else {"days": days},
        ),
        201,
    )


def accept(w, user, token, ack=True, **kw):
    as_(w.client, user)
    return api(w.client, "post", "/invitations/accept", json={"token": token, "operational_ack": ack, **kw})


def learner(db):
    return make_user(db, "learner")


# ---------- program lifecycle ----------
def test_unverified_partner_may_only_draft(w, db):
    w.partner.is_demo, w.partner.status, w.partner.published_at = (
        False,
        "draft",
        None,
    )  # mitra nyata, belum terverifikasi
    db.flush()
    p = mk_program(w)
    assert (
        p["status"] == "draft" and p["official"] is False and p["partner_verified"] is False and p["is_demo"] is False
    )
    r = api(w.client, "post", f"/programs/{p['id']}/transition", json={"action": "submit"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "PARTNER_NOT_VERIFIED"
    # draf tetap dapat diubah; program tidak resmi
    ok(api(w.client, "patch", f"/programs/{p['id']}", json={"description": "x"}))


def test_submit_requires_complete_program_and_approval_rules(w, db):
    verify_partner(db, w.partner, w.adm)
    p = mk_program(w, objective=None, end_date=None)
    r = api(w.client, "post", f"/programs/{p['id']}/transition", json={"action": "submit"})
    assert r.status_code == 422 and len(r.json()["error"]["details"]["missing"]) == 3
    ok(api(w.client, "patch", f"/programs/{p['id']}", json={"objective": "Tujuan", "end_date": "2027-01-31"}))
    mk_cohort(w, p["id"])
    ok(api(w.client, "post", f"/programs/{p['id']}/transition", json={"action": "submit"}))
    # tidak bisa diedit setelah diajukan
    assert api(w.client, "patch", f"/programs/{p['id']}", json={"name": "baru"}).status_code == 409
    # penulis/manager tidak dapat menyetujui; admin anggota mitra juga tidak
    for act in ("approve", "reject"):
        assert api(
            w.client, "post", f"/programs/{p['id']}/transition", json={"action": act, "note": "x", "evidence_ref": "x"}
        ).status_code in (403, 409)
    db.add(PartnerMember(partner_id=w.partner.id, user_id=w.adm2.id, role="instructor"))
    db.flush()
    as_(w.client, w.adm2)
    r = api(w.client, "post", f"/programs/{p['id']}/transition", json={"action": "approve", "evidence_ref": "x"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "SELF_APPROVAL"
    as_(w.client, w.adm)
    assert (
        api(w.client, "post", f"/programs/{p['id']}/transition", json={"action": "approve"}).status_code == 422
    )  # tanpa bukti
    assert (
        api(w.client, "post", f"/programs/{p['id']}/transition", json={"action": "reject"}).status_code == 422
    )  # tanpa catatan
    d = ok(
        api(w.client, "post", f"/programs/{p['id']}/transition", json={"action": "approve", "evidence_ref": "SK-123"})
    )
    assert (
        d["status"] == "approved"
        and d["official"] is True
        and d["approval_evidence_ref"] == "SK-123"
        and d["approved_by"] == w.adm.display_name
    )
    as_(w.client, w.mgr)
    assert (
        ok(api(w.client, "post", f"/programs/{p['id']}/transition", json={"action": "activate"}))["status"] == "active"
    )
    acts = [r.action for r in db.scalars(select(AuditLog).where(AuditLog.entity_id == p["id"]))]
    assert {"pilot.submit", "pilot.approve", "pilot.activate"} <= set(acts)


def test_cross_partner_isolation_and_roles(w, db):
    p = mk_program(w)
    as_(w.client, w.other_ins)
    assert api(w.client, "get", f"/programs/{p['id']}").status_code == 404
    assert p["id"] not in {x["id"] for x in ok(api(w.client, "get", "/programs"))["items"]}
    assert api(w.client, "post", "/programs", json={"partner_id": str(w.partner.id), "name": "x"}).status_code == 404
    as_(w.client, learner(db))
    assert api(w.client, "get", "/programs").status_code == 403
    assert api(w.client, "get", f"/programs/{p['id']}").status_code == 403


def test_course_and_instructor_must_belong_to_partner(w, db):
    p = mk_program(w)
    other_world = make_world(db, "published")
    r = api(
        w.client, "post", f"/programs/{p['id']}/cohorts", json={"name": "c", "course_id": str(other_world["course"].id)}
    )
    assert r.status_code == 422
    r = api(
        w.client,
        "post",
        f"/programs/{p['id']}/cohorts",
        json={"name": "c", "course_id": str(w.course.id), "instructor_user_id": str(w.other_ins.id)},
    )
    assert r.status_code == 422


# ---------- invitation ----------
def test_invitation_token_hashed_single_use_and_enrolls(w, db):
    p = mk_program(w)
    c = mk_cohort(w, p["id"])
    # sebelum program disetujui: tidak ada undangan
    as_(w.client, w.ins)
    assert api(w.client, "post", f"/cohorts/{c['id']}/invitations", json={}).status_code == 409
    approve_and_open(w, p["id"], c["id"])
    inv = invite(w, c["id"])
    token = inv["token"]
    row = db.get(CohortInvitation, uuid.UUID(inv["id"]))
    assert row.token_hash != token and token not in str(row.__dict__) and len(row.token_hash) == 64
    prev = ok(api(w.client, "get", "/invitations/preview", params={"token": token}))
    assert prev["joinable"] and prev["program_name"] == p["name"] and "@" not in str(prev)
    assert api(w.client, "get", "/invitations/preview", params={"token": "x" * 30}).status_code == 404
    u = learner(db)
    assert accept(w, u, token, ack=False).status_code == 422
    r = ok(accept(w, u, token, research_aggregate=True))
    assert r["cohort_id"] == c["id"]
    assert db.scalar(
        select(Enrollment.id).where(Enrollment.user_id == u.id, Enrollment.course_id == w.course.id)
    )  # enrollment existing dipakai
    # sekali pakai
    u2 = learner(db)
    r = accept(w, u2, token)
    assert r.status_code == 409 and r.json()["error"]["code"] == "INVITATION_ACCEPTED"
    assert ok(api(w.client, "get", "/invitations/preview", params={"token": token}))["status"] == "accepted"
    detail = ok(api(as_(w.client, w.ins) and w.client, "get", f"/cohorts/{c['id']}"))
    assert [i["status"] for i in detail["invitations"]] == ["accepted"] and "token" not in detail["invitations"][0]


def test_invitation_expiry_revocation_and_email_binding(w, db):
    p = mk_program(w)
    c = mk_cohort(w, p["id"])
    approve_and_open(w, p["id"], c["id"])
    # kedaluwarsa
    inv = invite(w, c["id"])
    row = db.get(CohortInvitation, uuid.UUID(inv["id"]))
    row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.flush()
    r = accept(w, learner(db), inv["token"])
    assert r.status_code == 410 and r.json()["error"]["code"] == "INVITATION_EXPIRED"
    # dicabut
    inv2 = invite(w, c["id"])
    as_(w.client, w.ins)
    ok(api(w.client, "delete", f"/invitations/{inv2['id']}"))
    r = accept(w, learner(db), inv2["token"])
    assert r.status_code == 410 and r.json()["error"]["code"] == "INVITATION_REVOKED"
    # terikat email
    target = learner(db)
    inv3 = invite(w, c["id"], email=target.email)
    assert accept(w, learner(db), inv3["token"]).status_code == 403
    ok(accept(w, target, inv3["token"]))
    # email belum terverifikasi
    inv4 = invite(w, c["id"])
    u = learner(db)
    as_(w.client, u)
    u.email_verified_at = None  # sesi sudah ada; email dianggap belum terverifikasi
    db.flush()
    r = api(w.client, "post", "/invitations/accept", json={"token": inv4["token"], "operational_ack": True})
    assert r.status_code == 403 and r.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


def test_no_double_enrollment_per_program_and_capacity(w, db):
    p = mk_program(w)
    c1 = mk_cohort(w, p["id"], capacity=1)
    c2 = mk_cohort(w, p["id"])
    approve_and_open(w, p["id"], c1["id"])
    as_(w.client, w.mgr)
    ok(api(w.client, "post", f"/cohorts/{c2['id']}/status", json={"status": "open"}))
    u = learner(db)
    ok(accept(w, u, invite(w, c1["id"])["token"]))
    # peserta yang sama ke cohort lain di program yang sama
    r = accept(w, u, invite(w, c2["id"])["token"])
    assert r.status_code == 409 and r.json()["error"]["code"] == "ALREADY_MEMBER"
    # kapasitas penuh
    r = accept(w, learner(db), invite(w, c1["id"])["token"])
    assert r.status_code == 409 and r.json()["error"]["code"] == "CAPACITY_FULL"
    # keluar lalu bergabung kembali ke cohort lain diperbolehkan; unik parsial menjaga DB
    as_(w.client, u)
    assert api(w.client, "delete", f"/me/cohorts/{c1['id']}").status_code == 204
    ok(accept(w, u, invite(w, c2["id"])["token"]))
    assert db.scalar(
        select(CohortMember.id).where(
            CohortMember.user_id == u.id, CohortMember.cohort_id == c2["id"], CohortMember.status == "active"
        )
    )


# ---------- portal ----------
def test_learner_portal_shows_cohort_progress_schedule_and_announcements(w, db):
    p = mk_program(w)
    c = mk_cohort(w, p["id"])
    approve_and_open(w, p["id"], c["id"])
    as_(w.client, w.ins)
    ok(
        api(
            w.client,
            "put",
            f"/cohorts/{c['id']}/sessions",
            json={"sessions": [{"title": "Pertemuan 1", "starts_at": "2026-12-05T09:00:00Z", "location_note": "Aula"}]},
        )
    )
    u = learner(db)
    ok(accept(w, u, invite(w, c["id"])["token"]))
    as_(w.client, w.ins)
    ok(
        api(
            w.client,
            "post",
            f"/programs/{p['id']}/announcements",
            json={"title": "Selamat datang", "body": "Mulai pekan depan", "cohort_id": c["id"]},
        ),
        201,
    )
    as_(w.client, u)
    lesson = w.world["lessons"][0]
    ok(w.client.put(f"/api/v1/me/lessons/{lesson.id}/progress", json={"status": "completed"}))
    portal = ok(api(w.client, "get", "/me/portal"))
    assert len(portal["memberships"]) == 1 and portal["memberships"][0]["progress"]["completed"] == 1
    d = ok(api(w.client, "get", f"/me/cohorts/{c['id']}"))
    assert d["sessions"][0]["title"] == "Pertemuan 1" and d["announcements"][0]["title"] == "Selamat datang"
    assert d["progress"]["percent"] == 33 and [x["completed"] for x in d["lessons"]] == [True, False, False]
    assert d["instructor"] == w.ins.display_name and d["consents"] == {
        "research_aggregate": False,
        "publication_quote": False,
    }
    as_(w.client, learner(db))
    assert api(w.client, "get", f"/me/cohorts/{c['id']}").status_code == 404


# ---------- outbox ----------
def test_announcement_outbox_honest_delivery_states(w, db, monkeypatch):
    p = mk_program(w)
    c = mk_cohort(w, p["id"])
    approve_and_open(w, p["id"], c["id"])
    users = [learner(db) for _ in range(2)]
    for u in users:
        ok(accept(w, u, invite(w, c["id"])["token"]))
    as_(w.client, w.ins)
    as_(w.client, w.mgr)
    r = ok(api(w.client, "post", f"/programs/{p['id']}/announcements", json={"title": "Info", "body": "Isi"}), 201)
    assert r["delivery"] == {"pending": 2}  # diantrekan, BELUM terkirim
    rows = db.scalars(select(NotificationOutbox).where(NotificationOutbox.kind == "announcement")).all()
    assert {x.to_email for x in rows} == {u.email for u in users} and all(x.status == "pending" for x in rows)
    # tanpa provider -> tidak diklaim terkirim
    monkeypatch.setattr(get_settings(), "mail_provider", "none")
    res = notify.deliver_due(db)
    assert res["undeliverable"] >= 2 and not db.scalar(
        select(OutboxEmail.id).where(OutboxEmail.to_email == users[0].email)
    )
    assert all(x.status == "undeliverable" and x.sent_at is None for x in rows)
    # dev_sink: tercatat sebagai dev_sink (bukan 'sent')
    monkeypatch.setattr(get_settings(), "mail_provider", "dev_sink")
    for x in rows:
        x.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)
    db.flush()
    res = notify.deliver_due(db)
    assert res["dev_sink"] >= 2 and all(x.status == "dev_sink" for x in rows)
    assert db.scalar(select(OutboxEmail.id).where(OutboxEmail.to_email == users[0].email))
    # idempoten: tidak ada pesan ganda
    assert (
        notify.enqueue(
            db, kind="announcement", to_email=users[0].email, subject="s", body="b", dedupe_key=rows[0].dedupe_key
        )
        is False
    )


def test_review_queue_notifies_staff_via_outbox(w, db):
    # pengajuan dokumentasi gerakan mengantre notifikasi untuk kurator/admin + manager mitra
    n = notify.notify_review_queue(
        db, doc_id=uuid.uuid4(), title="Gerakan Uji", version=1, partner_id=w.partner.id, action="submit1"
    )
    assert n >= 3
    rows = db.scalars(select(NotificationOutbox).where(NotificationOutbox.kind == "review_queue")).all()
    assert w.cur.email in {r.to_email for r in rows} and w.mgr.email in {r.to_email for r in rows}
    assert all(r.status == "pending" for r in rows)


# ---------- survei & consent ----------
def joined_cohort(w, n=1):
    p = mk_program(w)
    c = mk_cohort(w, p["id"], capacity=50)
    approve_and_open(w, p["id"], c["id"])
    us = []
    for _ in range(n):
        u = learner(w.db)
        ok(accept(w, u, invite(w, c["id"])["token"]))
        us.append(u)
    as_(w.client, w.ins)
    return p, c, us


def test_survey_template_validation_and_single_submission(w, db):
    p, c, (u,) = joined_cohort(w)
    s = ok(api(w.client, "post", f"/programs/{p['id']}/surveys/templates", json={"kind": "baseline"}), 201)
    assert "BELUM divalidasi" in s["instrument_note"] and s["status"] == "draft"
    as_(w.client, u)
    assert (
        api(w.client, "post", f"/surveys/{s['id']}/responses", json={"answers": {}}).status_code == 409
    )  # belum dibuka
    as_(w.client, w.ins)
    ok(api(w.client, "post", f"/surveys/{s['id']}/transition", json={"action": "open"}))
    as_(w.client, u)
    pending = ok(api(w.client, "get", "/me/surveys"))
    assert [x["id"] for x in pending] == [s["id"]]
    for bad in (
        {"pengalaman": "Tidak ada", "percaya_diri": 3, "akses_instruktur": "Sangat sulit"},
        {"pengalaman": "Belum pernah", "percaya_diri": 9, "akses_instruktur": "Sangat sulit"},
        {"pengalaman": "Belum pernah", "akses_instruktur": "Sangat sulit"},
        {"pengalaman": "Belum pernah", "percaya_diri": 3, "akses_instruktur": "Sangat sulit", "asing": "x"},
    ):
        assert api(w.client, "post", f"/surveys/{s['id']}/responses", json={"answers": bad}).status_code == 422, bad
    good = {"pengalaman": "Belum pernah", "percaya_diri": 4, "akses_instruktur": "Cukup mudah", "harapan": "Belajar"}
    ok(api(w.client, "post", f"/surveys/{s['id']}/responses", json={"answers": good}), 201)
    assert api(w.client, "post", f"/surveys/{s['id']}/responses", json={"answers": good}).status_code == 409
    assert ok(api(w.client, "get", "/me/surveys")) == []
    as_(w.client, learner(db))
    assert (
        api(w.client, "post", f"/surveys/{s['id']}/responses", json={"answers": good}).status_code == 404
    )  # bukan anggota


def test_consent_is_separate_optional_and_revocable(w, db):
    p, c, (u,) = joined_cohort(w)
    as_(w.client, u)
    assert ok(api(w.client, "get", f"/me/cohorts/{c['id']}"))["consents"] == {
        "research_aggregate": False,
        "publication_quote": False,
    }
    r = ok(api(w.client, "put", f"/me/programs/{p['id']}/consents", json={"research_aggregate": True}))
    assert r == {"research_aggregate": True, "publication_quote": False}
    r = ok(api(w.client, "put", f"/me/programs/{p['id']}/consents", json={"research_aggregate": False}))
    assert r["research_aggregate"] is False
    as_(w.client, learner(db))
    assert (
        api(w.client, "put", f"/me/programs/{p['id']}/consents", json={"research_aggregate": True}).status_code == 404
    )


def test_instructor_notes_are_separate_from_analytics(w, db):
    p, c, (u,) = joined_cohort(w)
    ok(
        api(
            w.client,
            "post",
            f"/cohorts/{c['id']}/notes",
            json={"participant_user_id": str(u.id), "note": "Perlu didampingi"},
        ),
        201,
    )
    assert (
        api(
            w.client, "post", f"/cohorts/{c['id']}/notes", json={"participant_user_id": str(uuid.uuid4()), "note": "x"}
        ).status_code
        == 422
    )
    a = ok(api(w.client, "get", f"/programs/{p['id']}/analytics"))
    csvtxt = w.client.get(f"/api/v1/pilot/programs/{p['id']}/report.csv").text
    assert "Perlu didampingi" not in str(a) and "Perlu didampingi" not in csvtxt
    as_(w.client, w.other_ins)
    assert api(w.client, "get", f"/cohorts/{c['id']}/notes").status_code == 404
    as_(w.client, learner(db))
    assert api(w.client, "get", f"/cohorts/{c['id']}/notes").status_code == 403


def test_retention_anonymizes_surveys_and_deletes_notes(w, db):
    p, c, us = joined_cohort(w, n=2)
    s = ok(api(w.client, "post", f"/programs/{p['id']}/surveys/templates", json={"kind": "feedback_learner"}), 201)
    ok(api(w.client, "post", f"/surveys/{s['id']}/transition", json={"action": "open"}))
    for u in us:
        as_(w.client, u)
        ok(
            api(
                w.client,
                "post",
                f"/surveys/{s['id']}/responses",
                json={"answers": {"kemudahan": 4, "materi": 5, "kamera": "Tidak mencoba", "saran": "Bagus"}},
            ),
            201,
        )
    as_(w.client, w.ins)
    ok(
        api(w.client, "post", f"/cohorts/{c['id']}/notes", json={"participant_user_id": str(us[0].id), "note": "n"}),
        201,
    )
    prog = db.get(__import__("app.models", fromlist=["PilotProgram"]).PilotProgram, uuid.UUID(p["id"]))
    prog.completed_at = datetime.now(UTC) - timedelta(days=get_settings().pilot_retention_days + 1)
    prog.status = "completed"
    db.flush()
    done = retention.run_retention(db)
    assert prog.id in done and prog.anonymized_at
    assert db.scalars(
        select(SurveyResponse).where(SurveyResponse.survey_id == uuid.UUID(s["id"]))
    ).all()  # agregat tetap ada
    assert all(r.user_id is None for r in db.scalars(select(SurveyResponse)).all() if str(r.survey_id) == s["id"])
    assert not db.scalar(select(InstructorNote.id).where(InstructorNote.cohort_id == uuid.UUID(c["id"])))
    assert retention.run_retention(db) == []  # idempoten


_ = (User, Partner)
