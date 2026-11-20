import pytest
from sqlalchemy.exc import IntegrityError

from app.models import CulturalTradition, Movement, Partner
from app.seed import seed_demo
from app.services.users import create_admin


def _base(db):
    p = Partner(slug="t-p", name="T", partner_type="school", is_demo=True)
    t = CulturalTradition(slug="t-t", name="T", is_demo=True)
    db.add_all([p, t])
    db.flush()
    return p, t


def test_assessment_cannot_be_enabled_for_unapproved_or_unsafe_movement(db):
    p, t = _base(db)
    db.add(Movement(tradition_id=t.id, partner_id=p.id, slug="m", name_id="m",
                    practice_mode="supervised_only", status="published", assessment_enabled=True))
    with pytest.raises(IntegrityError):
        db.flush()


def test_approved_tradition_requires_provenance(db):
    db.add(CulturalTradition(slug="x", name="x", status="published"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_public_listing_requires_verified_partner(db):
    db.add(Partner(slug="y", name="y", partner_type="school", public_listing_consent=True))
    with pytest.raises(IntegrityError):
        db.flush()


def test_seed_demo_is_idempotent_and_labelled(db):
    seed_demo(db)
    second = seed_demo(db)
    assert second == {}
    t = db.query(CulturalTradition).filter_by(slug="demo-tradisi").one()
    assert t.is_demo and "[DEMO]" in t.name


def test_traditions_endpoint_flags_demo_and_hides_restricted(client, db):
    db.add(CulturalTradition(slug="rahasia", name="Rahasia", status="draft",
                             access_scope="restricted"))
    seed_demo(db)
    slugs = {t["slug"]: t for t in client.get(
        "/api/v1/traditions", params={"q": "Tradisi", "page_size": 100}).json()["items"]}
    assert "rahasia" not in slugs
    assert slugs["demo-tradisi"]["provenance"]["is_demo"] is True


def test_create_admin_hashes_password_and_rejects_weak(db):
    with pytest.raises(ValueError):
        create_admin(db, "a@example.test", "short", "A")
    u = create_admin(db, "A@Example.test", "kata-sandi-panjang-123", "A")
    assert u.role == "admin" and u.email == "a@example.test"
    assert u.password_hash.startswith("$argon2")
