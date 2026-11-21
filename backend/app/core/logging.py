"""Log terstruktur (JSON satu baris) dengan korelasi `request_id`/`job_id` dan REDAKSI otomatis.

Tidak boleh ada di log: sandi, token sesi/CSRF/verifikasi/reset/undangan, isi email, alamat email lengkap, landmark.
Pertahanan berlapis: (1) kode tidak pernah mencatat nilai itu, (2) query string TIDAK dicatat (tautan undangan memuat `?token=`),
(3) filter ini meredaksi pola rahasia pada setiap pesan/ekstra sebagai jaring pengaman.
"""

import contextvars
import json
import logging
import os
import re
import sys
from datetime import UTC, datetime

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
job_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("job_id", default=None)

_PATTERNS = [
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (
        re.compile(
            r"(?i)(token|password|passwd|secret|csrf|authorization|cookie|session)(\"?\s*[:=]\s*\"?)[^\s\",&;]+"
        ),
        r"\1\2[REDACTED]",
    ),
    (re.compile(r"(?i)(silatara_session|silatara_csrf)=[^\s;,]+"), r"\1=[REDACTED]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (re.compile(r"\b[A-Za-z0-9_-]{40,}\b"), "[REDACTED-TOKEN]"),  # token_urlsafe(32) = 43 karakter
]
_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime", "taskName"}
_DENY_KEYS = re.compile(r"(?i)(password|token|secret|cookie|authorization|landmark|body|answers|note)")


def redact(text: str) -> str:
    for pat, rep in _PATTERNS:
        text = pat.sub(rep, text)
    return text


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        doc = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": redact(record.getMessage()),
            "request_id": request_id_var.get(),
            "job_id": job_id_var.get(),
        }
        for k, v in record.__dict__.items():
            if k in _RESERVED or k.startswith("_"):
                continue
            doc[k] = "[REDACTED]" if _DENY_KEYS.search(k) else (redact(v) if isinstance(v, str) else v)
        if record.exc_info:
            doc["error_class"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            doc["exc"] = redact(self.formatException(record.exc_info))[-1500:]
        return json.dumps({k: v for k, v in doc.items() if v is not None}, ensure_ascii=False, default=str)


def setup_logging() -> None:
    root = logging.getLogger()
    if any(getattr(h, "_silatara", False) for h in root.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler._silatara = True  # type: ignore[attr-defined]
    root.handlers = [handler]
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers, lg.propagate = [], True
    logging.getLogger("uvicorn.access").disabled = True  # memuat query string (token undangan); diganti access log kita
