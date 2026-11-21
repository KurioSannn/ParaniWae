"""Importer konten riset: validasi, DRY-RUN tanpa efek, idempoten, tidak pernah menerbitkan, menghormati alur review."""

import copy
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.content_import import ContentError, apply_bundle, load_bundle, run_import, validate_bundle
from app.models import (
    AuditLog,
    Course,
    CulturalTradition,
    Lesson,
    LessonMaterial,
    Movement,
    MovementDocument,
    MovementPhase,
    Partner,
)

SOURCES = {
    "schema": "silatara.sources/v1",
    "sources": [
        {
            "id": "src.uji.2005",
            "type": "academic_journal",
            "title": "Sumber Uji",
            "author_or_publisher": "Penulis Uji",
            "year": 2005,
            "url": "https://contoh.invalid/a",
            "read_status": "full_text",
        },
        {
            "id": "src.uji.cuplikan",
            "type": "academic_journal",
            "title": "Cuplikan",
            "author_or_publisher": "X",
            "year": 2020,
            "url": "https://contoh.invalid/b",
            "read_status": "search_snippet",
        },
    ],
}
COMMON = {
    "schema": "silatara.common/v1",
    "traditions": [
        {
            "id": "trd.uji",
            "slug": "tradisi-uji-impor",
            "name": "Tradisi Uji",
            "local_name": None,
            "region": "Uji",
            "public_summary": "Ringkas.",
            "access_scope": "restricted",
            "source_ids": ["src.uji.2005"],
            "content_status": "draft",
        }
    ],
    "editorial_partner": {
        "slug": "silatara-tim-editorial-internal",
        "name": "Tim Editorial SILATARA (internal — bukan mitra budaya)",
        "partner_type": "institution",
        "official_description": "Internal.",
        "decision_ref": "docs/adr/0006",
    },
    "safety": {
        "space": "2x2 m",
        "surface": "rata",
        "equipment": "tidak ada",
        "stop_when": ["nyeri"],
        "stop_basis": "editorial",
        "general_limits": "bukan pengganti pelatih",
        "warmup": "ringan",
    },
    "landmark_groups": {"lower_body": ["left_hip", "right_hip"], "upper_body": ["left_shoulder"], "head": ["nose"]},
    "anatomy_missing_text": "Tidak dirinci sumber.",
}


def movement(slug="gerak-a", **over):
    mid = f"mv.uji.{slug}"
    m = {
        "id": mid, "slug": slug, "names": {"primary": f"Gerak {slug}", "local": None, "aliases": [], "pronunciation": None},
        "category": "kuda_kuda", "level": "beginner", "safety_class": "solo_beginner", "solo_form_status": "documented_solo",
        "content_status": "draft", "evidence_tier": "research_supported", "instructor_validation": "not_validated", "permission_status": "parafrasa",
        "cultural_context": {"context": {"ref": "shared_context.def"}, "purpose": {"text": "Tujuan.", "source_ids": ["src.uji.2005"]}, "meaning": {"text": "-", "basis": "gap"}, "terminology": [], "variants": [], "differs_from": []},
        "prerequisites": {"abilities": "-", "physical_prep": "-", "space_ref": "common.safety.space", "surface_ref": "common.safety.surface", "equipment_ref": "common.safety.equipment", "limits_ref": "common.safety.general_limits"},
        "anatomy": {"knees": {"text": "Sedikit ditekuk.", "basis": "source", "source_ids": ["src.uji.2005"]}},
        "phases": [
            {"id": f"{mid}#p1", "order": 1, "name": "Awal", "start_position": "Tegak", "change": "-", "body_parts": [], "direction": "-", "end_position": "Tegak", "mistakes": [], "safety": None, "tempo": None, "keyframe_ref": None, "basis": "source", "source_ids": ["src.uji.2005"], "locator": "hlm. 1"},
            {"id": f"{mid}#p2", "order": 2, "name": "Turun", "start_position": "Tegak", "change": "Lutut ditekuk", "body_parts": ["lutut"], "direction": "turun", "end_position": "Rendah", "mistakes": [], "safety": "pelan", "tempo": None, "keyframe_ref": None, "basis": "source", "source_ids": ["src.uji.2005"], "locator": "hlm. 2"},
        ],
        "practice": {"start": "-", "sequence": "-", "tempo": {"text": "pelan", "basis": "editorial_unvalidated"}, "repetitions": {"text": "3", "basis": "editorial_unvalidated"}, "easier": "-", "progression": "-", "stop_when_ref": "common.safety.stop_when", "cooldown": "-"},
        "common_mistakes": [], "common_mistakes_gap": "-",
        "references": [{"source_id": "src.uji.2005", "locator": "hlm. 1–2", "supports": "uraian"}],
        "gaps": [], "landmarks": ["lower_body"],
        "animation": {"animation_id": f"anim.uji.{slug}.v1", "status": "needs_reference", "needs": "butuh referensi"},
    }  # fmt: skip
    if "slug_field" in over:
        m["slug"] = over.pop("slug_field")
    m.update(over)
    return m


