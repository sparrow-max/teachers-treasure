"""create students

Revision ID: 0001
Revises:
Create Date: 2026-11-06

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("student_no", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=32), nullable=False),
        sa.Column(
            "role", sa.String(length=16), nullable=False,
            server_default=sa.text("'学生'"),
        ),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("student_no", name="uk_students_student_no"),
        sa.CheckConstraint(
            "role IN ('学生', '班长', '教师')", name="ck_students_role"
        ),
        sa.CheckConstraint(
            "length(student_no) BETWEEN 6 AND 32", name="ck_students_no_len"
        ),
        sa.CheckConstraint(
            "length(name) BETWEEN 1 AND 32", name="ck_students_name_len"
        ),
    )
    op.create_index(
        "idx_students_active_no", "students", ["active", "student_no"]
    )


def downgrade() -> None:
    op.drop_index("idx_students_active_no", table_name="students")
    op.drop_table("students")