"""Phase 2 schema catch-up

Revision ID: f20500175955
Revises: b2e38f29ba62
Create Date: 2026-08-16 18:56:22.445611

These tables were historically created by SQLModel metadata.create_all on
developer databases, so autogenerate only emitted ALTER COLUMN. A fresh
Alembic-only database (Docker Compose) never had them — create if missing.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401


revision: str = "f20500175955"
down_revision: Union[str, Sequence[str], None] = "b2e38f29ba62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    return column in {c["name"] for c in _inspector().get_columns(table)}


def _has_index(table: str, name: str) -> bool:
    return name in {idx["name"] for idx in _inspector().get_indexes(table)}


def _add_column_if_missing(table: str, column: sa.Column) -> None:
    if not _has_column(table, column.name):
        op.add_column(table, column)


def _create_index_if_missing(name: str, table: str, columns: list[str]) -> None:
    if not _has_index(table, name):
        op.create_index(name, table, columns, unique=False)


def upgrade() -> None:
    op.alter_column(
        "audit_events",
        "agent_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )

    if not _has_table("findings"):
        op.create_table(
            "findings",
            sa.Column("finding_id", sa.String(), nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=True),
            sa.Column("customer_id", sa.String(), nullable=True),
            sa.Column("evaluation_id", sa.String(), nullable=True),
            sa.Column("rule_id", sa.String(), nullable=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("assignee", sa.String(), nullable=True),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("closure_evidence", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.customer_id"]),
            sa.PrimaryKeyConstraint("finding_id"),
        )
        op.create_index("ix_findings_tenant_id", "findings", ["tenant_id"])
        op.create_index("ix_findings_customer_id", "findings", ["customer_id"])
        op.create_index("ix_findings_evaluation_id", "findings", ["evaluation_id"])
        op.create_index("ix_findings_rule_id", "findings", ["rule_id"])
    else:
        _add_column_if_missing("findings", sa.Column("rule_id", sa.String(), nullable=True))
        _create_index_if_missing("ix_findings_rule_id", "findings", ["rule_id"])

    if not _has_table("obligations"):
        op.create_table(
            "obligations",
            sa.Column("obligation_id", sa.String(), nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("customer_id", sa.String(), nullable=False),
            sa.Column("obligation_key", sa.String(), nullable=True),
            sa.Column("rule_id", sa.String(), nullable=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("linked_finding_id", sa.String(), nullable=True),
            sa.Column("linked_document_id", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.customer_id"]),
            sa.PrimaryKeyConstraint("obligation_id"),
        )
        op.create_index("ix_obligations_tenant_id", "obligations", ["tenant_id"])
        op.create_index("ix_obligations_customer_id", "obligations", ["customer_id"])
        op.create_index("ix_obligations_obligation_key", "obligations", ["obligation_key"])
        op.create_index("ix_obligations_rule_id", "obligations", ["rule_id"])
        op.create_index("ix_obligations_linked_finding_id", "obligations", ["linked_finding_id"])
        op.create_index("ix_obligations_linked_document_id", "obligations", ["linked_document_id"])
    else:
        _add_column_if_missing(
            "obligations", sa.Column("obligation_key", sa.String(), nullable=True)
        )
        _add_column_if_missing("obligations", sa.Column("rule_id", sa.String(), nullable=True))
        _create_index_if_missing(
            "ix_obligations_obligation_key", "obligations", ["obligation_key"]
        )
        _create_index_if_missing("ix_obligations_rule_id", "obligations", ["rule_id"])

    if not _has_table("controls"):
        op.create_table(
            "controls",
            sa.Column("control_id", sa.String(), nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("customer_id", sa.String(), nullable=False),
            sa.Column("control_key", sa.String(), nullable=True),
            sa.Column("rule_id", sa.String(), nullable=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=False),
            sa.Column("answer", sa.String(), server_default=sa.text("'unanswered'"), nullable=False),
            sa.Column("owner", sa.String(), nullable=True),
            sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("linked_obligation_id", sa.String(), nullable=True),
            sa.Column("linked_finding_id", sa.String(), nullable=True),
            sa.Column("linked_document_id", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.customer_id"]),
            sa.PrimaryKeyConstraint("control_id"),
        )
        op.create_index("ix_controls_tenant_id", "controls", ["tenant_id"])
        op.create_index("ix_controls_customer_id", "controls", ["customer_id"])
        op.create_index("ix_controls_control_key", "controls", ["control_key"])
        op.create_index("ix_controls_rule_id", "controls", ["rule_id"])
        op.create_index("ix_controls_linked_obligation_id", "controls", ["linked_obligation_id"])
        op.create_index("ix_controls_linked_finding_id", "controls", ["linked_finding_id"])
        op.create_index("ix_controls_linked_document_id", "controls", ["linked_document_id"])
    else:
        _add_column_if_missing("controls", sa.Column("control_key", sa.String(), nullable=True))
        _add_column_if_missing("controls", sa.Column("rule_id", sa.String(), nullable=True))
        _add_column_if_missing(
            "controls",
            sa.Column(
                "answer",
                sa.String(),
                server_default=sa.text("'unanswered'"),
                nullable=False,
            ),
        )
        _add_column_if_missing("controls", sa.Column("owner", sa.String(), nullable=True))
        _add_column_if_missing(
            "controls",
            sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        )
        _create_index_if_missing("ix_controls_control_key", "controls", ["control_key"])
        _create_index_if_missing("ix_controls_rule_id", "controls", ["rule_id"])

    if not _has_table("tasks"):
        op.create_table(
            "tasks",
            sa.Column("task_id", sa.String(), nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=True),
            sa.Column("customer_id", sa.String(), nullable=True),
            sa.Column("finding_id", sa.String(), nullable=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("assignee", sa.String(), nullable=True),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("task_metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.customer_id"]),
            sa.ForeignKeyConstraint(["finding_id"], ["findings.finding_id"]),
            sa.PrimaryKeyConstraint("task_id"),
        )
        op.create_index("ix_tasks_tenant_id", "tasks", ["tenant_id"])
        op.create_index("ix_tasks_customer_id", "tasks", ["customer_id"])
        op.create_index("ix_tasks_finding_id", "tasks", ["finding_id"])

    if not _has_table("document_versions"):
        op.create_table(
            "document_versions",
            sa.Column("version_id", sa.String(), nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=True),
            sa.Column("customer_id", sa.String(), nullable=True),
            sa.Column("document_id", sa.String(), nullable=True),
            sa.Column("version_number", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("reviewed_by", sa.String(), nullable=True),
            sa.Column("approved_by", sa.String(), nullable=True),
            sa.Column("regenerated_from", sa.String(), nullable=True),
            sa.Column("superseded_by", sa.String(), nullable=True),
            sa.Column("created_by", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.customer_id"]),
            sa.PrimaryKeyConstraint("version_id"),
        )
        op.create_index("ix_document_versions_tenant_id", "document_versions", ["tenant_id"])
        op.create_index("ix_document_versions_customer_id", "document_versions", ["customer_id"])
        op.create_index("ix_document_versions_document_id", "document_versions", ["document_id"])

    if not _has_table("jobs"):
        op.create_table(
            "jobs",
            sa.Column("job_id", sa.String(), nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("job_type", sa.String(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("retry_count", sa.Integer(), nullable=False),
            sa.Column("max_retries", sa.Integer(), nullable=False),
            sa.Column("last_error", sa.String(), nullable=True),
            sa.Column("result", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
            sa.PrimaryKeyConstraint("job_id"),
        )
        op.create_index("ix_jobs_tenant_id", "jobs", ["tenant_id"])

    if not _has_table("evidence"):
        op.create_table(
            "evidence",
            sa.Column("evidence_id", sa.String(), nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("customer_id", sa.String(), nullable=False),
            sa.Column("control_id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("type", sa.String(), nullable=False),
            sa.Column("uri", sa.String(), nullable=False),
            sa.Column("verified", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.customer_id"]),
            sa.ForeignKeyConstraint(["control_id"], ["controls.control_id"]),
            sa.PrimaryKeyConstraint("evidence_id"),
        )
        op.create_index("ix_evidence_tenant_id", "evidence", ["tenant_id"])
        op.create_index("ix_evidence_customer_id", "evidence", ["customer_id"])
        op.create_index("ix_evidence_control_id", "evidence", ["control_id"])


def downgrade() -> None:
    if _has_table("evidence"):
        op.drop_table("evidence")
    if _has_table("jobs"):
        op.drop_table("jobs")
    if _has_table("document_versions"):
        op.drop_table("document_versions")
    if _has_table("tasks"):
        op.drop_table("tasks")
    if _has_table("controls"):
        op.drop_table("controls")
    if _has_table("obligations"):
        op.drop_table("obligations")
    if _has_table("findings"):
        op.drop_table("findings")
    op.alter_column(
        "audit_events",
        "agent_id",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
