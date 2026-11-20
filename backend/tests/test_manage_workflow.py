import pytest
from sqlalchemy import select

from app.models import AuditLog, CulturalTradition
from tests.factories import login, make_user, make_world, uid


def as_user(client, db, role):
    client.cookies.clear()
    client.headers.pop("X-CSRF-Token", None)
    u = make_user(db, role)
    login(client, u)
    return u


def tr(client, kind, oid, action, **kw):
    return client.post(f"/api/v1/manage/{kind}/{oid}/transition", json={"action": action, **kw})


def new_tradition(client, **over):
    body = {"name": f"Tradisi Uji {uid()}", "access_scope": "public",
            "source_citation": "Sumber uji"}
    body.update(over)
    r = client.post("/api/v1/manage/traditions", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_learner_cannot_use_management(client, db):
    as_user(client, db, "learner")
    assert client.get("/api/v1/manage/traditions").status_code == 403
    assert client.post("/api/v1/manage/traditions", json={"name": "x"}).status_code == 403
    assert client.get("/api/v1/manage/kinds").status_code == 403


def test_anonymous_gets_401(client):
    assert client.get("/api/v1/manage/traditions").status_code == 401


def test_instructor_kinds_limited(client, db):
    as_user(client, db, "instructor")
    keys = {k["key"] for k in client.get("/api/v1/manage/kinds").json()}
    assert keys == {"courses", "lessons"}
    assert client.post("/api/v1/manage/traditions", json={"name": "x"}).status_code == 403
    assert client.get("/api/v1/manage/partners").status_code == 403


def test_create_forces_draft_and_blocks_mass_assignment(client, db):
    as_user(client, db, "curator")
    d = new_tradition(client)
    assert d["fields"]["status"] == "draft" and d["fields"]["is_demo"] is False
    for bad in ({"status": "published"}, {"is_demo": True}, {"approved_by_user_id": "x"},
                {"created_by_user_id": "x"}, {"deleted_at": "2020-01-01T00:00:00Z"}):
        r = client.post("/api/v1/manage/traditions", json={"name": "x", **bad})
        assert r.status_code == 422, bad
    r = client.patch(f"/api/v1/manage/traditions/{d['fields']['id']}", json={"status": "published"})
    assert r.status_code == 422


def test_full_workflow_publish_and_unpublish(client, db):
    author = as_user(client, db, "curator")
    d = new_tradition(client)
    oid, slug = d["fields"]["id"], d["fields"]["slug"]
    # draft tidak bocor
    assert client.get(f"/api/v1/traditions/{slug}").status_code == 404
    assert tr(client, "traditions", oid, "submit").status_code == 200
    # penulis (curator) tidak boleh menyetujui kontennya sendiri
    r = tr(client, "traditions", oid, "approve", approval_evidence_ref="bukti")
    assert r.status_code == 403 and r.json()["error"]["code"] == "SELF_APPROVAL"
    assert client.get(f"/api/v1/traditions/{slug}").status_code == 404  # pending tidak bocor
    # curator lain: butuh bukti untuk konten non-demo
    other = as_user(client, db, "curator")
    assert tr(client, "traditions", oid, "approve").json()["error"]["code"] == "EVIDENCE_REQUIRED"
    r = tr(client, "traditions", oid, "approve", approval_evidence_ref="Surat persetujuan uji #1")
    assert r.status_code == 200 and r.json()["fields"]["status"] == "verified"
    assert r.json()["fields"]["approved_by_user_id"] == str(other.id)
    assert client.get(f"/api/v1/traditions/{slug}").status_code == 404  # verified belum publik
    r = tr(client, "traditions", oid, "publish")
    assert r.status_code == 200 and r.json()["fields"]["published_at"]
    pub = client.get(f"/api/v1/traditions/{slug}")
    assert pub.status_code == 200
    assert pub.json()["provenance"]["verification_label"] == "Terverifikasi oleh mitra"
    assert pub.json()["provenance"]["approved_by_name"] == other.display_name
    # published tidak bisa diedit langsung
    assert client.patch(f"/api/v1/manage/traditions/{oid}", json={"name": "baru"}).status_code == 409
    assert tr(client, "traditions", oid, "unpublish").status_code == 200
    assert client.get(f"/api/v1/traditions/{slug}").status_code == 404
    # audit trail lengkap
    actions = [a.action for a in db.scalars(select(AuditLog).where(
        AuditLog.entity_id == oid).order_by(AuditLog.created_at))]
    assert actions == ["content.create", "content.submit", "content.approve", "content.publish",
                       "content.unpublish"]
    hist = client.get(f"/api/v1/manage/traditions/{oid}").json()["history"]
    assert {h["action"] for h in hist} >= {"content.publish", "content.unpublish"}
    _ = author


def test_submit_needs_source_reject_needs_note_invalid_transitions(client, db):
    as_user(client, db, "curator")
    d = new_tradition(client, source_citation=None)
    oid = d["fields"]["id"]
    assert tr(client, "traditions", oid, "submit").json()["error"]["code"] == "SOURCE_REQUIRED"
    assert client.patch(f"/api/v1/manage/traditions/{oid}",
                        json={"source_citation": "ada sumber"}).status_code == 200
    assert tr(client, "traditions", oid, "publish").status_code == 409  # draft -> publish ilegal
    tr(client, "traditions", oid, "submit")
    as_user(client, db, "curator")
    assert tr(client, "traditions", oid, "reject").json()["error"]["code"] == "NOTE_REQUIRED"
    r = tr(client, "traditions", oid, "reject", note="Sumber kurang")
    assert r.json()["fields"]["status"] == "rejected" and r.json()["fields"]["review_note"] == "Sumber kurang"
    # ditolak -> dapat diedit dan diajukan ulang
    assert client.patch(f"/api/v1/manage/traditions/{oid}", json={"region": "R"}).status_code == 200
    assert tr(client, "traditions", oid, "submit").status_code == 200


def test_instructor_cannot_approve_or_publish_and_sees_only_own(client, db):
    w = make_world(db)  # tradisi+mitra published untuk referensi
    inst = as_user(client, db, "instructor")
    body = {"title": f"Kurikulum Saya {uid()}", "tradition_id": str(w["tradition"].id),
            "partner_id": str(w["partner"].id), "source_citation": "sumber"}
    r = client.post("/api/v1/manage/courses", json=body)
    assert r.status_code == 201, r.text
    cid = r.json()["fields"]["id"]
    assert r.json()["fields"]["created_by_user_id"] == str(inst.id)
    assert r.json()["allowed_actions"] == ["submit"]
    assert tr(client, "courses", cid, "submit").status_code == 200
    for act in ("approve", "reject", "publish"):
        assert tr(client, "courses", cid, act, note="x").status_code == 403
    # instruktur lain tidak melihat / tidak bisa mengubah (404, bukan 403)
    as_user(client, db, "instructor")
    items = client.get("/api/v1/manage/courses").json()["items"]
    assert cid not in {i["id"] for i in items}
    assert client.get(f"/api/v1/manage/courses/{cid}").status_code == 404
    assert client.patch(f"/api/v1/manage/courses/{cid}", json={"summary": "x"}).status_code == 404
    assert client.delete(f"/api/v1/manage/courses/{cid}").status_code == 404
    assert tr(client, "courses", cid, "submit").status_code == 404


def test_publish_requires_published_parents_and_instructor_flow(client, db):
    cur = as_user(client, db, "curator")
    t, p = new_tradition(client), None
    r = client.post("/api/v1/manage/partners", json={
        "name": f"Mitra {uid()}", "partner_type": "school", "source_citation": "s"})
    assert r.status_code == 201, r.text
    p = r.json()
    # Verifikasi TIDAK dapat diisi lewat /manage (celah ditutup); di sini disimulasikan keputusan admin di DB.
    from datetime import UTC, datetime

    from app.models import Partner
    row = db.get(Partner, p["fields"]["id"])
    row.verification_status, row.public_listing_consent = "verified", True
    row.verification_decided_by_user_id, row.verification_decided_at = cur.id, datetime.now(UTC)
    db.flush()
    r = client.post("/api/v1/manage/courses", json={
        "title": f"K {uid()}", "tradition_id": t["fields"]["id"], "partner_id": p["fields"]["id"],
        "source_citation": "s"})
    c = r.json()
    for kind, obj in (("traditions", t), ("partners", p), ("courses", c)):
        tr(client, kind, obj["fields"]["id"], "submit")
    as_user(client, db, "curator")
    for kind, obj in (("traditions", t), ("partners", p), ("courses", c)):
        assert tr(client, kind, obj["fields"]["id"], "approve",
                  approval_evidence_ref="bukti uji").status_code == 200
    # kursus tidak bisa terbit sebelum tradisi/mitranya terbit
    r = tr(client, "courses", c["fields"]["id"], "publish")
    assert r.status_code == 409 and r.json()["error"]["code"] == "PARENT_NOT_PUBLISHED"
    assert tr(client, "traditions", t["fields"]["id"], "publish").status_code == 200
    assert tr(client, "partners", p["fields"]["id"], "publish").status_code == 200
    assert tr(client, "courses", c["fields"]["id"], "publish").status_code == 200
    assert client.get(f"/api/v1/courses/{c['fields']['slug']}").status_code == 200
    # unpublish tradisi menyembunyikan kursus turunannya dari publik
    tr(client, "traditions", t["fields"]["id"], "unpublish")
    assert client.get(f"/api/v1/courses/{c['fields']['slug']}").status_code == 404
    _ = cur


def test_manage_cannot_set_verification_or_listing_consent(client, db):
    as_user(client, db, "curator")
    for extra in ({"verification_status": "verified"}, {"public_listing_consent": True}):
        r = client.post("/api/v1/manage/partners", json={"name": f"M {uid()}", "partner_type": "school", **extra})
        assert r.status_code == 422, r.text


def test_non_public_scope_and_unverified_partner_cannot_publish(client, db):
    as_user(client, db, "curator")
    t = new_tradition(client, access_scope="restricted")
    p = client.post("/api/v1/manage/partners", json={
        "name": f"M {uid()}", "partner_type": "school", "source_citation": "s"}).json()
    for kind, o in (("traditions", t), ("partners", p)):
        tr(client, kind, o["fields"]["id"], "submit")
    as_user(client, db, "curator")
    for kind, o in (("traditions", t), ("partners", p)):
        tr(client, kind, o["fields"]["id"], "approve", approval_evidence_ref="b")
    assert tr(client, "traditions", t["fields"]["id"], "publish").json()["error"]["code"] == "NOT_PUBLIC_SCOPE"
    assert tr(client, "partners", p["fields"]["id"], "publish").json()["error"]["code"] == "PARTNER_NOT_VERIFIED"


def test_validation_unknown_kind_slug_conflict_and_bad_reference(client, db):
    as_user(client, db, "curator")
    assert client.get("/api/v1/manage/hacks").status_code == 404
    assert client.post("/api/v1/manage/traditions", json={}).status_code == 422
    assert client.post("/api/v1/manage/traditions",
                       json={"name": "x", "slug": "Bad Slug!"}).status_code == 422
    assert client.post("/api/v1/manage/traditions",
                       json={"name": "x", "source_url": "javascript:alert(1)"}).status_code == 422
    n = f"Nama Sama {uid()}"
    a, b = new_tradition(client, name=n), new_tradition(client, name=n)
    assert a["fields"]["slug"] != b["fields"]["slug"]  # slug otomatis unik
    r = client.post("/api/v1/manage/courses", json={
        "title": "x", "tradition_id": str(__import__("uuid").uuid4()),
        "partner_id": str(__import__("uuid").uuid4())})
    assert r.status_code == 422 and r.json()["error"]["code"] == "INVALID_REFERENCE"
    assert client.get("/api/v1/manage/traditions/bukan-uuid").status_code == 404


def test_modules_lessons_materials_and_ownership(client, db):
    w = make_world(db)
    inst = as_user(client, db, "instructor")
    c = client.post("/api/v1/manage/courses", json={
        "title": f"K {uid()}", "tradition_id": str(w["tradition"].id),
        "partner_id": str(w["partner"].id), "source_citation": "s"}).json()
    cid = c["fields"]["id"]
    m = client.post("/api/v1/manage/modules", json={"course_id": cid, "title": "Modul A",
                                                    "order_index": 1})
    assert m.status_code == 201
    mid = m.json()["id"]
    lesson = client.post("/api/v1/manage/lessons", json={
        "title": "Pelajaran A", "course_id": cid, "module_id": mid, "body": "isi",
        "source_citation": "s"})
    assert lesson.status_code == 201, lesson.text
    lid = lesson.json()["fields"]["id"]
    mat = client.post("/api/v1/manage/materials", json={
        "lesson_id": lid, "kind": "text", "title": "Catatan", "content": "teks",
        "attribution_text": "Penulis uji"})
    assert mat.status_code == 201
    assert client.post("/api/v1/manage/materials", json={
        "lesson_id": lid, "kind": "link", "title": "T", "attribution_text": "a"}).status_code == 422
    assert client.post("/api/v1/manage/materials", json={
        "lesson_id": lid, "kind": "text", "title": "T"}).status_code == 422  # atribusi wajib
    detail = client.get(f"/api/v1/manage/lessons/{lid}").json()
    assert len(detail["materials"]) == 1
    # modul dari kursus lain tidak boleh dipakai (FK komposit)
    other = client.post("/api/v1/manage/courses", json={
        "title": f"K2 {uid()}", "tradition_id": str(w["tradition"].id),
        "partner_id": str(w["partner"].id)}).json()["fields"]["id"]
    bad = client.post("/api/v1/manage/lessons", json={
        "title": "X", "course_id": other, "module_id": mid})
    assert bad.status_code == 422
    # modul tidak kosong tidak bisa dihapus
    assert client.delete(f"/api/v1/manage/modules/{mid}").status_code == 409
    # instruktur lain tidak boleh menambah pelajaran/modul di kursus ini
    as_user(client, db, "instructor")
    assert client.post("/api/v1/manage/modules", json={"course_id": cid, "title": "Intrusi"}).status_code == 403
    assert client.post("/api/v1/manage/lessons", json={
        "title": "Intrusi", "course_id": cid, "module_id": mid}).status_code == 403
    assert client.post("/api/v1/manage/materials", json={
        "lesson_id": lid, "kind": "text", "title": "T", "attribution_text": "a"}).status_code == 403
    _ = inst


def test_soft_delete_hides_and_only_for_editable(client, db):
    as_user(client, db, "curator")
    d = new_tradition(client)
    oid = d["fields"]["id"]
    assert client.delete(f"/api/v1/manage/traditions/{oid}").status_code == 204
    assert client.get(f"/api/v1/manage/traditions/{oid}").status_code == 404
    row = db.get(CulturalTradition, oid)
    assert row is not None and row.deleted_at is not None  # soft delete: baris tetap ada


def test_list_filters_and_pagination(client, db):
    as_user(client, db, "curator")
    tag = uid()
    for i in range(3):
        new_tradition(client, name=f"Daftar {tag} {i}")
    r = client.get("/api/v1/manage/traditions", params={"q": tag, "status": "draft", "page_size": 2})
    j = r.json()
    assert j["total"] == 3 and len(j["items"]) == 2 and j["total_pages"] == 2
    assert client.get("/api/v1/manage/traditions", params={"q": tag, "status": "published"}).json()["total"] == 0


@pytest.mark.parametrize("role", ["curator", "instructor"])
def test_manage_mutations_need_csrf(client, db, role):
    as_user(client, db, role)
    del client.headers["X-CSRF-Token"]
    kind = "courses" if role == "instructor" else "traditions"
    assert client.post(f"/api/v1/manage/{kind}", json={"name": "x", "title": "x"}).status_code == 403
