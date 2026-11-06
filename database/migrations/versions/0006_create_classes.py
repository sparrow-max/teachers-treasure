"""create classes

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-06

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "classes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=32), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
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
        sa.UniqueConstraint("code", name="uk_classes_code"),
        sa.CheckConstraint(
            "length(name) BETWEEN 1 AND 32", name="ck_classes_name_len"
        ),
        sa.CheckConstraint(
            "length(code) BETWEEN 1 AND 32", name="ck_classes_code_len"
        ),
    )
    op.create_index(
        "idx_classes_active_code", "classes", ["active", "code"]
    )


def downgrade() -> None:
    op.drop_index("idx_classes_active_code", table_name="classes")
    op.drop_table("classes")