"""Status operasional + `doctor` (hanya-baca). Tidak mengubah state; tidak mengungkap secret/path/host internal."""

import json
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import timedelta
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import NotificationOutbox, PartnerDocument, ReferenceMedia, User
from app.services import jobs, outbox, scanner
from app.services.auth import now

BLOCKER, WARNING, INFO = "BLOCKER", "WARNING", "INFO"


@dataclass
class Finding:
    id: str
    severity: str
    title: str
    detail: str = ""
    fix: str = ""


def media_storage() -> dict:
    """Status penyimpanan media (tanpa path)."""
    root = Path(get_settings().media_dir)
    out = {"exists": root.is_dir(), "writable": False, "free_gb": None}
    if out["exists"]:
        out["writable"] = os.access(root, os.W_OK)
        out["free_gb"] = round(shutil.disk_usage(root).free / 1024**3, 1)
    return out


def head_revision() -> str | None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    return ScriptDirectory.from_config(
        Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    ).get_current_head()


def ops_status(db: Session) -> dict:
    """Ringkasan untuk admin: DB, migrasi, media, scanner, worker, outbox, email, retensi."""
    s = get_settings()
    cur = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
    w = jobs.last(db, "worker")
    age = (now() - w.heartbeat_at).total_seconds() if w and w.heartbeat_at else None
    ret = jobs.last(db, "retention")
    scan_counts = {}
    for model in (ReferenceMedia, PartnerDocument):
        for st, n in db.execute(select(model.scan_status, func.count()).group_by(model.scan_status)):
            scan_counts[st] = scan_counts.get(st, 0) + n
    return {
        "database": "ok",
        "migration": {"current": cur, "head": head_revision(), "up_to_date": cur == head_revision()},
        "media_storage": media_storage(),
        "scanner": {**scanner.health(), "status_counts": scan_counts},
        "worker": {
            "heartbeat_age_s": round(age, 1) if age is not None else None,
            "healthy": age is not None and age < max(180, s.worker_interval_s * 3),
        },
        "outbox": outbox.status_summary(db),
        "email": {"configured": s.mail_configured, "provider": s.mail_provider},
        "retention": {
            "days": s.pilot_retention_days,
            "auto_enabled": s.retention_auto_enabled,
            "last_run": ret.last_finished_at if ret else None,
            "last_summary": ret.last_summary if ret else None,
        },
    }


def _latest_backup(root: Path) -> tuple[Path, dict] | None:
    best = None
    for m in root.glob("full_*/manifest.json"):
        try:
            doc = json.loads(m.read_text())
        except (OSError, ValueError):
            continue
        if best is None or doc.get("created_at", "") > best[1].get("created_at", ""):
            best = (m.parent, doc)
    return best


