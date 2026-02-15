import os
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.workflow import BlockType, JobProgress, Workflow, WorkflowExecution
from app.workflow_engine import WorkflowEngine

router = APIRouter(prefix="/api/workflows", tags=["workflows"])
engine = WorkflowEngine()


@router.get("/blocks")
def list_block_types() -> list[dict[str, Any]]:
    """Return available block types and their parameter schemas for the frontend."""
    return [
        {"type": BlockType.READ_CSV, "label": "Read CSV", "params_schema": {"file_path": "string"}},
        {"type": BlockType.ENRICH_LEAD, "label": "Enrich Lead", "params_schema": {"struct": "object", "research_plan": "string"}},
        {"type": BlockType.FIND_EMAIL, "label": "Find Email", "params_schema": {"mode": "PROFESSIONAL | PERSONAL"}},
        {"type": BlockType.FILTER, "label": "Filter", "params_schema": {"column": "string", "operator": "contains|eq|ne", "value": "any", "expression": "optional pandas query"}},
        {"type": BlockType.SAVE_CSV, "label": "Save CSV", "params_schema": {"output_filename": "string"}},
    ]


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict[str, str]:
    """Upload a CSV file for use in a workflow. Returns the stored filename."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files are allowed")
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(upload_dir, unique_name)
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"file_path": unique_name}


@router.post("/run")
async def run_workflow(background_tasks: BackgroundTasks, body: WorkflowExecution) -> dict[str, str]:
    """Start a workflow run. Returns job_id for polling progress."""
    workflow = body.workflow
    if not workflow.blocks:
        raise HTTPException(400, "Workflow must have at least one block")
    blocks = [b.model_copy(deep=True) for b in workflow.blocks]
    if body.input_file_path and blocks[0].type == BlockType.READ_CSV:
        blocks[0].params["file_path"] = body.input_file_path
    job_id = engine.create_job(blocks)
    background_tasks.add_task(engine.run_workflow, job_id, blocks)
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
def get_job_progress(job_id: str) -> JobProgress | None:
    """Poll job progress and results."""
    return engine.get_progress(job_id)
