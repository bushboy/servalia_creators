from __future__ import annotations

import io
import os
import time
import zipfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(tmp_path / 'api.db').as_posix()}"
    os.environ["SEED_TEST_TENANT"] = "1"
    os.environ["UPLOAD_DIR"] = str(tmp_path / "uploads")
    os.environ["PACKAGE_DIR"] = str(tmp_path / "packages")
    os.environ.pop("MINDS_API_KEY", None)
    os.environ.setdefault(
        "PII_ENCRYPTION_KEY",
        "WJUOLW0cIk_DxCa7xGy6Gw63wOVU4qZhG9vIzLJNxiQ=",
    )
    from thebe_core import config as config_mod

    config_mod.settings.UPLOAD_DIR = os.environ["UPLOAD_DIR"]
    config_mod.settings.PACKAGE_DIR = os.environ["PACKAGE_DIR"]
    config_mod.settings.MINDS_API_KEY = None
    from thebe_core.api import app

    with TestClient(app) as test_client:
        test_client.headers["Authorization"] = "ApiKey test-api-key:test-secret"
        yield test_client


def _wait_job(client: TestClient, job_id: str, timeout: float = 15.0) -> dict:
    return _wait_job_until(client, job_id, {"completed"}, timeout=timeout)


def _wait_job_until(
    client: TestClient,
    job_id: str,
    statuses: set[str],
    timeout: float = 15.0,
) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/jobs/{job_id}")
        assert response.status_code == 200
        job = response.json()
        if job["status"] in statuses:
            return job
        if job["status"] == "failed" and "failed" not in statuses:
            raise AssertionError(job.get("last_error") or job)
        time.sleep(0.1)
    raise TimeoutError(f"job {job_id} did not reach {statuses}")


def test_seeded_author_and_editions(client):
    authors = client.get("/authors")
    assert authors.status_code == 200
    assert any(a["name"] == "Mara Ellison" for a in authors.json())
    author_id = next(a["author_id"] for a in authors.json() if a["name"] == "Mara Ellison")
    author = next(a for a in authors.json() if a["author_id"] == author_id)
    assert "careful with claims" in author["context"]["voice"]
    assert "First-time authors" in author["context"]["audience"]
    assert author["context"]["rights"] == "all_rights_owned"

    books = client.get("/books", params={"author_id": author_id})
    assert books.status_code == 200
    assert len(books.json()) == 1
    book_id = books.json()[0]["id"]
    assert "isbn" not in books.json()[0]

    editions = client.get(f"/books/{book_id}/editions")
    formats = {row["format"] for row in editions.json()}
    assert formats == {"paperback", "ebook"}
    paperback = next(row for row in editions.json() if row["format"] == "paperback")
    assert paperback["isbn"]
    assert paperback["list_price"] == 18.99


def test_mind_message_requires_credentials(client):
    authors = client.get("/authors").json()
    author_id = authors[0]["author_id"]
    response = client.post(
        f"/authors/{author_id}/mind/message",
        json={"message": "What is my voice?"},
    )
    assert response.status_code == 503


def test_unknown_job_does_not_stall_asset_generation(client):
    bad = client.post(
        "/jobs",
        json={"job_type": "not_a_real_type", "payload": {}, "max_retries": 0},
    )
    assert bad.status_code == 201
    failed = _wait_job_until(client, bad.json()["job_id"], {"failed"})
    assert failed["status"] == "failed"

    book_id = client.get("/books").json()[0]["id"]
    generated = client.post(f"/books/{book_id}/generate-assets", json={})
    assert generated.status_code == 200
    _wait_job(client, generated.json()["job_id"])
    assets = client.get(f"/books/{book_id}/assets")
    assert assets.status_code == 200
    assert len(assets.json()) == 5


