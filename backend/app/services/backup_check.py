"""Validasi bukti backup (manifest) sebelum operasi destruktif. Tidak membaca isi cadangan."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_manifest(
    manifest_path: str, *, max_age_hours: int, current_revision: str | None
) -> tuple[bool, list[str]]:
    """Cadangan sah bila: manifest terbaca, cukup baru, revisi skema = saat ini, berkas ada & sha256 cocok."""
    problems: list[str] = []
    p = Path(manifest_path)
    try:
        doc = json.loads(p.read_text())
    except (OSError, ValueError):
        return False, ["manifest tidak dapat dibaca"]
    try:
        age_h = (
            datetime.now(UTC) - datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00"))
        ).total_seconds() / 3600
    except (KeyError, ValueError):
        return False, ["manifest tanpa created_at yang valid"]
    if age_h > max_age_hours:
        problems.append(f"cadangan terlalu lama ({age_h:.1f} jam > {max_age_hours})")
    if current_revision and doc.get("alembic_revision") != current_revision:
        problems.append("revisi skema cadangan ≠ skema saat ini")
    for key, sha in (("db_dump", "db_sha256"), ("media_tar", "media_sha256")):
        f = p.parent / doc.get(key, "")
        if not f.is_file():
            problems.append(f"berkas {key} tidak ada")
        elif sha256_file(f) != doc.get(sha):
            problems.append(f"sha256 {key} tidak cocok")
    return not problems, problems
