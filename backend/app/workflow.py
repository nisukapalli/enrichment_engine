from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BlockType(str, Enum):
    READ_CSV = "read_csv"
    ENRICH_LEAD = "enrich_lead"
    FIND_EMAIL = "find_email"
    FILTER = "filter"
    SAVE_CSV = "save_csv"


class BlockConfig(BaseModel):
    """Configuration for a single block in a workflow."""

    id: str
    type: BlockType
    params: dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    """Ordered list of blocks that form a workflow."""

    name: str = "Untitled Workflow"
    blocks: list[BlockConfig] = Field(default_factory=list)


class WorkflowRunRequest(BaseModel):
    """Request to run a workflow (workflow def + optional input file)."""

    workflow: WorkflowDefinition
    input_file_path: str | None = None  # For read_csv; can be set when uploading


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BlockResult(BaseModel):
    """Result from executing a single block."""

    block_id: str
    block_type: BlockType
    rows_affected: int | None = None
    output_path: str | None = None
    error: str | None = None
    sample_data: list[dict[str, Any]] | None = None


class JobProgress(BaseModel):
    """Progress of a running or completed job."""

    job_id: str
    status: JobStatus
    current_block_index: int = 0
    total_blocks: int = 0
    blocks_completed: list[BlockResult] = Field(default_factory=list)
    error: str | None = None
