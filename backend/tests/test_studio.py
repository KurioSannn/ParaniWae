"""Instructor & Partner Studio: mitra, dokumentasi gerakan berversi, review, media, anotasi, lintas organisasi."""

import io
from datetime import UTC, datetime

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.core.config import get_settings
from app.models import AuditLog, Movement, MovementDocument, Partner
from tests.factories import login, make_user, make_world, uid

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
WEBM = b"\x1a\x45\xdf\xa3" + b"0" * 64
PDF = b"%PDF-1.4\n" + b"0" * 64


@pytest.fixture(autouse=True)
def _media_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "media_dir", str(tmp_path / "media"))


def as_(client, user):
    client.cookies.clear()
    client.headers.pop("X-CSRF-Token", None)
    login(client, user)
    return user


def api(client, method, path, **kw):
    return getattr(client, method)(f"/api/v1{path}", **kw)


def ok(r, code=200):
    assert r.status_code == code, r.text
    return r.json()


class W:
    """Dunia uji: satu mitra non-demo terverifikasi + dua instruktur anggota + mitra lain + staf."""


@pytest.fixture
def w(client, db):
    o = W()
    o.world = make_world(db, "published")
    o.trad = o.world["tradition"]
    o.mgr, o.inst, o.other = make_user(db, "instructor"), make_user(db, "instructor"), make_user(db, "instructor")
    o.cur, o.cur2 = make_user(db, "curator"), make_user(db, "curator")
    o.adm, o.adm2, o.learner = make_user(db, "admin"), make_user(db, "admin"), make_user(db, "learner")
    o.client = client
    # mitra dibuat lewat API (non-demo), lengkap, diverifikasi admin lain
    as_(client, o.mgr)
    p = ok(
        api(
            client,
            "post",
            "/studio/partners",
            json={
                "name": f"Mitra {uid()}",
                "partner_type": "school",
                "responsible_name": "Penanggung Jawab Uji",
                "responsible_role": "Ketua",
                "contact_email": "mitra@uji.test",
            },
        ),
        201,
    )
    o.pid = p["id"]
    ok(api(client, "put", f"/studio/partners/{o.pid}/traditions/{o.trad.id}"))
    ok(
        api(client, "post", f"/studio/partners/{o.pid}/members", json={"email": o.inst.email, "role": "instructor"}),
        201,
    )
    ok(
        api(
            client,
            "post",
            f"/studio/partners/{o.pid}/documents",
            data={"kind": "approval_letter"},
            files={"file": ("surat.pdf", io.BytesIO(PDF), "application/pdf")},
        ),
        201,
    )
    ok(api(client, "post", f"/studio/partners/{o.pid}/verification", json={"action": "submit"}))
    as_(client, o.adm)
    ok(
        api(
            client,
            "post",
            f"/studio/partners/{o.pid}/verification",
            json={"action": "verify", "evidence_ref": "Surat No. 1/UJI"},
        )
    )
    as_(client, o.mgr)
    ok(api(client, "patch", f"/studio/partners/{o.pid}", json={"public_listing_consent": True}))
    as_(client, o.adm)
    ok(api(client, "post", f"/studio/partners/{o.pid}/verification", json={"action": "publish_listing"}))
    return o


def full_doc(**over):
    d = {
        "level": "beginner",
        "safety_category": "solo_beginner",
        "description": "Deskripsi uji dari instruktur.",
        "safety_guidance": "Arahan keselamatan uji.",
        "source_citation": "Sumber uji (instruktur)",
        "author_declaration": True,
        "rights_holder": "Instruktur Uji",
        "license_type": "instructor_owned",
        "usage_scope": "Pembelajaran di SILATARA",
        "prerequisites": "Tidak ada",
        "learning_context": "Pemanasan ringan",
    }
    d.update(over)
    return d


def new_movement(w, user=None, name=None, **doc):
    c = w.client
    as_(c, user or w.inst)
    m = ok(
        api(
            c,
            "post",
            "/studio/movements",
            json={"name_id": name or f"Gerakan {uid()}", "tradition_id": str(w.trad.id), "partner_id": w.pid, **doc},
        ),
        201,
    )
    return m


def fill(w, m, user=None):
    c = w.client
    if user:
        as_(c, user)
    did = m["active_document"]["id"]
    ok(api(c, "patch", f"/studio/documents/{did}", json=full_doc()))
    ok(
        api(
            c,
            "put",
            f"/studio/documents/{did}/phases",
            json={
                "phases": [
                    {"name": "Fase 1", "instruction": "Instruksi 1"},
                    {"name": "Fase 2", "instruction": "Instruksi 2", "body_focus": ["bahu"]},
                ]
            },
        )
    )
    return did


