import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { XCircle, Play, RefreshCw, ArrowUpRight } from 'lucide-react'
import { api } from '../api/client'
import { refreshAllData } from '../lib/refresh'
import { Card, Badge, Button, PageHeader, EmptyState, Spinner } from '../components/ui'
import type { Job, Workflow, BlockStatus } from '../api/types'

interface JobCardProps {
  job: Job
  workflowName?: string
  workflowBlocks?: Array<{ id?: string; type: string }>
}

function JobCard({ job, workflowName, workflowBlocks }: JobCardProps) {
  const qc = useQueryClient()
  const navigate = useNavigate()

  const cancelMutation = useMutation({
    mutationFn: () => api.jobs.cancel(job.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  })

  const rerunMutation = useMutation({
    mutationFn: () => api.jobs.create({ workflow_id: job.workflow_id }),
    onSuccess: (newJob) => {
      qc.invalidateQueries({ queryKey: ['jobs'] })
      navigate(`/jobs/${newJob.id}`)
    },
  })

  const totalBlocks = job.total_blocks
  const completedBlocks = job.completed_blocks
  const progress = totalBlocks > 0 ? (completedBlocks / totalBlocks) * 100 : 0
  const isActive = job.status === 'running' || job.status === 'pending'

  // Build block display from workflow blocks + job block_states
  const blockDisplay = workflowBlocks?.map((b) => ({
    type: b.type,
    status: (b.id ? (job.block_states[b.id] ?? 'pending') : 'pending') as BlockStatus,
  })) ?? []

  return (
    <Card
      className={`flex flex-col p-5 cursor-pointer hover:border-gray-300 transition-colors group ${
        isActive ? 'border-blue-300' : ''
      }`}
      onClick={() => navigate(`/jobs/${job.id}`)}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="min-w-0">
          <p className="text-base font-semibold text-gray-900 truncate">
            {workflowName ?? 'Workflow'}
          </p>
          <p className="text-sm text-gray-400 mt-0.5 font-mono truncate">
            {job.id.slice(0, 20)}…
          </p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Badge status={job.status} />
          <ArrowUpRight size={15} className="text-gray-300 group-hover:text-gray-500 transition-colors" />
        </div>
      </div>

      {/* Progress bar */}
      {totalBlocks > 0 && (
        <div className="mb-3">
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

      {/* Block pills */}
      {blockDisplay.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {blockDisplay.map((b, i) => (
            <span
              key={i}
              title={`${b.type} — ${b.status}`}
              className={`px-2 py-0.5 rounded text-xs font-medium ${
                b.status === 'completed' ? 'bg-green-50 text-green-600'
                : b.status === 'running'  ? 'bg-blue-50 text-blue-600'
                : b.status === 'failed'   ? 'bg-red-50 text-red-600'
                : 'bg-gray-100 text-gray-400'
              }`}
            >
              {b.type}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-auto pt-3 border-t border-gray-100">
        <span className="text-sm text-gray-400">
          {job.started_at
            ? new Date(job.started_at).toLocaleTimeString()
            : new Date(job.created_at).toLocaleTimeString()}
        </span>
        <div className="flex items-center gap-2">
          {isActive && (
            <button
              onClick={(e) => { e.stopPropagation(); cancelMutation.mutate() }}
              disabled={cancelMutation.isPending}
              className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
            >
              <XCircle size={14} />
              Cancel
            </button>
          )}
          {!isActive && (
            <button
              onClick={(e) => { e.stopPropagation(); rerunMutation.mutate() }}
              disabled={rerunMutation.isPending}
              className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-blue-600 transition-colors disabled:opacity-50"
            >
              <RefreshCw size={14} />
              Rerun
            </button>
          )}
        </div>
        {job.status === 'failed' && job.error_message && (
          <span className="text-sm text-red-500 truncate max-w-[60%]" title={job.error_message}>
            {job.error_message}
          </span>
        )}
      </div>
    </Card>
  )
}

function sortJobs(jobs: Job[]): Job[] {
  return [...jobs].sort((a, b) => {
    const aActive = a.status === 'running' || a.status === 'pending'
    const bActive = b.status === 'running' || b.status === 'pending'
    if (aActive && !bActive) return -1
    if (!aActive && bActive) return 1
    if (aActive && bActive) {
      return new Date(b.started_at ?? b.created_at).getTime() -
             new Date(a.started_at ?? a.created_at).getTime()
    }
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
}

export function JobsPage() {
  const qc = useQueryClient()

  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: api.jobs.list,
    refetchInterval: (query) => {
      const jobs = query.state.data as Job[] | undefined
      const hasActive = jobs?.some((j) => j.status === 'running' || j.status === 'pending')
      return hasActive ? 2000 : false
    },
  })

  const { data: workflows = [] } = useQuery({
    queryKey: ['workflows'],
    queryFn: api.workflows.list,
  })

  const workflowMap = Object.fromEntries(
    (workflows as Workflow[]).map((w) => [w.id, w])
  )

  const sorted = sortJobs(jobs)

  return (
    <div className="p-10">
      <PageHeader
        title="Jobs"
        subtitle="Monitor running and completed pipeline executions"
        action={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refreshAllData(qc)}
          >
            <RefreshCw size={14} />
            Refresh
          </Button>
        }
      />

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size={28} /></div>
      ) : sorted.length === 0 ? (
        <EmptyState
          message="No jobs yet. Run a workflow to create one."
          action={
            <div className="flex items-center gap-1.5 text-base text-gray-400">
              <Play size={15} />
              Go to Workflows to run a pipeline
            </div>
          }
        />
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {sorted.map((j) => (
            <JobCard
              key={j.id}
              job={j}
              workflowName={workflowMap[j.workflow_id]?.name}
              workflowBlocks={workflowMap[j.workflow_id]?.blocks}
            />
          ))}
        </div>
      )}
    </div>
  )
}
