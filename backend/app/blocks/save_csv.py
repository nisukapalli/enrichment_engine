import os

import pandas as pd

from app.workflow import Block, BlockType

from .base import BlockBase


class SaveCsvBlock(BlockBase):
    """
    Saves the current DataFrame to a CSV file.

    Params:
        output_filename: Name of output file (saved to outputs/ directory)
    """

    block_type = BlockType.SAVE_CSV

    async def run(
        self,
        df: pd.DataFrame | None,
        config: Block,
    ) -> tuple[pd.DataFrame, dict]:
        if df is None or len(df) == 0:
            raise ValueError("save_csv requires a non-empty dataframe from previous block")

        output_filename = config.params.get("output_filename", "output.csv")

        # Ensure outputs directory exists
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)

        # If relative path, save to outputs/ directory
        if not os.path.isabs(output_filename):
            full_path = os.path.join(output_dir, output_filename)
        else:
            full_path = output_filename

        df.to_csv(full_path, index=False)
        return df, {"output_path": full_path, "rows": len(df)}