def tr(w, did, action, user, expect=200, **kw):
    as_(w.client, user)
    return (
        api(w.client, "post", f"/studio/documents/{did}/transition", json={"action": action, **kw})
        if expect is None
        else _chk(api(w.client, "post", f"/studio/documents/{did}/transition", json={"action": action, **kw}), expect)
    )


def _chk(r, expect):
    assert r.status_code == expect, r.text
    return r.json()


def publish_flow(w, did, author):
    tr(w, did, "submit", author)
    tr(w, did, "curator_review", w.cur)
    tr(w, did, "confirm_partner", w.mgr)
    tr(w, did, "approve", w.cur, evidence_ref="Berita acara uji")
    return tr(w, did, "publish", w.adm)


# ---------- mitra ----------
def test_partner_is_not_official_until_admin_verifies_with_evidence(client, db):
    inst, adm, adm2, cur = (make_user(db, r) for r in ("instructor", "admin", "admin", "curator"))
    as_(client, inst)
    p = ok(api(client, "post", "/studio/partners", json={"name": f"M {uid()}", "partner_type": "community"}), 201)
    assert p["verification_status"] == "draft" and p["my_role"] == "manager"
    assert (
        api(
            client,
            "post",
            "/studio/partners",
            json={"name": "x", "partner_type": "school", "public_listing_consent": True},
        ).status_code
        == 422
    )
    # tidak lengkap -> tidak bisa diajukan
    r = api(client, "post", f"/studio/partners/{p['id']}/verification", json={"action": "submit"})
    assert r.status_code == 422 and len(r.json()["error"]["details"]["missing"]) == 4
    api(
        client,
        "patch",
        f"/studio/partners/{p['id']}",
        json={"responsible_name": "A", "responsible_role": "B", "contact_email": "a@b.test"},
    )
    # manager tidak dapat memverifikasi dirinya sendiri
    assert (
        api(
            client, "post", f"/studio/partners/{p['id']}/verification", json={"action": "verify", "evidence_ref": "x"}
        ).status_code
        == 409
    )
    # curator tidak memutuskan verifikasi
    as_(client, cur)
    assert (
        api(
            client, "post", f"/studio/partners/{p['id']}/verification", json={"action": "verify", "evidence_ref": "x"}
        ).status_code
        == 409
    )
    # admin: butuh bukti + dokumen; menyimpan identitas & waktu
    as_(client, inst)
    api(client, "put", f"/studio/partners/{p['id']}/traditions/{make_world(db)['tradition'].id}")
    api(
        client,
        "post",
        f"/studio/partners/{p['id']}/documents",
        data={"kind": "approval_letter"},
        files={"file": ("a.png", io.BytesIO(PNG), "image/png")},
    )
    ok(api(client, "post", f"/studio/partners/{p['id']}/verification", json={"action": "submit"}))
    as_(client, adm)
    assert api(client, "post", f"/studio/partners/{p['id']}/verification", json={"action": "verify"}).status_code == 422
    d = ok(
        api(
            client,
            "post",
            f"/studio/partners/{p['id']}/verification",
            json={"action": "verify", "evidence_ref": "SK-1"},
        )
    )
    assert d["verification_status"] == "verified" and d["verification_decided_by"] == adm.display_name
    assert d["verification_decided_at"] and d["approval_evidence_ref"] == "SK-1"
    h = ok(api(client, "get", f"/studio/partners/{p['id']}/history"))
    assert [e["action"] for e in h][:2] == ["verify", "submit"] and h[0]["actor"] == adm.display_name
    _ = adm2


