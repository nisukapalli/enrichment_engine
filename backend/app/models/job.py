from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(BaseModel):
    id: str
    workflow_id: str
    status: JobStatus = JobStatus.PENDING

    total_blocks: int
    completed_blocks: int = 0
    current_block_id: Optional[str] = None
    failed_block_id: Optional[str] = None
    block_states: Dict[str, JobStatus] = Field(default_factory=dict)

    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    result_preview: Optional[Dict[str, Any]] = None
    output_path: Optional[str] = None


class JobCreate(BaseModel):
    workflow_id: str