import asyncio
import httpx
from typing import Any, Dict, Optional
from app.config import API_KEY, URL

_POLL_INTERVAL = 10  # seconds between status checks
_POLL_TIMEOUT = 1200  # 20 minutes max wait

# Shared async HTTP client — reuses the connection pool across all API calls.
# Only the auth header is set at the client level; Content-Type is handled
# automatically by httpx when json= is passed to a request.
_client = httpx.AsyncClient(
    headers={"x-api-key": API_KEY},
    timeout=30,
)


async def enrich_lead_async(
    lead_info: Dict[str, Any],
    struct: Dict[str, Any],
    research_plan: Optional[str] = None,
) -> str:
    """Submit an async enrich-lead job. Returns the task_id."""
    body: Dict[str, Any] = {"lead_info": lead_info, "struct": struct}
    if research_plan:
        body["research_plan"] = research_plan

    response = await _client.post(f"{URL}/enrich-lead-async", json=body)
    response.raise_for_status()
    return response.json()["task_id"]


async def poll_job_status(task_id: str) -> Dict[str, Any]:
    """Poll until the job is completed or failed. Returns the result dict."""
    elapsed = 0
    while elapsed < _POLL_TIMEOUT:
        response = await _client.get(f"{URL}/job-status/{task_id}")
        response.raise_for_status()
        data = response.json()

        if data["status"] == "completed":
            return data["result"]
        if data["status"] == "failed":
            raise RuntimeError(
                f"Enrich-lead job {task_id} failed: {data.get('error', 'unknown error')}"
            )

        await asyncio.sleep(_POLL_INTERVAL)
        elapsed += _POLL_INTERVAL

    raise TimeoutError(f"Enrich-lead job {task_id} did not complete within {_POLL_TIMEOUT}s")


async def find_email(
    lead: Dict[str, Any],
    mode: str = "PROFESSIONAL",
) -> Dict[str, Any]:
    """Find email(s) for a lead. Returns the full response dict."""
    response = await _client.post(
        f"{URL}/find-email",
        json={"lead": lead, "mode": mode},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


async def close() -> None:
    """Close the shared HTTP client. Call this on application shutdown."""
    await _client.aclose()
