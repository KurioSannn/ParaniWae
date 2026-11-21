"""Media referensi: deklarasi hak, persetujuan, akses, retensi. Tidak pernah publik tanpa izin terverifikasi."""

from datetime import date

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import Movement, MovementAnnotation, MovementDocument, MovementPhase, ReferenceMedia, User
from app.schemas import studio as sc
from app.services import audit, scanner, storage
from app.services import studio_perm as perm
from app.services import visibility as vis
from app.services.auth import now

LICENSES = {"instructor_owned", "partner_permission", "other_written_permission"}
SCAN_LABEL = {
    "pending": "Di karantina, menunggu pemindaian",
    "clean": "Lolos pemindaian",
    "infected": "Terinfeksi (dihapus)",
    "error": "Pemindaian gagal",
    "not_scanned": "Belum dipindai (pemindai tidak aktif)",
}
CONSENT_LABEL = {
    "declared": "Dideklarasikan (belum diverifikasi)",
    "verified": "Izin terverifikasi",
    "rejected": "Ditolak",
    "revoked": "Dicabut",
}


def upload(db: Session, user: User, m: Movement, file: UploadFile, f: dict, rid) -> ReferenceMedia:
    if user.role not in perm.STUDIO_ROLES or not perm.can_see_partner(db, user, m.partner_id):
        raise ApiError(403, "FORBIDDEN", "Anda tidak berwenang mengunggah media untuk gerakan ini.")
    if str(f.get("declaration_confirmed")).lower() not in {"true", "1", "on"}:
        raise ApiError(
            422,
            "DECLARATION_REQUIRED",
            "Unggah media memerlukan deklarasi bahwa Anda berhak/berizin menggunakan media ini.",
        )
    errs = {
        k: "wajib diisi"
        for k in ("title", "rights_holder", "source_description", "usage_scope")
        if not (f.get(k) or "").strip()
    }
    if f.get("license_type") not in LICENSES:
        errs["license_type"] = "tidak valid"
    retention = None
    if f.get("retention_until"):
        try:
            retention = date.fromisoformat(f["retention_until"])
        except ValueError:
            errs["retention_until"] = "format YYYY-MM-DD"
        else:
            if retention <= now().date():
                errs["retention_until"] = "harus tanggal mendatang"
    if errs:
        raise ApiError(
            422,
            "VALIDATION_ERROR",
            "Deklarasi media belum lengkap.",
            [{"field": k, "message": v} for k, v in errs.items()],
        )
    st = storage.save_upload(file, storage.MEDIA_TYPES, quarantine=scanner.enabled())
    row = ReferenceMedia(
        movement_id=m.id,
        uploader_user_id=user.id,
        kind="video" if st.mime.startswith("video/") else "image",
        title=f["title"].strip()[:200],
        original_filename=st.filename,
        storage_key=st.key,
        mime=st.mime,
        size_bytes=st.size,
        sha256=st.sha256,
        rights_holder=f["rights_holder"].strip()[:300],
        source_description=f["source_description"].strip()[:4000],
        license_type=f["license_type"],
        usage_scope=f["usage_scope"].strip()[:4000],
        declaration_confirmed=True,
        consent_status="declared",
        access_level="private",
        retention_until=retention,
        is_demo=False,
        scan_status=scanner.initial_status(),
    )
    db.add(row)
    db.flush()
    audit.record(
        db,
        actor=user,
        action="media.upload",
        entity_type="reference_media",
        entity_id=row.id,
        detail={"movement_id": str(m.id), "kind": row.kind, "sha256": st.sha256, "size": st.size},
        request_id=rid,
    )
    return row


def get(db: Session, media_id) -> ReferenceMedia:
    r = db.get(ReferenceMedia, perm.parse_id(media_id, "Media"))
    if not r:
        raise ApiError(404, "NOT_FOUND", "Media tidak ditemukan.")
    return r


