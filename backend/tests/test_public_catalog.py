import pytest

from app.models import CulturalTradition, Partner
from app.services import visibility
from tests.factories import login, make_movement, make_user, make_world, uid


def slugs(resp):
    assert resp.status_code == 200, resp.text
    return {i["slug"] for i in resp.json()["items"]}


@pytest.mark.parametrize("status", ["draft", "pending_review", "rejected", "verified", "archived"])
def test_non_published_content_never_leaks(client, db, status):
    w = make_world(db, status=status)
    t, p, c = w["tradition"], w["partner"], w["course"]
    q = {"q": t.name, "page_size": 100}
    assert t.slug not in slugs(client.get("/api/v1/traditions", params=q))
    assert p.slug not in slugs(client.get("/api/v1/partners", params={"q": p.name}))
    assert c.slug not in slugs(client.get("/api/v1/courses", params={"q": c.title}))
    for url in (f"/api/v1/traditions/{t.slug}", f"/api/v1/partners/{p.slug}",
                f"/api/v1/courses/{c.slug}"):
        assert client.get(url).status_code == 404


def test_published_content_is_visible_with_provenance(client, db):
    w = make_world(db)
    d = client.get(f"/api/v1/traditions/{w['tradition'].slug}").json()
    assert d["provenance"]["is_demo"] is True
    assert "DEMO" in d["provenance"]["verification_label"]
    assert d["provenance"]["partner_verified"] is False
    assert any(c["slug"] == w["course"].slug for c in d["courses"])
    cd = client.get(f"/api/v1/courses/{w['course'].slug}").json()
    assert [m["title"] for m in cd["modules"]] == ["Modul 1"]
    assert len(cd["modules"][0]["lessons"]) == 3
    assert "body" not in cd["modules"][0]["lessons"][0]  # isi pelajaran tidak bocor ke publik


def test_unpublished_parent_hides_children(client, db):
    w = make_world(db)
    w["tradition"].status = "draft"
    db.flush()
    assert client.get(f"/api/v1/courses/{w['course'].slug}").status_code == 404
    assert w["course"].slug not in slugs(client.get("/api/v1/courses", params={"q": w["course"].title}))


def test_demo_hidden_when_expose_demo_data_false(client, db, monkeypatch):
    w = make_world(db)

    class S:
        expose_demo_data = False

    monkeypatch.setattr(visibility, "get_settings", lambda: S())
    assert client.get(f"/api/v1/traditions/{w['tradition'].slug}").status_code == 404


def test_non_demo_partner_needs_verification_and_consent(client, db):
    base = dict(status="published", is_demo=False)
    a = Partner(slug=f"pv-{uid()}", name="X", partner_type="school", **base)
    approver = make_user(db, "curator")
    from datetime import UTC, datetime
    ok = dict(base, published_at=datetime.now(UTC), approved_by_user_id=approver.id,
              approved_at=datetime.now(UTC), source_citation="sumber", approval_evidence_ref="bukti")
    a = Partner(slug=f"pv-{uid()}", name="Tidak terverifikasi", partner_type="school", **ok)
    b = Partner(slug=f"pv-{uid()}", name="Terverifikasi", partner_type="school",
                verification_status="verified", public_listing_consent=True,
                verification_decided_by_user_id=approver.id, verification_decided_at=datetime.now(UTC), **ok)
    db.add_all([a, b])
    db.flush()
    assert client.get(f"/api/v1/partners/{a.slug}").status_code == 404
    r = client.get(f"/api/v1/partners/{b.slug}")
    assert r.status_code == 200
    assert r.json()["provenance"]["verification_label"] == "Terverifikasi oleh mitra"
    assert r.json()["provenance"]["approved_by_name"] == approver.display_name


def test_non_demo_without_evidence_is_labelled_unverified(client, db):
    from datetime import UTC, datetime
    approver = make_user(db, "curator")
    t = CulturalTradition(slug=f"nt-{uid()}", name="Tanpa bukti", access_scope="public",
                          status="published", is_demo=False, published_at=datetime.now(UTC),
                          approved_by_user_id=approver.id, approved_at=datetime.now(UTC),
                          source_citation="sumber")
    db.add(t)
    db.flush()
    p = client.get(f"/api/v1/traditions/{t.slug}").json()["provenance"]
    assert p["verification_label"] == "Belum diverifikasi mitra" and not p["partner_verified"]


def test_restricted_scope_tradition_not_public(client, db):
    w = make_world(db)
    w["tradition"].access_scope = "restricted"
    db.flush()
    assert client.get(f"/api/v1/traditions/{w['tradition'].slug}").status_code == 404


def test_pagination_search_sort_and_validation(client, db):
    tag = uid()
    for i in range(5):
        make_world(db, n_lessons=1)
        db.add(CulturalTradition(slug=f"pg-{tag}-{i}", name=f"Zeta{tag} {i}", access_scope="public",
                                 status="published", is_demo=True, source_citation="s",
                                 published_at=__import__("datetime").datetime.now(
                                     __import__("datetime").UTC)))
    db.flush()
    r = client.get("/api/v1/traditions", params={"q": f"Zeta{tag}", "page_size": 2, "page": 2,
                                                 "sort": "-name"}).json()
    assert r["total"] == 5 and r["total_pages"] == 3 and r["page"] == 2 and len(r["items"]) == 2
    assert r["items"][0]["name"] > r["items"][1]["name"]
    assert client.get("/api/v1/traditions", params={"sort": "drop table"}).status_code == 422
    assert client.get("/api/v1/traditions", params={"page_size": 1000}).status_code == 422
    # karakter wildcard SQL diperlakukan literal
    assert client.get("/api/v1/traditions", params={"q": "%"}).json()["total"] == 0


def test_movement_visibility_and_lookup(client, db):
    w = make_world(db)
    hidden = make_movement(db, w, status="draft", published_at=None)
    shown = make_movement(db, w)
    assert client.get(f"/api/v1/movements/{hidden.id}").status_code == 404
    assert client.get(f"/api/v1/movements/{shown.id}").status_code == 200
    assert client.get("/api/v1/movements/bukan-uuid").status_code == 404
    assert client.get(f"/api/v1/movements/{shown.id}").json()["assessment_enabled"] is False


def test_lesson_body_requires_login(client, db):
    w = make_world(db)
    url = f"/api/v1/courses/{w['course'].slug}/lessons/{w['lessons'][0].slug}"
    assert client.get(url).status_code == 401
    login(client, make_user(db))
    r = client.get(url)
    assert r.status_code == 200 and r.json()["body"] == "isi" and r.json()["enrolled"] is False
    assert r.json()["next_lesson"]["slug"] == w["lessons"][1].slug
