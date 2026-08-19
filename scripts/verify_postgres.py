"""Verify end-to-end PostgreSQL audit logging."""

from __future__ import annotations

import os

from thebe_core.audit.service import AuditService
from thebe_core.models import AuditEvent


def main() -> None:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://thebe:thebe@localhost:5432/thebe",
    )
    audit = AuditService(database_url)

    event = AuditEvent(
        vertical="test",
        customer_id="pg-verify",
        agent_id="verify",
        action="test",
        input_snapshot={"message": "ping"},
        output_snapshot={"message": "pong"},
    )
    event_id = audit.log_event(event)

    events = audit.query_events({"customer_id": "pg-verify"})
    assert len(events) == 1
    assert events[0].event_id == event_id

    print("PostgreSQL audit logging verified successfully.")


if __name__ == "__main__":
    main()
