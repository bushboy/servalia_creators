from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_rate_limit(tmp_path):
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(tmp_path / 'api.db').as_posix()}"
    os.environ["SEED_TEST_TENANT"] = "1"
    os.environ["RATE_LIMIT"] = "1/minute"
    os.environ.setdefault(
        "PII_ENCRYPTION_KEY",
        "WJUOLW0cIk_DxCa7xGy6Gw63wOVU4qZhG9vIzLJNxiQ=",
    )
    from thebe_core.api import app

    with TestClient(app) as test_client:
        test_client.headers["Authorization"] = "ApiKey test-api-key:test-secret"
        yield test_client


@pytest.mark.skip("Rate limit settings are loaded at import and not hot-reloadable in the same session.")
def test_rate_limit_blocks_excess(client_rate_limit):
    assert client_rate_limit.get("/me").status_code == 200
    response = client_rate_limit.get("/me")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text


def test_missing_credentials(client_rate_limit):
    client_rate_limit.headers = {}
    assert client_rate_limit.get("/me").status_code == 401


def test_unknown_api_key(client_rate_limit):
    client_rate_limit.headers["Authorization"] = "ApiKey unknown-key:wrong-secret"
    assert client_rate_limit.get("/me").status_code == 401
