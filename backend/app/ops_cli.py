"""Perintah CLI operasional (doctor, outbox, retensi, media). Output ringkas TANPA PII/secret."""

import json
import sys
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.services import backup_check, ops, outbox, retention
from app.services import media as media_svc


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def run(args, db: Session) -> int:
    c = args.cmd
    if c == "doctor":
        findings = ops.doctor(db, target=args.target, backups_dir=args.backups_dir)
        if args.json:
            _print(ops.summarize(findings))
        else:
            for sev in (ops.BLOCKER, ops.WARNING, ops.INFO):
                rows = [f for f in findings if f.severity == sev]
                print(f"\n== {sev} ({len(rows)})")
                for f in rows:
                    print(
                        f"  [{f.id}] {f.title}"
                        + (f" — {f.detail}" if f.detail else "")
                        + (f"\n      perbaikan: {f.fix}" if f.fix and sev != ops.INFO else "")
                    )
        return 1 if any(f.severity == ops.BLOCKER for f in findings) else 0
    if c == "outbox-status":
        _print(outbox.status_summary(db))
        return 0
    if c == "outbox-list":
        _print(outbox.list_rows(db, args.status))
        return 0
    if c == "outbox-requeue":
        import uuid

        ok = outbox.requeue(db, uuid.UUID(args.id))
        db.commit()
        print(
            "diantre ulang" if ok else "tidak dapat diantre ulang (bukan dead-letter / isi sudah diredaksi / tidak ada)"
        )
        return 0 if ok else 1
    if c == "outbox-purge":
        rep = outbox.purge(db, sent_days=args.sent_days, dead_days=args.dead_days, dry_run=not args.execute)
        db.commit()
        _print(rep)
        if not args.execute:
            print("\nDRY-RUN: tidak ada yang dihapus. Tambahkan --execute untuk menghapus.")
        return 0
    if c == "media-purge":
        rep = media_svc.purge_expired(db, dry_run=not args.execute)
        if args.execute:
            db.commit()
        _print({"expired": rep, "orphan_report (tidak pernah dihapus otomatis)": media_svc.orphan_report(db)})
        return 0
    if c == "retention-report":
        elig = retention.eligible_programs(db)
        from app.services import jobs

        last = jobs.last(db, "retention")
        _print(
            {
                "eligible_now": len(elig),
                "last_run": last.last_finished_at if last else None,
                "last_summary": last.last_summary if last else None,
            }
        )
        return 0
    if c == "pilot-anonymize":
        return _anonymize(args, db)
    return 2


def _anonymize(args, db: Session) -> int:
    import uuid

    before = datetime.fromisoformat(args.completed_before).replace(tzinfo=UTC) if args.completed_before else None
    if args.early and not (args.reason and args.reason.strip()):
        print("GAGAL: --early membutuhkan --reason", file=sys.stderr)
        return 2
    pid = uuid.UUID(args.program) if args.program else None
    cid = uuid.UUID(args.cohort) if args.cohort else None
    programs = retention.eligible_programs(db, program_id=pid, cohort_id=cid, completed_before=before, early=args.early)
    plan = [
        {
            "program_id": str(p.id),
            "status": p.status,
            "completed_at": p.completed_at,
            "impact": retention.impact(db, p, cid),
        }
        for p in programs
    ]
    totals = {
        k: sum(x["impact"][k] for x in plan) for k in ("survey_responses_identified", "instructor_notes", "invitations")
    }
    _print(
        {
            "mode": "EKSEKUSI" if args.execute else "DRY-RUN",
            "scope": "cohort" if cid else "program",
            "early": args.early,
            "retention_days": __import__("app.core.config", fromlist=["get_settings"])
            .get_settings()
            .pilot_retention_days,
            "programs": len(plan),
            "totals": totals,
            "detail": plan,
        }
    )
    if not args.execute:
        print(
            '\nDRY-RUN: tidak ada perubahan. Untuk mengeksekusi: --execute --operator <admin> --confirm "ANONIMKAN '
            f'{len(plan)} PROGRAM" --backup-manifest <manifest.json>'
        )
        return 0
    if not plan:
        print("Tidak ada program yang memenuhi syarat.")
        return 0
    if args.confirm != f"ANONIMKAN {len(plan)} PROGRAM":
        print(f'GAGAL: konfirmasi harus persis "ANONIMKAN {len(plan)} PROGRAM"', file=sys.stderr)
        return 2
    op = db.scalar(
        select(User).where(User.email == (args.operator or "").lower(), User.role == "admin", User.status == "active")
    )
    if not op:
        print("GAGAL: --operator harus email admin aktif", file=sys.stderr)
        return 2
    if args.accept_no_backup:
        print("PERINGATAN: dijalankan TANPA bukti backup (--accept-no-backup); tercatat di audit.", file=sys.stderr)
    else:
        if not args.backup_manifest:
            print("GAGAL: operasi destruktif butuh --backup-manifest (cadangan penuh terbaru)", file=sys.stderr)
            return 2
        from sqlalchemy import text

        cur = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
        okb, problems = backup_check.validate_manifest(
            args.backup_manifest, max_age_hours=args.max_backup_age_hours, current_revision=cur
        )
        if not okb:
            print("GAGAL: bukti backup tidak valid: " + "; ".join(problems), file=sys.stderr)
            return 2
    done, failed = [], []
    for p in programs:
        try:
            with db.begin_nested():
                counts = retention.anonymize_program(
                    db,
                    p,
                    actor=op,
                    only_cohort=cid,
                    reason=("[early] " if args.early else "") + (args.reason or "retensi manual"),
                )
                if not retention.verify_program(db, p, cid)["ok"]:
                    raise RuntimeError("verifikasi pasca-operasi gagal")
            done.append({"program_id": str(p.id), **counts})
        except Exception as exc:  # noqa: BLE001
            failed.append({"program_id": str(p.id), "error": type(exc).__name__})
    db.commit()
    _print(
        {
            "processed": len(done),
            "failed": len(failed),
            "results": done,
            "failures": failed,
            "verified": not failed,
            "backup_evidence": "dilewati (--accept-no-backup)" if args.accept_no_backup else "valid",
        }
    )
    return 1 if failed else 0
