"""Pilot Program, Cohort, Undangan, Portal, Pengumuman, Consent, Survei, Catatan.

Memakai ulang enrollments/lesson_progress (services.progress) — tidak ada tabel enrollment baru.
Lihat docs/PILOT_STUDIO_CONTRACT.md.
"""

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.security import new_token, token_digest
from app.models import (
    CohortInvitation,
    CohortMember,
    CohortSession,
    Course,
    Enrollment,
    InstructorNote,
    Lesson,
    NotificationOutbox,
    Partner,
    PartnerMember,
    PilotAnnouncement,
    PilotCohort,
    PilotConsent,
    PilotProgram,
    PilotSurvey,
    SurveyResponse,
    User,
)
from app.schemas import pilot as sc
from app.services import access, audit, notify, progress
from app.services import studio_perm as perm
from app.services import visibility as vis
from app.services.auth import now

PROGRAM_LABEL = {
    "draft": "Draf",
    "pending_approval": "Menunggu persetujuan",
    "approved": "Disetujui",
    "active": "Berjalan",
    "completed": "Selesai",
    "cancelled": "Dibatalkan",
    "archived": "Diarsipkan",
}
EDITABLE = {"draft"}
JOINABLE = {"approved", "active"}
TRANSITIONS = {
    "submit": ({"draft"}, "pending_approval"),
    "approve": ({"pending_approval"}, "approved"),
    "reject": ({"pending_approval"}, "draft"),
    "activate": ({"approved"}, "active"),
    "complete": ({"active"}, "completed"),
    "cancel": ({"draft", "pending_approval", "approved", "active"}, "cancelled"),
    "archive": ({"completed", "cancelled"}, "archived"),
}
OFFICIAL_NOTE = "Program ini resmi hanya bila berstatus Disetujui/Berjalan dengan penyetuju tercatat."


def _map(exc: IntegrityError) -> ApiError:
    from app.services.manage import map_integrity

    return map_integrity(exc)


def _flush(db: Session):
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _map(exc) from exc


def _pilot_course_ok():
    """Kursus yang boleh dipakai cohort: kursus PUBLIK yang lolos aturan publik, ATAU kursus `pilot_private` yang sudah
    terbit (tidak bergantung pada publikasi profil mitra)."""
    return or_(vis.course_public_ok(), and_(vis._published(Course), Course.distribution_scope == access.PRIVATE))


# ---------- izin ----------
def partner_role(db: Session, user: User, partner_id) -> str | None:
    if user.role == "admin":
        return "admin"
    return perm.member_role(db, user, partner_id)  # manager | instructor | None


def get_program(db: Session, user: User, program_id, *, manage: bool = False) -> PilotProgram:
    p = db.get(PilotProgram, perm.parse_id(program_id, "Program"))
    if not p or not partner_role(db, user, p.partner_id):
        raise ApiError(404, "NOT_FOUND", "Program tidak ditemukan.")
    if manage and user.role not in perm.STUDIO_ROLES:
        raise ApiError(403, "FORBIDDEN", "Tidak berwenang.")
    return p


def can_run_cohort(db: Session, user: User, cohort: PilotCohort, program: PilotProgram) -> bool:
    role = partner_role(db, user, program.partner_id)
    return bool(
        role in {"admin", "manager"} or program.responsible_user_id == user.id or cohort.instructor_user_id == user.id
    )


def get_cohort(db: Session, user: User, cohort_id, *, run: bool = True) -> tuple[PilotCohort, PilotProgram]:
    c = db.get(PilotCohort, perm.parse_id(cohort_id, "Cohort"))
    p = db.get(PilotProgram, c.program_id) if c else None
    if not c or not p or not partner_role(db, user, p.partner_id) or (run and not can_run_cohort(db, user, c, p)):
        raise ApiError(404, "NOT_FOUND", "Cohort tidak ditemukan.")
    return c, p


def _active_member(db: Session, user_id, partner_id) -> bool:
    return bool(
        user_id
        and db.scalar(
            select(PartnerMember.id).where(
                PartnerMember.partner_id == partner_id,
                PartnerMember.user_id == user_id,
                PartnerMember.status == "active",
            )
        )
    )


# ---------- program ----------
def create_program(db: Session, user: User, body: sc.ProgramCreate, rid) -> PilotProgram:
    if user.role not in perm.STUDIO_ROLES:
        raise ApiError(403, "FORBIDDEN", "Hanya instruktur, kurator, atau admin yang dapat membuat program.")
    partner = db.get(Partner, body.partner_id)
    if not partner or partner.deleted_at or not partner_role(db, user, partner.id):
        raise ApiError(404, "NOT_FOUND", "Mitra tidak ditemukan.")
    _check_refs(db, partner, body.responsible_user_id, body.default_course_id)
    p = PilotProgram(**body.model_dump(), status="draft", is_demo=partner.is_demo, created_by_user_id=user.id)
    db.add(p)
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="pilot.program_create",
        entity_type="pilot_program",
        entity_id=p.id,
        detail={"name": p.name, "partner_verified": partner.verification_status == "verified"},
        request_id=rid,
    )
    return p


def _check_refs(db, partner: Partner, responsible, course_id):
    if responsible and not _active_member(db, responsible, partner.id):
        raise ApiError(422, "INVALID_REFERENCE", "Penanggung jawab harus anggota aktif mitra penyelenggara.")
    if course_id:
        c = db.scalar(select(Course).where(Course.id == course_id, _pilot_course_ok()))
        if not c or c.partner_id != partner.id:
            raise ApiError(422, "INVALID_REFERENCE", "Kurikulum harus terbit dan milik mitra penyelenggara.")


