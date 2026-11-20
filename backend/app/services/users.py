from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User
from app.models.user import ROLES


def create_admin(
    db: Session, email: str, password: str, display_name: str, role: str = "admin"
) -> User:
    if role not in ROLES:
        raise ValueError(f"Peran tidak dikenal: {role}")
    if len(password) < 12:
        raise ValueError("Kata sandi minimal 12 karakter.")
    email = email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise ValueError(f"Pengguna dengan email {email} sudah ada.")
    user = User(
        email=email,
        display_name=display_name,
        password_hash=hash_password(password),
        role=role,
        email_verified_at=datetime.now(UTC),
    )
    db.add(user)
    db.commit()
    return user
