from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel


class MindDB(SQLModel, table=True):
    """One Mind bound to one author (customer_id)."""

    __tablename__ = "minds"
    __table_args__ = (UniqueConstraint("author_id", name="uq_minds_author_id"),)

    id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    author_id: str = Field(foreign_key="customers.customer_id", index=True)
    mind_id: str = Field(index=True)
    mind_email: str | None = Field(default=None)
    status: str = Field(default="bound")
    active_skills: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    last_interaction_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    memory_version: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class BookDB(SQLModel, table=True):
    __tablename__ = "books"

    id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    author_id: str = Field(foreign_key="customers.customer_id", index=True)
    working_title: str
    final_title: str | None = Field(default=None)
    subtitle: str | None = Field(default=None)
    series_name: str | None = Field(default=None)
    description: str = Field(default="")
    status: str = Field(default="draft")
    publication_strategy: str = Field(default="kdp_and_ingramspark")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class BookEditionDB(SQLModel, table=True):
    __tablename__ = "book_editions"

    id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    book_id: str = Field(foreign_key="books.id", index=True)
    format: str
    isbn: str | None = Field(default=None)
    language: str = Field(default="en")
    trim_size: str | None = Field(default=None)
    page_count: int | None = Field(default=None)
    interior_file_uri: str | None = Field(default=None)
    cover_file_uri: str | None = Field(default=None)
    list_price: float | None = Field(default=None)
    currency: str = Field(default="USD")
    publication_date: str | None = Field(default=None)
    platform_strategy: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    publishing_status: str = Field(default="not_started")
    proof_review_status: str = Field(default="not_requested")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class SourceDocumentDB(SQLModel, table=True):
    __tablename__ = "source_documents"

    id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    book_id: str = Field(foreign_key="books.id", index=True)
    file_uri: str
    file_name: str
    mime_type: str
    sha256: str
    extracted_text: str = Field(default="")
    rights_declaration: str = Field(default="unknown")
    version: int = Field(default=1)
    uploaded_by: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class AssetDB(SQLModel, table=True):
    __tablename__ = "assets"

    id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    book_id: str = Field(foreign_key="books.id", index=True)
    source_document_id: str | None = Field(
        default=None,
        foreign_key="source_documents.id",
        index=True,
    )
    parent_asset_id: str | None = Field(default=None, index=True)
    type: str
    platform: str
    content: str = Field(default="")
    source_references: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
    )
    assumptions: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    call_to_action: str = Field(default="")
    risk_notes: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    governance_status: str = Field(default="pending")
    approval_status: str = Field(default="draft")
    author_correction: str | None = Field(default=None)
    applied_preference: bool = Field(default=False)
    evaluation: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class CampaignDB(SQLModel, table=True):
    __tablename__ = "campaigns"

    id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    book_id: str = Field(foreign_key="books.id", index=True)
    campaign_type: str = Field(default="launch")
    launch_date: str | None = Field(default=None)
    timezone: str = Field(default="UTC")
    status: str = Field(default="draft")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class CampaignTaskDB(SQLModel, table=True):
    __tablename__ = "campaign_tasks"

    id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    campaign_id: str = Field(foreign_key="campaigns.id", index=True)
    asset_id: str | None = Field(default=None, foreign_key="assets.id")
    channel: str
    phase: str
    scheduled_for: str | None = Field(default=None)
    approval_status: str = Field(default="pending")
    execution_status: str = Field(default="not_started")
