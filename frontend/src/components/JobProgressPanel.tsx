import type { JobProgress as JobProgressType } from '../types'
import './JobProgressPanel.css'

interface JobProgressPanelProps {
  job: JobProgressType | null
  jobId: string | null
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
}

export function JobProgressPanel({ job, jobId }: JobProgressPanelProps) {
  if (!jobId && !job) {
    return (
      <div className="job-panel">
        <h3>Job progress</h3>
        <p className="job-placeholder">Run a workflow to see progress and results here.</p>
      </div>
    )
  }

  const statusClass = job?.status ?? 'pending'

  return (
    <div className="job-panel">
      <h3>Job progress</h3>
      {jobId && (
        <p className="job-id">
          <code>{jobId.slice(0, 8)}…</code>
        </p>
      )}
      {job && (
        <>
          <div className={`job-status job-status-${statusClass}`}>
            {STATUS_LABELS[job.status] ?? job.status}
          </div>
          {job.error && <p className="job-error">{job.error}</p>}
          <div className="job-blocks">
            <strong>Blocks</strong>
            <span className="block-count">
              {job.blocks_completed.length} / {job.total_blocks}
            </span>
            <ul className="blocks-completed">
              {job.blocks_completed.map((b, i) => (
                <li key={b.block_id}>
                  <span className="block-type">{b.block_type}</span>
                  {b.rows_affected != null && (
                    <span className="block-rows"> {b.rows_affected} rows</span>
                  )}
                  {b.error && <span className="block-err"> {b.error}</span>}
                  {b.sample_data && b.sample_data.length > 0 && (
                    <details className="block-sample">
                      <summary>Sample</summary>
                      <pre>{JSON.stringify(b.sample_data.slice(0, 2), null, 2)}</pre>
                    </details>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  )
}