def update_program(db: Session, user: User, p: PilotProgram, body: sc.ProgramPatch, rid) -> PilotProgram:
    if p.status not in EDITABLE:
        raise ApiError(409, "NOT_EDITABLE", "Program hanya dapat diubah saat berstatus draf.")
    ch = body.model_dump(exclude_unset=True)
    partner = db.get(Partner, p.partner_id)
    _check_refs(db, partner, ch.get("responsible_user_id"), ch.get("default_course_id"))
    for k, v in ch.items():
        if v is None and k in {"name", "capacity"}:
            raise ApiError(422, "VALIDATION_ERROR", f"Field {k} tidak boleh kosong.")
        setattr(p, k, v)
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="pilot.program_update",
        entity_type="pilot_program",
        entity_id=p.id,
        detail={"fields": sorted(ch)},
        request_id=rid,
    )
    return p


def program_actions(db: Session, user: User, p: PilotProgram) -> list[str]:
    role = partner_role(db, user, p.partner_id)
    out = []
    for a, (src, _) in TRANSITIONS.items():
        if p.status not in src:
            continue
        if a in {"submit", "cancel"} and role:
            out.append(a)
        elif a in {"approve", "reject"} and user.role == "admin" and not _conflict(db, user, p):
            out.append(a)
        elif a in {"activate", "complete"} and role in {"admin", "manager"}:
            out.append(a)
        elif a == "archive" and role in {"admin", "manager"}:
            out.append(a)
    return out


def _conflict(db, user, p) -> bool:
    """Penyetuju tidak boleh penulis atau anggota mitra penyelenggara."""
    return p.created_by_user_id == user.id or bool(perm.member_role(db, user, p.partner_id))


def transition(db: Session, user: User, p: PilotProgram, body: sc.ProgramAction, rid) -> PilotProgram:
    a, st = body.action, p.status
    if a not in program_actions(db, user, p):
        if st not in TRANSITIONS[a][0]:
            raise ApiError(
                409, "INVALID_TRANSITION", f"Aksi '{a}' tidak dapat dilakukan dari status '{PROGRAM_LABEL[st]}'."
            )
        if a in {"approve", "reject"} and user.role == "admin" and _conflict(db, user, p):
            raise ApiError(
                403, "SELF_APPROVAL", "Penulis program atau anggota mitra tidak dapat menyetujui/menolak program ini."
            )
        raise ApiError(403, "FORBIDDEN", "Aksi ini tidak tersedia untuk Anda.")
    note = (body.note or "").strip() or None
    t = now()
    partner = db.get(Partner, p.partner_id)
    if a == "submit":
        if not (partner.is_demo or partner.verification_status == "verified"):
            raise ApiError(
                409,
                "PARTNER_NOT_VERIFIED",
                "Mitra belum terverifikasi: program hanya dapat berstatus draf atau program demo.",
            )
        missing = _submit_missing(db, p)
        if missing:
            raise ApiError(422, "INCOMPLETE", "Program belum lengkap untuk diajukan.", {"missing": missing})
    elif a == "approve":
        ev = (body.evidence_ref or "").strip()
        if not p.is_demo and not ev:
            raise ApiError(422, "EVIDENCE_REQUIRED", "Rujukan bukti persetujuan wajib untuk program non-demo.")
        p.approved_by_user_id, p.approved_at, p.approval_evidence_ref = user.id, t, ev or None
    elif a == "reject":
        if not note:
            raise ApiError(422, "NOTE_REQUIRED", "Catatan penolakan wajib diisi.")
    elif a == "complete":
        p.completed_at = t
        for c in db.scalars(select(PilotCohort).where(PilotCohort.program_id == p.id)):
            c.status = "completed"
    if note is not None or a == "reject":
        p.review_note = note
    p.status = TRANSITIONS[a][1]
    _flush(db)
    audit.record(
        db,
        actor=user,
        action=f"pilot.{a}",
        entity_type="pilot_program",
        entity_id=p.id,
        detail={"from": st, "to": p.status, "note": note},
        request_id=rid,
    )
    if a == "submit":
        base = get_settings().public_base_url.rstrip("/")
        for (email,) in db.execute(select(User.email).where(User.role == "admin", User.status == "active")):
            notify.enqueue(
                db,
                kind="program_approval",
                to_email=email,
                dedupe_key=f"program-submit:{p.id}:{t.isoformat()}:{email}",
                subject=f"[SILATARA] Program pilot menunggu persetujuan: {p.name}",
                body=f'Program "{p.name}" diajukan dan menunggu persetujuan.\n\nBuka: {base}/app/pilot/manage/{p.id}\n',
            )
    return p


def _submit_missing(db, p) -> list[str]:
    m = []
    if not (p.objective or "").strip():
        m.append("Tujuan program")
    if not (p.start_date and p.end_date):
        m.append("Periode (mulai & selesai)")
    if not p.responsible_user_id:
        m.append("Instruktur penanggung jawab")
    n = db.scalar(select(func.count()).select_from(PilotCohort).where(PilotCohort.program_id == p.id)) or 0
    if n < 1:
        m.append("Minimal satu cohort")
    return m


# ---------- cohort ----------
def _check_cohort_refs(db, partner: Partner, course_id, instructor_id):
    c = db.scalar(select(Course).where(Course.id == course_id, _pilot_course_ok())) if course_id else None
    if not c or c.partner_id != partner.id:
        raise ApiError(422, "INVALID_REFERENCE", "Kurikulum harus terbit dan milik mitra penyelenggara.")
    if instructor_id and not _active_member(db, instructor_id, partner.id):
        raise ApiError(422, "INVALID_REFERENCE", "Instruktur cohort harus anggota aktif mitra penyelenggara.")


def create_cohort(db: Session, user: User, p: PilotProgram, body: sc.CohortCreate, rid) -> PilotCohort:
    if p.status in {"completed", "cancelled", "archived"}:
        raise ApiError(409, "NOT_EDITABLE", "Program sudah berakhir.")
    partner = db.get(Partner, p.partner_id)
    _check_cohort_refs(db, partner, body.course_id, body.instructor_user_id)
    c = PilotCohort(program_id=p.id, **body.model_dump())
    db.add(c)
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="pilot.cohort_create",
        entity_type="pilot_cohort",
        entity_id=c.id,
        detail={"program_id": str(p.id)},
        request_id=rid,
    )
    return c


