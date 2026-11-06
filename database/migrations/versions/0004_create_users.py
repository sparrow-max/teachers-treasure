"""create users

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-06

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=32), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("display_name", sa.String(length=32), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column(
            "must_change_password", sa.Boolean(), nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"],
            name="fk_users_student", ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("username", name="uk_users_username"),
        sa.UniqueConstraint("student_id", name="uk_users_student"),
        sa.CheckConstraint(
            "role IN ('teacher', 'monitor', 'student')", name="ck_users_role"
        ),
        sa.CheckConstraint(
            "(role = 'teacher' AND student_id IS NULL) "
            "OR (role <> 'teacher' AND student_id IS NOT NULL)",
            name="ck_users_binding",
        ),
        sa.CheckConstraint(
            "length(username) BETWEEN 1 AND 32", name="ck_users_username_len"
        ),
        sa.CheckConstraint(
            "length(display_name) BETWEEN 1 AND 32", name="ck_users_display_len"
        ),
        sa.CheckConstraint(
            "length(password_hash) >= 20", name="ck_users_password"
        ),
    )
    op.create_index("idx_users_role", "users", ["role"])
    op.create_index("idx_users_active", "users", ["active"])


def downgrade() -> None:
    op.drop_index("idx_users_active", table_name="users")
    op.drop_index("idx_users_role", table_name="users")
    op.drop_table("users")