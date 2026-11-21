"""API publik pratinjau riset: hanya-baca, berlabel draf, mati secara default, aman terhadap path traversal."""

import json

import pytest

from app.core.config import get_settings
from app.services import research
from tests.test_content_import import movement, write_repo


@pytest.fixture
def repo(tmp_path, monkeypatch):
    m_gen = movement("gerak-a", animation={"animation_id": "anim.uji.gerak-a.v1", "status": "generated"})
    root = write_repo(tmp_path, [m_gen, movement("gerak-b")])
    rp = root / "research" / "pencak-silat"
    for sub, name, data in (
        ("traditions", "entities.json", {"categories": {"tradition": "Tradisi"}, "rules": ["r"], "entities": [{"id": "ent.tradition.x", "name": "Tradisi X", "category": "tradition", "provinces": ["Bali"], "source_ids": ["src.uji.2005"], "verification": "research_supported"}]}),
        ("national-coverage", "provinces.json", {"as_of": "2026-11-20", "status_legend": {"sources_limited": "x"}, "global_gaps": ["celah"], "provinces": [{"name": "Bali", "status": "sources_limited", "entities": ["ent.tradition.x"], "gap": "g"}]}),
        ("movement-inventory", "inventory.json", {"purpose": "p", "groups": [{"tradition": "t", "label": "L", "items": [{"name": "Jurus A"}], "defaults": {"safety": "needs_reference"}}]}),
    ):  # fmt: skip
        (rp / sub).mkdir(parents=True, exist_ok=True)
        (rp / sub / name).write_text(json.dumps(data))
    d = root / "content/pencak-silat/animations/mv.uji.gerak-a"
    (d / "keyframes.json").write_text(
        json.dumps(
            {
                "animation_id": "anim.uji.gerak-a.v1",
                "movement_id": "mv.uji.gerak-a",
                "animation_status": "generated",
                "keyframes": [],
            }
        )
    )
    (d / "animation.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    (d / "thumbnail.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    (d / "ANIMATION_NOTES.md").write_text("# catatan")
    s = get_settings()
    monkeypatch.setattr(s, "research_preview_enabled", True)
    monkeypatch.setattr(s, "research_repo_dir", str(root))
    research._cache.update(key=None, data=None)
    return root


def test_switch_disables_knowledge_api(client, monkeypatch):
    from app.core.config import Settings

    # ADR-0008: basis pengetahuan publik AKTIF secara default; saklar tetap dapat mematikannya
    assert Settings.model_fields["research_preview_enabled"].default is True
    monkeypatch.setattr(get_settings(), "research_preview_enabled", False)
    assert client.get("/api/v1/research/summary").status_code == 404


def test_all_sections_public_and_labelled_draft(client, repo):
    s = client.get("/api/v1/research/summary").json()
    assert s["movements"] == {
        "total": 2,
        "animated": 1,
        "by_safety": {"solo_beginner": 2},
        "by_content_status": {"draft": 2},
    }
    assert s["instructor_validated"] == 0 and "bukan kurikulum" in s["disclaimer"]
    for path in ("coverage", "entities", "sources", "inventory", "movements", "curricula"):
        assert client.get(f"/api/v1/research/{path}").status_code == 200, path
    d = client.get("/api/v1/research/movements/gerak-a").json()
    assert d["instructor_validation"] == "not_validated" and d["animation"]["url"].endswith("/gerak-a/animation.svg")
    assert (
        len(d["anatomy"]) == 13 and d["cultural"]["context"]["text"] == "Definisi."
    )  # ref shared_context terselesaikan
    le = client.get("/api/v1/research/curricula/kursus-uji-impor/pelajaran-satu").json()
    assert le["quiz"][0]["answer_index"] == 1 and [m["slug"] for m in le["movements"]] == ["gerak-a", "gerak-b"]


def test_svg_served_with_strict_headers_and_traversal_blocked(client, repo):
    r = client.get("/api/v1/research/movements/gerak-a/animation.svg")
    assert r.status_code == 200 and r.headers["content-type"].startswith("image/svg+xml")
    assert (
        "default-src 'none'" in r.headers["content-security-policy"]
        and r.headers["x-content-type-options"] == "nosniff"
    )
    assert client.get("/api/v1/research/movements/gerak-b/animation.svg").status_code == 404  # needs_reference
    assert client.get("/api/v1/research/movements/gerak-a/keyframes.json").status_code == 404
    assert client.get("/api/v1/research/movements/..%2F..%2Fetc/animation.svg").status_code == 404
    assert client.get("/api/v1/research/movements/tidak-ada").status_code == 404
    assert client.get("/api/v1/research/curricula/kursus-uji-impor/..%2F..%2Fetc").status_code == 404


def test_public_text_has_no_page_citations_or_partner_wording():
    from app.services.research import scrub, scrub_text

    assert scrub_text("Herdiana (2008, hlm. 9) memakai penomoran 1–5.") == "Herdiana memakai penomoran 1–5."
    assert "hlm" not in scrub_text("Berdiri tegak. Nugroho hlm. 145; Herdiana hlm. 9")
    assert scrub_text("instruktur mitra yang akan menentukan versi") == "pelatih yang akan menentukan versi"
    out = scrub({"a": ["x (hlm. 3)", {"b": "perguruan mitra"}], "notes_markdown": "tetap (hlm. 1)"})
    assert out == {"a": ["x", {"b": "perguruan"}], "notes_markdown": "tetap (hlm. 1)"}
