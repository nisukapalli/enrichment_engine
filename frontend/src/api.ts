import type {
  BlockTypeInfo,
  JobProgress,
  WorkflowDefinition,
  WorkflowRunRequest,
} from './types'

const API_BASE = '/api/workflows'

export async function getBlockTypes(): Promise<BlockTypeInfo[]> {
  const res = await fetch(`${API_BASE}/blocks`)
  if (!res.ok) throw new Error('Failed to fetch block types')
  return res.json()
}

export async function uploadCsv(file: File): Promise<{ file_path: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error('Failed to upload file')
  return res.json()
}

export async function runWorkflow(
  body: WorkflowRunRequest
): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to run workflow')
  }
  return res.json()
}

export async function getJobProgress(jobId: string): Promise<JobProgress | null> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`)
  if (!res.ok) return null
  return res.json()
}
