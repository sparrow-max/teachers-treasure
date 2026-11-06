"""create attendance_records

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-06

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attendance_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("student_no", sa.String(length=32), nullable=False),
        sa.Column("student_name", sa.String(length=32), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("order_no", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(length=16), nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["rollcall_sessions.id"],
            name="fk_records_session", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"],
            name="fk_records_student", ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "session_id", "student_id", name="uk_records_session_student"
        ),
        sa.UniqueConstraint(
            "session_id", "order_no", name="uk_records_session_order"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'present', 'absent')", name="ck_records_status"
        ),
        sa.CheckConstraint("order_no >= 1", name="ck_records_order"),
        sa.CheckConstraint(
            "(status = 'pending' AND checked_at IS NULL) "
            "OR (status IN ('present', 'absent') AND checked_at IS NOT NULL)",
            name="ck_records_checked",
        ),
        sa.CheckConstraint(
            "length(student_no) BETWEEN 6 AND 32", name="ck_records_no_len"
        ),
        sa.CheckConstraint(
            "length(student_name) BETWEEN 1 AND 32", name="ck_records_name_len"
        ),
        sa.CheckConstraint(
            "role IN ('学生', '班长', '教师')", name="ck_records_role"
        ),
    )
    op.create_index(
        "idx_records_session_status_order",
        "attendance_records",
        ["session_id", "status", "order_no"],
    )
    op.create_index(
        "idx_records_session_order",
        "attendance_records",
        ["session_id", "order_no"],
    )
    op.create_index(
        "idx_records_student", "attendance_records", ["student_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_records_student", table_name="attendance_records")
    op.drop_index("idx_records_session_order", table_name="attendance_records")
    op.drop_index(
        "idx_records_session_status_order", table_name="attendance_records"
    )
    op.drop_table("attendance_records")