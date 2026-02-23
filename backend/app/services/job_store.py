import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from app.models.job import Job, JobStatus
from app.services import workflow_store


# In-memory storage: job_id -> Job
_jobs: Dict[str, Job] = {}


def list_jobs() -> List[Job]:
    return list(_jobs.values())


def get_job(job_id: str) -> Optional[Job]:
    return _jobs.get(job_id)


def create_job(*, workflow_id: str) -> Job:
    workflow = workflow_store.get_workflow(workflow_id)
    if workflow is None:
        raise ValueError("Workflow not found")
    
    job_id = uuid.uuid4().hex
    total_blocks = len(workflow.blocks)
    block_states = {block.id: JobStatus.PENDING for block in workflow.blocks}
    job = Job(
        id=job_id,
        workflow_id=workflow_id,
        status=JobStatus.PENDING,
        total_blocks=total_blocks,
        block_states=block_states,
        created_at=datetime.now(timezone.utc),
    )
    _jobs[job_id] = job
    return job


def update_job(job_id: str, updates: Dict[str, Any]) -> Optional[Job]:
    job = _jobs.get(job_id)
    if job is None:
        return None
    if not updates:
        return job

    updated_job = job.model_copy(update=updates)
    _jobs[job_id] = updated_job
    return updated_job


def cancel_job(job_id: str) -> bool:
    job = _jobs.get(job_id)
    if job is None:
        return False
    if job.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
        return True
    
    now = datetime.now(timezone.utc)
    terminal = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
    finished_at = now if job.started_at is not None else None
    cancelled_block_states = {
        block_id: (state if state in terminal else JobStatus.CANCELLED)
        for block_id, state in job.block_states.items()
    }
    updated_job = job.model_copy(
        update={
            "status": JobStatus.CANCELLED,
            "finished_at": finished_at,
            "block_states": cancelled_block_states,
        }
    )
    _jobs[job_id] = updated_job
    return True