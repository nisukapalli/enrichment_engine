"""
Comprehensive tests for /jobs endpoints.

Covers:
  - GET  /jobs
  - POST /jobs
  - GET  /jobs/{id}
  - POST /jobs/{id}/cancel

Note on background execution:
  BackgroundTasks runs synchronously inside TestClient before client.post()
  returns. The CREATE response still reflects the initial PENDING state, but
  a subsequent GET will show the final state (FAILED if no CSV exists, etc.).

  Cancel tests that need a job in PENDING state use the `pending_job_id`
  fixture, which creates the job directly in the store with no background task.
"""
import pytest
from datetime import datetime, timezone
from app.services import job_store
from app.models.job import JobStatus
from tests.conftest import READ_CSV_BLOCK, FILTER_BLOCK, SAVE_CSV_BLOCK


# ===========================================================================
# GET /jobs
# ===========================================================================

class TestListJobs:
    def test_empty_list_on_startup(self, client):
        r = client.get("/jobs")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_all_created_jobs(self, client, created_workflow):
        wf_id = created_workflow["id"]
        client.post("/jobs", json={"workflow_id": wf_id})
        client.post("/jobs", json={"workflow_id": wf_id})
        r = client.get("/jobs")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_response_is_list(self, client):
        r = client.get("/jobs")
        assert isinstance(r.json(), list)


# ===========================================================================
# POST /jobs  (response reflects initial state before background execution)
# ===========================================================================

