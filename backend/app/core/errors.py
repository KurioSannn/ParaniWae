"""Format error konsisten (docs/API_CONTRACTS.md): {"error": {code, message, details, request_id}}."""

import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Any = None,
                 headers: dict[str, str] | None = None):
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
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
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
            _body(request, exc.code, exc.message, exc.details), status_code=exc.status_code,
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
            {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            _body(request, "VALIDATION_ERROR", "Data yang dikirim tidak valid.", details),
            status_code=422,
        )
