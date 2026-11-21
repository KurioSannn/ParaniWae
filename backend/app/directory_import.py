"""Impor hasil pipeline direktori (content/pencak-silat/directory/*.json) ke DB.

- Idempoten: upsert berdasarkan `external_key`; tidak ada perubahan bila data sama.
- DRY-RUN secara default; `execute=True` menulis.
- TIDAK menghapus: tempat yang tidak ada lagi di build terbaru ditandai `missing_from_latest_build=true`
  (tetap tampil sampai peninjau memutuskan), setiap perubahan dicatat di `directory_place_history`.
- Field yang diubah lewat kiriman yang disetujui peninjau (`locked_fields` di riwayat) tidak ditimpa importer.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    DirectoryHeritageArea,
    DirectoryImportJob,
    DirectoryOrganization,
    DirectoryPlace,
    DirectoryPlaceHistory,
    DirectoryPlaceSource,
    DirectoryRegion,
)

PLACE_FIELDS = (
    "official_name", "display_name", "aliases", "place_category", "entity_id", "province_code", "regency_code",
    "district", "village", "locality_text", "full_address", "latitude", "longitude", "location_precision",
    "coordinate_check", "venue_type", "is_training_location", "is_organization_office", "contact_email",
    "official_website", "training_categories", "sports_listed", "public_access", "confidence", "evidence",
    "data_conflicts",
)
LIST_DEFAULTS = ("aliases", "training_categories", "sports_listed", "evidence", "data_conflicts")


class DirectoryImportError(Exception):
    pass


def load_bundle(repo: Path) -> dict:
    d = repo / "content/pencak-silat/directory"
    try:
        places = json.loads((d / "places.json").read_text(encoding="utf-8"))
        orgs = json.loads((d / "organizations.json").read_text(encoding="utf-8"))
        heritage = json.loads((d / "heritage_areas.json").read_text(encoding="utf-8"))
        regions = json.loads((repo / "research/pencak-silat/directory/regions.json").read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise DirectoryImportError(f"berkas tidak ditemukan: {e.filename} (jalankan `make directory-build`)") from e
    job_path = repo / "research/pencak-silat/directory/jobs" / f"{places['job_id']}.json"
    job = json.loads(job_path.read_text(encoding="utf-8")) if job_path.exists() else {}
    return {"places": places, "orgs": orgs, "heritage": heritage, "regions": regions, "job": job}


def validate(b: dict) -> list[str]:
    errs = []
    reg_codes = {r["code"] for r in b["regions"]["regencies"]}
    org_keys = {o["key"] for o in b["orgs"]["organizations"]}
    slugs = set()
    for p in b["places"]["places"]:
        k = p.get("external_key", "?")
        if not p.get("sources"):
            errs.append(f"{k}: tanpa sumber")
        if p.get("regency_code") not in reg_codes:
            errs.append(f"{k}: kode wilayah tidak dikenal")
        if p.get("organization_key") and p["organization_key"] not in org_keys:
            errs.append(f"{k}: organisasi induk tidak dikenal")
        if p["location_precision"] not in ("exact", "regency"):
            errs.append(f"{k}: presisi tidak dikenal")
        if p["slug"] in slugs:
            errs.append(f"{k}: slug ganda {p['slug']}")
        slugs.add(p["slug"])
        if not (0 <= p["confidence"] <= 1):
            errs.append(f"{k}: confidence di luar 0..1")
    return errs


def _norm(v):
    return round(v, 7) if isinstance(v, float) else v


def run(db: Session, repo: Path, *, execute: bool = False, operator=None) -> dict:
    b = load_bundle(repo)
    errs = validate(b)
    if errs:
        raise DirectoryImportError("; ".join(errs[:20]))
    now = datetime.now(UTC)
    job_id = b["places"]["job_id"]
    rep = {"job_id": job_id, "execute": execute, "regions": 0, "organizations": {"created": 0, "updated": 0},
           "places": {"created": 0, "updated": 0, "unchanged": 0, "marked_missing": 0}, "heritage_areas": 0}

    # wilayah
    existing = {r.code: r for r in db.scalars(select(DirectoryRegion))}
    for p in b["regions"]["provinces"]:
        if p["code"] not in existing:
            db.add(DirectoryRegion(code=p["code"], name=p["name"], kind="provinsi", province_code=p["code"],
                                   capital=p.get("capital"), latitude=p.get("lat"), longitude=p.get("lng")))
            rep["regions"] += 1
    for r in b["regions"]["regencies"]:
        if r["code"] not in existing:
            db.add(DirectoryRegion(code=r["code"], name=r["name"], kind=r["kind"], province_code=r["province_code"],
                                   capital=r.get("capital"), latitude=r.get("lat"), longitude=r.get("lng")))
            rep["regions"] += 1
    db.flush()

    # organisasi
    orgs = {o.key: o for o in db.scalars(select(DirectoryOrganization))}
    for o in b["orgs"]["organizations"]:
        row = orgs.get(o["key"])
        vals = {"official_name": o["official_name"], "short_name": o.get("short_name"),
                "organization_type": o["organization_type"], "entity_id": o.get("entity_id"), "sources": o.get("sources", [])}
        if row is None:
            row = DirectoryOrganization(key=o["key"], **vals)
            db.add(row)
            orgs[o["key"]] = row
            rep["organizations"]["created"] += 1
        elif any(getattr(row, k) != v for k, v in vals.items()):
            for k, v in vals.items():
                setattr(row, k, v)
            rep["organizations"]["updated"] += 1
    db.flush()

    # tempat
    rows = {r.external_key: r for r in db.scalars(select(DirectoryPlace))}
    seen = set()
    for p in b["places"]["places"]:
        key = p["external_key"]
        seen.add(key)
        org = orgs.get(p.get("organization_key")) if p.get("organization_key") else None
        vals = {f: (p.get(f) or []) if f in LIST_DEFAULTS else p.get(f) for f in PLACE_FIELDS}
        vals["public_access"] = vals["public_access"] or "unknown"
        vals["parent_organization_id"] = org.id if org else None
        vals["organization_type"] = org.organization_type if org else None
        row = rows.get(key)
        if row is None:
            row = DirectoryPlace(external_key=key, slug=p["slug"], operational_status="active_unverified",
                                 publication_status="published", record_updated_at=now, last_import_job=job_id, **vals)
            db.add(row)
            db.flush()
            _set_sources(db, row, p["sources"])
            db.add(DirectoryPlaceHistory(place_id=row.id, changed_at=now, change_type="import.create",
                                         changes={"slug": p["slug"]}, job_id=job_id,
                                         actor_user_id=operator.id if operator else None))
            rep["places"]["created"] += 1
            continue
        locked = _locked_fields(db, row)
        diff = {}
        for k, v in vals.items():
            if k in locked:
                continue
            if _norm(getattr(row, k)) != _norm(v):
                diff[k] = {"from": _jsonable(getattr(row, k)), "to": _jsonable(v)}
                setattr(row, k, v)
        src_now = [_src_tuple(s) for s in row.sources]
        src_new = [_src_tuple(s) for s in p["sources"]]
        if src_now != src_new:
            diff["sources"] = {"from": len(src_now), "to": len(src_new)}
            _set_sources(db, row, p["sources"])
        if row.missing_from_latest_build:
            row.missing_from_latest_build = False
            if row.publication_status == "hidden" and not key.startswith("submission:"):
                row.publication_status = "published"  # muncul lagi di build terbaru
            diff["missing_from_latest_build"] = {"from": True, "to": False}
        if diff:
            row.record_updated_at = now
            row.last_import_job = job_id
            db.add(DirectoryPlaceHistory(place_id=row.id, changed_at=now, change_type="import.update", changes=diff,
                                         job_id=job_id, actor_user_id=operator.id if operator else None))
            rep["places"]["updated"] += 1
        else:
            rep["places"]["unchanged"] += 1
    for key, row in rows.items():
        if key not in seen and row.missing_from_latest_build and row.publication_status == "published" and not key.startswith("submission:"):
            row.publication_status = "hidden"  # sudah ditandai hilang pada impor lama: sembunyikan sekarang
            db.add(DirectoryPlaceHistory(place_id=row.id, changed_at=now, change_type="import.hidden",
                                         changes={"note": "tidak ada di build terbaru; disembunyikan, tidak dihapus"}, job_id=job_id))
            rep["places"]["marked_missing"] += 1
        elif key not in seen and not row.missing_from_latest_build:
            row.missing_from_latest_build = True
            # Tempat hasil pipeline yang tidak lolos saringan lagi disembunyikan (BUKAN dihapus; riwayat tetap ada).
            # Tempat dari kiriman yang ditinjau redaksi tidak disentuh importer.
            hide = not key.startswith("submission:") and row.publication_status == "published"
            if hide:
                row.publication_status = "hidden"
            db.add(DirectoryPlaceHistory(place_id=row.id, changed_at=now, change_type="import.missing",
                                         changes={"note": "tidak ada di build terbaru" + ("; disembunyikan, tidak dihapus" if hide else "; tidak dihapus")},
                                         job_id=job_id))
            rep["places"]["marked_missing"] += 1

    # area warisan
    areas = {a.entity_id: a for a in db.scalars(select(DirectoryHeritageArea))}
    for h in b["heritage"]["areas"]:
        vals = {"name": h["name"], "category": h["category"], "regency_codes": h["regency_codes"], "points": h["points"],
                "locality_text": h.get("locality_text"), "public_note": h.get("public_note"), "sources": h.get("sources", [])}
        row = areas.get(h["entity_id"])
        if row is None:
            db.add(DirectoryHeritageArea(entity_id=h["entity_id"], **vals))
            rep["heritage_areas"] += 1
        else:
            for k, v in vals.items():
                setattr(row, k, v)

    job = b["job"]
    prev = db.scalar(select(DirectoryImportJob).where(DirectoryImportJob.job_id == job_id))
    if prev is None:
        db.add(DirectoryImportJob(job_id=job_id, pipeline_version=b["places"]["pipeline_version"], built_at=b["places"]["generated_at"],
                                  imported_at=now, imported_by_user_id=operator.id if operator else None,
                                  stages=job.get("stages", []), errors=job.get("errors", []), result=job.get("result", {}),
                                  import_counts=rep))
    else:
        prev.imported_at, prev.import_counts = now, rep
    if execute:
        db.commit()
    else:
        db.rollback()
    return rep


def _locked_fields(db: Session, row: DirectoryPlace) -> set[str]:
    hist = db.scalars(select(DirectoryPlaceHistory).where(DirectoryPlaceHistory.place_id == row.id,
                                                          DirectoryPlaceHistory.change_type == "submission.apply"))
    out: set[str] = set()
    for h in hist:
        out |= set(h.changes.get("fields", {}).keys())
    return out


def _set_sources(db: Session, row: DirectoryPlace, sources: list[dict]) -> None:
    row.sources.clear()
    db.flush()
    for i, s in enumerate(sources):
        row.sources.append(DirectoryPlaceSource(
            position=i, source_type=s["source_type"], source_id=s.get("source_id"), url=s.get("url"), title=s.get("title"),
            publisher=s.get("publisher"), year=s.get("year") if isinstance(s.get("year"), int) else None,
            license=s.get("license"), attribution=s.get("attribution"), read_status=s.get("read_status"),
            retrieved_at=s.get("retrieved_at"), supports=s.get("supports") or []))


def _src_tuple(s) -> tuple:
    g = (lambda k: getattr(s, k)) if not isinstance(s, dict) else s.get
    return (g("source_type"), g("source_id"), g("url"), g("title"))


def _jsonable(v):
    return v if isinstance(v, (str, int, float, bool, list, dict, type(None))) else str(v)
