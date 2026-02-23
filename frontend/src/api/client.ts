import type {
  Workflow,
  WorkflowCreate,
  WorkflowUpdate,
  Job,
  JobCreate,
} from './types'

const BASE = ''  // proxied by Vite dev server to localhost:8000

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status} ${text}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// ── Workflows ──────────────────────────────────────────────────────────────

export const api = {
  workflows: {
    list: () => request<Workflow[]>('/workflows'),
    get: (id: string) => request<Workflow>(`/workflows/${id}`),
    create: (body: WorkflowCreate) =>
      request<Workflow>('/workflows', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    update: (id: string, body: WorkflowUpdate) =>
      request<Workflow>(`/workflows/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      }),
    delete: (id: string) =>
      request<void>(`/workflows/${id}`, { method: 'DELETE' }),
  },

  jobs: {
    list: () => request<Job[]>('/jobs'),
    get: (id: string) => request<Job>(`/jobs/${id}`),
    create: (body: JobCreate) =>
      request<Job>('/jobs', { method: 'POST', body: JSON.stringify(body) }),
    cancel: (id: string) =>
      request<Job>(`/jobs/${id}/cancel`, { method: 'POST' }),
  },

  files: {
    listUploads: () => request<{ files: string[] }>('/files/uploads').then((r) => r.files),
    listOutputs: () => request<{ files: string[] }>('/files/outputs').then((r) => r.files),
    upload: (file: File) => {
      const form = new FormData()
      form.append('file', file)
      return fetch('/files/upload', { method: 'POST', body: form }).then((r) => {
        if (!r.ok) return r.json().then((e) => Promise.reject(new Error(e.detail ?? r.statusText)))
        return r.json()
      })
    },
    downloadUrl: (name: string) => `/files/download/${encodeURIComponent(name)}`,
    deleteUpload: (name: string) =>
      request<void>(`/files/uploads/${encodeURIComponent(name)}`, { method: 'DELETE' }),
    deleteOutput: (name: string) =>
      request<void>(`/files/outputs/${encodeURIComponent(name)}`, { method: 'DELETE' }),
  },
}
