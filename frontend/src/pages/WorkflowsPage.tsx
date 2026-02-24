import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Plus, Trash2, ArrowUpRight, Clock, Layers, Play, Copy } from 'lucide-react'
import { api } from '../api/client'
import type { Workflow, WorkflowCreate } from '../api/types'
import { Card, Button, Input, PageHeader, EmptyState, Spinner } from '../components/ui'

export function WorkflowsPage() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')
  const [nameError, setNameError] = useState<string | null>(null)
  const [duplicating, setDuplicating] = useState<Workflow | null>(null)
  const [duplicateName, setDuplicateName] = useState('')
  const [duplicateNameError, setDuplicateNameError] = useState<string | null>(null)

  const { data: workflows = [], isLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: api.workflows.list,
  })

  const createMutation = useMutation({
    mutationFn: (body: WorkflowCreate) => api.workflows.create(body),
    onSuccess: (w) => {
      qc.invalidateQueries({ queryKey: ['workflows'] })
      setCreating(false)
      setName('')
      setNameError(null)
      navigate(`/workflows/${w.id}`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: api.workflows.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflows'] }),
  })

  const runMutation = useMutation({
    mutationFn: (workflowId: string) => api.jobs.create({ workflow_id: workflowId }),
    onSuccess: (job) => {
      qc.invalidateQueries({ queryKey: ['jobs'] })
      navigate(`/jobs/${job.id}`)
    },
  })

  const duplicateMutation = useMutation({
    mutationFn: (body: WorkflowCreate) => api.workflows.create(body),
    onSuccess: (w) => {
      qc.invalidateQueries({ queryKey: ['workflows'] })
      setDuplicating(null)
      setDuplicateName('')
      setDuplicateNameError(null)
      navigate(`/workflows/${w.id}`)
    },
  })

  const nameAlreadyExists = (value: string) =>
    workflows.some((w) => w.name.trim() === value.trim())

  const handleDuplicate = () => {
    if (!duplicating) return
    setDuplicateNameError(null)
    const trimmed = duplicateName.trim()
    if (!trimmed) {
      setDuplicateNameError('Enter a name for the copy.')
      return
    }
    if (nameAlreadyExists(trimmed)) {
      setDuplicateNameError(`A workflow named "${trimmed}" already exists.`)
      return
    }
    duplicateMutation.mutate({ name: trimmed, blocks: duplicating.blocks })
  }

  const handleCreate = () => {
    setNameError(null)
    const trimmed = name.trim()
    if (trimmed && nameAlreadyExists(trimmed)) {
      setNameError(`A workflow named "${trimmed}" already exists.`)
      return
    }
    createMutation.mutate({ name: trimmed || undefined, blocks: [] })
  }

  return (
    <div className="p-10">
      <PageHeader
        title="Workflows"
        subtitle="Define and manage your data processing pipelines"
        action={
          <Button onClick={() => setCreating(true)}>
            <Plus size={16} />
            New Workflow
          </Button>
        }
      />

      {/* Create inline form */}
      {creating && (
        <Card className="mb-6 p-5">
          <div className="flex items-center gap-3">
            <Input
              autoFocus
              placeholder="Workflow name (optional)…"
              value={name}
              onChange={(e) => { setName(e.target.value); setNameError(null) }}
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              className={`flex-1 ${nameError ? 'border-red-400' : ''}`}
            />
            <Button onClick={handleCreate} disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner size={14} /> : 'Create'}
            </Button>
            <Button variant="ghost" onClick={() => { setCreating(false); setName(''); setNameError(null) }}>
              Cancel
            </Button>
          </div>
          {nameError && <p className="text-sm text-red-500 mt-2">{nameError}</p>}
        </Card>
      )}

      {/* Duplicate inline form */}
      {duplicating && (
        <Card className="mb-6 p-5">
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500 shrink-0">Duplicate &quot;{duplicating.name}&quot; as:</span>
            <Input
              autoFocus
              placeholder="Copy of …"
              value={duplicateName}
              onChange={(e) => { setDuplicateName(e.target.value); setDuplicateNameError(null) }}
              onKeyDown={(e) => e.key === 'Enter' && handleDuplicate()}
              className={`flex-1 ${duplicateNameError ? 'border-red-400' : ''}`}
            />
            <Button onClick={handleDuplicate} disabled={duplicateMutation.isPending}>
              {duplicateMutation.isPending ? <Spinner size={14} /> : 'Create copy'}
            </Button>
            <Button variant="ghost" onClick={() => { setDuplicating(null); setDuplicateName(''); setDuplicateNameError(null) }}>
              Cancel
            </Button>
          </div>
          {duplicateNameError && <p className="text-sm text-red-500 mt-2">{duplicateNameError}</p>}
        </Card>
      )}

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size={28} /></div>
      ) : workflows.length === 0 ? (
        <EmptyState message="No workflows yet. Create one to get started." />
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {[...workflows].sort((a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
          ).map((w) => (
            <Card
              key={w.id}
              className="flex flex-col p-5 hover:border-gray-300 cursor-pointer transition-colors group"
              onClick={() => navigate(`/workflows/${w.id}`)}
            >
              {/* Top row: name + open arrow */}
              <div className="flex items-start justify-between gap-2 mb-4">
                <p className="text-base font-semibold text-gray-900 leading-snug truncate">{w.name}</p>
                <ArrowUpRight
                  size={18}
                  className="text-gray-300 group-hover:text-gray-600 transition-colors shrink-0 mt-0.5"
                />
              </div>

              {/* Meta row */}
              <div className="flex items-center gap-3 text-sm text-gray-400 mt-auto">
                <span className="flex items-center gap-1.5">
                  <Layers size={14} />
                  {w.blocks.length} block{w.blocks.length !== 1 ? 's' : ''}
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock size={14} />
                  {new Date(w.updated_at).toLocaleDateString()}
                </span>
              </div>

              {/* Duplicate left; Run + Delete right */}
              <div className="flex justify-between items-center gap-2 mt-3 pt-3 border-t border-gray-100">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setDuplicating(w)
                    setDuplicateName(`Copy of ${w.name}`)
                  }}
                  className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-md px-2.5 py-1.5 hover:bg-gray-50 transition-colors"
                >
                  <Copy size={14} />
                  Duplicate
                </button>
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      runMutation.mutate(w.id)
                    }}
                    disabled={runMutation.isPending || w.blocks.length === 0}
                    className="flex items-center gap-1.5 text-sm font-medium text-green-700 bg-green-50 border border-green-200 rounded-md px-2.5 py-1.5 hover:bg-green-100 transition-colors disabled:opacity-50 disabled:pointer-events-none"
                  >
                    {runMutation.isPending ? <Spinner size={14} /> : <Play size={14} />}
                    Run
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteMutation.mutate(w.id)
                    }}
                    className="flex items-center gap-1.5 text-sm font-medium text-red-700 bg-red-50 border border-red-200 rounded-md px-2.5 py-1.5 hover:bg-red-100 transition-colors"
                  >
                    <Trash2 size={14} />
                    Delete
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
