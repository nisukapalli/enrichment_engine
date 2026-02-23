"""
Comprehensive unit tests for workflow_store and job_store.

These test the internal Python functions directly, bypassing HTTP.
"""
import pytest
from datetime import datetime, timezone

from app.models.job import JobStatus
from app.models.workflow import WorkflowCreate, WorkflowUpdate
from app.services import workflow_store, job_store


# ===========================================================================
# workflow_store — generate_default_name
# ===========================================================================

class TestGenerateDefaultName:

    def test_first_name_is_workflow_1(self):
        assert workflow_store.generate_default_name() == "Workflow 1"

    def test_increments_sequentially(self):
        workflow_store.create_workflow(WorkflowCreate(name=None))  # Workflow 1
        assert workflow_store.generate_default_name() == "Workflow 2"

    def test_fills_gap_after_delete(self):
        w1 = workflow_store.create_workflow(WorkflowCreate(name=None))  # Workflow 1
        workflow_store.create_workflow(WorkflowCreate(name=None))        # Workflow 2
        workflow_store.delete_workflow(w1.id)                            # remove Workflow 1
        assert workflow_store.generate_default_name() == "Workflow 1"

    def test_non_standard_names_dont_affect_counter(self):
        workflow_store.create_workflow(WorkflowCreate(name="Custom Pipeline"))
        assert workflow_store.generate_default_name() == "Workflow 1"

    def test_non_numeric_suffix_ignored(self):
        workflow_store.create_workflow(WorkflowCreate(name="Workflow abc"))
        assert workflow_store.generate_default_name() == "Workflow 1"

    def test_empty_suffix_ignored(self):
        workflow_store.create_workflow(WorkflowCreate(name="Workflow "))
        assert workflow_store.generate_default_name() == "Workflow 1"

    def test_zero_suffix_ignored(self):
        # "Workflow 0" — counter starts at 1, so 0 is irrelevant
        workflow_store.create_workflow(WorkflowCreate(name="Workflow 0"))
        assert workflow_store.generate_default_name() == "Workflow 1"

    def test_allocates_large_number(self):
        # Simulate many existing workflows
        for i in range(1, 6):
            workflow_store.create_workflow(WorkflowCreate(name=f"Workflow {i}"))
        assert workflow_store.generate_default_name() == "Workflow 6"


# ===========================================================================
# workflow_store — _validate_block_chain
# ===========================================================================

class TestValidateBlockChain:
    """Test via create_workflow which calls _validate_block_chain internally."""

    READ = [{"type": "read_csv", "params": {"path": "f.csv"}}]
    FILTER = [{"type": "filter", "params": {"column": "x", "operator": "gt", "value": "1"}}]
    SAVE = [{"type": "save_csv", "params": {"path": "out.csv"}}]

    def _create(self, blocks):
        from app.models.workflow import WorkflowCreate
        from pydantic import TypeAdapter
        from app.models.block import BlockCreate
        adapter = TypeAdapter(list[BlockCreate])
        parsed = adapter.validate_python(blocks)
        return workflow_store.create_workflow(WorkflowCreate(blocks=parsed))

    def _create_should_fail(self, blocks):
        with pytest.raises(ValueError):
            self._create(blocks)

    def test_empty_blocks_is_valid(self):
        w = workflow_store.create_workflow(WorkflowCreate())
        assert w.blocks == []

    def test_read_csv_only_is_valid(self):
        w = self._create(self.READ)
        assert len(w.blocks) == 1

    def test_read_csv_then_filter_is_valid(self):
        w = self._create(self.READ + self.FILTER)
        assert len(w.blocks) == 2

    def test_read_csv_then_filter_then_save_is_valid(self):
        w = self._create(self.READ + self.FILTER + self.SAVE)
        assert len(w.blocks) == 3

    def test_filter_first_is_invalid(self):
        self._create_should_fail(self.FILTER)

    def test_save_first_is_invalid(self):
        self._create_should_fail(self.SAVE)

    def test_read_csv_at_position_1_is_invalid(self):
        self._create_should_fail(self.READ + self.READ)

    def test_read_csv_at_position_2_is_invalid(self):
        self._create_should_fail(self.READ + self.FILTER + self.READ)

    def test_error_message_mentions_read_csv(self):
        with pytest.raises(ValueError, match="read_csv"):
            self._create(self.FILTER)


# ===========================================================================
# workflow_store — CRUD
# ===========================================================================

