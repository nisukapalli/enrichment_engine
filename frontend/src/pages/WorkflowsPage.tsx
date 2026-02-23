import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Plus, Trash2, ArrowUpRight, Clock, Layers } from 'lucide-react'
import { api } from '../api/client'
import type { WorkflowCreate } from '../api/types'
import { Card, Button, Input, PageHeader, EmptyState, Spinner } from '../components/ui'

export function WorkflowsPage() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')

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
      navigate(`/workflows/${w.id}`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: api.workflows.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflows'] }),
  })

  const handleCreate = () => {
    const trimmed = name.trim()
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
        <Card className="mb-6 p-5 flex items-center gap-3">
          <Input
            autoFocus
            placeholder="Workflow name (optional)…"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            className="flex-1"
          />
          <Button onClick={handleCreate} disabled={createMutation.isPending}>
            {createMutation.isPending ? <Spinner size={14} /> : 'Create'}
          </Button>
          <Button variant="ghost" onClick={() => { setCreating(false); setName('') }}>
            Cancel
          </Button>
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

              {/* Delete button */}
              <div className="flex justify-end mt-3 pt-3 border-t border-gray-100">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteMutation.mutate(w.id)
                  }}
                  className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-red-500 transition-colors"
                >
                  <Trash2 size={14} />
                  Delete
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
