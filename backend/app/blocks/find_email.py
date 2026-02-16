from typing import Any

import httpx
import pandas as pd

from app.config import settings
from app.workflow import Block, BlockType

from .base import BlockBase


class FindEmailBlock(BlockBase):
    block_type = BlockType.FIND_EMAIL

    async def run(
        self,
        df: pd.DataFrame | None,
        config: Block,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        if df is None or len(df) == 0:
            raise ValueError("find_email requires a non-empty dataframe from previous block")

        mode = config.params.get("mode", "PROFESSIONAL")

        results = []
        async with httpx.AsyncClient(timeout=120.0) as client:
            for _, row in df.iterrows():
                lead = {k: v for k, v in row.items() if pd.notna(v) and v != ""}
                resp = await client.post(
                    f"{settings.URL}/find-email",
                    headers={
                        "x-api-key": settings.API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={"lead": lead, "mode": mode},
                )
                resp.raise_for_status()
                data = resp.json()
                # Flatten email result into row
                row_dict = dict(row)
                if "email" in data and data["email"]:
                    row_dict["email"] = data["email"][0][0] if isinstance(data["email"][0], (list, tuple)) else data["email"]
                if "personal_email" in data and data["personal_email"]:
                    row_dict["personal_email"] = data["personal_email"][0][0] if isinstance(data["personal_email"][0], (list, tuple)) else data["personal_email"]
                results.append(row_dict)

        result_df = pd.DataFrame(results)
        return result_df, {"rows": len(result_df)}
