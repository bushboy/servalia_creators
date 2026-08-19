"""CreatorTrust books, minds, assets, campaigns

Revision ID: c7a1e0b4d2f1
Revises: f20500175955
Create Date: 2026-08-17 19:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7a1e0b4d2f1"
down_revision: Union[str, Sequence[str], None] = "f20500175955"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "minds",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("author_id", sa.String(), sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("mind_id", sa.String(), nullable=False),
        sa.Column("mind_email", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("active_skills", sa.JSON(), nullable=True),
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("memory_version", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("author_id", name="uq_minds_author_id"),
    )
    op.create_index("ix_minds_tenant_id", "minds", ["tenant_id"])
    op.create_index("ix_minds_author_id", "minds", ["author_id"])
    op.create_index("ix_minds_mind_id", "minds", ["mind_id"])

    op.create_table(
        "books",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("author_id", sa.String(), sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("working_title", sa.String(), nullable=False),
        sa.Column("final_title", sa.String(), nullable=True),
        sa.Column("subtitle", sa.String(), nullable=True),
        sa.Column("series_name", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("publication_strategy", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_books_tenant_id", "books", ["tenant_id"])
    op.create_index("ix_books_author_id", "books", ["author_id"])

    op.create_table(
        "book_editions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("book_id", sa.String(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("format", sa.String(), nullable=False),
        sa.Column("isbn", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("trim_size", sa.String(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("interior_file_uri", sa.String(), nullable=True),
        sa.Column("cover_file_uri", sa.String(), nullable=True),
        sa.Column("list_price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("publication_date", sa.String(), nullable=True),
        sa.Column("platform_strategy", sa.JSON(), nullable=True),
        sa.Column("publishing_status", sa.String(), nullable=False),
        sa.Column("proof_review_status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_book_editions_tenant_id", "book_editions", ["tenant_id"])
    op.create_index("ix_book_editions_book_id", "book_editions", ["book_id"])

    op.create_table(
        "source_documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("book_id", sa.String(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("file_uri", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("sha256", sa.String(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("rights_declaration", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_source_documents_tenant_id", "source_documents", ["tenant_id"])
    op.create_index("ix_source_documents_book_id", "source_documents", ["book_id"])

    op.create_table(
        "assets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("book_id", sa.String(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("source_document_id", sa.String(), sa.ForeignKey("source_documents.id"), nullable=True),
        sa.Column("parent_asset_id", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_references", sa.JSON(), nullable=True),
        sa.Column("assumptions", sa.JSON(), nullable=True),
        sa.Column("call_to_action", sa.String(), nullable=False),
        sa.Column("risk_notes", sa.JSON(), nullable=True),
        sa.Column("governance_status", sa.String(), nullable=False),
        sa.Column("approval_status", sa.String(), nullable=False),
        sa.Column("author_correction", sa.Text(), nullable=True),
        sa.Column("applied_preference", sa.Boolean(), nullable=False),
        sa.Column("evaluation", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assets_tenant_id", "assets", ["tenant_id"])
    op.create_index("ix_assets_book_id", "assets", ["book_id"])
    op.create_index("ix_assets_source_document_id", "assets", ["source_document_id"])
    op.create_index("ix_assets_parent_asset_id", "assets", ["parent_asset_id"])

    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("book_id", sa.String(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("campaign_type", sa.String(), nullable=False),
        sa.Column("launch_date", sa.String(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_campaigns_tenant_id", "campaigns", ["tenant_id"])
    op.create_index("ix_campaigns_book_id", "campaigns", ["book_id"])

    op.create_table(
        "campaign_tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("campaign_id", sa.String(), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("asset_id", sa.String(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("scheduled_for", sa.String(), nullable=True),
        sa.Column("approval_status", sa.String(), nullable=False),
        sa.Column("execution_status", sa.String(), nullable=False),
    )
    op.create_index("ix_campaign_tasks_tenant_id", "campaign_tasks", ["tenant_id"])
    op.create_index("ix_campaign_tasks_campaign_id", "campaign_tasks", ["campaign_id"])


def downgrade() -> None:
    op.drop_table("campaign_tasks")
    op.drop_table("campaigns")
    op.drop_table("assets")
    op.drop_table("source_documents")
    op.drop_table("book_editions")
    op.drop_table("books")
    op.drop_table("minds")