def update_cohort(db: Session, user: User, c: PilotCohort, p: PilotProgram, body: sc.CohortPatch, rid) -> PilotCohort:
    ch = body.model_dump(exclude_unset=True)
    members = _member_count(db, c.id)
    if "course_id" in ch and members:
        raise ApiError(409, "NOT_EDITABLE", "Kurikulum tidak dapat diganti setelah ada peserta.")
    if "capacity" in ch and ch["capacity"] is not None and ch["capacity"] < members:
        raise ApiError(409, "CAPACITY_BELOW_MEMBERS", "Kapasitas tidak boleh di bawah jumlah peserta aktif.")
    partner = db.get(Partner, p.partner_id)
    _check_cohort_refs(
        db, partner, ch.get("course_id", c.course_id), ch.get("instructor_user_id", c.instructor_user_id)
    )
    for k, v in ch.items():
        if v is None and k in {"name", "course_id", "capacity"}:
            raise ApiError(422, "VALIDATION_ERROR", f"Field {k} tidak boleh kosong.")
        setattr(c, k, v)
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="pilot.cohort_update",
        entity_type="pilot_cohort",
        entity_id=c.id,
        detail={"fields": sorted(ch)},
        request_id=rid,
    )
    return c


def set_cohort_status(db: Session, user: User, c: PilotCohort, p: PilotProgram, status: str, rid) -> PilotCohort:
    if status == "open" and p.status not in JOINABLE:
        raise ApiError(409, "PROGRAM_NOT_APPROVED", "Cohort baru dapat dibuka setelah program disetujui.")
    if c.status == "completed":
        raise ApiError(409, "INVALID_TRANSITION", "Cohort sudah selesai.")
    before, c.status = c.status, status
    audit.record(
        db,
        actor=user,
        action=f"pilot.cohort_{status}",
        entity_type="pilot_cohort",
        entity_id=c.id,
        detail={"from": before},
        request_id=rid,
    )
    return c


def put_sessions(db: Session, user: User, c: PilotCohort, body: sc.SessionsPut, rid) -> list[CohortSession]:
    for s in body.sessions:
        if s.ends_at and s.ends_at < s.starts_at:
            raise ApiError(422, "VALIDATION_ERROR", "Waktu selesai sesi lebih awal dari waktu mulai.")
    for old in db.scalars(select(CohortSession).where(CohortSession.cohort_id == c.id)):
        db.delete(old)
    db.flush()
    rows = [CohortSession(cohort_id=c.id, **s.model_dump()) for s in body.sessions]
    db.add_all(rows)
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="pilot.sessions_put",
        entity_type="pilot_cohort",
        entity_id=c.id,
        detail={"count": len(rows)},
        request_id=rid,
    )
    return rows


def _member_count(db, cohort_id) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(CohortMember)
            .where(CohortMember.cohort_id == cohort_id, CohortMember.status == "active")
        )
        or 0
    )


def remove_member(db: Session, user: User, c: PilotCohort, user_id, rid) -> None:
    uid = perm.parse_id(user_id, "Peserta")
    m = db.scalar(
        select(CohortMember).where(
            CohortMember.cohort_id == c.id, CohortMember.user_id == uid, CohortMember.status == "active"
        )
    )
    if not m:
        raise ApiError(404, "NOT_FOUND", "Peserta tidak ditemukan.")
    m.status = "removed"
    audit.record(
        db,
        actor=user,
        action="pilot.member_remove",
        entity_type="pilot_cohort",
        entity_id=c.id,
        detail={"user_id": str(uid)},
        request_id=rid,
    )


def leave(db: Session, user: User, cohort_id, rid) -> None:
    m = db.scalar(
        select(CohortMember).where(
            CohortMember.cohort_id == perm.parse_id(cohort_id, "Cohort"),
            CohortMember.user_id == user.id,
            CohortMember.status == "active",
        )
    )
    if not m:
        raise ApiError(404, "NOT_FOUND", "Anda tidak terdaftar di cohort ini.")
    m.status = "withdrawn"
    audit.record(
        db, actor=user, action="pilot.member_leave", entity_type="pilot_cohort", entity_id=m.cohort_id, request_id=rid
    )


# ---------- undangan ----------
def invite_status(inv: CohortInvitation) -> str:
    if inv.accepted_at:
        return "accepted"
    if inv.revoked_at:
        return "revoked"
    if inv.expires_at <= now():
        return "expired"
    return "pending"


def create_invitation(
    db: Session, user: User, c: PilotCohort, p: PilotProgram, body: sc.InviteCreate, rid
) -> tuple[CohortInvitation, str]:
    if p.status not in JOINABLE:
        raise ApiError(409, "PROGRAM_NOT_APPROVED", "Undangan hanya dapat dibuat untuk program yang sudah disetujui.")
    if c.status != "open":
        raise ApiError(409, "COHORT_NOT_OPEN", "Buka cohort terlebih dahulu sebelum mengundang.")
    raw = new_token()
    inv = CohortInvitation(
        cohort_id=c.id,
        email=(body.email or "").lower() or None,
        token_hash=token_digest(raw),
        expires_at=now() + timedelta(days=body.days),
        created_by_user_id=user.id,
    )
    db.add(inv)
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="pilot.invite_create",
        entity_type="pilot_cohort",
        entity_id=c.id,
        detail={"invitation_id": str(inv.id), "email_bound": bool(inv.email), "days": body.days},
        request_id=rid,
    )
    if inv.email:
        base = get_settings().public_base_url.rstrip("/")
        notify.enqueue(
            db,
            kind="cohort_invitation",
            to_email=inv.email,
            dedupe_key=f"invite:{inv.id}",
            subject=f"[SILATARA] Undangan program pilot: {p.name}",
            body=f'Anda diundang ke cohort "{c.name}" pada program "{p.name}".\n\nTerima undangan (berlaku hingga '
            f"{inv.expires_at:%d-%m-%Y}): {base}/undangan?token={raw}\n\nUndangan hanya dapat dipakai satu kali.\n",
        )
    return inv, raw


