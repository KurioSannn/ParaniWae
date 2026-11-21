"""Retensi, anonimisasi, dan verifikasi media (backup/restore). Lihat docs/PILOT_PRIVACY_RETENTION.md."""

import hashlib
from datetime import timedelta
from pathlib import Path

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    CohortInvitation,
    CohortMember,
    InstructorNote,
    PartnerDocument,
    PilotCohort,
    PilotProgram,
    ReferenceMedia,
    SurveyResponse,
)
from app.services import audit
from app.services.auth import now


def _cohort_ids(db: Session, program: PilotProgram, only_cohort=None) -> list:
    stmt = select(PilotCohort.id).where(PilotCohort.program_id == program.id)
    if only_cohort:
        stmt = stmt.where(PilotCohort.id == only_cohort)
    return list(db.scalars(stmt))


def impact(db: Session, program: PilotProgram, only_cohort=None) -> dict:
    """Ringkasan data terdampak — HANYA jumlah (tanpa identitas/isi)."""
    cids = _cohort_ids(db, program, only_cohort)
    if not cids:
        return {"survey_responses_identified": 0, "instructor_notes": 0, "invitations": 0}
    return {
        "survey_responses_identified": db.scalar(
            select(func.count())
            .select_from(SurveyResponse)
            .where(SurveyResponse.cohort_id.in_(cids), SurveyResponse.user_id.is_not(None))
        )
        or 0,
        "instructor_notes": db.scalar(
            select(func.count()).select_from(InstructorNote).where(InstructorNote.cohort_id.in_(cids))
        )
        or 0,
        "invitations": db.scalar(
            select(func.count()).select_from(CohortInvitation).where(CohortInvitation.cohort_id.in_(cids))
        )
        or 0,
    }


def anonymize_program(
    db: Session, program: PilotProgram, *, actor=None, only_cohort=None, reason: str | None = None
) -> dict:
    """Anonimkan data survei (`user_id`->NULL; agregat tetap), hapus catatan instruktur & undangan. IDEMPOTEN.
    Cakupan: seluruh program atau satu cohort. Audit memuat operator + jumlah saja (tanpa data pribadi).
    Yang SENGAJA tetap (kebijakan existing): keanggotaan cohort, progres pelajaran, metadata sesi latihan (terikat akun,
    dihapus bersama akun), dan catatan persetujuan opsional — lihat docs/adr/0004-pilot-data-lifecycle.md."""
    cids = _cohort_ids(db, program, only_cohort)
    res = (
        db.execute(
            update(SurveyResponse)
            .where(SurveyResponse.cohort_id.in_(cids), SurveyResponse.user_id.is_not(None))
            .values(user_id=None)
        )
        if cids
        else None
    )
    notes = db.execute(delete(InstructorNote).where(InstructorNote.cohort_id.in_(cids))).rowcount if cids else 0
    invs = db.execute(delete(CohortInvitation).where(CohortInvitation.cohort_id.in_(cids))).rowcount if cids else 0
    if not only_cohort:
        program.anonymized_at = now()
    counts = {"responses_anonymized": res.rowcount if res else 0, "notes_deleted": notes, "invitations_deleted": invs}
    audit.record(
        db,
        actor=actor,
        action="pilot.anonymize",
        entity_type="pilot_program",
        entity_id=program.id,
        detail={**counts, "scope": "cohort" if only_cohort else "program", "reason": (reason or "")[:200] or None},
        request_id=None,
    )
    return counts


def verify_program(db: Session, program: PilotProgram, only_cohort=None) -> dict:
    """Verifikasi pasca-operasi: tidak boleh tersisa identitas pada data yang dianonimkan."""
    i = impact(db, program, only_cohort)
    return {"ok": all(v == 0 for v in i.values()), "remaining": i}


