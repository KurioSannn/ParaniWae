import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, PageParams, auth_required
from app.core.db import get_db
from app.core.errors import ApiError
from app.models import AuditLog, Course, CourseModule, Lesson, LessonMaterial
from app.schemas import manage as sc
from app.services import audit
from app.services import manage as svc
from app.services.queries import paginate, search_cond

router = APIRouter(prefix="/manage", tags=["manajemen konten"])
Staff = auth_required("instructor", "curator", "admin")


def _rid(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _item(kind: svc.Kind, obj) -> dict:
    return {
        "id": obj.id, "kind": kind.key, "slug": obj.slug, "title": svc.title_of(kind, obj),
        "status": obj.status, "is_demo": obj.is_demo, "updated_at": obj.updated_at,
        "created_by_user_id": obj.created_by_user_id,
    }


def _detail(db: Session, ctx: AuthContext, kind: svc.Kind, obj) -> dict:
    out: dict[str, Any] = {
        "kind": kind.key, "fields": svc.serialize(obj),
        "allowed_actions": svc.allowed_actions(ctx.user, obj),
        "can_edit": obj.status in svc.EDITABLE,
        "history": svc.history(db, kind, obj.id),
    }
    if kind.key == "courses":
        mods = db.scalars(select(CourseModule).where(CourseModule.course_id == obj.id)
                          .order_by(CourseModule.order_index)).all()
        out["modules"] = [svc.serialize(m) for m in mods]
    if kind.key == "lessons":
        mats = db.scalars(select(LessonMaterial).where(LessonMaterial.lesson_id == obj.id)
                          .order_by(LessonMaterial.order_index)).all()
        out["materials"] = [svc.serialize(m) for m in mats]
    return jsonable_encoder(out)


def _flush(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise svc.map_integrity(exc) from exc


# ---- Modul ----
@router.post("/modules", status_code=201, summary="Buat modul kurikulum")
def create_module(body: sc.ModuleIn, request: Request, ctx: AuthContext = Depends(Staff),
                  db: Session = Depends(get_db)):
    svc.editable_module_parent(db, ctx.user, body.course_id)
    m = CourseModule(**body.model_dump())
    db.add(m)
    _flush(db)
    audit.record(db, actor=ctx.user, action="content.module_create", entity_type="courses",
                 entity_id=m.course_id, detail={"module": m.title}, request_id=_rid(request))
    db.commit()
    return jsonable_encoder(svc.serialize(m))


@router.patch("/modules/{module_id}", summary="Ubah modul")
def patch_module(module_id: uuid.UUID, body: sc.make_patch(sc.ModuleIn),  # type: ignore[valid-type]
                 request: Request, ctx: AuthContext = Depends(Staff),
                 db: Session = Depends(get_db)):
    m = db.get(CourseModule, module_id)
    if not m:
        raise ApiError(404, "NOT_FOUND", "Modul tidak ditemukan.")
    svc.editable_module_parent(db, ctx.user, m.course_id)
    changes = body.model_dump(exclude_unset=True)
    if "course_id" in changes:
        raise ApiError(422, "VALIDATION_ERROR", "course_id modul tidak dapat diubah.")
    for k, v in changes.items():
        if v is None and k in {"title", "order_index"}:
            raise ApiError(422, "VALIDATION_ERROR", f"Field {k} tidak boleh kosong.")
        setattr(m, k, v)
    _flush(db)
    db.commit()
    return jsonable_encoder(svc.serialize(m))


@router.delete("/modules/{module_id}", status_code=204, summary="Hapus modul (harus tanpa pelajaran)")
def delete_module(module_id: uuid.UUID, ctx: AuthContext = Depends(Staff),
                  db: Session = Depends(get_db)):
    m = db.get(CourseModule, module_id)
    if not m:
        raise ApiError(404, "NOT_FOUND", "Modul tidak ditemukan.")
    svc.editable_module_parent(db, ctx.user, m.course_id)
    if db.scalar(select(Lesson.id).where(Lesson.module_id == m.id, Lesson.deleted_at.is_(None))):
        raise ApiError(409, "NOT_EMPTY", "Pindahkan atau hapus pelajaran di modul ini terlebih dahulu.")
    db.delete(m)
    db.commit()


# ---- Materi ----
@router.post("/materials", status_code=201, summary="Tambah materi pendukung pelajaran")
def create_material(body: sc.MaterialIn, request: Request, ctx: AuthContext = Depends(Staff),
                    db: Session = Depends(get_db)):
    svc.editable_lesson_parent(db, ctx.user, body.lesson_id)
    if body.kind == "link" and not body.url:
        raise ApiError(422, "VALIDATION_ERROR", "Materi tipe link wajib memiliki url.")
    m = LessonMaterial(**body.model_dump())
    db.add(m)
    _flush(db)
    audit.record(db, actor=ctx.user, action="content.material_create", entity_type="lessons",
                 entity_id=m.lesson_id, detail={"material": m.title}, request_id=_rid(request))
    db.commit()
    return jsonable_encoder(svc.serialize(m))


@router.delete("/materials/{material_id}", status_code=204, summary="Hapus materi pendukung")
def delete_material(material_id: uuid.UUID, ctx: AuthContext = Depends(Staff),
                    db: Session = Depends(get_db)):
    m = db.get(LessonMaterial, material_id)
    if not m:
        raise ApiError(404, "NOT_FOUND", "Materi tidak ditemukan.")
    svc.editable_lesson_parent(db, ctx.user, m.lesson_id)
    db.delete(m)
    db.commit()


# ---- Konten utama (generik) ----
@router.get("/kinds", summary="Jenis konten yang boleh saya kelola")
def my_kinds(ctx: AuthContext = Depends(Staff)):
    return [{"key": k.key, "label": k.label} for k in svc.KINDS.values()
            if svc.can_use_kind(ctx.user, k)]


@router.get("/{kind}", summary="Daftar konten (semua status; instruktur hanya miliknya)")
def list_content(kind: str, status: str | None = None, q: str | None = None,
                 p: PageParams = Depends(), ctx: AuthContext = Depends(Staff),
                 db: Session = Depends(get_db)):
    k = svc.get_kind(kind)
    if not svc.can_use_kind(ctx.user, k):
        raise ApiError(403, "FORBIDDEN", "Anda tidak memiliki izin untuk jenis konten ini.")
    M = k.model
    stmt = select(M).where(M.deleted_at.is_(None))
    if ctx.user.role not in svc.STAFF:
        stmt = stmt.where(M.created_by_user_id == ctx.user.id)
    if status:
        stmt = stmt.where(M.status == status)
    if (c := search_cond(q, getattr(M, k.name_attr), M.slug)) is not None:
        stmt = stmt.where(c)
    stmt = stmt.order_by(M.updated_at.desc())
    return jsonable_encoder(paginate(db, stmt, p.page, p.page_size, lambda o: _item(k, o)))


@router.post("/{kind}", status_code=201, summary="Buat konten (selalu berstatus draft)")
def create_content(kind: str, body: dict, request: Request, ctx: AuthContext = Depends(Staff),
                   db: Session = Depends(get_db)):
    k = svc.get_kind(kind)
    if not svc.can_use_kind(ctx.user, k):
        raise ApiError(403, "FORBIDDEN", "Anda tidak memiliki izin untuk membuat jenis konten ini.")
    parsed = _parse(k.create, body)
    obj = svc.create(db, ctx.user, k, parsed, _rid(request))
    db.commit()
    return _detail(db, ctx, k, obj)


@router.get("/{kind}/{obj_id}", summary="Detail konten + riwayat audit")
def get_content(kind: str, obj_id: str, ctx: AuthContext = Depends(Staff),
                db: Session = Depends(get_db)):
    k = svc.get_kind(kind)
    return _detail(db, ctx, k, svc.load(db, k, obj_id, ctx.user))


@router.patch("/{kind}/{obj_id}", summary="Ubah konten (hanya draft/ditolak)")
def patch_content(kind: str, obj_id: str, body: dict, request: Request,
                  ctx: AuthContext = Depends(Staff), db: Session = Depends(get_db)):
    k = svc.get_kind(kind)
    obj = svc.load(db, k, obj_id, ctx.user)
    svc.update(db, ctx.user, k, obj, _parse(k.patch, body), _rid(request))
    db.commit()
    return _detail(db, ctx, k, obj)


@router.delete("/{kind}/{obj_id}", status_code=204, summary="Hapus lunak konten")
def delete_content(kind: str, obj_id: str, request: Request, ctx: AuthContext = Depends(Staff),
                   db: Session = Depends(get_db)):
    k = svc.get_kind(kind)
    obj = svc.load(db, k, obj_id, ctx.user)
    svc.soft_delete(db, ctx.user, k, obj, _rid(request))
    db.commit()


@router.post("/{kind}/{obj_id}/transition", summary="Ubah status alur kerja")
def transition_content(kind: str, obj_id: str, body: sc.TransitionIn, request: Request,
                       ctx: AuthContext = Depends(Staff), db: Session = Depends(get_db)):
    """submit → approve/reject → publish; unpublish/archive/restore. Lihat ADR/DATA_MODEL."""
    k = svc.get_kind(kind)
    obj = svc.load(db, k, obj_id, ctx.user)
    svc.transition(db, ctx.user, k, obj, body, _rid(request))
    db.commit()
    return _detail(db, ctx, k, obj)


def _parse(model, body: dict):
    from pydantic import ValidationError

    try:
        return model.model_validate(body)
    except ValidationError as exc:
        details = [{"field": ".".join(str(x) for x in e["loc"]), "message": e["msg"]}
                   for e in exc.errors()]
        raise ApiError(422, "VALIDATION_ERROR", "Data yang dikirim tidak valid.", details) from exc


_ = (AuditLog, Course, Query)  # dipakai oleh modul lain / dokumentasi