def get_for_studio(db: Session, user: User, media_id) -> tuple[ReferenceMedia, Movement]:
    r = get(db, media_id)
    return r, perm.get_movement(db, user, r.movement_id)  # 404 lintas organisasi


def _cohort_entitled(db: Session, user: User, movement_id) -> bool:
    """Peserta AKTIF cohort (program approved/active/completed) yang kursusnya memuat pelajaran terbit bertaut gerakan ini."""
    from app.models import Lesson
    from app.services import access

    return bool(
        db.scalar(
            select(Lesson.id).where(
                Lesson.movement_id == movement_id,
                Lesson.status == "published",
                Lesson.deleted_at.is_(None),
                Lesson.course_id.in_(access.member_course_ids(user)),
            )
        )
    )


def can_read_file(db: Session, user: User | None, r: ReferenceMedia) -> bool:
    """Otorisasi berkas media. FAIL-CLOSED: karantina/terinfeksi/error dan izin ditolak/dicabut tertutup untuk SEMUA orang
    (termasuk staf) — pencabutan izin berlaku seketika. Media publik wajib `clean` + izin terverifikasi + gerakan tayang."""
    if r.retention_until and r.retention_until < now().date():
        return False
    m = db.get(Movement, r.movement_id)
    if not m or m.deleted_at:
        return False
    if r.scan_status in {"pending", "infected", "error"}:
        return False
    if r.consent_status in {"rejected", "revoked"}:
        return False
    if (
        r.access_level == "public"
        and r.consent_status == "verified"
        and r.scan_status == "clean"
        and db.scalar(select(Movement.id).where(Movement.id == m.id, vis.movement_ok()))
    ):
        return True
    if user is None:
        return False
    if r.access_level == "pilot_cohort" and r.consent_status == "verified" and r.scan_status == "clean":
        if _cohort_entitled(db, user, m.id):
            return True
    if perm.is_staff(user):
        return True
    role = perm.member_role(db, user, m.partner_id)
    if role == "manager":
        return True
    if not role:
        return False
    return r.access_level in {"reviewers", "pilot_cohort"} or r.uploader_user_id == user.id


def patch(db: Session, user: User, r: ReferenceMedia, m: Movement, body: sc.MediaPatch, rid) -> ReferenceMedia:
    ch = body.model_dump(exclude_unset=True)
    is_mgr = perm.is_staff(user) or perm.is_manager(db, user, m.partner_id)
    if "title" in ch and ch["title"] and (is_mgr or r.uploader_user_id == user.id):
        r.title = ch["title"]
    if "retention_until" in ch and (is_mgr or r.uploader_user_id == user.id):
        if ch["retention_until"] and ch["retention_until"] <= now().date():
            raise ApiError(422, "VALIDATION_ERROR", "Tanggal retensi harus di masa depan.")
        r.retention_until = ch["retention_until"]
    if "consent_status" in ch or "permission_evidence_ref" in ch or "access_level" in ch:
        if not is_mgr:
            raise ApiError(
                403,
                "FORBIDDEN",
                "Hanya manager mitra, kurator, atau admin yang dapat mengubah persetujuan/akses media.",
            )
    if "consent_status" in ch and ch["consent_status"]:
        if r.uploader_user_id == user.id and ch["consent_status"] == "verified":
            raise ApiError(403, "SELF_APPROVAL", "Izin media tidak dapat diverifikasi oleh pengunggahnya sendiri.")
        ev = (ch.get("permission_evidence_ref") or r.permission_evidence_ref or "").strip()
        if ch["consent_status"] == "verified" and not ev:
            raise ApiError(
                422, "EVIDENCE_REQUIRED", "Rujukan bukti izin (permission_evidence_ref) wajib untuk verifikasi."
            )
        r.consent_status, r.decided_by_user_id, r.decided_at = ch["consent_status"], user.id, now()
        r.permission_evidence_ref = ev or None
        if ch["consent_status"] != "verified":
            r.access_level = "private"
    elif "permission_evidence_ref" in ch:
        r.permission_evidence_ref = ch["permission_evidence_ref"]
    if "access_level" in ch and ch["access_level"]:
        if ch["access_level"] in {"public", "pilot_cohort"} and r.scan_status != "clean":
            raise ApiError(409, "NOT_SCANNED", "Media hanya dapat dibagikan setelah lolos pemindaian malware.")
        if ch["access_level"] in {"public", "pilot_cohort"} and r.consent_status != "verified":
            raise ApiError(409, "CONSENT_NOT_VERIFIED", "Media hanya dapat dibagikan setelah izin terverifikasi.")
        r.access_level = ch["access_level"]
    db.flush()
    audit.record(
        db,
        actor=user,
        action="media.update",
        entity_type="reference_media",
        entity_id=r.id,
        detail={"fields": sorted(ch), "consent": r.consent_status, "access": r.access_level},
        request_id=rid,
    )
    return r