def revoke_invitation(db: Session, user: User, inv: CohortInvitation, rid) -> CohortInvitation:
    if inv.accepted_at:
        raise ApiError(409, "ALREADY_ACCEPTED", "Undangan sudah dipakai.")
    if not inv.revoked_at:
        inv.revoked_at, inv.revoked_by_user_id = now(), user.id
        audit.record(
            db,
            actor=user,
            action="pilot.invite_revoke",
            entity_type="pilot_cohort",
            entity_id=inv.cohort_id,
            detail={"invitation_id": str(inv.id)},
            request_id=rid,
        )
    return inv


def invitation_out(inv: CohortInvitation) -> dict:
    return {
        "id": inv.id,
        "email": inv.email,
        "status": invite_status(inv),
        "expires_at": inv.expires_at,
        "accepted_at": inv.accepted_at,
        "revoked_at": inv.revoked_at,
        "created_at": inv.created_at,
    }


def _by_token(db: Session, token: str, lock: bool = False) -> CohortInvitation:
    stmt = select(CohortInvitation).where(CohortInvitation.token_hash == token_digest(token))
    inv = db.scalar(stmt.with_for_update() if lock else stmt)
    if not inv:
        raise ApiError(404, "INVITATION_NOT_FOUND", "Undangan tidak ditemukan atau tidak valid.")
    return inv


def preview(db: Session, token: str) -> dict:
    inv = _by_token(db, token)
    c = db.get(PilotCohort, inv.cohort_id)
    p = db.get(PilotProgram, c.program_id)
    partner = db.get(Partner, p.partner_id)
    return {
        "status": invite_status(inv),
        "program_name": p.name,
        "cohort_name": c.name,
        "partner_name": partner.name,
        "is_demo": p.is_demo,
        "program_status": p.status,
        "program_status_label": PROGRAM_LABEL[p.status],
        "start_date": c.start_date,
        "end_date": c.end_date,
        "expires_at": inv.expires_at,
        "email_bound": bool(inv.email),
        "joinable": invite_status(inv) == "pending" and p.status in JOINABLE and c.status == "open",
    }


def accept(db: Session, user: User, body: sc.InviteAccept, rid) -> dict:
    if not body.operational_ack:
        raise ApiError(
            422, "ACK_REQUIRED", "Anda perlu menyetujui penggunaan data operasional program untuk bergabung."
        )
    if not user.email_verified_at:
        raise ApiError(403, "EMAIL_NOT_VERIFIED", "Verifikasi email Anda terlebih dahulu.")
    inv = _by_token(db, body.token, lock=True)
    st = invite_status(inv)
    if st != "pending":
        raise ApiError(
            410 if st in {"expired", "revoked"} else 409,
            f"INVITATION_{st.upper()}",
            {
                "accepted": "Undangan sudah dipakai.",
                "revoked": "Undangan telah dicabut.",
                "expired": "Undangan telah kedaluwarsa.",
            }[st],
        )
    if inv.email and inv.email.lower() != user.email.lower():
        raise ApiError(403, "INVITATION_EMAIL_MISMATCH", "Undangan ini ditujukan untuk alamat email lain.")
    c = db.get(PilotCohort, inv.cohort_id)
    p = db.get(PilotProgram, c.program_id)
    if p.status not in JOINABLE or c.status != "open":
        raise ApiError(409, "COHORT_CLOSED", "Cohort belum dibuka atau program belum aktif.")
    course = db.scalar(select(Course).where(Course.id == c.course_id, _pilot_course_ok()))
    if not course:
        raise ApiError(409, "COURSE_UNAVAILABLE", "Kurikulum cohort belum tersedia.")
    existing = db.scalar(
        select(CohortMember).where(
            CohortMember.program_id == p.id, CohortMember.user_id == user.id, CohortMember.status == "active"
        )
    )
    if existing:
        raise ApiError(409, "ALREADY_MEMBER", "Anda sudah terdaftar aktif pada program ini.")
    prog_total = (
        db.scalar(
            select(func.count())
            .select_from(CohortMember)
            .where(CohortMember.program_id == p.id, CohortMember.status == "active")
        )
        or 0
    )
    if _member_count(db, c.id) >= c.capacity or prog_total >= p.capacity:
        raise ApiError(409, "CAPACITY_FULL", "Kapasitas peserta sudah penuh.")
    enr = progress.enroll(db, user, course, rid)
    m = db.scalar(select(CohortMember).where(CohortMember.cohort_id == c.id, CohortMember.user_id == user.id))
    if m:
        m.status, m.joined_at, m.invitation_id, m.enrollment_id = "active", now(), inv.id, enr.id
    else:
        m = CohortMember(
            cohort_id=c.id,
            program_id=p.id,
            user_id=user.id,
            joined_at=now(),
            invitation_id=inv.id,
            enrollment_id=enr.id,
        )
        db.add(m)
    inv.accepted_by_user_id, inv.accepted_at = user.id, now()
    _flush(db)
    _set_consents(db, user, p, body.research_aggregate, body.publication_quote)
    audit.record(
        db,
        actor=user,
        action="pilot.invite_accept",
        entity_type="pilot_cohort",
        entity_id=c.id,
        detail={"invitation_id": str(inv.id), "research": body.research_aggregate, "quote": body.publication_quote},
        request_id=rid,
    )
    return {"cohort_id": c.id, "program_id": p.id}