class TestWorkflowStoreCrud:

    def test_create_assigns_unique_ids(self):
        w1 = workflow_store.create_workflow(WorkflowCreate(name="A"))
        w2 = workflow_store.create_workflow(WorkflowCreate(name="B"))
        assert w1.id != w2.id

    def test_create_sets_created_and_updated_at_equal(self):
        w = workflow_store.create_workflow(WorkflowCreate(name="W"))
        assert w.created_at == w.updated_at

    def test_list_workflows_returns_all(self):
        workflow_store.create_workflow(WorkflowCreate(name="X"))
        workflow_store.create_workflow(WorkflowCreate(name="Y"))
        all_wf = workflow_store.list_workflows()
        assert len(all_wf) == 2

    def test_get_workflow_returns_correct(self):
        w = workflow_store.create_workflow(WorkflowCreate(name="Z"))
        found = workflow_store.get_workflow(w.id)
        assert found is not None
        assert found.id == w.id

    def test_get_workflow_returns_none_for_missing(self):
        assert workflow_store.get_workflow("no-such-id") is None

    def test_delete_returns_true(self):
        w = workflow_store.create_workflow(WorkflowCreate(name="Del"))
        assert workflow_store.delete_workflow(w.id) is True

    def test_delete_returns_false_for_missing(self):
        assert workflow_store.delete_workflow("ghost") is False

    def test_delete_removes_from_store(self):
        w = workflow_store.create_workflow(WorkflowCreate(name="RM"))
        workflow_store.delete_workflow(w.id)
        assert workflow_store.get_workflow(w.id) is None

    def test_update_name_changes_name(self):
        w = workflow_store.create_workflow(WorkflowCreate(name="Old"))
        updated = workflow_store.update_workflow(w.id, WorkflowUpdate(name="New"))
        assert updated.name == "New"

    def test_update_bumps_updated_at(self):
        w = workflow_store.create_workflow(WorkflowCreate(name="W"))
        original_updated_at = w.updated_at
        updated = workflow_store.update_workflow(w.id, WorkflowUpdate(name="W2"))
        assert updated.updated_at >= original_updated_at

    def test_update_does_not_change_created_at(self):
        w = workflow_store.create_workflow(WorkflowCreate(name="W"))
        updated = workflow_store.update_workflow(w.id, WorkflowUpdate(name="W2"))
        assert updated.created_at == w.created_at

    def test_update_empty_payload_returns_unchanged_workflow(self):
        w = workflow_store.create_workflow(WorkflowCreate(name="Stable"))
        result = workflow_store.update_workflow(w.id, WorkflowUpdate())
        assert result.name == "Stable"

    def test_update_returns_none_for_missing(self):
        result = workflow_store.update_workflow("ghost", WorkflowUpdate(name="X"))
        assert result is None

    def test_blocks_get_new_uuids_on_update(self):
        from pydantic import TypeAdapter
        from app.models.block import BlockCreate
        adapter = TypeAdapter(list[BlockCreate])
        blocks = adapter.validate_python([{"type": "read_csv", "params": {"path": "f.csv"}}])
        w = workflow_store.create_workflow(WorkflowCreate(blocks=blocks))
        original_block_id = w.blocks[0].id

        updated = workflow_store.update_workflow(w.id, WorkflowUpdate(blocks=blocks))
        new_block_id = updated.blocks[0].id
        assert new_block_id != original_block_id


# ===========================================================================
# job_store — CRUD and lifecycle
# ===========================================================================

class TestJobStoreCrud:

    @pytest.fixture
    def wf(self):
        return workflow_store.create_workflow(WorkflowCreate(name="TestWF"))

    @pytest.fixture
    def wf_with_blocks(self):
        from pydantic import TypeAdapter
        from app.models.block import BlockCreate
        adapter = TypeAdapter(list[BlockCreate])
        blocks = adapter.validate_python([
            {"type": "read_csv", "params": {"path": "f.csv"}},
            {"type": "filter", "params": {"column": "x", "operator": "gt", "value": "1"}},
        ])
        return workflow_store.create_workflow(WorkflowCreate(blocks=blocks))

    def test_create_job_valid_workflow(self, wf):
        job = job_store.create_job(workflow_id=wf.id)
        assert job.workflow_id == wf.id
        assert job.status == JobStatus.PENDING

    def test_create_job_raises_for_missing_workflow(self):
        with pytest.raises(ValueError, match="Workflow not found"):
            job_store.create_job(workflow_id="ghost")

    def test_create_job_total_blocks_matches_workflow(self, wf_with_blocks):
        job = job_store.create_job(workflow_id=wf_with_blocks.id)
        assert job.total_blocks == 2

    def test_create_job_block_states_all_pending(self, wf_with_blocks):
        job = job_store.create_job(workflow_id=wf_with_blocks.id)
        assert all(v == JobStatus.PENDING for v in job.block_states.values())

    def test_create_job_block_state_keys_are_block_ids(self, wf_with_blocks):
        expected = {b.id for b in wf_with_blocks.blocks}
        job = job_store.create_job(workflow_id=wf_with_blocks.id)
        assert set(job.block_states.keys()) == expected

    def test_list_jobs_empty(self):
        assert job_store.list_jobs() == []

    def test_list_jobs_returns_all(self, wf):
        job_store.create_job(workflow_id=wf.id)
        job_store.create_job(workflow_id=wf.id)
        assert len(job_store.list_jobs()) == 2

    def test_get_job_returns_correct(self, wf):
        job = job_store.create_job(workflow_id=wf.id)
        found = job_store.get_job(job.id)
        assert found.id == job.id

    def test_get_job_returns_none_for_missing(self):
        assert job_store.get_job("ghost") is None

    def test_update_job_modifies_fields(self, wf):
        job = job_store.create_job(workflow_id=wf.id)
        updated = job_store.update_job(job.id, {"status": JobStatus.RUNNING})
        assert updated.status == JobStatus.RUNNING

    def test_update_job_returns_none_for_missing(self):
        assert job_store.update_job("ghost", {"status": JobStatus.RUNNING}) is None


