"""
Background job executor.

Runs all blocks in a workflow sequentially, updating job and per-block
states (PENDING → RUNNING → COMPLETED | FAILED) as execution proceeds.
Checks for cancellation before each block so that cancel requests are
honoured between steps.
"""
import asyncio
import os
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from app.models.job import JobStatus
from app.models.block import BlockType
from app.services import job_store, workflow_store
from app.services.block_runners import (
    run_read_csv,
    run_filter,
    run_save_csv,
    run_enrich_lead,
    run_find_email,
)


async def execute_job(job_id: str) -> None:
    try:
        await _execute_job_inner(job_id)
    except Exception as exc:
        job_store.update_job(job_id, {
            "status": JobStatus.FAILED,
            "current_block_id": None,
            "error_message": f"Unexpected executor error: {exc}",
            "finished_at": datetime.now(timezone.utc),
        })


async def _execute_job_inner(job_id: str) -> None:
    job = job_store.get_job(job_id)
    if job is None or job.status == JobStatus.CANCELLED:
        return

    workflow = workflow_store.get_workflow(job.workflow_id)
    if workflow is None:
        job_store.update_job(job_id, {
            "status": JobStatus.FAILED,
            "error_message": "Workflow not found",
            "finished_at": datetime.now(timezone.utc),
        })
        return

    job_store.update_job(job_id, {
        "status": JobStatus.RUNNING,
        "started_at": datetime.now(timezone.utc),
    })

    df: Optional[pd.DataFrame] = None

    for block in workflow.blocks:
        current_job = job_store.get_job(job_id)
        if current_job is None or current_job.status == JobStatus.CANCELLED:
            return

        updated_states = {**current_job.block_states, block.id: JobStatus.RUNNING}
        job_store.update_job(job_id, {
            "current_block_id": block.id,
            "block_states": updated_states,
        })

        try:
            if block.type == BlockType.READ_CSV:
                df = await asyncio.to_thread(run_read_csv, block)
            elif block.type == BlockType.FILTER:
                df = await asyncio.to_thread(run_filter, block, df)
            elif block.type == BlockType.ENRICH_LEAD:
                df = await run_enrich_lead(block, df)
            elif block.type == BlockType.FIND_EMAIL:
                df = await run_find_email(block, df)
            elif block.type == BlockType.SAVE_CSV:
                df = await asyncio.to_thread(run_save_csv, block, df)
        except Exception as exc:
            current_job = job_store.get_job(job_id)
            updated_states = {**current_job.block_states, block.id: JobStatus.FAILED}
            job_store.update_job(job_id, {
                "status": JobStatus.FAILED,
                "failed_block_id": block.id,
                "current_block_id": None,
                "error_message": str(exc),
                "block_states": updated_states,
                "finished_at": datetime.now(timezone.utc),
            })
            return

        current_job = job_store.get_job(job_id)
        updated_states = {**current_job.block_states, block.id: JobStatus.COMPLETED}
        block_previews = dict(current_job.block_previews or {})
        if df is not None and not df.empty:
            block_previews[block.id] = {
                "columns": list(df.columns),
                "rows": df.head(5).to_dict(orient="records"),
            }
        job_store.update_job(job_id, {
            "completed_blocks": current_job.completed_blocks + 1,
            "current_block_id": None,
            "block_states": updated_states,
            "block_previews": block_previews,
        })

    result_preview = None
    output_path = None
    if df is not None and not df.empty:
        result_preview = {
            "columns": list(df.columns),
            "rows": df.head(5).to_dict(orient="records"),
        }
    if workflow.blocks and workflow.blocks[-1].type == BlockType.SAVE_CSV:
        output_path = os.path.basename(workflow.blocks[-1].params.path) or None

    job_store.update_job(job_id, {
        "status": JobStatus.COMPLETED,
        "current_block_id": None,
        "finished_at": datetime.now(timezone.utc),
        "result_preview": result_preview,
        "output_path": output_path,
    })
