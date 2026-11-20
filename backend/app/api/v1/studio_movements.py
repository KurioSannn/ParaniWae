from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, PageParams, auth_required
from app.core.db import get_db
from app.schemas import studio as sc
from app.services import media as media_svc
from app.services import movement_studio as ms
from app.services import studio_perm as perm

router = APIRouter(prefix="/studio", tags=["studio: gerakan"])
Studio = auth_required(*perm.STUDIO_ROLES)


def _rid(r: Request):
    return getattr(r.state, "request_id", None)


@router.get("/dashboard", summary="Instructor Dashboard")
def dashboard(ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    return ms.dashboard(db, ctx.user)


@router.get("/movements", summary="Gerakan yang dapat saya kelola")
def list_movements(
    q: str | None = None,
    status: str | None = None,
    tradition_id: str | None = None,
    partner_id: str | None = None,
    safety_category: str | None = None,
    level: str | None = None,
    p: PageParams = Depends(),
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    tid = perm.parse_id(tradition_id) if tradition_id else None
    pid = perm.parse_id(partner_id) if partner_id else None
    return ms.list_movements(
        db,
        ctx.user,
        p.page,
        p.page_size,
        q=q,
        status=status,
        tradition_id=tid,
        partner_id=pid,
        safety_category=safety_category,
        level=level,
    )


@router.post("/movements", status_code=201, summary="Buat dokumentasi gerakan (versi 1, draf)")
def create_movement(
    body: sc.MovementCreate, request: Request, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)
):
    m = ms.create_movement(db, ctx.user, body, _rid(request))
    db.commit()
    return ms.detail_out(db, ctx.user, m)


@router.get("/movements/{movement_id}", summary="Detail gerakan (dokumentasi, versi, tautan lesson)")
def get_movement(movement_id: str, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    return ms.detail_out(db, ctx.user, perm.get_movement(db, ctx.user, movement_id))


@router.get("/movements/{movement_id}/versions/{version_no}", summary="Satu versi dokumentasi")
def get_version(movement_id: str, version_no: int, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    from sqlalchemy import select

    from app.core.errors import ApiError
    from app.models import MovementDocument

    m = perm.get_movement(db, ctx.user, movement_id)
    d = db.scalar(
        select(MovementDocument).where(MovementDocument.movement_id == m.id, MovementDocument.version_no == version_no)
    )
    if not d:
        raise ApiError(404, "NOT_FOUND", "Versi tidak ditemukan.")
    return ms.doc_out(db, ctx.user, d, m)


@router.post("/movements/{movement_id}/versions", status_code=201, summary="Buat versi baru dari versi tayang")
def new_version(movement_id: str, request: Request, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    m = perm.get_movement(db, ctx.user, movement_id)
    ms.new_version(db, ctx.user, m, _rid(request))
    db.commit()
    return ms.detail_out(db, ctx.user, m)


@router.patch("/documents/{doc_id}", summary="Ubah isi dokumentasi (draf/revisi; dipakai autosave)")
def patch_document(
    doc_id: str,
    body: sc.DocumentPatch,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    d, m = ms.get_doc(db, ctx.user, doc_id)
    ms.update_document(db, ctx.user, d, m, body, _rid(request))
    db.commit()
    return ms.doc_out(db, ctx.user, d, m)


@router.put("/documents/{doc_id}/phases", summary="Ganti seluruh fase berurutan")
def put_phases(
    doc_id: str, body: sc.PhasesPut, request: Request, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)
):
    d, m = ms.get_doc(db, ctx.user, doc_id)
    ms.put_phases(db, ctx.user, d, body, _rid(request))
    db.commit()
    return ms.doc_out(db, ctx.user, d, m)


@router.post("/documents/{doc_id}/transition", summary="Alur review: ajukan/tinjau/konfirmasi/setujui/terbitkan")
def transition(
    doc_id: str,
    body: sc.DocTransition,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    d, m = ms.get_doc(db, ctx.user, doc_id)
    ms.transition(db, ctx.user, d, m, body, _rid(request))
    db.commit()
    return ms.detail_out(db, ctx.user, m)


@router.get("/movements/{movement_id}/history", summary="Riwayat perubahan & keputusan")
def history(movement_id: str, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    return ms.history(db, perm.get_movement(db, ctx.user, movement_id))


@router.get("/movements/{movement_id}/lessons", summary="Pelajaran yang dapat ditautkan")
def linkable(movement_id: str, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    return ms.linkable_lessons(db, ctx.user, perm.get_movement(db, ctx.user, movement_id))


@router.put("/movements/{movement_id}/lessons/{lesson_id}", summary="Tautkan gerakan ke pelajaran")
def link_lesson(
    movement_id: str,
    lesson_id: str,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    m = perm.get_movement(db, ctx.user, movement_id)
    ms.link_lesson(db, ctx.user, m, lesson_id, True, _rid(request))
    db.commit()
    return ms.detail_out(db, ctx.user, m)


@router.delete("/movements/{movement_id}/lessons/{lesson_id}", summary="Lepas tautan gerakan–pelajaran")
def unlink_lesson(
    movement_id: str,
    lesson_id: str,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    m = perm.get_movement(db, ctx.user, movement_id)
    ms.link_lesson(db, ctx.user, m, lesson_id, False, _rid(request))
    db.commit()
    return ms.detail_out(db, ctx.user, m)


# ---------- media ----------
@router.get("/movements/{movement_id}/media", summary="Media referensi gerakan")
def list_media(movement_id: str, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    m = perm.get_movement(db, ctx.user, movement_id)
    return media_svc.list_for(db, ctx.user, m)


@router.post("/movements/{movement_id}/media", status_code=201, summary="Unggah media referensi (wajib deklarasi hak)")
def upload_media(
    movement_id: str,
    request: Request,
    title: str = Form(""),
    rights_holder: str = Form(""),
    source_description: str = Form(""),
    license_type: str = Form(""),
    usage_scope: str = Form(""),
    declaration_confirmed: str = Form("false"),
    retention_until: str | None = Form(None),
    file: UploadFile = File(...),
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    m = perm.get_movement(db, ctx.user, movement_id)
    r = media_svc.upload(
        db,
        ctx.user,
        m,
        file,
        {
            "title": title,
            "rights_holder": rights_holder,
            "source_description": source_description,
            "license_type": license_type,
            "usage_scope": usage_scope,
            "declaration_confirmed": declaration_confirmed,
            "retention_until": retention_until,
        },
        _rid(request),
    )
    db.commit()
    return media_svc.out(db, ctx.user, r, m)


@router.patch("/media/{media_id}", summary="Ubah persetujuan/akses/retensi media")
def patch_media(
    media_id: str,
    body: sc.MediaPatch,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    r, m = media_svc.get_for_studio(db, ctx.user, media_id)
    media_svc.patch(db, ctx.user, r, m, body, _rid(request))
    db.commit()
    return media_svc.out(db, ctx.user, r, m)


@router.delete("/media/{media_id}", status_code=204, summary="Hapus media (file + metadata)")
def delete_media(media_id: str, request: Request, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    r, m = media_svc.get_for_studio(db, ctx.user, media_id)
    media_svc.delete(db, ctx.user, r, m, _rid(request))
    db.commit()


# ---------- anotasi ----------
@router.get("/movements/{movement_id}/annotations", summary="Anotasi referensi instruktur")
def list_annotations(
    movement_id: str,
    media_id: str | None = None,
    fixture_key: str | None = None,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    return media_svc.list_annotations(db, perm.get_movement(db, ctx.user, movement_id), media_id, fixture_key)


@router.post("/movements/{movement_id}/annotations", status_code=201, summary="Tambah anotasi referensi instruktur")
def create_annotation(
    movement_id: str,
    body: sc.AnnotationIn,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    m = perm.get_movement(db, ctx.user, movement_id)
    out = media_svc.create_annotation(db, ctx.user, m, body, _rid(request))
    db.commit()
    return out


@router.patch("/annotations/{ann_id}", summary="Ubah/tinjau anotasi")
def patch_annotation(
    ann_id: str,
    body: sc.AnnotationPatch,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    a, m = media_svc.get_annotation(db, ctx.user, ann_id)
    out = media_svc.patch_annotation(db, ctx.user, a, m, body, _rid(request))
    db.commit()
    return out


@router.delete("/annotations/{ann_id}", status_code=204, summary="Hapus anotasi")
def delete_annotation(ann_id: str, request: Request, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    a, m = media_svc.get_annotation(db, ctx.user, ann_id)
    media_svc.delete_annotation(db, ctx.user, a, m, _rid(request))
    db.commit()


_ = File
