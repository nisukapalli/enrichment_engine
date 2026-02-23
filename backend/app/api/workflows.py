from fastapi import APIRouter, HTTPException, Response, status
from typing import List
from app.models.workflow import Workflow, WorkflowCreate, WorkflowUpdate
from app.services import workflow_store


router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
)


@router.get("", response_model=List[Workflow])
def list_workflows():
    return workflow_store.list_workflows()


@router.get("/{workflow_id}", response_model=Workflow)
def get_workflow(workflow_id: str):
    workflow = workflow_store.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return workflow


@router.post("", response_model=Workflow, status_code=status.HTTP_201_CREATED)
def create_workflow(payload: WorkflowCreate):
    try:
        return workflow_store.create_workflow(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/{workflow_id}", response_model=Workflow)
def update_workflow(workflow_id: str, payload: WorkflowUpdate):
    try:
        updated = workflow_store.update_workflow(workflow_id, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return updated


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(workflow_id: str):
    if not workflow_store.delete_workflow(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)