from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

class BlockType(str, Enum):
    READ_CSV = "read_csv"
    FILTER = "filter"
    ENRICH_LEAD = "enrich_lead"
    FIND_EMAIL = "find_email"
    SAVE_CSV = "save_csv"

class Block(BaseModel):
    id: str
    type: BlockType
    params: Dict[str, Any]  # block-specific parameters
    name: Optional[str] = None  # display name on UI
