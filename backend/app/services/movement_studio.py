"""Movement Documentation Studio: dokumentasi gerakan berversi + alur review + publikasi.

Semua isi (sejarah/filosofi/teknik/deskripsi) ditulis instruktur; sistem tidak mengisinya.
Versi published/archived/pending/verified immutable (trigger DB) — perubahan = versi baru + changelog + review ulang.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import (
    AuditLog,
    Course,
    CulturalTradition,
    Lesson,
    Movement,
    MovementAnnotation,
    MovementDocument,
    MovementPhase,
    Partner,
    ReferenceMedia,
    TraditionPartner,
    User,
)
from app.schemas import studio as sc
from app.services import audit
from app.services import studio_perm as perm
from app.services import visibility as vis
from app.services.auth import now
from app.services.manage import map_integrity, slugify

EDITABLE = {"draft", "needs_revision", "rejected"}
OPEN = {"draft", "needs_revision", "pending_review", "verified"}
CONTENT_FIELDS = (
    "name_id",
    "name_local",
    "level",
    "safety_category",
    "prerequisites",
    "learning_context",
    "description",
    "terminology_notes",
    "common_mistakes",
    "safety_guidance",
    "relevant_body_parts",
    "relevant_landmarks",
    "source_citation",
    "source_url",
    "author_declaration",
    "rights_holder",
    "license_type",
    "usage_scope",
    "changelog",
)
LIST_FIELDS = {"common_mistakes", "relevant_body_parts", "relevant_landmarks"}
_REVIEW = {"pending_review"}
SOURCES = {
    "submit": EDITABLE,
    "curator_review": _REVIEW,
    "confirm_partner": _REVIEW,
    "request_revision": _REVIEW,
    "reject": _REVIEW,
    "approve": _REVIEW,
    "publish": {"verified"},
    "archive": EDITABLE | {"verified", "published"},
}
SELF_BLOCKED = {"curator_review", "confirm_partner", "request_revision", "reject", "approve", "publish"}
PRACTICE_MODE = {"solo_beginner": "solo_beginner", "supervised_practice": "supervised_only"}
SAFETY_LABEL = {
    "solo_beginner": "Solo pemula",
    "supervised_practice": "Latihan terawasi",
    "contact_practice": "Latihan kontak",
    "weapon_related": "Terkait senjata",
    "restricted": "Terbatas",
}
STATUS_LABEL = {
    "draft": "Draf",
    "pending_review": "Menunggu tinjauan",
    "needs_revision": "Perlu revisi",
    "verified": "Terverifikasi",
    "published": "Terbit",
    "rejected": "Ditolak",
    "archived": "Diarsipkan",
}


# ---------- akses ----------
def get_doc(db: Session, user: User, doc_id) -> tuple[MovementDocument, Movement]:
    d = db.get(MovementDocument, perm.parse_id(doc_id, "Dokumentasi"))
    if not d or d.deleted_at:
        raise ApiError(404, "NOT_FOUND", "Dokumentasi tidak ditemukan.")
    m = perm.get_movement(db, user, d.movement_id)
    return d, m


def _name(db, uid) -> str | None:
    u = db.get(User, uid) if uid else None
    return u.display_name if u else None


def _flush(db):
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise map_integrity(exc) from exc


def _docs(db, m) -> list[MovementDocument]:
    return list(
        db.scalars(
            select(MovementDocument)
            .where(MovementDocument.movement_id == m.id, MovementDocument.deleted_at.is_(None))
            .order_by(MovementDocument.version_no.desc())
        )
    )


def _phases(db, d) -> list[MovementPhase]:
    return list(
        db.scalars(select(MovementPhase).where(MovementPhase.document_id == d.id).order_by(MovementPhase.order_index))
    )


# ---------- pembuatan ----------
def _apply(d: MovementDocument, changes: dict) -> None:
    for k, v in changes.items():
        if k not in CONTENT_FIELDS:
            continue
        if k in LIST_FIELDS:
            v = v or []
        if v is None and k in {"name_id"}:
            raise ApiError(422, "VALIDATION_ERROR", "Nama gerakan tidak boleh kosong.")
        if k == "author_declaration" and v is None:
            v = False
        setattr(d, k, v)


def create_movement(db: Session, user: User, body: sc.MovementCreate, rid) -> Movement:
    if user.role not in perm.STUDIO_ROLES:
        raise ApiError(
            403, "FORBIDDEN", "Hanya instruktur, kurator, atau admin yang dapat membuat dokumentasi gerakan."
        )
    partner = db.get(Partner, body.partner_id)
    if not partner or partner.deleted_at or not perm.can_see_partner(db, user, partner.id):
        raise ApiError(404, "NOT_FOUND", "Mitra tidak ditemukan.")
    trad = db.scalar(
        select(CulturalTradition).where(
            CulturalTradition.id == body.tradition_id, CulturalTradition.deleted_at.is_(None)
        )
    )
    if not trad:
        raise ApiError(422, "INVALID_REFERENCE", "Tradisi tidak ditemukan.")
    if not db.scalar(
        select(TraditionPartner.id).where(
            TraditionPartner.partner_id == partner.id, TraditionPartner.tradition_id == trad.id
        )
    ):
        raise ApiError(
            422,
            "TRADITION_NOT_IN_SCOPE",
            "Tradisi ini belum masuk cakupan mitra. Tambahkan di Partner Workspace terlebih dahulu.",
        )
    base = body.slug or slugify(body.name_id)
    slug, n = base, 1
    while db.scalar(select(Movement.id).where(Movement.tradition_id == trad.id, Movement.slug == slug)):
        n += 1
        slug = f"{base}-{n}"
    m = Movement(
        tradition_id=trad.id,
        partner_id=partner.id,
        slug=slug,
        name_id=body.name_id,
        created_by_user_id=user.id,
        status="draft",
        is_demo=False,
        practice_mode="not_for_practice",
    )
    db.add(m)
    _flush(db)
    d = MovementDocument(
        movement_id=m.id, version_no=1, name_id=body.name_id, created_by_user_id=user.id, status="draft", is_demo=False
    )
    _apply(d, body.model_dump(exclude_unset=True, exclude={"tradition_id", "partner_id", "slug"}))
    db.add(d)
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="movement.create",
        entity_type="movement",
        entity_id=m.id,
        detail={"name": m.name_id, "document_id": str(d.id)},
        request_id=rid,
    )
    return m


def update_document(db: Session, user: User, d: MovementDocument, m: Movement, body: sc.DocumentPatch, rid):
    if d.status not in EDITABLE:
        raise ApiError(
            409,
            "NOT_EDITABLE",
            "Versi ini tidak dapat diubah. Buat versi baru untuk merevisi konten yang sudah diajukan/terbit.",
        )
    changes = body.model_dump(exclude_unset=True)
    _apply(d, changes)
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="movement.document_update",
        entity_type="movement_document",
        entity_id=d.id,
        detail={"fields": sorted(changes), "version": d.version_no},
        request_id=rid,
    )
    return d


def put_phases(db: Session, user: User, d: MovementDocument, body: sc.PhasesPut, rid):
    if d.status not in EDITABLE:
        raise ApiError(409, "NOT_EDITABLE", "Fase hanya dapat diubah pada versi draf/revisi.")
    for i, p in enumerate(body.phases):
        if p.start_ms is not None and p.end_ms is not None and p.end_ms < p.start_ms:
            raise ApiError(422, "VALIDATION_ERROR", f"Fase {i + 1}: waktu akhir lebih awal dari waktu mulai.")
    for old in _phases(db, d):
        db.delete(old)
    db.flush()
    for i, p in enumerate(body.phases):
        db.add(MovementPhase(document_id=d.id, order_index=i, **p.model_dump()))
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="movement.phases_put",
        entity_type="movement_document",
        entity_id=d.id,
        detail={"count": len(body.phases), "version": d.version_no},
        request_id=rid,
    )
    return _phases(db, d)


def new_version(db: Session, user: User, m: Movement, rid) -> MovementDocument:
    if user.role not in perm.STUDIO_ROLES or not perm.can_see_partner(db, user, m.partner_id):
        raise ApiError(403, "FORBIDDEN", "Anda tidak berwenang membuat versi baru.")
    docs = _docs(db, m)
    if any(x.status in OPEN for x in docs):
        raise ApiError(
            409,
            "OPEN_VERSION_EXISTS",
            "Masih ada versi yang berjalan (draf/revisi/ditinjau/terverifikasi). Selesaikan lebih dulu.",
        )
    src = next((x for x in docs if x.status == "published"), docs[0] if docs else None)
    if not src:
        raise ApiError(409, "NO_SOURCE", "Tidak ada versi sumber.")
    nxt = (
        db.scalar(select(func.max(MovementDocument.version_no)).where(MovementDocument.movement_id == m.id)) or 0
    ) + 1
    d = MovementDocument(
        movement_id=m.id,
        version_no=nxt,
        status="draft",
        created_by_user_id=user.id,
        is_demo=src.is_demo,
        name_id=src.name_id,
    )
    _apply(d, {k: getattr(src, k) for k in CONTENT_FIELDS if k != "changelog"})
    d.is_demo = src.is_demo
    db.add(d)
    db.flush()
    for p in _phases(db, src):
        db.add(
            MovementPhase(
                document_id=d.id,
                order_index=p.order_index,
                name=p.name,
                instruction=p.instruction,
                body_focus=p.body_focus,
                safety_note=p.safety_note,
                start_ms=p.start_ms,
                end_ms=p.end_ms,
            )
        )
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="movement.new_version",
        entity_type="movement",
        entity_id=m.id,
        detail={"version": nxt, "from_version": src.version_no, "document_id": str(d.id)},
        request_id=rid,
    )
    return d


# ---------- kelengkapan ----------
def completeness(db: Session, d: MovementDocument, m: Movement) -> list[dict]:
    ph = _phases(db, d)
    solo = d.safety_category == "solo_beginner"
    linked = bool(
        db.scalar(
            select(TraditionPartner.id).where(
                TraditionPartner.partner_id == m.partner_id, TraditionPartner.tradition_id == m.tradition_id
            )
        )
    )

    def has(v):
        return bool((v or "").strip()) if isinstance(v, str) else bool(v)

    items = [
        ("name", "Nama gerakan", has(d.name_id)),
        ("scope", "Tradisi termasuk cakupan mitra", linked),
        ("level", "Tingkat (level)", has(d.level)),
        ("safety_category", "Kategori keselamatan", has(d.safety_category)),
        ("description", "Deskripsi gerakan (ditulis instruktur)", has(d.description)),
        ("phases", "Minimal satu fase berurutan", len(ph) >= 1),
        ("safety_guidance", "Arahan keselamatan", has(d.safety_guidance)),
        ("source", "Sumber / atribusi", has(d.source_citation)),
        ("author_declaration", "Deklarasi penulis (isi berasal dari instruktur)", bool(d.author_declaration)),
        (
            "rights",
            "Pemegang hak, jenis izin, dan ruang lingkup penggunaan",
            has(d.rights_holder) and has(d.license_type) and has(d.usage_scope),
        ),
    ]
    if solo:
        items += [
            ("prerequisites", "Prasyarat (wajib untuk solo pemula)", has(d.prerequisites)),
            ("learning_context", "Konteks belajar (wajib untuk solo pemula)", has(d.learning_context)),
        ]
    if d.version_no > 1:
        items.append(("changelog", "Catatan perubahan (changelog) dari versi sebelumnya", has(d.changelog)))
    return [{"key": k, "label": lbl, "ok": ok} for k, lbl, ok in items]


# ---------- alur kerja ----------
def allowed_actions(db: Session, user: User, d: MovementDocument, m: Movement) -> list[str]:
    st, out = d.status, []
    staff, role = perm.is_staff(user), perm.member_role(db, user, m.partner_id)
    author = d.created_by_user_id == user.id
    if st in EDITABLE and (staff or role):
        out.append("submit")
    if st == "pending_review":
        if staff and not author:
            if not d.curator_reviewed_at:
                out.append("curator_review")
            out += ["request_revision", "reject"]
            if d.is_demo or (d.curator_reviewed_at and d.partner_confirmed_at):
                out.append("approve")
        if role == "manager" and not author:
            if not d.partner_confirmed_at:
                out.append("confirm_partner")
            if not staff:
                out.append("request_revision")
    if st == "verified" and user.role == "admin" and not author:
        out.append("publish")
    if (staff and st in EDITABLE | {"verified", "published"}) or (role and st in EDITABLE):
        out.append("archive")
    return out


def _check_parents_publishable(db, m):
    def need(ok, what):
        if not ok:
            raise ApiError(409, "PARENT_NOT_PUBLISHED", f"{what} harus berstatus published terlebih dahulu.")

    need(
        bool(db.scalar(select(CulturalTradition.id).where(CulturalTradition.id == m.tradition_id, vis.tradition_ok()))),
        "Tradisi",
    )
    need(
        bool(db.scalar(select(Partner.id).where(Partner.id == m.partner_id, vis.partner_ok()))),
        "Mitra (terverifikasi + dicantumkan di direktori)",
    )


def _sync_published(m: Movement, d: MovementDocument, t) -> None:
    m.name_id, m.name_local, m.description, m.safety_notes = d.name_id, d.name_local, d.description, d.safety_guidance
    m.practice_mode = PRACTICE_MODE.get(d.safety_category or "", "not_for_practice")
    m.assessment_enabled = False
    m.level, m.safety_category = d.level, d.safety_category
    m.published_document_id, m.published_version_no = d.id, d.version_no
    m.is_demo, m.source_citation, m.source_url = d.is_demo, d.source_citation, d.source_url
    m.approved_by_user_id, m.approved_at, m.approval_evidence_ref = (
        d.approved_by_user_id,
        d.approved_at,
        d.approval_evidence_ref,
    )
    m.status, m.published_at, m.review_note = "published", t, d.review_note


def transition(db: Session, user: User, d: MovementDocument, m: Movement, body: sc.DocTransition, rid):
    action, st = body.action, d.status
    if action not in allowed_actions(db, user, d, m):
        if st not in SOURCES[action]:
            raise ApiError(
                409, "INVALID_TRANSITION", f"Aksi '{action}' tidak dapat dilakukan dari status '{STATUS_LABEL[st]}'."
            )
        if d.created_by_user_id == user.id and action in SELF_BLOCKED:
            raise ApiError(
                403,
                "SELF_APPROVAL",
                "Anda tidak dapat meninjau/menyetujui/menerbitkan dokumentasi yang Anda tulis sendiri.",
            )
        raise ApiError(403, "FORBIDDEN", "Aksi ini tidak tersedia untuk Anda atau sudah dilakukan.")
    t, note = now(), (body.note or "").strip() or None
    new = st
    if action == "submit":
        missing = [c["label"] for c in completeness(db, d, m) if not c["ok"]]
        if missing:
            raise ApiError(422, "INCOMPLETE", "Dokumentasi belum lengkap untuk diajukan.", {"missing": missing})
        new = "pending_review"
        d.curator_reviewed_by_user_id = d.curator_reviewed_at = None
        d.partner_confirmed_by_user_id = d.partner_confirmed_at = d.partner_confirmation_note = None
        d.review_note = None
    elif action == "curator_review":
        d.curator_reviewed_by_user_id, d.curator_reviewed_at = user.id, t
        d.review_note = note or d.review_note
    elif action == "confirm_partner":
        d.partner_confirmed_by_user_id, d.partner_confirmed_at, d.partner_confirmation_note = user.id, t, note
    elif action in {"request_revision", "reject"}:
        if not note:
            raise ApiError(422, "NOTE_REQUIRED", "Catatan wajib diisi (alasan penolakan / hal yang perlu direvisi).")
        new, d.review_note = ("needs_revision" if action == "request_revision" else "rejected"), note
    elif action == "approve":
        ev = (body.evidence_ref or d.approval_evidence_ref or "").strip()
        if not d.is_demo and not ev:
            raise ApiError(
                422, "EVIDENCE_REQUIRED", "Rujukan bukti persetujuan (evidence_ref) wajib untuk konten non-demo."
            )
        new, d.approval_evidence_ref = "verified", ev or None
        d.approved_by_user_id, d.approved_at, d.review_note = user.id, t, note or d.review_note
    elif action == "publish":
        _check_parents_publishable(db, m)
        for old in _docs(db, m):
            if old.status == "published" and old.id != d.id:
                old.status = "archived"
        db.flush()
        new, d.published_at = "published", t
    elif action == "archive":
        new = "archived"
    d.status = new
    _flush(db)
    if action == "publish":
        _sync_published(m, d, t)
    elif action == "archive" and m.published_document_id == d.id:
        m.status, m.published_document_id, m.published_version_no = "archived", None, None
        m.practice_mode, m.assessment_enabled, m.published_at = "not_for_practice", False, None
    _flush(db)
    audit.record(
        db,
        actor=user,
        action=f"movement.{action}",
        entity_type="movement_document",
        entity_id=d.id,
        detail={"from": st, "to": new, "note": note, "version": d.version_no, "movement_id": str(m.id)},
        request_id=rid,
    )
    return d


# ---------- tautan lesson ----------
def link_lesson(db: Session, user: User, m: Movement, lesson_id, present: bool, rid) -> Lesson:
    lesson = db.get(Lesson, perm.parse_id(lesson_id, "Pelajaran"))
    if not lesson or lesson.deleted_at:
        raise ApiError(404, "NOT_FOUND", "Pelajaran tidak ditemukan.")
    course = db.get(Course, lesson.course_id)
    if not perm.is_staff(user) and (lesson.created_by_user_id != user.id and course.created_by_user_id != user.id):
        raise ApiError(404, "NOT_FOUND", "Pelajaran tidak ditemukan.")
    if course.partner_id != m.partner_id or course.tradition_id != m.tradition_id:
        raise ApiError(422, "SCOPE_MISMATCH", "Pelajaran harus berada di kurikulum dengan mitra dan tradisi yang sama.")
    if lesson.status not in {"draft", "rejected", "needs_revision"}:
        raise ApiError(
            409,
            "NOT_EDITABLE",
            "Pelajaran yang sudah diajukan/terbit harus ditarik ke draf (unpublish) sebelum tautan gerakan diubah.",
        )
    if present:
        lesson.movement_id = m.id
    elif lesson.movement_id == m.id:
        lesson.movement_id = None
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="movement.lesson_link" if present else "movement.lesson_unlink",
        entity_type="movement",
        entity_id=m.id,
        detail={"lesson_id": str(lesson.id)},
        request_id=rid,
    )
    return lesson


def linked_lessons(db: Session, m: Movement) -> list[dict]:
    rows = db.execute(
        select(Lesson, Course)
        .join(Course, Course.id == Lesson.course_id)
        .where(Lesson.movement_id == m.id, Lesson.deleted_at.is_(None))
        .order_by(Course.title, Lesson.order_index)
    ).all()
    return [
        {
            "id": le.id,
            "title": le.title,
            "slug": le.slug,
            "status": le.status,
            "course_slug": c.slug,
            "course_title": c.title,
        }
        for le, c in rows
    ]


def linkable_lessons(db: Session, user: User, m: Movement) -> list[dict]:
    stmt = (
        select(Lesson, Course)
        .join(Course, Course.id == Lesson.course_id)
        .where(
            Course.partner_id == m.partner_id,
            Course.tradition_id == m.tradition_id,
            Lesson.deleted_at.is_(None),
            Course.deleted_at.is_(None),
            (Lesson.movement_id.is_(None)) | (Lesson.movement_id == m.id),
        )
    )
    if not perm.is_staff(user):
        stmt = stmt.where((Lesson.created_by_user_id == user.id) | (Course.created_by_user_id == user.id))
    return [
        {"id": le.id, "title": le.title, "course_title": c.title, "status": le.status, "linked": le.movement_id == m.id}
        for le, c in db.execute(stmt.order_by(Course.title, Lesson.order_index))
    ]


# ---------- serialisasi studio ----------
def doc_out(db: Session, user: User, d: MovementDocument, m: Movement) -> dict:
    comp = completeness(db, d, m)
    base = {
        k: getattr(d, k)
        for k in (
            "id",
            "version_no",
            "status",
            "is_demo",
            "review_note",
            "created_at",
            "updated_at",
            "published_at",
            "approved_at",
            "approval_evidence_ref",
            "partner_confirmation_note",
            "curator_reviewed_at",
            "partner_confirmed_at",
            "legacy_import",
            *CONTENT_FIELDS,
        )
    }
    return {
        **base,
        "status_label": STATUS_LABEL[d.status],
        "phases": [
            {
                "id": p.id,
                "order_index": p.order_index,
                "name": p.name,
                "instruction": p.instruction,
                "body_focus": p.body_focus,
                "safety_note": p.safety_note,
                "start_ms": p.start_ms,
                "end_ms": p.end_ms,
            }
            for p in _phases(db, d)
        ],
        "author": _name(db, d.created_by_user_id),
        "approved_by": _name(db, d.approved_by_user_id),
        "curator_reviewed_by": _name(db, d.curator_reviewed_by_user_id),
        "partner_confirmed_by": _name(db, d.partner_confirmed_by_user_id),
        "completeness": comp,
        "complete": all(c["ok"] for c in comp),
        "editable": d.status in EDITABLE and bool(perm.is_staff(user) or perm.member_role(db, user, m.partner_id)),
        "allowed_actions": allowed_actions(db, user, d, m),
        "is_author": d.created_by_user_id == user.id,
    }


def _active_doc(docs: list[MovementDocument]) -> MovementDocument | None:
    return (
        next((x for x in docs if x.status in OPEN), None)
        or next((x for x in docs if x.status == "published"), None)
        or (docs[0] if docs else None)
    )


def summary_out(db: Session, user: User, m: Movement) -> dict:
    docs = _docs(db, m)
    a = _active_doc(docs)
    tr, pa = db.get(CulturalTradition, m.tradition_id), db.get(Partner, m.partner_id)
    return {
        "id": m.id,
        "slug": m.slug,
        "name_id": a.name_id if a else m.name_id,
        "name_local": a.name_local if a else m.name_local,
        "tradition_id": m.tradition_id,
        "tradition_name": tr.name if tr else None,
        "partner_id": m.partner_id,
        "partner_name": pa.name if pa else None,
        "level": a.level if a else None,
        "safety_category": a.safety_category if a else None,
        "is_demo": m.is_demo,
        "working_version": a.version_no if a else None,
        "working_status": a.status if a else None,
        "working_status_label": STATUS_LABEL[a.status] if a else None,
        "working_document_id": a.id if a else None,
        "published_version_no": m.published_version_no,
        "published": m.status == "published",
        "updated_at": a.updated_at if a else m.updated_at,
    }


def detail_out(db: Session, user: User, m: Movement) -> dict:
    docs = _docs(db, m)
    a = _active_doc(docs)
    return {
        **summary_out(db, user, m),
        "active_document": doc_out(db, user, a, m) if a else None,
        "versions": [
            {
                "id": x.id,
                "version_no": x.version_no,
                "status": x.status,
                "status_label": STATUS_LABEL[x.status],
                "changelog": x.changelog,
                "author": _name(db, x.created_by_user_id),
                "published_at": x.published_at,
                "created_at": x.created_at,
                "is_current": x.id == m.published_document_id,
            }
            for x in docs
        ],
        "lessons": linked_lessons(db, m),
        "can_create_version": bool(docs)
        and not any(x.status in OPEN for x in docs)
        and bool(perm.is_staff(user) or perm.member_role(db, user, m.partner_id)),
        "media_count": db.scalar(
            select(func.count()).select_from(ReferenceMedia).where(ReferenceMedia.movement_id == m.id)
        )
        or 0,
        "annotation_count": db.scalar(
            select(func.count()).select_from(MovementAnnotation).where(MovementAnnotation.movement_id == m.id)
        )
        or 0,
        "practice_eligible": bool(m.status == "published" and m.practice_mode == "solo_beginner"),
    }


def list_movements(
    db: Session,
    user: User,
    page: int,
    size: int,
    *,
    q=None,
    status=None,
    tradition_id=None,
    partner_id=None,
    safety_category=None,
    level=None,
) -> dict:
    from app.services.queries import paginate, search_cond

    M, D = Movement, MovementDocument
    stmt = select(M).where(M.deleted_at.is_(None))
    if not perm.is_staff(user):
        stmt = stmt.where(M.partner_id.in_(perm.my_partner_ids(db, user)))
    if (c := search_cond(q, M.name_id, M.name_local)) is not None:
        stmt = stmt.where(c)
    if tradition_id:
        stmt = stmt.where(M.tradition_id == tradition_id)
    if partner_id:
        stmt = stmt.where(M.partner_id == partner_id)
    if status or safety_category or level:
        sub = select(D.movement_id).where(D.deleted_at.is_(None))
        if status:
            sub = sub.where(D.status == status)
        if safety_category:
            sub = sub.where(D.safety_category == safety_category)
        if level:
            sub = sub.where(D.level == level)
        stmt = stmt.where(M.id.in_(sub))
    return paginate(db, stmt.order_by(M.updated_at.desc()), page, size, lambda x: summary_out(db, user, x))


def history(db: Session, m: Movement) -> list[dict]:
    ids = [str(m.id)] + [
        str(x) for x in db.scalars(select(MovementDocument.id).where(MovementDocument.movement_id == m.id))
    ]
    rows = db.execute(
        select(AuditLog, User.display_name)
        .outerjoin(User, User.id == AuditLog.actor_user_id)
        .where(AuditLog.entity_id.in_(ids), AuditLog.entity_type.in_(["movement", "movement_document"]))
        .order_by(AuditLog.created_at.desc())
        .limit(200)
    ).all()
    return [{"action": r.action, "actor": n, "detail": r.detail, "created_at": r.created_at} for r, n in rows]


# ---------- dashboard ----------
def dashboard(db: Session, user: User) -> dict:
    from app.services import partner_studio as ps

    staff = perm.is_staff(user)
    pids = perm.my_partner_ids(db, user)
    pstmt = select(Partner).where(Partner.deleted_at.is_(None))
    if not staff:
        pstmt = pstmt.where(Partner.id.in_(pids))
    partners = list(db.scalars(pstmt.order_by(Partner.name)))
    mstmt = select(Movement).where(Movement.deleted_at.is_(None))
    if not staff:
        mstmt = mstmt.where(Movement.partner_id.in_(pids))
    movements = list(db.scalars(mstmt))
    mids = [m.id for m in movements]
    docs = (
        list(
            db.scalars(
                select(MovementDocument).where(
                    MovementDocument.movement_id.in_(mids), MovementDocument.deleted_at.is_(None)
                )
            )
        )
        if mids
        else []
    )
    by_m = {m.id: m for m in movements}
    attention: list[dict] = []
    for d in docs:
        m = by_m[d.movement_id]
        acts = allowed_actions(db, user, d, m)
        base = {
            "movement_id": m.id,
            "document_id": d.id,
            "title": d.name_id,
            "version_no": d.version_no,
            "since": d.updated_at,
        }
        if d.status == "needs_revision" and (
            d.created_by_user_id == user.id or perm.member_role(db, user, m.partner_id)
        ):
            attention.append({**base, "kind": "needs_revision", "label": "Perlu revisi", "note": d.review_note})
        if any(a in acts for a in ("curator_review", "approve", "reject")):
            attention.append({**base, "kind": "awaiting_review", "label": "Menunggu tinjauan Anda", "note": None})
        elif "confirm_partner" in acts:
            attention.append(
                {**base, "kind": "awaiting_confirmation", "label": "Menunggu konfirmasi mitra Anda", "note": None}
            )
        if "publish" in acts:
            attention.append({**base, "kind": "ready_to_publish", "label": "Siap diterbitkan", "note": None})
    if user.role == "admin":
        for p in partners:
            if p.verification_status == "pending_verification":
                attention.append(
                    {
                        "kind": "partner_pending",
                        "label": "Mitra menunggu verifikasi",
                        "partner_id": p.id,
                        "title": p.name,
                        "since": p.submitted_at or p.updated_at,
                        "note": None,
                    }
                )
    status_counts: dict[str, int] = {}
    for d in docs:
        status_counts[d.status] = status_counts.get(d.status, 0) + 1
    cover: dict = {}
    for m in movements:
        c = cover.setdefault(m.tradition_id, {"tradition_id": m.tradition_id, "total": 0, "published": 0})
        c["total"] += 1
        c["published"] += 1 if m.status == "published" else 0
    names = (
        {t.id: t.name for t in db.scalars(select(CulturalTradition).where(CulturalTradition.id.in_(list(cover))))}
        if cover
        else {}
    )
    for c in cover.values():
        c["tradition_name"] = names.get(c["tradition_id"])
    media_pending = (
        db.scalar(
            select(func.count())
            .select_from(ReferenceMedia)
            .where(ReferenceMedia.movement_id.in_(mids), ReferenceMedia.consent_status == "declared")
        )
        if mids
        else 0
    )
    lessons_linked = (
        db.scalar(
            select(func.count()).select_from(Lesson).where(Lesson.movement_id.in_(mids), Lesson.deleted_at.is_(None))
        )
        if mids
        else 0
    )
    scope_ids = [str(x) for x in [*mids, *[d.id for d in docs], *[p.id for p in partners]]]
    act_rows = (
        db.execute(
            select(AuditLog, User.display_name)
            .outerjoin(User, User.id == AuditLog.actor_user_id)
            .where(
                AuditLog.entity_id.in_(scope_ids),
                AuditLog.entity_type.in_(["movement", "movement_document", "partner"]),
            )
            .order_by(AuditLog.created_at.desc())
            .limit(15)
        ).all()
        if scope_ids
        else []
    )
    return {
        "role": user.role,
        "partners": [ps.summary(db, user, p) for p in partners],
        "attention": sorted(attention, key=lambda x: x["since"] or now(), reverse=True),
        "counts": {
            "movements": len(movements),
            "documents_by_status": status_counts,
            "published_movements": sum(1 for m in movements if m.status == "published"),
            "media_awaiting_consent": media_pending or 0,
            "lessons_linked": lessons_linked or 0,
        },
        "tradition_coverage": sorted(cover.values(), key=lambda c: c["tradition_name"] or ""),
        "recent_activity": [
            {
                "action": r.action,
                "actor": n,
                "detail": r.detail,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "created_at": r.created_at,
            }
            for r, n in act_rows
        ],
    }


_ = uuid
