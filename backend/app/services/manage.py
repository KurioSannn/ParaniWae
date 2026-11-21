"""Manajemen konten: kind registry, permission, alur kerja (workflow), audit."""

import re
import unicodedata
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import (
    AuditLog,
    Course,
    CourseModule,
    CulturalTradition,
    Instructor,
    Lesson,
    Movement,
    Partner,
    User,
)
from app.schemas import manage as sc
from app.services import audit
from app.services.auth import now

STAFF = {"curator", "admin"}
EDITABLE = {"draft", "rejected"}


@dataclass(frozen=True)
class Kind:
    key: str
    label: str
    model: type
    create: type
    patch: type
    name_attr: str
    instructor_can_create: bool


KINDS: dict[str, Kind] = {
    k.key: k
    for k in [
        Kind("traditions", "Tradisi", CulturalTradition, sc.TraditionIn, sc.make_patch(sc.TraditionIn), "name", False),
        Kind("partners", "Perguruan", Partner, sc.PartnerIn, sc.make_patch(sc.PartnerIn), "name", False),
        Kind("instructors", "Instruktur", Instructor, sc.InstructorIn, sc.make_patch(sc.InstructorIn), "name", False),
        Kind("courses", "Kurikulum", Course, sc.CourseIn, sc.make_patch(sc.CourseIn), "title", True),
        Kind("lessons", "Pelajaran", Lesson, sc.LessonIn, sc.make_patch(sc.LessonIn), "title", True),
    ]
}


def get_kind(key: str) -> Kind:
    if key not in KINDS:
        raise ApiError(404, "NOT_FOUND", "Jenis konten tidak dikenal.")
    return KINDS[key]


# ---------- permission ----------
def can_use_kind(user: User, kind: Kind) -> bool:
    return user.role in STAFF or (user.role == "instructor" and kind.instructor_can_create)


def is_owner(user: User, obj) -> bool:
    return obj.created_by_user_id == user.id


def load(db: Session, kind: Kind, obj_id: uuid.UUID | str, user: User):
    """Muat objek untuk manajemen; 404 (bukan 403) bila bukan haknya agar tidak membocorkan."""
    try:
        oid = uuid.UUID(str(obj_id))
    except ValueError as exc:
        raise ApiError(404, "NOT_FOUND", "Konten tidak ditemukan.") from exc
    if not can_use_kind(user, kind):
        raise ApiError(403, "FORBIDDEN", "Anda tidak memiliki izin untuk jenis konten ini.")
    obj = db.scalar(select(kind.model).where(kind.model.id == oid, kind.model.deleted_at.is_(None)))
    if not obj or (user.role not in STAFF and not is_owner(user, obj)):
        raise ApiError(404, "NOT_FOUND", "Konten tidak ditemukan.")
    return obj


# ---------- util ----------
def slugify(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:100] or "item"


def unique_slug(db: Session, kind: Kind, base: str, scope: dict) -> str:
    slug, n = base, 1
    while db.scalar(
        select(kind.model.id).where(kind.model.slug == slug, *[getattr(kind.model, k) == v for k, v in scope.items()])
    ):
        n += 1
        slug = f"{base}-{n}"
    return slug


def _slug_scope(kind: Kind, data: dict) -> dict:
    if kind.key == "lessons":
        return {"course_id": data["course_id"]}
    return {}


def map_integrity(exc: IntegrityError) -> ApiError:
    sqlstate = getattr(exc.orig, "sqlstate", None)
    if sqlstate == "23505":
        return ApiError(409, "CONFLICT", "Data dengan nilai unik yang sama sudah ada.")
    if sqlstate == "23503":
        return ApiError(422, "INVALID_REFERENCE", "Referensi (tradisi/mitra/kursus/modul) tidak valid.")
    if sqlstate == "23514":
        return ApiError(
            422,
            "CONSTRAINT_VIOLATION",
            "Data melanggar aturan integritas konten.",
            {"constraint": getattr(getattr(exc.orig, "diag", None), "constraint_name", None)},
        )
    return ApiError(422, "INVALID_DATA", "Data tidak dapat disimpan.")


def serialize(obj) -> dict:
    return {c.key: getattr(obj, c.key) for c in obj.__mapper__.column_attrs}


def title_of(kind: Kind, obj) -> str:
    return getattr(obj, kind.name_attr)


# ---------- CRUD ----------
def _check_lesson_parent(db: Session, user: User, course_id, module_id=None) -> None:
    course = db.get(Course, course_id)
    if not course or course.deleted_at:
        raise ApiError(422, "INVALID_REFERENCE", "Kurikulum tidak ditemukan.")
    if user.role not in STAFF and not is_owner(user, course):
        raise ApiError(403, "FORBIDDEN", "Anda hanya dapat menambah pelajaran di kurikulum milik Anda.")


