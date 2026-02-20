from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from .block import Block

class Workflow(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    blocks: List[Block] = []

    created_at: datetime
    updated_at: datetime