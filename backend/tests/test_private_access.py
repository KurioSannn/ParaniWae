"""Pilot privat: akses materi ditentukan keanggotaan cohort + status program, BUKAN publikasi profil mitra.
Matriks izin lintas partner/cohort/program/materi/media/latihan dan perubahan status program."""

import io
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models import (
    Course,
    Lesson,
    Movement,
    MovementDocument,
    Partner,
    PartnerMember,
    PilotCohort,
    PilotProgram,
    ReferenceMedia,
)
from tests.factories import make_movement, make_user, make_world, uid
from tests.test_pilot import accept, approve_and_open, as_, learner, ok
from tests.test_pilot import api as papi
from tests.test_studio import WEBM, media_form


def get(client, path, **kw):
    return client.get(f"/api/v1{path}", **kw)


class PW:
    pass


@pytest.fixture
def pw(client, db, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "media_dir", str(tmp_path / "media"))
    o = PW()
    o.client, o.db = client, db
    o.world = make_world(db, "published", n_lessons=3)
    o.partner, o.course = o.world["partner"], o.world["course"]
    o.mgr, o.ins, o.ins2 = make_user(db, "instructor"), make_user(db, "instructor"), make_user(db, "instructor")
    o.adm, o.cur = make_user(db, "admin"), make_user(db, "curator")
    for u, role in ((o.mgr, "manager"), (o.ins, "instructor"), (o.ins2, "instructor")):
        db.add(PartnerMember(partner_id=o.partner.id, user_id=u.id, role=role))
    aid = o.adm.id
    # Mitra PRIVAT: nyata + terverifikasi, TIDAK tampil di direktori publik (tanpa listing/consent/publikasi)
    p = o.partner
    p.is_demo, p.verification_status = False, "verified"
    p.verification_decided_by_user_id, p.verification_decided_at = aid, datetime.now(UTC)
    p.public_listing_consent, p.status, p.published_at = False, "draft", None
    o.course.distribution_scope = "pilot_private"
    o.movement = make_movement(db, o.world, practice_mode="solo_beginner")
    o.lesson = o.world["lessons"][0]
    o.lesson.movement_id = o.movement.id
    # mitra lain + instruktur luar
    o.other_world = make_world(db, "published")
    o.outsider = make_user(db, "instructor")
    db.add(PartnerMember(partner_id=o.other_world["partner"].id, user_id=o.outsider.id, role="manager"))
    db.flush()
    o.slug, o.lslug = o.course.slug, o.lesson.slug
    # program: draf -> disetujui -> aktif; cohort terbuka; L1 menerima undangan
    return o


def run_program(o, accept_users=1):
    """Program disetujui+aktif, cohort terbuka. Mengembalikan (program, cohort, [peserta])."""
    as_(o.client, o.mgr)
    p = ok(
        papi(
            o.client,
            "post",
            "/programs",
            json={
                "partner_id": str(o.partner.id),
                "name": f"Pilot Privat {uid()}",
                "objective": "uji",
                "start_date": "2026-12-01",
                "end_date": "2027-03-01",
                "capacity": 20,
                "responsible_user_id": str(o.ins.id),
            },
        ),
        201,
    )
    c = ok(
        papi(
            o.client,
            "post",
            f"/programs/{p['id']}/cohorts",
            json={
                "name": "Cohort Privat",
                "course_id": str(o.course.id),
                "instructor_user_id": str(o.ins.id),
                "capacity": 10,
            },
        ),
        201,
    )
    approve_and_open(
        o, p["id"], c["id"], partner_verified=False
    )  # mitra sudah terverifikasi (fixture), tanpa listing publik
    users = []
    for _ in range(accept_users):
        u = learner(o.db)
        as_(o.client, o.ins)
        tok = ok(papi(o.client, "post", f"/cohorts/{c['id']}/invitations", json={"days": 14}), 201)["token"]
        r = accept(o, u, tok)
        assert r.status_code == 200, r.text
        users.append(u)
    return p, c, users


def set_program_status(o, pid, status):
    prog = o.db.get(PilotProgram, uuid.UUID(pid))
    prog.status = status
    if status == "completed":
        prog.completed_at = datetime.now(UTC)
    o.db.flush()


