import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.security import hash_password, new_token, token_digest, verify_password
from app.models import Session, User
from app.services import audit

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")


def now() -> datetime:
    return datetime.now(UTC)


def normalize_email(email: str) -> str:
    return email.strip().lower()


GENERIC_REGISTER = {
    "status": "check_email",
    "message": "Jika email ini dapat didaftarkan, kami telah mengirim petunjuk ke kotak masuk Anda.",
}


def register(db: DbSession, email: str, password: str, display_name: str, rid: str | None,
             mailer) -> None:
    """Respons ke klien SELALU sama (anti-enumerasi). Email yang sudah terdaftar menerima pemberitahuan."""
    from app.core.config import get_settings
    from app.services import mail, tokens

    email = normalize_email(email)
    pw_hash = hash_password(password)  # selalu dihitung agar waktu respons mirip
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        mailer.send(email, "Percobaan pendaftaran di SILATARA",
                    "Seseorang mencoba mendaftar dengan email ini, tetapi akun sudah ada.\n\n"
                    f"Jika itu Anda, silakan masuk: {get_settings().public_base_url}/masuk\n"
                    f"atau atur ulang kata sandi: {get_settings().public_base_url}/lupa-sandi\n\n"
                    "Jika bukan Anda, abaikan email ini.")
        audit.record(db, actor=existing, action="user.register_duplicate", entity_type="user",
                     entity_id=existing.id, request_id=rid)
        return
    user = User(email=email, display_name=display_name.strip(), password_hash=pw_hash, role="learner")
    db.add(user)
    db.flush()
    raw = tokens.issue(db, user, "verify_email", timedelta(hours=get_settings().verify_token_ttl_hours))
    mailer.send(email, "Verifikasi email SILATARA",
                f"Halo {user.display_name},\n\nVerifikasi email Anda dengan membuka tautan berikut "
                f"(berlaku {get_settings().verify_token_ttl_hours} jam):\n"
                f"{mail.link('/verifikasi-email', raw)}\n\n"
                "Jika Anda tidak mendaftar, abaikan email ini.")
    audit.record(db, actor=user, action="user.register", entity_type="user", entity_id=user.id,
                 request_id=rid)


def authenticate(db: DbSession, email: str, password: str, rid: str | None) -> User:
    s = get_settings()
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    t = now()
    if user and user.locked_until and user.locked_until > t:
        verify_password(None, password)  # samakan waktu
        raise ApiError(429, "ACCOUNT_LOCKED",
                       "Terlalu banyak percobaan gagal. Coba lagi beberapa menit lagi.")
    ok, rehash = verify_password(user.password_hash if user else None, password)
    if not user or not ok or user.status != "active":
        if user:
            user.failed_logins += 1
            if user.failed_logins >= s.login_max_failures:
                user.locked_until = t + timedelta(minutes=s.login_lock_minutes)
                user.failed_logins = 0
            audit.record(db, actor=user, action="user.login_failed", entity_type="user",
                         entity_id=user.id, request_id=rid)
            db.commit()
        raise ApiError(401, "INVALID_CREDENTIALS", "Email atau kata sandi salah.")
    if user.email_verified_at is None:
        raise ApiError(403, "EMAIL_NOT_VERIFIED",
                       "Email belum diverifikasi. Periksa kotak masuk Anda atau kirim ulang verifikasi.")
    user.failed_logins = 0
    user.locked_until = None
    if rehash:
        user.password_hash = hash_password(password)
    return user


def create_session(db: DbSession, user: User) -> tuple[str, Session]:
    s = get_settings()
    token = new_token()
    t = now()
    row = Session(
        user_id=user.id,
        token_hash=token_digest(token),
        csrf_token=new_token(),
        expires_at=t + timedelta(hours=s.session_ttl_hours),
        last_seen_at=t,
    )
    db.add(row)
    db.flush()
    return token, row


def revoke_all_sessions(db: DbSession, user_id) -> None:
    t = now()
    for row in db.scalars(select(Session).where(Session.user_id == user_id,
                                                Session.revoked_at.is_(None))):
        row.revoked_at = t
