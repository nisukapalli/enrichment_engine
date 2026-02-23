import asyncio
import os
import pandas as pd
from typing import Any, Dict

from app.models.block import (
    ReadCsvBlock,
    FilterBlock,
    FilterOperator,
    EnrichLeadBlock,
    FindEmailBlock,
    SaveCsvBlock,
)
from app.config import MAX_CONCURRENT_API_CALLS
from app.services import sixtyfour_client

_UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
_OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "outputs")


# ---------------------------------------------------------------------------
# Simple (non-API) runners
# ---------------------------------------------------------------------------

def run_read_csv(block: ReadCsvBlock) -> pd.DataFrame:
    filename = os.path.basename(block.params.path)
    if not filename:
        raise ValueError(f"Invalid path in read_csv block: '{block.params.path}'")
    path = os.path.join(_UPLOADS_DIR, filename)
    return pd.read_csv(path)


def run_filter(block: FilterBlock, df: pd.DataFrame) -> pd.DataFrame:
    col = block.params.column
    op = block.params.operator
    val = block.params.value

    # Coerce value to numeric for comparison operators
    numeric_val: Any = val
    if op in (FilterOperator.GT, FilterOperator.GTE, FilterOperator.LT, FilterOperator.LTE):
        try:
            numeric_val = float(val)
        except ValueError:
            raise ValueError(
                f"Filter operator '{op.value}' requires a numeric value, got '{val}'"
            )

    if op == FilterOperator.CONTAINS:
        mask = df[col].astype(str).str.contains(val, na=False)
    elif op == FilterOperator.NOT_CONTAINS:
        mask = ~df[col].astype(str).str.contains(val, na=False)
    elif op == FilterOperator.EQUALS:
        try:
            mask = df[col] == float(val)
        except ValueError:
            mask = df[col] == val
    elif op == FilterOperator.NOT_EQUALS:
        try:
            mask = df[col] != float(val)
        except ValueError:
            mask = df[col] != val
    elif op == FilterOperator.GT:
        mask = pd.to_numeric(df[col], errors="coerce") > numeric_val
    elif op == FilterOperator.GTE:
        mask = pd.to_numeric(df[col], errors="coerce") >= numeric_val
    elif op == FilterOperator.LT:
        mask = pd.to_numeric(df[col], errors="coerce") < numeric_val
    elif op == FilterOperator.LTE:
        mask = pd.to_numeric(df[col], errors="coerce") <= numeric_val
    else:
        raise ValueError(f"Unknown filter operator: {op}")

    return df[mask].reset_index(drop=True)


def run_save_csv(block: SaveCsvBlock, df: pd.DataFrame) -> pd.DataFrame:
    filename = os.path.basename(block.params.path)
    if not filename:
        raise ValueError(f"Invalid path in save_csv block: '{block.params.path}'")
    os.makedirs(_OUTPUTS_DIR, exist_ok=True)
    path = os.path.join(_OUTPUTS_DIR, filename)
    df.to_csv(path, index=False)
    return df


# ---------------------------------------------------------------------------
# API runners
# ---------------------------------------------------------------------------

async def run_enrich_lead(block: EnrichLeadBlock, df: pd.DataFrame) -> pd.DataFrame:
    """
    Submit all rows as concurrent enrich-lead jobs, then collect results.
    Submissions are rate-limited by MAX_CONCURRENT_API_CALLS; polling is
    uncapped because it's just lightweight GET requests every 10 seconds.
    The returned struct fields are merged as new columns onto the dataframe.
    """
    sem = asyncio.Semaphore(MAX_CONCURRENT_API_CALLS)

    async def _enrich_one(row: pd.Series) -> Dict[str, Any]:
        lead_info = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
        async with sem:
            task_id = await sixtyfour_client.enrich_lead_async(
                lead_info=lead_info,
                struct=block.params.struct,
                research_plan=block.params.research_plan,
            )
        return await sixtyfour_client.poll_job_status(task_id)

    results = await asyncio.gather(*[_enrich_one(row) for _, row in df.iterrows()])

    enriched_df = df.copy()
    for key in block.params.struct:
        enriched_df[key] = [r.get(key) for r in results]

    return enriched_df


async def run_find_email(block: FindEmailBlock, df: pd.DataFrame) -> pd.DataFrame:
    """
    Submit all rows as concurrent find-email requests, then collect results.
    Requests are rate-limited by MAX_CONCURRENT_API_CALLS.
    Adds a 'found_email' column to the dataframe.
    """
    sem = asyncio.Semaphore(MAX_CONCURRENT_API_CALLS)

    async def _find_one(row: pd.Series) -> Any:
        lead = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
        async with sem:
            response = await sixtyfour_client.find_email(
                lead=lead,
                mode=block.params.mode.value,
            )
        return response.get("email")

    found_emails = await asyncio.gather(*[_find_one(row) for _, row in df.iterrows()])

    result_df = df.copy()
    result_df["found_email"] = list(found_emails)
    return result_df
