"""Penghitung query per-request untuk LOAD TEST (opt-in: DEBUG_QUERY_STATS=true; header `X-DB-Queries`). Tidak aktif default."""

import contextvars

from sqlalchemy import event
from starlette.middleware.base import BaseHTTPMiddleware

_count: contextvars.ContextVar[list | None] = contextvars.ContextVar("db_query_count", default=None)  # wadah mutabel: dibagi ke thread endpoint sync
_installed = False


def install(engine) -> None:
    global _installed
    if _installed:
        return
    _installed = True

    @event.listens_for(engine, "before_cursor_execute")
    def _count_query(conn, cursor, statement, parameters, context, executemany):  # noqa: ARG001
        box = _count.get()
        if box is not None:
            box[0] += 1


class QueryStatsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        box = [0]
        token = _count.set(box)
        try:
            response = await call_next(request)
            response.headers["X-DB-Queries"] = str(box[0])
            return response
        finally:
            _count.reset(token)