# ---------- 1. publik/anonim: tidak ada kebocoran ----------
def test_private_pilot_does_not_leak_to_public_surfaces(pw):
    p, c, (l1,) = run_program(pw)
    pw.client.cookies.clear()
    pw.client.headers.pop("X-CSRF-Token", None)
    assert get(pw.client, f"/courses/{pw.slug}").status_code == 404
    assert pw.slug not in {x["slug"] for x in ok(get(pw.client, "/courses", params={"page_size": 100}))["items"]}
    assert str(pw.partner.id) not in str(
        get(pw.client, "/partners", params={"page_size": 100}).json()
    )  # profil privat tidak tampil
    assert get(pw.client, f"/partners/{pw.partner.slug}").status_code == 404
    assert get(pw.client, f"/movements/{pw.movement.id}").status_code == 404
    assert str(pw.movement.id) not in str(get(pw.client, "/movements", params={"page_size": 100}).json())
    t = ok(get(pw.client, f"/traditions/{pw.world['tradition'].slug}"))
    assert pw.slug not in str(t["courses"]) and str(pw.movement.id) not in str(t["movements"])
    assert get(pw.client, f"/courses/{pw.slug}/lessons/{pw.lslug}").status_code == 404  # anonim: kursus privat tidak terlihat (ADR-0008)
    assert get(pw.client, "/pilot/invitations/preview", params={"token": "x" * 30}).status_code == 404


# ---------- 2. orang asing / undangan belum diterima ----------
def test_strangers_and_unaccepted_invitees_get_404_everywhere(pw):
    p, c, (l1,) = run_program(pw)
    as_(pw.client, pw.ins)
    pending_tok = ok(papi(pw.client, "post", f"/cohorts/{c['id']}/invitations", json={"days": 7}), 201)[
        "token"
    ]  # tidak diterima
    stranger, invitee = learner(pw.db), learner(pw.db)
    for who in (stranger, invitee):
        as_(pw.client, who)
        assert get(pw.client, f"/courses/{pw.slug}").status_code == 404, "kursus privat bocor"
        assert get(pw.client, f"/courses/{pw.slug}/lessons/{pw.lslug}").status_code == 404
        assert pw.client.post(f"/api/v1/courses/{pw.slug}/enroll").status_code == 404  # tidak bisa self-enroll
        assert (
            pw.client.put(f"/api/v1/me/lessons/{pw.lesson.id}/progress", json={"status": "completed"}).status_code
            == 404
        )
        assert (
            pw.client.post(
                "/api/v1/practice-sessions", json={"lesson_id": str(pw.lesson.id), "model_version": "uji-xyz"}
            ).status_code
            == 404
        )
        assert pw.slug not in {x["slug"] for x in ok(get(pw.client, "/courses", params={"page_size": 100}))["items"]}
        assert ok(get(pw.client, "/me/progress"))["enrollments"] == []
        assert ok(papi(pw.client, "get", "/me/portal"))["memberships"] == []
        assert papi(pw.client, "get", f"/me/cohorts/{c['id']}").status_code == 404
    assert pending_tok  # undangan yang belum diterima tidak memberi akses ke materi


# ---------- 3. peserta sah ----------
def test_member_can_learn_progress_and_practice_but_course_stays_out_of_public_catalog(pw):
    p, c, (l1,) = run_program(pw)
    as_(pw.client, l1)
    r = get(pw.client, f"/courses/{pw.slug}")
    assert r.status_code == 200 and r.json()["distribution_scope"] == "pilot_private" and r.json()["modules"]
    assert r.headers["cache-control"] == "private, no-store" and "Cookie" in r.headers["vary"]
    ld = ok(get(pw.client, f"/courses/{pw.slug}/lessons/{pw.lslug}"))
    assert ld["movement"]["id"] == str(pw.movement.id) and ld["practice"]["available"] is True
    assert pw.slug not in {
        x["slug"] for x in ok(get(pw.client, "/courses", params={"page_size": 100}))["items"]
    }  # publik tetap tanpa privat
    assert any(e["course"]["slug"] == pw.slug for e in ok(get(pw.client, "/me/progress"))["enrollments"])
    out = ok(pw.client.put(f"/api/v1/me/lessons/{pw.lesson.id}/progress", json={"status": "completed"}))
    assert out["enrollment"]["progress"]["completed"] == 1 and out["enrollment"]["progress"]["total"] == 3
    s = pw.client.post("/api/v1/practice-sessions", json={"lesson_id": str(pw.lesson.id), "model_version": "uji"})
    assert s.status_code == 201, s.text
    portal = ok(papi(pw.client, "get", "/me/portal"))["memberships"][0]
    assert portal["course_slug"] == pw.slug and portal["progress"]["completed"] == 1
    cohort = ok(papi(pw.client, "get", f"/me/cohorts/{c['id']}"))
    assert [x["completed"] for x in cohort["lessons"]] == [True, False, False]
    # Profil mitra privat TETAP tidak publik walau peserta sudah belajar
    pw.client.cookies.clear()
    assert get(pw.client, f"/partners/{pw.partner.slug}").status_code == 404


