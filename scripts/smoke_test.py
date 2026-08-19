"""Smoke test against a running Thebe Core API."""

from __future__ import annotations

import sys

import httpx


def main() -> int:
    base = "http://localhost:8000"
    with httpx.Client(base_url=base, timeout=30.0) as client:
        print("GET /health")
        health = client.get("/health")
        print(health.status_code, health.json())

        print("\nGET /verticals")
        verticals = client.get("/verticals")
        print(verticals.status_code, verticals.text)

        print("\nGET /audit")
        audit = client.get("/audit")
        print(audit.status_code, f"events={len(audit.json()) if audit.status_code == 200 else audit.text}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
