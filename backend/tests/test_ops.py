"""Operasional: batas unggahan, karantina + pemindai (protokol clamd nyata), worker, verifikasi backup-restore."""

import io
import socket
import struct
import threading
import uuid
from pathlib import Path

import pytest
from fastapi import UploadFile
from sqlalchemy import select

from app.core.config import get_settings
from app.core.errors import ApiError
from app.models import PartnerDocument, ReferenceMedia
from app.services import retention, scanner, storage
from app.worker import run_once
from tests.test_studio import PDF, WEBM, api, as_, media_form, new_movement, ok, w  # noqa: F401

EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


@pytest.fixture(autouse=True)
def _media_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "media_dir", str(tmp_path / "media"))


class FakeClamd:
    """Server TCP kecil yang berbicara protokol clamd INSTREAM (zINSTREAM\\0 + chunk bertanda panjang). Mendeteksi EICAR."""

    def __init__(self):
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(5)
        self.port = self.sock.getsockname()[1]
        self.received = 0
        self.t = threading.Thread(target=self.serve, daemon=True)
        self.t.start()

    def serve(self):
        while True:
            try:
                c, _ = self.sock.accept()
            except OSError:
                return
            with c:
                cmd = b""
                while not cmd.endswith(b"\0"):
                    cmd += c.recv(1)
                assert cmd == b"zINSTREAM\0"
                data = b""
                while True:
                    hdr = b""
                    while len(hdr) < 4:
                        hdr += c.recv(4 - len(hdr))
                    n = struct.unpack("!I", hdr)[0]
                    if n == 0:
                        break
                    chunk = b""
                    while len(chunk) < n:
                        chunk += c.recv(n - len(chunk))
                    data += chunk
                self.received += len(data)
                c.sendall(b"stream: Eicar-Test-Signature FOUND\0" if EICAR in data else b"stream: OK\0")

    def close(self):
        self.sock.close()


@pytest.fixture
def clamd(monkeypatch):
    s = FakeClamd()
    st = get_settings()
    monkeypatch.setattr(st, "scan_provider", "clamav")
    monkeypatch.setattr(st, "scan_host", "127.0.0.1")
    monkeypatch.setattr(st, "scan_port", s.port)
    yield s
    s.close()


def up(body, name="a.webm"):
    return UploadFile(file=io.BytesIO(body), filename=name)


# ---------- batas unggahan ----------
def test_upload_limit_exact_100mb_accepted_and_one_byte_over_rejected(tmp_path):
    limit = get_settings().media_max_video_mb * 1024 * 1024
    assert limit == 100 * 1024 * 1024
    ok_body = WEBM + b"\0" * (limit - len(WEBM))
    st = storage.save_upload(up(ok_body), storage.MEDIA_TYPES)
    assert st.size == limit and storage.path_for(st.key).exists()
    storage.remove(st.key)
    with pytest.raises(ApiError) as e:
        storage.save_upload(up(ok_body + b"\0"), storage.MEDIA_TYPES)
    assert e.value.status_code == 413
    root = Path(get_settings().media_dir)
    assert not [p for p in root.rglob("*") if p.is_file()]  # tidak ada berkas parsial tertinggal


def test_upload_rejects_wrong_type_and_empty():
    with pytest.raises(ApiError) as e:
        storage.save_upload(up(b"MZ\x90\0 bukan media"), storage.MEDIA_TYPES)
    assert e.value.status_code == 415
    with pytest.raises(ApiError) as e:
        storage.save_upload(up(b""), storage.MEDIA_TYPES)
    assert e.value.status_code in (415, 422)


# ---------- karantina + pemindai ----------
def upload_media(client, w, m, body=WEBM + b"0" * 64):
    return api(
        client,
        "post",
        f"/studio/movements/{m['id']}/media",
        data=media_form(),
        files={"file": ("a.webm", io.BytesIO(body), "video/webm")},
    )


def test_quarantine_blocks_access_until_scan_clean(client, db, w, clamd):  # noqa: F811
    m = new_movement(w, w.inst)
    r = ok(upload_media(client, w, m), 201)
    assert r["scan_status"] == "pending" and "karantina" in r["scan_label"]
    row = db.get(ReferenceMedia, uuid.UUID(r["id"]))
    assert storage.quarantine_path(row.storage_key).exists() and not storage.path_for(row.storage_key).exists()
    # tidak dapat dibuka siapa pun (uploader, manager, kurator, admin), apa pun tingkat aksesnya
    for u in (w.inst, w.mgr, w.cur, w.adm):
        as_(client, u)
        assert client.get(f"/api/v1/media/{r['id']}/file").status_code == 404, u.role
    # tidak dapat dijadikan publik
    as_(client, w.mgr)
    assert api(client, "patch", f"/studio/media/{r['id']}", json={"access_level": "public"}).status_code == 409
    # pemindai bersih -> dirilis ke penyimpanan utama
    assert scanner.scan_pending(db)["clean"] == 1 and clamd.received > 0
    assert (
        row.scan_status == "clean"
        and storage.path_for(row.storage_key).exists()
        and not storage.quarantine_path(row.storage_key).exists()
    )
    as_(client, w.inst)
    assert client.get(f"/api/v1/media/{r['id']}/file").status_code == 200