def create(db: Session, user: User, kind: Kind, body, rid: str | None):
    if not can_use_kind(user, kind):
        raise ApiError(403, "FORBIDDEN", "Anda tidak memiliki izin untuk membuat jenis konten ini.")
    data = body.model_dump()
    if kind.key == "lessons":
        _check_lesson_parent(db, user, data["course_id"])
    base = data.pop("slug", None) or slugify(data[kind.name_attr])
    data["slug"] = unique_slug(db, kind, base, _slug_scope(kind, data))
    obj = kind.model(**data, created_by_user_id=user.id, status="draft", is_demo=False)
    db.add(obj)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise map_integrity(exc) from exc
    audit.record(
        db,
        actor=user,
        action="content.create",
        entity_type=kind.key,
        entity_id=obj.id,
        detail={"title": title_of(kind, obj)},
        request_id=rid,
    )
    return obj


def update(db: Session, user: User, kind: Kind, obj, body, rid: str | None):
    if obj.status not in EDITABLE:
        raise ApiError(409, "NOT_EDITABLE", "Konten hanya dapat diedit saat berstatus draft atau ditolak.")
    changes = body.model_dump(exclude_unset=True)
    if kind.key == "lessons" and "course_id" in changes:
        _check_lesson_parent(db, user, changes["course_id"])
    for key, value in changes.items():
        col = getattr(kind.model, key).property.columns[0]
        if value is None and not col.nullable:
            raise ApiError(422, "VALIDATION_ERROR", f"Field {key} tidak boleh kosong.")
        setattr(obj, key, value)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise map_integrity(exc) from exc
    audit.record(
        db,
        actor=user,
        action="content.update",
        entity_type=kind.key,
        entity_id=obj.id,
        detail={"fields": sorted(changes)},
        request_id=rid,
    )
    return obj


def soft_delete(db: Session, user: User, kind: Kind, obj, rid: str | None) -> None:
    if obj.status not in EDITABLE | {"archived"}:
        raise ApiError(409, "NOT_DELETABLE", "Hanya konten draft/ditolak/diarsipkan yang dapat dihapus.")
    obj.deleted_at = now()
    audit.record(
        db,
        actor=user,
        action="content.delete",
        entity_type=kind.key,
        entity_id=obj.id,
        detail={"title": title_of(kind, obj)},
        request_id=rid,
    )


# ---------- workflow ----------
ACTIONS: dict[str, tuple[set[str], str]] = {
    "submit": ({"draft", "rejected"}, "pending_review"),
    "approve": ({"pending_review"}, "verified"),
    "reject": ({"pending_review"}, "rejected"),
    "publish": ({"verified"}, "published"),
    "unpublish": ({"published"}, "draft"),
    "archive": ({"draft", "rejected", "pending_review", "verified", "published"}, "archived"),
    "restore": ({"archived"}, "draft"),
}


def actor_may(user: User, action: str, obj) -> bool:
    if user.role in STAFF:
        return True
    return action == "submit" and user.role == "instructor" and is_owner(user, obj)


def allowed_actions(user: User, obj) -> list[str]:
    out = []
    for action, (sources, _) in ACTIONS.items():
        if obj.status in sources and actor_may(user, action, obj):
            if action == "approve" and is_owner(user, obj) and user.role != "admin":
                continue
            out.append(action)
    return out


def _published(db: Session, model, obj_id) -> bool:
    o = db.get(model, obj_id) if obj_id else None
    return bool(o and o.status == "published" and not o.deleted_at)


def _check_publish(db: Session, kind: Kind, obj) -> None:
    def need(ok: bool, what: str):
        if not ok:
            raise ApiError(409, "PARENT_NOT_PUBLISHED", f"{what} harus berstatus published terlebih dahulu.")

    k = kind.key
    if k == "traditions" and not obj.is_demo and obj.access_scope != "public":
        raise ApiError(409, "NOT_PUBLIC_SCOPE", "Hanya tradisi dengan access_scope=public yang dapat dipublikasikan.")
    if (
        k == "partners"
        and not obj.is_demo
        and not (obj.verification_status == "verified" and obj.public_listing_consent)
    ):
        raise ApiError(
            409,
            "PARTNER_NOT_VERIFIED",
            "Mitra harus terverifikasi dan menyetujui listing publik sebelum dipublikasikan.",
        )
    if k == "instructors":
        need(_published(db, Partner, obj.partner_id), "Mitra")
    if k == "courses":
        need(_published(db, CulturalTradition, obj.tradition_id), "Tradisi")
        if obj.distribution_scope == "pilot_private":
            # Kursus privat TIDAK mensyaratkan profil mitra tampil publik; cukup mitra terverifikasi (atau demo).
            partner = db.get(Partner, obj.partner_id)
            if not partner or partner.deleted_at or not (partner.is_demo or partner.verification_status == "verified"):
                raise ApiError(
                    409,
                    "PARTNER_NOT_VERIFIED",
                    "Kursus privat hanya dapat terbit untuk mitra yang sudah terverifikasi.",
                )
        else:
            need(_published(db, Partner, obj.partner_id), "Mitra")
            if obj.instructor_id:
                need(_published(db, Instructor, obj.instructor_id), "Instruktur")
    if k == "lessons":
        need(_published(db, Course, obj.course_id), "Kurikulum")
        if obj.movement_id:
            need(_published(db, Movement, obj.movement_id), "Gerakan")


