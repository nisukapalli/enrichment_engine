import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, RefreshCw, XCircle, CheckCircle2, Clock, AlertCircle, Loader2 } from 'lucide-react'
import { api } from '../api/client'
import type { BlockStatus } from '../api/types'
import { Card, Badge, Button, Spinner } from '../components/ui'

function blockStatusIcon(status: BlockStatus) {
  switch (status) {
    case 'completed': return <CheckCircle2 size={16} className="text-green-500 shrink-0" />
    case 'running':   return <Loader2 size={16} className="text-blue-500 animate-spin shrink-0" />
    case 'failed':    return <AlertCircle size={16} className="text-red-500 shrink-0" />
    default:          return <Clock size={16} className="text-gray-300 shrink-0" />
  }
}

interface BlockDisplayRow {
  type: string
  status: BlockStatus
}

function BlockRow({ block, isFailed, errorMessage }: { block: BlockDisplayRow; isFailed: boolean; errorMessage?: string }) {
  return (
    <Card className="p-5">
      <div className="flex items-start gap-3">
        {blockStatusIcon(block.status)}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-base font-semibold text-gray-900">{block.type}</span>
            <Badge status={block.status} />
          </div>

          {/* Error for this block */}
          {isFailed && errorMessage && (
            <div className="mt-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 font-mono break-all">
              {errorMessage}
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: job, isLoading } = useQuery({
    queryKey: ['jobs', id],
    queryFn: () => api.jobs.get(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const j = query.state.data
      return j?.status === 'running' || j?.status === 'pending' ? 2000 : false
    },
  })

  const { data: workflows = [] } = useQuery({
    queryKey: ['workflows'],
    queryFn: api.workflows.list,
  })

  const cancelMutation = useMutation({
    mutationFn: () => api.jobs.cancel(id!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs', id] }),
  })

  const workflow = workflows.find((w) => w.id === job?.workflow_id)
  const workflowName = workflow?.name

  if (isLoading) {
    return <div className="flex justify-center py-20"><Spinner size={24} /></div>
  }

  if (!job) {
    return (
      <div className="p-10">
        <p className="text-gray-500 text-base">Job not found.</p>
      </div>
    )
  }

  const isActive = job.status === 'running' || job.status === 'pending'
  const totalBlocks = job.total_blocks
  const completedBlocks = job.completed_blocks
  const progress = totalBlocks > 0 ? (completedBlocks / totalBlocks) * 100 : 0

  // Build block display rows from workflow blocks + job block_states
  const blockRows: BlockDisplayRow[] = workflow?.blocks.map((b) => ({
    type: b.type,
    status: (b.id ? (job.block_states[b.id] ?? 'pending') : 'pending') as BlockStatus,
  })) ?? []

  return (
    <div className="p-10">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate('/jobs')}>
          <ArrowLeft size={16} />
        </Button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-gray-900 truncate">
              {workflowName ?? 'Job'}
            </h1>
            <Badge status={job.status} />
          </div>
          <p className="text-sm text-gray-400 font-mono mt-0.5">{job.id}</p>
        </div>
        <div className="flex items-center gap-2">
          {isActive && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending}
            >
              <XCircle size={15} />
              Cancel
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => qc.invalidateQueries({ queryKey: ['jobs', id] })}
          >
            <RefreshCw size={14} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Meta */}
      <Card className="p-5 mb-6">
        <div className="grid grid-cols-3 gap-4 text-base">
          <div>
            <p className="text-sm text-gray-400 mb-0.5">Workflow</p>
            <p className="font-medium text-gray-900 truncate">{workflowName ?? job.workflow_id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-400 mb-0.5">Started</p>
            <p className="font-medium text-gray-900">
              {job.started_at ? new Date(job.started_at).toLocaleTimeString() : '—'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-400 mb-0.5">Completed</p>
            <p className="font-medium text-gray-900">
              {job.finished_at ? new Date(job.finished_at).toLocaleTimeString() : '—'}
            </p>
          </div>
        </div>

        {/* Progress bar */}
        {totalBlocks > 0 && (
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-400 mb-1">
              <span>{completedBlocks} / {totalBlocks} blocks</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  isActive ? 'bg-blue-500' : job.status === 'completed' ? 'bg-green-500' : 'bg-red-500'
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Top-level error */}
        {job.error_message && (
          <div className="mt-4 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <span className="font-semibold">Error: </span>{job.error_message}
          </div>
        )}
      </Card>

      {/* Block list */}
      <div>
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Blocks
        </p>
        {blockRows.length === 0 ? (
          <p className="text-base text-gray-400">No block data available.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {blockRows.map((b, i) => (
              <BlockRow
                key={i}
                block={b}
                isFailed={b.status === 'failed'}
                errorMessage={b.status === 'failed' ? job.error_message : undefined}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
