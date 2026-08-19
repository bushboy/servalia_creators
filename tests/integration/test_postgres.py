from __future__ import annotations

import asyncio
import os

os.environ.setdefault(
    "PII_ENCRYPTION_KEY",
    "WJUOLW0cIk_DxCa7xGy6Gw63wOVU4qZhG9vIzLJNxiQ=",
)

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from thebe_core.audit.service import AuditService
from thebe_core.auth.service import AuthService
from thebe_core.models import AuditEvent

DEFAULT_DATABASE_URL = (
    os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://thebe:thebe@localhost:5432/thebe",
    )
    .replace("postgresql://", "postgresql+asyncpg://")
    .replace("postgres://", "postgresql+asyncpg://")
)


def _ping_postgres(url: str) -> bool:
    async def _ping() -> bool:
        engine = create_async_engine(url)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            await engine.dispose()

    return asyncio.run(_ping())


@pytest.fixture
def postgres_url():
    if not _ping_postgres(DEFAULT_DATABASE_URL):
        pytest.skip("PostgreSQL is not available for integration tests")
    return DEFAULT_DATABASE_URL


async def test_audit_service_on_postgres(postgres_url):
    audit = AuditService(postgres_url)
    await audit.create_tables()

    event = AuditEvent(
        vertical="test",
        customer_id="pg-cust-001",
        agent_id="onboarding-agent",
        action="onboard",
        input_snapshot={"company": "PG Acme"},
        output_snapshot={"status": "ok"},
    )
    await audit.log_event(event)

    results = await audit.query_events({"customer_id": "pg-cust-001"})
    assert len(results) == 1
    assert results[0].input_snapshot == {"company": "PG Acme"}
    assert results[0].output_snapshot == {"status": "ok"}


async def test_auth_service_on_postgres(postgres_url):
    audit = AuditService(postgres_url)
    await audit.create_tables()
    auth = AuthService(audit.engine)

    await auth.create_tenant("pg-tenant", "PG Tenant", "pg-tenant")
    await auth.create_api_key(
        "pg-tenant", "pg-key", "pg-secret", ["admin"]
    )

    context = await auth.get_tenant_context("apikey", "pg-key:pg-secret")
    assert context.tenant_id == "pg-tenant"
    assert context.has_role("admin")
