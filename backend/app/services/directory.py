"""Layanan direktori nasional (kueri viewport, klaster, filter, statistik, kiriman). Kontrak: docs/NATIONAL_DIRECTORY_CONTRACT.md."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.errors import ApiError
from app.models import (
    DirectoryHeritageArea,
    DirectoryOrganization,
    DirectoryPlace,
    DirectoryPlaceHistory,
    DirectoryRegion,
    DirectorySubmission,
)
from app.models.directory import PLACE_CATEGORIES

CATEGORY_LABEL = {
    "perguruan_branch": "Cabang/ranting perguruan", "perguruan_center": "Pusat perguruan", "padepokan": "Padepokan",
    "training_center": "Pusat latihan", "ipsi": "Organisasi IPSI", "organization_office": "Kantor organisasi",
    "campus_unit": "Kampus/UKM", "community": "Sanggar/komunitas", "sports_venue": "Gelanggang olahraga",
    "cultural_center": "Pusat budaya & pelestarian", "cultural_landmark": "Monumen/penanda budaya",
}
PRECISION_LABEL = {
    "exact": "Titik tempat menurut data peta",
    "district": "Lokasi pada tingkat kecamatan",
    "regency": "Lokasi pada tingkat kabupaten/kota; alamat latihan belum terdata",
    "province": "Lokasi pada tingkat provinsi",
}
SOURCE_TYPE_LABEL = {
    "openstreetmap": "OpenStreetMap", "official_site": "Situs resmi", "heritage_record": "Berkas warisan budaya",
    "academic": "Publikasi akademik", "news": "Berita", "map_listing": "Daftar peta (dicatat tim)", "google_places": "Google Maps", "overture": "Overture Maps", "submission": "Kiriman pengelola",
}
OSM_ATTRIBUTION = "© kontributor OpenStreetMap (ODbL 1.0)"
MAX_POINTS = 400


@dataclass
class Filters:
    q: str | None = None
    province: str | None = None
    regency: str | None = None
    district: str | None = None
    categories: tuple[str, ...] = ()
    organization: str | None = None
    tradition: str | None = None
    activity: str | None = None  # training | office | heritage
    has_contact: bool = False
    has_schedule: bool = False
    open_public: bool = False
    status: str | None = None
    precision: str | None = None
    bbox: tuple[float, float, float, float] | None = None  # minLng,minLat,maxLng,maxLat


def parse_bbox(s: str | None) -> tuple[float, float, float, float] | None:
    if not s:
        return None
    try:
        a = tuple(float(x) for x in s.split(","))
    except ValueError as e:
        raise ApiError(422, "BAD_BBOX", "bbox harus minLng,minLat,maxLng,maxLat") from e
    if len(a) != 4 or not (-180 <= a[0] <= a[2] <= 180 and -90 <= a[1] <= a[3] <= 90):
        raise ApiError(422, "BAD_BBOX", "bbox harus minLng,minLat,maxLng,maxLat")
    return a  # type: ignore[return-value]


def parse_point(s: str | None) -> tuple[float, float] | None:
    if not s:
        return None
    try:
        lat, lng = (float(x) for x in s.split(","))
    except ValueError as e:
        raise ApiError(422, "BAD_POINT", "near harus lat,lng") from e
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ApiError(422, "BAD_POINT", "near harus lat,lng")
    return lat, lng


def _query(f: Filters):
    P = DirectoryPlace
    q = select(P).where(P.publication_status == "published")
    if f.q:
        like = f"%{f.q.strip()[:80]}%"
        q = q.where(or_(P.display_name.ilike(like), P.official_name.ilike(like), cast(P.aliases, String).ilike(like),
                        P.full_address.ilike(like), P.locality_text.ilike(like), P.district.ilike(like)))
    if f.province:
        q = q.where(P.province_code == f.province)
    if f.regency:
        q = q.where(P.regency_code == f.regency)
    if f.district:
        q = q.where(P.district.ilike(f"%{f.district[:60]}%"))
    if f.categories:
        q = q.where(P.place_category.in_(f.categories))
    if f.organization:
        q = q.join(DirectoryOrganization, P.parent_organization_id == DirectoryOrganization.id).where(
            DirectoryOrganization.key == f.organization)
    if f.tradition:
        q = q.where(or_(P.entity_id == f.tradition, P.tradition_ids.contains([f.tradition]), P.style_ids.contains([f.tradition])))
    if f.activity == "training":
        q = q.where(P.is_training_location.is_(True))
    elif f.activity == "office":
        q = q.where(P.is_organization_office.is_(True))
    elif f.activity == "heritage":
        q = q.where(P.place_category.in_(("cultural_center", "cultural_landmark")))
    if f.has_contact:
        q = q.where(or_(P.contact_email.is_not(None), P.contact_phone.is_not(None), P.official_website.is_not(None)))
    if f.has_schedule:
        q = q.where(P.practice_schedule.is_not(None))
    if f.open_public:
        q = q.where(P.public_access == "open")
    if f.status:
        q = q.where(P.operational_status == f.status)
    if f.precision:
        q = q.where(P.location_precision == f.precision)
    if f.bbox:
        a, b, c, d = f.bbox
        q = q.where(P.longitude >= a, P.longitude <= c, P.latitude >= b, P.latitude <= d)
    return q


def haversine_km(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def _regions(db: Session) -> dict[str, DirectoryRegion]:
    return {r.code: r for r in db.scalars(select(DirectoryRegion))}


def summary_out(p: DirectoryPlace, regions: dict, near=None) -> dict:
    org = p.organization
    types = sorted({s.source_type for s in p.sources})
    out = {
        "slug": p.slug, "name": p.display_name, "category": p.place_category,
        "category_label": CATEGORY_LABEL.get(p.place_category, p.place_category),
        "organization": {"key": org.key, "name": org.official_name, "short_name": org.short_name} if org else None,
        "province_code": p.province_code, "province": regions[p.province_code].name if p.province_code in regions else None,
        "regency_code": p.regency_code, "regency": regions[p.regency_code].name if p.regency_code in regions else None,
        "district": p.district, "address": p.full_address, "locality_text": p.locality_text,
        "lat": p.latitude, "lng": p.longitude, "precision": p.location_precision,
        "precision_label": PRECISION_LABEL[p.location_precision],
        "is_training_location": p.is_training_location, "is_organization_office": p.is_organization_office,
        "website": p.official_website, "has_contact": bool(p.contact_email or p.contact_phone or p.official_website),
        "has_schedule": bool(p.practice_schedule), "operational_status": p.operational_status,
        "source_types": [SOURCE_TYPE_LABEL.get(t, t) for t in types], "source_count": len(p.sources),
        "attribution": (OSM_ATTRIBUTION if "openstreetmap" in types else "Data tempat: Google Maps" if "google_places" in types else "Data tempat: Overture Maps Foundation" if "overture" in types else None),
    }
    if near:
        out["distance_km"] = round(haversine_km(near, (p.latitude, p.longitude)), 1)
    return out


def places(db: Session, f: Filters, zoom: int | None, near=None, sort: str = "name", limit: int = MAX_POINTS) -> dict:
    rows = list(db.scalars(_query(f).options(selectinload(DirectoryPlace.sources), selectinload(DirectoryPlace.organization))))
    regions = _regions(db)
    total = len(rows)
    z = zoom if zoom is not None else 5
    if total > 20 and z < 8:
        return {"mode": "clusters", "total": total, "clusters": _cluster(rows, z, regions, near), "items": []}
    items = [summary_out(p, regions, near) for p in rows]
    _sort(items, sort, near)
    return {"mode": "points", "total": total, "clusters": [], "items": items[:limit], "truncated": total > limit}


def _sort(items: list[dict], sort: str, near) -> None:
    if sort == "distance" and near:
        items.sort(key=lambda x: (x["distance_km"], x["name"]))
    else:
        items.sort(key=lambda x: (x["province"] or "", x["regency"] or "", x["name"]))


def _cluster(rows: list[DirectoryPlace], zoom: int, regions: dict, near=None) -> list[dict]:
    """Klaster grid sisi-server: ukuran sel mengikuti zoom (≈ 1/4 tile)."""
    cell = 360.0 / (2 ** max(zoom, 1)) / 4
    buckets: dict[tuple[int, int], list[DirectoryPlace]] = {}
    for p in rows:
        buckets.setdefault((math.floor(p.longitude / cell), math.floor(p.latitude / cell)), []).append(p)
    out = []
    for b in buckets.values():
        lat = sum(p.latitude for p in b) / len(b)
        lng = sum(p.longitude for p in b) / len(b)
        out.append({"lat": round(lat, 5), "lng": round(lng, 5), "count": len(b),
                    "bbox": [min(p.longitude for p in b), min(p.latitude for p in b), max(p.longitude for p in b), max(p.latitude for p in b)],
                    "single": summary_out(b[0], regions, near) if len(b) == 1 else None})
    return out


def list_places(db: Session, f: Filters, near=None, sort="name", page=1, page_size=20) -> dict:
    rows = list(db.scalars(_query(f).options(selectinload(DirectoryPlace.sources), selectinload(DirectoryPlace.organization))))
    regions = _regions(db)
    items = [summary_out(p, regions, near) for p in rows]
    _sort(items, sort, near)
    start = (page - 1) * page_size
    return {"total": len(items), "page": page, "page_size": page_size, "items": items[start:start + page_size]}


def place_detail(db: Session, slug: str) -> dict:
    p = db.scalar(select(DirectoryPlace).where(DirectoryPlace.slug == slug, DirectoryPlace.publication_status == "published")
                  .options(selectinload(DirectoryPlace.sources), selectinload(DirectoryPlace.organization)))
    if not p:
        raise ApiError(404, "NOT_FOUND", "Tempat tidak ditemukan.")
    regions = _regions(db)
    out = summary_out(p, regions)
    out.update({
        "official_name": p.official_name, "aliases": p.aliases, "village": p.village, "venue_type": p.venue_type,
        "coordinate_check": p.coordinate_check,
        "contact": ({"email": p.contact_email, "phone": p.contact_phone, "source": p.contact_source}
                    if (p.contact_email or p.contact_phone) else None),
        "social_links": p.public_social_links, "practice_schedule": p.practice_schedule,
        "training_levels": p.training_levels, "training_categories": p.training_categories,
        "sports_listed": p.sports_listed, "facilities": p.facilities, "accessibility": p.accessibility_information,
        "public_access": p.public_access, "evidence": p.evidence, "data_conflicts": p.data_conflicts,
        "entity_id": p.entity_id, "last_verified_at": p.last_verified_at.isoformat() if p.last_verified_at else None,
        "record_updated_at": p.record_updated_at.isoformat(),
        "sources": [{"type": s.source_type, "type_label": SOURCE_TYPE_LABEL.get(s.source_type, s.source_type),
                     "title": s.title, "publisher": s.publisher, "year": s.year, "url": s.url, "license": s.license,
                     "attribution": s.attribution, "retrieved_at": s.retrieved_at, "supports": s.supports} for s in p.sources],
        "directions_url": _directions(p),
        "map_search_url": "https://www.google.com/maps/search/?api=1&query=" + _q(f"{p.display_name} {out['regency'] or ''}"),
    })
    nearby = db.scalars(select(DirectoryPlace).where(DirectoryPlace.regency_code == p.regency_code, DirectoryPlace.id != p.id,
                                                     DirectoryPlace.publication_status == "published").limit(6)
                        .options(selectinload(DirectoryPlace.sources), selectinload(DirectoryPlace.organization)))
    out["same_regency"] = [summary_out(x, regions) for x in nearby]
    return out


def _q(s: str) -> str:
    from urllib.parse import quote
    return quote(s.strip())


def _directions(p: DirectoryPlace) -> str | None:
    """Arah hanya untuk titik aktual; penanda wilayah tidak diberi arah ke alamat palsu."""
    if p.location_precision != "exact":
        return None
    return f"https://www.openstreetmap.org/directions?to={p.latitude:.6f}%2C{p.longitude:.6f}"


def facets(db: Session, province: str | None = None) -> dict:
    P = DirectoryPlace
    regions = _regions(db)
    prov_counts = dict(db.execute(select(P.province_code, func.count()).where(P.publication_status == "published").group_by(P.province_code)).all())
    reg_q = select(P.regency_code, func.count()).where(P.publication_status == "published")
    if province:
        reg_q = reg_q.where(P.province_code == province)
    reg_counts = dict(db.execute(reg_q.group_by(P.regency_code)).all())
    cat_counts = dict(db.execute(select(P.place_category, func.count()).where(P.publication_status == "published").group_by(P.place_category)).all())
    orgs = db.execute(select(DirectoryOrganization.key, DirectoryOrganization.official_name, DirectoryOrganization.short_name, func.count(P.id))
                      .join(P, P.parent_organization_id == DirectoryOrganization.id).where(P.publication_status == "published")
                      .group_by(DirectoryOrganization.id).order_by(func.count(P.id).desc())).all()
    provinces = sorted((r for r in regions.values() if r.kind == "provinsi"), key=lambda r: r.code)
    regencies = sorted((r for r in regions.values() if r.kind != "provinsi" and (not province or r.province_code == province)),
                       key=lambda r: r.name)
    trad = db.execute(select(P.entity_id).where(P.entity_id.is_not(None), P.publication_status == "published")).scalars().all()
    return {
        "provinces": [{"code": r.code, "name": r.name, "count": prov_counts.get(r.code, 0), "bbox": region_bbox(r.code)}
                      for r in provinces],
        "regencies": [{"code": r.code, "name": r.name, "province_code": r.province_code, "count": reg_counts.get(r.code, 0),
                       "bbox": region_bbox(r.code) if province else None} for r in regencies],
        "categories": [{"key": c, "label": CATEGORY_LABEL[c], "count": cat_counts.get(c, 0)} for c in PLACE_CATEGORIES if cat_counts.get(c)],
        "organizations": [{"key": k, "name": n, "short_name": s, "count": c} for k, n, s, c in orgs],
        "activities": [{"key": "training", "label": "Tempat latihan"}, {"key": "office", "label": "Kantor/sekretariat"},
                       {"key": "heritage", "label": "Budaya & pelestarian"}],
        "precisions": [{"key": k, "label": v} for k, v in PRECISION_LABEL.items() if k in ("exact", "regency")],
        "entity_ids_with_places": sorted(set(trad)),
    }


def stats(db: Session) -> dict:
    P = DirectoryPlace
    pub = P.publication_status == "published"
    regions = _regions(db)
    total = db.scalar(select(func.count()).select_from(P).where(pub)) or 0
    by_prov = dict(db.execute(select(P.province_code, func.count()).where(pub).group_by(P.province_code)).all())
    by_reg = db.execute(select(P.regency_code, func.count()).where(pub).group_by(P.regency_code).having(func.count() >= 2)
                        .order_by(func.count().desc())).all()
    by_cat = dict(db.execute(select(P.place_category, func.count()).where(pub).group_by(P.place_category)).all())
    by_prec = dict(db.execute(select(P.location_precision, func.count()).where(pub).group_by(P.location_precision)).all())
    training = db.scalar(select(func.count()).select_from(P).where(pub, P.is_training_location.is_(True))) or 0
    orgs = db.execute(select(DirectoryOrganization.key, DirectoryOrganization.official_name, DirectoryOrganization.short_name, func.count(P.id))
                      .join(P, P.parent_organization_id == DirectoryOrganization.id).where(pub)
                      .group_by(DirectoryOrganization.id).order_by(func.count(P.id).desc())).all()
    rows = list(db.scalars(select(P).where(pub).options(selectinload(P.sources), selectinload(P.organization))))
    featured = sorted(rows, key=lambda p: (-_completeness(p), p.display_name))[:6]
    areas = list(db.scalars(select(DirectoryHeritageArea)))
    provinces = sorted((r for r in regions.values() if r.kind == "provinsi"), key=lambda r: r.code)
    return {
        "total_places": total, "training_locations": training,
        "provinces_with_places": len(by_prov), "provinces_total": len(provinces),
        "regencies_with_places": db.scalar(select(func.count(func.distinct(P.regency_code))).where(pub)) or 0,
        "regencies_total": sum(1 for r in regions.values() if r.kind != "provinsi"),
        "by_province": [{"code": r.code, "name": r.name, "count": by_prov.get(r.code, 0)} for r in provinces],
        "regencies_multi": [{"code": c, "name": regions[c].name, "count": n} for c, n in by_reg],
        "by_category": [{"key": k, "label": CATEGORY_LABEL[k], "count": v} for k, v in sorted(by_cat.items(), key=lambda x: -x[1])],
        "by_precision": [{"key": k, "label": PRECISION_LABEL[k], "count": v} for k, v in by_prec.items()],
        "by_organization": [{"key": k, "name": n, "short_name": s, "count": c} for k, n, s, c in orgs],
        "featured": [{**summary_out(p, regions), "completeness": _completeness(p)} for p in featured],
        "heritage_areas": len(areas),
        "note": "Angka adalah lokasi yang terdata di SILATARA dari sumber yang dapat ditelusuri, bukan jumlah seluruh perguruan atau ukuran popularitas.",
        "attribution": [OSM_ATTRIBUTION, "Wilayah: Kepmendagri No 300.2.2-2138 Tahun 2025"],
    }


def _completeness(p: DirectoryPlace) -> int:
    """Kelengkapan informasi (bukan peringkat kualitas perguruan)."""
    return (2 * min(len(p.sources), 3) + (2 if p.location_precision == "exact" else 0) + (1 if p.full_address else 0)
            + (1 if (p.contact_email or p.official_website) else 0) + (1 if p.practice_schedule else 0)
            + (1 if p.parent_organization_id else 0) + (1 if p.is_training_location else 0))


def heritage_areas(db: Session) -> list[dict]:
    return [{"entity_id": a.entity_id, "name": a.name, "category": a.category, "regency_codes": a.regency_codes,
             "points": a.points, "locality_text": a.locality_text, "public_note": a.public_note,
             "sources": [{"title": s.get("title"), "publisher": s.get("publisher"), "year": s.get("year"), "url": s.get("url")}
                         for s in a.sources]}
            for a in db.scalars(select(DirectoryHeritageArea).order_by(DirectoryHeritageArea.name))]


# ---------------------------------------------------------------- kiriman
@lru_cache(maxsize=1)
def _polygons() -> dict:
    path = Path(get_settings().research_repo_dir) / "research/pencak-silat/directory/regions.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {r["code"]: r["rings"] for r in data["regencies"]} | {"_prov:" + r["code"]: r["rings"] for r in data["provinces"]}


def region_bbox(code: str) -> list[float] | None:
    """[minLng, minLat, maxLng, maxLat] dari poligon wilayah (provinsi bila kode 2 digit)."""
    rings = _polygons().get(code if "." in code else "_prov:" + code)
    pts = [p for ring in rings or [] for p in ring]
    if not pts:
        return None
    return [min(p[1] for p in pts), min(p[0] for p in pts), max(p[1] for p in pts), max(p[0] for p in pts)]


def _pip(lat: float, lng: float, ring) -> bool:
    inside, j = False, len(ring) - 1
    for i in range(len(ring)):
        yi, xi = ring[i]
        yj, xj = ring[j]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def _key(n: str) -> str:
    return re.sub(r"[^a-z0-9]", "", n.lower())


def create_submission(db: Session, body: dict, user=None) -> DirectorySubmission:
    place = None
    if body.get("place_slug"):
        place = db.scalar(select(DirectoryPlace).where(DirectoryPlace.slug == body["place_slug"]))
        if not place:
            raise ApiError(404, "NOT_FOUND", "Tempat tidak ditemukan.")
    if body["kind"] != "new_place" and not place:
        raise ApiError(422, "PLACE_REQUIRED", "Pilih tempat yang ingin dikoreksi.")
    data = body["payload"]
    checks: dict = {}
    dups: list = []
    regions = _regions(db)
    reg = data.get("regency_code")
    if reg and reg not in regions:
        raise ApiError(422, "BAD_REGION", "Kode kabupaten/kota tidak dikenal.")
    # pemeriksaan duplikasi (tempat baru)
    if body["kind"] == "new_place" and data.get("name"):
        k = _key(data["name"])
        q = select(DirectoryPlace)
        if reg:
            q = q.where(DirectoryPlace.regency_code == reg)
        for p in db.scalars(q):
            pk = _key(p.display_name)
            if k and (k in pk or pk in k):
                dups.append({"slug": p.slug, "name": p.display_name})
        checks["duplicate"] = "possible_duplicate" if dups else "none_found"
    # pemeriksaan koordinat
    lat, lng = data.get("lat"), data.get("lng")
    if lat is not None and lng is not None:
        if not (-11.5 <= lat <= 6.5 and 94.5 <= lng <= 141.5):
            checks["coordinate"] = "outside_indonesia"
        elif reg and _polygons().get(reg):
            checks["coordinate"] = "inside_regency" if any(_pip(lat, lng, r) for r in _polygons()[reg]) else "outside_stated_regency"
        else:
            checks["coordinate"] = "not_checked"
    else:
        checks["coordinate"] = "no_coordinate"
    checks["source"] = "url_provided" if body.get("source_url") else ("manager_claim" if body["submitter_relation"] == "pengelola" else "missing")
    status = "duplicate_check" if dups else ("coordinate_check" if checks["coordinate"] in ("outside_indonesia", "outside_stated_regency")
                                             else "source_check")
    sub = DirectorySubmission(kind=body["kind"], status=status, place_id=place.id if place else None, payload=data,
                              source_url=body.get("source_url"), submitter_relation=body["submitter_relation"],
                              submitter_user_id=user.id if user else None, contact_email=body.get("contact_email"),
                              duplicate_candidates=dups, checks=checks)
    db.add(sub)
    db.commit()
    return sub


def submission_out(s: DirectorySubmission, include_private: bool = False) -> dict:
    out = {"id": str(s.id), "kind": s.kind, "status": s.status, "place_id": str(s.place_id) if s.place_id else None,
           "payload": s.payload, "source_url": s.source_url, "submitter_relation": s.submitter_relation,
           "duplicate_candidates": s.duplicate_candidates, "checks": s.checks, "review_note": s.review_note,
           "created_at": s.created_at.isoformat() if s.created_at else None,
           "reviewed_at": s.reviewed_at.isoformat() if s.reviewed_at else None}
    if include_private:
        out["contact_email"] = s.contact_email
    return out


APPLY_FIELDS = {"name": "display_name", "address": "full_address", "website": "official_website",
                "contact_email": "contact_email", "contact_phone": "contact_phone", "district": "district"}

TRANSITIONS = {
    "approve": ("source_check", "duplicate_check", "coordinate_check", "awaiting_manager", "submitted"),
    "awaiting_manager": ("source_check", "duplicate_check", "coordinate_check", "submitted"),
    "reject": ("source_check", "duplicate_check", "coordinate_check", "awaiting_manager", "submitted", "approved"),
    "duplicate": ("duplicate_check", "source_check", "submitted"),
    "publish": ("approved",),
}


def review_submission(db: Session, sub_id, action: str, note: str | None, reviewer) -> DirectorySubmission:
    s = db.get(DirectorySubmission, sub_id)
    if not s:
        raise ApiError(404, "NOT_FOUND", "Kiriman tidak ditemukan.")
    if action not in TRANSITIONS or s.status not in TRANSITIONS[action]:
        raise ApiError(409, "BAD_TRANSITION", f"Tidak bisa '{action}' dari status '{s.status}'.")
    now = datetime.now(UTC)
    if action == "publish":
        _apply(db, s, reviewer, now)
        s.status = "published"
    else:
        s.status = {"approve": "approved", "awaiting_manager": "awaiting_manager", "reject": "rejected", "duplicate": "duplicate"}[action]
    s.review_note, s.reviewed_by_user_id, s.reviewed_at = note, reviewer.id, now
    db.commit()
    return s


def _apply(db: Session, s: DirectorySubmission, reviewer, now) -> None:
    d = s.payload
    if s.kind == "new_place":
        if not s.source_url and s.submitter_relation != "pengelola":
            raise ApiError(409, "SOURCE_REQUIRED", "Tempat baru wajib punya sumber atau konfirmasi pengelola.")
        regions = _regions(db)
        reg = d.get("regency_code")
        if reg not in regions:
            raise ApiError(409, "REGION_REQUIRED", "Kabupaten/kota wajib diisi.")
        exact = s.checks.get("coordinate") == "inside_regency"
        r = regions[reg]
        from app.services.manage import slugify  # noqa: PLC0415

        base = slugify(f"{d['name']} {r.name.replace('Kabupaten ', '').replace('Kota ', '')}")
        slug, k = base, 2
        while db.scalar(select(DirectoryPlace.id).where(DirectoryPlace.slug == slug)):
            slug, k = f"{base}-{k}", k + 1
        p = DirectoryPlace(
            slug=slug, external_key=f"submission:{s.id}", official_name=d["name"], display_name=d["name"],
            place_category=d.get("category") if d.get("category") in PLACE_CATEGORIES else "community",
            province_code=r.province_code, regency_code=reg, district=d.get("district"), full_address=d.get("address"),
            latitude=d["lat"] if exact else r.latitude, longitude=d["lng"] if exact else r.longitude,
            location_precision="exact" if exact else "regency", coordinate_check="submission_checked" if exact else "regency_capital_area_marker",
            official_website=d.get("website"), contact_email=d.get("contact_email"), contact_phone=d.get("contact_phone"),
            contact_source="Kiriman pengelola yang ditinjau" if (d.get("contact_email") or d.get("contact_phone")) else None,
            is_training_location=d.get("is_training_location"), confidence=0.6 if s.submitter_relation == "pengelola" else 0.5,
            evidence=[d.get("note")] if d.get("note") else [], record_updated_at=now, last_verified_at=now,
        )
        db.add(p)
        db.flush()
        from app.models import DirectoryPlaceSource  # noqa: PLC0415

        p.sources.append(DirectoryPlaceSource(position=0, source_type="submission", url=s.source_url,
                                              title="Kiriman ke direktori SILATARA (ditinjau redaksi)",
                                              retrieved_at=now.date().isoformat(), supports=list(d.keys())))
        s.place_id = p.id
        db.add(DirectoryPlaceHistory(place_id=p.id, changed_at=now, change_type="submission.create",
                                     changes={"fields": dict.fromkeys(d, True)}, submission_id=s.id, actor_user_id=reviewer.id))
        return
    p = db.get(DirectoryPlace, s.place_id)
    if s.kind == "closed_report":
        changes = {"operational_status": {"from": p.operational_status, "to": "closed"}}
        p.operational_status = "closed"  # tidak dihapus; tetap tercatat sebagai riwayat
    elif s.kind == "schedule_update":
        if not d.get("schedule"):
            raise ApiError(409, "EMPTY", "Jadwal kosong.")
        changes = {"practice_schedule": {"from": p.practice_schedule, "to": d["schedule"]}}
        p.practice_schedule = [{**x, "source": "kiriman ditinjau"} for x in d["schedule"]]
    else:
        changes = {}
        for k, col in APPLY_FIELDS.items():
            if d.get(k):
                changes[col] = {"from": getattr(p, col), "to": d[k]}
                setattr(p, col, d[k])
        if "contact_email" in changes or "contact_phone" in changes:
            p.contact_source = "Kiriman pengelola yang ditinjau"
    p.record_updated_at = p.last_verified_at = now
    db.add(DirectoryPlaceHistory(place_id=p.id, changed_at=now, change_type="submission.apply",
                                 changes={"fields": changes}, submission_id=s.id, actor_user_id=reviewer.id))
