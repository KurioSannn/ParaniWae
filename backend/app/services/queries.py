from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.schemas.common import make_page


def like(q: str) -> str:
    esc = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{esc}%"


def search_cond(q: str | None, *cols):
    if not q or not q.strip():
        return None
    pat = like(q.strip()[:100])
    return or_(*[c.ilike(pat, escape="\\") for c in cols])


def apply_sort(stmt, sort: str | None, allowed: dict, default: str):
    key = sort or default
    if key not in allowed:
        raise ApiError(422, "INVALID_SORT", "Parameter sort tidak dikenal.",
                       {"allowed": sorted(allowed)})
    return stmt.order_by(*allowed[key])


def paginate(db: Session, stmt, page: int, page_size: int, mapper) -> dict:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(stmt.limit(page_size).offset((page - 1) * page_size)).all()
    return make_page([mapper(r) for r in rows], total, page, page_size)
