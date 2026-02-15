"""Workflow block implementations. Each block receives a DataFrame and optional context, returns updated DataFrame."""

from .base import BlockBase, BlockContext
from .enrich_lead import EnrichLeadBlock
from .filter_block import FilterBlock
from .find_email import FindEmailBlock
from .read_csv import ReadCsvBlock
from .save_csv import SaveCsvBlock

__all__ = [
    "BlockBase",
    "BlockContext",
    "EnrichLeadBlock",
    "FilterBlock",
    "FindEmailBlock",
    "ReadCsvBlock",
    "SaveCsvBlock",
]
