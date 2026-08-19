from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel

# Import auth and creator tables so SQLModel's shared metadata registers them before create_all.
from thebe_core.auth.models import APIKeyDB, TenantDB, TenantMembershipDB  # noqa: F401
from thebe_core.creator.tables import (  # noqa: F401
    AssetDB,
    BookDB,
    BookEditionDB,
    CampaignDB,
    CampaignTaskDB,
    MindDB,
    SourceDocumentDB,
)


class AuditEventDB(SQLModel, table=True):
    """Persistent audit event record."""

    __tablename__ = "audit_events"

    event_id: str = Field(primary_key=True)
    tenant_id: str | None = Field(
        default=None,
        foreign_key="tenants.tenant_id",
        index=True,
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    vertical: str
    customer_id: str
    agent_id: str | None = Field(default=None)
    action: str
    input_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    output_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    event_metadata: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )


class CustomerDB(SQLModel, table=True):
    """Customer / entity under audit with lifecycle states."""

    __tablename__ = "customers"

    customer_id: str = Field(primary_key=True)
    tenant_id: str | None = Field(
        default=None,
        foreign_key="tenants.tenant_id",
        index=True,
    )
    vertical: str
    name: str
    slug: str | None = Field(default=None, index=True)
    status: str = Field(default="draft")
    context: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    archived_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


class EvaluationDB(SQLModel, table=True):
    """Persisted evaluation result."""

    __tablename__ = "evaluations"

    evaluation_id: str = Field(primary_key=True)
    tenant_id: str | None = Field(
        default=None,
        foreign_key="tenants.tenant_id",
        index=True,
    )
    customer_id: str | None = Field(default=None, index=True)
    vertical: str
    entity_type: str
    score: float | None = Field(default=None, nullable=True)
    rule_results: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
    )
    violations: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
    )
    required_actions: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class FindingDB(SQLModel, table=True):
    """A compliance or rights finding linked to an evaluation."""

    __tablename__ = "findings"

    finding_id: str = Field(primary_key=True)
    tenant_id: str | None = Field(
        default=None,
        foreign_key="tenants.tenant_id",
        index=True,
    )
    customer_id: str | None = Field(
        default=None,
        foreign_key="customers.customer_id",
        index=True,
    )
    evaluation_id: str | None = Field(default=None, index=True)
    rule_id: str | None = Field(default=None, index=True)
    title: str
    description: str = ""
    severity: str
    status: str = Field(default="open")
    assignee: str | None = Field(default=None)
    due_date: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    closure_evidence: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class TaskDB(SQLModel, table=True):
    """A remediation task linked to a finding."""

    __tablename__ = "tasks"

    task_id: str = Field(primary_key=True)
    tenant_id: str | None = Field(
        default=None,
        foreign_key="tenants.tenant_id",
        index=True,
    )
    customer_id: str | None = Field(
        default=None,
        foreign_key="customers.customer_id",
        index=True,
    )
    finding_id: str | None = Field(
        default=None,
        foreign_key="findings.finding_id",
        index=True,
    )
    title: str
    assignee: str | None = Field(default=None)
    due_date: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    status: str = Field(default="todo")
    task_metadata: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class DocumentVersionDB(SQLModel, table=True):
    """A version of a generated document with lifecycle status."""

    __tablename__ = "document_versions"

    version_id: str = Field(primary_key=True)
    tenant_id: str | None = Field(
        default=None,
        foreign_key="tenants.tenant_id",
        index=True,
    )
    customer_id: str | None = Field(
        default=None,
        foreign_key="customers.customer_id",
        index=True,
    )
    document_id: str | None = Field(default=None, index=True)
    version_number: int = 1
    status: str = Field(default="generated")
    content: str = ""
    reviewed_by: str | None = Field(default=None)
    approved_by: str | None = Field(default=None)
    regenerated_from: str | None = Field(default=None)
    superseded_by: str | None = Field(default=None)
    created_by: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class EvidenceDB(SQLModel, table=True):
    """Proof attached to a control."""

    __tablename__ = "evidence"

    evidence_id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    customer_id: str = Field(foreign_key="customers.customer_id", index=True)
    control_id: str = Field(foreign_key="controls.control_id", index=True)
    name: str
    type: str = Field(default="other")
    uri: str
    verified: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class JobDB(SQLModel, table=True):
    """An async background job with retry tracking."""

    __tablename__ = "jobs"

    job_id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    job_type: str
    payload: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    status: str = Field(default="pending")
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    last_error: str | None = Field(default=None)
    result: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    started_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


class ObligationDB(SQLModel, table=True):
    """A customer-specific compliance obligation."""

    __tablename__ = "obligations"

    obligation_id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    customer_id: str = Field(foreign_key="customers.customer_id", index=True)
    obligation_key: str | None = Field(default=None, index=True)
    rule_id: str | None = Field(default=None, index=True)
    name: str
    description: str = ""
    status: str = Field(default="pending")
    linked_finding_id: str | None = Field(default=None, index=True)
    linked_document_id: str | None = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class ControlDB(SQLModel, table=True):
    """A customer-specific control that satisfies one or more obligations."""

    __tablename__ = "controls"

    control_id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    customer_id: str = Field(foreign_key="customers.customer_id", index=True)
    control_key: str | None = Field(default=None, index=True)
    rule_id: str | None = Field(default=None, index=True)
    name: str
    description: str = ""
    answer: str = Field(default="unanswered")
    owner: str | None = Field(default=None)
    last_reviewed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    status: str = Field(default="pending")
    linked_obligation_id: str | None = Field(default=None, index=True)
    linked_finding_id: str | None = Field(default=None, index=True)
    linked_document_id: str | None = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
