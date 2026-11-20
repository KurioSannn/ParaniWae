"""Seed DEMO — semua data FIKTIF/placeholder untuk uji teknis, bukan materi budaya.

- Setiap item berlabel [DEMO], `is_demo=true`, tanpa klaim sejarah/filosofi/teknik/maestro/mitra.
- Tidak ada gerakan yang `assessment_enabled`; tidak ada rubrik. Gerakan placeholder = not_for_practice.
- Beberapa item sengaja draft/pending_review untuk menguji bahwa konten itu tidak bocor ke publik.
- Idempotent: aman dijalankan berulang (baris demo disinkronkan, tidak diduplikasi).
- Akun demo hanya dibuat saat APP_ENV=development.
"""

import os
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import (
    Course,
    CourseModule,
    CulturalTradition,
    Instructor,
    Lesson,
    LessonMaterial,
    Movement,
    MovementAnnotation,
    MovementDocument,
    MovementPhase,
    Partner,
    PartnerMember,
    TraditionPartner,
    User,
)

DEMO_SRC = "[DEMO] Data contoh buatan tim pengembang untuk uji teknis; bukan sumber budaya."
DEMO_NOTE = "[DEMO] Teks placeholder untuk pengujian teknis. Bukan sejarah, filosofi, atau materi budaya."
DEMO_USERS = [
    ("demo-pelajar@silatara.test", "[DEMO] Pelajar", "learner"),
    ("demo-instruktur@silatara.test", "[DEMO] Instruktur", "instructor"),
    ("demo-instruktur-b@silatara.test", "[DEMO] Instruktur B (mitra lain)", "instructor"),
    ("demo-kurator@silatara.test", "[DEMO] Kurator", "curator"),
    ("demo-admin@silatara.test", "[DEMO] Admin", "admin"),
    ("demo-admin-2@silatara.test", "[DEMO] Admin 2", "admin"),
]


def _wf(status: str) -> dict:
    d = {"status": status, "is_demo": True, "source_citation": DEMO_SRC}
    if status == "published":
        d["published_at"] = datetime.now(UTC)
    return d


def _ensure(db: Session, model, where: dict, values: dict, counts: dict, key: str):
    obj = db.scalar(select(model).filter_by(**where))
    if obj is None:
        obj = model(**where, **values)
        db.add(obj)
        counts[key] = counts.get(key, 0) + 1
    else:
        if not getattr(obj, "is_demo", True):
            return obj  # jangan pernah menimpa data non-demo
        for k, v in values.items():
            if k == "published_at" and obj.published_at:
                continue
            setattr(obj, k, v)
    db.flush()
    return obj


