"""Format error konsisten (docs/API_CONTRACTS.md): {"error": {code, message, details, request_id}}."""

import logging
import re
import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_id_var

log = logging.getLogger("silatara.access")
_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def _route_path(request: Request) -> str:
    """Template rute (mis. /pilot/programs/{program_id}) bila ada; fallback path dengan UUID diganti :id. Tanpa query."""
    route = request.scope.get("route")
    return getattr(route, "path", None) or _UUID.sub(":id", request.url.path)


class ApiError(Exception):
    def __init__(
        self, status_code: int, code: str, message: str, details: Any = None, headers: dict[str, str] | None = None
    ):
        self.status_code, self.code, self.message, self.details = (
            status_code,
            code,
            message,
            details,
        )
        self.headers = headers


def _body(request: Request, code: str, message: str, details: Any = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": getattr(request.state, "request_id", None),
        }
    }


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = rid[:64]
        token = request_id_var.set(request.state.request_id)
        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            log.error(
                "permintaan gagal tak tertangani",
                exc_info=exc,
                extra={"method": request.method, "path": _route_path(request), "error_class": type(exc).__name__},
            )
            raise
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request.state.request_id
        # access log TANPA query string (tautan undangan/token di query) dan tanpa nilai header/cookie
        status = response.status_code
        log.log(
            logging.ERROR if status >= 500 else logging.INFO,
            "http",
            extra={
                "method": request.method,
                "path": _route_path(request),
                "status": status,
                "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
                "authenticated": "cookie" in request.headers
                and "silatara_session" in request.headers.get("cookie", ""),
                "request_id": request.state.request_id,
                "error_class": "http_5xx" if status >= 500 else ("http_4xx" if status >= 400 else None),
            },
        )
        return response


_HTTP_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(request: Request, exc: ApiError):
        return JSONResponse(
            _body(request, exc.code, exc.message, exc.details),
            status_code=exc.status_code,
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = _HTTP_CODES.get(exc.status_code, "ERROR")
        return JSONResponse(_body(request, code, str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        # Tidak menyertakan nilai input (bisa berisi sandi) — hanya lokasi & pesan.
        details = [
            {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]} for e in exc.errors()
        ]
        return JSONResponse(
            _body(request, "VALIDATION_ERROR", "Data yang dikirim tidak valid.", details),
            status_code=422,
        )
