"""Partner Workspace: profil, anggota, tradisi, dokumen persetujuan (privat), verifikasi + riwayat.

Membuat profil BUKAN mitra resmi. `verified` hanya lewat keputusan admin dengan bukti; identitas + waktu tersimpan.
"""

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import (
    AuditLog,
    CulturalTradition,
    Partner,
    PartnerDocument,
    PartnerMember,
    PartnerVerificationEvent,
    TraditionPartner,
    User,
)
from app.schemas import studio as sc
from app.services import audit, storage
from app.services import studio_perm as perm
from app.services import visibility as vis
from app.services.auth import now
from app.services.manage import map_integrity, slugify

EDITABLE_PROFILE = {"draft", "rejected"}
VERIF_LABEL = {
    "draft": "Draf — belum diajukan",
    "pending_verification": "Menunggu verifikasi admin",
    "verified": "Terverifikasi",
    "rejected": "Ditolak",
    "suspended": "Ditangguhkan",
}


def _unique_slug(db: Session, base: str) -> str:
    slug, n = base, 1
    while db.scalar(select(Partner.id).where(Partner.slug == slug)):
        n += 1
        slug = f"{base}-{n}"
    return slug


def _event(db, partner, action, frm, to, user, note=None, evidence=None):
    db.add(
        PartnerVerificationEvent(
            partner_id=partner.id,
            action=action,
            from_status=frm,
            to_status=to,
            actor_user_id=user.id,
            note=note,
            evidence_ref=evidence,
            created_at=now(),
        )
    )


def create(db: Session, user: User, body: sc.PartnerCreate, rid) -> Partner:
    if user.role not in perm.STUDIO_ROLES:
        raise ApiError(403, "FORBIDDEN", "Hanya instruktur, kurator, atau admin yang dapat membuat profil mitra.")
    if body.public_listing_consent:
        raise ApiError(
            422,
            "CONSENT_AFTER_VERIFICATION",
            "Persetujuan tampil di direktori publik baru dapat diberikan setelah mitra terverifikasi.",
        )
    data = body.model_dump(exclude={"slug", "public_listing_consent"})
    p = Partner(
        **data,
        slug=_unique_slug(db, body.slug or slugify(body.name)),
        created_by_user_id=user.id,
        status="draft",
        verification_status="draft",
        is_demo=False,
    )
    db.add(p)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise map_integrity(exc) from exc
    db.add(PartnerMember(partner_id=p.id, user_id=user.id, role="manager", invited_by_user_id=user.id))
    _event(db, p, "create", None, "draft", user)
    audit.record(
        db,
        actor=user,
        action="partner.create",
        entity_type="partner",
        entity_id=p.id,
        detail={"name": p.name},
        request_id=rid,
    )
    return p


def update(db: Session, user: User, p: Partner, body: sc.PartnerPatch, rid) -> Partner:
    changes = body.model_dump(exclude_unset=True)
    consent = changes.pop("public_listing_consent", None)
    if changes and p.verification_status not in EDITABLE_PROFILE:
        raise ApiError(409, "NOT_EDITABLE", "Profil hanya dapat diubah saat berstatus draf atau ditolak.")
    for k, v in changes.items():
        if v is None and k in {"name", "partner_type"}:
            raise ApiError(422, "VALIDATION_ERROR", f"Field {k} tidak boleh kosong.")
        setattr(p, k, v)
    if consent is not None:
        if consent and p.verification_status != "verified":
            raise ApiError(
                409, "CONSENT_AFTER_VERIFICATION", "Persetujuan tampil publik hanya untuk mitra terverifikasi."
            )
        p.public_listing_consent = consent
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise map_integrity(exc) from exc
    audit.record(
        db,
        actor=user,
        action="partner.update",
        entity_type="partner",
        entity_id=p.id,
        detail={"fields": sorted(list(changes) + (["public_listing_consent"] if consent is not None else []))},
        request_id=rid,
    )
    return p


