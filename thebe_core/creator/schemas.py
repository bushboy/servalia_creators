from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuthorCreateRequest(BaseModel):
    name: str
    context: dict[str, Any] = Field(default_factory=dict)


class AuthorUpdateRequest(BaseModel):
    name: str | None = None
    status: str | None = None
    context: dict[str, Any] | None = None


class MindStatus(BaseModel):
    mind_row_id: str
    mind_id: str
    mind_email: str | None = None
    status: str
    last_interaction_at: datetime | None = None
    memory_version: str | None = None
    configured: bool = False


class AuthorResponse(BaseModel):
    author_id: str
    customer_id: str
    tenant_id: str
    name: str
    status: str
    vertical: str
    context: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    mind: MindStatus | None = None


class MindMessageRequest(BaseModel):
    message: str


class MindMessageResponse(BaseModel):
    job_id: str
    status: str
    author_id: str


class BookCreateRequest(BaseModel):
    author_id: str
    working_title: str
    final_title: str | None = None
    subtitle: str | None = None
    series_name: str | None = None
    description: str = ""
    publication_strategy: str = "kdp_and_ingramspark"


class BookUpdateRequest(BaseModel):
    working_title: str | None = None
    final_title: str | None = None
    subtitle: str | None = None
    series_name: str | None = None
    description: str | None = None
    status: str | None = None
    publication_strategy: str | None = None


class BookResponse(BaseModel):
    id: str
    author_id: str
    working_title: str
    final_title: str | None
    subtitle: str | None
    series_name: str | None
    description: str
    status: str
    publication_strategy: str
    created_at: datetime
    updated_at: datetime


class EditionCreateRequest(BaseModel):
    format: str
    isbn: str | None = None
    language: str = "en"
    trim_size: str | None = None
    page_count: int | None = None
    interior_file_uri: str | None = None
    cover_file_uri: str | None = None
    list_price: float | None = None
    currency: str = "USD"
    publication_date: str | None = None
    platform_strategy: dict[str, Any] = Field(default_factory=dict)


class EditionUpdateRequest(BaseModel):
    format: str | None = None
    isbn: str | None = None
    language: str | None = None
    trim_size: str | None = None
    page_count: int | None = None
    interior_file_uri: str | None = None
    cover_file_uri: str | None = None
    list_price: float | None = None
    currency: str | None = None
    publication_date: str | None = None
    platform_strategy: dict[str, Any] | None = None
    publishing_status: str | None = None
    proof_review_status: str | None = None


class EditionResponse(BaseModel):
    id: str
    book_id: str
    format: str
    isbn: str | None
    language: str
    trim_size: str | None
    page_count: int | None
    interior_file_uri: str | None
    cover_file_uri: str | None
    list_price: float | None
    currency: str
    publication_date: str | None
    platform_strategy: dict[str, Any]
    publishing_status: str
    proof_review_status: str
    created_at: datetime
    updated_at: datetime


class DocumentResponse(BaseModel):
    id: str
    book_id: str
    file_uri: str
    file_name: str
    mime_type: str
    sha256: str
    extracted_text: str
    rights_declaration: str
    version: int
    created_at: datetime


class AssetResponse(BaseModel):
    id: str
    book_id: str
    source_document_id: str | None
    parent_asset_id: str | None
    type: str
    platform: str
    content: str
    source_references: list[dict[str, Any]]
    assumptions: list[str]
    call_to_action: str
    risk_notes: list[str]
    governance_status: str
    approval_status: str
    author_correction: str | None
    applied_preference: bool
    evaluation: dict[str, Any] | None
    created_at: datetime


class GenerateAssetsRequest(BaseModel):
    source_document_id: str | None = None


class GenerateAssetsResponse(BaseModel):
    job_id: str
    status: str


class AssetDecisionRequest(BaseModel):
    note: str | None = None


class AssetReviseRequest(BaseModel):
    correction: str


class CampaignCreateRequest(BaseModel):
    campaign_type: str = "launch"
    launch_date: str | None = None
    timezone: str = "UTC"


class CampaignTaskResponse(BaseModel):
    id: str
    campaign_id: str
    asset_id: str | None
    channel: str
    phase: str
    scheduled_for: str | None
    approval_status: str
    execution_status: str


class CampaignResponse(BaseModel):
    id: str
    book_id: str
    campaign_type: str
    launch_date: str | None
    timezone: str
    status: str
    tasks: list[CampaignTaskResponse] = Field(default_factory=list)


class PublishingStatusUpdate(BaseModel):
    publishing_status: str | None = None
    proof_review_status: str | None = None
