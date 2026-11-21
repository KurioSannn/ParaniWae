"""content_basis: pengetahuan berbasis sumber vs kurikulum resmi vs konten terbatas mitra (ADR-0008)

- Kolom `content_basis` pada tradisi, gerakan, dokumen gerakan, kursus, pelajaran:
  `source_backed` (pengetahuan umum disusun redaksi dari sumber terbuka; terbit lewat tinjauan editorial),
  `official_curriculum` (kurikulum/representasi resmi mitra; wajib konfirmasi mitra) — DEFAULT untuk semua baris lama,
  `partner_restricted` (materi terbatas mitra).
- Constraint dokumen gerakan: versi verified/published non-demo tetap wajib tinjauan kurator + bukti; konfirmasi mitra
  hanya diwajibkan untuk konten resmi/terbatas, BUKAN untuk pengetahuan berbasis sumber.

Revision ID: b8e4f1c2d7a9
Revises: a3d9c5e7b2f1
Create Date: 2026-11-21
"""

import sqlalchemy as sa
from alembic import op

revision = "b8e4f1c2d7a9"
down_revision = "a3d9c5e7b2f1"
branch_labels = None
depends_on = None

TABLES = ("cultural_traditions", "movements", "movement_documents", "courses", "lessons")
BASES = "'source_backed','official_curriculum','partner_restricted'"

OLD_DOC_CK = (
    "is_demo OR legacy_import OR status NOT IN ('verified','published') OR "
    "(curator_reviewed_by_user_id IS NOT NULL AND curator_reviewed_at IS NOT NULL "
    "AND partner_confirmed_by_user_id IS NOT NULL AND partner_confirmed_at IS NOT NULL "
    "AND approval_evidence_ref IS NOT NULL)"
)
NEW_DOC_CK = (
    "is_demo OR legacy_import OR status NOT IN ('verified','published') OR "
    "(curator_reviewed_by_user_id IS NOT NULL AND curator_reviewed_at IS NOT NULL AND approval_evidence_ref IS NOT NULL "
    "AND (content_basis = 'source_backed' OR "
    "(partner_confirmed_by_user_id IS NOT NULL AND partner_confirmed_at IS NOT NULL)))"
)


def upgrade() -> None:
    for t in TABLES:
        op.add_column(t, sa.Column("content_basis", sa.String(24), nullable=False, server_default="official_curriculum"))
        op.create_check_constraint(f"ck_{t}_content_basis", t, f"content_basis IN ({BASES})")
        op.create_index(f"ix_{t}_content_basis", t, ["content_basis"])
    op.drop_constraint("ck_movement_doc_verified_has_reviews", "movement_documents", type_="check")
    op.create_check_constraint("ck_movement_doc_verified_has_reviews", "movement_documents", NEW_DOC_CK)


def downgrade() -> None:
    op.drop_constraint("ck_movement_doc_verified_has_reviews", "movement_documents", type_="check")
    op.create_check_constraint("ck_movement_doc_verified_has_reviews", "movement_documents", OLD_DOC_CK)
    for t in TABLES:
        op.drop_index(f"ix_{t}_content_basis", table_name=t)
        op.drop_constraint(f"ck_{t}_content_basis", t, type_="check")
        op.drop_column(t, "content_basis")