def doctor(db: Session, *, target: str = "current", backups_dir: str | None = None) -> list[Finding]:
    """Periksa kesiapan deployment. `target`: current (ketat sesuai APP_ENV) | production (anggap produksi)."""
    s: Settings = get_settings()
    strict = target == "production" or s.is_production or s.app_env == "staging"
    F: list[Finding] = []

    def add(id_, sev_strict, title, detail="", fix="", sev_loose=WARNING):
        F.append(Finding(id_, sev_strict if strict else sev_loose, title, detail, fix))

    for p in s.production_problems():
        add("config." + p.split()[0].lower(), BLOCKER, p, fix="Perbaiki variabel lingkungan terkait.", sev_loose=INFO)
    if s.rate_limit_enabled:
        F.append(Finding("rate_limit", INFO, "Rate limit aktif"))
    else:
        add("rate_limit", BLOCKER, "Rate limit dimatikan", fix="Set RATE_LIMIT_ENABLED=true", sev_loose=WARNING)
    if not s.trusted_proxy_cidrs:
        add(
            "proxy",
            WARNING,
            "TRUSTED_PROXY_CIDRS kosong: semua klien dianggap berasal dari IP proxy/langsung",
            "Di belakang reverse proxy, rate limit per-IP menjadi global.",
            "Isi CIDR proxy yang MENIMPA X-Forwarded-For (docs/SECURITY_HYGIENE.md §4).",
            sev_loose=INFO,
        )
    else:
        F.append(Finding("proxy", INFO, "Proxy tepercaya dikonfigurasi", f"hops={s.trusted_proxy_hops}"))
    if strict and ("localhost" in s.public_base_url or s.public_base_url.startswith("http://")):
        F.append(
            Finding(
                "public_base_url",
                BLOCKER,
                "PUBLIC_BASE_URL bukan HTTPS publik",
                "Tautan undangan/verifikasi di email akan salah/tidak aman.",
                "Set PUBLIC_BASE_URL=https://domain",
            )
        )
    if strict and any("localhost" in o or "127.0.0.1" in o for o in s.cors_origin_list):
        F.append(Finding("cors", WARNING, "CORS_ORIGINS memuat localhost", fix="Batasi ke origin frontend produksi."))
    # email
    if s.mail_provider == "smtp" and s.smtp_host:
        F.append(
            Finding(
                "smtp",
                INFO,
                "SMTP dikonfigurasi",
                "Pengiriman nyata belum diverifikasi oleh doctor (gunakan uji mail sink / email uji).",
            )
        )
        if "localhost" in s.mail_from:
            F.append(
                Finding(
                    "mail_from",
                    WARNING,
                    "MAIL_FROM memakai domain localhost",
                    fix="Pakai pengirim dengan domain terverifikasi (SPF/DKIM).",
                )
            )
    else:
        add(
            "smtp",
            BLOCKER,
            "Email tidak dikonfigurasi (MAIL_PROVIDER≠smtp)",
            "Undangan dan notifikasi tertahan (undeliverable/dev_sink).",
            "Konfigurasikan SMTP.",
            sev_loose=WARNING,
        )
    # scanner
    sh = scanner.health()
    if not sh["enabled"]:
        add(
            "scanner",
            BLOCKER,
            "Pemindai malware nonaktif (SCAN_PROVIDER=disabled)",
            "Berkas hanya berstatus not_scanned (tidak pernah publik).",
            "SCAN_PROVIDER=clamav + jalankan ClamAV.",
            sev_loose=WARNING,
        )
    elif not sh["reachable"]:
        F.append(
            Finding(
                "scanner",
                BLOCKER,
                "ClamAV tidak terjangkau",
                "Unggahan menumpuk di karantina (fail-closed).",
                "Periksa layanan clamav (≈1 GB RAM).",
            )
        )
    else:
        F.append(Finding("scanner", INFO, "ClamAV terjangkau"))
    # database & migrasi
    try:
        cur = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
        if cur != head_revision():
            F.append(
                Finding(
                    "migration",
                    BLOCKER,
                    "Migrasi belum di head",
                    f"saat ini {cur}, head {head_revision()}",
                    "alembic upgrade head (setelah backup).",
                )
            )
        else:
            F.append(Finding("migration", INFO, "Migrasi di head", cur or ""))
    except Exception as exc:  # noqa: BLE001
        F.append(Finding("database", BLOCKER, "Database tidak dapat dibaca", type(exc).__name__))
        return F
    # media
    ms = media_storage()
    if not ms["exists"] or not ms["writable"]:
        F.append(
            Finding(
                "media",
                BLOCKER,
                "Penyimpanan media tidak ada/tidak dapat ditulis",
                fix="Pasang volume media_data dengan izin tulis untuk user aplikasi.",
            )
        )
    else:
        root = Path(s.media_dir)
        if root.stat().st_mode & 0o002:
            F.append(
                Finding(
                    "media_perm",
                    WARNING,
                    "Direktori media dapat ditulis semua pengguna (o+w)",
                    fix="chmod o-w pada volume media.",
                )
            )
        if ms["free_gb"] is not None and ms["free_gb"] < 1:
            F.append(Finding("media_space", BLOCKER, f"Ruang media tinggal {ms['free_gb']} GB"))
        elif ms["free_gb"] is not None and ms["free_gb"] < 5:
            F.append(Finding("media_space", WARNING, f"Ruang media rendah ({ms['free_gb']} GB)"))
        else:
            F.append(Finding("media", INFO, "Penyimpanan media siap", f"bebas {ms['free_gb']} GB"))
    # worker
    w = jobs.last(db, "worker")
    age = (now() - w.heartbeat_at).total_seconds() if w and w.heartbeat_at else None
    if age is None or age > max(180, s.worker_interval_s * 3):
        add(
            "worker",
            BLOCKER,
            "Worker tidak berdetak (heartbeat hilang/basi)",
            "Outbox, pemindaian, purge, dan retensi tidak berjalan.",
            "Jalankan layanan worker.",
            sev_loose=WARNING,
        )
    else:
        F.append(Finding("worker", INFO, "Worker sehat", f"heartbeat {round(age)} dtk lalu"))
    # outbox
    counts = dict(db.execute(select(NotificationOutbox.status, func.count()).group_by(NotificationOutbox.status)).all())
    if counts.get("dead"):
        F.append(
            Finding(
                "outbox_dead",
                WARNING,
                f"{counts['dead']} pesan dead-letter",
                fix="python -m app.cli outbox-list --status dead; selidiki lalu outbox-requeue.",
            )
        )
    oldest = db.scalar(
        select(func.min(NotificationOutbox.created_at)).where(
            NotificationOutbox.status.in_(["pending", "undeliverable"])
        )
    )
    if oldest and now() - oldest > timedelta(hours=1):
        F.append(
            Finding(
                "outbox_backlog",
                WARNING,
                "Ada pesan pending/undeliverable > 1 jam",
                fix="Periksa provider email dan worker.",
            )
        )
    # akun demo
    demo = db.scalar(select(func.count()).select_from(User).where(User.email.like("%@silatara.test"))) or 0
    if demo:
        add(
            "demo_accounts",
            BLOCKER,
            f"{demo} akun demo (@silatara.test) ada di database",
            "Kredensial demo bersifat publik.",
            "Jangan membawa database dev ke pilot/produksi.",
            sev_loose=INFO,
        )
    # backup
    keyf = os.environ.get("BACKUP_ENCRYPTION_KEY_FILE")
    if not keyf:
        add(
            "backup_encryption",
            BLOCKER,
            "Enkripsi backup tidak dikonfigurasi (BACKUP_ENCRYPTION_KEY_FILE)",
            fix="Buat kunci di luar repo (chmod 600) dan set variabelnya.",
            sev_loose=INFO,
        )
    elif not Path(keyf).is_file():
        F.append(Finding("backup_encryption", BLOCKER, "Berkas kunci backup tidak ditemukan"))
    elif Path(keyf).stat().st_mode & 0o077:
        F.append(Finding("backup_encryption", BLOCKER, "Izin berkas kunci backup terlalu longgar", fix="chmod 600"))
    else:
        F.append(Finding("backup_encryption", INFO, "Kunci backup terkonfigurasi (izin ketat)"))
    broot = Path(backups_dir or os.environ.get("BACKUPS_DIR", "/backups"))
    lb = _latest_backup(broot) if broot.is_dir() else None
    if lb is None:
        add(
            "backup_recent",
            BLOCKER,
            "Tidak ada cadangan penuh yang terdeteksi",
            fix="make backup-all lalu make restore-verify",
            sev_loose=INFO,
        )
    else:
        from datetime import datetime

        created = datetime.fromisoformat(lb[1]["created_at"].replace("Z", "+00:00"))
        age_h = (now() - created).total_seconds() / 3600
        enc = lb[1].get("encryption", {}).get("enabled", False)
        if age_h > 24 * 7:
            add("backup_recent", BLOCKER, f"Cadangan terakhir berumur {round(age_h / 24)} hari", sev_loose=INFO)
        elif age_h > 26:
            F.append(Finding("backup_recent", WARNING, f"Cadangan terakhir berumur {round(age_h)} jam"))
        else:
            F.append(Finding("backup_recent", INFO, f"Cadangan terakhir {round(age_h, 1)} jam lalu"))
        if not enc:
            add("backup_plaintext", BLOCKER, "Cadangan terakhir TIDAK terenkripsi", sev_loose=WARNING)
        if not lb[1].get("destination", {}).get("uploaded"):
            F.append(
                Finding(
                    "backup_offsite",
                    WARNING if strict else INFO,
                    "Cadangan belum dikirim off-site (belum ada bukti unggah terverifikasi)",
                )
            )
    F.append(
        Finding(
            "retention",
            INFO,
            f"Retensi pilot {s.pilot_retention_days} hari; otomatis={'ya' if s.retention_auto_enabled else 'tidak'}",
        )
    )
    if s.app_env == "development" and not strict:
        F.append(
            Finding(
                "env", INFO, "APP_ENV=development (evaluasi longgar; gunakan --target production untuk gerbang pilot)"
            )
        )
    return F


def summarize(findings: list[Finding]) -> dict:
    return {sev: [asdict(f) for f in findings if f.severity == sev] for sev in (BLOCKER, WARNING, INFO)}