def delete(db: Session, user: User, r: ReferenceMedia, m: Movement, rid) -> None:
    if not (perm.is_staff(user) or perm.is_manager(db, user, m.partner_id) or r.uploader_user_id == user.id):
        raise ApiError(403, "FORBIDDEN", "Tidak berwenang menghapus media ini.")
    key, mid = r.storage_key, r.id
    db.delete(r)
    db.flush()
    storage.remove(key)
    audit.record(
        db,
        actor=user,
        action="media.delete",
        entity_type="reference_media",
        entity_id=mid,
        detail={"movement_id": str(m.id)},
        request_id=rid,
    )


def out(db: Session, user: User, r: ReferenceMedia, m: Movement) -> dict:
    up = db.get(User, r.uploader_user_id) if r.uploader_user_id else None
    is_mgr = perm.is_staff(user) or perm.is_manager(db, user, m.partner_id)
    return {
        "id": r.id,
        "kind": r.kind,
        "title": r.title,
        "filename": r.original_filename,
        "mime": r.mime,
        "size_bytes": r.size_bytes,
        "sha256": r.sha256,
        "rights_holder": r.rights_holder,
        "source_description": r.source_description,
        "license_type": r.license_type,
        "usage_scope": r.usage_scope,
        "consent_status": r.consent_status,
        "consent_label": CONSENT_LABEL[r.consent_status],
        "permission_evidence_ref": r.permission_evidence_ref,
        "access_level": r.access_level,
        "retention_until": r.retention_until,
        "uploader": up.display_name if up else None,
        "scan_status": r.scan_status,
        "scan_label": SCAN_LABEL[r.scan_status],
        "is_demo": r.is_demo,
        "created_at": r.created_at,
        "url": f"/api/v1/media/{r.id}/file",
        "can_decide": is_mgr and r.uploader_user_id != user.id,
        "can_delete": is_mgr or r.uploader_user_id == user.id,
    }


def list_for(db: Session, user: User, m: Movement) -> list[dict]:
    rows = db.scalars(
        select(ReferenceMedia).where(ReferenceMedia.movement_id == m.id).order_by(ReferenceMedia.created_at.desc())
    )
    return [
        out(db, user, r, m) for r in rows if can_read_file(db, user, r) or perm.can_see_partner(db, user, m.partner_id)
    ]


