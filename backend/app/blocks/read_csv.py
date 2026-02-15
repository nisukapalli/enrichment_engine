import pandas as pd

from app.workflow import BlockConfig, BlockType

from .base import BlockBase, BlockContext


class ReadCsvBlock(BlockBase):
    block_type = BlockType.READ_CSV

    async def run(
        self,
        df: pd.DataFrame | None,
        config: BlockConfig,
        context: BlockContext,
    ) -> tuple[pd.DataFrame, dict]:
        # params: file_path (relative to upload_dir or absolute)
        file_path = config.params.get("file_path", "")
        if not file_path:
            raise ValueError("read_csv block requires 'file_path' in params")

        full_path = file_path if file_path.startswith("/") else f"{context.upload_dir}/{file_path}"
        result_df = pd.read_csv(full_path)
        return result_df, {"rows": len(result_df), "columns": list(result_df.columns)}