# ===========================================================================
# job_store — cancel_job
# ===========================================================================

class TestCancelJob:

    @pytest.fixture
    def job(self):
        wf = workflow_store.create_workflow(WorkflowCreate(name="WF"))
        return job_store.create_job(workflow_id=wf.id)

    @pytest.fixture
    def job_with_blocks(self):
        from pydantic import TypeAdapter
        from app.models.block import BlockCreate
        adapter = TypeAdapter(list[BlockCreate])
        blocks = adapter.validate_python([
            {"type": "read_csv", "params": {"path": "f.csv"}},
            {"type": "save_csv", "params": {"path": "out.csv"}},
        ])
        wf = workflow_store.create_workflow(WorkflowCreate(blocks=blocks))
        return job_store.create_job(workflow_id=wf.id)

    def test_cancel_nonexistent_returns_false(self):
        assert job_store.cancel_job("ghost") is False

    def test_cancel_pending_returns_true(self, job):
        assert job_store.cancel_job(job.id) is True

    def test_cancel_pending_sets_status_cancelled(self, job):
        job_store.cancel_job(job.id)
        assert job_store.get_job(job.id).status == JobStatus.CANCELLED

    def test_cancel_pending_never_started_finished_at_is_none(self, job):
        """No started_at → finished_at should remain None after cancel."""
        assert job.started_at is None
        job_store.cancel_job(job.id)
        assert job_store.get_job(job.id).finished_at is None

    def test_cancel_running_job_sets_finished_at(self, job):
        job_store.update_job(job.id, {
            "status": JobStatus.RUNNING,
            "started_at": datetime.now(timezone.utc),
        })
        job_store.cancel_job(job.id)
        assert job_store.get_job(job.id).finished_at is not None

    def test_cancel_completed_is_noop_returns_true(self, job):
        job_store.update_job(job.id, {
            "status": JobStatus.COMPLETED,
            "finished_at": datetime.now(timezone.utc),
        })
        assert job_store.cancel_job(job.id) is True
        assert job_store.get_job(job.id).status == JobStatus.COMPLETED

    def test_cancel_failed_is_noop_returns_true(self, job):
        job_store.update_job(job.id, {
            "status": JobStatus.FAILED,
            "finished_at": datetime.now(timezone.utc),
        })
        assert job_store.cancel_job(job.id) is True
        assert job_store.get_job(job.id).status == JobStatus.FAILED

    def test_cancel_already_cancelled_is_noop(self, job):
        job_store.cancel_job(job.id)
        assert job_store.cancel_job(job.id) is True
        assert job_store.get_job(job.id).status == JobStatus.CANCELLED

    def test_cancel_sets_all_pending_block_states_to_cancelled(self, job_with_blocks):
        job_store.cancel_job(job_with_blocks.id)
        states = job_store.get_job(job_with_blocks.id).block_states
        assert all(v == JobStatus.CANCELLED for v in states.values())

    def test_cancel_preserves_completed_block_states(self, job_with_blocks):
        block_ids = list(job_with_blocks.block_states.keys())
        # Mark first block as completed
        job_store.update_job(job_with_blocks.id, {
            "status": JobStatus.RUNNING,
            "started_at": datetime.now(timezone.utc),
            "block_states": {
                block_ids[0]: JobStatus.COMPLETED,
                block_ids[1]: JobStatus.PENDING,
            },
        })
        job_store.cancel_job(job_with_blocks.id)
        states = job_store.get_job(job_with_blocks.id).block_states
        assert states[block_ids[0]] == JobStatus.COMPLETED  # unchanged
        assert states[block_ids[1]] == JobStatus.CANCELLED  # was pending

    def test_cancel_preserves_failed_block_states(self, job_with_blocks):
        block_ids = list(job_with_blocks.block_states.keys())
        job_store.update_job(job_with_blocks.id, {
            "status": JobStatus.RUNNING,
            "started_at": datetime.now(timezone.utc),
            "block_states": {
                block_ids[0]: JobStatus.FAILED,
                block_ids[1]: JobStatus.PENDING,
            },
        })
        job_store.cancel_job(job_with_blocks.id)
        states = job_store.get_job(job_with_blocks.id).block_states
        assert states[block_ids[0]] == JobStatus.FAILED   # unchanged
        assert states[block_ids[1]] == JobStatus.CANCELLED
