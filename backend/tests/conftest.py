"""
Shared fixtures for all tests.

API_KEY must exist before any app.* import, so we set it here at module level.
The .env file in backend/ is loaded by config.py, but this ensures tests work
even without a real key (all external API calls are mocked).
"""
import os
import pytest

# Must be set before any app.* import (config.py does os.environ["API_KEY"])
os.environ.setdefault("API_KEY", "test-api-key-placeholder")

from fastapi.testclient import TestClient
from app.main import app
from app.services import workflow_store, job_store


# ---------------------------------------------------------------------------
# Store isolation — wipe in-memory state before every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_stores():
    workflow_store._workflows.clear()
    job_store._jobs.clear()
    yield
    workflow_store._workflows.clear()
    job_store._jobs.clear()


# ---------------------------------------------------------------------------
# HTTP client (session-scoped to avoid repeated lifespan calls)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Reusable payloads
# ---------------------------------------------------------------------------

READ_CSV_BLOCK = {"type": "read_csv", "params": {"path": "data.csv"}}
FILTER_BLOCK = {"type": "filter", "params": {"column": "age", "operator": "gt", "value": "30"}}
SAVE_CSV_BLOCK = {"type": "save_csv", "params": {"path": "output.csv"}}
ENRICH_LEAD_BLOCK = {"type": "enrich_lead", "params": {"struct": {"company": "company name"}}}
FIND_EMAIL_BLOCK = {"type": "find_email", "params": {"mode": "PROFESSIONAL"}}


@pytest.fixture
def simple_workflow_payload():
    return {"name": "Test Workflow", "blocks": [READ_CSV_BLOCK]}


@pytest.fixture
def full_workflow_payload():
    return {
        "name": "Full Workflow",
        "blocks": [READ_CSV_BLOCK, FILTER_BLOCK, SAVE_CSV_BLOCK],
    }


@pytest.fixture
def created_workflow(client, simple_workflow_payload):
    r = client.post("/workflows", json=simple_workflow_payload)
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def created_job(client, created_workflow):
    r = client.post("/jobs", json={"workflow_id": created_workflow["id"]})
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def pending_job_id(created_workflow):
    """
    Creates a job directly in the store — no HTTP call, so no BackgroundTask
    is triggered. Use this in cancel tests that need the job to remain PENDING.
    """
    job = job_store.create_job(workflow_id=created_workflow["id"])
    return job.id