def write_repo(root: Path, movements=None, lessons_over=None):
    c = root / "content" / "pencak-silat"
    for sub in ("catalog", "movements", "curricula", "lessons", "animations"):
        (c / sub).mkdir(parents=True, exist_ok=True)
    (root / "research" / "pencak-silat" / "sources").mkdir(parents=True, exist_ok=True)
    (root / "research" / "pencak-silat" / "sources" / "sources.json").write_text(json.dumps(SOURCES))
    (c / "catalog" / "common.json").write_text(json.dumps(COMMON))
    mvs = movements if movements is not None else [movement("gerak-a"), movement("gerak-b")]
    (c / "movements" / "uji.json").write_text(
        json.dumps(
            {
                "schema": "silatara.movements/v1",
                "tradition_id": "trd.uji",
                "shared_context": {"def": {"text": "Definisi.", "source_ids": ["src.uji.2005"]}},
                "movements": mvs,
            }
        )
    )
    for m in mvs:
        d = c / "animations" / m["id"]
        d.mkdir(exist_ok=True)
        (d / "keyframes.json").write_text(
            json.dumps(
                {
                    "animation_id": m["animation"]["animation_id"],
                    "movement_id": m["id"],
                    "animation_status": m["animation"]["status"],
                    "needs": "x",
                }
            )
        )
    course = {
        "schema": "silatara.curriculum/v1", "id": "crs.uji", "slug": "kursus-uji-impor", "tradition_id": "trd.uji", "title": "Kursus Uji", "summary": "Ringkas",
        "level": "beginner", "estimated_minutes": 30, "safety_notes": "aman", "content_status": "draft", "instructor_validation": "not_validated",
        "source_ids": ["src.uji.2005"], "modules": [{"id": "crs.uji.m01", "order": 1, "title": "Modul 1", "summary": "-"}],
    }  # fmt: skip
    (c / "curricula" / "crs.uji.json").write_text(json.dumps(course))
    lesson = {
        "id": "crs.uji.l01", "module_id": "crs.uji.m01", "order": 1, "slug": "pelajaran-satu", "title": "Pelajaran 1", "description": "Deskripsi",
        "objectives": ["tujuan"], "prior_competence": "-", "duration_min": 10, "equipment": "-", "space": "-", "safety_briefing": "aman",
        "theory": "Teori.", "cultural_explanation": "Budaya.", "movement_ids": [m["id"] for m in mvs], "primary_movement_id": mvs[0]["id"] if mvs else None,
        "practice_steps": ["langkah"], "summary": "Ringkas", "reflection": ["?"],
        "quiz": [{"q": "?", "options": ["a", "b"], "answer_index": 1, "source_id": "src.uji.2005"}],
        "references": [{"source_id": "src.uji.2005", "locator": "hlm. 1"}],
    }  # fmt: skip
    lesson.update(lessons_over or {})
    (c / "lessons" / "crs.uji.json").write_text(
        json.dumps({"schema": "silatara.lessons/v1", "course_id": "crs.uji", "lessons": [lesson]})
    )
    return root


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


# ---------------------------------------------------------------- validasi
def test_valid_bundle_has_no_errors(tmp_path):
    assert validate_bundle(load_bundle(write_repo(tmp_path))) == []