def test_admin_member_cannot_verify_own_partner(client, db):
    adm = make_user(db, "admin")
    as_(client, adm)
    p = ok(
        api(
            client,
            "post",
            "/studio/partners",
            json={
                "name": f"M {uid()}",
                "partner_type": "school",
                "responsible_name": "A",
                "responsible_role": "B",
                "contact_email": "a@b.test",
            },
        ),
        201,
    )
    api(client, "put", f"/studio/partners/{p['id']}/traditions/{make_world(db)['tradition'].id}")
    api(
        client,
        "post",
        f"/studio/partners/{p['id']}/documents",
        data={"kind": "other"},
        files={"file": ("a.pdf", io.BytesIO(PDF), "application/pdf")},
    )
    ok(api(client, "post", f"/studio/partners/{p['id']}/verification", json={"action": "submit"}))
    r = api(client, "post", f"/studio/partners/{p['id']}/verification", json={"action": "verify", "evidence_ref": "x"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "SELF_APPROVAL"


def test_cross_org_partner_and_documents_are_404(client, db, w):
    as_(client, w.other)
    assert api(client, "get", f"/studio/partners/{w.pid}").status_code == 404
    assert api(client, "patch", f"/studio/partners/{w.pid}", json={"city": "x"}).status_code == 404
    assert w.pid not in {i["id"] for i in ok(api(client, "get", "/studio/partners"))["items"]}
    as_(client, w.mgr)
    doc = ok(api(client, "get", f"/studio/partners/{w.pid}"))["documents"][0]
    assert api(client, "get", f"/studio/partner-documents/{doc['id']}/file").status_code == 200
    as_(client, w.inst)  # anggota biasa tidak melihat dokumen persetujuan
    assert api(client, "get", f"/studio/partner-documents/{doc['id']}/file").status_code == 404
    assert ok(api(client, "get", f"/studio/partners/{w.pid}"))["documents"] == []
    as_(client, w.other)
    assert api(client, "get", f"/studio/partner-documents/{doc['id']}/file").status_code == 404
    as_(client, w.learner)
    assert api(client, "get", "/studio/partners").status_code == 403


def test_partner_document_type_and_size_validation(client, db):
    inst = make_user(db, "instructor")
    as_(client, inst)
    p = ok(api(client, "post", "/studio/partners", json={"name": f"M {uid()}", "partner_type": "school"}), 201)
    r = api(
        client,
        "post",
        f"/studio/partners/{p['id']}/documents",
        data={"kind": "other"},
        files={"file": ("x.pdf", io.BytesIO(b"MZ\x90\x00 bukan pdf"), "application/pdf")},
    )
    assert r.status_code == 415
    r = api(
        client,
        "post",
        f"/studio/partners/{p['id']}/documents",
        data={"kind": "other"},
        files={"file": ("x.pdf", io.BytesIO(b""), "application/pdf")},
    )
    assert r.status_code in (415, 422)


def test_directory_lists_only_verified_consented_partners(client, db, w):
    lst = ok(client.get("/api/v1/partners"))["items"]
    me = next(x for x in lst if x["id"] == w.pid)
    assert me["provenance"]["partner_verified"] is True and me["provenance"]["approved_by_name"] == w.adm.display_name
    # ditangguhkan -> hilang dari direktori
    as_(client, w.adm)
    ok(api(client, "post", f"/studio/partners/{w.pid}/verification", json={"action": "suspend", "note": "uji"}))
    client.cookies.clear()
    assert w.pid not in {x["id"] for x in ok(client.get("/api/v1/partners"))["items"]}


# ---------- dokumentasi & versi ----------
def test_create_edit_and_completeness_gate(client, db, w):
    m = new_movement(w)
    assert m["active_document"]["status"] == "draft" and m["active_document"]["version_no"] == 1
    did = m["active_document"]["id"]
    r = api(client, "post", f"/studio/documents/{did}/transition", json={"action": "submit"})
    assert (
        r.status_code == 422 and r.json()["error"]["code"] == "INCOMPLETE" and r.json()["error"]["details"]["missing"]
    )
    fill(w, m)
    ok(api(client, "post", f"/studio/documents/{did}/transition", json={"action": "submit"}))
    # setelah diajukan: tidak bisa diedit
    assert api(client, "patch", f"/studio/documents/{did}", json={"description": "x"}).status_code == 409
    assert api(client, "put", f"/studio/documents/{did}/phases", json={"phases": []}).status_code == 409


def test_movement_requires_tradition_in_partner_scope_and_membership(client, db, w):
    as_(client, w.inst)
    other_trad = make_world(db)["tradition"]
    r = api(
        client,
        "post",
        "/studio/movements",
        json={"name_id": "x", "tradition_id": str(other_trad.id), "partner_id": w.pid},
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "TRADITION_NOT_IN_SCOPE"
    as_(client, w.other)
    assert (
        api(
            client,
            "post",
            "/studio/movements",
            json={"name_id": "x", "tradition_id": str(w.trad.id), "partner_id": w.pid},
        ).status_code
        == 404
    )


def test_validation_rejects_bad_input_and_mass_assignment(client, db, w):
    m = new_movement(w)
    did = m["active_document"]["id"]
    for bad in (
        {"status": "published"},
        {"level": "master"},
        {"safety_category": "x"},
        {"relevant_landmarks": [99]},
        {"license_type": "z"},
        {"approved_by_user_id": str(w.adm.id)},
    ):
        assert api(client, "patch", f"/studio/documents/{did}", json=bad).status_code == 422, bad
    r = api(
        client,
        "put",
        f"/studio/documents/{did}/phases",
        json={"phases": [{"name": "a", "instruction": "b", "start_ms": 9, "end_ms": 1}]},
    )
    assert r.status_code == 422


def test_full_review_flow_publish_and_public_visibility(client, db, w):
    m = new_movement(w, w.inst, name="Gerakan Alur Penuh")
    mid = m["id"]
    did = fill(w, m)
    assert client.get(f"/api/v1/movements/{mid}").status_code in (200, 404)
    client.cookies.clear()
    assert api(client, "get", f"/movements/{mid}").status_code == 404  # draf tidak bocor
    # penulis tidak boleh menyetujui/menerbitkan sendiri; instruktur lain bukan manager
    tr(w, did, "submit", w.inst)
    for act in ("curator_review", "approve", "publish", "confirm_partner"):
        r = tr(w, did, act, w.inst, expect=None)
        assert r.status_code in (403, 409), (act, r.text)
    # kurator penulis? bukan; kurator lain boleh review. Admin tidak boleh menerbitkan sebelum verified.
    assert tr(w, did, "publish", w.adm, expect=None).status_code == 409
    # approve butuh tinjauan kurator + konfirmasi mitra
    assert tr(w, did, "approve", w.cur, expect=None, evidence_ref="x").status_code == 403
    tr(w, did, "curator_review", w.cur)
    assert tr(w, did, "approve", w.cur, expect=None, evidence_ref="x").status_code == 403  # belum konfirmasi mitra
    tr(w, did, "confirm_partner", w.mgr)
    assert tr(w, did, "approve", w.cur, expect=None).status_code == 422  # tanpa bukti
    d = tr(w, did, "approve", w.cur, evidence_ref="Berita acara uji")
    assert d["active_document"]["status"] == "verified"
    assert tr(w, did, "publish", w.cur, expect=None).status_code == 403  # hanya admin
    d = tr(w, did, "publish", w.adm)
    assert d["published_version_no"] == 1 and d["practice_eligible"] is True
    row = db.get(Movement, mid)
    assert row.status == "published" and row.practice_mode == "solo_beginner" and row.assessment_enabled is False
    assert row.approved_by_user_id and row.safety_category == "solo_beginner"
    client.cookies.clear()
    pub = ok(api(client, "get", f"/movements/{mid}"))
    assert (
        pub["document"]["version_no"] == 1 and len(pub["document"]["phases"]) == 2 and pub["partner_verified"] is True
    )
    assert (
        ok(
            api(
                client,
                "get",
                "/movements",
                params={"safety_category": "solo_beginner", "partner_verified": "true", "level": "beginner"},
            )
        )["total"]
        >= 1
    )
    assert mid not in {
        x["id"] for x in ok(api(client, "get", "/movements", params={"safety_category": "restricted"}))["items"]
    }


def test_admin_cannot_self_approve_or_publish_own_documentation(client, db, w):
    m = new_movement(w, w.adm)
    did = fill(w, m)
    tr(w, did, "submit", w.adm)
    for act in ("curator_review", "reject", "approve"):
        r = tr(w, did, act, w.adm, expect=None, note="x")
        assert r.status_code == 403 and r.json()["error"]["code"] == "SELF_APPROVAL", act


def test_reject_and_revision_require_note_and_record_it(client, db, w):
    m = new_movement(w)
    did = fill(w, m)
    tr(w, did, "submit", w.inst)
    assert tr(w, did, "reject", w.cur, expect=None).status_code == 422
    assert tr(w, did, "request_revision", w.cur, expect=None).status_code == 422
    d = tr(w, did, "request_revision", w.cur, note="Lengkapi arahan keselamatan.")
    assert d["active_document"]["status"] == "needs_revision" and d["active_document"]["review_note"].startswith(
        "Lengkapi"
    )
    # penulis merevisi & mengajukan ulang; tinjauan lama direset
    as_(client, w.inst)
    ok(api(client, "patch", f"/studio/documents/{did}", json={"safety_guidance": "Revisi arahan."}))
    d = tr(w, did, "submit", w.inst)
    assert d["active_document"]["curator_reviewed_at"] is None
    d = tr(w, did, "reject", w.cur, note="Belum memadai.")
    assert d["active_document"]["status"] == "rejected" and d["active_document"]["review_note"] == "Belum memadai."
    assert ok(api(client, "get", f"/studio/movements/{m['id']}/history"))[0]["action"] == "movement.reject"


def test_versioning_keeps_published_immutable_and_archives_old(client, db, w):
    m = new_movement(w)
    did = fill(w, m)
    publish_flow(w, did, w.inst)
    as_(client, w.inst)
    # versi tayang tak bisa diubah lewat API maupun DB
    assert api(client, "patch", f"/studio/documents/{did}", json={"description": "diam-diam"}).status_code == 409
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            db.execute(text("update movement_documents set description = 'diam-diam' where id = :i"), {"i": did})
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            db.execute(
                text("insert into movement_phases(document_id,order_index,name,instruction) values (:i,9,'x','y')"),
                {"i": did},
            )
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            db.execute(text("delete from movement_documents where id = :i"), {"i": did})
    v2 = ok(api(client, "post", f"/studio/movements/{m['id']}/versions"), 201)
    assert v2["active_document"]["version_no"] == 2 and v2["active_document"]["status"] == "draft"
    assert len(v2["active_document"]["phases"]) == 2 and v2["can_create_version"] is False
    assert api(client, "post", f"/studio/movements/{m['id']}/versions").status_code == 409
    did2 = v2["active_document"]["id"]
    # versi >1 wajib changelog; versi lama tetap tayang selama v2 ditinjau
    r = api(client, "post", f"/studio/documents/{did2}/transition", json={"action": "submit"})
    assert r.status_code == 422 and any("changelog" in x.lower() for x in r.json()["error"]["details"]["missing"])
    ok(
        api(
            client,
            "patch",
            f"/studio/documents/{did2}",
            json={"changelog": "Perbaikan penjelasan fase 2.", "description": "Deskripsi v2"},
        )
    )
    tr(w, did2, "submit", w.inst)
    client.cookies.clear()
    assert ok(api(client, "get", f"/movements/{m['id']}"))["document"]["version_no"] == 1
    tr(w, did2, "curator_review", w.cur)
    tr(w, did2, "confirm_partner", w.mgr)
    tr(w, did2, "approve", w.cur, evidence_ref="BA v2")
    d = tr(w, did2, "publish", w.adm)
    assert d["published_version_no"] == 2
    statuses = {v["version_no"]: v["status"] for v in d["versions"]}
    assert statuses == {1: "archived", 2: "published"}
    client.cookies.clear()
    pub = ok(api(client, "get", f"/movements/{m['id']}"))
    assert pub["document"]["version_no"] == 2 and pub["document"]["description"] == "Deskripsi v2"
    vers = ok(api(client, "get", f"/movements/{m['id']}/versions"))
    assert [(v["version_no"], v["is_current"]) for v in vers] == [(2, True), (1, False)] and vers[0][
        "changelog"
    ].startswith("Perbaikan")
    n = db.scalar(
        select(__import__("sqlalchemy").func.count())
        .select_from(MovementDocument)
        .where(MovementDocument.movement_id == m["id"], MovementDocument.status == "published")
    )
    assert n == 1


def test_archiving_published_version_unpublishes_movement_and_practice(client, db, w):
    m = new_movement(w)
    did = fill(w, m)
    publish_flow(w, did, w.inst)
    d = tr(w, did, "archive", w.cur)
    assert d["published_version_no"] is None and d["practice_eligible"] is False
    client.cookies.clear()
    assert api(client, "get", f"/movements/{m['id']}").status_code == 404


def test_only_solo_beginner_published_opens_practice(client, db, w):
    for cat, expect in (("solo_beginner", True), ("supervised_practice", False), ("contact_practice", False)):
        m = new_movement(w)
        did = fill(w, m)
        as_(client, w.inst)
        ok(api(client, "patch", f"/studio/documents/{did}", json={"safety_category": cat}))
        d = publish_flow(w, did, w.inst)
        assert d["practice_eligible"] is expect, cat
        assert db.get(Movement, m["id"]).practice_mode == {
            "solo_beginner": "solo_beginner",
            "supervised_practice": "supervised_only",
        }.get(cat, "not_for_practice")


def test_solo_beginner_requires_prerequisites_and_context(client, db, w):
    m = new_movement(w)
    did = fill(w, m)
    ok(api(client, "patch", f"/studio/documents/{did}", json={"prerequisites": None, "learning_context": ""}))
    r = api(client, "post", f"/studio/documents/{did}/transition", json={"action": "submit"})
    assert r.status_code == 422 and len(r.json()["error"]["details"]["missing"]) == 2


def test_cross_org_movement_isolation(client, db, w):
    m = new_movement(w)
    did = fill(w, m)
    as_(client, w.other)
    assert w.pid not in {x["partner_id"] for x in ok(api(client, "get", "/studio/movements"))["items"]}
    for method, path, body in (
        ("get", f"/studio/movements/{m['id']}", None),
        ("patch", f"/studio/documents/{did}", {"description": "x"}),
        ("post", f"/studio/documents/{did}/transition", {"action": "submit"}),
        ("get", f"/studio/movements/{m['id']}/history", None),
        ("get", f"/studio/movements/{m['id']}/media", None),
    ):
        r = getattr(client, method)(f"/api/v1{path}", **({"json": body} if body else {}))
        assert r.status_code == 404, (path, r.status_code)


# ---------- integrasi lesson ----------
def test_link_lesson_and_academy_integration(client, db, w):
    world = w.world
    # kursus/pelajaran milik mitra uji: gunakan data world tetapi samakan mitra dengan mitra studio
    pid = w.pid
    from app.models import Course, Lesson

    course, lesson = world["course"], world["lessons"][0]
    course.partner_id, course.tradition_id = pid, w.trad.id
    lesson.status = "draft"
    lesson.created_by_user_id = w.inst.id
    db.flush()
    m = new_movement(w)
    did = fill(w, m)
    as_(client, w.inst)
    assert any(x["id"] == str(lesson.id) for x in ok(api(client, "get", f"/studio/movements/{m['id']}/lessons")))
    d = ok(api(client, "put", f"/studio/movements/{m['id']}/lessons/{lesson.id}"))
    assert [x["id"] for x in d["lessons"]] == [str(lesson.id)]
    publish_flow(w, did, w.inst)
    lesson.status, lesson.published_at = "published", datetime.now(UTC)
    course.status, course.published_at = "published", datetime.now(UTC)
    db.flush()
    as_(client, w.learner)
    cs = course.slug
    ok(api(client, "post", f"/courses/{cs}/enroll"))
    ld = ok(api(client, "get", f"/courses/{cs}/lessons/{lesson.slug}"))
    assert (
        ld["movement"]["id"] == m["id"]
        and ld["movement"]["document"]["phases"]
        and ld["movement"]["partner_verified"] is True
    )
    assert ld["practice"]["available"] is True
    # tautan pelajaran yang sudah terbit tidak boleh diubah diam-diam
    as_(client, w.inst)
    assert api(client, "delete", f"/studio/movements/{m['id']}/lessons/{lesson.id}").status_code == 409
    _ = Course, Lesson


# ---------- media ----------
def media_form(**over):
    f = {
        "title": "Rekaman uji",
        "rights_holder": "Instruktur Uji",
        "source_description": "Direkam sendiri",
        "license_type": "instructor_owned",
        "usage_scope": "Pembelajaran",
        "declaration_confirmed": "true",
    }
    f.update(over)
    return f


def upload(w, m, user=None, body=WEBM, name="a.webm", **over):
    if user:
        as_(w.client, user)
    return api(
        w.client,
        "post",
        f"/studio/movements/{m['id']}/media",
        data=media_form(**over),
        files={"file": (name, io.BytesIO(body), "video/webm")},
    )


def test_media_requires_declaration_and_validates_type(client, db, w):
    m = new_movement(w)
    assert upload(w, m, declaration_confirmed="false").status_code == 422
    assert upload(w, m, rights_holder="").status_code == 422
    assert upload(w, m, license_type="bebas").status_code == 422
    assert upload(w, m, body=b"MZ\x90\x00bukan media", name="x.webm").status_code == 415
    assert upload(w, m, body=b"<html><script>x</script>", name="x.png").status_code == 415
    r = ok(upload(w, m), 201)
    assert r["consent_status"] == "declared" and r["access_level"] == "private" and "storage_key" not in r


def test_media_size_limit(client, db, w, monkeypatch):
    monkeypatch.setattr(get_settings(), "media_max_video_mb", 0)
    m = new_movement(w)
    assert upload(w, m).status_code == 413


def test_media_private_by_default_and_cross_org_hidden(client, db, w):
    m = new_movement(w, w.inst)
    r = ok(upload(w, m), 201)
    mid = r["id"]
    client.cookies.clear()
    assert client.get(f"/api/v1/media/{mid}/file").status_code == 404  # anonim
    for u in (w.other, w.learner):
        as_(client, u)
        assert client.get(f"/api/v1/media/{mid}/file").status_code == 404
    for u in (w.inst, w.mgr, w.cur):
        as_(client, u)
        resp = client.get(f"/api/v1/media/{mid}/file")
        assert resp.status_code == 200 and resp.headers["cache-control"] == "private, no-store"
        assert resp.headers["x-content-type-options"] == "nosniff" and resp.content.startswith(b"\x1a\x45\xdf\xa3")
    as_(client, w.other)
    assert api(client, "patch", f"/studio/media/{mid}", json={"access_level": "public"}).status_code == 404
    assert api(client, "delete", f"/studio/media/{mid}").status_code == 404
    # anggota lain mitra yang sama melihat metadata, tetapi file private hanya uploader/manager/staf
    as_(client, w.inst)
    ok(api(client, "get", f"/studio/movements/{m['id']}/media"))


def test_media_public_requires_verified_consent_by_non_uploader_and_published_movement(client, db, w):
    m = new_movement(w, w.inst)
    did = fill(w, m)
    mid = ok(upload(w, m), 201)["id"]
    as_(client, w.inst)
    assert (
        api(client, "patch", f"/studio/media/{mid}", json={"access_level": "public"}).status_code == 403
    )  # bukan manager
    as_(client, w.mgr)
    assert (
        api(client, "patch", f"/studio/media/{mid}", json={"access_level": "public"}).status_code == 409
    )  # belum verified
    assert (
        api(client, "patch", f"/studio/media/{mid}", json={"consent_status": "verified"}).status_code == 422
    )  # tanpa bukti
    r = ok(
        api(
            client,
            "patch",
            f"/studio/media/{mid}",
            json={"consent_status": "verified", "permission_evidence_ref": "Surat izin 7"},
        )
    )
    assert r["consent_status"] == "verified"
    ok(api(client, "patch", f"/studio/media/{mid}", json={"access_level": "public"}))
    client.cookies.clear()
    assert client.get(f"/api/v1/media/{mid}/file").status_code == 404  # gerakan belum terbit
    publish_flow(w, did, w.inst)
    client.cookies.clear()
    assert client.get(f"/api/v1/media/{mid}/file").status_code == 200
    pub = ok(api(client, "get", f"/movements/{m['id']}"))
    assert [x["id"] for x in pub["document"]["media"]] == [mid] and pub["document"]["media"][0][
        "rights_holder"
    ] == "Instruktur Uji"
    # izin dicabut -> langsung tertutup
    as_(client, w.mgr)
    ok(api(client, "patch", f"/studio/media/{mid}", json={"consent_status": "revoked"}))
    client.cookies.clear()
    assert client.get(f"/api/v1/media/{mid}/file").status_code == 404


def test_uploader_cannot_verify_own_media(client, db, w):
    m = new_movement(w, w.mgr)
    mid = ok(upload(w, m, w.mgr), 201)["id"]
    r = api(
        w.client, "patch", f"/studio/media/{mid}", json={"consent_status": "verified", "permission_evidence_ref": "x"}
    )
    assert r.status_code == 403 and r.json()["error"]["code"] == "SELF_APPROVAL"
    as_(client, w.cur)
    ok(
        api(
            client, "patch", f"/studio/media/{mid}", json={"consent_status": "verified", "permission_evidence_ref": "x"}
        )
    )


def test_media_delete_removes_file_and_retention_purge(client, db, w, tmp_path):
    from datetime import timedelta

    from app.models import ReferenceMedia
    from app.services import media as media_svc
    from app.services import storage

    m = new_movement(w, w.inst)
    r = ok(upload(w, m, retention_until=str((datetime.now(UTC) + timedelta(days=5)).date())), 201)
    row = db.get(ReferenceMedia, r["id"])
    assert storage.path_for(row.storage_key).exists()
    row.retention_until = (datetime.now(UTC) - timedelta(days=1)).date()
    db.flush()
    as_(client, w.inst)
    assert client.get(f"/api/v1/media/{r['id']}/file").status_code == 404  # lewat retensi
    key = row.storage_key
    assert media_svc.purge_expired(db) == 1 and not storage.path_for(key).exists()
    r2 = ok(upload(w, m), 201)
    key2 = db.get(ReferenceMedia, r2["id"]).storage_key
    assert api(client, "delete", f"/studio/media/{r2['id']}").status_code == 204 and not storage.path_for(key2).exists()


# ---------- anotasi ----------
def test_annotations_are_instructor_reference_annotations_with_provenance(client, db, w):
    m = new_movement(w, w.inst)
    did = fill(w, m)
    mid = ok(upload(w, m), 201)["id"]
    ph = ok(api(client, "get", f"/studio/movements/{m['id']}"))["active_document"]["phases"][0]["id"]
    a = ok(
        api(
            client,
            "post",
            f"/studio/movements/{m['id']}/annotations",
            json={
                "media_id": mid,
                "phase_id": ph,
                "timestamp_ms": 1200,
                "label": "Awal fase 1",
                "model_version": "mediapipe-tasks-vision 1.2.3",
                "source_note": "Dari rekaman instruktur",
            },
        ),
        201,
    )
    assert (
        a["review_status"] == "pending"
        and a["annotator"] == w.inst.display_name
        and "ground truth" in a["provenance_label"].lower()
    )
    # target wajib tepat satu; fixture hanya demo-synthetic
    assert (
        api(
            client, "post", f"/studio/movements/{m['id']}/annotations", json={"timestamp_ms": 1, "label": "x"}
        ).status_code
        == 422
    )
    assert (
        api(
            client,
            "post",
            f"/studio/movements/{m['id']}/annotations",
            json={"fixture_key": "lain", "timestamp_ms": 1, "label": "x"},
        ).status_code
        == 422
    )
    f = ok(
        api(
            client,
            "post",
            f"/studio/movements/{m['id']}/annotations",
            json={"fixture_key": "demo-synthetic", "timestamp_ms": 0, "label": "[DEMO]"},
        ),
        201,
    )
    assert f["fixture_key"] == "demo-synthetic"
    # pembuat tidak boleh menyetujui anotasinya sendiri; manager boleh
    assert api(client, "patch", f"/studio/annotations/{a['id']}", json={"review_status": "accepted"}).status_code == 403
    as_(client, w.mgr)
    r = ok(api(client, "patch", f"/studio/annotations/{a['id']}", json={"review_status": "accepted"}))
    assert r["review_status"] == "accepted" and r["reviewed_by"] == w.mgr.display_name
    # mengubah isi mengembalikan ke pending
    as_(client, w.inst)
    r = ok(api(client, "patch", f"/studio/annotations/{a['id']}", json={"timestamp_ms": 1300}))
    assert r["review_status"] == "pending"
    assert len(ok(api(client, "get", f"/studio/movements/{m['id']}/annotations", params={"media_id": mid}))) == 1
    as_(client, w.other)
    assert api(client, "get", f"/studio/movements/{m['id']}/annotations").status_code == 404
    assert api(client, "patch", f"/studio/annotations/{a['id']}", json={"label": "x"}).status_code == 404
    _ = did


# ---------- dashboard & audit ----------
def test_dashboard_surfaces_work_that_needs_attention(client, db, w):
    m = new_movement(w, w.inst)
    did = fill(w, m)
    tr(w, did, "submit", w.inst)
    as_(client, w.cur)
    d = ok(api(client, "get", "/studio/dashboard"))
    assert any(x["kind"] == "awaiting_review" and x["document_id"] == did for x in d["attention"])
    as_(client, w.mgr)
    assert any(x["kind"] == "awaiting_confirmation" for x in ok(api(client, "get", "/studio/dashboard"))["attention"])
    as_(client, w.inst)
    d = ok(api(client, "get", "/studio/dashboard"))
    assert d["counts"]["documents_by_status"].get("pending_review", 0) >= 1 and d["partners"] and d["recent_activity"]
    assert not any(x["kind"] == "awaiting_review" for x in d["attention"])  # penulis tak diminta meninjau
    as_(client, w.other)
    d = ok(api(client, "get", "/studio/dashboard"))
    assert d["counts"]["movements"] == 0 and d["partners"] == []


def test_audit_trail_records_decisions_with_identity(client, db, w):
    m = new_movement(w)
    did = fill(w, m)
    publish_flow(w, did, w.inst)
    rows = db.scalars(select(AuditLog).where(AuditLog.entity_id == did).order_by(AuditLog.created_at)).all()
    acts = [r.action for r in rows]
    for a in (
        "movement.submit",
        "movement.curator_review",
        "movement.confirm_partner",
        "movement.approve",
        "movement.publish",
    ):
        assert a in acts, a
    assert next(r for r in rows if r.action == "movement.publish").actor_user_id == w.adm.id
    row = db.get(MovementDocument, did)
    assert (
        row.curator_reviewed_by_user_id == w.cur.id
        and row.partner_confirmed_by_user_id == w.mgr.id
        and row.approved_by_user_id == w.cur.id
    )


def test_legacy_manage_cannot_create_movements_or_set_partner_verification(client, db):
    cur = make_user(db, "curator")
    as_(client, cur)
    assert client.get("/api/v1/manage/movements").status_code == 404
    _ = Partner
