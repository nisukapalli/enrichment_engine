import pandas as pd

from app.workflow import BlockConfig, BlockType

from .base import BlockBase, BlockContext


class FilterBlock(BlockBase):
    block_type = BlockType.FILTER

    async def run(
        self,
        df: pd.DataFrame | None,
        config: BlockConfig,
        context: BlockContext,
    ) -> tuple[pd.DataFrame, dict]:
        if df is None or len(df) == 0:
            raise ValueError("filter requires a non-empty dataframe from previous block")

        # params: expression (pandas-like, e.g. column + op + value) or custom logic
        # Simplified: support "column", "operator", "value" for common cases
        expression = config.params.get("expression")
        if expression:
            # For safety, only allow column access and simple comparisons if eval is used
            # Prefer building the mask from params to avoid eval
            result_df = df.query(expression)
        else:
            column = config.params.get("column")
            operator = config.params.get("operator", "contains")
            value = config.params.get("value")
            if not column or value is None:
                raise ValueError("filter block requires 'column' and 'value' (or 'expression') in params")

            if operator == "contains":
                result_df = df[df[column].astype(str).str.contains(str(value), na=False)]
            elif operator == "eq":
                result_df = df[df[column] == value]
            elif operator == "ne":
                result_df = df[df[column] != value]
            else:
                result_df = df[df[column].astype(str).str.contains(str(value), na=False)]

        return result_df, {"rows_before": len(df), "rows_after": len(result_df)}