def test_infected_file_is_deleted_and_never_accessible(client, db, w, clamd):  # noqa: F811
    m = new_movement(w, w.inst)
    r = ok(upload_media(client, w, m, body=WEBM + EICAR), 201)
    row = db.get(ReferenceMedia, uuid.UUID(r["id"]))
    assert scanner.scan_pending(db)["infected"] == 1
    assert row.scan_status == "infected" and "Eicar" in row.scan_detail
    assert storage.locate(row.storage_key) is None  # berkas dihapus
    as_(client, w.cur)
    assert client.get(f"/api/v1/media/{r['id']}/file").status_code == 404
    lst = ok(api(client, "get", f"/studio/movements/{m['id']}/media"))
    assert lst[0]["scan_status"] == "infected"  # statusnya tetap terlihat oleh pengelola


def test_scanner_unreachable_keeps_file_quarantined_not_clean(client, db, w, clamd, monkeypatch):  # noqa: F811
    m = new_movement(w, w.inst)
    r = ok(upload_media(client, w, m), 201)
    free = socket.socket()
    free.bind(("127.0.0.1", 0))
    dead_port = free.getsockname()[1]
    free.close()  # port tanpa pendengar -> koneksi ditolak
    monkeypatch.setattr(get_settings(), "scan_port", dead_port)
    monkeypatch.setattr(get_settings(), "scan_timeout_s", 1)
    out = scanner.scan_pending(db)
    row = db.get(ReferenceMedia, uuid.UUID(r["id"]))
    assert out["pending"] == 1 and row.scan_status == "pending" and "tidak dapat dihubungi" in row.scan_detail
    as_(client, w.mgr)
    assert client.get(f"/api/v1/media/{r['id']}/file").status_code == 404  # tidak pernah dianggap bersih


def test_scanner_disabled_marks_not_scanned_internal_only(client, db, w):  # noqa: F811
    assert get_settings().scan_provider == "disabled"
    m = new_movement(w, w.inst)
    r = ok(upload_media(client, w, m), 201)
    assert r["scan_status"] == "not_scanned" and "Belum dipindai" in r["scan_label"]
    as_(client, w.inst)
    assert client.get(f"/api/v1/media/{r['id']}/file").status_code == 200  # internal berwenang
    as_(client, w.mgr)
    assert (
        api(client, "patch", f"/studio/media/{r['id']}", json={"access_level": "public"}).status_code == 409
    )  # tidak pernah publik


def test_partner_document_quarantine(client, db, w, clamd):  # noqa: F811
    as_(client, w.mgr)
    r = client.post(
        f"/api/v1/studio/partners/{w.pid}/documents",
        data={"kind": "other"},
        files={"file": ("b.pdf", io.BytesIO(PDF), "application/pdf")},
    )
    assert r.status_code == 201
    doc = next(d for d in r.json()["documents"] if d["scan_status"] == "pending")
    assert client.get(f"/api/v1/studio/partner-documents/{doc['id']}/file").status_code == 423
    assert scanner.scan_pending(db)["clean"] >= 1
    assert client.get(f"/api/v1/studio/partner-documents/{doc['id']}/file").status_code == 200
    _ = PartnerDocument


def test_clamd_protocol_client_against_fake_server(tmp_path, clamd):
    f = tmp_path / "x.bin"
    f.write_bytes(b"halo dunia" * 10_000)  # > satu chunk
    assert scanner.clamd_scan(f) == (True, "OK")
    f.write_bytes(b"depan" + EICAR)
    assert scanner.clamd_scan(f) == (False, "Eicar-Test-Signature")


def test_production_requires_scanner():
    from app.core.config import Settings

    with pytest.raises(RuntimeError) as e:
        Settings(
            app_env="production",
            expose_demo_data=False,
            postgres_password="x" * 24,
            mail_provider="smtp",
            smtp_host="h",
            cookie_secure=True,
            demo_user_password=None,
            seed_demo_data=False,
            scan_provider="disabled",
        ).validate_runtime()
    assert "SCAN_PROVIDER" in str(e.value)


# ---------- worker & restore ----------
def test_worker_round_runs_every_step_without_failure(db):
    out = run_once(db)
    assert set(out) == {"job_id", "outbox", "scan", "purge_media", "retention"}
    assert not [v for k, v in out.items() if k != "job_id" and isinstance(v, str)]


def test_verify_media_detects_missing_tampered_and_counts_orphans(client, db, w, tmp_path):  # noqa: F811
    m = new_movement(w, w.inst)
    a = ok(upload_media(client, w, m, body=WEBM + b"A" * 100), 201)
    b = ok(upload_media(client, w, m, body=WEBM + b"B" * 100), 201)
    c = ok(upload_media(client, w, m, body=WEBM + b"C" * 100), 201)
    root = Path(get_settings().media_dir)
    rows = {k: db.get(ReferenceMedia, uuid.UUID(x["id"])) for k, x in (("a", a), ("b", b), ("c", c))}
    assert retention.verify_media(db, root) == {"checked": 4, "problems": [], "orphans": 0}  # 3 media + 1 dokumen mitra
    storage.path_for(rows["b"].storage_key).write_bytes(b"rusak")  # dirusak
    storage.path_for(rows["c"].storage_key).unlink()  # hilang
    (root / "ff").mkdir(exist_ok=True)
    (root / "ff" / ("f" * 32)).write_bytes(b"yatim")
    res = retention.verify_media(db, root)
    assert (
        {p["problem"] for p in res["problems"]} == {"sha256 tidak cocok", "berkas hilang"}
        and res["orphans"] == 1
        and res["checked"] == 4
    )
    _ = select
