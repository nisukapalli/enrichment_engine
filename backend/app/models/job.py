from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Job(BaseModel):
    id: str
    workflow_id: str
    status: JobStatus

    total_blocks: int
    completed_blocks: int
    current_block_id: Optional[str] = None
    failed_block_id: Optional[str] = None
    block_states: Optional[Dict[str, JobStatus]] = None

    created_at: datetime
    started_at: datetime
    finished_at: datetime

    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    output_path: Optional[str] = None