class TestCreateJob:

    def test_create_job_returns_201(self, client, created_workflow):
        r = client.post("/jobs", json={"workflow_id": created_workflow["id"]})
        assert r.status_code == 201

    def test_create_job_response_status_is_pending(self, client, created_workflow):
        """The CREATE response is the snapshot at creation time — always PENDING."""
        r = client.post("/jobs", json={"workflow_id": created_workflow["id"]})
        assert r.json()["status"] == "pending"

    def test_create_job_transitions_out_of_pending(self, client, created_workflow):
        """After background execution, a subsequent GET shows the terminal state."""
        r = client.post("/jobs", json={"workflow_id": created_workflow["id"]})
        job_id = r.json()["id"]
        live = client.get(f"/jobs/{job_id}").json()
        assert live["status"] != "pending"

    def test_create_job_empty_workflow_completes_immediately(self, client):
        """An empty workflow (no blocks) completes with no errors."""
        r_wf = client.post("/workflows", json={"name": "Empty"})
        r_job = client.post("/jobs", json={"workflow_id": r_wf.json()["id"]})
        job_id = r_job.json()["id"]
        live = client.get(f"/jobs/{job_id}").json()
        assert live["status"] == "completed"
        assert live["finished_at"] is not None

    def test_create_job_fails_when_csv_missing(self, client, created_workflow):
        """A workflow with read_csv fails because the file doesn't exist in uploads/."""
        r = client.post("/jobs", json={"workflow_id": created_workflow["id"]})
        job_id = r.json()["id"]
        live = client.get(f"/jobs/{job_id}").json()
        assert live["status"] == "failed"
        assert live["error_message"] is not None

    def test_create_job_has_correct_workflow_id(self, client, created_workflow):
        wf_id = created_workflow["id"]
        r = client.post("/jobs", json={"workflow_id": wf_id})
        assert r.json()["workflow_id"] == wf_id

    def test_create_job_assigns_unique_id(self, client, created_workflow):
        wf_id = created_workflow["id"]
        r1 = client.post("/jobs", json={"workflow_id": wf_id})
        r2 = client.post("/jobs", json={"workflow_id": wf_id})
        assert r1.json()["id"] != r2.json()["id"]

    def test_create_job_total_blocks_matches_workflow(self, client):
        r_wf = client.post("/workflows", json={
            "blocks": [READ_CSV_BLOCK, FILTER_BLOCK, SAVE_CSV_BLOCK]
        })
        wf_id = r_wf.json()["id"]
        r_job = client.post("/jobs", json={"workflow_id": wf_id})
        assert r_job.json()["total_blocks"] == 3

    def test_create_job_total_blocks_zero_for_empty_workflow(self, client):
        r_wf = client.post("/workflows", json={"name": "Empty"})
        r_job = client.post("/jobs", json={"workflow_id": r_wf.json()["id"]})
        assert r_job.json()["total_blocks"] == 0

    def test_create_job_response_completed_blocks_is_zero(self, client, created_workflow):
        """Response snapshot; actual completed_blocks may differ after bg execution."""
        r = client.post("/jobs", json={"workflow_id": created_workflow["id"]})
        assert r.json()["completed_blocks"] == 0

    def test_create_job_response_block_states_all_pending(self, client):
        r_wf = client.post("/workflows", json={"blocks": [READ_CSV_BLOCK, FILTER_BLOCK]})
        r_job = client.post("/jobs", json={"workflow_id": r_wf.json()["id"]})
        assert all(v == "pending" for v in r_job.json()["block_states"].values())

    def test_create_job_block_state_keys_match_block_ids(self, client):
        r_wf = client.post("/workflows", json={"blocks": [READ_CSV_BLOCK, FILTER_BLOCK]})
        wf = r_wf.json()
        expected_ids = {b["id"] for b in wf["blocks"]}
        r_job = client.post("/jobs", json={"workflow_id": wf["id"]})
        assert set(r_job.json()["block_states"].keys()) == expected_ids

    def test_create_job_response_has_no_started_or_finished_at(self, client, created_workflow):
        r = client.post("/jobs", json={"workflow_id": created_workflow["id"]})
        assert r.json()["started_at"] is None
        assert r.json()["finished_at"] is None

    def test_create_job_has_created_at(self, client, created_workflow):
        r = client.post("/jobs", json={"workflow_id": created_workflow["id"]})
        assert r.json()["created_at"] is not None

    def test_create_job_response_no_error_fields(self, client, created_workflow):
        r = client.post("/jobs", json={"workflow_id": created_workflow["id"]})
        assert r.json()["error_message"] is None
        assert r.json()["error_details"] is None

    def test_create_job_response_no_result_or_output(self, client, created_workflow):
        r = client.post("/jobs", json={"workflow_id": created_workflow["id"]})
        assert r.json()["result_preview"] is None
        assert r.json()["output_path"] is None

    def test_create_multiple_jobs_from_same_workflow(self, client, created_workflow):
        wf_id = created_workflow["id"]
        assert client.post("/jobs", json={"workflow_id": wf_id}).status_code == 201
        assert client.post("/jobs", json={"workflow_id": wf_id}).status_code == 201

    # --- Failure cases ---

    def test_create_job_nonexistent_workflow_returns_400(self, client):
        r = client.post("/jobs", json={"workflow_id": "does-not-exist"})
        assert r.status_code == 400
        assert "workflow" in r.json()["detail"].lower()

    def test_create_job_empty_string_workflow_id_returns_400(self, client):
        r = client.post("/jobs", json={"workflow_id": ""})
        assert r.status_code == 400

    def test_create_job_missing_workflow_id_returns_422(self, client):
        r = client.post("/jobs", json={})
        assert r.status_code == 422

    def test_create_job_wrong_type_workflow_id(self, client):
        r = client.post("/jobs", json={"workflow_id": 12345})
        assert r.status_code in (400, 422)


# ===========================================================================
# GET /jobs/{id}
# ===========================================================================

