from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from typing import List
from app.models.job import Job, JobCreate, JobStatus
from app.services import job_store
from app.services.job_executor import execute_job


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


@router.get("", response_model=List[Job])
def list_jobs():
    return job_store.list_jobs()


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str):
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


@router.post("", response_model=Job, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, background_tasks: BackgroundTasks):
    try:
        job = job_store.create_job(workflow_id=payload.workflow_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    background_tasks.add_task(execute_job, job.id)
    return job


@router.post("/{job_id}/cancel", status_code=status.HTTP_200_OK, response_model=Job)
def cancel_job(job_id: str):
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    if job.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel a {job.status.value} job",
        )
    job_store.cancel_job(job_id)
    return job_store.get_job(job_id)
