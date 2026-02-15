import os
from pathlib import Path

import pandas as pd

from app.workflow import BlockConfig, BlockType

from .base import BlockBase, BlockContext


class SaveCsvBlock(BlockBase):
    block_type = BlockType.SAVE_CSV

    async def run(
        self,
        df: pd.DataFrame | None,
        config: BlockConfig,
        context: BlockContext,
    ) -> tuple[pd.DataFrame, dict]:
        if df is None or len(df) == 0:
            raise ValueError("save_csv requires a non-empty dataframe from previous block")

        output_filename = config.params.get("output_filename", "output.csv")
        Path(context.output_dir).mkdir(parents=True, exist_ok=True)
        full_path = os.path.join(context.output_dir, output_filename)
        df.to_csv(full_path, index=False)
        return df, {"output_path": full_path, "rows": len(df)}
