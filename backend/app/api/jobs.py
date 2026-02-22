from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.job import Job, JobCreate
from app.services import job_store


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


@router.get("/", response_model=List[Job])
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


@router.post("/", response_model=Job, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate):
    try:
        return job_store.create_job(workflow_id=payload.workflow_id)
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


@router.post("/{job_id}/cancel", status_code=status.HTTP_200_OK, response_model=Job)
def cancel_job(job_id: str):
    ok = job_store.cancel_job(job_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job