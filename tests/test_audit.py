from __future__ import annotations

import os
from datetime import datetime, timezone

os.environ.setdefault(
    "PII_ENCRYPTION_KEY",
    "WJUOLW0cIk_DxCa7xGy6Gw63wOVU4qZhG9vIzLJNxiQ=",
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from thebe_core.audit.service import AuditService
from thebe_core.audit.store import AuditEventDB, CustomerDB
from thebe_core.models import AuditEvent


async def _make_service(db_path):
    service = AuditService(f"sqlite+aiosqlite:///{db_path.as_posix()}")
    await service.create_tables()
    return service


async def test_log_and_query_audit_event(tmp_path):
    db_path = tmp_path / "audit.db"
    service = await _make_service(db_path)

    event = AuditEvent(
        vertical="test",
        customer_id="cust-001",
        action="onboard",
        input_snapshot={"company": "Acme"},
        output_snapshot={"status": "ok"},
        metadata={"source": "test"},
    )
    event_id = await service.log_event(event)

    results = await service.query_events({"customer_id": "cust-001"})
    assert len(results) == 1
    assert results[0].event_id == event_id
    assert results[0].metadata == {"source": "test"}


async def test_query_filters_by_vertical_and_action(tmp_path):
    db_path = tmp_path / "audit.db"
    service = await _make_service(db_path)

    await service.log_event(
        AuditEvent(
            vertical="test",
            customer_id="c1",
            action="evaluate",
            input_snapshot={},
            output_snapshot={},
        )
    )
    await service.log_event(
        AuditEvent(
            vertical="creator_rights",
            customer_id="c2",
            action="evaluate",
            input_snapshot={},
            output_snapshot={},
        )
    )

    assert len(await service.query_events({"vertical": "test"})) == 1
    assert len(await service.query_events({"action": "evaluate"})) == 2
    assert len(await service.query_events({"vertical": "creator_rights"})) == 1
    assert await service.query_events({"customer_id": "unknown"}) == []


async def test_time_range_filter(tmp_path):
    db_path = tmp_path / "audit.db"
    service = await _make_service(db_path)

    now = datetime.now(timezone.utc)
    event = AuditEvent(
        vertical="test",
        customer_id="c4",
        action="onboard",
        input_snapshot={},
        output_snapshot={},
        timestamp=now,
    )
    await service.log_event(event)

    results = await service.query_events({
        "from": now.replace(hour=0, minute=0, second=0, microsecond=0),
        "to": now,
    })
    assert len(results) == 1

    results = await service.query_events({
        "from": datetime(2000, 1, 1, tzinfo=timezone.utc),
        "to": datetime(2000, 12, 31, tzinfo=timezone.utc),
    })
    assert results == []


async def test_pii_encrypted_at_rest(tmp_path):
    db_path = tmp_path / "audit.db"
    service = await _make_service(db_path)

    event = AuditEvent(
        vertical="test",
        customer_id="cust-001",
        action="onboard",
        input_snapshot={"company": "Acme"},
        output_snapshot={"status": "ok"},
    )
    await service.log_event(event)

    async with AsyncSession(service.engine) as session:
        result = await session.execute(select(AuditEventDB))
        row = result.scalars().first()
        assert "__encrypted__" in row.input_snapshot
        assert "__encrypted__" in row.output_snapshot

    fetched = await service.query_events({"customer_id": "cust-001"})
    assert fetched is not None
    assert len(fetched) == 1
    assert fetched[0].input_snapshot == event.input_snapshot
    assert fetched[0].output_snapshot == event.output_snapshot


async def test_customer_context_encrypted_at_rest(tmp_path):
    db_path = tmp_path / "audit.db"
    service = await _make_service(db_path)

    await service.create_customer(
        customer_id="cust-001",
        tenant_id="tenant-001",
        vertical="test",
        name="Acme",
        context={"company_name": "Acme", "registration": "12345"},
    )

    async with AsyncSession(service.engine) as session:
        result = await session.execute(select(CustomerDB))
        row = result.scalars().first()
        assert "__encrypted__" in row.context

    customer = await service.get_customer("cust-001", "tenant-001")
    assert customer is not None
    assert customer.context["company_name"] == "Acme"
    assert customer.context["registration"] == "12345"
