"""Direktori nasional: kueri viewport/filter, klaster, kiriman (publik, honeypot, rate), tinjauan kurator, tanpa data berkas."""

from datetime import UTC, datetime

import pytest

from app.core.config import get_settings
from app.models import DirectoryOrganization, DirectoryPlace, DirectoryPlaceSource, DirectoryRegion, DirectorySubmission
from tests.factories import login, make_user, uid


@pytest.fixture
def world(db):
    """Dua provinsi, dua kab/kota, satu organisasi, beberapa tempat. Kode unik agar tidak bentrok dengan DB dev."""
    for code, name, kind, prov in (("98", "Provinsi Uji", "provinsi", "98"), ("98.01", "Kota Uji A", "kota", "98"), ("98.02", "Kabupaten Uji B", "kabupaten", "98")):
        if not db.get(DirectoryRegion, code):
            db.add(DirectoryRegion(code=code, name=name, kind=kind, province_code=prov, latitude=-6.0, longitude=107.0))
    db.flush()
    org = DirectoryOrganization(key=f"org.uji-{uid()}", official_name="Perguruan Uji", short_name="PU", organization_type="perguruan")
    db.add(org)
    db.flush()
    made = []
    for i, (cat, reg, lat, lng, prec) in enumerate((("perguruan_branch", "98.01", -6.20, 106.80, "exact"), ("padepokan", "98.01", -6.21, 106.81, "exact"),
                                                   ("perguruan_branch", "98.02", -7.00, 110.00, "regency"))):
        p = DirectoryPlace(slug=f"uji-{uid()}", external_key=f"uji:{uid()}", official_name=f"Tempat Uji {i}", display_name=f"Tempat Uji {i}",
                           place_category=cat, province_code="98", regency_code=reg, latitude=lat, longitude=lng, location_precision=prec,
                           confidence=0.6, record_updated_at=datetime.now(UTC), parent_organization_id=org.id if i < 2 else None,
                           is_training_location=True)
        p.sources.append(DirectoryPlaceSource(position=0, source_type="openstreetmap", title="OSM", attribution="© OSM", supports=["nama"]))
        db.add(p)
        made.append(p)
    db.flush()
    return {"org": org, "places": made}


def test_filter_bbox_category_and_sync_between_map_and_list(client, world):
    allr = client.get("/api/v1/directory/list?province=98&page_size=50").json()
    assert allr["total"] == 3
    box = client.get("/api/v1/directory/places?province=98&bbox=106.5,-6.5,107.0,-6.0&zoom=12").json()
    assert box["mode"] == "points" and box["total"] == 2
    assert {i["category"] for i in box["items"]} == {"perguruan_branch", "padepokan"}
    only = client.get("/api/v1/directory/list?province=98&category=padepokan").json()
    assert only["total"] == 1
    # peta dan daftar memakai saringan yang sama -> jumlah sama
    assert client.get("/api/v1/directory/places?province=98&category=padepokan&zoom=12").json()["total"] == only["total"]
    assert client.get("/api/v1/directory/list?province=98&organization=" + world["org"].key).json()["total"] == 2


def test_bad_params_rejected(client):
    assert client.get("/api/v1/directory/places?category=foo").status_code == 422
    assert client.get("/api/v1/directory/places?bbox=1,2,3").status_code == 422
    assert client.get("/api/v1/directory/places?bbox=10,0,5,1").status_code == 422
    assert client.get("/api/v1/directory/places?near=abc").status_code == 422
    assert client.get("/api/v1/directory/places?province=9").status_code == 422


def test_region_level_places_never_get_directions_and_label_precision(client, world):
    p = world["places"][2]
    d = client.get(f"/api/v1/directory/places/{p.slug}").json()
    assert d["precision"] == "regency" and d["directions_url"] is None
    assert "kabupaten/kota" in d["precision_label"]
    assert d["practice_schedule"] is None and d["contact"] is None  # tidak ada jadwal/kontak tanpa sumber
    e = client.get(f"/api/v1/directory/places/{world['places'][0].slug}").json()
    assert e["directions_url"] and e["attribution"] == "© kontributor OpenStreetMap (ODbL 1.0)"
    assert "rating" not in e and "reviews" not in e