# ---------- anggota ----------
def add_member(db: Session, actor: User, p: Partner, body: sc.MemberIn, rid) -> PartnerMember:
    u = db.scalar(select(User).where(func.lower(User.email) == body.email.strip().lower(), User.status == "active"))
    if not u or u.role not in perm.STUDIO_ROLES:
        # pesan sama untuk "tidak ada" dan "peran tidak sesuai": tidak membocorkan keberadaan akun
        raise ApiError(
            422,
            "MEMBER_NOT_ELIGIBLE",
            "Pengguna tidak ditemukan atau belum berperan instruktur. Minta admin menetapkan peran instruktur.",
        )
    m = db.scalar(select(PartnerMember).where(PartnerMember.partner_id == p.id, PartnerMember.user_id == u.id))
    if m:
        m.role, m.status = body.role, "active"
    else:
        m = PartnerMember(partner_id=p.id, user_id=u.id, role=body.role, invited_by_user_id=actor.id)
        db.add(m)
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="partner.member_add",
        entity_type="partner",
        entity_id=p.id,
        detail={"user_id": str(u.id), "role": body.role},
        request_id=rid,
    )
    return m


def remove_member(db: Session, actor: User, p: Partner, user_id, rid) -> None:
    uid = perm.parse_id(user_id, "Anggota")
    m = db.scalar(
        select(PartnerMember).where(
            PartnerMember.partner_id == p.id, PartnerMember.user_id == uid, PartnerMember.status == "active"
        )
    )
    if not m:
        raise ApiError(404, "NOT_FOUND", "Anggota tidak ditemukan.")
    if (
        m.role == "manager"
        and (
            db.scalar(
                select(func.count())
                .select_from(PartnerMember)
                .where(
                    PartnerMember.partner_id == p.id, PartnerMember.role == "manager", PartnerMember.status == "active"
                )
            )
            or 0
        )
        <= 1
    ):
        raise ApiError(409, "LAST_MANAGER", "Mitra harus memiliki minimal satu penanggung jawab (manager).")
    m.status = "removed"
    audit.record(
        db,
        actor=actor,
        action="partner.member_remove",
        entity_type="partner",
        entity_id=p.id,
        detail={"user_id": str(uid)},
        request_id=rid,
    )


# ---------- tradisi ----------
def set_tradition(db: Session, actor: User, p: Partner, tradition_id, present: bool, rid) -> None:
    if p.verification_status not in EDITABLE_PROFILE and actor.role != "admin":
        raise ApiError(
            409,
            "NOT_EDITABLE",
            "Cakupan tradisi mitra terverifikasi hanya dapat diubah admin (butuh verifikasi ulang).",
        )
    tid = perm.parse_id(tradition_id, "Tradisi")
    t = db.scalar(select(CulturalTradition).where(CulturalTradition.id == tid, CulturalTradition.deleted_at.is_(None)))
    if not t or (
        not perm.is_staff(actor)
        and not db.scalar(select(CulturalTradition.id).where(CulturalTradition.id == tid, vis.tradition_ok()))
    ):
        raise ApiError(404, "NOT_FOUND", "Tradisi tidak ditemukan.")
    link = db.scalar(
        select(TraditionPartner).where(TraditionPartner.partner_id == p.id, TraditionPartner.tradition_id == tid)
    )
    if present and not link:
        db.add(TraditionPartner(partner_id=p.id, tradition_id=tid, relationship_type="teaching_partner"))
    elif not present and link:
        db.delete(link)
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="partner.tradition_set" if present else "partner.tradition_unset",
        entity_type="partner",
        entity_id=p.id,
        detail={"tradition_id": str(tid)},
        request_id=rid,
    )