@pytest.mark.parametrize(
    "over, needle",
    [
        ({"instructor_validation": "validated"}, "validasi instruktur"),
        ({"content_status": "published"}, "content_status"),
        ({"safety_class": "aman"}, "safety_class"),
        ({"solo_form_status": "inferred_not_documented"}, "bentuk solo"),
        ({"references": [{"source_id": "src.tidak-ada", "locator": "-", "supports": "-"}]}, "source_id tak dikenal"),
        ({"references": [{"source_id": "src.uji.cuplikan", "locator": "-", "supports": "-"}]}, "search_snippet"),
        ({"references": []}, "wajib memiliki rujukan"),
        ({"slug_field": "beda"}, "slug harus sama"),
    ],
)
def test_validation_rejects_bad_movement(tmp_path, over, needle):
    errs = validate_bundle(load_bundle(write_repo(tmp_path, [movement("gerak-a", **over)])))
    assert any(needle in e for e in errs), errs


def test_validation_rejects_bad_phase_ids_and_unresolvable_refs(tmp_path):
    m = movement("gerak-a")
    m["phases"][1]["id"] = "mv.uji.gerak-a#p5"
    m["cultural_context"]["context"] = {"ref": "shared_context.tidak-ada"}
    errs = validate_bundle(load_bundle(write_repo(tmp_path, [m])))
    assert any("fase ke-2" in e for e in errs) and any("ref tidak ditemukan" in e for e in errs)


def test_validation_rejects_lesson_mixing_traditions_and_bad_quiz(tmp_path):
    errs = validate_bundle(
        load_bundle(
            write_repo(
                tmp_path,
                lessons_over={
                    "movement_ids": ["mv.lain.gerak"],
                    "primary_movement_id": None,
                    "quiz": [{"q": "?", "options": ["a"], "answer_index": 3, "source_id": "src.uji.2005"}],
                },
            )
        )
    )
    assert any("gerakan tak dikenal" in e for e in errs) and any("kunci kuis" in e for e in errs)


def test_validation_checks_animation_folder_consistency(tmp_path):
    m = movement("gerak-a", animation={"animation_id": "anim.uji.gerak-a.v1", "status": "generated"})
    root = write_repo(tmp_path, [m])
    # keyframes ditulis write_repo dengan status yang sama, tetapi tanpa keyframe -> fase merujuk kf yang tidak ada
    m["phases"][0]["keyframe_ref"] = "kf-1"
    (root / "content/pencak-silat/movements/uji.json").write_text(
        json.dumps(
            {
                "schema": "silatara.movements/v1",
                "tradition_id": "trd.uji",
                "shared_context": {"def": {"text": "D"}},
                "movements": [m],
            }
        )
    )
    errs = validate_bundle(load_bundle(root))
    assert any("keyframe_ref kf-1" in e for e in errs)


# ---------------------------------------------------------------- impor
def test_dry_run_reports_but_writes_nothing(db, tmp_path):
    root = write_repo(tmp_path)
    before = {
        mdl: count(db, mdl)
        for mdl in (Partner, CulturalTradition, Movement, MovementDocument, Course, Lesson, AuditLog)
    }
    out = run_import(db, root, execute=False)
    assert out["mode"] == "DRY-RUN"
    assert out["counts"]["movement"] == {"create": 2} and out["counts"]["lesson"] == {"create": 1}
    after = {mdl: count(db, mdl) for mdl in before}
    assert before == after  # tidak ada baris tersisa