# ---------- consent ----------
def _set_consents(db, user, p, research: bool | None, quote: bool | None):
    for scope, val in (("research_aggregate", research), ("publication_quote", quote)):
        if val is None:
            continue
        row = db.scalar(
            select(PilotConsent).where(
                PilotConsent.program_id == p.id, PilotConsent.user_id == user.id, PilotConsent.scope == scope
            )
        )
        if row:
            row.granted, row.decided_at, row.policy_version = val, now(), get_settings().pilot_policy_version
        else:
            db.add(
                PilotConsent(
                    program_id=p.id,
                    user_id=user.id,
                    scope=scope,
                    granted=val,
                    decided_at=now(),
                    policy_version=get_settings().pilot_policy_version,
                )
            )
    db.flush()


def consents_of(db, user_id, program_id) -> dict:
    rows = {
        r.scope: r
        for r in db.scalars(
            select(PilotConsent).where(PilotConsent.program_id == program_id, PilotConsent.user_id == user_id)
        )
    }
    return {s: bool(rows[s].granted) if s in rows else False for s in ("research_aggregate", "publication_quote")}


def put_consents(db: Session, user: User, program_id, body: sc.ConsentPut, rid) -> dict:
    p = db.get(PilotProgram, perm.parse_id(program_id, "Program"))
    if not p or not db.scalar(
        select(CohortMember.id).where(CohortMember.program_id == p.id, CohortMember.user_id == user.id)
    ):
        raise ApiError(404, "NOT_FOUND", "Program tidak ditemukan.")
    _set_consents(db, user, p, body.research_aggregate, body.publication_quote)
    audit.record(
        db,
        actor=user,
        action="pilot.consent_update",
        entity_type="pilot_program",
        entity_id=p.id,
        detail=body.model_dump(exclude_unset=True),
        request_id=rid,
    )
    return consents_of(db, user.id, p.id)


# ---------- pengumuman ----------
def announce(db: Session, user: User, p: PilotProgram, body: sc.AnnouncementIn, rid) -> PilotAnnouncement:
    cohort = None
    if body.cohort_id:
        cohort = db.get(PilotCohort, body.cohort_id)
        if not cohort or cohort.program_id != p.id:
            raise ApiError(422, "INVALID_REFERENCE", "Cohort bukan bagian dari program ini.")
        if not can_run_cohort(db, user, cohort, p):
            raise ApiError(403, "FORBIDDEN", "Anda bukan pengelola cohort ini.")
    elif partner_role(db, user, p.partner_id) not in {"admin", "manager"} and p.responsible_user_id != user.id:
        raise ApiError(403, "FORBIDDEN", "Pengumuman seluruh program hanya oleh penanggung jawab, manager, atau admin.")
    a = PilotAnnouncement(
        program_id=p.id, cohort_id=body.cohort_id, author_user_id=user.id, title=body.title, body=body.body
    )
    db.add(a)
    _flush(db)
    queued = 0
    if body.notify:
        stmt = (
            select(User.email)
            .join(CohortMember, CohortMember.user_id == User.id)
            .where(CohortMember.program_id == p.id, CohortMember.status == "active", User.status == "active")
        )
        if body.cohort_id:
            stmt = stmt.where(CohortMember.cohort_id == body.cohort_id)
        base = get_settings().public_base_url.rstrip("/")
        for (email,) in db.execute(stmt):
            queued += notify.enqueue(
                db,
                kind="announcement",
                to_email=email,
                dedupe_key=f"announce:{a.id}:{email}",
                subject=f"[SILATARA] Pengumuman: {a.title}",
                body=f"{a.body}\n\nProgram: {p.name}\nBuka portal: {base}/app/pilot\n",
            )
    audit.record(
        db,
        actor=user,
        action="pilot.announce",
        entity_type="pilot_program",
        entity_id=p.id,
        detail={"announcement_id": str(a.id), "queued": queued},
        request_id=rid,
    )
    return a


def announcements_out(db: Session, program_id, cohort_id=None) -> list[dict]:
    stmt = (
        select(PilotAnnouncement, User.display_name)
        .outerjoin(User, User.id == PilotAnnouncement.author_user_id)
        .where(PilotAnnouncement.program_id == program_id)
    )
    if cohort_id:
        stmt = stmt.where((PilotAnnouncement.cohort_id.is_(None)) | (PilotAnnouncement.cohort_id == cohort_id))
    return [
        {
            "id": a.id,
            "title": a.title,
            "body": a.body,
            "cohort_id": a.cohort_id,
            "author": n,
            "created_at": a.created_at,
        }
        for a, n in db.execute(stmt.order_by(PilotAnnouncement.created_at.desc()).limit(50))
    ]


def delivery_summary(db: Session, announcement_id) -> dict:
    rows = db.execute(
        select(NotificationOutbox.status, func.count())
        .where(NotificationOutbox.dedupe_key.like(f"announce:{announcement_id}:%"))
        .group_by(NotificationOutbox.status)
    ).all()
    return dict(rows)


# ---------- catatan instruktur ----------
def add_note(db: Session, user: User, c: PilotCohort, body: sc.NoteIn, rid) -> InstructorNote:
    if not db.scalar(
        select(CohortMember.id).where(CohortMember.cohort_id == c.id, CohortMember.user_id == body.participant_user_id)
    ):
        raise ApiError(422, "INVALID_REFERENCE", "Peserta bukan anggota cohort ini.")
    n = InstructorNote(
        cohort_id=c.id, participant_user_id=body.participant_user_id, author_user_id=user.id, note=body.note
    )
    db.add(n)
    _flush(db)
    audit.record(db, actor=user, action="pilot.note_add", entity_type="pilot_cohort", entity_id=c.id, request_id=rid)
    return n


def notes_out(db: Session, c: PilotCohort) -> list[dict]:
    rows = db.execute(
        select(InstructorNote, User.display_name)
        .join(User, User.id == InstructorNote.participant_user_id)
        .where(InstructorNote.cohort_id == c.id)
        .order_by(InstructorNote.created_at.desc())
        .limit(200)
    ).all()
    return [
        {
            "id": n.id,
            "participant_user_id": n.participant_user_id,
            "participant": name,
            "note": n.note,
            "created_at": n.created_at,
        }
        for n, name in rows
    ]