def transition(db: Session, user: User, kind: Kind, obj, body: sc.TransitionIn, rid: str | None):
    action = body.action
    sources, target = ACTIONS[action]
    if not actor_may(user, action, obj):  # izin dicek lebih dulu agar respons konsisten
        raise ApiError(403, "FORBIDDEN", "Anda tidak memiliki izin untuk aksi ini.")
    if obj.status not in sources:
        raise ApiError(409, "INVALID_TRANSITION", f"Aksi '{action}' tidak dapat dilakukan dari status '{obj.status}'.")
    before = obj.status
    t = now()
    if action == "submit":
        if not (obj.source_citation or "").strip():
            raise ApiError(422, "SOURCE_REQUIRED", "Sumber/atribusi (source_citation) wajib diisi sebelum diajukan.")
    elif action == "approve":
        if is_owner(user, obj) and user.role != "admin":
            raise ApiError(403, "SELF_APPROVAL", "Anda tidak dapat menyetujui konten buatan sendiri.")
        evidence = body.approval_evidence_ref or obj.approval_evidence_ref
        if not obj.is_demo and not (evidence or "").strip():
            raise ApiError(
                422,
                "EVIDENCE_REQUIRED",
                "Rujukan bukti persetujuan (approval_evidence_ref) wajib untuk konten non-demo.",
            )
        obj.approval_evidence_ref = evidence
        obj.approved_by_user_id, obj.approved_at = user.id, t
    elif action == "reject":
        if not (body.note or "").strip():
            raise ApiError(422, "NOTE_REQUIRED", "Catatan penolakan wajib diisi.")
    elif action == "publish":
        _check_publish(db, kind, obj)
        obj.published_at = t
    elif action == "unpublish":
        obj.approved_by_user_id = obj.approved_at = obj.published_at = None
    obj.status = target
    if body.note is not None or action in {"reject", "approve", "publish"}:
        obj.review_note = body.note
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise map_integrity(exc) from exc
    audit.record(
        db,
        actor=user,
        action=f"content.{action}",
        entity_type=kind.key,
        entity_id=obj.id,
        detail={"from": before, "to": target, "note": body.note},
        request_id=rid,
    )
    return obj


def history(db: Session, kind: Kind, obj_id) -> list[dict]:
    rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.entity_type == kind.key, AuditLog.entity_id == str(obj_id))
        .order_by(AuditLog.created_at.desc())
        .limit(50)
    )
    names = {u.id: u.display_name for u in db.scalars(select(User))}  # kecil di MVP
    return [
        {"action": r.action, "actor": names.get(r.actor_user_id), "detail": r.detail, "created_at": r.created_at}
        for r in rows
    ]


# ---------- modul & materi ----------
def editable_module_parent(db: Session, user: User, course_id) -> Course:
    c = db.get(Course, course_id)
    if not c or c.deleted_at:
        raise ApiError(422, "INVALID_REFERENCE", "Kurikulum tidak ditemukan.")
    if not can_use_kind(user, KINDS["courses"]) or (user.role not in STAFF and not is_owner(user, c)):
        raise ApiError(403, "FORBIDDEN", "Anda tidak berwenang atas kurikulum ini.")
    if c.status not in EDITABLE:
        raise ApiError(409, "NOT_EDITABLE", "Kurikulum hanya dapat diedit saat draft/ditolak.")
    return c


def editable_lesson_parent(db: Session, user: User, lesson_id) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if not lesson or lesson.deleted_at:
        raise ApiError(422, "INVALID_REFERENCE", "Pelajaran tidak ditemukan.")
    if not can_use_kind(user, KINDS["lessons"]) or (user.role not in STAFF and not is_owner(user, lesson)):
        raise ApiError(403, "FORBIDDEN", "Anda tidak berwenang atas pelajaran ini.")
    if lesson.status not in EDITABLE:
        raise ApiError(409, "NOT_EDITABLE", "Pelajaran hanya dapat diedit saat draft/ditolak.")
    return lesson


def module_course(db: Session, module: CourseModule) -> Course:
    return db.get(Course, module.course_id)