def eligible_programs(
    db: Session, *, program_id=None, cohort_id=None, completed_before=None, early: bool = False
) -> list:
    """Program yang memenuhi aturan retensi (selesai + PILOT_RETENTION_DAYS) dan belum dianonimkan.
    `early=True` = di luar jadwal retensi (keputusan manual eksplisit; dicatat di audit bersama alasan)."""
    stmt = select(PilotProgram).where(PilotProgram.anonymized_at.is_(None) if not cohort_id else True)
    if program_id:
        stmt = stmt.where(PilotProgram.id == program_id)
    if cohort_id:
        stmt = stmt.where(PilotProgram.id.in_(select(PilotCohort.program_id).where(PilotCohort.id == cohort_id)))
    cutoff = now() - timedelta(days=get_settings().pilot_retention_days)
    if not early:
        stmt = stmt.where(
            PilotProgram.status.in_(["completed", "archived"]),
            PilotProgram.completed_at.is_not(None),
            PilotProgram.completed_at < cutoff,
        )
    if completed_before is not None:
        stmt = stmt.where(PilotProgram.completed_at.is_not(None), PilotProgram.completed_at < completed_before)
    return list(db.scalars(stmt.order_by(PilotProgram.completed_at)))


def run_retention(db: Session) -> list:
    """Anonimkan program `completed` yang melewati PILOT_RETENTION_DAYS (jalur otomatis worker)."""
    done = []
    for p in eligible_programs(db):
        anonymize_program(db, p, reason="retensi terjadwal")
        done.append(p.id)
    return done


def run_scheduled(db: Session, *, interval_hours: int = 24, force: bool = False) -> dict:
    """Pekerjaan retensi terjadwal dengan KUNCI: satu worker saja; tidak berjalan lebih sering dari `interval_hours`.
    Laporan: jumlah eligible / diproses / gagal (tanpa PII)."""
    from app.services import jobs

    if not jobs.try_lock(db, "retention"):
        db.rollback()
        return {"skipped": "dikunci worker lain"}
    last = jobs.last(db, "retention")
    if (
        not force
        and last
        and last.last_finished_at
        and (now() - last.last_finished_at) < timedelta(hours=interval_hours)
    ):
        db.rollback()
        return {"skipped": "belum jatuh tempo"}
    started = now()
    elig = eligible_programs(db)
    processed, failed = 0, 0
    for p in elig:
        try:
            with db.begin_nested():
                anonymize_program(db, p, reason="retensi terjadwal")
                if not verify_program(db, p)["ok"]:
                    raise RuntimeError("verifikasi pasca-anonimisasi gagal")
            processed += 1
        except Exception:  # noqa: BLE001
            failed += 1
    summary = {"eligible": len(elig), "processed": processed, "failed": failed}
    jobs.record(db, "retention", started=started, status="ok" if not failed else "partial", summary=summary)
    return summary


def verify_media(db: Session, root: Path) -> dict:
    """Bandingkan baris DB dengan berkas di `root` (struktur <2hex>/<key>): ada + sha256 cocok. Untuk restore-verify."""
    problems, checked = [], 0
    for model, label in ((ReferenceMedia, "reference_media"), (PartnerDocument, "partner_documents")):
        for r in db.scalars(select(model)):
            if getattr(r, "scan_status", "") in {"infected"}:
                continue
            checked += 1
            candidates = [root / r.storage_key[:2] / r.storage_key, root / ".quarantine" / r.storage_key]
            f = next((p for p in candidates if p.exists()), None)
            if not f:
                problems.append({"table": label, "id": str(r.id), "problem": "berkas hilang"})
                continue
            h = hashlib.sha256()
            with open(f, "rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    h.update(chunk)
            if h.hexdigest() != r.sha256:
                problems.append({"table": label, "id": str(r.id), "problem": "sha256 tidak cocok"})
    known = {r for (r,) in db.execute(select(ReferenceMedia.storage_key))} | {
        r for (r,) in db.execute(select(PartnerDocument.storage_key))
    }
    orphans = [
        p.name
        for p in root.glob("*/*")
        if p.is_file() and not p.name.endswith(".part") and p.name not in known and p.parent.name != ".quarantine"
    ]
    return {"checked": checked, "problems": problems, "orphans": len(orphans)}


_ = CohortMember