# ---------- serialisasi ----------
def program_out(db: Session, user: User, p: PilotProgram, detail: bool = False) -> dict:
    partner = db.get(Partner, p.partner_id)
    resp = db.get(User, p.responsible_user_id) if p.responsible_user_id else None
    base = {
        "id": p.id,
        "name": p.name,
        "partner_id": p.partner_id,
        "partner_name": partner.name if partner else None,
        "partner_verified": bool(partner and partner.verification_status == "verified"),
        "status": p.status,
        "status_label": PROGRAM_LABEL[p.status],
        "is_demo": p.is_demo,
        "start_date": p.start_date,
        "end_date": p.end_date,
        "capacity": p.capacity,
        "responsible": resp.display_name if resp else None,
        "official": p.status in {"approved", "active", "completed"} and bool(p.approved_by_user_id or p.is_demo),
        "official_note": OFFICIAL_NOTE,
        "updated_at": p.updated_at,
        "cohort_count": db.scalar(select(func.count()).select_from(PilotCohort).where(PilotCohort.program_id == p.id))
        or 0,
        "member_count": db.scalar(
            select(func.count())
            .select_from(CohortMember)
            .where(CohortMember.program_id == p.id, CohortMember.status == "active")
        )
        or 0,
    }
    if not detail:
        return base
    appr = db.get(User, p.approved_by_user_id) if p.approved_by_user_id else None
    return {
        **base,
        "objective": p.objective,
        "description": p.description,
        "responsible_user_id": p.responsible_user_id,
        "default_course_id": p.default_course_id,
        "review_note": p.review_note,
        "approved_by": appr.display_name if appr else None,
        "approved_at": p.approved_at,
        "approval_evidence_ref": p.approval_evidence_ref,
        "allowed_actions": program_actions(db, user, p),
        "submit_missing": _submit_missing(db, p) if p.status == "draft" else [],
        "cohorts": [
            cohort_out(db, c)
            for c in db.scalars(
                select(PilotCohort).where(PilotCohort.program_id == p.id).order_by(PilotCohort.created_at)
            )
        ],
        "announcements": announcements_out(db, p.id),
        "retention_days": get_settings().pilot_retention_days,
        "anonymized_at": p.anonymized_at,
    }


def cohort_out(db: Session, c: PilotCohort) -> dict:
    course = db.get(Course, c.course_id)
    inst = db.get(User, c.instructor_user_id) if c.instructor_user_id else None
    sessions = db.scalars(
        select(CohortSession).where(CohortSession.cohort_id == c.id).order_by(CohortSession.starts_at)
    ).all()
    return {
        "id": c.id,
        "program_id": c.program_id,
        "name": c.name,
        "course_id": c.course_id,
        "course_title": course.title if course else None,
        "instructor_user_id": c.instructor_user_id,
        "instructor": inst.display_name if inst else None,
        "status": c.status,
        "start_date": c.start_date,
        "end_date": c.end_date,
        "capacity": c.capacity,
        "member_count": _member_count(db, c.id),
        "sessions": [
            {
                "id": s.id,
                "title": s.title,
                "starts_at": s.starts_at,
                "ends_at": s.ends_at,
                "location_note": s.location_note,
            }
            for s in sessions
        ],
    }


def list_programs(db: Session, user: User, page: int, size: int, status: str | None) -> dict:
    from app.services.queries import paginate

    stmt = select(PilotProgram)
    if user.role != "admin":
        stmt = stmt.where(PilotProgram.partner_id.in_(perm.my_partner_ids(db, user)))
    if status:
        stmt = stmt.where(PilotProgram.status == status)
    return paginate(db, stmt.order_by(PilotProgram.updated_at.desc()), page, size, lambda x: program_out(db, user, x))


def members_out(db: Session, c: PilotCohort) -> list[dict]:
    rows = db.execute(
        select(CohortMember, User)
        .join(User, User.id == CohortMember.user_id)
        .where(CohortMember.cohort_id == c.id)
        .order_by(CohortMember.status, User.display_name)
    ).all()
    return [
        {"user_id": u.id, "name": u.display_name, "email": u.email, "status": m.status, "joined_at": m.joined_at}
        for m, u in rows
    ]


# ---------- portal pelajar ----------
def portal(db: Session, user: User) -> dict:
    rows = db.execute(
        select(CohortMember, PilotCohort, PilotProgram)
        .join(PilotCohort, PilotCohort.id == CohortMember.cohort_id)
        .join(PilotProgram, PilotProgram.id == PilotCohort.program_id)
        .where(
            CohortMember.user_id == user.id,
            CohortMember.status == "active",
            PilotProgram.status.in_(access.PROGRAM_RW + access.PROGRAM_RO),  # cancelled/archived/draft: akses ditutup
        )
        .order_by(CohortMember.joined_at.desc())
    ).all()
    out = []
    for m, c, p in rows:
        course = db.get(Course, c.course_id)
        enr = progress.get_enrollment(db, user.id, c.course_id)
        out.append(
            {
                "cohort_id": c.id,
                "cohort_name": c.name,
                "program_id": p.id,
                "program_name": p.name,
                "program_status": p.status,
                "program_status_label": PROGRAM_LABEL[p.status],
                "is_demo": p.is_demo,
                "course_slug": course.slug if course else None,
                "course_title": course.title if course else None,
                "joined_at": m.joined_at,
                "progress": progress.enrollment_state(db, enr)["progress"] if enr else None,
            }
        )
    pending = pending_surveys(db, user)
    return {"memberships": out, "pending_surveys": pending}


