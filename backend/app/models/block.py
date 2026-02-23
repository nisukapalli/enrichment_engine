from enum import Enum
from typing import Annotated, Any, Dict, Literal, Optional, Union
from pydantic import BaseModel, Field


class BlockType(str, Enum):
    READ_CSV = "read_csv"
    FILTER = "filter"
    ENRICH_LEAD = "enrich_lead"
    FIND_EMAIL = "find_email"
    SAVE_CSV = "save_csv"



class ReadCsvParams(BaseModel):
    path: str


class FilterOperator(str, Enum):
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"


class FilterParams(BaseModel):
    column: str
    operator: FilterOperator
    value: str


class EnrichLeadParams(BaseModel):
    struct: Dict[str, Any]  # fields to collect, e.g. {"university": "undergrad university"}
    research_plan: Optional[str] = None


class FindEmailMode(str, Enum):
    PROFESSIONAL = "PROFESSIONAL"
    PERSONAL = "PERSONAL"


class FindEmailParams(BaseModel):
    mode: FindEmailMode = FindEmailMode.PROFESSIONAL


class SaveCsvParams(BaseModel):
    path: str



class ReadCsvBlockCreate(BaseModel):
    type: Literal[BlockType.READ_CSV]
    params: ReadCsvParams
    name: Optional[str] = None


class FilterBlockCreate(BaseModel):
    type: Literal[BlockType.FILTER]
    params: FilterParams
    name: Optional[str] = None


class EnrichLeadBlockCreate(BaseModel):
    type: Literal[BlockType.ENRICH_LEAD]
    params: EnrichLeadParams
    name: Optional[str] = None


class FindEmailBlockCreate(BaseModel):
    type: Literal[BlockType.FIND_EMAIL]
    params: FindEmailParams
    name: Optional[str] = None


class SaveCsvBlockCreate(BaseModel):
    type: Literal[BlockType.SAVE_CSV]
    params: SaveCsvParams
    name: Optional[str] = None


BlockCreate = Annotated[
    Union[
        ReadCsvBlockCreate,
        FilterBlockCreate,
        EnrichLeadBlockCreate,
        FindEmailBlockCreate,
        SaveCsvBlockCreate,
    ],
    Field(discriminator="type"),
]



class ReadCsvBlock(ReadCsvBlockCreate):
    id: str


class FilterBlock(FilterBlockCreate):
    id: str


class EnrichLeadBlock(EnrichLeadBlockCreate):
    id: str


class FindEmailBlock(FindEmailBlockCreate):
    id: str


class SaveCsvBlock(SaveCsvBlockCreate):
    id: str


Block = Annotated[
    Union[
        ReadCsvBlock,
        FilterBlock,
        EnrichLeadBlock,
        FindEmailBlock,
        SaveCsvBlock,
    ],
    Field(discriminator="type"),
]
