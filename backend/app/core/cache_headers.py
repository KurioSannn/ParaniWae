"""Header cache untuk API. Materi/respons yang bergantung pada identitas TIDAK boleh tersimpan di cache bersama/publik.

- Semua respons /api/v1 membawa `Vary: Cookie` (respons dapat berbeda per pengguna: mis. kursus privat vs publik).
- Permintaan ber-sesi, atau path privat (pilot, studio, me, media, manage, admin, practice, pelajaran), mendapat
  `Cache-Control: private, no-store` kecuali endpoint sudah menetapkannya (mis. media publik terverifikasi).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings

PRIVATE_PREFIXES = (
    "/api/v1/pilot",
    "/api/v1/studio",
    "/api/v1/me",
    "/api/v1/media",
    "/api/v1/manage",
    "/api/v1/admin",
    "/api/v1/practice",
    "/api/v1/auth",
)


def _is_private_path(path: str) -> bool:
    return path.startswith(PRIVATE_PREFIXES) or (path.startswith("/api/v1/courses/") and "/lessons/" in path)


class CacheHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if not request.url.path.startswith("/api/v1"):
            return response
        response.headers["Vary"] = "Cookie" if "vary" not in response.headers else response.headers["vary"] + ", Cookie"
        has_session = get_settings().session_cookie_name in request.cookies
        if "cache-control" not in response.headers and (has_session or _is_private_path(request.url.path)):
            response.headers["Cache-Control"] = "private, no-store"
        return response
