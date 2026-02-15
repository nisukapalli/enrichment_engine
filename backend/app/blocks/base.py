from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from app.workflow import BlockConfig, BlockType


class BlockContext:
    """Shared context passed through the workflow (API key, paths, etc.)."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.sixtyfour.ai",
        upload_dir: str = "uploads",
        output_dir: str = "outputs",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.upload_dir = upload_dir
        self.output_dir = output_dir


class BlockBase(ABC):
    """Base class for all workflow blocks."""

    block_type: BlockType

    @abstractmethod
    async def run(
        self,
        df: pd.DataFrame | None,
        config: BlockConfig,
        context: BlockContext,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """
        Execute the block. Returns (updated DataFrame, result metadata).
        First block may receive df=None (e.g. read_csv).
        """
        ...
