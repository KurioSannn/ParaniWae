"""Anonimisasi/retensi: dry-run default, filter, konfirmasi, bukti backup, idempotensi, audit tanpa PII, kunci scheduler."""

import hashlib
import json
import threading
import uuid
from argparse import Namespace
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_engine
from app.models import AuditLog, CohortMember, InstructorNote, PilotConsent, PilotProgram, SurveyResponse
from app.ops_cli import _anonymize
from app.services import backup_check, jobs, retention
from tests.factories import uid
from tests.test_pilot import api as papi
from tests.test_pilot import as_, joined_cohort, ok, w  # noqa: F401


def args(**kw):
    base = dict(
        program=None,
        cohort=None,
        completed_before=None,
        early=False,
        reason=None,
        operator=None,
        execute=False,
        confirm=None,
        backup_manifest=None,
        max_backup_age_hours=24,
        accept_no_backup=False,
    )
    base.update(kw)
    return Namespace(cmd="pilot-anonymize", **base)


def seed(w, db, n=2, completed_days_ago=None):
    """Program dengan survei terisi + catatan instruktur + undangan; opsional ditandai selesai `completed_days_ago` hari lalu."""
    p, c, us = joined_cohort(w, n=n)
    s = ok(papi(w.client, "post", f"/programs/{p['id']}/surveys/templates", json={"kind": "feedback_learner"}), 201)
    ok(papi(w.client, "post", f"/surveys/{s['id']}/transition", json={"action": "open"}))
    for u in us:
        as_(w.client, u)
        ok(
            papi(
                w.client,
                "post",
                f"/surveys/{s['id']}/responses",
                json={"answers": {"kemudahan": 4, "materi": 5, "kamera": "Tidak mencoba", "saran": "ok"}},
            ),
            201,
        )
        ok(papi(w.client, "put", f"/me/programs/{p['id']}/consents", json={"research_aggregate": True}))
    as_(w.client, w.ins)
    ok(
        papi(
            w.client,
            "post",
            f"/cohorts/{c['id']}/notes",
            json={"participant_user_id": str(us[0].id), "note": "catatan privat"},
        ),
        201,
    )
    prog = db.get(PilotProgram, uuid.UUID(p["id"]))
    if completed_days_ago is not None:
        prog.status, prog.completed_at = "completed", datetime.now(UTC) - timedelta(days=completed_days_ago)
        db.flush()
    return prog, c, us, s