def test_execute_creates_drafts_only_never_publishes_and_is_idempotent(db, tmp_path):
    root = write_repo(tmp_path)
    first = run_import(db, root, execute=True)
    assert first["counts"]["movement"] == {"create": 2} and first["counts"]["movement_document"] == {"create": 2}
    trd = db.scalar(select(CulturalTradition).where(CulturalTradition.slug == "tradisi-uji-impor"))
    mvs = db.scalars(select(Movement).where(Movement.tradition_id == trd.id)).all()
    assert len(mvs) == 2
    for m in mvs:
        assert m.status == "draft" and m.practice_mode == "not_for_practice" and m.assessment_enabled is False
        assert m.published_document_id is None and m.is_demo is False
        doc = db.scalar(select(MovementDocument).where(MovementDocument.movement_id == m.id))
        assert (
            doc.status == "draft"
            and doc.version_no == 1
            and doc.license_type is None
            and doc.author_declaration is False
        )
        # teks pembaca tanpa label internal; status & dasar konten tersimpan di kolom, bukan di teks (ADR-0008)
        assert doc.content_basis == "source_backed" and m.content_basis == "source_backed"
        assert "Rujukan:" in doc.description and doc.source_citation and "DRAF" not in doc.description
        assert [
            p.order_index
            for p in db.scalars(
                select(MovementPhase).where(MovementPhase.document_id == doc.id).order_by(MovementPhase.order_index)
            )
        ] == [0, 1]
    partner = db.scalar(select(Partner).where(Partner.slug == "silatara-tim-editorial-internal"))
    assert (
        partner.verification_status == "draft" and partner.public_listing_consent is False and partner.status == "draft"
    )
    course = db.scalar(select(Course).where(Course.slug == "kursus-uji-impor"))
    assert course.status == "draft" and course.published_at is None
    lesson = db.scalar(select(Lesson).where(Lesson.course_id == course.id))
    assert lesson.status == "draft" and lesson.movement_id is not None
    titles = [
        x.title
        for x in db.scalars(
            select(LessonMaterial).where(LessonMaterial.lesson_id == lesson.id).order_by(LessonMaterial.order_index)
        )
    ]
    assert titles == ["Materi teori", "Penjelasan budaya", "Kuis pemahaman teori", "Rujukan"]
    assert db.scalar(select(AuditLog).where(AuditLog.action == "content.import"))
    # idempoten: menjalankan ulang tidak membuat duplikat dan tidak mengubah apa pun
    snap = {
        mdl: count(db, mdl)
        for mdl in (
            Movement,
            MovementDocument,
            MovementPhase,
            Course,
            Lesson,
            LessonMaterial,
            Partner,
            CulturalTradition,
        )
    }
    second = run_import(db, root, execute=True)
    assert all(set(v) == {"unchanged"} for v in second["counts"].values()), second["counts"]
    assert snap == {mdl: count(db, mdl) for mdl in snap}


def test_changed_content_updates_draft_in_place(db, tmp_path):
    root = write_repo(tmp_path)
    run_import(db, root, execute=True)
    m = movement("gerak-a")
    m["phases"][1]["change"] = "Lutut ditekuk lebih dalam"
    write_repo(tmp_path, [m, movement("gerak-b")])
    out = run_import(db, root, execute=True)
    assert out["counts"]["movement_document"] == {"update": 1, "unchanged": 1}
    mv = db.scalar(select(Movement).where(Movement.slug == "gerak-a", Movement.review_note.like("Impor%")))
    docs = db.scalars(select(MovementDocument).where(MovementDocument.movement_id == mv.id)).all()
    assert len(docs) == 1 and "pembaruan isi draf" in docs[0].changelog


def test_reviewed_content_is_never_overwritten(db, tmp_path):
    root = write_repo(tmp_path)
    run_import(db, root, execute=True)
    mv = db.scalar(select(Movement).where(Movement.slug == "gerak-a", Movement.review_note.like("Impor%")))
    doc = db.scalar(select(MovementDocument).where(MovementDocument.movement_id == mv.id))
    doc.status = "pending_review"  # kurator sedang meninjau
    db.flush()
    m = movement("gerak-a")
    m["phases"][1]["change"] = "Teks baru"
    write_repo(tmp_path, [m, movement("gerak-b")])
    out = run_import(db, root, execute=True)
    assert out["counts"]["movement_document"]["blocked_review"] == 1
    db.refresh(doc)
    assert doc.status == "pending_review"
    assert "Teks baru" not in " ".join(
        p.instruction for p in db.scalars(select(MovementPhase).where(MovementPhase.document_id == doc.id))
    )


def test_published_version_gets_new_draft_version_not_mutation(db, tmp_path):
    root = write_repo(tmp_path)
    run_import(db, root, execute=True)
    mv = db.scalar(select(Movement).where(Movement.slug == "gerak-b", Movement.review_note.like("Impor%")))
    doc = db.scalar(select(MovementDocument).where(MovementDocument.movement_id == mv.id))
    # simulasikan versi yang sudah terbit (demo agar lolos constraint review) — importer tidak boleh menyentuhnya
    doc.is_demo, doc.status, doc.published_at = True, "published", datetime.now(UTC)
    db.flush()
    m = movement("gerak-b")
    m["phases"][0]["change"] = "Berubah"
    write_repo(tmp_path, [movement("gerak-a"), m])
    out = run_import(db, root, execute=True)
    assert out["counts"]["movement_document"].get("new_version") == 1
    docs = db.scalars(
        select(MovementDocument).where(MovementDocument.movement_id == mv.id).order_by(MovementDocument.version_no)
    ).all()
    assert [d.status for d in docs] == ["published", "draft"] and docs[1].version_no == 2


