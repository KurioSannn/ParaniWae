"""Riwayat hasil penilaian: login+CSRF, tanpa landmark/video, breakdown hanya dengan persetujuan, versi protokol dicek."""

import pytest

from app.core.config import get_settings
from app.services import assets3d
from tests.factories import login, make_user


@pytest.fixture
def repo_ok(monkeypatch):
    from pathlib import Path

    root = Path(get_settings().research_repo_dir)  # /repo (read-only mount) di container dev
    if not (root / "content/pencak-silat/assessments").is_dir():
        pytest.skip("berkas protokol tidak tersedia di lingkungan ini")
    monkeypatch.setattr(get_settings(), "research_repo_dir", str(root))
    monkeypatch.setattr(get_settings(), "research_preview_enabled", True)
    assets3d._cached.cache_clear()


def payload(**kw):
    p = assets3d.protocol("mv.psdp.langkah-angkatan")
    base = {"movement_id": p["movement_id"], "protocol_id": p["protocol_id"], "protocol_version": p["protocol_version"],
            "reference_id": p["reference_id"], "engine_version": "1.0.0", "model_version": "uji", "status": "scored", "total_score": 72,
            "input_quality": 0.9, "duration_ms": 9000, "frames_analyzed": 120}
    return {**base, **kw}


def test_requires_login_and_csrf(client, db, repo_ok):
    assert client.post("/api/v1/assessments", json=payload()).status_code == 401
    login(client, make_user(db))
    del client.headers["X-CSRF-Token"]
    assert client.post("/api/v1/assessments", json=payload()).status_code == 403


def test_rejects_landmarks_video_and_inconsistent_scores(client, db, repo_ok):
    login(client, make_user(db))
    for extra in ({"landmarks": [[0, 0, 0]]}, {"video": "x"}, {"frames": []}, {"face": "x"}):
        assert client.post("/api/v1/assessments", json=payload(**extra)).status_code == 422
    assert client.post("/api/v1/assessments", json=payload(total_score=101)).status_code == 422
    assert client.post("/api/v1/assessments", json=payload(total_score=None)).status_code == 422  # scored tanpa skor
    assert client.post("/api/v1/assessments", json=payload(status="not_assessable", total_score=60)).status_code == 422  # skor palsu
    assert client.post("/api/v1/assessments", json=payload(status="not_assessable", total_score=None, not_assessable_reason="LOW_INPUT_QUALITY")).status_code == 201


def test_breakdown_requires_consent_and_is_not_stored_without_it(client, db, repo_ok):
    login(client, make_user(db))
    crit = [{"id": "high_thigh", "label": "Tinggi angkatan", "score": 40, "actual": 55.0, "target": 90.0, "weight": 30, "status": "below"}]
    assert client.post("/api/v1/assessments", json=payload(criteria=crit)).status_code == 422
    r = client.post("/api/v1/assessments", json=payload(criteria=crit, consent_breakdown=True))
    assert r.status_code == 201 and r.json()["criteria"][0]["score"] == 40
    r2 = client.post("/api/v1/assessments", json=payload())
    assert r2.json()["criteria"] is None and r2.json()["consent_breakdown"] is False


def test_protocol_version_checked_and_history_is_private(client, db, repo_ok):
    a = make_user(db)
    login(client, a)
    assert client.post("/api/v1/assessments", json=payload(protocol_version="0.0.1")).status_code == 409
    assert client.post("/api/v1/assessments", json=payload(movement_id="mv.psdp.tidak-ada")).status_code in (404, 422)
    mine = client.post("/api/v1/assessments", json=payload()).json()
    hist = client.get("/api/v1/assessments?movement_id=mv.psdp.langkah-angkatan").json()
    assert hist["items"][0]["id"] == mine["id"] and hist["by_movement"][0]["best_score"] == 72 and len(hist["trend"]) == 1
    client.cookies.clear()
    client.headers.pop("X-CSRF-Token", None)
    login(client, make_user(db))
    assert client.get("/api/v1/assessments").json()["items"] == []  # riwayat orang lain tidak terlihat
    assert client.delete(f"/api/v1/assessments/{mine['id']}").status_code == 404
