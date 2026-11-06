"""create rollcall_sessions

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-06

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rollcall_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=64), nullable=False),
        sa.Column(
            "status", sa.String(length=16), nullable=False,
            server_default=sa.text("'calling'"),
        ),
        sa.Column(
            "order_by", sa.String(length=16), nullable=False,
            server_default=sa.text("'student_no'"),
        ),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "status IN ('calling', 'ended')", name="ck_sessions_status"
        ),
        sa.CheckConstraint(
            "order_by IN ('student_no', 'name', 'id')",
            name="ck_sessions_order_by",
        ),
        sa.CheckConstraint(
            "length(title) BETWEEN 1 AND 64", name="ck_sessions_title_len"
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_sessions_time",
        ),
        sa.CheckConstraint(
            "(status = 'calling' AND ended_at IS NULL) "
            "OR (status = 'ended' AND ended_at IS NOT NULL)",
            name="ck_sessions_state",
        ),
    )
    op.create_index(
        "idx_sessions_started", "rollcall_sessions", ["started_at", "id"]
    )
    op.create_index("idx_sessions_status", "rollcall_sessions", ["status"])


def downgrade() -> None:
    op.drop_index("idx_sessions_status", table_name="rollcall_sessions")
    op.drop_index("idx_sessions_started", table_name="rollcall_sessions")
    op.drop_table("rollcall_sessions")