def test_invalid_bundle_aborts_before_any_write(db, tmp_path):
    root = write_repo(tmp_path, [movement("gerak-a", instructor_validation="validated")])
    n = count(db, Movement)
    with pytest.raises(ContentError):
        run_import(db, root, execute=True)
    assert count(db, Movement) == n


def test_operator_must_be_admin_or_curator(db, tmp_path):
    with pytest.raises(ContentError):
        run_import(db, write_repo(tmp_path), execute=True, operator_email="tidak-ada@contoh.invalid")


def test_apply_bundle_never_writes_non_draft_status(db, tmp_path):
    b = load_bundle(write_repo(tmp_path))
    bad = copy.deepcopy(b)
    apply_bundle(db, bad)
    for mdl in (Movement, MovementDocument, Course, Lesson, CulturalTradition):
        assert set(
            db.scalars(
                select(mdl.status).where(mdl.review_note.like("Impor%") if hasattr(mdl, "review_note") else True)
            ).all()
        ) <= {"draft"}


# ---------------------------------------------------------------- konten nyata repo (opsional: butuh mount /repo)
REPO = Path(os.environ.get("SILATARA_REPO", "/repo"))


@pytest.mark.skipif(
    not (REPO / "content" / "pencak-silat").is_dir(), reason="repo konten tidak di-mount (set SILATARA_REPO)"
)
def test_real_repository_content_is_valid_and_imports_as_drafts(db):
    b = load_bundle(REPO)
    assert validate_bundle(b) == []
    out = run_import(db, REPO, execute=False)
    assert out["counts"]["movement"].get("create", 0) + out["counts"]["movement"].get("unchanged", 0) + out["counts"][
        "movement"
    ].get("update", 0) == len(b.movements)


# ---------------------------------------------------------------- publikasi editorial (ADR-0008)
def test_publish_requires_non_demo_editorial_operator(db, tmp_path):
    root = write_repo(tmp_path)
    with pytest.raises(ContentError):
        run_import(db, root, execute=True, publish=True)  # tanpa operator
    from tests.factories import make_user

    demo = make_user(db, role="curator")
    demo.email = f"demo-kurator-{demo.id.hex[:6]}@silatara.test"
    db.flush()
    with pytest.raises(ContentError):
        run_import(db, root, execute=True, operator_email=demo.email, publish=True)


def test_editorial_publish_makes_knowledge_public_without_partner_or_practice(client, db, tmp_path):
    from tests.factories import make_user

    editor = make_user(db, role="curator")
    root = write_repo(tmp_path)
    out = run_import(db, root, execute=True, operator_email=editor.email, publish=True)
    assert out["counts"]["movement"]["publish"] == 2 and out["counts"]["lesson"]["publish"] == 1
    mv = db.scalar(select(Movement).where(Movement.slug == "gerak-a", Movement.review_note.like("Impor%")))
    doc = db.get(MovementDocument, mv.published_document_id)
    assert mv.status == "published" and mv.content_basis == "source_backed"
    assert mv.practice_mode == "not_for_practice" and mv.assessment_enabled is False  # Practice Studio tetap tertutup
    assert (
        doc.status == "published"
        and doc.curator_reviewed_by_user_id == editor.id
        and doc.partner_confirmed_by_user_id is None
    )
    assert mv.approved_by_user_id == editor.id and "Tinjauan editorial" in mv.approval_evidence_ref
    partner = db.scalar(select(Partner).where(Partner.slug == "silatara-tim-editorial-internal"))
    assert (
        partner.verification_status == "draft" and partner.public_listing_consent is False
    )  # mitra TIDAK diverifikasi
    # publik tanpa login: gerakan, kursus, pelajaran
    client.cookies.clear()
    r = client.get(f"/api/v1/movements/{mv.id}")
    assert r.status_code == 200 and r.json()["partner_name"] is None
    assert (
        r.json()["provenance"]["attribution"] == "Redaksi SILATARA"
        and r.json()["provenance"]["partner_verified"] is False
    )
    assert client.get("/api/v1/courses/kursus-uji-impor").status_code == 200
    le = client.get("/api/v1/courses/kursus-uji-impor/lessons/pelajaran-satu")
    assert le.status_code == 200 and le.json()["enrolled"] is False
    # idempoten
    again = run_import(db, root, execute=True, operator_email=editor.email, publish=True)
    assert set(again["counts"]["movement"]) <= {"unchanged", "already_published"}
