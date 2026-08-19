"""End-to-end smoke test for the CreatorTrust API.

This script exercises the remaining core flows against a running API.

Environment variables:
    API_BASE_URL    base URL of the API (default: http://localhost:8000)
    API_KEY         API key in the form "id:secret" (default: test-api-key:test-secret)
    OIDC_TOKEN      If set, uses Bearer token auth instead of API key
    X_TENANT_ID     Optional tenant hint for OIDC users with multiple tenants

Usage:
    python scripts/e2e_test.py
"""

from __future__ import annotations

import os
import sys
import uuid
from typing import Any

import httpx


class E2ETester:
    def __init__(self) -> None:
        self.base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        self.api_key = os.environ.get("API_KEY", "test-api-key:test-secret")
        self.token = os.environ.get("OIDC_TOKEN", "")
        self.tenant_hint = os.environ.get("X_TENANT_ID", "")
        self.passed: list[str] = []
        self.failed: list[str] = []
        self._customer_id = f"e2e-cust-{uuid.uuid4().hex[:8]}"

    def _client(self) -> httpx.Client:
        headers: dict[str, str] = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        else:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        if self.tenant_hint:
            headers["X-Tenant-Id"] = self.tenant_hint
        return httpx.Client(base_url=self.base_url, headers=headers, timeout=30.0)

    def _check(self, name: str, condition: bool, details: Any = None) -> None:
        if condition:
            self.passed.append(name)
            print(f"  PASS: {name}")
        else:
            self.failed.append(name)
            print(f"  FAIL: {name} {details if details is not None else ''}")

    def run(self) -> int:
        with self._client() as client:
            print("--- Health ---")
            try:
                r = client.get("/health")
                self._check("GET /health 200", r.status_code == 200)
            except Exception as exc:
                self._check("GET /health 200", False, exc)
                print("\nAPI is not reachable. Start the server first:")
                print("  uvicorn thebe_core.api:app --host 0.0.0.0 --port 8000")
                return 1

            print("\n--- Auth context ---")
            r = client.get("/me")
            self._check("GET /me 200", r.status_code == 200, r.text)
            if r.status_code == 200:
                me = r.json()
                self._check("tenant_id present", bool(me.get("tenant_id")))
                print(f"  tenant: {me.get('tenant_id')} roles: {me.get('roles')}")

            print("\n--- Verticals ---")
            r = client.get("/verticals")
            self._check("GET /verticals 200", r.status_code == 200, r.text)

            print("\n--- Authors (customers) ---")
            customer_payload = {
                "vertical": "test",
                "name": f"E2E Author {uuid.uuid4().hex[:8]}",
                "context": {"display_name": "E2E Author"},
            }
            r = client.post("/customers", json=customer_payload)
            self._check("POST /customers 201", r.status_code == 201, r.text)
            customer = r.json()
            self._customer_id = customer.get("customer_id", self._customer_id)

            r = client.get(f"/customers/{self._customer_id}")
            self._check("GET /customers/:id 200", r.status_code == 200, r.text)

            r = client.patch(
                f"/customers/{self._customer_id}",
                json={"status": "active"},
            )
            self._check(
                "PATCH /customers/:id 200",
                r.status_code == 200 and r.json().get("status") == "active",
            )

            r = client.patch(
                f"/customers/{self._customer_id}/context",
                json={"context": {"display_name": "E2E Author", "voice": "practical"}},
            )
            self._check("PATCH /customers/:id/context 200", r.status_code == 200, r.text)

            r = client.get(
                f"/customers/{self._customer_id}/timeline",
                params={"limit": "10"},
            )
            self._check("GET /customers/:id/timeline 200", r.status_code == 200)

            print("\n--- Audit ---")
            r = client.get(
                "/audit", params={"customer_id": self._customer_id, "limit": "20"}
            )
            self._check("GET /audit 200", r.status_code == 200)

        print("\n--- Summary ---")
        print(f"Passed: {len(self.passed)}")
        print(f"Failed: {len(self.failed)}")
        if self.failed:
            print("Failing checks:")
            for name in self.failed:
                print(f"  - {name}")
            return 1
        return 0


def main() -> int:
    print("CreatorTrust E2E Smoke Test")
    print(f"API: {os.environ.get('API_BASE_URL', 'http://localhost:8000')}")
    if os.environ.get("OIDC_TOKEN"):
        print("Auth: Bearer token")
    else:
        print(f"Auth: ApiKey {os.environ.get('API_KEY', 'test-api-key:test-secret')}")
    print()
    return E2ETester().run()


if __name__ == "__main__":
    sys.exit(main())