def purge_expired(db: Session, *, dry_run: bool = False, actor=None) -> int | dict:
    """Hapus media yang melewati `retention_until` (berkas + baris). Aman karena:
    - hanya yang retensinya BENAR-BENAR habis (tanggal diisi pemilik, tidak ditebak);
    - tidak pernah menghapus berkas yatim/tanpa referensi (itu hanya DILAPORKAN: `orphan_report`);
    - dry_run melaporkan jumlah+rincian tanpa menghapus; eksekusi dicatat di audit (jumlah saja).
    Mengembalikan jumlah (eksekusi) atau laporan (dry_run) — kompatibel dengan pemanggil lama."""
    from app.core.config import get_settings

    today = now().date()
    rows = list(db.scalars(select(ReferenceMedia).where(ReferenceMedia.retention_until < today)))
    if dry_run:
        by_access: dict[str, int] = {}
        for r in rows:
            by_access[r.access_level] = by_access.get(r.access_level, 0) + 1
        return {"dry_run": True, "eligible": len(rows), "by_access_level": by_access, "bytes": sum(r.size_bytes for r in rows)}
    if not get_settings().media_purge_enabled:
        return 0
    n = 0
    for r in rows:
        storage.remove(r.storage_key)
        db.delete(r)
        n += 1
    if n:
        audit.record(db, actor=actor, action="media.purge_expired", entity_type="reference_media", entity_id=None,
                     detail={"deleted": n}, request_id=None)
    return n


def orphan_report(db: Session) -> dict:
    """Berkas di penyimpanan tanpa baris DB (dan sebaliknya). HANYA melaporkan — tidak pernah menghapus otomatis."""
    from pathlib import Path

    from app.core.config import get_settings
    root = Path(get_settings().media_dir)
    known = {k for (k,) in db.execute(select(ReferenceMedia.storage_key))}
    from app.models import PartnerDocument
    known |= {k for (k,) in db.execute(select(PartnerDocument.storage_key))}
    files = [p for p in root.glob("*/*") if p.is_file() and not p.name.endswith(".part")] if root.exists() else []
    qfiles = [p for p in (root / ".quarantine").glob("*") if p.is_file()] if (root / ".quarantine").exists() else []
    orphans = [p.name for p in files + qfiles if p.name not in known and p.parent.name != ".quarantine" or (p.parent.name == ".quarantine" and p.name not in known)]
    missing = [k for k in known if not (root / k[:2] / k).exists() and not (root / ".quarantine" / k).exists()]
    return {"files": len(files) + len(qfiles), "orphan_files": len(orphans), "rows_without_file": len(missing)}


# ---------- anotasi referensi instruktur ----------
def _ann_out(db, a: MovementAnnotation) -> dict:
    who = db.get(User, a.annotator_user_id) if a.annotator_user_id else None
    rv = db.get(User, a.reviewed_by_user_id) if a.reviewed_by_user_id else None
    return {
        "id": a.id,
        "movement_id": a.movement_id,
        "media_id": a.media_id,
        "fixture_key": a.fixture_key,
        "phase_id": a.phase_id,
        "kind": a.kind,
        "timestamp_ms": a.timestamp_ms,
        "label": a.label,
        "note": a.note,
        "annotator": who.display_name if who else None,
        "annotator_user_id": a.annotator_user_id,
        "model_version": a.model_version,
        "source_note": a.source_note,
        "review_status": a.review_status,
        "reviewed_by": rv.display_name if rv else None,
        "reviewed_at": a.reviewed_at,
        "created_at": a.created_at,
        "provenance_label": "Instructor reference annotation — bukan ground truth dan bukan label akurasi",
    }


def list_annotations(db: Session, m: Movement, media_id=None, fixture_key=None) -> list[dict]:
    stmt = select(MovementAnnotation).where(MovementAnnotation.movement_id == m.id)
    if media_id:
        stmt = stmt.where(MovementAnnotation.media_id == perm.parse_id(media_id, "Media"))
    if fixture_key:
        stmt = stmt.where(MovementAnnotation.fixture_key == fixture_key)
    return [_ann_out(db, a) for a in db.scalars(stmt.order_by(MovementAnnotation.timestamp_ms))]


def _check_phase(db, m, phase_id):
    if phase_id and not db.scalar(
        select(MovementPhase.id)
        .join(MovementDocument, MovementDocument.id == MovementPhase.document_id)
        .where(MovementPhase.id == phase_id, MovementDocument.movement_id == m.id)
    ):
        raise ApiError(422, "INVALID_REFERENCE", "Fase tidak termasuk gerakan ini.")


