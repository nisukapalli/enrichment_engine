"""
Comprehensive tests for /workflows endpoints.

Covers:
  - GET  /workflows
  - POST /workflows
  - GET  /workflows/{id}
  - PATCH /workflows/{id}
  - DELETE /workflows/{id}

Including all validation rules, edge cases, and failure modes.
"""
import pytest
from tests.conftest import READ_CSV_BLOCK, FILTER_BLOCK, SAVE_CSV_BLOCK, ENRICH_LEAD_BLOCK, FIND_EMAIL_BLOCK


# ===========================================================================
# GET /workflows
# ===========================================================================

class TestListWorkflows:
    def test_empty_list_on_startup(self, client):
        r = client.get("/workflows")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_all_created_workflows(self, client):
        client.post("/workflows", json={"name": "A"})
        client.post("/workflows", json={"name": "B"})
        r = client.get("/workflows")
        assert r.status_code == 200
        names = {w["name"] for w in r.json()}
        assert names == {"A", "B"}

    def test_response_is_list(self, client):
        r = client.get("/workflows")
        assert isinstance(r.json(), list)


# ===========================================================================
# POST /workflows
# ===========================================================================

class TestCreateWorkflow:

    # --- Happy path ---

    def test_create_minimal_no_name_no_blocks(self, client):
        """Empty payload is valid; name is auto-generated, blocks is empty."""
        r = client.post("/workflows", json={})
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Workflow 1"
        assert body["blocks"] == []
        assert body["description"] is None

    def test_create_with_explicit_name(self, client):
        r = client.post("/workflows", json={"name": "My Pipeline"})
        assert r.status_code == 201
        assert r.json()["name"] == "My Pipeline"

    def test_create_with_description(self, client):
        r = client.post("/workflows", json={"name": "W", "description": "A test"})
        assert r.status_code == 201
        assert r.json()["description"] == "A test"

    def test_create_assigns_unique_id(self, client):
        r1 = client.post("/workflows", json={"name": "W1"})
        r2 = client.post("/workflows", json={"name": "W2"})
        assert r1.json()["id"] != r2.json()["id"]

    def test_create_sets_timestamps(self, client):
        r = client.post("/workflows", json={"name": "W"})
        body = r.json()
        assert "created_at" in body
        assert "updated_at" in body
        assert body["created_at"] == body["updated_at"]

    def test_create_with_single_read_csv_block(self, client):
        r = client.post("/workflows", json={"blocks": [READ_CSV_BLOCK]})
        assert r.status_code == 201
        blocks = r.json()["blocks"]
        assert len(blocks) == 1
        assert blocks[0]["type"] == "read_csv"
        assert "id" in blocks[0]  # UUID assigned

    def test_create_blocks_get_unique_ids(self, client):
        payload = {"blocks": [READ_CSV_BLOCK, FILTER_BLOCK, SAVE_CSV_BLOCK]}
        r = client.post("/workflows", json=payload)
        assert r.status_code == 201
        ids = [b["id"] for b in r.json()["blocks"]]
        assert len(ids) == len(set(ids))  # all unique

    def test_create_full_block_chain(self, client):
        payload = {
            "blocks": [READ_CSV_BLOCK, FILTER_BLOCK, ENRICH_LEAD_BLOCK, FIND_EMAIL_BLOCK, SAVE_CSV_BLOCK]
        }
        r = client.post("/workflows", json=payload)
        assert r.status_code == 201
        assert len(r.json()["blocks"]) == 5

    def test_create_with_named_blocks(self, client):
        block = {**READ_CSV_BLOCK, "name": "Load Leads"}
        r = client.post("/workflows", json={"blocks": [block]})
        assert r.status_code == 201
        assert r.json()["blocks"][0]["name"] == "Load Leads"

    def test_create_enrich_lead_with_research_plan(self, client):
        block = {
            "type": "enrich_lead",
            "params": {"struct": {"bio": "short bio"}, "research_plan": "search LinkedIn"},
        }
        r = client.post("/workflows", json={"blocks": [READ_CSV_BLOCK, block]})
        assert r.status_code == 201

    def test_create_find_email_personal_mode(self, client):
        block = {"type": "find_email", "params": {"mode": "PERSONAL"}}
        r = client.post("/workflows", json={"blocks": [READ_CSV_BLOCK, block]})
        assert r.status_code == 201
        assert r.json()["blocks"][1]["params"]["mode"] == "PERSONAL"

    def test_create_filter_all_operators(self, client):
        operators = ["contains", "not_contains", "equals", "not_equals", "gt", "gte", "lt", "lte"]
        for op in operators:
            payload = {
                "blocks": [
                    READ_CSV_BLOCK,
                    {"type": "filter", "params": {"column": "x", "operator": op, "value": "1"}},
                ]
            }
            r = client.post("/workflows", json=payload)
            assert r.status_code == 201, f"Operator '{op}' failed: {r.json()}"

    # --- Auto-naming ---

    def test_auto_name_sequential(self, client):
        r1 = client.post("/workflows", json={})
        r2 = client.post("/workflows", json={})
        r3 = client.post("/workflows", json={})
        assert r1.json()["name"] == "Workflow 1"
        assert r2.json()["name"] == "Workflow 2"
        assert r3.json()["name"] == "Workflow 3"

    def test_auto_name_fills_gap_after_delete(self, client):
        r1 = client.post("/workflows", json={})
        wf_id = r1.json()["id"]
        client.post("/workflows", json={})  # Workflow 2
        client.delete(f"/workflows/{wf_id}")  # remove Workflow 1
        r3 = client.post("/workflows", json={})  # should fill gap → Workflow 1
        assert r3.json()["name"] == "Workflow 1"

    def test_explicit_name_does_not_affect_autonaming_counter(self, client):
        client.post("/workflows", json={"name": "Custom"})  # non-default name
        r = client.post("/workflows", json={})
        assert r.json()["name"] == "Workflow 1"

    def test_auto_name_ignores_non_numeric_suffix(self, client):
        client.post("/workflows", json={"name": "Workflow abc"})
        r = client.post("/workflows", json={})
        assert r.json()["name"] == "Workflow 1"

    def test_auto_name_ignores_empty_suffix(self, client):
        client.post("/workflows", json={"name": "Workflow "})
        r = client.post("/workflows", json={})
        assert r.json()["name"] == "Workflow 1"

    # --- Block chain validation failures → 400 ---

    def test_create_fails_if_first_block_is_filter(self, client):
        r = client.post("/workflows", json={"blocks": [FILTER_BLOCK]})
        assert r.status_code == 400
        assert "read_csv" in r.json()["detail"].lower()

    def test_create_fails_if_first_block_is_save_csv(self, client):
        r = client.post("/workflows", json={"blocks": [SAVE_CSV_BLOCK]})
        assert r.status_code == 400

    def test_create_fails_if_first_block_is_enrich_lead(self, client):
        r = client.post("/workflows", json={"blocks": [ENRICH_LEAD_BLOCK]})
        assert r.status_code == 400

    def test_create_fails_if_first_block_is_find_email(self, client):
        r = client.post("/workflows", json={"blocks": [FIND_EMAIL_BLOCK]})
        assert r.status_code == 400

    def test_create_fails_if_read_csv_appears_second(self, client):
        r = client.post("/workflows", json={"blocks": [READ_CSV_BLOCK, READ_CSV_BLOCK]})
        assert r.status_code == 400
        assert "read_csv" in r.json()["detail"].lower()

    def test_create_fails_if_read_csv_appears_third(self, client):
        r = client.post("/workflows", json={
            "blocks": [READ_CSV_BLOCK, FILTER_BLOCK, READ_CSV_BLOCK]
        })
        assert r.status_code == 400

    # --- Pydantic validation failures → 422 ---

    def test_create_fails_with_invalid_block_type(self, client):
        r = client.post("/workflows", json={
            "blocks": [{"type": "unknown_block", "params": {}}]
        })
        assert r.status_code == 422

    def test_create_fails_with_missing_read_csv_path(self, client):
        r = client.post("/workflows", json={
            "blocks": [{"type": "read_csv", "params": {}}]
        })
        assert r.status_code == 422

    def test_create_fails_with_missing_filter_params(self, client):
        r = client.post("/workflows", json={
            "blocks": [READ_CSV_BLOCK, {"type": "filter", "params": {"column": "x"}}]
        })
        assert r.status_code == 422

    def test_create_fails_with_invalid_filter_operator(self, client):
        r = client.post("/workflows", json={
            "blocks": [
                READ_CSV_BLOCK,
                {"type": "filter", "params": {"column": "x", "operator": "between", "value": "1"}},
            ]
        })
        assert r.status_code == 422

    def test_create_fails_with_invalid_find_email_mode(self, client):
        r = client.post("/workflows", json={
            "blocks": [
                READ_CSV_BLOCK,
                {"type": "find_email", "params": {"mode": "BUSINESS"}},
            ]
        })
        assert r.status_code == 422

    def test_create_fails_with_missing_enrich_struct(self, client):
        r = client.post("/workflows", json={
            "blocks": [READ_CSV_BLOCK, {"type": "enrich_lead", "params": {}}]
        })
        assert r.status_code == 422


