from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.block import Block

class Workflow(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    blocks: List[Block] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

class WorkflowCreate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    blocks: List[Block] = Field(default_factory=list)

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    blocks: Optional[List[Block]] = None