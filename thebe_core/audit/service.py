from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import Fernet
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from thebe_core.audit.store import (
    AuditEventDB,
    ControlDB,
    CustomerDB,
    DocumentVersionDB,
    EvaluationDB,
    EvidenceDB,
    FindingDB,
    ObligationDB,
    SQLModel,
    TaskDB,
)
from thebe_core.config import settings
from thebe_core.models import (
    AuditEvent,
    Customer,
    CustomerWorkspace,
    DocumentVersion,
    TimelineEvent,
)


class AuditService:
    """Evidence-grade async audit store backed by SQLModel/SQLAlchemy."""

    def __init__(self, database_url: str) -> None:
        self.engine = create_async_engine(
            database_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_recycle=settings.DB_POOL_RECYCLE,
        )
        self._fernet = self._load_fernet()

    def _load_fernet(self) -> Fernet:
        key = settings.PII_ENCRYPTION_KEY
        if key is None or key.get_secret_value() is None:
            raise RuntimeError(
                "PII_ENCRYPTION_KEY is required. "
                'Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        return Fernet(key.get_secret_value().encode())

    def _encrypt(self, snapshot: dict[str, Any]) -> dict[str, str]:
        plaintext = json.dumps(snapshot, sort_keys=True).encode()
        token = self._fernet.encrypt(plaintext)
        return {"__encrypted__": base64.b64encode(token).decode()}

    def _decrypt(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        if "__encrypted__" not in snapshot:
            return dict(snapshot)
        token = base64.b64decode(snapshot["__encrypted__"].encode())
        plaintext = self._fernet.decrypt(token)
        return json.loads(plaintext)

    async def create_tables(self) -> None:
        """Create all tables asynchronously."""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    # ------------------------------------------------------------------
    # Audit events
    # ------------------------------------------------------------------

    async def log_event(self, event: AuditEvent) -> str:
        """Store an AuditEvent and return its event_id."""
        db_event = AuditEventDB(
            event_id=event.event_id,
            tenant_id=event.tenant_id,
            timestamp=event.timestamp,
            vertical=event.vertical,
            customer_id=event.customer_id,
            agent_id=event.agent_id,
            action=event.action,
            input_snapshot=self._encrypt(event.input_snapshot),
            output_snapshot=self._encrypt(event.output_snapshot),
            event_metadata=event.metadata,
        )
        async with AsyncSession(self.engine) as session:
            session.add(db_event)
            await session.commit()
        return event.event_id

    async def query_events(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit events by tenant_id, customer_id, vertical, action, and time range."""
        filters = filters or {}
        stmt = select(AuditEventDB)

        if "tenant_id" in filters:
            stmt = stmt.where(AuditEventDB.tenant_id == filters["tenant_id"])
        if "customer_id" in filters:
            stmt = stmt.where(AuditEventDB.customer_id == filters["customer_id"])
        if "vertical" in filters:
            stmt = stmt.where(AuditEventDB.vertical == filters["vertical"])
        if "agent_id" in filters:
            stmt = stmt.where(AuditEventDB.agent_id == filters["agent_id"])
        if "action" in filters:
            stmt = stmt.where(AuditEventDB.action == filters["action"])
        if "from" in filters:
            stmt = stmt.where(AuditEventDB.timestamp >= filters["from"])
        if "to" in filters:
            stmt = stmt.where(AuditEventDB.timestamp <= filters["to"])

        stmt = stmt.order_by(AuditEventDB.timestamp.desc()).limit(limit)

        async with AsyncSession(self.engine) as session:
            result = await session.execute(stmt)
            rows = result.scalars().all()

        events: list[AuditEvent] = []
        for row in rows:
            data = row.model_dump()
            data["metadata"] = data.pop("event_metadata", {})
            data["input_snapshot"] = self._decrypt(data["input_snapshot"])
            data["output_snapshot"] = self._decrypt(data["output_snapshot"])
            events.append(AuditEvent(**data))
        return events

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    async def create_customer(
        self,
        customer_id: str,
        tenant_id: str,
        vertical: str,
        name: str,
        slug: str | None = None,
        status: str = "draft",
        context: dict[str, Any] | None = None,
    ) -> str:
        """Create a customer record with encrypted PII context."""
        customer = CustomerDB(
            customer_id=customer_id,
            tenant_id=tenant_id,
            vertical=vertical,
            name=name,
            slug=slug,
            status=status,
            context=self._encrypt(context or {}),
        )
        async with AsyncSession(self.engine) as session:
            session.add(customer)
            await session.commit()
        return customer_id

    async def get_customer(
        self, customer_id: str, tenant_id: str
    ) -> CustomerDB | None:
        """Fetch a customer record by id, scoped to a tenant."""
        async with AsyncSession(self.engine) as session:
            stmt = select(CustomerDB).where(
                CustomerDB.customer_id == customer_id,
                CustomerDB.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            customer = result.scalars().first()
            if customer is not None:
                customer.context = self._decrypt(customer.context)
            return customer

    async def update_customer(
        self,
        customer_id: str,
        tenant_id: str,
        name: str | None = None,
        slug: str | None = None,
        status: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> CustomerDB | None:
        """Update a customer record and return the updated row."""
        async with AsyncSession(self.engine) as session:
            stmt = select(CustomerDB).where(
                CustomerDB.customer_id == customer_id,
                CustomerDB.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            customer = result.scalars().first()
            if customer is None:
                return None

            if name is not None:
                customer.name = name
            if slug is not None:
                customer.slug = slug
            if status is not None:
                customer.status = status
                if status == "archived":
                    customer.archived_at = datetime.now(timezone.utc)
                else:
                    customer.archived_at = None
            if context is not None:
                customer.context = self._encrypt(context)
            customer.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(customer)
            customer.context = self._decrypt(customer.context)
            return customer

    async def list_customers(
        self,
        tenant_id: str,
        status: str | None = None,
        limit: int = 100,
    ) -> list[CustomerDB]:
        """List customer records scoped to a tenant, optionally filtered by status."""
        async with AsyncSession(self.engine) as session:
            stmt = select(CustomerDB).where(CustomerDB.tenant_id == tenant_id)
            if status is not None:
                stmt = stmt.where(CustomerDB.status == status)
            stmt = stmt.order_by(CustomerDB.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            rows = list(result.scalars().all())
            for row in rows:
                row.context = self._decrypt(row.context)
            return rows

    # ------------------------------------------------------------------
    # Evaluations
    # ------------------------------------------------------------------

    async def persist_evaluation(
        self,
        evaluation_id: str,
        tenant_id: str,
        customer_id: str,
        vertical: str,
        entity_type: str,
        score: float | None,
        rule_results: list[dict[str, Any]],
        violations: list[dict[str, Any]],
        required_actions: list[str],
    ) -> None:
        """Persist an evaluation result for timeline and workspace summaries."""
        async with AsyncSession(self.engine) as session:
            session.add(
                EvaluationDB(
                    evaluation_id=evaluation_id,
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    vertical=vertical,
                    entity_type=entity_type,
                    score=score,
                    rule_results=rule_results,
                    violations=violations,
                    required_actions=required_actions,
                )
            )
            await session.commit()

    async def get_latest_evaluation(
        self, customer_id: str, tenant_id: str
    ) -> EvaluationDB | None:
        """Return the most recent evaluation for a customer."""
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(EvaluationDB)
                .where(
                    EvaluationDB.customer_id == customer_id,
                    EvaluationDB.tenant_id == tenant_id,
                )
                .order_by(EvaluationDB.created_at.desc())
                .limit(1)
            )
            return result.scalars().first()

    # ------------------------------------------------------------------
    # Findings
    # ------------------------------------------------------------------

    async def create_finding(
        self,
        finding_id: str,
        tenant_id: str,
        customer_id: str,
        evaluation_id: str | None,
        title: str,
        description: str,
        severity: str,
        status: str = "open",
        assignee: str | None = None,
        due_date: datetime | None = None,
        closure_evidence: dict[str, Any] | None = None,
        rule_id: str | None = None,
    ) -> FindingDB:
        """Create a new finding linked to a customer and optionally an evaluation."""
        finding = FindingDB(
            finding_id=finding_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            evaluation_id=evaluation_id,
            rule_id=rule_id,
            title=title,
            description=description,
            severity=severity,
            status=status,
            assignee=assignee,
            due_date=due_date,
            closure_evidence=closure_evidence or {},
        )
        async with AsyncSession(self.engine) as session:
            session.add(finding)
            await session.commit()
            await session.refresh(finding)
        return finding

    async def get_finding(
        self, finding_id: str, tenant_id: str
    ) -> FindingDB | None:
        """Fetch a finding by id scoped to a tenant."""
        async with AsyncSession(self.engine) as session:
            row = await session.get(FindingDB, finding_id)
            if row is None or row.tenant_id != tenant_id:
                return None
            return row

    async def list_findings(
        self,
        tenant_id: str,
        customer_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        assignee: str | None = None,
        sort: str = "created_at_desc",
        limit: int = 100,
    ) -> list[FindingDB]:
        """List findings for a tenant with optional filters."""
        async with AsyncSession(self.engine) as session:
            stmt = select(FindingDB).where(FindingDB.tenant_id == tenant_id)
            if customer_id is not None:
                stmt = stmt.where(FindingDB.customer_id == customer_id)
            if status is not None:
                stmt = stmt.where(FindingDB.status == status)
            if severity is not None:
                stmt = stmt.where(FindingDB.severity == severity)
            if assignee is not None:
                stmt = stmt.where(FindingDB.assignee == assignee)

            field, _, direction = sort.partition("_")
            order_field = getattr(FindingDB, field, FindingDB.created_at)
            if direction == "asc":
                stmt = stmt.order_by(order_field.asc())
            else:
                stmt = stmt.order_by(order_field.desc())

            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    _FINDING_TRANSITIONS: dict[str, set[str]] = {
        "open": {"triaged", "assigned", "resolved", "closed"},
        "triaged": {"assigned", "resolved", "closed"},
        "assigned": {"resolved", "closed"},
        "resolved": {"closed"},
        "closed": set(),
    }

    async def update_finding(
        self,
        finding_id: str,
        tenant_id: str,
        status: str | None = None,
        assignee: str | None = None,
        due_date: datetime | None = None,
        closure_evidence: dict[str, Any] | None = None,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> FindingDB | None:
        """Update a finding and log any state transition."""
        async with AsyncSession(self.engine) as session:
            row = await session.get(FindingDB, finding_id)
            if row is None or row.tenant_id != tenant_id:
                return None

            if status is not None and status != row.status:
                allowed = self._FINDING_TRANSITIONS.get(row.status, set())
                if status not in allowed:
                    raise ValueError(
                        f"Invalid finding transition: {row.status} -> {status}"
                    )
                old_status = row.status
                row.status = status
                event = AuditEvent(
                    tenant_id=tenant_id,
                    vertical="findings",
                    customer_id=row.customer_id or "",
                    agent_id="api",
                    action="finding_status_changed",
                    input_snapshot={
                        "old_status": old_status,
                        "new_status": status,
                        "reason": reason,
                    },
                    output_snapshot={
                        "finding_id": finding_id,
                        "actor_id": actor_id,
                    },
                    metadata={"actor_id": actor_id, "reason": reason},
                )
                await self.log_event(event)

            if assignee is not None:
                row.assignee = assignee
            if due_date is not None:
                row.due_date = due_date
            if closure_evidence is not None:
                row.closure_evidence = closure_evidence

            row.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(row)
            return row

    async def upsert_findings_from_result(
        self,
        tenant_id: str,
        customer_id: str,
        evaluation_id: str,
        rule_results: list[dict[str, Any]],
    ) -> None:
        """Create or update findings based on FAIL/PARTIAL/PASS rule results."""
        async with AsyncSession(self.engine) as session:
            stmt = select(FindingDB).where(
                FindingDB.tenant_id == tenant_id,
                FindingDB.customer_id == customer_id,
            )
            result = await session.execute(stmt)
            existing = {row.rule_id: row for row in result.scalars().all() if row.rule_id}

        for r in rule_results:
            status = r.get("status")
            rule_id = r.get("rule_id")
            if status in {"FAIL", "PARTIAL"}:
                if rule_id in existing and existing[rule_id].status != "closed":
                    continue
                await self.create_finding(
                    finding_id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    evaluation_id=evaluation_id,
                    title=r.get("description") or r.get("rule_id"),
                    description=r.get("description") or "",
                    severity=r.get("severity", "medium"),
                    status="open",
                    rule_id=rule_id,
                )
            elif status == "PASS":
                finding = existing.get(rule_id)
                if finding and finding.status not in {"closed", "resolved"}:
                    await self.update_finding(
                        finding_id=finding.finding_id,
                        tenant_id=tenant_id,
                        status="resolved",
                        reason="Rule now passing",
                    )

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    async def create_task(
        self,
        task_id: str,
        tenant_id: str,
        customer_id: str,
        finding_id: str | None,
        title: str,
        assignee: str | None = None,
        due_date: datetime | None = None,
        status: str = "todo",
    ) -> TaskDB:
        """Create a remediation task linked to a finding."""
        task = TaskDB(
            task_id=task_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            finding_id=finding_id,
            title=title,
            assignee=assignee,
            due_date=due_date,
            status=status,
        )
        async with AsyncSession(self.engine) as session:
            session.add(task)
            await session.commit()
            await session.refresh(task)
        return task

    async def get_task(self, task_id: str, tenant_id: str) -> TaskDB | None:
        """Fetch a task by id scoped to a tenant."""
        async with AsyncSession(self.engine) as session:
            row = await session.get(TaskDB, task_id)
            if row is None or row.tenant_id != tenant_id:
                return None
            return row

    async def list_tasks(
        self,
        tenant_id: str,
        customer_id: str | None = None,
        finding_id: str | None = None,
        status: str | None = None,
        assignee: str | None = None,
        sort: str = "created_at_desc",
        limit: int = 100,
    ) -> list[TaskDB]:
        """List tasks for a tenant with optional filters."""
        async with AsyncSession(self.engine) as session:
            stmt = select(TaskDB).where(TaskDB.tenant_id == tenant_id)
            if customer_id is not None:
                stmt = stmt.where(TaskDB.customer_id == customer_id)
            if finding_id is not None:
                stmt = stmt.where(TaskDB.finding_id == finding_id)
            if status is not None:
                stmt = stmt.where(TaskDB.status == status)
            if assignee is not None:
                stmt = stmt.where(TaskDB.assignee == assignee)

            field, _, direction = sort.partition("_")
            order_field = getattr(TaskDB, field, TaskDB.created_at)
            if direction == "asc":
                stmt = stmt.order_by(order_field.asc())
            else:
                stmt = stmt.order_by(order_field.desc())

            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    _TASK_TRANSITIONS: dict[str, set[str]] = {
        "todo": {"in_progress", "awaiting_evidence", "done"},
        "in_progress": {"awaiting_evidence", "done"},
        "awaiting_evidence": {"done"},
        "done": set(),
    }

    async def update_task(
        self,
        task_id: str,
        tenant_id: str,
        title: str | None = None,
        finding_id: str | None = None,
        set_finding_id: bool = False,
        status: str | None = None,
        assignee: str | None = None,
        due_date: datetime | None = None,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> TaskDB | None:
        """Update a task and log any state transition."""
        async with AsyncSession(self.engine) as session:
            row = await session.get(TaskDB, task_id)
            if row is None or row.tenant_id != tenant_id:
                return None

            if title is not None:
                cleaned = title.strip()
                if not cleaned:
                    raise ValueError("Task title cannot be empty")
                row.title = cleaned

            if set_finding_id:
                row.finding_id = finding_id or None

            if status is not None and status != row.status:
                allowed = self._TASK_TRANSITIONS.get(row.status, set())
                if status not in allowed:
                    raise ValueError(
                        f"Invalid task transition: {row.status} -> {status}"
                    )
                old_status = row.status
                row.status = status
                event = AuditEvent(
                    tenant_id=tenant_id,
                    vertical="tasks",
                    customer_id=row.customer_id or "",
                    agent_id="api",
                    action="task_status_changed",
                    input_snapshot={
                        "old_status": old_status,
                        "new_status": status,
                        "reason": reason,
                    },
                    output_snapshot={
                        "task_id": task_id,
                        "actor_id": actor_id,
                    },
                    metadata={"actor_id": actor_id, "reason": reason},
                )
                await self.log_event(event)

            if assignee is not None:
                row.assignee = assignee or None
            if due_date is not None:
                row.due_date = due_date

            row.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(row)
            return row

    async def delete_task(self, task_id: str, tenant_id: str) -> bool:
        """Delete a task scoped to a tenant. Returns False if missing."""
        async with AsyncSession(self.engine) as session:
            row = await session.get(TaskDB, task_id)
            if row is None or row.tenant_id != tenant_id:
                return False
            await session.delete(row)
            await session.commit()
            return True

    # ------------------------------------------------------------------
    # Document versions
    # ------------------------------------------------------------------

    async def create_document_version(
        self,
        version_id: str,
        tenant_id: str,
        customer_id: str,
        document_id: str,
        version_number: int,
        status: str,
        content: str,
        created_by: str | None,
        reviewed_by: str | None = None,
        approved_by: str | None = None,
        regenerated_from: str | None = None,
    ) -> DocumentVersion:
        """Persist a document version snapshot."""
        version = DocumentVersionDB(
            version_id=version_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            document_id=document_id,
            version_number=version_number,
            status=status,
            content=content,
            created_by=created_by,
            reviewed_by=reviewed_by,
            approved_by=approved_by,
            regenerated_from=regenerated_from,
        )
        async with AsyncSession(self.engine) as session:
            session.add(version)
            await session.commit()
            await session.refresh(version)
            return DocumentVersion(**version.model_dump())

    async def _get_current_document_version(
        self, document_id: str, tenant_id: str
    ) -> DocumentVersion | None:
        """Return the current (unsuperseded) version of a document."""
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(DocumentVersionDB)
                .where(
                    DocumentVersionDB.document_id == document_id,
                    DocumentVersionDB.tenant_id == tenant_id,
                    DocumentVersionDB.superseded_by.is_(None),
                )
                .order_by(DocumentVersionDB.version_number.desc())
                .limit(1)
            )
            row = result.scalars().first()
            if row is None:
                return None
            return DocumentVersion(**row.model_dump())

    async def list_current_documents(
        self,
        tenant_id: str,
        customer_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[DocumentVersion]:
        """List the current version of each document for a tenant."""
        async with AsyncSession(self.engine) as session:
            stmt = (
                select(DocumentVersionDB)
                .where(
                    DocumentVersionDB.tenant_id == tenant_id,
                    DocumentVersionDB.superseded_by.is_(None),
                )
                .order_by(DocumentVersionDB.created_at.desc())
                .limit(limit)
            )
            if customer_id is not None:
                stmt = stmt.where(DocumentVersionDB.customer_id == customer_id)
            if status is not None:
                stmt = stmt.where(DocumentVersionDB.status == status)
            result = await session.execute(stmt)
            return [
                DocumentVersion(**row.model_dump())
                for row in result.scalars().all()
            ]

    async def list_document_versions(
        self,
        document_id: str,
        tenant_id: str,
        limit: int = 100,
    ) -> list[DocumentVersion]:
        """Return version history for a document."""
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(DocumentVersionDB)
                .where(
                    DocumentVersionDB.document_id == document_id,
                    DocumentVersionDB.tenant_id == tenant_id,
                )
                .order_by(DocumentVersionDB.version_number.desc())
                .limit(limit)
            )
            return [
                DocumentVersion(**row.model_dump())
                for row in result.scalars().all()
            ]

    async def review_document(
        self,
        document_id: str,
        tenant_id: str,
        actor_id: str,
    ) -> DocumentVersion | None:
        """Mark the current document version as reviewed by an actor."""
        current = await self._get_current_document_version(document_id, tenant_id)
        if current is None:
            return None
        new_version_id = str(uuid.uuid4())
        new_version = await self.create_document_version(
            version_id=new_version_id,
            tenant_id=tenant_id,
            customer_id=current.customer_id or "",
            document_id=document_id,
            version_number=current.version_number + 1,
            status="reviewed",
            content=current.content,
            created_by=actor_id,
            reviewed_by=actor_id,
            regenerated_from=current.version_id,
        )
        async with AsyncSession(self.engine) as session:
            current_db = await session.get(DocumentVersionDB, current.version_id)
            if current_db is None:
                return None
            current_db.superseded_by = new_version.version_id
            current_db.updated_at = datetime.now(timezone.utc)
            await session.commit()

        event = AuditEvent(
            tenant_id=tenant_id,
            vertical="documents",
            customer_id=current.customer_id or "",
            agent_id="api",
            action="document_reviewed",
            input_snapshot={
                "document_id": document_id,
                "previous_version_id": current.version_id,
            },
            output_snapshot={
                "version_id": new_version.version_id,
                "reviewed_by": actor_id,
            },
            metadata={"actor_id": actor_id},
        )
        await self.log_event(event)
        return new_version

    async def approve_document(
        self,
        document_id: str,
        tenant_id: str,
        actor_id: str,
    ) -> DocumentVersion | None:
        """Approve the current document version; requires prior review by another actor."""
        current = await self._get_current_document_version(document_id, tenant_id)
        if current is None:
            return None
        if current.status != "reviewed":
            raise ValueError("Document must be reviewed before approval")
        if not current.reviewed_by or current.reviewed_by == actor_id:
            raise ValueError("Approver cannot be the same as reviewer")

        new_version_id = str(uuid.uuid4())
        new_version = await self.create_document_version(
            version_id=new_version_id,
            tenant_id=tenant_id,
            customer_id=current.customer_id or "",
            document_id=document_id,
            version_number=current.version_number + 1,
            status="approved",
            content=current.content,
            created_by=actor_id,
            reviewed_by=current.reviewed_by,
            approved_by=actor_id,
            regenerated_from=current.version_id,
        )
        async with AsyncSession(self.engine) as session:
            current_db = await session.get(DocumentVersionDB, current.version_id)
            if current_db is None:
                return None
            current_db.superseded_by = new_version.version_id
            current_db.updated_at = datetime.now(timezone.utc)
            await session.commit()

        event = AuditEvent(
            tenant_id=tenant_id,
            vertical="documents",
            customer_id=current.customer_id or "",
            agent_id="api",
            action="document_approved",
            input_snapshot={
                "document_id": document_id,
                "previous_version_id": current.version_id,
            },
            output_snapshot={
                "version_id": new_version.version_id,
                "approved_by": actor_id,
            },
            metadata={"actor_id": actor_id},
        )
        await self.log_event(event)
        return new_version

    async def regenerate_document(
        self,
        document_id: str,
        tenant_id: str,
        actor_id: str,
        content: str | None = None,
    ) -> DocumentVersion | None:
        """Create a new generated version of a document."""
        current = await self._get_current_document_version(document_id, tenant_id)
        if current is None:
            return None
        new_version_id = str(uuid.uuid4())
        new_version = await self.create_document_version(
            version_id=new_version_id,
            tenant_id=tenant_id,
            customer_id=current.customer_id or "",
            document_id=document_id,
            version_number=current.version_number + 1,
            status="generated",
            content=content if content is not None else current.content,
            created_by=actor_id,
            regenerated_from=current.version_id,
        )
        async with AsyncSession(self.engine) as session:
            current_db = await session.get(DocumentVersionDB, current.version_id)
            if current_db is None:
                return None
            current_db.superseded_by = new_version.version_id
            current_db.updated_at = datetime.now(timezone.utc)
            await session.commit()

        event = AuditEvent(
            tenant_id=tenant_id,
            vertical="documents",
            customer_id=current.customer_id or "",
            agent_id="api",
            action="document_regenerated",
            input_snapshot={"document_id": document_id},
            output_snapshot={
                "version_id": new_version.version_id,
                "regenerated_from": current.version_id,
            },
            metadata={"actor_id": actor_id},
        )
        await self.log_event(event)
        return new_version

    # ------------------------------------------------------------------
    # Workspace & timeline
    # ------------------------------------------------------------------

    async def get_customer_workspace(
        self, customer_id: str, tenant_id: str
    ) -> CustomerWorkspace | None:
        """Return a workspace summary for a customer."""
        async with AsyncSession(self.engine) as session:
            customer = await session.get(CustomerDB, customer_id)
            if customer is None or customer.tenant_id != tenant_id:
                return None

            eval_count = await session.scalar(
                select(func.count(EvaluationDB.evaluation_id)).where(
                    EvaluationDB.customer_id == customer_id,
                    EvaluationDB.tenant_id == tenant_id,
                )
            )
            doc_count = await session.scalar(
                select(func.count(DocumentVersionDB.version_id)).where(
                    DocumentVersionDB.customer_id == customer_id,
                    DocumentVersionDB.tenant_id == tenant_id,
                )
            )
            event_count = await session.scalar(
                select(func.count(AuditEventDB.event_id)).where(
                    AuditEventDB.customer_id == customer_id,
                    AuditEventDB.tenant_id == tenant_id,
                )
            )

            open_findings_count = await session.scalar(
                select(func.count(FindingDB.finding_id)).where(
                    FindingDB.customer_id == customer_id,
                    FindingDB.tenant_id == tenant_id,
                    FindingDB.status.in_(["open", "triaged", "assigned"]),
                )
            )

            latest_eval = await self.get_latest_evaluation(customer_id, tenant_id)

            latest_time = max(
                filter(
                    None,
                    [
                        customer.updated_at,
                        latest_eval.created_at if latest_eval else None,
                    ],
                ),
                default=None,
            )

            obligations = [
                self._row_to_dict(o)
                for o in await self.list_obligations(tenant_id, customer_id)
            ]
            controls = [
                self._row_to_dict(c)
                for c in await self.list_controls(tenant_id, customer_id)
            ]
            evidence = [
                self._row_to_dict(e)
                for e in await self.list_evidence(tenant_id, customer_id=customer_id)
            ]

            customer.context = self._decrypt(customer.context)
            latest_eval_dict = self._row_to_dict(latest_eval) if latest_eval else None

            return CustomerWorkspace(
                customer=Customer(**customer.model_dump()),
                obligations=obligations,
                controls=controls,
                evidence=evidence,
                latest_evaluation=latest_eval_dict,
                evaluation_count=eval_count or 0,
                document_count=doc_count or 0,
                audit_event_count=event_count or 0,
                open_findings_count=open_findings_count or 0,
                latest_evaluation_id=latest_eval.evaluation_id if latest_eval else None,
                latest_score=latest_eval.score if latest_eval else None,
                latest_activity_at=latest_time,
            )

    async def get_customer_timeline(
        self, customer_id: str, tenant_id: str, limit: int = 100
    ) -> list[TimelineEvent]:
        """Build a chronological evidence timeline for a customer."""
        events: list[TimelineEvent] = []
        async with AsyncSession(self.engine) as session:
            audit_rows = await session.scalars(
                select(AuditEventDB)
                .where(
                    AuditEventDB.customer_id == customer_id,
                    AuditEventDB.tenant_id == tenant_id,
                )
                .order_by(AuditEventDB.timestamp.desc())
                .limit(limit)
            )
            for row in audit_rows:
                events.append(
                    TimelineEvent(
                        event_id=row.event_id,
                        event_type="audit",
                        artifact_id=row.event_id,
                        action=row.action,
                        timestamp=row.timestamp,
                        actor_id=None,
                        vertical=row.vertical,
                        summary=f"{row.action} via {row.agent_id}",
                        links={"audit": f"/audit?event_id={row.event_id}"},
                    )
                )

            eval_rows = await session.scalars(
                select(EvaluationDB)
                .where(
                    EvaluationDB.customer_id == customer_id,
                    EvaluationDB.tenant_id == tenant_id,
                )
                .order_by(EvaluationDB.created_at.desc())
                .limit(limit)
            )
            for row in eval_rows:
                score_str = f"{row.score:.0%}" if row.score is not None else "N/A"
                events.append(
                    TimelineEvent(
                        event_id=str(uuid.uuid4()),
                        event_type="evaluation",
                        artifact_id=row.evaluation_id,
                        action="evaluation_complete",
                        timestamp=row.created_at,
                        actor_id="api",
                        vertical=row.vertical,
                        summary=f"Evaluation completed with score {score_str}",
                        links={
                            "evaluation": f"/customers/{customer_id}/evaluations/{row.evaluation_id}"
                        },
                    )
                )

            doc_rows = await session.scalars(
                select(DocumentVersionDB)
                .where(
                    DocumentVersionDB.customer_id == customer_id,
                    DocumentVersionDB.tenant_id == tenant_id,
                )
                .order_by(DocumentVersionDB.created_at.desc())
                .limit(limit)
            )
            for row in doc_rows:
                events.append(
                    TimelineEvent(
                        event_id=str(uuid.uuid4()),
                        event_type="document",
                        artifact_id=row.version_id,
                        action="document_generated",
                        timestamp=row.created_at,
                        actor_id="api",
                        vertical="documents",
                        summary=f"Generated {row.status} document",
                        links={
                            "document": f"/customers/{customer_id}/documents/{row.document_id}"
                        },
                    )
                )

        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    # ------------------------------------------------------------------
    # Obligations & controls
    # ------------------------------------------------------------------

    async def create_obligation(
        self,
        obligation_id: str,
        tenant_id: str,
        customer_id: str,
        name: str,
        description: str = "",
        status: str = "pending",
        linked_finding_id: str | None = None,
        linked_document_id: str | None = None,
        obligation_key: str | None = None,
        rule_id: str | None = None,
    ) -> ObligationDB:
        """Create a customer-specific obligation."""
        obligation = ObligationDB(
            obligation_id=obligation_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            obligation_key=obligation_key,
            rule_id=rule_id,
            name=name,
            description=description,
            status=status,
            linked_finding_id=linked_finding_id,
            linked_document_id=linked_document_id,
        )
        async with AsyncSession(self.engine) as session:
            session.add(obligation)
            await session.commit()
            await session.refresh(obligation)
        return obligation

    async def list_obligations(
        self,
        tenant_id: str,
        customer_id: str,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ObligationDB]:
        """List obligations for a customer, scoped to a tenant."""
        async with AsyncSession(self.engine) as session:
            stmt = (
                select(ObligationDB)
                .where(
                    ObligationDB.tenant_id == tenant_id,
                    ObligationDB.customer_id == customer_id,
                )
                .order_by(ObligationDB.created_at.desc())
                .limit(limit)
            )
            if status is not None:
                stmt = stmt.where(ObligationDB.status == status)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_obligation(
        self,
        obligation_id: str,
        tenant_id: str,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        linked_finding_id: str | None = None,
        linked_document_id: str | None = None,
    ) -> ObligationDB | None:
        """Update an obligation and return the updated row."""
        async with AsyncSession(self.engine) as session:
            row = await session.get(ObligationDB, obligation_id)
            if row is None or row.tenant_id != tenant_id:
                return None

            if name is not None:
                row.name = name
            if description is not None:
                row.description = description
            if status is not None:
                row.status = status
            if linked_finding_id is not None:
                row.linked_finding_id = linked_finding_id
            if linked_document_id is not None:
                row.linked_document_id = linked_document_id

            row.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(row)
            return row

    async def create_control(
        self,
        control_id: str,
        tenant_id: str,
        customer_id: str,
        name: str,
        description: str = "",
        status: str = "pending",
        linked_obligation_id: str | None = None,
        linked_finding_id: str | None = None,
        linked_document_id: str | None = None,
        control_key: str | None = None,
        rule_id: str | None = None,
        obligation_key: str | None = None,
        answer: str = "unanswered",
        owner: str | None = None,
        last_reviewed_at: datetime | None = None,
    ) -> ControlDB:
        """Create a customer-specific control."""
        control = ControlDB(
            control_id=control_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            control_key=control_key,
            rule_id=rule_id,
            obligation_key=obligation_key,
            name=name,
            description=description,
            status=status,
            answer=answer,
            owner=owner,
            last_reviewed_at=last_reviewed_at,
            linked_obligation_id=linked_obligation_id,
            linked_finding_id=linked_finding_id,
            linked_document_id=linked_document_id,
        )
        async with AsyncSession(self.engine) as session:
            session.add(control)
            await session.commit()
            await session.refresh(control)
        return control

    async def list_controls(
        self,
        tenant_id: str,
        customer_id: str,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ControlDB]:
        """List controls for a customer, scoped to a tenant."""
        async with AsyncSession(self.engine) as session:
            stmt = (
                select(ControlDB)
                .where(
                    ControlDB.tenant_id == tenant_id,
                    ControlDB.customer_id == customer_id,
                )
                .order_by(ControlDB.created_at.desc())
                .limit(limit)
            )
            if status is not None:
                stmt = stmt.where(ControlDB.status == status)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_control(
        self,
        control_id: str,
        tenant_id: str,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        linked_obligation_id: str | None = None,
        linked_finding_id: str | None = None,
        linked_document_id: str | None = None,
        answer: str | None = None,
        owner: str | None = None,
        last_reviewed_at: datetime | None = None,
    ) -> ControlDB | None:
        """Update a control and return the updated row."""
        async with AsyncSession(self.engine) as session:
            row = await session.get(ControlDB, control_id)
            if row is None or row.tenant_id != tenant_id:
                return None

            if name is not None:
                row.name = name
            if description is not None:
                row.description = description
            if status is not None:
                row.status = status
            if answer is not None:
                row.answer = answer
                row.status = self._answer_status(answer)
            if owner is not None:
                row.owner = owner
            if last_reviewed_at is not None:
                row.last_reviewed_at = last_reviewed_at
            if linked_obligation_id is not None:
                row.linked_obligation_id = linked_obligation_id
            if linked_finding_id is not None:
                row.linked_finding_id = linked_finding_id
            if linked_document_id is not None:
                row.linked_document_id = linked_document_id

            row.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(row)
            return row

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------

    async def create_evidence(
        self,
        evidence_id: str,
        tenant_id: str,
        customer_id: str,
        control_id: str,
        name: str,
        type: str,
        uri: str,
        verified: bool = False,
    ) -> EvidenceDB:
        """Create proof linked to a control."""
        evidence = EvidenceDB(
            evidence_id=evidence_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            control_id=control_id,
            name=name,
            type=type,
            uri=uri,
            verified=verified,
        )
        async with AsyncSession(self.engine) as session:
            session.add(evidence)
            await session.commit()
            await session.refresh(evidence)
        return evidence

    async def list_evidence(
        self,
        tenant_id: str,
        customer_id: str | None = None,
        control_id: str | None = None,
        limit: int = 100,
    ) -> list[EvidenceDB]:
        """List evidence for a tenant, optionally filtered by customer or control."""
        async with AsyncSession(self.engine) as session:
            stmt = select(EvidenceDB).where(EvidenceDB.tenant_id == tenant_id)
            if customer_id is not None:
                stmt = stmt.where(EvidenceDB.customer_id == customer_id)
            if control_id is not None:
                stmt = stmt.where(EvidenceDB.control_id == control_id)
            stmt = stmt.order_by(EvidenceDB.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_evidence(
        self,
        evidence_id: str,
        tenant_id: str,
        customer_id: str,
        control_id: str | None = None,
        name: str | None = None,
        type: str | None = None,
        uri: str | None = None,
    ) -> EvidenceDB | None:
        """Update proof linked to a control."""
        async with AsyncSession(self.engine) as session:
            row = await session.get(EvidenceDB, evidence_id)
            if (
                row is None
                or row.tenant_id != tenant_id
                or row.customer_id != customer_id
            ):
                return None

            if control_id is not None:
                control = await session.get(ControlDB, control_id)
                if (
                    control is None
                    or control.tenant_id != tenant_id
                    or control.customer_id != customer_id
                ):
                    raise ValueError("Control not found")
                row.control_id = control_id
            if name is not None:
                cleaned = name.strip()
                if not cleaned:
                    raise ValueError("Evidence name cannot be empty")
                row.name = cleaned
            if type is not None:
                row.type = type
            if uri is not None:
                cleaned_uri = uri.strip()
                if not cleaned_uri:
                    raise ValueError("Evidence URI cannot be empty")
                row.uri = cleaned_uri

            row.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(row)
            return row

    async def delete_evidence(
        self, evidence_id: str, tenant_id: str, customer_id: str
    ) -> bool:
        """Delete proof scoped to a customer. Returns False if missing."""
        async with AsyncSession(self.engine) as session:
            row = await session.get(EvidenceDB, evidence_id)
            if (
                row is None
                or row.tenant_id != tenant_id
                or row.customer_id != customer_id
            ):
                return False
            await session.delete(row)
            await session.commit()
            return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _answer_status(answer: str) -> str:
        if answer == "yes":
            return "implemented"
        if answer == "no":
            return "failed"
        if answer == "not_sure":
            return "partial"
        return "pending"

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        if row is None:
            return {}
        return row.model_dump()
