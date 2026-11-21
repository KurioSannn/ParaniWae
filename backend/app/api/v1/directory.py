"""API direktori nasional pencak silat (publik baca; kiriman tanpa login dengan rate limit; tinjauan kurator/admin)."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, auth_required, optional_auth
from app.core.db import get_db
from app.core.errors import ApiError
from app.core.netinfo import client_ip
from app.models import DirectorySubmission
from app.models.directory import PLACE_CATEGORIES
from app.services import audit, ratelimit
from app.services import directory as svc

router = APIRouter(prefix="/directory", tags=["directory"])
CATS = set(PLACE_CATEGORIES)
EMAIL = r"^[^@\s]{1,64}@[^@\s]{1,190}\.[A-Za-z]{2,24}$"


def _filters(
    q: str | None = Query(None, max_length=80),
    province: str | None = Query(None, pattern=r"^\d{2}$"),
    regency: str | None = Query(None, pattern=r"^\d{2}\.\d{2}$"),
    district: str | None = Query(None, max_length=60),
    category: str | None = Query(None, max_length=300, description="satu atau beberapa kategori dipisah koma"),
    organization: str | None = Query(None, max_length=80),
    tradition: str | None = Query(None, max_length=120),
    activity: Literal["training", "office", "heritage"] | None = None,
    has_contact: bool = False,
    has_schedule: bool = False,
    open_public: bool = False,
    status: Literal["active_unverified", "active_confirmed", "inactive", "closed"] | None = None,
    precision: Literal["exact", "regency"] | None = None,
    bbox: str | None = Query(None, description="minLng,minLat,maxLng,maxLat"),
) -> svc.Filters:
    cats = tuple(c for c in (category or "").split(",") if c)
    bad = [c for c in cats if c not in CATS]
    if bad:
        raise ApiError(422, "BAD_CATEGORY", f"Kategori tidak dikenal: {', '.join(bad)}")
    return svc.Filters(q=q, province=province, regency=regency, district=district, categories=cats,
                       organization=organization, tradition=tradition, activity=activity, has_contact=has_contact,
                       has_schedule=has_schedule, open_public=open_public, status=status, precision=precision,
                       bbox=svc.parse_bbox(bbox))


@router.get("/places", summary="Tempat dalam viewport: klaster (zoom rendah) atau titik")
def places(f: svc.Filters = Depends(_filters), zoom: int | None = Query(None, ge=0, le=22),
           near: str | None = Query(None, description="lat,lng lokasi pengguna (tidak disimpan)"),
           sort: Literal["name", "distance"] = "name", db: Session = Depends(get_db)):
    return svc.places(db, f, zoom, svc.parse_point(near), sort)


@router.get("/list", summary="Daftar tempat (sinkron dengan filter peta), berhalaman")
def list_places(f: svc.Filters = Depends(_filters), near: str | None = None, sort: Literal["name", "distance"] = "name",
                page: int = Query(1, ge=1, le=1000), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return svc.list_places(db, f, svc.parse_point(near), sort, page, page_size)


@router.get("/places/{slug}", summary="Detail tempat + sumber")
def place(slug: str, db: Session = Depends(get_db)):
    return svc.place_detail(db, slug)


@router.get("/facets", summary="Pilihan filter beserta jumlah")
def facets(province: str | None = Query(None, pattern=r"^\d{2}$"), db: Session = Depends(get_db)):
    return svc.facets(db, province)


@router.get("/stats", summary="Statistik dihitung dari DB (lokasi yang terdata, bukan peringkat)")
def stats(db: Session = Depends(get_db)):
    return svc.stats(db)


@router.get("/heritage-areas", summary="Area warisan pencak silat yang terdokumentasi sumber")
def heritage(db: Session = Depends(get_db)):
    return {"items": svc.heritage_areas(db)}


# ---------------------------------------------------------------- kiriman
class ScheduleItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    day: str = Field(max_length=20)
    time: str = Field(max_length=40)
    note: str | None = Field(None, max_length=200)


class SubmissionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(None, min_length=3, max_length=200)
    category: str | None = None
    regency_code: str | None = Field(None, pattern=r"^\d{2}\.\d{2}$")
    district: str | None = Field(None, max_length=120)
    address: str | None = Field(None, max_length=400)
    lat: float | None = Field(None, ge=-90, le=90)
    lng: float | None = Field(None, ge=-180, le=180)
    website: HttpUrl | None = None
    contact_email: str | None = Field(None, max_length=200, pattern=EMAIL)
    contact_phone: str | None = Field(None, max_length=40, pattern=r"^[0-9+()\-\s]{6,40}$")
    is_training_location: bool | None = None
    schedule: list[ScheduleItem] | None = Field(None, max_length=14)
    note: str | None = Field(None, max_length=1000)

    @field_validator("category")
    @classmethod
    def _cat(cls, v):
        if v is not None and v not in CATS:
            raise ValueError("kategori tidak dikenal")
        return v


class SubmissionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["new_place", "correction", "contact_update", "schedule_update", "closed_report"]
    place_slug: str | None = Field(None, max_length=120)
    payload: SubmissionPayload
    source_url: HttpUrl | None = None
    submitter_relation: Literal["pengelola", "anggota", "publik"]
    contact_email: str | None = Field(None, max_length=200, pattern=EMAIL, description="untuk tindak lanjut redaksi; tidak ditampilkan publik")
    website_hp: str | None = Field(None, max_length=200, description="honeypot; harus kosong")


@router.post("/submissions", status_code=201, summary="Kirim tempat baru/koreksi (ditinjau redaksi; tidak terbit otomatis)")
def submit(body: SubmissionIn, request: Request, ctx: AuthContext | None = Depends(optional_auth), db: Session = Depends(get_db)):
    ratelimit.hit(db, "directory-submit:ip", client_ip(request), (8, 3600))
    if body.website_hp:
        raise ApiError(422, "REJECTED", "Kiriman tidak dapat diproses.")
    if body.kind == "new_place" and (not body.payload.name or not body.payload.regency_code):
        raise ApiError(422, "FIELDS_REQUIRED", "Nama tempat dan kabupaten/kota wajib diisi.")
    data = body.model_dump(mode="json", exclude={"website_hp"})
    data["payload"] = {k: v for k, v in data["payload"].items() if v is not None}
    sub = svc.create_submission(db, data, ctx.user if ctx else None)
    return {"id": str(sub.id), "status": sub.status, "checks": sub.checks,
            "message": "Terima kasih. Kiriman Anda akan diperiksa redaksi sebelum tampil di direktori."}


class ReviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["approve", "awaiting_manager", "reject", "duplicate", "publish"]
    note: str | None = Field(None, max_length=1000)


@router.get("/submissions", summary="Antrean kiriman (kurator/admin)")
def list_submissions(status: str | None = Query(None, max_length=24),
                     ctx: AuthContext = Depends(auth_required("curator", "admin")), db: Session = Depends(get_db)):
    q = select(DirectorySubmission).order_by(DirectorySubmission.created_at.desc()).limit(200)
    if status:
        q = q.where(DirectorySubmission.status == status)
    return {"items": [svc.submission_out(s, include_private=True) for s in db.scalars(q)]}


@router.post("/submissions/{sub_id}/review", summary="Tinjau kiriman (kurator/admin)")
def review(sub_id: uuid.UUID, body: ReviewIn, request: Request,
           ctx: AuthContext = Depends(auth_required("curator", "admin")), db: Session = Depends(get_db)):
    s = svc.review_submission(db, sub_id, body.action, body.note, ctx.user)
    audit.record(db, actor=ctx.user, action=f"directory.submission.{body.action}", entity_type="directory_submission",
                 entity_id=s.id, detail={"status": s.status}, request_id=request.headers.get("x-request-id"))
    db.commit()
    return svc.submission_out(s, include_private=True)
