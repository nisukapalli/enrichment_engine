"""
Workflow execution engine. Runs a list of blocks in order, passing DataFrame between them.
Supports async execution and progress reporting.
"""

import uuid
from typing import Any

import pandas as pd

from app.blocks import (
    EnrichLeadBlock,
    FilterBlock,
    FindEmailBlock,
    ReadCsvBlock,
    SaveCsvBlock,
)
from app.blocks.base import BlockContext
from app.config import settings
from app.workflow import (
    BlockConfig,
    BlockResult,
    BlockType,
    JobProgress,
    JobStatus,
)

# Registry of block type -> block class
BLOCK_REGISTRY: dict[BlockType, type] = {
    BlockType.READ_CSV: ReadCsvBlock,
    BlockType.ENRICH_LEAD: EnrichLeadBlock,
    BlockType.FIND_EMAIL: FindEmailBlock,
    BlockType.FILTER: FilterBlock,
    BlockType.SAVE_CSV: SaveCsvBlock,
}


class WorkflowEngine:
    def __init__(self):
        self._jobs: dict[str, JobProgress] = {}

    def create_job(self, workflow: list[BlockConfig]) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = JobProgress(
            job_id=job_id,
            status=JobStatus.PENDING,
            total_blocks=len(workflow),
        )
        return job_id

    def get_progress(self, job_id: str) -> JobProgress | None:
        return self._jobs.get(job_id)

    async def run_workflow(
        self,
        job_id: str,
        blocks: list[BlockConfig],
        context_overrides: dict[str, Any] | None = None,
    ) -> JobProgress:
        context = BlockContext(
            api_key=context_overrides.get("api_key", "") or settings.API_KEY,
            base_url=settings.URL,
        )
        progress = self._jobs[job_id]
        progress.status = JobStatus.RUNNING
        df: pd.DataFrame | None = None

        for i, config in enumerate(blocks):
            progress.current_block_index = i
            block_cls = BLOCK_REGISTRY.get(config.type)
            if not block_cls:
                progress.status = JobStatus.FAILED
                progress.error = f"Unknown block type: {config.type}"
                return progress

            try:
                block = block_cls()
                df, meta = await block.run(df, config, context)
                sample = df.head(5).to_dict("records") if df is not None and len(df) > 0 else None
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
                progress.blocks_completed.append(
                    BlockResult(block_id=config.id, block_type=config.type, error=str(e))
                )
                return progress

        progress.status = JobStatus.COMPLETED
        progress.current_block_index = len(blocks)
        return progress
