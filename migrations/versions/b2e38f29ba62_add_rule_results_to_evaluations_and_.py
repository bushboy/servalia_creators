"""Add rule_results to evaluations and make score nullable

Revision ID: b2e38f29ba62
Revises: b8f306dd5f58
Create Date: 2026-08-16 18:27:48.339917

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2e38f29ba62'
down_revision: Union[str, Sequence[str], None] = 'b8f306dd5f58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'evaluations',
        sa.Column('rule_results', sa.JSON(), nullable=True),
    )
    op.alter_column(
        'evaluations',
        'score',
        existing_type=sa.Float(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'evaluations',
        'score',
        existing_type=sa.Float(),
        nullable=False,
    )
    op.drop_column('evaluations', 'rule_results')
