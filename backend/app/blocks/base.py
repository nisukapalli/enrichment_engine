from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from app.workflow import Block, BlockType


class BlockBase(ABC):
    """Base class for all workflow blocks."""

    block_type: BlockType

    @abstractmethod
    async def run(
        self,
        df: pd.DataFrame | None,
        config: Block,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """
        Execute the block. Returns (updated DataFrame, result metadata).
        First block may receive df=None (e.g. read_csv).
        """
        ...
