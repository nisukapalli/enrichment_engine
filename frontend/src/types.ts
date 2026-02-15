export type BlockType =
  | 'read_csv'
  | 'enrich_lead'
  | 'find_email'
  | 'filter'
  | 'save_csv'

export interface BlockConfig {
  id: string
  type: BlockType
  params: Record<string, unknown>
}

export interface WorkflowDefinition {
  name: string
  blocks: BlockConfig[]
}

export interface WorkflowRunRequest {
  workflow: WorkflowDefinition
  input_file_path?: string | null
}

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface BlockResult {
  block_id: string
  block_type: BlockType
  rows_affected?: number | null
  output_path?: string | null
  error?: string | null
  sample_data?: Record<string, unknown>[] | null
}

export interface JobProgress {
  job_id: string
  status: JobStatus
  current_block_index: number
  total_blocks: number
  blocks_completed: BlockResult[]
  error?: string | null
}

export interface BlockTypeInfo {
  type: BlockType
  label: string
  params_schema: Record<string, string>
}