def test_clusters_at_low_zoom_when_many(client, db, world):
    for i in range(30):
        db.add(DirectoryPlace(slug=f"klaster-{uid()}-{i}", external_key=f"k:{uid()}", official_name=f"K{i}", display_name=f"K{i}", place_category="community",
                              province_code="98", regency_code="98.01", latitude=-6.2 + i * 0.001, longitude=106.8, location_precision="exact",
                              confidence=0.5, record_updated_at=datetime.now(UTC)))
    db.flush()
    r = client.get("/api/v1/directory/places?province=98&zoom=5").json()
    assert r["mode"] == "clusters" and sum(c["count"] for c in r["clusters"]) == r["total"] >= 33
    assert client.get("/api/v1/directory/places?province=98&zoom=15&bbox=106.7,-6.3,106.9,-6.1").json()["mode"] == "points"


def test_submission_public_with_honeypot_and_review_flow(client, db, world):
    body = {"kind": "new_place", "payload": {"name": "Perguruan Baru Uji", "regency_code": "98.01", "address": "Jl. Uji 1"},
            "submitter_relation": "pengelola", "source_url": "https://contoh.test/perguruan"}
    assert client.post("/api/v1/directory/submissions", json={**body, "website_hp": "bot"}).status_code == 422
    r = client.post("/api/v1/directory/submissions", json=body)
    assert r.status_code == 201 and r.json()["status"] in ("source_check", "duplicate_check", "coordinate_check")
    sid = r.json()["id"]
    assert "Perguruan Baru Uji" not in [p["name"] for p in client.get("/api/v1/directory/list?province=98&page_size=100").json()["items"]]  # tidak terbit otomatis
    # anonim/pelajar tidak boleh meninjau
    assert client.get("/api/v1/directory/submissions").status_code == 401
    login(client, make_user(db, "learner"))
    assert client.get("/api/v1/directory/submissions").status_code == 403
    client.headers.pop("X-CSRF-Token", None)
    client.cookies.clear()
    cur = make_user(db, "curator")
    login(client, cur)
    assert client.post(f"/api/v1/directory/submissions/{sid}/review", json={"action": "publish"}).status_code == 409  # belum disetujui
    assert client.post(f"/api/v1/directory/submissions/{sid}/review", json={"action": "approve", "note": "ok"}).status_code == 200
    assert client.post(f"/api/v1/directory/submissions/{sid}/review", json={"action": "publish"}).status_code == 200
    names = [p["name"] for p in client.get("/api/v1/directory/list?province=98&page_size=100").json()["items"]]
    assert "Perguruan Baru Uji" in names
    sub = db.get(DirectorySubmission, __import__("uuid").UUID(sid))
    assert sub.status == "published" and sub.place_id


def test_submission_validation(client, world):
    ok = {"kind": "new_place", "payload": {"name": "X Perguruan", "regency_code": "98.01"}, "submitter_relation": "publik"}
    assert client.post("/api/v1/directory/submissions", json={**ok, "payload": {"name": "X Perguruan", "regency_code": "98.01", "landmarks": [1]}}).status_code == 422  # field asing
    assert client.post("/api/v1/directory/submissions", json={**ok, "payload": {"name": "ab"}}).status_code == 422
    assert client.post("/api/v1/directory/submissions", json={**ok, "kind": "correction"}).status_code == 422  # butuh tempat
    assert client.post("/api/v1/directory/submissions", json={**ok, "payload": {"name": "Perguruan Uji", "regency_code": "98.01", "lat": 55, "lng": 10}}).status_code == 201  # koordinat di luar Indonesia ditandai, bukan diterbitkan


def test_submission_rate_limit(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "rate_limit_enabled", True)
    body = {"kind": "new_place", "payload": {"name": "Perguruan Rate", "regency_code": "98.01"}, "submitter_relation": "publik"}
    codes = [client.post("/api/v1/directory/submissions", json=body).status_code for _ in range(10)]
    assert 429 in codes
