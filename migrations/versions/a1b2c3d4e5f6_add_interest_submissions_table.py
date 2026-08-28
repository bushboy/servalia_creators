"""add interest_submissions table

Revision ID: a1b2c3d4e5f6
Revises: c7a1e0b4d2f1
Create Date: 2026-08-28 07:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "c7a1e0b4d2f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interest_submissions",
        sa.Column("submission_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("organization", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="new"),
        sa.PrimaryKeyConstraint("submission_id"),
    )
    op.create_index("ix_interest_submissions_email", "interest_submissions", ["email"])
    op.create_index("ix_interest_submissions_status", "interest_submissions", ["status"])
    op.create_index("ix_interest_submissions_created_at", "interest_submissions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_interest_submissions_created_at", table_name="interest_submissions")
    op.drop_index("ix_interest_submissions_status", table_name="interest_submissions")
    op.drop_index("ix_interest_submissions_email", table_name="interest_submissions")
    op.drop_table("interest_submissions")