def my_cohort(db: Session, user: User, cohort_id) -> dict:
    c = db.get(PilotCohort, perm.parse_id(cohort_id, "Cohort"))
    m = (
        db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == c.id, CohortMember.user_id == user.id, CohortMember.status == "active"
            )
        )
        if c
        else None
    )
    if not c or not m:
        raise ApiError(404, "NOT_FOUND", "Cohort tidak ditemukan.")
    p = db.get(PilotProgram, c.program_id)
    if p.status not in access.PROGRAM_RW + access.PROGRAM_RO:
        raise ApiError(404, "NOT_FOUND", "Cohort tidak ditemukan.")  # program cancelled/archived/draft: akses ditutup
    partner = db.get(Partner, p.partner_id)
    course = db.get(Course, c.course_id)
    enr = progress.get_enrollment(db, user.id, c.course_id)
    lessons = progress.visible_lessons(db, c.course_id, user, system=True)
    done = progress.completed_ids(db, user.id, c.course_id)
    from app.models import PracticeSession

    prac = db.execute(
        select(func.count(), func.coalesce(func.sum(PracticeSession.active_duration_ms), 0)).where(
            PracticeSession.user_id == user.id,
            PracticeSession.lesson_id.in_([le.id for le, _ in lessons] or [uuid.uuid4()]),
            PracticeSession.status == "completed",
        )
    ).one()
    return {
        **cohort_out(db, c),
        "program_name": p.name,
        "program_objective": p.objective,
        "program_status_label": PROGRAM_LABEL[p.status],
        "is_demo": p.is_demo,
        "partner_name": partner.name,
        "course_slug": course.slug if course else None,
        "lessons": [
            {"id": le.id, "slug": le.slug, "title": le.title, "module": mod.title, "completed": le.id in done}
            for le, mod in lessons
        ],
        "progress": progress.enrollment_state(db, enr)["progress"] if enr else None,
        "practice": {"completed_sessions": prac[0], "active_minutes": round((prac[1] or 0) / 60000)},
        "announcements": announcements_out(db, p.id, c.id),
        "consents": consents_of(db, user.id, p.id),
        "surveys": pending_surveys(db, user, program_id=p.id),
        "policy_version": get_settings().pilot_policy_version,
    }


# ---------- survei ----------
TEMPLATES = {
    "baseline": (
        "Survei awal (baseline)",
        [
            {
                "id": "pengalaman",
                "type": "single_choice",
                "text": "Seberapa sering Anda berlatih pencak silat dalam tiga bulan terakhir?",
                "options": ["Belum pernah", "Beberapa kali", "Sekitar sekali seminggu", "Beberapa kali seminggu"],
            },
            {
                "id": "percaya_diri",
                "type": "rating",
                "text": "Seberapa yakin Anda dapat mengikuti materi pencak silat melalui aplikasi?",
                "min_label": "Tidak yakin",
                "max_label": "Sangat yakin",
            },
            {
                "id": "akses_instruktur",
                "type": "single_choice",
                "text": "Seberapa mudah Anda menemui instruktur/perguruan untuk belajar?",
                "options": ["Sangat sulit", "Cukup sulit", "Cukup mudah", "Sangat mudah"],
            },
            {
                "id": "harapan",
                "type": "open_text",
                "text": "Apa yang ingin Anda dapatkan dari program ini?",
                "required": False,
            },
        ],
    ),
    "endline": (
        "Survei akhir (endline)",
        [
            {
                "id": "pengalaman",
                "type": "single_choice",
                "text": "Seberapa sering Anda berlatih pencak silat selama program?",
                "options": ["Belum pernah", "Beberapa kali", "Sekitar sekali seminggu", "Beberapa kali seminggu"],
            },
            {
                "id": "percaya_diri",
                "type": "rating",
                "text": "Seberapa yakin Anda dapat mengikuti materi pencak silat melalui aplikasi?",
                "min_label": "Tidak yakin",
                "max_label": "Sangat yakin",
            },
            {
                "id": "akses_instruktur",
                "type": "single_choice",
                "text": "Seberapa mudah Anda menemui instruktur/perguruan untuk belajar?",
                "options": ["Sangat sulit", "Cukup sulit", "Cukup mudah", "Sangat mudah"],
            },
            {
                "id": "catatan",
                "type": "open_text",
                "text": "Perubahan apa yang Anda rasakan setelah mengikuti program (menurut Anda sendiri)?",
                "required": False,
            },
        ],
    ),
    "feedback_learner": (
        "Umpan balik peserta",
        [
            {
                "id": "kemudahan",
                "type": "rating",
                "text": "Seberapa mudah aplikasi digunakan?",
                "min_label": "Sulit",
                "max_label": "Mudah",
            },
            {
                "id": "materi",
                "type": "rating",
                "text": "Seberapa jelas materi pelajaran?",
                "min_label": "Tidak jelas",
                "max_label": "Sangat jelas",
            },
            {
                "id": "kamera",
                "type": "single_choice",
                "text": "Apakah Anda mencoba Practice Studio (kamera)?",
                "options": ["Ya, berjalan baik", "Ya, ada kendala", "Tidak mencoba"],
            },
            {"id": "saran", "type": "open_text", "text": "Saran atau kendala yang Anda alami", "required": False},
        ],
    ),
    "feedback_instructor": (
        "Umpan balik instruktur",
        [
            {
                "id": "kemudahan",
                "type": "rating",
                "text": "Seberapa mudah mengelola cohort dan memantau peserta?",
                "min_label": "Sulit",
                "max_label": "Mudah",
            },
            {
                "id": "waktu",
                "type": "single_choice",
                "text": "Waktu yang dibutuhkan mengelola cohort per minggu",
                "options": ["< 1 jam", "1–3 jam", "3–6 jam", "> 6 jam"],
            },
            {"id": "saran", "type": "open_text", "text": "Masukan untuk platform", "required": False},
        ],
    ),
}


