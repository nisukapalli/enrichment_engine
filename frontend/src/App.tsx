import { useState, useCallback } from 'react'
import { WorkflowBuilder } from './components/WorkflowBuilder'
import { JobProgressPanel } from './components/JobProgressPanel'
import type { BlockConfig, JobProgress as JobProgressType } from './types'
import './App.css'

function App() {
  const [blocks, setBlocks] = useState<BlockConfig[]>([])
  const [workflowName, setWorkflowName] = useState('Untitled Workflow')
  const [uploadedFilePath, setUploadedFilePath] = useState<string | null>(null)
  const [currentJob, setCurrentJob] = useState<JobProgressType | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)

  const handleRun = useCallback(
    async (inputFilePath: string | null) => {
      setCurrentJob(null)
      setJobId(null)
      const workflow = {
        name: workflowName,
        blocks,
      }
      try {
        const { job_id } = await (await import('./api')).runWorkflow({
          workflow,
          input_file_path: inputFilePath ?? undefined,
        })
        setJobId(job_id)
        setUploadedFilePath(inputFilePath)
        const poll = async () => {
          const progress = await (await import('./api')).getJobProgress(job_id)
          if (progress) setCurrentJob(progress)
          if (progress?.status === 'running' || progress?.status === 'pending') {
            setTimeout(poll, 1500)
          }
        }
        poll()
      } catch (e) {
        setCurrentJob({
          job_id: '',
          status: 'failed',
          current_block_index: 0,
          total_blocks: blocks.length,
          blocks_completed: [],
          error: e instanceof Error ? e.message : 'Unknown error',
        })
      }
    },
    [blocks, workflowName]
  )

  return (
    <div className="app">
      <header className="app-header">
        <h1>Sixtyfour Workflow Engine</h1>
        <p className="tagline">Configure and run workflows with chainable blocks</p>
      </header>
      <main className="app-main">
        <section className="workflow-section">
          <div className="workflow-header">
            <input
              type="text"
              className="workflow-name"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              placeholder="Workflow name"
            />
          </div>
          <WorkflowBuilder
            blocks={blocks}
            onBlocksChange={setBlocks}
            onRun={handleRun}
            uploadedFilePath={uploadedFilePath}
            onUploadedFileChange={setUploadedFilePath}
          />
        </section>
        <aside className="results-section">
          <JobProgressPanel job={currentJob} jobId={jobId} />
        </aside>
      </main>
    </div>
  )
}

export default App