class TestGetJob:

    def test_get_existing_job(self, client, created_job):
        r = client.get(f"/jobs/{created_job['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created_job["id"]

    def test_get_returns_full_schema(self, client, created_job):
        r = client.get(f"/jobs/{created_job['id']}")
        body = r.json()
        for field in (
            "id", "workflow_id", "status", "total_blocks", "completed_blocks",
            "current_block_id", "failed_block_id", "block_states",
            "created_at", "started_at", "finished_at",
            "error_message", "error_details", "result_preview", "output_path",
        ):
            assert field in body, f"Missing field: {field}"

    def test_get_nonexistent_job_returns_404(self, client):
        r = client.get("/jobs/no-such-id")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()


# ===========================================================================
# POST /jobs/{id}/cancel
#
# Tests for PENDING/RUNNING cancellation use `pending_job_id` (store-direct,
# no background execution). Tests for terminal-state behaviour use
# `created_job` + store manipulation to set up the desired state.
# ===========================================================================

class TestCancelJob:

    def test_cancel_pending_job_returns_200(self, client, pending_job_id):
        r = client.post(f"/jobs/{pending_job_id}/cancel")
        assert r.status_code == 200

    def test_cancel_pending_job_status_is_cancelled(self, client, pending_job_id):
        r = client.post(f"/jobs/{pending_job_id}/cancel")
        assert r.json()["status"] == "cancelled"

    def test_cancel_pending_job_finished_at_is_none(self, client, pending_job_id):
        """Job never started (no started_at) → finished_at stays None after cancel."""
        r = client.post(f"/jobs/{pending_job_id}/cancel")
        assert r.json()["finished_at"] is None

    def test_cancel_pending_job_block_states_all_cancelled(self, client):
        from app.models.workflow import WorkflowCreate
        from pydantic import TypeAdapter
        from app.models.block import BlockCreate
        from app.services import workflow_store
        adapter = TypeAdapter(list[BlockCreate])
        blocks = adapter.validate_python([READ_CSV_BLOCK, FILTER_BLOCK])
        wf = workflow_store.create_workflow(WorkflowCreate(blocks=blocks))
        job = job_store.create_job(workflow_id=wf.id)
        r = client.post(f"/jobs/{job.id}/cancel")
        assert all(v == "cancelled" for v in r.json()["block_states"].values())

    def test_cancel_nonexistent_job_returns_404(self, client):
        r = client.post("/jobs/ghost-id/cancel")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_cancel_already_cancelled_is_idempotent(self, client, pending_job_id):
        """Cancelling a CANCELLED job is a 200 no-op."""
        client.post(f"/jobs/{pending_job_id}/cancel")
        r = client.post(f"/jobs/{pending_job_id}/cancel")
        assert r.status_code == 200
        assert r.json()["status"] == "cancelled"

    def test_cancel_completed_job_returns_409(self, client, created_job):
        """Cannot cancel a job that has already completed — returns 409 Conflict."""
        job_id = created_job["id"]
        job_store.update_job(job_id, {
            "status": JobStatus.COMPLETED,
            "finished_at": datetime.now(timezone.utc),
        })
        r = client.post(f"/jobs/{job_id}/cancel")
        assert r.status_code == 409
        assert "completed" in r.json()["detail"].lower()

    def test_cancel_failed_job_returns_409(self, client, created_job):
        """Cannot cancel a job that has already failed — returns 409 Conflict."""
        job_id = created_job["id"]
        job_store.update_job(job_id, {
            "status": JobStatus.FAILED,
            "finished_at": datetime.now(timezone.utc),
            "error_message": "something broke",
        })
        r = client.post(f"/jobs/{job_id}/cancel")
        assert r.status_code == 409
        assert "failed" in r.json()["detail"].lower()

    def test_cancel_running_job_sets_finished_at(self, client, created_job):
        """A RUNNING job (has started_at) gets finished_at set when cancelled."""
        job_id = created_job["id"]
        job_store.update_job(job_id, {
            "status": JobStatus.RUNNING,
            "started_at": datetime.now(timezone.utc),
        })
        r = client.post(f"/jobs/{job_id}/cancel")
        assert r.status_code == 200
        assert r.json()["status"] == "cancelled"
        assert r.json()["finished_at"] is not None

    def test_cancel_running_job_mixed_block_states(self, client):
        """COMPLETED block states are preserved; RUNNING/PENDING become CANCELLED."""
        r_wf = client.post("/workflows", json={"blocks": [READ_CSV_BLOCK, FILTER_BLOCK, SAVE_CSV_BLOCK]})
        wf = r_wf.json()
        r_job = client.post("/jobs", json={"workflow_id": wf["id"]})
        job_id = r_job.json()["id"]
        block_ids = list(r_job.json()["block_states"].keys())

        job_store.update_job(job_id, {
            "status": JobStatus.RUNNING,
            "started_at": datetime.now(timezone.utc),
            "block_states": {
                block_ids[0]: JobStatus.COMPLETED,
                block_ids[1]: JobStatus.RUNNING,
                block_ids[2]: JobStatus.PENDING,
            },
        })

        r = client.post(f"/jobs/{job_id}/cancel")
        states = r.json()["block_states"]
        assert states[block_ids[0]] == "completed"
        assert states[block_ids[1]] == "cancelled"
        assert states[block_ids[2]] == "cancelled"