def seed_demo(db: Session) -> dict[str, int]:
    s = get_settings()
    if s.app_env != "development" and os.environ.get("ALLOW_DEMO_CONTENT_SEED") != "true":
        raise RuntimeError("Seed DEMO hanya diizinkan saat APP_ENV=development "
                           "(staging: ALLOW_DEMO_CONTENT_SEED=true, tetap tanpa akun demo).")
    c: dict[str, int] = {}
    pa = _ensure(db, Partner, {"slug": "demo-perguruan-contoh"}, dict(
        name="[DEMO] Perguruan Contoh A", partner_type="school", city="[DEMO] Kota Contoh",
        region="[DEMO] Wilayah Contoh 1", official_description=DEMO_NOTE,
        verification_status="verified", responsible_name="[DEMO] Penanggung Jawab A",
        responsible_role="[DEMO] Peran contoh", contact_email="demo-mitra-a@silatara.test",
        **_wf("published")), c, "partners")
    pb = _ensure(db, Partner, {"slug": "demo-komunitas-b"}, dict(
        name="[DEMO] Komunitas Contoh B", partner_type="community", city="[DEMO] Kota Contoh",
        region="[DEMO] Wilayah Contoh 2", official_description=DEMO_NOTE,
        verification_status="verified", responsible_name="[DEMO] Penanggung Jawab B",
        responsible_role="[DEMO] Peran contoh", contact_email="demo-mitra-b@silatara.test",
        **_wf("published")), c, "partners")
    _ensure(db, Partner, {"slug": "demo-perguruan-menunggu"}, dict(
        name="[DEMO] Perguruan Menunggu Verifikasi (tidak boleh tampil)", partner_type="school",
        official_description=DEMO_NOTE, verification_status="pending_verification",
        responsible_name="[DEMO] Penanggung Jawab C", responsible_role="[DEMO] Peran contoh",
        contact_email="demo-mitra-c@silatara.test", **_wf("draft")), c, "partners")
    _ensure(db, Partner, {"slug": "demo-perguruan-draf"}, dict(
        name="[DEMO] Perguruan Draf (tidak boleh tampil)", partner_type="school",
        official_description=DEMO_NOTE, **_wf("draft")), c, "partners")

    ta = _ensure(db, CulturalTradition, {"slug": "demo-tradisi"}, dict(
        name="[DEMO] Tradisi Contoh A", region="[DEMO] Wilayah Contoh 1", public_summary=DEMO_NOTE,
        access_scope="public", **_wf("published")), c, "traditions")
    tb = _ensure(db, CulturalTradition, {"slug": "demo-tradisi-b"}, dict(
        name="[DEMO] Tradisi Contoh B", region="[DEMO] Wilayah Contoh 2", public_summary=DEMO_NOTE,
        access_scope="public", **_wf("published")), c, "traditions")
    _ensure(db, CulturalTradition, {"slug": "demo-tradisi-draf"}, dict(
        name="[DEMO] Tradisi Draf (tidak boleh tampil)", public_summary=DEMO_NOTE,
        **_wf("draft")), c, "traditions")
    _ensure(db, CulturalTradition, {"slug": "demo-tradisi-review"}, dict(
        name="[DEMO] Tradisi Menunggu Review (tidak boleh tampil)", public_summary=DEMO_NOTE,
        access_scope="public", **_wf("pending_review")), c, "traditions")
    for t, p in ((ta, pa), (tb, pb)):
        _ensure(db, TraditionPartner, {"tradition_id": t.id, "partner_id": p.id},
                {"relationship_type": "teaching_partner"}, c, "tradition_partners")

    ia = _ensure(db, Instructor, {"slug": "demo-instruktur-a"}, dict(
        partner_id=pa.id, name="[DEMO] Instruktur Contoh A", bio=DEMO_NOTE,
        preferred_attribution="[DEMO] Instruktur Contoh A", **_wf("published")), c, "instructors")
    _ensure(db, Instructor, {"slug": "demo-instruktur-b"}, dict(
        partner_id=pb.id, name="[DEMO] Instruktur Contoh B", bio=DEMO_NOTE,
        **_wf("published")), c, "instructors")

    safety = "[DEMO] Placeholder: tidak ada instruksi gerakan di sini dan tidak untuk dipraktikkan."
    m1 = _ensure(db, Movement, {"tradition_id": ta.id, "slug": "demo-gerakan-1"}, dict(
        partner_id=pa.id, name_id="[DEMO] Gerakan Contoh 1", description=DEMO_NOTE,
        safety_notes=safety, practice_mode="not_for_practice", assessment_enabled=False,
        **_wf("published")), c, "movements")
    _ensure(db, Movement, {"tradition_id": ta.id, "slug": "demo-gerakan-2"}, dict(
        partner_id=pa.id, name_id="[DEMO] Gerakan Contoh 2", description=DEMO_NOTE,
        safety_notes=safety, practice_mode="not_for_practice", assessment_enabled=False,
        **_wf("published")), c, "movements")
    _ensure(db, Movement, {"tradition_id": ta.id, "slug": "demo-gerakan-draf"}, dict(
        partner_id=pa.id, name_id="[DEMO] Gerakan Draf (tidak boleh tampil)", description=DEMO_NOTE,
        practice_mode="not_for_practice", **_wf("draft")), c, "movements")

    _seed_course(db, c, ta, pa, ia, m1, "demo-kurikulum-a", "[DEMO] Kurikulum Contoh A", [
        ("[DEMO] Modul 1: Mengenal Platform", [
            ("demo-orientasi", "[DEMO] Orientasi: Cara Memakai SILATARA", PLATFORM_BODY, None),
            ("demo-keselamatan", "[DEMO] Keselamatan dan Privasi Secara Umum", SAFETY_BODY, None)]),
        ("[DEMO] Modul 2: Contoh Referensi", [
            ("demo-referensi", "[DEMO] Pelajaran dengan Referensi Gerakan", PLACEHOLDER_BODY, m1),
            ("demo-penutup", "[DEMO] Pelajaran Penutup Contoh", PLACEHOLDER_BODY, None)]),
    ], "published")
    _seed_course(db, c, tb, pb, None, None, "demo-kurikulum-b", "[DEMO] Kurikulum Contoh B", [
        ("[DEMO] Modul Tunggal", [
            ("demo-b-1", "[DEMO] Pelajaran B1", PLACEHOLDER_BODY, None),
            ("demo-b-2", "[DEMO] Pelajaran B2", PLACEHOLDER_BODY, None)]),
    ], "published")
    _seed_course(db, c, ta, pa, None, None, "demo-kurikulum-draf",
                 "[DEMO] Kurikulum Draf (tidak boleh tampil)", [
        ("[DEMO] Modul Draf", [("demo-draf-1", "[DEMO] Pelajaran Draf", PLACEHOLDER_BODY, None)]),
    ], "draft")

    if get_settings().app_env == "development":
        pw = os.environ.get("DEMO_USER_PASSWORD", "demo-sandi-12345")
        for email, name, role in DEMO_USERS:
            if not db.scalar(select(User.id).where(User.email == email)):
                db.add(User(email=email, display_name=name, role=role, email_verified_at=datetime.now(UTC),
                            password_hash=hash_password(pw)))
                c["users"] = c.get("users", 0) + 1
        db.flush()
        _seed_studio(db, c, ta, tb, pa, pb, ia, m1)
    db.commit()
    return c


