from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field


class Provenance(BaseModel):
    """Trace metadata linking an artifact to its actor, source inputs, and runtime."""

    actor_id: str | None = None
    actor_type: str | None = None
    tenant_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_artifact_ids: dict[str, str] = Field(default_factory=dict)
    runtime: dict[str, Any] = Field(default_factory=dict)


class EntityContext(BaseModel):
    """Normalized context describing an entity under evaluation."""

    entity_type: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    relationships: list[dict[str, Any]] = Field(default_factory=list)


class Question(BaseModel):
    """Founder-facing copy for a profile or checklist question."""

    key: str | None = None
    control_key: str | None = None
    obligation_key: str | None = None
    title: str
    help: str = ""
    type: str = "text"
    required: bool = False
    options: dict[str, str] | list[str] | None = None


class ObligationCopy(BaseModel):
    """Founder-facing copy for an obligation framework."""

    title: str
    description: str = ""


class QuestionCatalog(BaseModel):
    """Vertical question catalog loaded from questions.yaml."""

    vertical: str
    version: str = "1.0"
    profile: list[Question] = Field(default_factory=list)
    checklist: list[Question] = Field(default_factory=list)
    obligations: dict[str, ObligationCopy] = Field(default_factory=dict)


class Rule(BaseModel):
    """A single compliance or rights rule."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    rule_id: str
    description: str = ""
    severity: str = "medium"  # low | medium | high
    recommended_actions: list[str] = Field(default_factory=list)

    # Legacy single condition (kept for compatibility with simple packs).
    condition: Callable[[EntityContext], bool] | dict[str, Any] | str | None = None

    # Phase 2 control rule pieces.
    rule_type: str | None = None  # "applicability" | "control"
    obligation_key: str | None = None
    control_key: str | None = None
    applies_when: dict[str, Any] | str | None = None
    check: dict[str, Any] | Callable[[EntityContext], bool] | str | None = None
    evidence_required: bool = False


class RulePack(BaseModel):
    """Vertical-specific collection of applicability and control rules."""

    vertical: str
    applicability_rules: list[Rule] = Field(default_factory=list)
    rules: list[Rule] = Field(default_factory=list)


class RuleResult(BaseModel):
    """Per-rule five-state evaluation result."""

    rule_id: str
    control_key: str | None = None
    obligation_key: str | None = None
    status: str  # PASS | PARTIAL | FAIL | NOT_APPLICABLE | UNKNOWN
    severity: str = "medium"
    description: str = ""
    recommended_actions: list[str] = Field(default_factory=list)
    source_fields: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class Violation(BaseModel):
    """A rule violation surfaced by the policy engine (FAIL + PARTIAL)."""

    rule_id: str
    control_key: str | None = None
    obligation_key: str | None = None
    description: str = ""
    severity: str = "medium"
    recommended_actions: list[str] = Field(default_factory=list)
    source_fields: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    """Result of evaluating an entity against a rule pack."""

    evaluation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vertical: str
    entity_type: str = "company"
    score: float | None = None
    rule_results: list[RuleResult] = Field(default_factory=list)
    violations: list[Violation] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    provenance: Provenance | None = None


class AuditEvent(BaseModel):
    """Evidence-grade record of an action performed by the API."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str | None = None
    vertical: str
    customer_id: str
    agent_id: str | None = None
    action: str
    input_snapshot: dict[str, Any] = Field(default_factory=dict)
    output_snapshot: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance | None = None


class Document(BaseModel):
    """Generated report or agreement (in-memory artifact)."""

    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vertical: str
    format: str  # markdown | json | html
    content: str
    provenance: Provenance | None = None


class Template(BaseModel):
    """A Jinja2 or plain-text document template."""

    name: str
    format: str
    content: str


class DocumentVersion(BaseModel):
    """A snapshot of a generated document at a specific lifecycle state."""

    version_id: str
    document_id: str
    tenant_id: str
    customer_id: str
    version_number: int
    status: str
    content: str
    reviewed_by: str | None = None
    approved_by: str | None = None
    regenerated_from: str | None = None
    superseded_by: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime


class OnboardingSchema(BaseModel):
    """Schema that defines the onboarding questions for a vertical pack."""

    vertical: str
    version: str = "1.0"
    json_schema: dict[str, Any] = Field(default_factory=dict)


class Customer(BaseModel):
    """Customer / entity under audit with lifecycle state."""

    customer_id: str
    tenant_id: str
    vertical: str
    name: str
    slug: str | None = None
    status: str = "draft"
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    archived_at: datetime | None = None


class CustomerWorkspace(BaseModel):
    """Summary view of a customer's compliance posture."""

    customer: Customer
    obligations: list[dict[str, Any]] = Field(default_factory=list)
    controls: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    latest_evaluation: dict[str, Any] | None = None
    evaluation_count: int = 0
    document_count: int = 0
    audit_event_count: int = 0
    open_findings_count: int = 0
    latest_evaluation_id: str | None = None
    latest_score: float | None = None
    latest_activity_at: datetime | None = None


class TimelineEvent(BaseModel):
    """A single chronological event on a customer's evidence timeline."""

    event_id: str
    event_type: str
    artifact_id: str
    action: str
    timestamp: datetime
    actor_id: str | None = None
    vertical: str | None = None
    summary: str = ""
    links: dict[str, str] = Field(default_factory=dict)


class InterestSubmission(BaseModel):
    """Interest form submission from potential customers."""

    submission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    organization: str | None = None
    role: str | None = None
    message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "new"  # new | contacted | qualified | closed
