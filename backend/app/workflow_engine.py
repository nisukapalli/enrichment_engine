"""
Workflow execution engine. Runs a list of blocks in order, passing DataFrame between them.
Supports async execution and progress reporting.
"""

import logging
import uuid

import pandas as pd

from app.blocks import (
    EnrichLeadBlock,
    FilterBlock,
    FindEmailBlock,
    ReadCsvBlock,
    SaveCsvBlock,
)
from app.workflow import (
    Block,
    BlockResult,
    BlockType,
    JobProgress,
    JobStatus,
)

# Registry of block type -> block class
BLOCK_TYPES: dict[BlockType, type] = {
    BlockType.READ_CSV: ReadCsvBlock,
    BlockType.ENRICH_LEAD: EnrichLeadBlock,
    BlockType.FIND_EMAIL: FindEmailBlock,
    BlockType.FILTER: FilterBlock,
    BlockType.SAVE_CSV: SaveCsvBlock,
}

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Orchestrates workflow execution by running blocks sequentially.

    Each block receives the DataFrame output from the previous block and returns
    an updated DataFrame. Progress is tracked in memory and can be queried by job_id.
    """

    def __init__(self):
        self._jobs: dict[str, JobProgress] = {}

    def create_job(self, workflow: list[Block]) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = JobProgress(
            job_id=job_id,
            status=JobStatus.PENDING,
            total_blocks=len(workflow),
        )
        return job_id

    def get_progress(self, job_id: str) -> JobProgress | None:
        """Get current progress for a job, or None if not found."""
        return self._jobs.get(job_id)

    async def run_workflow(
        self,
        job_id: str,
        blocks: list[Block],
    ) -> JobProgress:
        """
        Execute a workflow asynchronously.

        Args:
            job_id: Unique identifier for this job
            blocks: Ordered list of blocks to execute

        Returns:
            Final JobProgress with status and results

        Note:
            Blocks are executed sequentially with DataFrame passing between them.
            API-calling blocks (enrich_lead, find_email) parallelize row-level operations internally.
        """
        progress = self._jobs[job_id]
        progress.status = JobStatus.RUNNING
        logger.info(f"Starting workflow {job_id} with {len(blocks)} blocks")
        df: pd.DataFrame | None = None

        for i, config in enumerate(blocks):
            progress.current_block_index = i
            logger.info(f"[{job_id}] Executing block {i+1}/{len(blocks)}: {config.type}")

            block_cls = BLOCK_TYPES.get(config.type)
            if not block_cls:
                progress.status = JobStatus.FAILED
                progress.error = f"Unknown block type: {config.type}"
                logger.error(f"[{job_id}] Unknown block type: {config.type}")
                return progress

            try:
                block = block_cls()
                df, meta = await block.run(df, config)
                sample = df.head(5).to_dict("records") if df is not None and len(df) > 0 else None
                logger.info(f"[{job_id}] Block {config.type} completed: {len(df) if df is not None else 0} rows")

                progress.blocks_completed.append(
                    BlockResult(
                        block_id=config.id,
                        block_type=config.type,
                        rows_affected=len(df) if df is not None else None,
                        output_path=meta.get("output_path"),
                        sample_data=sample,
                    )
                )
            except Exception as e:
                progress.status = JobStatus.FAILED
                progress.error = str(e)
                logger.error(f"[{job_id}] Block {config.type} failed: {str(e)}")
                progress.blocks_completed.append(
                    BlockResult(block_id=config.id, block_type=config.type, error=str(e))
                )
                return progress

        progress.status = JobStatus.COMPLETED
        progress.current_block_index = len(blocks)
        logger.info(f"[{job_id}] Workflow completed successfully")
        return progress
