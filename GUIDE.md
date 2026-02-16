# Sixtyfour Workflow Engine - Codebase Guide

## Overview

A simplified replica of Sixtyfour's Workflow Engine for a fullstack engineer take-home assignment. Users can configure and execute workflows made up of modular, chainable blocks.

## Architecture

### Backend (`/backend/app/`)

#### Core Models (`workflow.py`)
- **BlockType**: Enum of 5 block types (READ_CSV, ENRICH_LEAD, FIND_EMAIL, FILTER, SAVE_CSV)
- **Block**: Block configuration (id, type, params)
- **Workflow**: Collection of blocks with a name
- **WorkflowExecution**: Request body for running a workflow
- **JobStatus**: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
- **BlockResult**: Result from a single block execution
- **JobProgress**: Full job state with status, current block, and results

#### Workflow Engine (`workflow_engine.py`)
- **In-memory job store**: `_jobs: dict[str, JobProgress]`
- **Block registry**: Maps BlockType → Block class
- **Execution model**: Sequential block execution, DataFrame passed between blocks
- **Logging**: Structured logs for job lifecycle and block execution

#### Blocks (`blocks/`)
All blocks inherit from `BlockBase` with async `run(df, config) → (DataFrame, metadata)` signature.

**ReadCsvBlock**:
- Loads CSV from `backend/uploads/` (or absolute path)
- Returns DataFrame with row/column metadata

**FilterBlock**:
- Filters DataFrame by expression (pandas query) or column/operator/value
- Returns filtered DataFrame with before/after row counts

**EnrichLeadBlock**:
- Calls `/enrich-lead` API for each row
- Currently sequential (room for optimization)
- Returns enriched DataFrame

**FindEmailBlock**:
- Calls `/find-email` API for each row
- Currently sequential (room for optimization)
- Returns DataFrame with email columns added

**SaveCsvBlock**:
- Saves DataFrame to `backend/outputs/`
- Returns same DataFrame with output path

#### API Routes (`workflow_routes.py`)
- **GET `/api/workflows/blocks`**: Returns available block types and param schemas
- **POST `/api/workflows/upload`**: Upload CSV file, returns file_path
- **POST `/api/workflows/run`**: Create and execute workflow, returns job_id
- **GET `/api/workflows/jobs/{job_id}`**: Poll job progress

#### Configuration (`config.py`)
- Loads API_KEY and URL from .env via Pydantic Settings
- Validates API_KEY is required
- CORS configured for React dev server

### Frontend (`/frontend/src/`)

#### Types (`types.ts`)
- TypeScript interfaces matching backend models
- BlockType, Block, Workflow, WorkflowExecution
- JobStatus, JobProgress, BlockResult

#### Components (To Be Implemented)
- **App.tsx**: Main component managing workflow state
- **WorkflowBuilder.tsx**: Canvas for building workflows
- **BlockPalette.tsx**: Block selector
- **BlockCard.tsx**: Visual block representation
- **BlockParamsForm.tsx**: Block parameter editing
- **JobProgressPanel.tsx**: Display job progress and results

## Key Design Decisions

### 1. DataFrame as Contract
Using pandas DataFrame as the data contract between blocks makes transforms composable and testable. Each block is a pure function: DataFrame in → DataFrame out.

### 2. In-Memory Job Store
Jobs are stored in memory (`_jobs` dict) for simplicity. Lost on restart, but sufficient for demo. Production would use SQLite/Redis/database.

### 3. Sequential Execution
Blocks execute sequentially in order. The workflow engine passes the DataFrame output from one block as input to the next.

### 4. Async API Calls
EnrichLeadBlock and FindEmailBlock currently call APIs sequentially for each row. **Major optimization opportunity**: parallelize with `asyncio.gather()` and add rate limiting with semaphores.

### 5. No Persistent Storage
Per spec, using local file system for uploads/outputs. No database required.

## Performance Considerations (Interview Discussion)

### Current Bottlenecks
1. **API blocks are sequential**: EnrichLead and FindEmail process rows one-by-one
2. **No rate limiting**: Could overwhelm API or hit rate limits
3. **No partial failure handling**: One failed row fails entire job
4. **No progress tracking**: Can't see progress within a block

### Optimization Strategies

**Parallelization** (most important):
```python
# Use asyncio.gather() to parallelize API calls
tasks = [enrich_row(row) for row in df.iterrows()]
results = await asyncio.gather(*tasks)
```

**Rate Limiting**:
```python
# Use semaphore to limit concurrent requests
semaphore = asyncio.Semaphore(10)  # Max 10 concurrent
async with semaphore:
    # make API call
```

**Partial Failure Handling**:
- Mark failed rows with `_error` field instead of failing entire job
- Return error metadata in BlockResult

**Row-Level Progress**:
- Add progress callback to blocks
- Update `JobProgress.current_block_progress` field

## File Structure

```
sixtyfour/
├── backend/
│   ├── app/
│   │   ├── blocks/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── read_csv.py
│   │   │   ├── filter_block.py
│   │   │   ├── enrich_lead.py
│   │   │   ├── find_email.py
│   │   │   └── save_csv.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── workflow.py
│   │   ├── workflow_engine.py
│   │   └── workflow_routes.py
│   ├── uploads/           # User-uploaded CSVs
│   ├── outputs/           # Workflow results
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── App.tsx
│   └── package.json
└── .gitignore
```

## Development Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your API_KEY
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Testing Workflow

1. Upload CSV via `/api/workflows/upload`
2. Build workflow in frontend (or POST directly to `/api/workflows/run`)
3. Poll `/api/workflows/jobs/{job_id}` until status = "completed"
4. View results in sample_data or download from output_path

## What's NOT Implemented Yet

- [ ] Block param validation (server-side)
- [ ] JSON Schema generation for block params
- [ ] Parallelized API calls in enrich/find_email blocks
- [ ] Partial failure handling
- [ ] Row-level progress tracking
- [ ] Frontend UI implementation
- [ ] Job persistence (survives restart)
- [ ] Unit tests

## Interview Talking Points

### "How would you make API calls faster?"
- Parallelize with `asyncio.gather()`
- Add semaphore for rate limiting
- Consider batching if API supports it
- Cache frequently enriched entities

### "How would you scale to thousands of rows?"
- Chunk processing (process 100 rows at a time)
- Background job queue (Celery/RQ) instead of BackgroundTasks
- Database persistence for job state
- Consider message queue for block-to-block communication

### "How would you handle partial failures?"
- Graceful error handling per row
- Mark failed rows with `_error` field
- Return error summary in metadata
- Option to retry failed rows

### "How would you prevent incompatible blocks?"
- Define output schema for each block type
- Validate input requirements before execution
- Type system for DataFrame schemas (e.g., Pandera)
- Frontend validation in workflow builder

### "What would you change for production?"
- Job persistence (SQLite/PostgreSQL/Redis)
- Distributed task queue (Celery with Redis)
- Object storage for CSVs (S3/GCS)
- Monitoring and alerting (DataDog/Prometheus)
- Authentication and multi-tenancy
- API versioning
- Comprehensive logging and tracing
