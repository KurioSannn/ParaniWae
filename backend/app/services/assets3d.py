"""Aset karakter 3D, urutan referensi, dan protokol penilaian (berkas di content/pencak-silat/{character,assessments}).

Hanya-baca dari repo (sumber kebenaran = berkas). Tidak ada data pengguna di sini.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from app.core.errors import ApiError
from app.services.research import _root

MOVEMENT_ID_RE = re.compile(r"^mv\.[a-z0-9]+\.[a-z0-9-]{1,100}$")


def _char_dir() -> Path:
    return _root() / "content" / "pencak-silat" / "character"


def _read(path: Path):
    try:
        return _cached(str(path), path.stat().st_mtime)
    except FileNotFoundError as e:
        raise ApiError(404, "NOT_FOUND", "Tidak ditemukan.") from e


@lru_cache(maxsize=64)
def _cached(path: str, _mtime: float):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def character() -> dict:
    d = _char_dir()
    meta = _read(d / "character.json")
    clips = _read(d / "clips.json")
    val = _read(d / "validation.json")
    checks = {c["movement_id"]: c["ok"] for c in val.get("clips", [])}
    return {
        "character": {k: meta[k] for k in ("character_id", "version", "sha256", "bytes", "format", "joint_count", "finger_joints",
                                            "units", "up_axis", "forward_axis", "license", "costume", "not_a_mascot")}
        | {"meshes": [{"name": m["name"], "features": m["features"]} for m in meta["meshes"]],
           "model_url": "/api/v1/research/character/model.glb"},
        "clips": [c | {"checks_passed": checks.get(c["movement_id"], False)} for c in clips["clips"]],
    }


def glb() -> tuple[Path, str]:
    d = _char_dir()
    meta = _read(d / "character.json")
    path = d / meta["file"]
    if not path.is_file():
        raise ApiError(404, "NOT_FOUND", "Model belum dibangun.")
    return path, meta["sha256"]


def reference(movement_id: str) -> dict:
    if not MOVEMENT_ID_RE.match(movement_id):
        raise ApiError(404, "NOT_FOUND", "Tidak ditemukan.")
    return _read(_char_dir() / "reference" / f"{movement_id}.json")


def _assess_dir() -> Path:
    return _root() / "content" / "pencak-silat" / "assessments"


def protocols() -> dict:
    items = []
    for f in sorted(_assess_dir().glob("*.protocol.json")):
        p = _read(f)
        items.append({k: p.get(k) for k in ("protocol_id", "movement_id", "protocol_version", "status", "title", "required_view",
                                            "criteria_count", "reference_id", "summary")}
                     | {"criteria_count": len(p.get("criteria", []))})
    readiness = _read(_assess_dir() / "readiness.json") if (_assess_dir() / "readiness.json").exists() else {"movements": []}
    return {"items": items, "readiness": readiness.get("movements", [])}


def protocol(movement_id: str) -> dict:
    if not MOVEMENT_ID_RE.match(movement_id):
        raise ApiError(404, "NOT_FOUND", "Tidak ditemukan.")
    for f in _assess_dir().glob("*.protocol.json"):
        p = _read(f)
        if p.get("movement_id") == movement_id:
            return p
    raise ApiError(404, "NOT_FOUND", "Belum ada protokol penilaian untuk gerakan ini.")
