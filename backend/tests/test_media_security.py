"""Keamanan media: nama file, tipe palsu, arsip, overwrite, kegagalan pemindai (fail-closed), purge aman."""

import io
import socket
import threading
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import UploadFile
from sqlalchemy import select

from app.core.config import get_settings
from app.core.errors import ApiError
from app.models import AuditLog, ReferenceMedia
from app.services import media as media_svc
from app.services import scanner, storage
from tests.test_ops import FakeClamd, clamd, upload_media  # noqa: F401
from tests.test_studio import PNG, WEBM, api, as_, media_form, new_movement, ok, w  # noqa: F401


@pytest.fixture(autouse=True)
def _media_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "media_dir", str(tmp_path / "media"))


def up(body, name="a.webm"):
    return UploadFile(file=io.BytesIO(body), filename=name)


def files(root):
    return sorted(p for p in Path(root).rglob("*") if p.is_file())


# ---------- nama file / path traversal / overwrite ----------
@pytest.mark.parametrize(
    "name",
    ["../../etc/passwd.webm", "..\\..\\windows\\system32\\x.webm", "/abs/path/x.webm", "a\x00b.webm", "x\r\ny.webm"],
)
def test_hostile_filenames_never_affect_storage_path(name, tmp_path):
    st = storage.save_upload(up(WEBM + b"0" * 32, name), storage.MEDIA_TYPES)
    assert (
        ".." not in st.filename
        and "/" not in st.filename
        and "\\" not in st.filename
        and "\x00" not in st.filename
        and "\n" not in st.filename
    )
    assert storage.KEY_RE.match(st.key)  # nama berkas di disk = kunci acak 32 hex, bukan nama dari klien
    root = (tmp_path / "media").resolve()
    stored = files(root)
    assert len(stored) == 1 and stored[0].resolve().is_relative_to(root) and stored[0].name == st.key
    assert not (tmp_path / "etc").exists()


@pytest.mark.parametrize("key", ["../x", "..%2fx", "a" * 31, "g" * 32, "A" * 32, "", "../../etc/passwd"])
def test_path_for_rejects_non_random_keys(key):
    with pytest.raises(ApiError) as e:
        storage.path_for(key)
    assert e.value.status_code == 404
    with pytest.raises(ApiError):
        storage.quarantine_path(key)


def test_same_filename_twice_never_overwrites():
    a = storage.save_upload(up(WEBM + b"A" * 32, "sama.webm"), storage.MEDIA_TYPES)
    b = storage.save_upload(up(WEBM + b"B" * 32, "sama.webm"), storage.MEDIA_TYPES)
    assert (
        a.key != b.key
        and storage.path_for(a.key).read_bytes().endswith(b"A" * 32)
        and storage.path_for(b.key).read_bytes().endswith(b"B" * 32)
    )


# ---------- tipe: isi menentukan, bukan nama/header klien ----------
def test_content_decides_type_not_extension_or_client_mime(client, db, w):  # noqa: F811
    m = new_movement(w, w.inst)
    as_(client, w.inst)
    # PNG sungguhan dengan nama .webm + Content-Type video/webm -> disimpan sebagai image/png
    r = ok(
        api(
            client,
            "post",
            f"/studio/movements/{m['id']}/media",
            data=media_form(),
            files={"file": ("palsu.webm", io.BytesIO(PNG), "video/webm")},
        ),
        201,
    )
    assert r["mime"] == "image/png" and r["kind"] == "image"
    # executable Windows menyamar sebagai PNG/MP4/PDF -> ditolak
    for name, ctype in (("x.png", "image/png"), ("x.mp4", "video/mp4"), ("x.pdf", "application/pdf")):
        r = api(
            client,
            "post",
            f"/studio/movements/{m['id']}/media",
            data=media_form(),
            files={"file": (name, io.BytesIO(b"MZ\x90\x00" + b"0" * 64), ctype)},
        )
        assert r.status_code == 415, name
    # HTML/SVG/skrip menyamar sebagai gambar -> ditolak
    for body in (
        b"<html><script>alert(1)</script>",
        b"<svg xmlns='http://www.w3.org/2000/svg'><script/></svg>",
        b"#!/bin/sh\nrm -rf /",
    ):
        assert (
            api(
                client,
                "post",
                f"/studio/movements/{m['id']}/media",
                data=media_form(),
                files={"file": ("x.png", io.BytesIO(body), "image/png")},
            ).status_code
            == 415
        )