def manifest(tmp_path, *, age_h=1, rev=None, tamper=False):
    d = tmp_path / "bk"
    d.mkdir(exist_ok=True)
    (d / "db.dump.enc").write_bytes(b"dump")
    (d / "media.tar.enc").write_bytes(b"tar")
    m = {
        "created_at": (datetime.now(UTC) - timedelta(hours=age_h)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "alembic_revision": rev,
        "db_dump": "db.dump.enc",
        "db_sha256": hashlib.sha256(b"dump").hexdigest(),
        "media_tar": "media.tar.enc",
        "media_sha256": hashlib.sha256(b"XXX" if tamper else b"tar").hexdigest(),
    }
    (d / "manifest.json").write_text(json.dumps(m))
    return str(d / "manifest.json")


def head(db):
    return db.execute(text("SELECT version_num FROM alembic_version")).scalar()


# ---------- dry-run & kelayakan ----------
def test_dry_run_is_default_changes_nothing_and_prints_counts_only(w, db, capsys):
    prog, c, us, s = seed(w, db, completed_days_ago=get_settings().pilot_retention_days + 5)
    rc = _anonymize(args(program=str(prog.id)), db)
    out = capsys.readouterr().out
    assert rc == 0 and "DRY-RUN" in out and '"survey_responses_identified": 2' in out and '"instructor_notes": 1' in out
    assert "catatan privat" not in out and us[0].email not in out and us[0].display_name not in out  # tanpa PII
    assert all(r.user_id is not None for r in db.scalars(select(SurveyResponse)).all() if str(r.survey_id) == s["id"])
    assert prog.anonymized_at is None


def test_only_programs_past_retention_are_eligible_unless_early_with_reason(w, db, capsys):
    recent, *_ = seed(w, db, completed_days_ago=10)  # belum melewati 365 hari
    assert retention.eligible_programs(db, program_id=recent.id) == []
    assert retention.eligible_programs(db, program_id=recent.id, early=True) == [recent]
    assert _anonymize(args(program=str(recent.id), early=True), db) == 2  # --early tanpa --reason ditolak
    assert "membutuhkan --reason" in capsys.readouterr().err
    # program yang belum selesai (active) tidak pernah eligible secara terjadwal
    p, c, us = joined_cohort(w, n=1)
    assert retention.eligible_programs(db, program_id=uuid.UUID(p["id"])) == []


def test_filters_by_completed_before_and_cohort_scope(w, db):
    old, c, us, s = seed(w, db, completed_days_ago=get_settings().pilot_retention_days + 100)
    assert (
        retention.eligible_programs(
            db, completed_before=datetime.now(UTC) - timedelta(days=get_settings().pilot_retention_days + 200)
        )
        == []
    )
    assert old in retention.eligible_programs(db, completed_before=datetime.now(UTC))
    assert old in retention.eligible_programs(db, cohort_id=uuid.UUID(c["id"]))
    assert retention.eligible_programs(db, cohort_id=uuid.uuid4()) == []


# ---------- eksekusi: pengaman ----------
def test_execute_requires_exact_confirmation_admin_operator_and_valid_backup(w, db, tmp_path, capsys):
    prog, c, us, s = seed(w, db, completed_days_ago=get_settings().pilot_retention_days + 5)
    pid = str(prog.id)
    ex = dict(program=pid, execute=True, operator=w.adm.email)
    assert _anonymize(args(**ex), db) == 2 and "konfirmasi" in capsys.readouterr().err  # tanpa --confirm
    conf = "ANONIMKAN 1 PROGRAM"
    assert _anonymize(args(**ex, confirm="ya"), db) == 2
    assert _anonymize(args(**{**ex, "operator": w.ins.email}, confirm=conf), db) == 2  # bukan admin
    assert "admin aktif" in capsys.readouterr().err
    capsys.readouterr()
    assert (
        _anonymize(args(**ex, confirm=conf), db) == 2 and "--backup-manifest" in capsys.readouterr().err
    )  # tanpa bukti backup
    for kw, msg in (
        ({"age_h": 100}, "terlalu lama"),
        ({"rev": "revisi-lama"}, "revisi skema"),
        ({"tamper": True}, "sha256"),
    ):
        m = manifest(tmp_path, rev=kw.pop("rev", head(db)), **kw)
        assert _anonymize(args(**ex, confirm=conf, backup_manifest=m), db) == 2
        assert msg in capsys.readouterr().err
    assert all(
        r.user_id is not None for r in db.scalars(select(SurveyResponse)).all() if str(r.survey_id) == s["id"]
    )  # belum ada perubahan
    assert prog.anonymized_at is None


def test_execute_anonymizes_verifies_audits_operator_and_is_idempotent(w, db, tmp_path, capsys):
    prog, c, us, s = seed(w, db, completed_days_ago=get_settings().pilot_retention_days + 5)
    usage_before = db.scalar(select(text("count(*)")).select_from(CohortMember))
    consents_before = db.scalar(select(text("count(*)")).select_from(PilotConsent))
    m = manifest(tmp_path, rev=head(db))
    cmd = args(
        program=str(prog.id), execute=True, operator=w.adm.email, confirm="ANONIMKAN 1 PROGRAM", backup_manifest=m
    )
    assert _anonymize(cmd, db) == 0
    summary = capsys.readouterr().out
    assert '"processed": 1' in summary and '"verified": true' in summary and "catatan privat" not in summary
    mine = [r for r in db.scalars(select(SurveyResponse)).all() if str(r.survey_id) == s["id"]]
    assert len(mine) == 2 and all(r.user_id is None for r in mine)  # agregat tetap, identitas hilang
    assert not db.scalars(select(InstructorNote).where(InstructorNote.cohort_id == uuid.UUID(c["id"]))).all()
    assert retention.verify_program(db, prog)["ok"] and prog.anonymized_at
    # data penggunaan & persetujuan TIDAK ikut dihapus (kebijakan existing; lihat ADR-0004)
    assert db.scalar(select(text("count(*)")).select_from(CohortMember)) == usage_before
    assert db.scalar(select(text("count(*)")).select_from(PilotConsent)) == consents_before
    a = db.scalar(
        select(AuditLog)
        .where(AuditLog.action == "pilot.anonymize", AuditLog.entity_id == str(prog.id))
        .order_by(AuditLog.created_at.desc())
    )
    assert (
        a.actor_user_id == w.adm.id
        and a.detail["responses_anonymized"] == 2
        and a.detail["notes_deleted"] == 1
        and a.detail["scope"] == "program"
    )
    assert all(u.email not in json.dumps(a.detail, default=str) for u in us)
    # idempoten: tidak lagi eligible; menjalankan ulang aman
    assert retention.eligible_programs(db, program_id=prog.id) == []
    assert retention.anonymize_program(db, prog) == {
        "responses_anonymized": 0,
        "notes_deleted": 0,
        "invitations_deleted": 0,
    }


def test_cohort_scoped_anonymization_leaves_program_marker_untouched(w, db):
    prog, c, us, s = seed(w, db, completed_days_ago=get_settings().pilot_retention_days + 5)
    counts = retention.anonymize_program(
        db, prog, only_cohort=uuid.UUID(c["id"]), reason="permintaan penghapusan cohort"
    )
    assert (
        counts["responses_anonymized"] == 2 and prog.anonymized_at is None
    )  # program belum dianggap selesai dianonimkan seluruhnya


def test_scheduled_retention_runs_with_lock_report_and_interval(w, db):
    seed(w, db, completed_days_ago=get_settings().pilot_retention_days + 5)
    rep = retention.run_scheduled(db, force=True)
    assert rep == {"eligible": 1, "processed": 1, "failed": 0}  # laporan: jumlah saja
    last = jobs.last(db, "retention")
    assert last.last_summary == rep and last.last_status == "ok"
    assert retention.run_scheduled(db) == {"skipped": "belum jatuh tempo"}


def test_retention_job_cannot_run_in_parallel_advisory_lock():
    """Dua koneksi nyata: yang kedua tidak mendapat kunci selama yang pertama menahannya."""
    key = f"retention-test-{uuid.uuid4().hex}"
    with Session(get_engine()) as a, Session(get_engine()) as b:
        assert jobs.try_lock(a, key) is True
        assert jobs.try_lock(b, key) is False
        a.rollback()  # kunci tingkat-transaksi dilepas otomatis
        assert jobs.try_lock(b, key) is True


# ---------- validasi manifest ----------
def test_backup_manifest_validation(tmp_path):
    ok_, probs = backup_check.validate_manifest(manifest(tmp_path, rev="r1"), max_age_hours=24, current_revision="r1")
    assert ok_ and probs == []
    assert (
        backup_check.validate_manifest(str(tmp_path / "tidak-ada.json"), max_age_hours=24, current_revision="r1")[0]
        is False
    )
    assert not backup_check.validate_manifest(
        manifest(tmp_path, rev="r1", age_h=48), max_age_hours=24, current_revision="r1"
    )[0]
    assert not backup_check.validate_manifest(manifest(tmp_path, rev="r2"), max_age_hours=24, current_revision="r1")[0]


_ = (threading, uid)
