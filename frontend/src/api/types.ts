// ── Block types ────────────────────────────────────────────────────────────

export type BlockType =
  | 'read_csv'
  | 'filter'
  | 'enrich_lead'
  | 'find_email'
  | 'save_csv'

export interface ReadCsvBlock {
  id?: string
  type: 'read_csv'
  params: { path: string }
}

export interface FilterBlock {
  id?: string
  type: 'filter'
  params: {
    column: string
    operator: 'contains' | 'equals' | 'not_equals' | 'gt' | 'lt' | 'gte' | 'lte'
    value: string
  }
}

export interface EnrichLeadBlock {
  id?: string
  type: 'enrich_lead'
  params: {
    struct: Record<string, string>
    research_plan?: string
  }
}

export interface FindEmailBlock {
  id?: string
  type: 'find_email'
  params: { mode: 'PROFESSIONAL' | 'PERSONAL' }
}

export interface SaveCsvBlock {
  id?: string
  type: 'save_csv'
  params: { path: string }
}

export type Block =
  | ReadCsvBlock
  | FilterBlock
  | EnrichLeadBlock
  | FindEmailBlock
  | SaveCsvBlock

// ── Workflow ───────────────────────────────────────────────────────────────

export interface Workflow {
  id: string
  name: string
  blocks: Block[]
  created_at: string
  updated_at: string
}

export interface WorkflowCreate {
  name?: string
  blocks: Block[]
}

export interface WorkflowUpdate {
  name?: string
  blocks?: Block[]
}

// ── Job ────────────────────────────────────────────────────────────────────

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type BlockStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'cancelled'

export interface Job {
  id: string
  workflow_id: string
  status: JobStatus
  total_blocks: number
  completed_blocks: number
  current_block_id?: string
  failed_block_id?: string
  block_states: Record<string, string>   // block_id -> status string
  created_at: string
  started_at?: string
  finished_at?: string
  error_message?: string
  /** Optional details (e.g. traceback) for failed jobs */
  error_details?: Record<string, unknown>
  /** Head (5 rows) of the dataframe after this block ran; keyed by block id */
  block_previews?: Record<string, { columns: string[]; rows: Record<string, unknown>[] }>
}

export interface JobCreate {
  workflow_id: string
}
