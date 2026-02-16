import os

import pandas as pd

from app.workflow import Block, BlockType

from .base import BlockBase


class ReadCsvBlock(BlockBase):
    """
    Reads a CSV file into a DataFrame.

    Params:
        file_path: Path to CSV file (relative to uploads/ or absolute path)
    """

    block_type = BlockType.READ_CSV

    async def run(
        self,
        df: pd.DataFrame | None,
        config: Block,
    ) -> tuple[pd.DataFrame, dict]:
        file_path = config.params.get("file_path", "")
        if not file_path:
            raise ValueError("read_csv block requires 'file_path' in params")

        # If relative path, assume it's in uploads/ directory
        if not os.path.isabs(file_path):
            file_path = os.path.join("uploads", file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        result_df = pd.read_csv(file_path)
        return result_df, {"rows": len(result_df), "columns": list(result_df.columns)}
