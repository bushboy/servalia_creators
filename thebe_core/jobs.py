from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from prometheus_client import Counter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from thebe_core.audit.service import AuditService
from thebe_core.audit.store import AuditEventDB, CustomerDB, JobDB
from thebe_core.verticals.pack import VerticalPack

logger = logging.getLogger("thebe.jobs")

JOBS_TOTAL = Counter(
    "thebe_jobs_total",
    "Total jobs processed",
    ["type", "status"],
)


class JobService:
    """In-process async job queue and worker for evaluation/doc generation."""

    def __init__(
        self,
        audit: AuditService,
        packs: dict[str, VerticalPack],
    ) -> None:
        self.audit = audit
        self.packs = packs
        self._event = asyncio.Event()
        self._shutdown = False

    async def create_job(
        self,
        tenant_id: str,
        job_type: str,
        payload: dict[str, Any],
        max_retries: int = 3,
    ) -> JobDB:
        """Enqueue a new background job."""
        now = datetime.now(timezone.utc)
        job = JobDB(
            job_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            job_type=job_type,
            payload=payload,
            status="pending",
            retry_count=0,
            max_retries=max_retries,
            created_at=now,
            updated_at=now,
        )
        async with AsyncSession(self.audit.engine) as session:
            session.add(job)
            await session.commit()
            await session.refresh(job)
        self._event.set()
        logger.info("Job %s enqueued: %s", job.job_id, job_type)
        return job

    async def get_job(self, job_id: str, tenant_id: str) -> JobDB | None:
        """Fetch a job scoped to a tenant."""
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(JobDB, job_id)
            if row is None or row.tenant_id != tenant_id:
                return None
            return row

    async def list_jobs(
        self,
        tenant_id: str,
        status: str | None = None,
        limit: int = 100,
    ) -> list[JobDB]:
        """List jobs for a tenant, optionally filtered by status."""
        async with AsyncSession(self.audit.engine) as session:
            stmt = select(JobDB).where(JobDB.tenant_id == tenant_id)
            if status is not None:
                stmt = stmt.where(JobDB.status == status)
            stmt = stmt.order_by(JobDB.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def retry_job(self, job_id: str, tenant_id: str) -> JobDB | None:
        """Reset a failed job back to pending."""
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(JobDB, job_id)
            if row is None or row.tenant_id != tenant_id:
                return None
            if row.status != "failed":
                return None
            row.status = "pending"
            row.retry_count = 0
            row.last_error = None
            row.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(row)
        self._event.set()
        logger.info("Job %s queued for retry", job_id)
        return row

    async def _next_pending(self) -> JobDB | None:
        async with AsyncSession(self.audit.engine) as session:
            stmt = (
                select(JobDB)
                .where(JobDB.status == "pending")
                .order_by(JobDB.created_at.asc())
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def run(self) -> None:
        """Worker loop that processes pending jobs."""
        while not self._shutdown:
            job = await self._next_pending()
            if job is None:
                self._event.clear()
                try:
                    await asyncio.wait_for(self._event.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    pass
                continue
            await self._process_job(job)

    def stop(self) -> None:
        self._shutdown = True
        self._event.set()

    async def _process_job(self, job: JobDB) -> None:
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(JobDB, job.job_id)
            if row is None or row.status != "pending":
                return
            row.status = "running"
            row.started_at = datetime.now(timezone.utc)
            row.updated_at = row.started_at
            await session.commit()

        try:
            result = await self._execute(job)
            async with AsyncSession(self.audit.engine) as session:
                row = await session.get(JobDB, job.job_id)
                if row is None:
                    return
                row.status = "completed"
                row.result = result
                row.last_error = None
                row.completed_at = datetime.now(timezone.utc)
                row.updated_at = row.completed_at
                await session.commit()
            JOBS_TOTAL.labels(type=job.job_type, status="completed").inc()
            logger.info("Job %s completed", job.job_id)
        except Exception as exc:
            logger.exception("Job %s failed: %s", job.job_id, exc)
            async with AsyncSession(self.audit.engine) as session:
                row = await session.get(JobDB, job.job_id)
                if row is None:
                    return
                row.retry_count += 1
                row.last_error = str(exc)
                if row.retry_count >= row.max_retries:
                    row.status = "failed"
                else:
                    row.status = "pending"
                row.updated_at = datetime.now(timezone.utc)
                await session.commit()
                requeue = row.status == "pending"
            JOBS_TOTAL.labels(type=job.job_type, status="failed").inc()
            if requeue:
                self._event.set()

    async def _execute(self, job: JobDB) -> dict[str, Any]:
        if job.job_type == "generate_assets":
            from thebe_core.creator.jobs import execute_generate_assets

            return await execute_generate_assets(self.audit, self.packs, job)
        if job.job_type == "mind_message":
            from thebe_core.creator.jobs import execute_mind_message

            return await execute_mind_message(self.audit, self.packs, job)
        if job.job_type == "build_package":
            from thebe_core.creator.jobs import execute_build_package

            return await execute_build_package(self.audit, self.packs, job)
        raise ValueError(f"Unsupported job type: {job.job_type}")

    async def get_system_events(self, tenant_id: str) -> list[dict[str, Any]]:
        """Return actionable system signals for the admin observability page."""
        events: list[dict[str, Any]] = []

        failed_jobs = await self.list_jobs(tenant_id, status="failed", limit=20)
        for job in failed_jobs:
            events.append({
                "event_id": job.job_id,
                "event_type": "failed_job",
                "severity": "high",
                "message": f"Job {job.job_type} failed after {job.retry_count} retries",
                "occurred_at": job.updated_at,
                "artifact_id": job.job_id,
                "link": f"/settings/system?job={job.job_id}",
            })

        threshold = datetime.now(timezone.utc) - timedelta(hours=24)
        async with AsyncSession(self.audit.engine) as session:
            customer_id_col: Any = CustomerDB.customer_id
            customer_name_col: Any = CustomerDB.name
            event_ts_col: Any = AuditEventDB.timestamp
            subq = (
                select(
                    customer_id_col,
                    customer_name_col,
                    func.max(event_ts_col).label("last_event"),
                )
                .where(
                    CustomerDB.tenant_id == tenant_id,
                    CustomerDB.status != "archived",
                )
                .outerjoin(
                    AuditEventDB,
                    AuditEventDB.customer_id == CustomerDB.customer_id,
                )
                .group_by(CustomerDB.customer_id, CustomerDB.name)
            )
            result = await session.execute(subq)
            for customer_id, name, last_event in result.all():
                if last_event is None or last_event < threshold:
                    events.append({
                        "event_id": f"stale-audit-{customer_id}",
                        "event_type": "stale_audit",
                        "severity": "medium",
                        "message": f"No recent audit activity for {name}",
                        "occurred_at": last_event
                        if last_event is not None
                        else threshold,
                        "artifact_id": customer_id,
                        "link": f"/audit?customer_id={customer_id}",
                    })

        auth_actions = {"authentication_failed", "authorization_failed"}
        async with AsyncSession(self.audit.engine) as session:
            stmt = (
                select(AuditEventDB)
                .where(
                    AuditEventDB.tenant_id == tenant_id,
                    AuditEventDB.action.in_(auth_actions),
                    AuditEventDB.timestamp >= threshold,
                )
                .order_by(AuditEventDB.timestamp.desc())
                .limit(20)
            )
            result = await session.execute(stmt)
            for row in result.scalars().all():
                events.append({
                    "event_id": row.event_id,
                    "event_type": "auth_anomaly",
                    "severity": "high",
                    "message": f"Auth anomaly: {row.action}",
                    "occurred_at": row.timestamp,
                    "artifact_id": row.customer_id,
                    "link": f"/audit?event_id={row.event_id}",
                })

        for job in failed_jobs:
            error = (job.last_error or "").lower()
            if any(k in error for k in ("api", "http", "timeout", "connection")):
                events.append({
                    "event_id": f"api-failure-{job.job_id}",
                    "event_type": "api_failure",
                    "severity": "high",
                    "message": f"API failure in {job.job_type} job",
                    "occurred_at": job.updated_at,
                    "artifact_id": job.job_id,
                    "link": f"/settings/system?job={job.job_id}",
                })
            if any(k in error for k in ("model", "llm", "template")):
                events.append({
                    "event_id": f"model-failure-{job.job_id}",
                    "event_type": "model_failure",
                    "severity": "high",
                    "message": f"Model failure in {job.job_type} job",
                    "occurred_at": job.updated_at,
                    "artifact_id": job.job_id,
                    "link": f"/settings/system?job={job.job_id}",
                })

        events.sort(key=lambda e: e["occurred_at"], reverse=True)
        return events[:50]