def _demo_doc(db, c, mv, version_no, status, author, phases=(), **kw):
    """Dokumentasi gerakan DEMO: semua teks placeholder berlabel [DEMO] (bukan materi budaya)."""
    fields = dict(
        name_id=mv.name_id, level="beginner", safety_category=None, description=DEMO_NOTE,
        safety_guidance="[DEMO] Placeholder keselamatan; tidak ada instruksi gerakan.",
        source_citation=DEMO_SRC, author_declaration=True, rights_holder="[DEMO] Tim pengembang SILATARA",
        license_type="instructor_owned", usage_scope="[DEMO] Hanya uji teknis internal.",
        created_by_user_id=author.id if author else None, is_demo=True, status=status,
        common_mistakes=[], relevant_body_parts=[], relevant_landmarks=[])
    fields.update(kw)
    if status in {"verified", "published", "archived"}:
        fields.setdefault("approved_at", datetime.now(UTC))
    if status in {"published", "archived"}:
        fields.setdefault("published_at", datetime.now(UTC))
    d = db.scalar(select(MovementDocument).where(MovementDocument.movement_id == mv.id,
                                                 MovementDocument.version_no == version_no))
    if d is None:
        # dibuat sebagai draf agar fase dapat diisi (trigger DB membekukan fase setelah diajukan), baru status akhir
        d = MovementDocument(movement_id=mv.id, version_no=version_no, **{**fields, "status": "draft"})
        db.add(d)
        c["movement_documents"] = c.get("movement_documents", 0) + 1
        db.flush()
        _demo_phases(db, d, phases)
        if status != "draft":
            d.status = status
            db.flush()
    return d


def _demo_phases(db, doc, names):
    if db.scalar(select(MovementPhase.id).where(MovementPhase.document_id == doc.id)):
        return
    for i, n in enumerate(names):
        db.add(MovementPhase(document_id=doc.id, order_index=i, name=f"[DEMO] {n}",
                             instruction="[DEMO] Teks instruksi placeholder (bukan teknik nyata).", body_focus=[]))
    db.flush()