def create_annotation(db: Session, user: User, m: Movement, body: sc.AnnotationIn, rid) -> dict:
    if user.role not in perm.STUDIO_ROLES:
        raise ApiError(403, "FORBIDDEN", "Tidak berwenang membuat anotasi.")
    if (body.media_id is None) == (body.fixture_key is None):
        raise ApiError(422, "VALIDATION_ERROR", "Isi tepat salah satu: media_id atau fixture_key.")
    if body.media_id:
        r = db.get(ReferenceMedia, body.media_id)
        if not r or r.movement_id != m.id or not can_read_file(db, user, r) or r.kind != "video":
            raise ApiError(422, "INVALID_REFERENCE", "Media video tidak ditemukan atau tidak dapat diakses.")
        if r.consent_status in {"rejected", "revoked"}:
            raise ApiError(409, "CONSENT_NOT_VALID", "Izin media ditolak/dicabut; anotasi tidak dapat dibuat.")
    _check_phase(db, m, body.phase_id)
    a = MovementAnnotation(movement_id=m.id, annotator_user_id=user.id, **body.model_dump())
    db.add(a)
    db.flush()
    audit.record(
        db,
        actor=user,
        action="annotation.create",
        entity_type="movement_annotation",
        entity_id=a.id,
        detail={"movement_id": str(m.id), "ts": a.timestamp_ms, "model_version": a.model_version},
        request_id=rid,
    )
    return _ann_out(db, a)


def get_annotation(db: Session, user: User, ann_id) -> tuple[MovementAnnotation, Movement]:
    a = db.get(MovementAnnotation, perm.parse_id(ann_id, "Anotasi"))
    if not a:
        raise ApiError(404, "NOT_FOUND", "Anotasi tidak ditemukan.")
    return a, perm.get_movement(db, user, a.movement_id)


def patch_annotation(
    db: Session, user: User, a: MovementAnnotation, m: Movement, body: sc.AnnotationPatch, rid
) -> dict:
    ch = body.model_dump(exclude_unset=True)
    review = ch.pop("review_status", None)
    if ch:
        if not (a.annotator_user_id == user.id or perm.is_staff(user)):
            raise ApiError(403, "FORBIDDEN", "Hanya pembuat anotasi atau kurator/admin yang dapat mengubahnya.")
        if "phase_id" in ch:
            _check_phase(db, m, ch["phase_id"])
        for k, v in ch.items():
            setattr(a, k, v)
        a.review_status, a.reviewed_by_user_id, a.reviewed_at = "pending", None, None
    if review:
        if not (perm.is_staff(user) or perm.is_manager(db, user, m.partner_id)) or a.annotator_user_id == user.id:
            raise ApiError(403, "SELF_APPROVAL", "Anotasi ditinjau oleh manager/kurator/admin selain pembuatnya.")
        a.review_status = review
        a.reviewed_by_user_id, a.reviewed_at = (user.id, now()) if review != "pending" else (None, None)
    db.flush()
    audit.record(
        db,
        actor=user,
        action="annotation.update",
        entity_type="movement_annotation",
        entity_id=a.id,
        detail={"fields": sorted(ch), "review": review},
        request_id=rid,
    )
    return _ann_out(db, a)


def delete_annotation(db: Session, user: User, a: MovementAnnotation, m: Movement, rid) -> None:
    if not (a.annotator_user_id == user.id or perm.is_staff(user) or perm.is_manager(db, user, m.partner_id)):
        raise ApiError(403, "FORBIDDEN", "Tidak berwenang menghapus anotasi ini.")
    aid = a.id
    db.delete(a)
    db.flush()
    audit.record(
        db,
        actor=user,
        action="annotation.delete",
        entity_type="movement_annotation",
        entity_id=aid,
        detail={"movement_id": str(m.id)},
        request_id=rid,
    )
