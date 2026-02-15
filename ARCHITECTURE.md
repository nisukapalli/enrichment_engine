# Architecture & flow

## What’s implemented (roadmap)

| Layer | Implemented |
|-------|-------------|
| **Backend** | FastAPI app, config from env, CORS |
| **API** | `GET /api/workflows/blocks`, `POST /api/workflows/upload`, `POST /api/workflows/run`, `GET /api/workflows/jobs/{id}` |
| **Workflow engine** | In-memory job store, run blocks in order, pass DataFrame between blocks, background run, progress + block results |
| **Blocks** | read_csv, enrich_lead, find_email, filter, save_csv (all chainable) |
| **Frontend** | Workflow name, block palette, drag-and-drop order, per-block params, CSV upload, run button, job progress panel with sample results |

**Not implemented (per assignment):** persistent storage, auth, parallelization of Sixtyfour API calls, async Sixtyfour jobs (e.g. enrich-lead-async + polling).

---

## High-level architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Frontend (React, Vite, localhost:5173)                                  │
│  • WorkflowBuilder: blocks state, palette, upload, run                    │
│  • BlockCard (sortable): block params                                     │
│  • JobProgressPanel: poll job, show status & results                     │
│  • api.ts: fetch('/api/workflows/...')  →  proxied to backend             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    Vite proxy /api → http://127.0.0.1:8000
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI, port 8000)                                            │
│  • main.py: app, CORS, lifespan, mount router                             │
│  • workflow_routes.py: 4 endpoints, single WorkflowEngine instance       │
│  • workflow_engine.py: create_job, run_workflow, get_progress            │
│  • blocks/*: one class per block type, each returns (df, meta)            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    Sixtyfour API (enrich-lead, find-email)
```

---

## How the pieces fit together

1. **Backend**
   - **Config** (`app/config.py`): API key, base URL, CORS origins (from env).
   - **Workflow models** (`app/workflow.py`): `BlockType`, `BlockConfig`, `WorkflowDefinition`, `WorkflowRunRequest`, `JobStatus`, `BlockResult`, `JobProgress` — shared shapes for API and engine.
   - **Workflow routes** (`app/workflow_routes.py`): HTTP handlers; the only place that talks to `WorkflowEngine`. One shared `WorkflowEngine()` instance holds all jobs in memory.
   - **Workflow engine** (`app/workflow_engine.py`): Creates jobs, runs a list of `BlockConfig` in order in a background task, passes a single pandas DataFrame from block to block, and updates one `JobProgress` per job (status, current block index, list of `BlockResult` with optional sample_data).
   - **Blocks** (`app/blocks/`): Each block has a `run(df, config, context)` that returns `(new_df, meta)`. First block (e.g. read_csv) can get `df=None`; later blocks get the previous block’s DataFrame. `BlockContext` carries API key and base URL.

2. **Frontend**
   - **App.tsx**: Holds workflow state (name, blocks, uploaded file path, current job, job id). Calls `runWorkflow` then starts polling `getJobProgress(job_id)` until status is no longer running/pending.
   - **WorkflowBuilder**: Loads block types from API, manages block list (add from palette, reorder by drag, remove). Handles file input → `uploadCsv` → stores `file_path` and passes it into run. “Run workflow” calls `onRun(uploadedFilePath)`.
   - **BlockCard**: One card per block (sortable via @dnd-kit). Renders block type and `BlockParamsForm`; updates parent state when params change.
   - **BlockParamsForm**: Per-block-type inputs (file_path, filter column/operator/value, enrich struct, find_email mode, output filename).
   - **JobProgressPanel**: Shows job_id, status, blocks completed, errors, and expandable sample data from each block.
   - **api.ts**: All backend calls go through here (getBlockTypes, uploadCsv, runWorkflow, getJobProgress). Base URL is relative so Vite proxy sends them to the backend.

3. **Data flow**
   - Workflow definition lives in React state as `blocks: BlockConfig[]` (id, type, params). Same shape as backend `WorkflowDefinition.blocks`.
   - On run, frontend sends `{ workflow: { name, blocks }, input_file_path? }`. Backend can override the first block’s `file_path` with `input_file_path` if it’s read_csv.
   - Job progress is only on the backend; frontend has no workflow queue. Polling reads the same `JobProgress` object the engine updates.

---

## End-to-end workflow (user actions → backend)

### 1. Page load

- Frontend: `WorkflowBuilder` mounts → `getBlockTypes()` → `GET /api/workflows/blocks` → backend returns list of block types/labels. Used to render the “Add block” palette.

### 2. Upload CSV

- User selects file → `WorkflowBuilder` calls `uploadCsv(file)` → `POST /api/workflows/upload` (multipart).
- Backend: save file, return `{ file_path: "..." }`.
- Frontend: stores `file_path` in state and (if first block is read_csv) sets that block’s `params.file_path`.

### 3. Build workflow

- User adds blocks from palette → new `BlockConfig` (id, type, default params) appended to `blocks`.
- User drags to reorder → `onBlocksChange(arrayMove(blocks, oldIndex, newIndex))`.
- User edits params in each card → `BlockParamsForm` calls `onUpdate` → parent updates that block’s `params` in state. No API calls until Run.

### 4. Run workflow

- User clicks “Run workflow”.
- Frontend: `handleRun(uploadedFilePath)`:
  - `runWorkflow({ workflow: { name, blocks }, input_file_path: uploadedFilePath })` → `POST /api/workflows/run` with JSON body.
- Backend:
  - Validates at least one block.
  - If first block is read_csv and `input_file_path` is set, sets that block’s `params["file_path"]` to `input_file_path`.
  - `engine.create_job(blocks)` → new UUID, `JobProgress` (pending, total_blocks) stored in `engine._jobs[job_id]`.
  - `background_tasks.add_task(engine.run_workflow, job_id, blocks)` so the request returns immediately.
  - Response: `{ job_id }`.
- Frontend: saves `job_id`, then starts polling.

### 5. Background execution (engine)

- `run_workflow(job_id, blocks)`:
  - Builds `BlockContext` (API key, URL from config).
  - Sets job status to RUNNING.
  - For each block in order:
    - Looks up block class in `BLOCK_REGISTRY`, instantiates it.
    - Calls `block.run(current_df, config, context)`.
    - Appends a `BlockResult` (block_id, block_type, rows_affected, output_path if any, sample_data = first 5 rows of df) to `JobProgress.blocks_completed`.
    - On exception: sets status FAILED, appends BlockResult with error, returns.
  - When all blocks finish: sets status COMPLETED.

Data flow inside engine: `df` starts as `None`. read_csv returns a DataFrame; every later block receives that (or the previous block’s output) and returns a new DataFrame (or the same, e.g. filter returns a subset). save_csv writes to disk and still returns the same df.

### 6. Polling and display

- Frontend: every 1.5s `getJobProgress(job_id)` → `GET /api/workflows/jobs/{job_id}`.
- Backend: `engine.get_progress(job_id)` returns the `JobProgress` object (or 404).
- Frontend: `setCurrentJob(progress)`. If status is `running` or `pending`, schedules next poll; otherwise stops.
- **JobProgressPanel** shows status, block count, list of completed blocks with optional sample data and errors.

---

## Request/response summary

| Action | Frontend | HTTP | Backend |
|--------|----------|------|--------|
| Load block types | `getBlockTypes()` | GET /api/workflows/blocks | List block types + param hints |
| Upload CSV | `uploadCsv(file)` | POST /api/workflows/upload (form) | Save file, return file_path |
| Run workflow | `runWorkflow({ workflow, input_file_path })` | POST /api/workflows/run (JSON) | create_job, run_workflow in background, return job_id |
| Poll progress | `getJobProgress(jobId)` | GET /api/workflows/jobs/:id | Return JobProgress for that job |

---

## File layout (reference)

```
backend/
  app/
    main.py              # FastAPI app, CORS, lifespan, include_router
    config.py            # Settings (API_KEY, URL, CORS_ORIGINS)
    workflow.py          # BlockType, BlockConfig, WorkflowDefinition, WorkflowRunRequest, JobProgress, BlockResult
    workflow_routes.py   # GET blocks, POST upload, POST run, GET jobs/:id
    workflow_engine.py   # WorkflowEngine, BLOCK_REGISTRY, run_workflow loop
    blocks/
      base.py            # BlockContext, BlockBase.run(df, config, context)
      read_csv.py        # ReadCsvBlock
      enrich_lead.py     # EnrichLeadBlock (Sixtyfour API)
      find_email.py      # FindEmailBlock (Sixtyfour API)
      filter_block.py   # FilterBlock
      save_csv.py       # SaveCsvBlock

frontend/
  src/
    App.tsx              # workflow state, handleRun, polling, layout
    api.ts               # getBlockTypes, uploadCsv, runWorkflow, getJobProgress
    types.ts             # BlockConfig, WorkflowDefinition, JobProgress, etc.
    components/
      WorkflowBuilder.tsx  # palette, blocks list (sortable), upload, run button
      BlockCard.tsx       # single block UI, params form, remove
      BlockParamsForm.tsx # per-type fields (file_path, filter, struct, mode, output_filename)
      JobProgressPanel.tsx # job status, blocks completed, sample data
```

This is the architecture and flow of what’s implemented end to end.
