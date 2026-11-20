"""Instructor & Partner Studio: kemitraan, dokumentasi gerakan berversi, media referensi, anotasi.

Revision ID: e5a1b7c9d3f2
Revises: c7d2e9a1f3b4
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "e5a1b7c9d3f2"
down_revision = "c7d2e9a1f3b4"
branch_labels = None
depends_on = None

OLD_STS = "'draft','pending_review','rejected','verified','published','archived'"
NEW_STS = "'draft','pending_review','needs_revision','rejected','verified','published','archived'"
WF_TABLES = (
    ("partners", "partners"),
    ("cultural_traditions", "traditions"),
    ("instructors", "instructors"),
    ("movements", "movements"),
    ("courses", "courses"),
    ("lessons", "lessons"),
)
EMPTY = sa.text("'[]'::jsonb")
UID = pg.UUID(as_uuid=True)


def _wf_columns():
    return [
        sa.Column("status", sa.String(16), server_default="draft", nullable=False),
        sa.Column("is_demo", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("source_citation", sa.Text()),
        sa.Column("source_url", sa.String(500)),
        sa.Column("review_note", sa.Text()),
        sa.Column("created_by_user_id", UID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("approved_by_user_id", UID, sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("approval_evidence_ref", sa.Text()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    ]


def _idts():
    return [
        sa.Column("id", UID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    # ---- status baru `needs_revision` untuk semua tabel workflow ----
    for t, p in WF_TABLES:
        op.drop_constraint(f"ck_{p}_status", t, type_="check")
        op.create_check_constraint(f"ck_{p}_status", t, f"status IN ({NEW_STS})")

    # ---- partners ----
    op.drop_constraint("ck_partners_public_requires_verified", "partners", type_="check")
    op.drop_constraint("ck_partners_verification", "partners", type_="check")
    op.alter_column("partners", "verification_status", type_=sa.String(24), server_default="draft")
    for name, typ in (
        ("responsible_name", sa.String(200)), ("responsible_role", sa.String(120)),
        ("responsible_contact", sa.String(320)), ("contact_email", sa.String(320)),
        ("contact_phone", sa.String(40)), ("verification_note", sa.Text()),
    ):
        op.add_column("partners", sa.Column(name, typ))
    op.add_column("partners", sa.Column("verification_decided_by_user_id", UID,
                                        sa.ForeignKey("users.id", ondelete="RESTRICT")))
    op.add_column("partners", sa.Column("verification_decided_at", sa.DateTime(timezone=True)))
    op.add_column("partners", sa.Column("submitted_at", sa.DateTime(timezone=True)))
    op.execute("""UPDATE partners SET verification_status = CASE verification_status
        WHEN 'unverified' THEN 'draft' WHEN 'revoked' THEN 'suspended' ELSE verification_status END""")
    # `verified` hanya bila ada jejak penyetuju; bila tidak ada, jangan dianggap mitra resmi (non-destruktif: turun ke pending).
    op.execute("""UPDATE partners SET verification_decided_by_user_id = approved_by_user_id,
        verification_decided_at = approved_at
        WHERE verification_status = 'verified' AND approved_by_user_id IS NOT NULL AND approved_at IS NOT NULL""")
    op.execute("""UPDATE partners SET public_listing_consent = false, verification_status = 'pending_verification',
        verification_note = 'Dimigrasikan: status verified lama tanpa jejak penyetuju; perlu verifikasi ulang.'
        WHERE verification_status = 'verified' AND NOT is_demo AND verification_decided_by_user_id IS NULL""")
    op.create_check_constraint("ck_partners_verification", "partners",
        "verification_status IN ('draft','pending_verification','verified','rejected','suspended')")
    op.create_check_constraint("ck_partners_verified_has_decider", "partners",
        "verification_status <> 'verified' OR is_demo OR "
        "(verification_decided_by_user_id IS NOT NULL AND verification_decided_at IS NOT NULL)")
    op.create_check_constraint("ck_partners_public_requires_verified", "partners",
        "NOT public_listing_consent OR verification_status = 'verified'")

    # ---- instructors.user_id ----
    op.add_column("instructors", sa.Column("user_id", UID, sa.ForeignKey("users.id", ondelete="SET NULL")))
    op.create_unique_constraint("uq_instructors_user_id", "instructors", ["user_id"])

    # ---- tabel baru ----
    op.create_table("partner_members", *_idts(),
        sa.Column("partner_id", UID, sa.ForeignKey("partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(12), nullable=False),
        sa.Column("status", sa.String(10), server_default="active", nullable=False),
        sa.Column("invited_by_user_id", UID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_id", "user_id", name="uq_partner_member"),
        sa.CheckConstraint("role IN ('manager','instructor')", name="ck_partner_members_role"),
        sa.CheckConstraint("status IN ('active','removed')", name="ck_partner_members_status"))
    op.create_index("ix_partner_members_partner_id", "partner_members", ["partner_id"])
    op.create_index("ix_partner_members_user_id", "partner_members", ["user_id"])

    op.create_table("partner_documents", *_idts(),
        sa.Column("partner_id", UID, sa.ForeignKey("partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("description", sa.String(300)),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(80), nullable=False),
        sa.Column("mime", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("uploaded_by_user_id", UID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
        sa.CheckConstraint("kind IN ('approval_letter','identity','other')", name="ck_partner_docs_kind"))
    op.create_index("ix_partner_documents_partner_id", "partner_documents", ["partner_id"])

    op.create_table("partner_verification_events", *_idts(),
        sa.Column("partner_id", UID, sa.ForeignKey("partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(24), nullable=False),
        sa.Column("from_status", sa.String(24)),
        sa.Column("to_status", sa.String(24), nullable=False),
        sa.Column("actor_user_id", UID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("note", sa.Text()),
        sa.Column("evidence_ref", sa.Text()),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_partner_verification_events_partner_id", "partner_verification_events", ["partner_id"])

    # movement_documents (satu baris per versi)
    op.create_table("movement_documents", *_idts(), *_wf_columns(),
        sa.Column("movement_id", UID, sa.ForeignKey("movements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("name_id", sa.String(200), nullable=False),
        sa.Column("name_local", sa.String(200)),
        sa.Column("level", sa.String(16)),
        sa.Column("safety_category", sa.String(24)),
        sa.Column("prerequisites", sa.Text()),
        sa.Column("learning_context", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("terminology_notes", sa.Text()),
        sa.Column("common_mistakes", pg.JSONB(), server_default=EMPTY, nullable=False),
        sa.Column("safety_guidance", sa.Text()),
        sa.Column("relevant_body_parts", pg.JSONB(), server_default=EMPTY, nullable=False),
        sa.Column("relevant_landmarks", pg.JSONB(), server_default=EMPTY, nullable=False),
        sa.Column("legacy_import", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("author_declaration", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("rights_holder", sa.String(300)),
        sa.Column("license_type", sa.String(30)),
        sa.Column("usage_scope", sa.Text()),
        sa.Column("changelog", sa.Text()),
        sa.Column("curator_reviewed_by_user_id", UID, sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("curator_reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("partner_confirmed_by_user_id", UID, sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("partner_confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("partner_confirmation_note", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("movement_id", "version_no", name="uq_movement_doc_version"),
        sa.CheckConstraint("version_no >= 1", name="ck_movement_doc_version_pos"),
        sa.CheckConstraint("level IS NULL OR level IN ('beginner','intermediate','advanced')", name="ck_movement_doc_level"),
        sa.CheckConstraint("safety_category IS NULL OR safety_category IN "
            "('solo_beginner','supervised_practice','contact_practice','weapon_related','restricted')",
            name="ck_movement_doc_safety"),
        sa.CheckConstraint("license_type IS NULL OR license_type IN "
            "('instructor_owned','partner_permission','other_written_permission')", name="ck_movement_doc_license"),
        sa.CheckConstraint("is_demo OR legacy_import OR status NOT IN ('verified','published') OR "
            "(curator_reviewed_by_user_id IS NOT NULL AND curator_reviewed_at IS NOT NULL "
            "AND partner_confirmed_by_user_id IS NOT NULL AND partner_confirmed_at IS NOT NULL "
            "AND approval_evidence_ref IS NOT NULL)", name="ck_movement_doc_verified_has_reviews"),
        sa.CheckConstraint(f"status IN ({NEW_STS})", name="ck_movement_documents_status"),
        sa.CheckConstraint("is_demo OR status NOT IN ('verified','published') OR (approved_by_user_id IS NOT NULL "
            "AND approved_at IS NOT NULL AND source_citation IS NOT NULL)",
            name="ck_movement_documents_verified_has_provenance"),
        sa.CheckConstraint("status <> 'published' OR published_at IS NOT NULL",
            name="ck_movement_documents_published_has_timestamp"))
    op.create_index("ix_movement_documents_movement_id", "movement_documents", ["movement_id"])
    op.create_index("ix_movement_documents_status", "movement_documents", ["status"])
    # Paling banyak satu versi tayang per gerakan.
    op.create_index("uq_movement_one_published", "movement_documents", ["movement_id"], unique=True,
                    postgresql_where=sa.text("status = 'published' AND deleted_at IS NULL"))

    op.create_table("movement_phases", *_idts(),
        sa.Column("document_id", UID, sa.ForeignKey("movement_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("body_focus", pg.JSONB(), server_default=EMPTY, nullable=False),
        sa.Column("safety_note", sa.Text()),
        sa.Column("start_ms", sa.Integer()),
        sa.Column("end_ms", sa.Integer()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "order_index", name="uq_phase_order"),
        sa.CheckConstraint("order_index >= 0", name="ck_phase_order_nonneg"),
        sa.CheckConstraint("start_ms IS NULL OR end_ms IS NULL OR end_ms >= start_ms", name="ck_phase_time_order"))
    op.create_index("ix_movement_phases_document_id", "movement_phases", ["document_id"])

    op.create_table("reference_media", *_idts(),
        sa.Column("movement_id", UID, sa.ForeignKey("movements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploader_user_id", UID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("kind", sa.String(8), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(80), nullable=False),
        sa.Column("mime", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("rights_holder", sa.String(300), nullable=False),
        sa.Column("source_description", sa.Text(), nullable=False),
        sa.Column("license_type", sa.String(30), nullable=False),
        sa.Column("usage_scope", sa.Text(), nullable=False),
        sa.Column("declaration_confirmed", sa.Boolean(), nullable=False),
        sa.Column("permission_evidence_ref", sa.Text()),
        sa.Column("consent_status", sa.String(10), server_default="declared", nullable=False),
        sa.Column("access_level", sa.String(10), server_default="private", nullable=False),
        sa.Column("retention_until", sa.Date()),
        sa.Column("decided_by_user_id", UID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("is_demo", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
        sa.CheckConstraint("kind IN ('video','image')", name="ck_media_kind"),
        sa.CheckConstraint("declaration_confirmed", name="ck_media_declared"),
        sa.CheckConstraint("consent_status IN ('declared','verified','rejected','revoked')", name="ck_media_consent"),
        sa.CheckConstraint("access_level IN ('private','reviewers','public')", name="ck_media_access"),
        sa.CheckConstraint("license_type IN ('instructor_owned','partner_permission','other_written_permission')",
            name="ck_media_license"),
        sa.CheckConstraint("access_level <> 'public' OR consent_status = 'verified'", name="ck_media_public_verified"))
    op.create_index("ix_reference_media_movement_id", "reference_media", ["movement_id"])

    op.create_table("movement_annotations", *_idts(),
        sa.Column("movement_id", UID, sa.ForeignKey("movements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("media_id", UID, sa.ForeignKey("reference_media.id", ondelete="CASCADE")),
        sa.Column("fixture_key", sa.String(40)),
        sa.Column("phase_id", UID, sa.ForeignKey("movement_phases.id", ondelete="SET NULL")),
        sa.Column("kind", sa.String(14), nullable=False),
        sa.Column("timestamp_ms", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("annotator_user_id", UID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("model_version", sa.String(120)),
        sa.Column("source_note", sa.Text()),
        sa.Column("review_status", sa.String(10), server_default="pending", nullable=False),
        sa.Column("reviewed_by_user_id", UID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("kind IN ('phase_marker','note')", name="ck_annotation_kind"),
        sa.CheckConstraint("review_status IN ('pending','accepted','rejected')", name="ck_annotation_review"),
        sa.CheckConstraint("timestamp_ms >= 0", name="ck_annotation_ts"),
        sa.CheckConstraint("(media_id IS NOT NULL) <> (fixture_key IS NOT NULL)", name="ck_annotation_target"),
        sa.CheckConstraint("fixture_key IS NULL OR fixture_key = 'demo-synthetic'", name="ck_annotation_fixture"))
    op.create_index("ix_movement_annotations_movement_id", "movement_annotations", ["movement_id"])
    op.create_index("ix_movement_annotations_media_id", "movement_annotations", ["media_id"])

    # ---- movements: penunjuk versi tayang ----
    op.add_column("movements", sa.Column("published_document_id", UID))
    op.add_column("movements", sa.Column("published_version_no", sa.Integer()))
    op.add_column("movements", sa.Column("level", sa.String(16)))
    op.add_column("movements", sa.Column("safety_category", sa.String(24)))
    op.create_foreign_key("fk_movements_published_document", "movements", "movement_documents",
                          ["published_document_id"], ["id"], ondelete="SET NULL")
    op.create_check_constraint("ck_movements_level", "movements",
        "level IS NULL OR level IN ('beginner','intermediate','advanced')")
    op.create_check_constraint("ck_movements_safety_category", "movements",
        "safety_category IS NULL OR safety_category IN "
        "('solo_beginner','supervised_practice','contact_practice','weapon_related','restricted')")

    # ---- migrasi data: setiap gerakan lama -> dokumen versi 1 (tanpa mengubah baris asal) ----
    op.execute("""
        INSERT INTO movement_documents (movement_id, version_no, name_id, name_local, description, safety_guidance,
            safety_category, status, is_demo, source_citation, source_url, review_note, created_by_user_id,
            approved_by_user_id, approved_at, approval_evidence_ref, published_at, deleted_at, legacy_import, changelog)
        SELECT id, 1, name_id, name_local, description, safety_notes,
            CASE practice_mode WHEN 'solo_beginner' THEN 'solo_beginner' WHEN 'supervised_only' THEN 'supervised_practice' END,
            status, is_demo, source_citation, source_url, review_note, created_by_user_id,
            approved_by_user_id, approved_at, approval_evidence_ref, published_at, deleted_at, true,
            'Dimigrasikan dari data gerakan sebelum Instructor & Partner Studio.'
        FROM movements""")
    op.execute("""UPDATE movements m SET published_document_id = d.id, published_version_no = 1,
        safety_category = d.safety_category
        FROM movement_documents d WHERE d.movement_id = m.id AND d.version_no = 1 AND d.status = 'published'""")

    # ---- trigger immutability ----
    op.execute("""
    CREATE OR REPLACE FUNCTION movement_documents_guard() RETURNS trigger AS $$
    DECLARE
        mutable text[] := ARRAY['status','review_note','approved_by_user_id','approved_at','approval_evidence_ref',
            'published_at','updated_at','deleted_at','curator_reviewed_by_user_id','curator_reviewed_at',
            'partner_confirmed_by_user_id','partner_confirmed_at','partner_confirmation_note'];
    BEGIN
        IF TG_OP = 'DELETE' THEN
            IF OLD.status IN ('pending_review','verified','published','archived') THEN
                RAISE EXCEPTION 'Versi dokumentasi berstatus % tidak boleh dihapus', OLD.status
                    USING ERRCODE = 'integrity_constraint_violation';
            END IF;
            RETURN OLD;
        END IF;
        IF OLD.status IN ('pending_review','verified','published','archived') THEN
            IF (to_jsonb(OLD) - mutable) IS DISTINCT FROM (to_jsonb(NEW) - mutable) THEN
                RAISE EXCEPTION 'Isi versi dokumentasi berstatus % tidak dapat diubah; buat versi baru', OLD.status
                    USING ERRCODE = 'integrity_constraint_violation';
            END IF;
        END IF;
        IF OLD.status = 'published' AND NEW.status NOT IN ('published','archived') THEN
            RAISE EXCEPTION 'Versi tayang hanya dapat diarsipkan' USING ERRCODE = 'integrity_constraint_violation';
        END IF;
        IF OLD.status = 'archived' AND NEW.status <> 'archived' THEN
            RAISE EXCEPTION 'Versi arsip tidak dapat diaktifkan kembali; buat versi baru'
                USING ERRCODE = 'integrity_constraint_violation';
        END IF;
        RETURN NEW;
    END $$ LANGUAGE plpgsql""")
    op.execute("""CREATE TRIGGER movement_documents_immutable BEFORE UPDATE OR DELETE ON movement_documents
        FOR EACH ROW EXECUTE FUNCTION movement_documents_guard()""")
    op.execute("""
    CREATE OR REPLACE FUNCTION movement_phases_guard() RETURNS trigger AS $$
    DECLARE st text; did uuid;
    BEGIN
        did := CASE WHEN TG_OP = 'DELETE' THEN OLD.document_id ELSE NEW.document_id END;
        SELECT status INTO st FROM movement_documents WHERE id = did;
        IF st IS NOT NULL AND st NOT IN ('draft','needs_revision','rejected') THEN
            RAISE EXCEPTION 'Fase tidak dapat diubah pada versi berstatus %', st
                USING ERRCODE = 'integrity_constraint_violation';
        END IF;
        RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
    END $$ LANGUAGE plpgsql""")
    op.execute("""CREATE TRIGGER movement_phases_immutable BEFORE INSERT OR UPDATE OR DELETE ON movement_phases
        FOR EACH ROW EXECUTE FUNCTION movement_phases_guard()""")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS movement_phases_immutable ON movement_phases")
    op.execute("DROP TRIGGER IF EXISTS movement_documents_immutable ON movement_documents")
    op.execute("DROP FUNCTION IF EXISTS movement_phases_guard()")
    op.execute("DROP FUNCTION IF EXISTS movement_documents_guard()")
    op.drop_constraint("ck_movements_safety_category", "movements", type_="check")
    op.drop_constraint("ck_movements_level", "movements", type_="check")
    op.drop_constraint("fk_movements_published_document", "movements", type_="foreignkey")
    for c in ("safety_category", "level", "published_version_no", "published_document_id"):
        op.drop_column("movements", c)
    for t in ("movement_annotations", "reference_media", "movement_phases", "movement_documents",
              "partner_verification_events", "partner_documents", "partner_members"):
        op.drop_table(t)
    op.drop_constraint("uq_instructors_user_id", "instructors", type_="unique")
    op.drop_column("instructors", "user_id")

    op.drop_constraint("ck_partners_public_requires_verified", "partners", type_="check")
    op.drop_constraint("ck_partners_verified_has_decider", "partners", type_="check")
    op.drop_constraint("ck_partners_verification", "partners", type_="check")
    op.execute("""UPDATE partners SET verification_status = CASE verification_status
        WHEN 'verified' THEN 'verified' WHEN 'suspended' THEN 'revoked' ELSE 'unverified' END""")
    op.execute("UPDATE partners SET public_listing_consent = false WHERE verification_status <> 'verified'")
    for c in ("submitted_at", "verification_decided_at", "verification_decided_by_user_id", "verification_note",
              "contact_phone", "contact_email", "responsible_contact", "responsible_role", "responsible_name"):
        op.drop_column("partners", c)
    op.alter_column("partners", "verification_status", type_=sa.String(16), server_default="unverified")
    op.create_check_constraint("ck_partners_verification", "partners",
        "verification_status IN ('unverified','verified','revoked')")
    op.create_check_constraint("ck_partners_public_requires_verified", "partners",
        "NOT public_listing_consent OR verification_status = 'verified'")

    for t, p in WF_TABLES:
        op.execute(f"UPDATE {t} SET status = 'draft' WHERE status = 'needs_revision'")
        op.drop_constraint(f"ck_{p}_status", t, type_="check")
        op.create_check_constraint(f"ck_{p}_status", t, f"status IN ({OLD_STS})")