# ---------- dokumen persetujuan (privat) ----------
def add_document(db: Session, actor: User, p: Partner, upload: UploadFile, kind: str, description: str | None, rid):
    if kind not in {"approval_letter", "identity", "other"}:
        raise ApiError(422, "VALIDATION_ERROR", "Jenis dokumen tidak valid.")
    if p.verification_status == "suspended":
        raise ApiError(409, "NOT_EDITABLE", "Mitra yang ditangguhkan tidak dapat menambah dokumen.")
    st = storage.save_upload(upload, storage.DOC_TYPES)
    d = PartnerDocument(
        partner_id=p.id,
        kind=kind,
        description=(description or None) and description[:300],
        original_filename=st.filename,
        storage_key=st.key,
        mime=st.mime,
        size_bytes=st.size,
        sha256=st.sha256,
        uploaded_by_user_id=actor.id,
    )
    db.add(d)
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="partner.document_add",
        entity_type="partner",
        entity_id=p.id,
        detail={"document_id": str(d.id), "kind": kind, "sha256": st.sha256},
        request_id=rid,
    )
    return d


def get_document(db: Session, user: User, doc_id) -> PartnerDocument:
    d = db.get(PartnerDocument, perm.parse_id(doc_id, "Dokumen"))
    if not d:
        raise ApiError(404, "NOT_FOUND", "Dokumen tidak ditemukan.")
    p = db.get(Partner, d.partner_id)
    if not p or p.deleted_at or not (perm.is_staff(user) or perm.is_manager(db, user, p.id)):
        raise ApiError(
            404, "NOT_FOUND", "Dokumen tidak ditemukan."
        )  # anggota biasa pun tidak melihat dokumen persetujuan
    return d


def delete_document(db: Session, user: User, d: PartnerDocument, rid) -> None:
    p = db.get(Partner, d.partner_id)
    if not perm.can_edit_partner(db, user, p.id):
        raise ApiError(403, "FORBIDDEN", "Hanya manager atau admin yang dapat menghapus dokumen.")
    if p.verification_status not in EDITABLE_PROFILE:
        raise ApiError(409, "NOT_EDITABLE", "Dokumen bukti tidak dapat dihapus setelah diajukan.")
    key = d.storage_key
    db.delete(d)
    db.flush()
    storage.remove(key)
    audit.record(
        db,
        actor=user,
        action="partner.document_delete",
        entity_type="partner",
        entity_id=p.id,
        detail={"document_id": str(d.id)},
        request_id=rid,
    )


# ---------- verifikasi ----------
def _doc_count(db, p) -> int:
    return db.scalar(select(func.count()).select_from(PartnerDocument).where(PartnerDocument.partner_id == p.id)) or 0


def readiness(db: Session, p: Partner) -> list[dict]:
    n_trad = (
        db.scalar(select(func.count()).select_from(TraditionPartner).where(TraditionPartner.partner_id == p.id)) or 0
    )
    return [
        {
            "key": "responsible",
            "label": "Penanggung jawab (nama & peran)",
            "ok": bool(p.responsible_name and p.responsible_role),
        },
        {"key": "contact", "label": "Email kontak resmi", "ok": bool(p.contact_email)},
        {"key": "traditions", "label": "Minimal satu tradisi dalam cakupan", "ok": n_trad > 0},
        {"key": "documents", "label": "Minimal satu dokumen persetujuan terunggah", "ok": _doc_count(db, p) > 0},
    ]


def allowed_actions(db: Session, user: User, p: Partner) -> list[str]:
    st, out = p.verification_status, []
    mgr = perm.can_edit_partner(db, user, p.id)
    adm = user.role == "admin" and not perm.member_role(db, user, p.id)
    if st == "draft" and mgr:
        out.append("submit")
    if st == "pending_verification" and adm:
        out += ["verify", "reject"]
    if st in {"verified", "pending_verification"} and adm:
        out.append("suspend")
    if st == "rejected" and mgr:
        out.append("reopen")
    if st == "suspended" and adm:
        out.append("reinstate")
    if st == "verified" and p.public_listing_consent and p.status != "published" and adm:
        out.append("publish_listing")
    if p.status == "published" and (adm or mgr):
        out.append("unlist")
    return out