@pytest.mark.parametrize(
    "head",
    [
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"\x1f\x8b\x08",
        b"Rar!\x1a\x07\x00",
        b"7z\xbc\xaf\x27\x1c",
        b"BZh9",
        b"\xfd7zXZ\x00",
    ],
)
def test_archives_are_not_accepted_so_archive_bombs_cannot_be_stored(head):
    with pytest.raises(ApiError) as e:
        storage.save_upload(up(head + b"0" * 200, "arsip.webm"), storage.MEDIA_TYPES | storage.DOC_TYPES)
    assert e.value.status_code == 415
    assert not files(get_settings().media_dir)  # tidak ada sisa


def test_tar_archive_rejected():
    tar = b"\0" * 257 + b"ustar\x0000" + b"\0" * 300
    with pytest.raises(ApiError):
        storage.save_upload(up(tar), storage.MEDIA_TYPES | storage.DOC_TYPES)


def test_oversize_stream_leaves_no_partial_file(monkeypatch):
    monkeypatch.setattr(get_settings(), "media_max_video_mb", 1)
    with pytest.raises(ApiError) as e:
        storage.save_upload(up(WEBM + b"0" * (1024 * 1024 + 10)), storage.MEDIA_TYPES)
    assert e.value.status_code == 413 and not files(get_settings().media_dir)


# ---------- pemindai: fail-closed ----------
def _server(handler):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(5)

    def run():
        while True:
            try:
                c, _ = srv.accept()
            except OSError:
                return
            with c:
                handler(c)

    threading.Thread(target=run, daemon=True).start()
    return srv


def _point(monkeypatch, port):
    st = get_settings()
    monkeypatch.setattr(st, "scan_provider", "clamav")
    monkeypatch.setattr(st, "scan_host", "127.0.0.1")
    monkeypatch.setattr(st, "scan_port", port)
    monkeypatch.setattr(st, "scan_timeout_s", 1)


def _row(client, w, m, body=WEBM + b"0" * 64):
    r = ok(upload_media(client, w, m, body), 201)
    return r["id"]


def test_scanner_size_limit_error_is_terminal_error_not_clean(client, db, w, monkeypatch):  # noqa: F811
    def h(c):  # konsumsi protokol INSTREAM utuh, lalu balas galat batas ukuran seperti clamd asli
        import struct

        buf = b""
        while not buf.endswith(b"\0"):
            buf += c.recv(1)
        while True:
            hdr = b""
            while len(hdr) < 4:
                hdr += c.recv(4 - len(hdr))
            n = struct.unpack("!I", hdr)[0]
            if n == 0:
                break
            got = 0
            while got < n:
                got += len(c.recv(n - got))
        c.sendall(b"INSTREAM size limit exceeded. ERROR\0")

    srv = _server(h)
    _point(monkeypatch, srv.getsockname()[1])
    m = new_movement(w, w.inst)
    mid = _row(client, w, m)
    assert scanner.scan_pending(db)["error"] == 1
    row = db.get(ReferenceMedia, uuid.UUID(mid))
    assert (
        row.scan_status == "error"
        and "menolak" in row.scan_detail
        and storage.quarantine_path(row.storage_key).exists()
    )
    as_(client, w.adm)
    assert client.get(f"/api/v1/media/{mid}/file").status_code == 404  # fail-closed, termasuk admin
    srv.close()


