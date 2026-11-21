"""Pemindaian malware nyata lewat clamd (ClamAV, protokol INSTREAM). Tidak ada "antivirus palsu".

- SCAN_PROVIDER=clamav: unggahan masuk karantina (`scan_status='pending'`, TIDAK dapat diakses siapa pun) -> dipindai worker
  -> `clean` (dipindah ke penyimpanan utama) | `infected` (berkas dihapus) | tetap `pending` bila pemindai tidak terjangkau.
- SCAN_PROVIDER=disabled: berkas langsung di penyimpanan utama dengan `scan_status='not_scanned'`: hanya untuk pengguna
  berwenang (internal), TIDAK PERNAH publik, dan UI melabelinya "belum dipindai".
"""

import socket
import struct
from datetime import datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import PartnerDocument, ReferenceMedia
from app.services import storage
from app.services.auth import now

_CHUNK = 64 * 1024


class ScannerUnavailable(Exception):
    """Pemindai tidak terjangkau/timeout/OOM/respons tak dikenal -> DICOBA ULANG; berkas tetap karantina (fail-closed)."""


class ScanRejected(Exception):
    """Pemindai menolak memproses berkas (mis. melebihi batas ukuran) -> status `error` terminal; tidak pernah dianggap bersih."""


def enabled() -> bool:
    return get_settings().scan_provider == "clamav"


def initial_status() -> str:
    return "pending" if enabled() else "not_scanned"


def clamd_scan(path, host: str | None = None, port: int | None = None, timeout: int | None = None) -> tuple[bool, str]:
    """(bersih?, detail). Melempar ScannerUnavailable bila clamd tidak terjangkau/berantakan."""
    s = get_settings()
    host, port, timeout = host or s.scan_host, port or s.scan_port, timeout or s.scan_timeout_s
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(b"zINSTREAM\0")
            with open(path, "rb") as f:
                while chunk := f.read(_CHUNK):
                    sock.sendall(struct.pack("!I", len(chunk)) + chunk)
            sock.sendall(struct.pack("!I", 0))
            resp = b""
            while not resp.endswith(b"\0") and (part := sock.recv(4096)):
                resp += part
    except OSError as exc:
        raise ScannerUnavailable(str(exc)) from exc
    text = resp.rstrip(b"\0").decode("utf-8", "replace").strip()
    if text.endswith("OK"):
        return True, "OK"
    if text.endswith("FOUND"):
        return False, text.removeprefix("stream:").removesuffix("FOUND").strip()[:200]
    if "size limit exceeded" in text.lower():
        raise ScanRejected(
            "ukuran melebihi batas pemindai (StreamMaxLength)"
        )  # terminal: bukan 'bersih', bukan 'coba lagi'
    raise ScannerUnavailable(f"respons clamd tidak dikenal: {text[:100]}")


MAX_SCAN_ATTEMPTS = 8


def _scan_row(row, now_: datetime) -> str:
    q = storage.quarantine_path(row.storage_key)
    if not q.exists():
        row.scan_status, row.scan_detail, row.scanned_at = "error", "berkas karantina tidak ditemukan", now_
        return "error"
    row.scan_attempts = (row.scan_attempts or 0) + 1
    try:
        clean, detail = clamd_scan(q)
    except ScanRejected as exc:
        row.scan_status, row.scan_detail, row.scanned_at = "error", f"pemindai menolak: {exc}", now_
        return "error"
    except ScannerUnavailable as exc:
        row.scan_detail = f"pemindai tidak dapat dihubungi: {str(exc)[:200]}"
        if row.scan_attempts >= MAX_SCAN_ATTEMPTS:  # berhenti mengulang tanpa batas; tetap TIDAK bersih
            row.scan_status, row.scanned_at = "error", now_
            row.scan_detail = f"pemindaian gagal setelah {row.scan_attempts} percobaan: {str(exc)[:150]}"
            return "error"
        row.scan_next_at = now_ + timedelta(seconds=min(900, 30 * 2 ** (row.scan_attempts - 1)))
        return "pending"
    row.scanned_at = now_
    if clean:
        storage.release(row.storage_key)
        row.scan_status, row.scan_detail = "clean", "ClamAV: OK"
        return "clean"
    storage.remove(row.storage_key)
    row.scan_status, row.scan_detail = "infected", f"ClamAV: {detail}"
    return "infected"


def scan_pending(db: Session, limit: int = 20) -> dict[str, int]:
    out = {"clean": 0, "infected": 0, "error": 0, "pending": 0}
    if not enabled():
        return out
    t = now()
    for model in (ReferenceMedia, PartnerDocument):
        for row in db.scalars(
            select(model)
            .where(model.scan_status == "pending", or_(model.scan_next_at.is_(None), model.scan_next_at <= t))
            .limit(limit)
        ):
            out[_scan_row(row, t)] += 1
    db.flush()
    return out


def health() -> dict:
    """Ping clamd (zPING). Dipakai doctor/ops-status; tidak mengubah state."""
    if not enabled():
        return {"enabled": False, "reachable": None}
    s = get_settings()
    try:
        with socket.create_connection((s.scan_host, s.scan_port), timeout=3) as sock:
            sock.sendall(b"zPING\0")
            return {"enabled": True, "reachable": sock.recv(16).startswith(b"PONG")}
    except OSError:
        return {"enabled": True, "reachable": False}
