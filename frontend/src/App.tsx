import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { WorkflowsPage } from './pages/WorkflowsPage'
import { WorkflowBuilderPage } from './pages/WorkflowBuilderPage'
import { JobsPage } from './pages/JobsPage'
import { JobDetailPage } from './pages/JobDetailPage'
import { FilesPage } from './pages/FilesPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/workflows" replace />} />
        <Route path="workflows" element={<WorkflowsPage />} />
        <Route path="workflows/:id" element={<WorkflowBuilderPage />} />
        <Route path="jobs" element={<JobsPage />} />
        <Route path="jobs/:id" element={<JobDetailPage />} />
        <Route path="files" element={<FilesPage />} />
      </Route>
    </Routes>
  )
}