def act(db: Session, user: User, p: Partner, body: sc.PartnerAction, rid) -> Partner:
    action, st = body.action, p.verification_status
    if action not in allowed_actions(db, user, p):
        # bedakan 'tidak berwenang' vs 'status tidak cocok' agar pesan membantu
        if (
            user.role == "admin"
            and perm.member_role(db, user, p.id)
            and action in {"verify", "reject", "suspend", "reinstate", "publish_listing"}
        ):
            raise ApiError(
                403, "SELF_APPROVAL", "Anda anggota mitra ini; keputusan verifikasi harus dilakukan admin lain."
            )
        raise ApiError(409, "INVALID_TRANSITION", f"Aksi '{action}' tidak tersedia dari status '{st}' untuk Anda.")
    t = now()
    note = (body.note or "").strip() or None
    new = st
    if action == "submit":
        missing = [r["label"] for r in readiness(db, p) if not r["ok"]]
        if missing:
            raise ApiError(422, "INCOMPLETE", "Profil belum lengkap untuk diajukan.", {"missing": missing})
        new, p.submitted_at = "pending_verification", t
    elif action == "verify":
        ev = (body.evidence_ref or "").strip()
        if not ev:
            raise ApiError(422, "EVIDENCE_REQUIRED", "Rujukan bukti verifikasi (evidence_ref) wajib diisi.")
        if _doc_count(db, p) < 1:
            raise ApiError(422, "DOCUMENT_REQUIRED", "Mitra belum mengunggah dokumen persetujuan.")
        new = "verified"
        p.verification_decided_by_user_id, p.verification_decided_at, p.verification_note = user.id, t, note
        p.approval_evidence_ref = ev
        if hasattr(p, "verified_at"):
            p.verified_at = t
    elif action in {"reject", "suspend"}:
        if not note:
            raise ApiError(422, "NOTE_REQUIRED", "Alasan wajib diisi.")
        new = "rejected" if action == "reject" else "suspended"
        p.verification_decided_by_user_id, p.verification_decided_at, p.verification_note = user.id, t, note
        if action == "suspend":
            p.public_listing_consent = False
            if p.status == "published":
                p.status, p.published_at = "archived", None
    elif action == "reopen":
        new = "draft"
    elif action == "reinstate":
        new, p.verification_decided_by_user_id, p.verification_decided_at = "pending_verification", None, None
    elif action == "publish_listing":
        ev = p.approval_evidence_ref or ""
        p.status, p.published_at, p.approved_by_user_id, p.approved_at = "published", t, user.id, t
        p.source_citation = p.source_citation or f"Verifikasi kemitraan SILATARA (rujukan: {ev})"
    elif action == "unlist":
        p.status, p.published_at = "draft", None
    p.verification_status = new
    _event(db, p, action, st, new, user, note, body.evidence_ref)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise map_integrity(exc) from exc
    audit.record(
        db,
        actor=user,
        action=f"partner.{action}",
        entity_type="partner",
        entity_id=p.id,
        detail={"from": st, "to": new, "note": note},
        request_id=rid,
    )
    return p


# ---------- serialisasi ----------
def _members(db, p) -> list[dict]:
    rows = db.execute(
        select(PartnerMember, User)
        .join(User, User.id == PartnerMember.user_id)
        .where(PartnerMember.partner_id == p.id, PartnerMember.status == "active")
        .order_by(PartnerMember.role, User.display_name)
    ).all()
    return [
        {"user_id": u.id, "name": u.display_name, "email": u.email, "role": m.role, "user_role": u.role}
        for m, u in rows
    ]


