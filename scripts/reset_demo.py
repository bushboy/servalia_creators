"""Restore the demo to the seeded starting point without dropping tenants or Keycloak.

Removes generated books, assets, campaigns, and packages for the current tenant,
then recreates Mara Ellison, *Manuscript to Launch*, editions, and the excerpt.
The author profile is kept and refreshed if it already exists.

Environment:
    API_BASE_URL    default http://localhost:8100 (Docker Compose API)
    API_KEY         default test-api-key:test-secret

Usage:
    python scripts/reset_demo.py
    python scripts/reset_demo.py --base-url http://localhost:8000
    python scripts/reset_demo.py --base-url http://localhost:8200
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

DEFAULT_BASE = os.environ.get("API_BASE_URL", "http://localhost:8100")
DEFAULT_KEY = os.environ.get("API_KEY", "test-api-key:test-secret")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reset CreatorTrust demo data to the original seed."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE,
        help="API origin (no /api suffix). Default: %(default)s",
    )
    parser.add_argument(
        "--api-key",
        default=DEFAULT_KEY,
        help="API key id:secret (admin). Default: seeded test key.",
    )
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    headers = {"Authorization": f"ApiKey {args.api_key}"}

    with httpx.Client(base_url=base, headers=headers, timeout=60.0) as client:
        health = client.get("/health")
        if health.status_code != 200:
            print(
                f"API not healthy at {base}/health ({health.status_code}). "
                "Is Compose up? Try --base-url http://localhost:8000 or :8200.",
                file=sys.stderr,
            )
            return 1

        reset = client.post("/admin/demo-reset")
        if reset.status_code != 200:
            print(
                f"Reset failed: {reset.status_code} {reset.text}",
                file=sys.stderr,
            )
            return 1
        payload = reset.json()
        tenant_id = payload.get("tenant_id", "")

        authors = client.get("/authors")
        authors.raise_for_status()
        mara = next(
            (row for row in authors.json() if row.get("name") == "Mara Ellison"),
            None,
        )
        if mara is None:
            print("Reset returned ok but Mara Ellison is missing.", file=sys.stderr)
            return 1

        books = client.get("/books", params={"author_id": mara["author_id"]})
        books.raise_for_status()
        titles = [row.get("working_title") or row.get("final_title") for row in books.json()]

    print(f"Demo seed restored for tenant {tenant_id}.")
    print("Kept: tenant, API keys, Keycloak users, Mara Ellison profile.")
    print(f"Author: Mara Ellison ({mara['author_id']})")
    print(f"Books: {', '.join(str(t) for t in titles) or '(none)'}")
    print("Generated assets, campaigns, and extra manuscripts were removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
