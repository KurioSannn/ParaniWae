"""Penyimpanan file privat (media referensi & dokumen persetujuan mitra).

- File disimpan dengan nama acak (32 hex) di `MEDIA_DIR/<2 hex>/<key>`; nama asli hanya metadata.
- Tipe file ditentukan dari magic bytes, bukan ekstensi/Content-Type klien.
- Ukuran dibatasi saat streaming; file parsial dihapus. Tidak ada URL statis: akses lewat endpoint terotorisasi.
"""

import hashlib
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.errors import ApiError

KEY_RE = re.compile(r"^[0-9a-f]{32}$")
MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "video/mp4", "video/webm"}
DOC_TYPES = {"application/pdf", "image/jpeg", "image/png"}
_CHUNK = 1024 * 1024


@dataclass
class Stored:
    key: str
    mime: str
    size: int
    sha256: str
    filename: str


def sniff(head: bytes) -> str | None:
    if head[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head[4:8] == b"ftyp":
        return "video/mp4"
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return "video/webm"
    if head[:5] == b"%PDF-":
        return "application/pdf"
    return None


def clean_filename(name: str | None) -> str:
    base = os.path.basename((name or "file").replace("\\", "/"))
    base = re.sub(r"[\x00-\x1f\x7f]", "", base).strip() or "file"
    return base[-255:]


def _root() -> Path:
    return Path(get_settings().media_dir)


def path_for(key: str) -> Path:
    if not KEY_RE.match(key):
        raise ApiError(404, "NOT_FOUND", "File tidak ditemukan.")
    return _root() / key[:2] / key


def max_bytes(mime: str) -> int:
    s = get_settings()
    if mime.startswith("video/"):
        return s.media_max_video_mb * 1024 * 1024
    return (s.media_max_image_mb if mime.startswith("image/") else s.partner_doc_max_mb) * 1024 * 1024


def save_upload(upload: UploadFile, allowed: set[str]) -> Stored:
    """Streaming + validasi. Melempar ApiError 415/413/422; tidak meninggalkan file parsial."""
    key = uuid.uuid4().hex
    final = path_for(key)
    final.parent.mkdir(parents=True, exist_ok=True)
    tmp = final.with_suffix(".part")
    h, size, mime = hashlib.sha256(), 0, None
    try:
        with open(tmp, "wb") as out:
            while chunk := upload.file.read(_CHUNK):
                if mime is None:
                    mime = sniff(chunk[:16])
                    if mime is None or mime not in allowed:
                        raise ApiError(
                            415, "UNSUPPORTED_MEDIA_TYPE", "Jenis file tidak didukung.", {"allowed": sorted(allowed)}
                        )
                size += len(chunk)
                if size > max_bytes(mime):
                    raise ApiError(
                        413, "FILE_TOO_LARGE", f"Ukuran file melebihi batas {max_bytes(mime) // (1024 * 1024)} MB."
                    )
                h.update(chunk)
                out.write(chunk)
        if mime is None or size == 0:
            raise ApiError(422, "EMPTY_FILE", "File kosong.")
        os.replace(tmp, final)
        os.chmod(final, 0o640)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return Stored(key, mime, size, h.hexdigest(), clean_filename(upload.filename))


def remove(key: str) -> None:
    try:
        path_for(key).unlink(missing_ok=True)
    except ApiError:
        pass