def test_excerpt_to_packages_and_revise(client):
    book_id = client.get("/books").json()[0]["id"]
    documents = client.get(f"/books/{book_id}/documents")
    assert documents.status_code == 200
    assert documents.json()[0]["extracted_text"].find("guarantees") != -1

    generated = client.post(f"/books/{book_id}/generate-assets", json={})
    assert generated.status_code == 200
    _wait_job(client, generated.json()["job_id"])

    assets = client.get(f"/books/{book_id}/assets").json()
    types = {row["type"] for row in assets}
    assert types == {
        "description",
        "newsletter",
        "social_post",
        "podcast_pitch",
        "video_script",
    }
    assert all(row["source_document_id"] for row in assets)

    description = next(row for row in assets if row["type"] == "description")
    assert (
        "This method guarantees that every new author will double their book sales."
        in description["content"]
    )
    evaluated = client.post(f"/assets/{description['id']}/evaluate")
    assert evaluated.status_code == 200
    body = evaluated.json()
    assert body["governance_status"] in {"review", "block"}
    rule_ids = [r["rule_id"] for r in (body["evaluation"] or {}).get("rule_results") or []]
    assert "CREATOR-CLAIM-001" in rule_ids
    claim = next(
        r
        for r in body["evaluation"]["rule_results"]
        if r["rule_id"] == "CREATOR-CLAIM-001"
    )
    assert claim["status"] in {"PARTIAL", "FAIL"}

    rejected = client.post(
        f"/assets/{description['id']}/reject",
        json={"note": "Do not use guaranteed results or aggressive sales language."},
    )
    assert rejected.status_code == 200
    revised = client.post(
        f"/assets/{description['id']}/revise",
        json={"correction": "Do not use guaranteed results or aggressive sales language."},
    )
    assert revised.status_code == 200
    revised_body = revised.json()
    assert revised_body["applied_preference"] is True
    assert revised_body["parent_asset_id"] == description["id"]
    assert revised_body["version"] == 2
    assert "Applied author preference" in revised_body["content"]
    assert "guarantees that every new author will double" not in revised_body["content"]
    assert (
        "This method gives first-time authors a practical workflow for preparing a coordinated launch."
        in revised_body["content"]
    )

    approved = client.post(f"/assets/{revised_body['id']}/approve")
    assert approved.status_code == 200

    editions = client.get(f"/books/{book_id}/editions").json()
    paperback_id = next(row["id"] for row in editions if row["format"] == "paperback")

    kdp = client.post(f"/editions/{paperback_id}/packages/kdp")
    assert kdp.status_code == 200
    assert kdp.headers["content-type"].startswith("application/zip")
    kdp_zip = zipfile.ZipFile(io.BytesIO(kdp.content))
    assert set(kdp_zip.namelist()) >= {
        "metadata.json",
        "checklist.md",
        "validation-report.json",
        "SUBMIT.md",
        "excerpt.txt",
    }

    ingram = client.post(f"/editions/{paperback_id}/packages/ingramspark")
    assert ingram.status_code == 200
    ingram_zip = zipfile.ZipFile(io.BytesIO(ingram.content))
    assert "validation-report.json" in ingram_zip.namelist()

    campaign = client.post(
        f"/books/{book_id}/campaigns",
        json={"campaign_type": "launch", "launch_date": "2026-09-01"},
    )
    assert campaign.status_code == 201
    phases = {task["phase"] for task in campaign.json()["tasks"]}
    assert phases == {"pre-launch", "launch_week", "post-launch"}

    audit = client.get(f"/books/{book_id}/audit")
    assert audit.status_code == 200
    actions = {event["action"] for event in audit.json()}
    assert "assets_generated" in actions
    assert "asset_evaluated" in actions
    assert "asset_rejected" in actions
    assert "asset_revised" in actions
    assert "package_built" in actions

    reset = client.post("/admin/demo-reset")
    assert reset.status_code == 200
    books_after = client.get("/books")
    assert books_after.status_code == 200
    assert len(books_after.json()) == 1


def test_upload_rejects_pdf(client):
    book_id = client.get("/books").json()[0]["id"]
    response = client.post(
        f"/books/{book_id}/documents",
        files={"file": ("notes.pdf", b"%PDF-fake", "application/pdf")},
        data={"rights_declaration": "all_rights_owned"},
    )
    assert response.status_code == 400
