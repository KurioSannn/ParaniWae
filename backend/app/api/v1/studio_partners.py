import uuid

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, PageParams, auth_required
from app.core.db import get_db
from app.core.errors import ApiError
from app.schemas import studio as sc
from app.services import partner_studio as ps
from app.services import storage
from app.services import studio_perm as perm

router = APIRouter(prefix="/studio", tags=["studio: mitra"])
Studio = auth_required(*perm.STUDIO_ROLES)


def _rid(r: Request):
    return getattr(r.state, "request_id", None)


@router.get("/partners", summary="Mitra yang dapat saya kelola/lihat")
def list_partners(
    status: str | None = None,
    q: str | None = None,
    p: PageParams = Depends(),
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    return ps.list_for(db, ctx.user, p.page, p.page_size, status, q)


@router.post("/partners", status_code=201, summary="Buat profil mitra (draf; bukan mitra resmi)")
def create_partner(
    body: sc.PartnerCreate, request: Request, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)
):
    p = ps.create(db, ctx.user, body, _rid(request))
    db.commit()
    return ps.detail(db, ctx.user, p)


@router.get("/partners/{partner_id}", summary="Partner Workspace")
def get_partner(partner_id: str, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    return ps.detail(db, ctx.user, perm.get_partner(db, ctx.user, partner_id))


@router.patch("/partners/{partner_id}", summary="Ubah profil mitra (draf/ditolak)")
def patch_partner(
    partner_id: str,
    body: sc.PartnerPatch,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    p = perm.get_partner(db, ctx.user, partner_id, edit=True)
    ps.update(db, ctx.user, p, body, _rid(request))
    db.commit()
    return ps.detail(db, ctx.user, p)


@router.post("/partners/{partner_id}/members", status_code=201, summary="Tambah anggota (manager/instruktur)")
def add_member(
    partner_id: str,
    body: sc.MemberIn,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    p = perm.get_partner(db, ctx.user, partner_id, edit=True)
    ps.add_member(db, ctx.user, p, body, _rid(request))
    db.commit()
    return ps.detail(db, ctx.user, p)


@router.delete("/partners/{partner_id}/members/{user_id}", summary="Keluarkan anggota")
def remove_member(
    partner_id: str, user_id: str, request: Request, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)
):
    p = perm.get_partner(db, ctx.user, partner_id, edit=True)
    ps.remove_member(db, ctx.user, p, user_id, _rid(request))
    db.commit()
    return ps.detail(db, ctx.user, p)


@router.put("/partners/{partner_id}/traditions/{tradition_id}", summary="Tambah tradisi ke cakupan mitra")
def put_tradition(
    partner_id: str,
    tradition_id: str,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    p = perm.get_partner(db, ctx.user, partner_id, edit=True)
    ps.set_tradition(db, ctx.user, p, tradition_id, True, _rid(request))
    db.commit()
    return ps.detail(db, ctx.user, p)


@router.delete("/partners/{partner_id}/traditions/{tradition_id}", summary="Hapus tradisi dari cakupan mitra")
def delete_tradition(
    partner_id: str,
    tradition_id: str,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    p = perm.get_partner(db, ctx.user, partner_id, edit=True)
    ps.set_tradition(db, ctx.user, p, tradition_id, False, _rid(request))
    db.commit()
    return ps.detail(db, ctx.user, p)


@router.post("/partners/{partner_id}/documents", status_code=201, summary="Unggah dokumen persetujuan (privat)")
def upload_document(
    partner_id: str,
    request: Request,
    kind: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    p = perm.get_partner(db, ctx.user, partner_id, edit=True)
    ps.add_document(db, ctx.user, p, file, kind, description, _rid(request))
    db.commit()
    return ps.detail(db, ctx.user, p)


@router.get("/partner-documents/{doc_id}/file", summary="Unduh dokumen persetujuan (manager/kurator/admin)")
def download_document(doc_id: str, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    d = ps.get_document(db, ctx.user, doc_id)
    if d.scan_status in {"pending", "infected", "error"}:
        raise ApiError(423, "QUARANTINED", "Dokumen masih di karantina atau tidak lolos pemindaian.")
    path = storage.path_for(d.storage_key)
    if not path.exists():
        raise ApiError(404, "NOT_FOUND", "File tidak ditemukan.")
    return FileResponse(
        path,
        media_type=d.mime,
        filename=d.original_filename,
        content_disposition_type="attachment",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/partner-documents/{doc_id}", summary="Hapus dokumen persetujuan (hanya saat draf/ditolak)")
def delete_document(doc_id: str, request: Request, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    d = ps.get_document(db, ctx.user, doc_id)
    p = perm.get_partner(db, ctx.user, d.partner_id)
    ps.delete_document(db, ctx.user, d, _rid(request))
    db.commit()
    return ps.detail(db, ctx.user, p)


@router.post("/partners/{partner_id}/verification", summary="Aksi verifikasi kemitraan")
def verification(
    partner_id: str,
    body: sc.PartnerAction,
    request: Request,
    ctx: AuthContext = Depends(Studio),
    db: Session = Depends(get_db),
):
    p = perm.get_partner(db, ctx.user, partner_id)
    ps.act(db, ctx.user, p, body, _rid(request))
    db.commit()
    return ps.detail(db, ctx.user, p)


@router.get("/partners/{partner_id}/history", summary="Riwayat verifikasi")
def history(partner_id: str, ctx: AuthContext = Depends(Studio), db: Session = Depends(get_db)):
    return ps.history(db, perm.get_partner(db, ctx.user, partner_id))


_ = uuid