# ===========================================================================
# GET /workflows/{id}
# ===========================================================================

class TestGetWorkflow:

    def test_get_existing_workflow(self, client, created_workflow):
        wf_id = created_workflow["id"]
        r = client.get(f"/workflows/{wf_id}")
        assert r.status_code == 200
        assert r.json()["id"] == wf_id

    def test_get_returns_full_schema(self, client, created_workflow):
        r = client.get(f"/workflows/{created_workflow['id']}")
        body = r.json()
        for field in ("id", "name", "description", "blocks", "created_at", "updated_at"):
            assert field in body, f"Missing field: {field}"

    def test_get_nonexistent_returns_404(self, client):
        r = client.get("/workflows/does-not-exist")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_get_empty_id_segment_not_routed_as_detail(self, client):
        # An empty id resolves to GET /workflows (list), not detail
        r = client.get("/workflows/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ===========================================================================
# PATCH /workflows/{id}
# ===========================================================================

class TestUpdateWorkflow:

    def test_update_name(self, client, created_workflow):
        wf_id = created_workflow["id"]
        r = client.patch(f"/workflows/{wf_id}", json={"name": "Renamed"})
        assert r.status_code == 200
        assert r.json()["name"] == "Renamed"

    def test_update_description(self, client, created_workflow):
        wf_id = created_workflow["id"]
        r = client.patch(f"/workflows/{wf_id}", json={"description": "New desc"})
        assert r.status_code == 200
        assert r.json()["description"] == "New desc"

    def test_update_blocks(self, client, created_workflow):
        wf_id = created_workflow["id"]
        new_blocks = [READ_CSV_BLOCK, FILTER_BLOCK]
        r = client.patch(f"/workflows/{wf_id}", json={"blocks": new_blocks})
        assert r.status_code == 200
        assert len(r.json()["blocks"]) == 2

    def test_update_blocks_generates_new_uuids(self, client, created_workflow):
        wf_id = created_workflow["id"]
        original_block_id = created_workflow["blocks"][0]["id"]
        r = client.patch(f"/workflows/{wf_id}", json={"blocks": [READ_CSV_BLOCK]})
        new_block_id = r.json()["blocks"][0]["id"]
        assert new_block_id != original_block_id

    def test_update_bumps_updated_at_but_not_created_at(self, client, created_workflow):
        wf_id = created_workflow["id"]
        original_created = created_workflow["created_at"]
        original_updated = created_workflow["updated_at"]
        r = client.patch(f"/workflows/{wf_id}", json={"name": "Changed"})
        body = r.json()
        assert body["created_at"] == original_created
        assert body["updated_at"] >= original_updated

    def test_update_empty_payload_returns_unchanged(self, client, created_workflow):
        wf_id = created_workflow["id"]
        r = client.patch(f"/workflows/{wf_id}", json={})
        assert r.status_code == 200
        assert r.json()["name"] == created_workflow["name"]

    def test_update_nonexistent_returns_404(self, client):
        r = client.patch("/workflows/no-such-id", json={"name": "X"})
        assert r.status_code == 404

    def test_update_fails_invalid_block_chain(self, client, created_workflow):
        wf_id = created_workflow["id"]
        r = client.patch(f"/workflows/{wf_id}", json={"blocks": [FILTER_BLOCK]})
        assert r.status_code == 400

    def test_update_fails_read_csv_at_position_1(self, client, created_workflow):
        wf_id = created_workflow["id"]
        r = client.patch(f"/workflows/{wf_id}", json={
            "blocks": [READ_CSV_BLOCK, READ_CSV_BLOCK]
        })
        assert r.status_code == 400

    def test_update_to_empty_blocks_is_valid(self, client, created_workflow):
        """Clearing all blocks is allowed (empty chain passes validation)."""
        wf_id = created_workflow["id"]
        r = client.patch(f"/workflows/{wf_id}", json={"blocks": []})
        assert r.status_code == 200
        assert r.json()["blocks"] == []

    def test_update_name_to_null_explicitly(self, client, created_workflow):
        """PATCH {"name": null} is treated as a no-op — name stays unchanged."""
        wf_id = created_workflow["id"]
        original_name = created_workflow["name"]
        r = client.patch(f"/workflows/{wf_id}", json={"name": None})
        assert r.status_code == 200
        assert r.json()["name"] == original_name

    def test_update_blocks_to_null_explicitly(self, client, created_workflow):
        """PATCH {"blocks": null} is treated as a no-op — blocks stay unchanged."""
        wf_id = created_workflow["id"]
        original_blocks = created_workflow["blocks"]
        r = client.patch(f"/workflows/{wf_id}", json={"blocks": None})
        assert r.status_code == 200
        assert r.json()["blocks"] == original_blocks


# ===========================================================================
# DELETE /workflows/{id}
# ===========================================================================

class TestDeleteWorkflow:

    def test_delete_existing_returns_204(self, client, created_workflow):
        wf_id = created_workflow["id"]
        r = client.delete(f"/workflows/{wf_id}")
        assert r.status_code == 204
        assert r.content == b""

    def test_delete_then_get_returns_404(self, client, created_workflow):
        wf_id = created_workflow["id"]
        client.delete(f"/workflows/{wf_id}")
        r = client.get(f"/workflows/{wf_id}")
        assert r.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        r = client.delete("/workflows/ghost-id")
        assert r.status_code == 404

    def test_delete_is_not_idempotent(self, client, created_workflow):
        """Deleting twice: first is 204, second is 404."""
        wf_id = created_workflow["id"]
        client.delete(f"/workflows/{wf_id}")
        r = client.delete(f"/workflows/{wf_id}")
        assert r.status_code == 404

    def test_delete_removes_from_list(self, client, created_workflow):
        wf_id = created_workflow["id"]
        client.delete(f"/workflows/{wf_id}")
        ids = [w["id"] for w in client.get("/workflows").json()]
        assert wf_id not in ids

    def test_delete_workflow_with_pending_job_returns_409(self, client, created_workflow):
        """Cannot delete a workflow that has a pending job."""
        wf_id = created_workflow["id"]
        from app.services import job_store
        job_store.create_job(workflow_id=wf_id)
        r = client.delete(f"/workflows/{wf_id}")
        assert r.status_code == 409
        assert "active job" in r.json()["detail"].lower()

    def test_delete_workflow_with_running_job_returns_409(self, client, created_workflow):
        """Cannot delete a workflow that has a running job."""
        from app.services import job_store
        from app.models.job import JobStatus
        from datetime import datetime, timezone
        wf_id = created_workflow["id"]
        job = job_store.create_job(workflow_id=wf_id)
        job_store.update_job(job.id, {"status": JobStatus.RUNNING, "started_at": datetime.now(timezone.utc)})
        r = client.delete(f"/workflows/{wf_id}")
        assert r.status_code == 409

    def test_delete_workflow_with_completed_job_succeeds(self, client, created_workflow):
        """A completed job does not block deletion."""
        from app.services import job_store
        from app.models.job import JobStatus
        from datetime import datetime, timezone
        wf_id = created_workflow["id"]
        job = job_store.create_job(workflow_id=wf_id)
        job_store.update_job(job.id, {"status": JobStatus.COMPLETED, "finished_at": datetime.now(timezone.utc)})
        r = client.delete(f"/workflows/{wf_id}")
        assert r.status_code == 204

    def test_delete_workflow_with_failed_job_succeeds(self, client, created_workflow):
        """A failed job does not block deletion."""
        from app.services import job_store
        from app.models.job import JobStatus
        from datetime import datetime, timezone
        wf_id = created_workflow["id"]
        job = job_store.create_job(workflow_id=wf_id)
        job_store.update_job(job.id, {"status": JobStatus.FAILED, "finished_at": datetime.now(timezone.utc)})
        r = client.delete(f"/workflows/{wf_id}")
        assert r.status_code == 204
