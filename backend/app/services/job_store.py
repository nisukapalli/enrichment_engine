from typing import Dict, List, Optional
from datetime import datetime
from app.models.job import Job, JobStatus


# In-memory storage: job_id -> Job
_jobs: Dict[str, Job] = {}


def list_jobs() -> List[Job]:
    return list(_jobs.values())


def get_job(job_id: str) -> Optional[Job]:
    return _jobs.get(job_id)


def create_job(*, workflow_id: str, total_blocks: int) -> Job:
    """
    Create and store a new job for running a workflow.

    Responsibilities (you will implement later):
    - generate job id
    - set status=PENDING
    - set created_at
    - initialize progress fields (completed_blocks=0, current_block_id=None, etc.)
    - optionally initialize block_states
    - store in _jobs
    """
    raise NotImplementedError


def update_job(job_id: str, job: Job) -> None:
    """
    Persist the latest job state into the in-memory store.

    Note: for MVP you can just overwrite _jobs[job_id] = job.
    """
    raise NotImplementedError


def delete_job(job_id: str) -> bool:
    """Delete a job from the store. Returns True if deleted."""
    raise NotImplementedError