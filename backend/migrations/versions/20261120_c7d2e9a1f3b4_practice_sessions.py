"""practice_sessions: metadata sesi Practice Studio (tanpa video/frame/landmark)

Revision ID: c7d2e9a1f3b4
Revises: b3f1c2d4e5a6
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c7d2e9a1f3b4"
down_revision = "b3f1c2d4e5a6"
branch_labels = None
depends_on = None

MAX_MS = 86_400_000


def upgrade() -> None:
    op.create_table(
        "practice_sessions",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("lesson_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="in_progress", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active_duration_ms", sa.Integer(), nullable=True),
        sa.Column("paused_duration_ms", sa.Integer(), nullable=True),
        sa.Column("model_version", sa.String(length=120), nullable=False),
        sa.Column("client_version", sa.String(length=40), nullable=True),
        sa.Column("quality_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_code", sa.String(length=40), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('in_progress','completed','abandoned','error')", name="ck_practice_status"),
        sa.CheckConstraint("(status = 'in_progress') = (ended_at IS NULL)", name="ck_practice_ended_iff_done"),
        sa.CheckConstraint(f"active_duration_ms IS NULL OR (active_duration_ms >= 0 AND active_duration_ms <= {MAX_MS})", name="ck_practice_active_range"),
        sa.CheckConstraint(f"paused_duration_ms IS NULL OR (paused_duration_ms >= 0 AND paused_duration_ms <= {MAX_MS})", name="ck_practice_paused_range"),
        sa.CheckConstraint("status = 'in_progress' OR active_duration_ms IS NOT NULL", name="ck_practice_done_has_duration"),
        sa.CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ck_practice_time_order"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_practice_user_started", "practice_sessions", ["user_id", "started_at"])
    op.create_index(op.f("ix_practice_sessions_lesson_id"), "practice_sessions", ["lesson_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_practice_sessions_lesson_id"), table_name="practice_sessions")
    op.drop_index("ix_practice_user_started", table_name="practice_sessions")
    op.drop_table("practice_sessions")
