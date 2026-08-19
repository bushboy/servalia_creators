from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(tmp_path / 'api.db').as_posix()}"
    os.environ["SEED_TEST_TENANT"] = "1"
    os.environ.setdefault(
        "PII_ENCRYPTION_KEY",
        "WJUOLW0cIk_DxCa7xGy6Gw63wOVU4qZhG9vIzLJNxiQ=",
    )
    from thebe_core.api import app

    with TestClient(app) as test_client:
        test_client.headers["Authorization"] = "ApiKey test-api-key:test-secret"
        yield test_client


def test_customer_lifecycle(client):
    create_response = client.post(
        "/customers",
        json={"vertical": "test", "name": "Ada Lovelace"},
    )
    assert create_response.status_code == 201
    customer = create_response.json()
    assert customer["name"] == "Ada Lovelace"
    assert customer["status"] == "draft"
    customer_id = customer["customer_id"]

    list_response = client.get("/customers")
    assert list_response.status_code == 200
    assert any(c["customer_id"] == customer_id for c in list_response.json())

    patch_response = client.patch(
        f"/customers/{customer_id}",
        json={"status": "active"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "active"

    get_response = client.get(f"/customers/{customer_id}")
    assert get_response.status_code == 200
    assert get_response.json()["customer_id"] == customer_id


def test_patch_context(client):
    created = client.post(
        "/customers",
        json={"vertical": "test", "name": "Context Author"},
    )
    customer_id = created.json()["customer_id"]
    response = client.patch(
        f"/customers/{customer_id}/context",
        json={"context": {"voice": "practical", "genres": ["technology"]}},
    )
    assert response.status_code == 200
    assert response.json()["context"]["voice"] == "practical"

    timeline = client.get(f"/customers/{customer_id}/timeline")
    assert timeline.status_code == 200
    assert isinstance(timeline.json(), list)


def test_audit_query(client):
    created = client.post(
        "/customers",
        json={"vertical": "test", "name": "Audit Author"},
    )
    customer_id = created.json()["customer_id"]
    client.patch(
        f"/customers/{customer_id}/context",
        json={"context": {"display_name": "Audit Author"}},
    )
    response = client.get("/audit", params={"customer_id": customer_id})
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    assert all(e["customer_id"] == customer_id for e in events)


def test_unauthenticated(client):
    response = client.get("/verticals", headers={"Authorization": ""})
    assert response.status_code == 401


def test_invalid_api_key(client):
    response = client.get(
        "/verticals", headers={"Authorization": "ApiKey unknown:secret"}
    )
    assert response.status_code == 401


def test_wrong_api_key_secret(client):
    response = client.get(
        "/verticals",
        headers={"Authorization": "ApiKey test-api-key:wrong-secret"},
    )
    assert response.status_code == 401


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "thebe_http_requests_total" in response.text


def test_finops_routes_are_gone(client):
    assert client.post("/onboard", json={"vertical": "test"}).status_code == 404
    assert client.post("/evaluate", json={"customer_id": "x"}).status_code == 404
    assert client.get("/findings").status_code == 404
    assert client.get("/tasks").status_code == 404
    assert client.get("/documents").status_code == 404


def test_tenant_isolation(client):
    auth = client.app.state.auth_service
    import asyncio

    asyncio.run(auth.create_tenant("other-tenant", "Other Tenant", "other-tenant"))
    asyncio.run(
        auth.create_api_key("other-tenant", "other-key", "other-secret", ["admin"])
    )

    created = client.post(
        "/customers",
        json={"vertical": "test", "name": "Isolation Author"},
    )
    customer_id = created.json()["customer_id"]
    client.patch(
        f"/customers/{customer_id}/context",
        json={"context": {"display_name": "Isolation Author"}},
    )

    own = client.get("/audit")
    assert own.status_code == 200
    assert any(e["customer_id"] == customer_id for e in own.json())

    other = client.get(
        "/audit", headers={"Authorization": "ApiKey other-key:other-secret"}
    )
    assert other.status_code == 200
    assert not any(e["customer_id"] == customer_id for e in other.json())