# ---------- 4. peran pengelola ----------
def test_role_matrix_for_private_course_and_pilot_resources(pw):
    p, c, (l1,) = run_program(pw)
    # pratinjau (baca): ditugaskan, manager mitra, kurator, admin → 200; instruktur mitra tak ditugaskan & mitra lain → 404
    expect = {"ins": 200, "mgr": 200, "cur": 200, "adm": 200, "ins2": 404, "outsider": 404}
    for name, code in expect.items():
        as_(pw.client, getattr(pw, name))
        assert get(pw.client, f"/courses/{pw.slug}").status_code == code, name
    # pratinjau tidak boleh mencatat progres/ berlatih sebagai peserta
    as_(pw.client, pw.ins)
    r = pw.client.put(f"/api/v1/me/lessons/{pw.lesson.id}/progress", json={"status": "completed"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "PREVIEW_ONLY"
    assert pw.client.post(f"/api/v1/courses/{pw.slug}/enroll").status_code == 404
    # sumber daya pilot lintas partner
    for who in (pw.outsider, pw.ins2):
        as_(pw.client, who)
        for path in (
            f"/programs/{p['id']}",
            f"/cohorts/{c['id']}",
            f"/cohorts/{c['id']}/dashboard",
            f"/cohorts/{c['id']}/notes",
            f"/programs/{p['id']}/analytics",
            f"/programs/{p['id']}/report.csv",
        ):
            if who is pw.ins2 and path.startswith("/programs") and "analytics" not in path and "report" not in path:
                assert papi(pw.client, "get", path).status_code == 200  # anggota mitra boleh melihat program mitranya
            else:
                assert papi(pw.client, "get", path).status_code == 404, (who.role, path)
    # peserta tidak melihat roster/dashboard/analytics
    as_(pw.client, l1)
    for path in (
        f"/programs/{p['id']}",
        f"/cohorts/{c['id']}",
        f"/cohorts/{c['id']}/dashboard",
        f"/programs/{p['id']}/analytics",
    ):
        assert papi(pw.client, "get", path).status_code == 403, path


# ---------- 5. siklus hidup status program ----------
def test_access_follows_program_lifecycle(pw):
    p, c, (l1,) = run_program(pw)
    as_(pw.client, l1)
    assert get(pw.client, f"/courses/{pw.slug}").status_code == 200
    # selesai: baca-saja historis
    set_program_status(pw, p["id"], "completed")
    assert get(pw.client, f"/courses/{pw.slug}").status_code == 200
    assert get(pw.client, f"/courses/{pw.slug}/lessons/{pw.lslug}").status_code == 200
    assert papi(pw.client, "get", f"/me/cohorts/{c['id']}").status_code == 200
    r = pw.client.put(f"/api/v1/me/lessons/{pw.lesson.id}/progress", json={"status": "completed"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "PROGRAM_READ_ONLY"
    r = pw.client.post("/api/v1/practice-sessions", json={"lesson_id": str(pw.lesson.id), "model_version": "uji-xyz"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "PROGRAM_READ_ONLY"
    # dibatalkan / diarsipkan / kembali draf: akses ditutup (tidak diasumsikan aktif selamanya)
    for st in ("cancelled", "archived", "draft", "pending_approval"):
        set_program_status(pw, p["id"], st)
        assert get(pw.client, f"/courses/{pw.slug}").status_code == 404, st
        assert get(pw.client, f"/courses/{pw.slug}/lessons/{pw.lslug}").status_code == 404, st
        assert ok(papi(pw.client, "get", "/me/portal"))["memberships"] == [], st
        assert papi(pw.client, "get", f"/me/cohorts/{c['id']}").status_code == 404, st
    set_program_status(pw, p["id"], "active")
    assert get(pw.client, f"/courses/{pw.slug}").status_code == 200  # akses pulih ketika program sah kembali


def test_withdrawn_or_removed_member_loses_access(pw):
    p, c, (l1, l2) = run_program(pw, accept_users=2)
    as_(pw.client, l1)
    assert papi(pw.client, "delete", f"/me/cohorts/{c['id']}").status_code == 204
    assert get(pw.client, f"/courses/{pw.slug}").status_code == 404
    as_(pw.client, pw.ins)
    assert papi(pw.client, "delete", f"/cohorts/{c['id']}/members/{l2.id}").status_code == 204
    as_(pw.client, l2)
    assert get(pw.client, f"/courses/{pw.slug}").status_code == 404


def test_member_of_one_private_course_cannot_open_another_private_course(pw):
    p, c, (l1,) = run_program(pw)
    other = Course(
        slug=f"priv-{uid()}",
        title="Kursus privat lain",
        tradition_id=pw.world["tradition"].id,
        partner_id=pw.partner.id,
        distribution_scope="pilot_private",
        status="published",
        is_demo=True,
        source_citation="s",
        published_at=datetime.now(UTC),
    )
    pw.db.add(other)
    pw.db.flush()
    as_(pw.client, l1)
    assert get(pw.client, f"/courses/{other.slug}").status_code == 404
    assert pw.client.post(f"/api/v1/courses/{other.slug}/enroll").status_code == 404


# ---------- 6. media ----------
def test_cohort_scoped_media_requires_membership_consent_and_clean_scan(pw):
    p, c, (l1,) = run_program(pw)
    stranger = learner(pw.db)
    as_(pw.client, pw.ins)
    m = ok(
        pw.client.post(
            f"/api/v1/studio/movements/{pw.movement.id}/media",
            data=media_form(),
            files={"file": ("a.webm", io.BytesIO(WEBM + b"0" * 64), "video/webm")},
        ),
        201,
    )
    mid = m["id"]
    row = pw.db.get(ReferenceMedia, uuid.UUID(mid))
    as_(pw.client, pw.mgr)
    # belum dapat dibagikan: izin belum terverifikasi / belum dipindai
    assert papi_studio(pw, mid, {"access_level": "pilot_cohort"}).status_code == 409
    ok(papi_studio(pw, mid, {"consent_status": "verified", "permission_evidence_ref": "izin tertulis"}))
    assert (
        papi_studio(pw, mid, {"access_level": "pilot_cohort"}).status_code == 409
    )  # belum clean (scanner nonaktif => not_scanned)
    row.scan_status = "clean"
    pw.db.flush()
    ok(papi_studio(pw, mid, {"access_level": "pilot_cohort"}))
    as_(pw.client, l1)
    r = pw.client.get(f"/api/v1/media/{mid}/file")
    assert r.status_code == 200 and r.headers["cache-control"] == "private, no-store"  # tidak di-cache publik
    ld = ok(get(pw.client, f"/courses/{pw.slug}/lessons/{pw.lslug}"))
    assert mid in str(ld["movement"]["document"]["media"]) if ld["movement"]["document"] else True
    for who in (stranger, None):
        if who:
            as_(pw.client, who)
        else:
            pw.client.cookies.clear()
        assert pw.client.get(f"/api/v1/media/{mid}/file").status_code == 404
    # pencabutan izin = langsung tertutup untuk SEMUA (termasuk peserta, pengelola, kurator, admin)
    as_(pw.client, pw.mgr)
    ok(papi_studio(pw, mid, {"consent_status": "revoked"}))
    for u in (l1, pw.mgr, pw.ins, pw.cur, pw.adm):
        as_(pw.client, u)
        assert pw.client.get(f"/api/v1/media/{mid}/file").status_code == 404, u.role
    # program dibatalkan: peserta kehilangan media meski izin dipulihkan
    row.consent_status, row.access_level = "verified", "pilot_cohort"
    pw.db.flush()
    set_program_status(pw, p["id"], "cancelled")
    as_(pw.client, l1)
    assert pw.client.get(f"/api/v1/media/{mid}/file").status_code == 404


def papi_studio(pw, mid, body):
    return pw.client.patch(f"/api/v1/studio/media/{mid}", json=body)


# ---------- 7. penerbitan konten untuk mitra privat ----------
def test_private_partner_can_publish_course_and_movement_without_public_listing(pw):
    # kursus privat: terbit lewat alur /manage TANPA mitra tampil publik
    as_(pw.client, pw.ins)
    c = ok(
        pw.client.post(
            "/api/v1/manage/courses",
            json={
                "title": f"Kursus Privat {uid()}",
                "tradition_id": str(pw.world["tradition"].id),
                "partner_id": str(pw.partner.id),
                "distribution_scope": "pilot_private",
                "source_citation": "sumber",
            },
        ),
        201,
    )
    cid = c["fields"]["id"]
    assert c["fields"]["distribution_scope"] == "pilot_private"
    assert pw.client.post(f"/api/v1/manage/courses/{cid}/transition", json={"action": "submit"}).status_code == 200
    as_(pw.client, pw.cur)
    assert (
        pw.client.post(
            f"/api/v1/manage/courses/{cid}/transition", json={"action": "approve", "approval_evidence_ref": "bukti"}
        ).status_code
        == 200
    )
    as_(pw.client, pw.adm)
    r = pw.client.post(f"/api/v1/manage/courses/{cid}/transition", json={"action": "publish"})
    assert r.status_code == 200, r.text
    pw.client.cookies.clear()
    assert get(pw.client, f"/courses/{c['fields']['slug']}").status_code == 404  # tetap tidak publik
    # cakupan tidak dapat diubah diam-diam setelah terbit
    as_(pw.client, pw.cur)
    assert pw.client.patch(f"/api/v1/manage/courses/{cid}", json={"distribution_scope": "public"}).status_code == 409
    # mitra BELUM terverifikasi: kursus privat tidak boleh terbit
    pw.partner.verification_status, pw.partner.verification_decided_by_user_id = "pending_verification", None
    pw.db.flush()
    as_(pw.client, pw.ins)
    c2 = ok(
        pw.client.post(
            "/api/v1/manage/courses",
            json={
                "title": f"Privat2 {uid()}",
                "tradition_id": str(pw.world["tradition"].id),
                "partner_id": str(pw.partner.id),
                "distribution_scope": "pilot_private",
                "source_citation": "s",
            },
        ),
        201,
    )
    pw.client.post(f"/api/v1/manage/courses/{c2['fields']['id']}/transition", json={"action": "submit"})
    as_(pw.client, pw.cur)
    pw.client.post(
        f"/api/v1/manage/courses/{c2['fields']['id']}/transition",
        json={"action": "approve", "approval_evidence_ref": "b"},
    )
    as_(pw.client, pw.adm)
    r = pw.client.post(f"/api/v1/manage/courses/{c2['fields']['id']}/transition", json={"action": "publish"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "PARTNER_NOT_VERIFIED"


def test_pilot_program_can_run_with_private_course_for_unlisted_partner_and_profile_stays_private(pw):
    p, c, (l1,) = run_program(pw)
    assert ok(papi(pw.client, "get", f"/programs/{p['id']}")) if as_(pw.client, pw.mgr) else None
    pw.client.cookies.clear()
    assert pw.partner.slug not in str(get(pw.client, "/partners", params={"page_size": 100}).json())
    assert get(pw.client, "/instructors", params={"page_size": 100}).status_code == 200
    # publikasi gerakan oleh mitra privat tidak memaksa listing (lihat test_studio untuk alur lengkap): gerakan tetap tidak publik
    assert get(pw.client, f"/movements/{pw.movement.id}").status_code == 404


_ = (Lesson, Movement, MovementDocument, Partner, PilotCohort, select)
