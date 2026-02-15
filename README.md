# Sixtyfour Workflow Engine

A simplified replica of Sixtyfour's Workflow Engine: configure and run workflows built from chainable blocks (Read CSV, Enrich Lead, Find Email, Filter, Save CSV). Built with **Python (FastAPI)** and **React**.

## Quick start

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

## Project layout

- **backend/** – FastAPI app
  - `app/main.py` – app entry, CORS, router
  - `app/workflow_routes.py` – workflows API (blocks, upload, run, job status)
  - `app/workflow.py` – Pydantic models (BlockType, Workflow, WorkflowExecution, JobProgress, etc.)
  - `app/workflow_engine.py` – runs blocks in order, keeps job progress
  - `app/blocks/` – block implementations (read_csv, enrich_lead, find_email, filter, save_csv)
  - `app/config.py` – settings (API key, CORS)

- **frontend/** – React (Vite + TypeScript)
  - `src/App.tsx` – layout, workflow state, run + job progress
  - `src/components/WorkflowBuilder.tsx` – drag-and-drop block list, palette, upload, run
  - `src/components/BlockCard.tsx` – sortable block card + params form
  - `src/components/BlockParamsForm.tsx` – per-block parameter inputs
  - `src/components/JobProgressPanel.tsx` – job status and block results
  - `src/api.ts` – client for backend workflows API

## Features (scaffolding)

- **Backend**: Five block types (Read CSV, Enrich Lead, Find Email, Filter, Save CSV), chainable in any order; CSV upload; workflow run with background execution; job progress polling.
- **Frontend**: Add blocks from palette; drag-and-drop reorder; configure parameters per block; upload CSV; run workflow; see job progress and sample results.

## Environment

- `API_KEY` – from https://app.sixtyfour.ai (required for Enrich Lead and Find Email).

## Example workflows

1. **Basic**: Read CSV → Enrich Lead → Save CSV  
2. **Filtered**: Read CSV → Filter (e.g. company contains "Ariglad Inc") → Enrich Lead → Filter (e.g. is_american_education = true) → Save CSV  

Use the sample CSV from the take-home PDF for testing.



## Testing the backend

**1. Start the server** (from project root or `backend/`):

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**2. Use the interactive API docs**

Open **http://127.0.0.1:8000/docs**. You can:

- **GET /** – health check (should return `{"message": "Sixtyfour Workflow Engine API", "docs": "/docs"}`).
- **GET /api/workflows/blocks** – list block types (no body).
- **POST /api/workflows/upload** – upload a CSV (use the "Choose File" in the request body, pick e.g. `sample_data.csv` from the repo), then copy the returned `file_path`.
- **POST /api/workflows/run** – run a workflow. Example body (replace `YOUR_FILE_PATH` with the value from upload):

```json
{
  "workflow": {
    "name": "Test",
    "blocks": [
      { "id": "1", "type": "read_csv", "params": { "file_path": "YOUR_FILE_PATH" } },
      { "id": "2", "type": "save_csv", "params": { "output_filename": "out.csv" } }
    ]
  },
  "input_file_path": "YOUR_FILE_PATH"
}
```

- **GET /api/workflows/jobs/{job_id}** – paste the `job_id` from the run response and check status and `blocks_completed`.

**3. Quick curl checks** (with server running)

```bash
# Health
curl -s http://127.0.0.1:8000/

# Block types
curl -s http://127.0.0.1:8000/api/workflows/blocks

# Upload (from repo root; adjust path to your CSV)
curl -s -X POST http://127.0.0.1:8000/api/workflows/upload -F "file=@sample_data.csv"
# Use the returned file_path in the next request.

# Run workflow (replace FILE_PATH with upload response)
curl -s -X POST http://127.0.0.1:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"workflow":{"name":"Test","blocks":[{"id":"1","type":"read_csv","params":{"file_path":"FILE_PATH"}},{"id":"2","type":"save_csv","params":{"output_filename":"out.csv"}}]},"input_file_path":"FILE_PATH"}'
# Then: curl -s http://127.0.0.1:8000/api/workflows/jobs/JOB_ID
```