def _seed_studio(db, c, ta, tb, pa, pb, ia, m1):
    """Data Studio DEMO: keanggotaan, dokumentasi bervariasi status, anotasi fixture. Terpisah dari konten resmi."""
    u = {x.email: x for x in db.scalars(select(User).where(User.email.like("demo-%@silatara.test")))}
    ins_a, ins_b = u.get("demo-instruktur@silatara.test"), u.get("demo-instruktur-b@silatara.test")
    if not (ins_a and ins_b):
        return
    for partner, user in ((pa, ins_a), (pb, ins_b)):
        if not db.scalar(select(PartnerMember.id).where(PartnerMember.partner_id == partner.id,
                                                        PartnerMember.user_id == user.id)):
            db.add(PartnerMember(partner_id=partner.id, user_id=user.id, role="manager"))
            c["partner_members"] = c.get("partner_members", 0) + 1
    ia.user_id = ins_a.id
    # gerakan existing -> dokumen v1 (idempotent; migrasi sudah membuatnya pada DB lama)
    for mv in db.scalars(select(Movement).where(Movement.is_demo.is_(True), Movement.tradition_id == ta.id)):
        st = "published" if mv.status == "published" else "draft"
        d = _demo_doc(db, c, mv, 1, st, ins_a, changelog=None)
        if st == "published" and not mv.published_document_id:
            mv.published_document_id, mv.published_version_no = d.id, 1
    specs = [
        ("demo-studio-review", "[DEMO] Dokumentasi Menunggu Tinjauan", "pending_review",
         dict(safety_category="solo_beginner", prerequisites="[DEMO] Tidak ada prasyarat nyata.",
              learning_context="[DEMO] Konteks belajar placeholder.")),
        ("demo-studio-revisi", "[DEMO] Dokumentasi Perlu Revisi", "needs_revision",
         dict(safety_category="supervised_practice", review_note="[DEMO] Mohon lengkapi arahan keselamatan.")),
        ("demo-studio-ditolak", "[DEMO] Dokumentasi Ditolak", "rejected",
         dict(safety_category="restricted", review_note="[DEMO] Contoh alasan penolakan.")),
        ("demo-studio-siap-terbit", "[DEMO] Dokumentasi Siap Terbit", "verified",
         dict(safety_category="solo_beginner", prerequisites="[DEMO] Tidak ada prasyarat nyata.",
              learning_context="[DEMO] Konteks belajar placeholder.", approval_evidence_ref="[DEMO] bukti contoh",
              approved_by_user_id=u.get("demo-kurator@silatara.test").id if u.get("demo-kurator@silatara.test") else None)),
    ]
    for slug, name, status, extra in specs:
        mv = _ensure(db, Movement, {"tradition_id": ta.id, "slug": slug}, dict(
            partner_id=pa.id, name_id=name, description=DEMO_NOTE, practice_mode="not_for_practice",
            assessment_enabled=False, created_by_user_id=ins_a.id, **_wf("draft")), c, "movements")
        d = _demo_doc(db, c, mv, 1, status, ins_a, phases=["Fase satu", "Fase dua"], name_id=name, **extra)
        if slug == "demo-studio-review":
            demo_ann = db.scalar(select(MovementAnnotation.id).where(MovementAnnotation.movement_id == mv.id))
            if not demo_ann:
                for i, ts in enumerate((0, 1500, 3000)):
                    db.add(MovementAnnotation(movement_id=mv.id, fixture_key="demo-synthetic", kind="phase_marker",
                                              timestamp_ms=ts, label=f"[DEMO] Penanda {i + 1}",
                                              annotator_user_id=ins_a.id, model_version="[DEMO] fixture sintetis",
                                              source_note="[DEMO] Fixture sintetis, bukan rekaman manusia."))
    # contoh versioning: v1 diarsipkan, v2 tayang (changelog)
    mv = _ensure(db, Movement, {"tradition_id": ta.id, "slug": "demo-studio-versi"}, dict(
        partner_id=pa.id, name_id="[DEMO] Dokumentasi Berversi", description=DEMO_NOTE,
        practice_mode="not_for_practice", assessment_enabled=False, created_by_user_id=ins_a.id,
        **_wf("published")), c, "movements")
    d1 = _demo_doc(db, c, mv, 1, "archived", ins_a, name_id=mv.name_id, safety_category="supervised_practice")
    d2 = _demo_doc(db, c, mv, 2, "published", ins_a, phases=["Fase satu"], name_id=mv.name_id,
                   safety_category="supervised_practice",
                   changelog="[DEMO] Perbaikan placeholder pada arahan keselamatan.")
    mv.published_document_id, mv.published_version_no, mv.safety_category = d2.id, 2, "supervised_practice"
    mv.practice_mode, mv.level = "supervised_only", "beginner"
    _ = (d1, tb, pb, m1)
    db.flush()


