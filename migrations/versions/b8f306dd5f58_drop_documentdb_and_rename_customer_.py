"""Drop DocumentDB and rename customer_metadata to context

Revision ID: b8f306dd5f58
Revises: ffed4f6af45a
Create Date: 2026-08-16 17:24:27.987932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = 'b8f306dd5f58'
down_revision: Union[str, Sequence[str], None] = 'ffed4f6af45a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The legacy DocumentDB table is no longer written by the API.
    # On Postgres, CASCADE removes any historic FK from document_versions.
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("DROP TABLE IF EXISTS documents CASCADE")
    else:
        op.drop_index(op.f('ix_documents_customer_id'), table_name='documents')
        op.drop_index(op.f('ix_documents_tenant_id'), table_name='documents')
        op.drop_table('documents')

    # customer_metadata was replaced with context in CustomerDB.
    op.alter_column(
        'customers',
        'customer_metadata',
        new_column_name='context',
        existing_type=sa.JSON(),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'customers',
        'context',
        new_column_name='customer_metadata',
        existing_type=sa.JSON(),
        existing_nullable=True,
    )

    op.create_table(
        'documents',
        sa.Column('document_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('customer_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('vertical', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('format', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id']),
        sa.PrimaryKeyConstraint('document_id'),
    )
    op.create_index(op.f('ix_documents_customer_id'), 'documents', ['customer_id'], unique=False)
    op.create_index(op.f('ix_documents_tenant_id'), 'documents', ['tenant_id'], unique=False)
