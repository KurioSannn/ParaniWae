from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.api.deps import AuthContext, auth_required
from app.core.config import get_settings
from app.core.db import get_db
from app.core.netinfo import client_ip
from app.core.security import hash_password
from app.models import User
from app.schemas.auth import AuthOut, EmailIn, LoginIn, RegisterIn, ResetConfirmIn, TokenIn
from app.services import audit, mail, ratelimit, tokens
from app.services import auth as svc
from app.services.auth import now, revoke_all_sessions
from app.services.mail import get_mailer

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookies(response: Response, token: str, csrf: str) -> None:
    s = get_settings()
    max_age = s.session_ttl_hours * 3600
    response.set_cookie(
        s.session_cookie_name, token, max_age=max_age, httponly=True,
        samesite="lax", secure=s.use_secure_cookies, path="/",
    )
    # Dapat dibaca JS (double-submit untuk header X-CSRF-Token); bukan kredensial.
    response.set_cookie(
        s.csrf_cookie_name, csrf, max_age=max_age, httponly=False,
        samesite="lax", secure=s.use_secure_cookies, path="/",
    )


def _clear_cookies(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(s.session_cookie_name, path="/")
    response.delete_cookie(s.csrf_cookie_name, path="/")


def _rid(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


ACCEPTED_GENERIC = {"status": "ok", "message": "Jika data sesuai, petunjuk telah dikirim ke email Anda."}


@router.post("/register", status_code=202, summary="Daftar akun pelajar (verifikasi email)")
def register(body: RegisterIn, request: Request, db: DbSession = Depends(get_db)):
    """Respons identik untuk email baru maupun yang sudah terdaftar (anti-enumerasi). Tidak ada sesi
    sampai email diverifikasi. Semua registrasi publik berperan `learner`."""
    s = get_settings()
    ratelimit.hit(db, "register:ip", client_ip(request), s.rl_register_ip)
    mailer = get_mailer(db)  # 503 bila email belum dikonfigurasi (tidak berpura-pura terkirim)
    svc.register(db, body.email, body.password, body.display_name, _rid(request), mailer)
    db.commit()
    return svc.GENERIC_REGISTER


@router.post("/verify-email", summary="Verifikasi email dengan token sekali pakai")
def verify_email(body: TokenIn, request: Request, db: DbSession = Depends(get_db)):
    ratelimit.hit(db, "verify:ip", client_ip(request), get_settings().rl_verify_ip)
    user = tokens.consume(db, body.token, "verify_email")
    user.email_verified_at = user.email_verified_at or now()
    audit.record(db, actor=user, action="user.email_verified", entity_type="user",
                 entity_id=user.id, request_id=_rid(request))
    db.commit()
    return {"status": "verified"}


@router.post("/resend-verification", status_code=202, summary="Kirim ulang email verifikasi")
def resend_verification(body: EmailIn, request: Request, db: DbSession = Depends(get_db)):
    s = get_settings()
    ratelimit.hit(db, "resend:ip", client_ip(request), s.rl_reset_ip)
    ratelimit.hit(db, "resend:email", svc.normalize_email(body.email), s.rl_resend_email)
    mailer = get_mailer(db)
    user = db.scalar(select(User).where(User.email == svc.normalize_email(body.email)))
    if user and user.status == "active" and user.email_verified_at is None:
        raw = tokens.issue(db, user, "verify_email", timedelta(hours=s.verify_token_ttl_hours))
        mailer.send(user.email, "Verifikasi email SILATARA",
                    f"Verifikasi email Anda: {mail.link('/verifikasi-email', raw)}")
    db.commit()
    return ACCEPTED_GENERIC


@router.post("/password-reset/request", status_code=202, summary="Minta tautan reset kata sandi")
def password_reset_request(body: EmailIn, request: Request, db: DbSession = Depends(get_db)):
    s = get_settings()
    ratelimit.hit(db, "reset:ip", client_ip(request), s.rl_reset_ip)
    ratelimit.hit(db, "reset:email", svc.normalize_email(body.email), s.rl_reset_email)
    mailer = get_mailer(db)
    user = db.scalar(select(User).where(User.email == svc.normalize_email(body.email)))
    if user and user.status == "active":
        raw = tokens.issue(db, user, "reset_password", timedelta(minutes=s.reset_token_ttl_minutes))
        mailer.send(user.email, "Atur ulang kata sandi SILATARA",
                    f"Atur ulang kata sandi (berlaku {s.reset_token_ttl_minutes} menit, sekali pakai):\n"
                    f"{mail.link('/atur-ulang-sandi', raw)}\n\nJika bukan Anda, abaikan email ini.")
        audit.record(db, actor=user, action="user.password_reset_requested", entity_type="user",
                     entity_id=user.id, request_id=_rid(request))
    db.commit()
    return ACCEPTED_GENERIC  # sama persis untuk email terdaftar maupun tidak


@router.post("/password-reset/confirm", summary="Tetapkan kata sandi baru dengan token reset")
def password_reset_confirm(body: ResetConfirmIn, request: Request, db: DbSession = Depends(get_db)):
    ratelimit.hit(db, "resetc:ip", client_ip(request), get_settings().rl_verify_ip)
    user = tokens.consume(db, body.token, "reset_password")
    user.password_hash = hash_password(body.new_password)
    user.email_verified_at = user.email_verified_at or now()  # menerima email membuktikan kepemilikan
    user.failed_logins, user.locked_until = 0, None
    revoke_all_sessions(db, user.id)  # semua sesi lama dicabut
    audit.record(db, actor=user, action="user.password_reset", entity_type="user",
                 entity_id=user.id, request_id=_rid(request))
    db.commit()
    return {"status": "password_changed"}


@router.post("/login", response_model=AuthOut, summary="Masuk")
def login(body: LoginIn, request: Request, response: Response, db: DbSession = Depends(get_db)):
    ratelimit.hit(db, "login:ip", client_ip(request), get_settings().rl_login_ip)
    user = svc.authenticate(db, body.email, body.password, _rid(request))
    token, row = svc.create_session(db, user)  # sesi baru setiap login (anti-fixation)
    audit.record(db, actor=user, action="user.login", entity_type="user",
                 entity_id=user.id, request_id=_rid(request))
    db.commit()
    _set_cookies(response, token, row.csrf_token)
    return {"user": user, "csrf_token": row.csrf_token}


@router.post("/logout", status_code=204, summary="Keluar (mencabut sesi)")
def logout(request: Request, response: Response, ctx: AuthContext = Depends(auth_required()),
           db: DbSession = Depends(get_db)):
    ctx.session.revoked_at = now()
    audit.record(db, actor=ctx.user, action="user.logout", entity_type="user",
                 entity_id=ctx.user.id, request_id=_rid(request))
    db.commit()
    _clear_cookies(response)
    response.status_code = 204
    return response


@router.get("/me", response_model=AuthOut, summary="Identitas pengguna saat ini")
def me(ctx: AuthContext = Depends(auth_required())):
    return {"user": ctx.user, "csrf_token": ctx.session.csrf_token}