def _seed_course(db, c, trad, partner, instructor, movement, slug, title, modules, status):
    course = _ensure(db, Course, {"slug": slug}, dict(
        tradition_id=trad.id, partner_id=partner.id, instructor_id=instructor.id if instructor else None,
        title=title, summary=DEMO_NOTE, level="beginner", estimated_minutes=20,
        safety_notes="[DEMO] Placeholder keselamatan; tidak ada praktik gerakan pada kurikulum contoh.",
        **_wf(status)), c, "courses")
    lesson_no = 0
    for mi, (mtitle, lessons) in enumerate(modules, start=1):
        mod = _ensure(db, CourseModule, {"course_id": course.id, "order_index": mi},
                      {"title": mtitle, "summary": DEMO_NOTE}, c, "modules")
        for li, (lslug, ltitle, body, mv) in enumerate(lessons, start=1):
            lesson_no += 1
            lesson = _ensure(db, Lesson, {"course_id": course.id, "slug": lslug}, dict(
                module_id=mod.id, title=ltitle, objective="[DEMO] Tujuan contoh untuk uji tampilan.",
                body=body, safety_notes=None, order_index=li, estimated_minutes=5,
                movement_id=mv.id if mv else None, **_wf(status)), c, "lessons")
            if not db.scalar(select(LessonMaterial.id).where(LessonMaterial.lesson_id == lesson.id)):
                db.add(LessonMaterial(
                    lesson_id=lesson.id, kind="text", title="[DEMO] Catatan pengembang",
                    content="Materi pendukung contoh (teks). Tidak ada media atau tautan pihak ketiga.",
                    attribution_text="[DEMO] Tim pengembang SILATARA (teks uji)"))
                c["materials"] = c.get("materials", 0) + 1


PLATFORM_BODY = """Pelajaran ini menjelaskan cara memakai SILATARA pada tahap pengembangan.

Daftar ke sebuah kurikulum dengan tombol "Ikuti kurikulum". Setelah terdaftar, buka tiap pelajaran dan tekan "Tandai selesai" bila sudah selesai membaca.

Halaman Progres menampilkan persentase pelajaran yang telah Anda selesaikan. Persentase hanya menghitung pelajaran yang saat ini diterbitkan.

Seluruh isi bertanda [DEMO] hanyalah contoh teknis dan bukan materi budaya resmi."""

SAFETY_BODY = """SILATARA adalah alat bantu belajar, bukan pengganti instruktur. Instruktur tetap menjadi otoritas atas gerakan dan tingkatan.

Kamera hanya menyala atas pilihan Anda, dapat dihentikan kapan saja, dan video mentah tidak disimpan atau dikirim ke server. Fitur penilaian gerakan belum tersedia.

Hentikan kegiatan apa pun bila Anda merasa nyeri atau tidak nyaman."""

PLACEHOLDER_BODY = """[DEMO] Ini adalah teks placeholder untuk menguji tampilan pelajaran.

Tidak ada materi budaya, sejarah, filosofi, atau teknik pada pelajaran ini."""
