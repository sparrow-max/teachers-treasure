"""add class_id to students and rollcall_sessions

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-06

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    op.execute(
        "INSERT INTO classes (name, code, active) "
        "SELECT '默认班级', 'DEFAULT', 1 "
        "WHERE NOT EXISTS (SELECT 1 FROM classes)"
    )
    default_class_id = bind.execute(
        sa.text("SELECT id FROM classes WHERE code = 'DEFAULT'")
    ).scalar_one()

    op.add_column(
        "students", sa.Column("class_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "rollcall_sessions",
        sa.Column("class_id", sa.Integer(), nullable=True),
    )

    bind.execute(
        sa.text(
            "UPDATE students SET class_id = :class_id WHERE class_id IS NULL"
        ),
        {"class_id": default_class_id},
    )
    bind.execute(
        sa.text(
            "UPDATE rollcall_sessions "
            "SET class_id = :class_id WHERE class_id IS NULL"
        ),
        {"class_id": default_class_id},
    )

    with op.batch_alter_table("students") as batch_op:
        batch_op.alter_column(
            "class_id", existing_type=sa.Integer(), nullable=False
        )
        batch_op.create_foreign_key(
            "fk_students_class", "classes", ["class_id"], ["id"],
            ondelete="RESTRICT",
        )
    op.create_index(
        "idx_students_class_active_no",
        "students",
        ["class_id", "active", "student_no"],
    )

    with op.batch_alter_table("rollcall_sessions") as batch_op:
        batch_op.alter_column(
            "class_id", existing_type=sa.Integer(), nullable=False
        )
        batch_op.create_foreign_key(
            "fk_sessions_class", "classes", ["class_id"], ["id"],
            ondelete="RESTRICT",
        )
    op.create_index(
        "idx_sessions_class_started",
        "rollcall_sessions",
        ["class_id", "started_at", "id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_sessions_class_started", table_name="rollcall_sessions"
    )
    with op.batch_alter_table("rollcall_sessions") as batch_op:
        batch_op.drop_constraint("fk_sessions_class", type_="foreignkey")
        batch_op.drop_column("class_id")

    op.drop_index(
        "idx_students_class_active_no", table_name="students"
    )
    with op.batch_alter_table("students") as batch_op:
        batch_op.drop_constraint("fk_students_class", type_="foreignkey")
        batch_op.drop_column("class_id")