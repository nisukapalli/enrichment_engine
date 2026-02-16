from typing import Any

import httpx
import pandas as pd

from app.config import settings
from app.workflow import Block, BlockType

from .base import BlockBase


class EnrichLeadBlock(BlockBase):
    block_type = BlockType.ENRICH_LEAD

    async def run(
        self,
        df: pd.DataFrame | None,
        config: Block,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        if df is None or len(df) == 0:
            raise ValueError("enrich_lead requires a non-empty dataframe from previous block")

        # params: struct (fields to collect), optional research_plan
        struct = config.params.get("struct", {})
        if not struct:
            struct = {
                "name": "The individual's full name",
                "email": "The individual's email address",
                "company": "The company the individual is associated with",
                "title": "The individual's job title",
            }

        results = []
        async with httpx.AsyncClient(timeout=900.0) as client:
            for _, row in df.iterrows():
                lead_info = {k: v for k, v in row.items() if pd.notna(v) and v != ""}
                resp = await client.post(
                    f"{settings.URL}/enrich-lead",
                    headers={
                        "x-api-key": settings.API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "lead_info": lead_info,
                        "struct": struct,
                        **({"research_plan": config.params["research_plan"]} if config.params.get("research_plan") else {}),
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                merged = {**lead_info, **(data.get("structured_data") or {})}
                results.append(merged)

        result_df = pd.DataFrame(results)
        return result_df, {"rows": len(result_df)}
