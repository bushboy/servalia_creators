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


def test_me_requires_auth(client):
    response = client.get("/me", headers={"Authorization": ""})
    assert response.status_code == 401


def test_me_returns_context(client):
    response = client.get("/me")
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "test-tenant"
    assert data["auth_method"] == "api_key"
    assert "admin" in data["roles"]


def test_list_customers(client):
    created = client.post(
        "/customers",
        json={"vertical": "test", "name": "AdminCo"},
    )
    assert created.status_code == 201
    customer_id = created.json()["customer_id"]
    response = client.get("/customers")
    assert response.status_code == 200
    data = response.json()
    assert any(c["customer_id"] == customer_id for c in data)


def test_get_customer(client):
    created = client.post(
        "/customers",
        json={"vertical": "test", "name": "GetCo"},
    )
    customer_id = created.json()["customer_id"]
    response = client.get(f"/customers/{customer_id}")
    assert response.status_code == 200
    assert response.json()["customer_id"] == customer_id


def test_get_customer_not_found(client):
    response = client.get("/customers/missing")
    assert response.status_code == 404


def test_api_key_lifecycle(client):
    response = client.post(
        "/admin/api-keys",
        json={"api_key_id": "new-key", "roles": ["operator"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["api_key_id"] == "new-key"
    assert "secret" in data

    response = client.get("/admin/api-keys")
    assert response.status_code == 200
    assert any(k["api_key_id"] == "new-key" for k in response.json())

    response = client.delete("/admin/api-keys/new-key")
    assert response.status_code == 200
    assert response.json()["revoked"] is True


def test_membership_lifecycle(client):
    response = client.post(
        "/admin/members",
        json={"subject": "user-123", "role": "viewer"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["subject"] == "user-123"
    membership_id = data["membership_id"]

    response = client.get("/admin/members")
    assert response.status_code == 200
    assert any(m["membership_id"] == membership_id for m in response.json())

    response = client.delete(f"/admin/members/{membership_id}")
    assert response.status_code == 200
    assert response.json()["revoked"] is True


def test_tenant_details(client):
    response = client.get("/admin/tenant")
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "test-tenant"

    response = client.patch(
        "/admin/tenant",
        json={"name": "Updated Tenant"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Tenant"


def test_tenant_update_validates_slug(client):
    response = client.patch(
        "/admin/tenant",
        json={"slug": "INVALID SLUG"},
    )
    assert response.status_code == 400
    assert "slug" in response.json()["error"]["message"].lower()


def test_tenant_status_state_machine(client):
    response = client.patch(
        "/admin/tenant",
        json={"status": "suspended"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "suspended"

    response = client.patch(
        "/admin/tenant",
        json={"status": "invalid"},
    )
    assert response.status_code == 400


def test_tenant_creation_requires_bearer_token(client):
    response = client.post("/tenants", json={"name": "New Tenant", "slug": "new-tenant"})
    assert response.status_code == 401


def test_list_my_tenants_requires_bearer_token(client):
    response = client.get("/me/tenants")
    assert response.status_code == 401


def test_admin_routes_require_admin_role(client):
    # Create an operator-scoped API key using the admin client.
    response = client.post(
        "/admin/api-keys",
        json={"api_key_id": "operator-key", "roles": ["operator"]},
    )
    assert response.status_code == 200
    secret = response.json()["secret"]

    # The same client authenticated with the operator key must be rejected.
    original_auth = client.headers["Authorization"]
    client.headers["Authorization"] = f"ApiKey operator-key:{secret}"
    try:
        assert client.get("/admin/api-keys").status_code == 403
        assert client.get("/admin/members").status_code == 403
        assert client.get("/admin/tenant").status_code == 403
    finally:
        client.headers["Authorization"] = original_auth


def test_cors_preflight(client):
    response = client.options(
        "/verticals",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