def create_survey(
    db: Session, user: User, p: PilotProgram, kind: str, title: str, questions: list[dict], rid
) -> PilotSurvey:
    ids = [q["id"] for q in questions]
    if len(set(ids)) != len(ids):
        raise ApiError(422, "VALIDATION_ERROR", "ID pertanyaan harus unik.")
    for q in questions:
        if q["type"] == "single_choice" and not (q.get("options") and len(q["options"]) >= 2):
            raise ApiError(422, "VALIDATION_ERROR", f"Pertanyaan {q['id']}: pilihan ganda butuh minimal 2 opsi.")
    s = PilotSurvey(program_id=p.id, kind=kind, title=title, questions=questions, status="draft")
    db.add(s)
    _flush(db)
    audit.record(
        db,
        actor=user,
        action="pilot.survey_create",
        entity_type="pilot_survey",
        entity_id=s.id,
        detail={"kind": kind},
        request_id=rid,
    )
    return s


def survey_from_template(db, user, p, kind, rid) -> PilotSurvey:
    title, qs = TEMPLATES[kind]
    full = [
        {"required": True, "scale_min": 1, "scale_max": 5, "options": None, "min_label": None, "max_label": None, **q}
        for q in qs
    ]
    return create_survey(db, user, p, kind, title, full, rid)


def survey_action(db: Session, user: User, s: PilotSurvey, action: str, rid) -> PilotSurvey:
    if action == "open" and s.status != "draft":
        raise ApiError(409, "INVALID_TRANSITION", "Survei hanya dapat dibuka dari draf.")
    if action == "close" and s.status != "open":
        raise ApiError(409, "INVALID_TRANSITION", "Survei hanya dapat ditutup saat terbuka.")
    s.status = "open" if action == "open" else "closed"
    audit.record(
        db, actor=user, action=f"pilot.survey_{action}", entity_type="pilot_survey", entity_id=s.id, request_id=rid
    )
    return s


def survey_out(s: PilotSurvey, responses: int | None = None) -> dict:
    return {
        "id": s.id,
        "program_id": s.program_id,
        "kind": s.kind,
        "title": s.title,
        "status": s.status,
        "questions": s.questions,
        "instrument_note": s.instrument_note,
        "responses": responses,
    }


def audience(s: PilotSurvey) -> str:
    return "instructor" if s.kind == "feedback_instructor" else "learner"


def pending_surveys(db: Session, user: User, program_id=None) -> list[dict]:
    """Survei terbuka yang relevan bagi pengguna dan belum diisi."""
    out = []
    mem = select(CohortMember.program_id).where(CohortMember.user_id == user.id, CohortMember.status == "active")
    stmt = select(PilotSurvey).where(
        PilotSurvey.status == "open", PilotSurvey.kind != "feedback_instructor", PilotSurvey.program_id.in_(mem)
    )
    if program_id:
        stmt = stmt.where(PilotSurvey.program_id == program_id)
    rows = list(db.scalars(stmt))
    inst = select(PilotCohort.program_id).where(PilotCohort.instructor_user_id == user.id)
    rows += list(
        db.scalars(
            select(PilotSurvey).where(
                PilotSurvey.status == "open",
                PilotSurvey.kind == "feedback_instructor",
                PilotSurvey.program_id.in_(inst),
            )
        )
    )
    for s in rows:
        done = db.scalar(
            select(SurveyResponse.id).where(SurveyResponse.survey_id == s.id, SurveyResponse.user_id == user.id)
        )
        out.append({**survey_out(s), "answered": bool(done)})
    return [o for o in out if not o["answered"]] if program_id is None else out


def submit_survey(db: Session, user: User, s: PilotSurvey, body: sc.SurveySubmit, rid) -> SurveyResponse:
    if s.status != "open":
        raise ApiError(409, "SURVEY_CLOSED", "Survei tidak sedang dibuka.")
    cohort_id = None
    if audience(s) == "learner":
        m = db.scalar(
            select(CohortMember).where(
                CohortMember.program_id == s.program_id,
                CohortMember.user_id == user.id,
                CohortMember.status == "active",
            )
        )
        if not m:
            raise ApiError(404, "NOT_FOUND", "Survei tidak ditemukan.")
        cohort_id = m.cohort_id
    else:
        c = db.scalar(
            select(PilotCohort).where(PilotCohort.program_id == s.program_id, PilotCohort.instructor_user_id == user.id)
        )
        if not c:
            raise ApiError(404, "NOT_FOUND", "Survei tidak ditemukan.")
        cohort_id = c.id
    answers = validate_answers(s.questions, body.answers)
    r = SurveyResponse(survey_id=s.id, cohort_id=cohort_id, user_id=user.id, answers=answers, submitted_at=now())
    db.add(r)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(409, "ALREADY_SUBMITTED", "Anda sudah mengisi survei ini.") from exc
    audit.record(
        db, actor=user, action="pilot.survey_submit", entity_type="pilot_survey", entity_id=s.id, request_id=rid
    )
    return r


def validate_answers(questions: list[dict], raw: dict) -> dict:
    known = {q["id"] for q in questions}
    extra = set(raw) - known
    if extra:
        raise ApiError(422, "VALIDATION_ERROR", "Jawaban memuat pertanyaan yang tidak dikenal.", sorted(extra))
    out, errs = {}, []
    for q in questions:
        v = raw.get(q["id"])
        if v in (None, ""):
            if q.get("required", True):
                errs.append({"field": q["id"], "message": "wajib diisi"})
            continue
        if q["type"] == "single_choice":
            if v not in (q.get("options") or []):
                errs.append({"field": q["id"], "message": "pilihan tidak valid"})
            else:
                out[q["id"]] = v
        elif q["type"] == "rating":
            lo, hi = q.get("scale_min", 1), q.get("scale_max", 5)
            if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
                errs.append({"field": q["id"], "message": f"harus angka {lo}–{hi}"})
            else:
                out[q["id"]] = v
        else:
            if not isinstance(v, str) or len(v) > 2000:
                errs.append({"field": q["id"], "message": "teks maksimal 2000 karakter"})
            else:
                out[q["id"]] = v.strip()
    if errs:
        raise ApiError(422, "VALIDATION_ERROR", "Jawaban survei tidak valid.", errs)
    return out


_ = (date, datetime, Enrollment, Lesson)
