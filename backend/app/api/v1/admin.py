import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, PageParams, auth_required
from app.core.db import get_db
from app.core.errors import ApiError
from app.models import AuditLog, User
from app.schemas.manage import AdminUserPatch
from app.services import audit
from app.services.auth import revoke_all_sessions
from app.services.queries import paginate, search_cond

router = APIRouter(prefix="/admin", tags=["admin"])
Admin = auth_required("admin")


def _user(u: User) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "display_name": u.display_name,
        "role": u.role,
        "status": u.status,
        "created_at": u.created_at,
    }


@router.get("/users", summary="Daftar pengguna")
def list_users(
    q: str | None = None,
    role: str | None = None,
    p: PageParams = Depends(),
    ctx: AuthContext = Depends(Admin),
    db: Session = Depends(get_db),
):
    stmt = select(User)
    if (c := search_cond(q, User.email, User.display_name)) is not None:
        stmt = stmt.where(c)
    if role:
        stmt = stmt.where(User.role == role)
    return jsonable_encoder(paginate(db, stmt.order_by(User.created_at.desc()), p.page, p.page_size, _user))


@router.patch("/users/{user_id}", summary="Ubah peran/status pengguna (diaudit)")
def patch_user(
    user_id: uuid.UUID,
    body: AdminUserPatch,
    request: Request,
    ctx: AuthContext = Depends(Admin),
    db: Session = Depends(get_db),
):
    from app.core.config import get_settings
    from app.services import ratelimit

    ratelimit.hit(db, "admin:user", str(ctx.user.id), get_settings().rl_admin_user)
    u = db.get(User, user_id)
    if not u:
        raise ApiError(404, "NOT_FOUND", "Pengguna tidak ditemukan.")
    if u.id == ctx.user.id:
        raise ApiError(409, "SELF_CHANGE", "Admin tidak dapat mengubah peran/status akunnya sendiri.")
    before = {"role": u.role, "status": u.status}
    if body.role:
        u.role = body.role
    if body.status:
        u.status = body.status
    if before != {"role": u.role, "status": u.status}:
        revoke_all_sessions(db, u.id)  # perubahan hak akses berlaku seketika
    audit.record(
        db,
        actor=ctx.user,
        action="user.update",
        entity_type="user",
        entity_id=u.id,
        detail={"before": before, "after": {"role": u.role, "status": u.status}},
        request_id=getattr(request.state, "request_id", None),
    )
    db.commit()
    return jsonable_encoder(_user(u))


@router.get("/audit-logs", summary="Jejak audit")
def audit_logs(
    entity_type: str | None = None,
    p: PageParams = Depends(),
    ctx: AuthContext = Depends(Admin),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    return jsonable_encoder(
        paginate(
            db,
            stmt.order_by(AuditLog.created_at.desc()),
            p.page,
            p.page_size,
            lambda a: {
                "id": a.id,
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "actor_user_id": a.actor_user_id,
                "detail": a.detail,
                "created_at": a.created_at,
            },
        )
    )


# ---------- operasional (hanya-baca) ----------
@router.get("/ops/status", summary="Status operasional: DB, migrasi, media, scanner, worker, outbox, email, retensi")
def ops_status(ctx: AuthContext = Depends(Admin), db: Session = Depends(get_db)):
    from app.services import ops

    return jsonable_encoder(ops.ops_status(db))


@router.get("/ops/doctor", summary="Pemeriksaan kesiapan deployment (BLOCKER/WARNING/INFO), hanya-baca")
def ops_doctor(target: str = "current", ctx: AuthContext = Depends(Admin), db: Session = Depends(get_db)):
    from app.services import ops

    if target not in {"current", "production"}:
        raise ApiError(422, "VALIDATION_ERROR", "target harus current atau production.")
    return ops.summarize(ops.doctor(db, target=target))


@router.get("/ops/outbox", summary="Outbox: ringkasan + daftar untuk investigasi (tanpa isi pesan, email dimasker)")
def ops_outbox(status: str = "dead", ctx: AuthContext = Depends(Admin), db: Session = Depends(get_db)):
    from app.services import outbox

    if status not in {"pending", "sending", "sent", "dev_sink", "dead", "undeliverable"}:
        raise ApiError(422, "VALIDATION_ERROR", "status tidak valid.")
    return jsonable_encoder({"summary": outbox.status_summary(db), "rows": outbox.list_rows(db, status)})