def test_scanner_connection_reset_or_timeout_retries_with_backoff_then_errors_never_clean(client, db, w, monkeypatch):  # noqa: F811
    def h(c):  # menerima lalu menutup tanpa jawaban (crash/OOM clamd)
        c.recv(10)

    srv = _server(h)
    _point(monkeypatch, srv.getsockname()[1])
    m = new_movement(w, w.inst)
    mid = _row(client, w, m)
    row = db.get(ReferenceMedia, uuid.UUID(mid))
    out = scanner.scan_pending(db)
    assert (
        out["pending"] == 1
        and row.scan_status == "pending"
        and row.scan_attempts == 1
        and row.scan_next_at > datetime.now(UTC)
    )
    # belum jatuh tempo -> tidak dipindai ulang
    assert scanner.scan_pending(db) == {"clean": 0, "infected": 0, "error": 0, "pending": 0} and row.scan_attempts == 1
    for _ in range(scanner.MAX_SCAN_ATTEMPTS):
        row.scan_next_at = datetime.now(UTC) - timedelta(seconds=1)
        db.flush()
        scanner.scan_pending(db)
    assert (
        row.scan_status == "error"
        and row.scan_attempts >= scanner.MAX_SCAN_ATTEMPTS
        and storage.quarantine_path(row.storage_key).exists()
    )
    assert row.scan_status != "clean"
    srv.close()


def test_scanner_health_reports_without_changing_state(monkeypatch):
    monkeypatch.setattr(get_settings(), "scan_provider", "disabled")
    assert scanner.health() == {"enabled": False, "reachable": None}
    monkeypatch.setattr(get_settings(), "scan_provider", "clamav")
    monkeypatch.setattr(get_settings(), "scan_host", "127.0.0.1")
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    monkeypatch.setattr(get_settings(), "scan_port", port)
    assert scanner.health() == {"enabled": True, "reachable": False}


# ---------- purge aman ----------
def test_purge_expired_dry_run_execute_audit_and_orphans_never_auto_deleted(client, db, w):  # noqa: F811
    m = new_movement(w, w.inst)
    keep, expired = _row(client, w, m), _row(client, w, m, WEBM + b"E" * 64)
    krow, erow = db.get(ReferenceMedia, uuid.UUID(keep)), db.get(ReferenceMedia, uuid.UUID(expired))
    erow.retention_until = (datetime.now(UTC) - timedelta(days=1)).date()
    krow.retention_until = (datetime.now(UTC) + timedelta(days=30)).date()
    db.flush()
    root = Path(get_settings().media_dir)
    (root / "ff").mkdir(exist_ok=True)
    orphan = root / "ff" / ("f" * 32)
    orphan.write_bytes(b"yatim")
    rep = media_svc.purge_expired(db, dry_run=True)
    assert (
        rep["dry_run"] is True and rep["eligible"] == 1 and storage.path_for(erow.storage_key).exists()
    )  # dry-run: tidak ada yang hilang
    assert media_svc.orphan_report(db) == {
        "files": 4,
        "orphan_files": 1,
        "rows_without_file": 0,
    }  # 2 media + 1 dokumen mitra (fixture) + 1 yatim
    assert media_svc.purge_expired(db) == 1
    assert not storage.path_for(erow.storage_key).exists() and storage.path_for(krow.storage_key).exists()
    assert orphan.exists(), "berkas yatim tidak boleh dihapus otomatis"
    a = db.scalar(select(AuditLog).where(AuditLog.action == "media.purge_expired"))
    assert a.detail == {"deleted": 1}


def test_purge_can_be_disabled_by_config(client, db, w, monkeypatch):  # noqa: F811
    m = new_movement(w, w.inst)
    mid = _row(client, w, m)
    row = db.get(ReferenceMedia, uuid.UUID(mid))
    row.retention_until = (datetime.now(UTC) - timedelta(days=1)).date()
    db.flush()
    monkeypatch.setattr(get_settings(), "media_purge_enabled", False)
    assert media_svc.purge_expired(db) == 0 and storage.path_for(row.storage_key).exists()


_ = (FakeClamd, clamd, PNG)
