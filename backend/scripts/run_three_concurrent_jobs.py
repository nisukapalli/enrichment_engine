#!/usr/bin/env python3
"""
Create 3 complex workflows using backend/uploads/sample.csv and start 3 jobs
simultaneously to test concurrency. Run with backend server up:

  cd backend && python scripts/run_three_concurrent_jobs.py

Uses sample.csv columns: name, company, email, company_location, linkedin
"""

import sys
import urllib.request
import json

BASE = "http://127.0.0.1:8000"


def request(method: str, path: str, body: dict | None = None) -> dict:
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode()) if r.length else {}


# ── 3 complex workflows (all use sample.csv) ─────────────────────────────────

WORKFLOW_1 = {
    "name": "Concurrent Test 1: US leads → enrich + email",
    "blocks": [
        {"type": "read_csv", "params": {"path": "sample.csv"}},
        {
            "type": "filter",
            "params": {
                "column": "company_location",
                "operator": "contains",
                "value": "United States",
            },
        },
        {
            "type": "enrich_lead",
            "params": {
                "struct": {
                    "college": "the college they attended",
                    "title": "current job title",
                },
                "research_plan": "Check their LinkedIn profile for education and role.",
            },
        },
        {"type": "find_email", "params": {"mode": "PROFESSIONAL"}},
        {"type": "save_csv", "params": {"path": "concurrent_1_us_enriched.csv"}},
    ],
}

WORKFLOW_2 = {
    "name": "Concurrent Test 2: Canada leads → enrich + personal email",
    "blocks": [
        {"type": "read_csv", "params": {"path": "sample.csv"}},
        {
            "type": "filter",
            "params": {
                "column": "company_location",
                "operator": "contains",
                "value": "Canada",
            },
        },
        {
            "type": "enrich_lead",
            "params": {
                "struct": {
                    "industry": "industry or sector",
                    "title": "job title",
                },
            },
        },
        {"type": "find_email", "params": {"mode": "PERSONAL"}},
        {"type": "save_csv", "params": {"path": "concurrent_2_canada_enriched.csv"}},
    ],
}

WORKFLOW_3 = {
    "name": "Concurrent Test 3: Full pipeline (no filter)",
    "blocks": [
        {"type": "read_csv", "params": {"path": "sample.csv"}},
        {
            "type": "enrich_lead",
            "params": {
                "struct": {
                    "college": "college or university attended",
                    "title": "current job title",
                    "industry": "industry",
                },
                "research_plan": "Focus on LinkedIn education and experience.",
            },
        },
        {"type": "find_email", "params": {"mode": "PROFESSIONAL"}},
        {"type": "save_csv", "params": {"path": "concurrent_3_full_enriched.csv"}},
    ],
}


def main() -> None:
    print("Creating 3 workflows...")
    w1 = request("POST", "/workflows", WORKFLOW_1)
    w2 = request("POST", "/workflows", WORKFLOW_2)
    w3 = request("POST", "/workflows", WORKFLOW_3)
    print(f"  Created: {w1['name']} ({w1['id'][:8]}...)")
    print(f"  Created: {w2['name']} ({w2['id'][:8]}...)")
    print(f"  Created: {w3['name']} ({w3['id'][:8]}...)")

    print("\nStarting 3 jobs simultaneously (concurrency test)...")
    j1 = request("POST", "/jobs", {"workflow_id": w1["id"]})
    j2 = request("POST", "/jobs", {"workflow_id": w2["id"]})
    j3 = request("POST", "/jobs", {"workflow_id": w3["id"]})
    print(f"  Job 1: {j1['id'][:8]}... (workflow {w1['name'][:30]}...)")
    print(f"  Job 2: {j2['id'][:8]}... (workflow {w2['name'][:30]}...)")
    print(f"  Job 3: {j3['id'][:8]}... (workflow {w3['name'][:30]}...)")

    print("\nDone. Open the Jobs page to watch all 3 run concurrently.")
    print(f"  Jobs: {BASE.replace('127.0.0.1', 'localhost')}/docs → or use frontend at http://localhost:5173/jobs")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as e:
        print(f"Error: Is the backend running? {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