def summary(db: Session, user: User, p: Partner) -> dict:
    return {
        "id": p.id,
        "slug": p.slug,
        "name": p.name,
        "partner_type": p.partner_type,
        "region": p.region,
        "city": p.city,
        "verification_status": p.verification_status,
        "verification_label": ("[DEMO] " if p.is_demo else "") + VERIF_LABEL[p.verification_status],
        "is_demo": p.is_demo,
        "listed_publicly": p.status == "published",
        "my_role": perm.member_role(db, user, p.id),
        "updated_at": p.updated_at,
    }


def detail(db: Session, user: User, p: Partner) -> dict:
    traditions = db.execute(
        select(CulturalTradition.id, CulturalTradition.slug, CulturalTradition.name)
        .join(TraditionPartner, TraditionPartner.tradition_id == CulturalTradition.id)
        .where(TraditionPartner.partner_id == p.id)
        .order_by(CulturalTradition.name)
    ).all()
    docs = (
        db.scalars(
            select(PartnerDocument)
            .where(PartnerDocument.partner_id == p.id)
            .order_by(PartnerDocument.created_at.desc())
        ).all()
        if (perm.is_staff(user) or perm.is_manager(db, user, p.id))
        else []
    )
    decider = db.get(User, p.verification_decided_by_user_id) if p.verification_decided_by_user_id else None
    return {
        **summary(db, user, p),
        "official_description": p.official_description,
        "responsible_name": p.responsible_name,
        "responsible_role": p.responsible_role,
        "responsible_contact": p.responsible_contact,
        "contact_email": p.contact_email,
        "contact_phone": p.contact_phone,
        "public_listing_consent": p.public_listing_consent,
        "verification_note": p.verification_note,
        "approval_evidence_ref": p.approval_evidence_ref,
        "verification_decided_by": decider.display_name if decider else None,
        "verification_decided_at": p.verification_decided_at,
        "submitted_at": p.submitted_at,
        "members": _members(db, p),
        "traditions": [{"id": i, "slug": s, "name": n} for i, s, n in traditions],
        "documents": [
            {
                "id": d.id,
                "kind": d.kind,
                "description": d.description,
                "filename": d.original_filename,
                "mime": d.mime,
                "size_bytes": d.size_bytes,
                "sha256": d.sha256,
                "created_at": d.created_at,
            }
            for d in docs
        ],
        "readiness": readiness(db, p),
        "allowed_actions": allowed_actions(db, user, p),
        "can_edit_profile": perm.can_edit_partner(db, user, p.id) and p.verification_status in EDITABLE_PROFILE,
        "can_manage": perm.can_edit_partner(db, user, p.id),
    }


def history(db: Session, p: Partner) -> list[dict]:
    rows = db.execute(
        select(PartnerVerificationEvent, User.display_name)
        .outerjoin(User, User.id == PartnerVerificationEvent.actor_user_id)
        .where(PartnerVerificationEvent.partner_id == p.id)
        .order_by(PartnerVerificationEvent.created_at.desc())
    ).all()
    return [
        {
            "action": e.action,
            "from_status": e.from_status,
            "to_status": e.to_status,
            "actor": n,
            "note": e.note,
            "evidence_ref": e.evidence_ref,
            "created_at": e.created_at,
        }
        for e, n in rows
    ]


def list_for(db: Session, user: User, page: int, size: int, status: str | None, q: str | None) -> dict:
    from app.services.queries import paginate, search_cond

    stmt = select(Partner).where(Partner.deleted_at.is_(None))
    if not perm.is_staff(user):
        stmt = stmt.where(Partner.id.in_(perm.my_partner_ids(db, user)))
    if status:
        stmt = stmt.where(Partner.verification_status == status)
    if (c := search_cond(q, Partner.name, Partner.city)) is not None:
        stmt = stmt.where(c)
    return paginate(db, stmt.order_by(Partner.updated_at.desc()), page, size, lambda x: summary(db, user, x))


_ = AuditLog  # dipakai modul lain untuk riwayat gabungan
