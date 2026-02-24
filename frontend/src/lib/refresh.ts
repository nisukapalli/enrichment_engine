import type { QueryClient } from '@tanstack/react-query'

/**
 * Refetch all main app data (files, jobs, workflows) so the UI is up to date
 * on every page. Call this when the user clicks Refresh.
 */
export async function refreshAllData(qc: QueryClient) {
  await Promise.all([
    qc.refetchQueries({ queryKey: ['files'] }),
    qc.refetchQueries({ queryKey: ['jobs'] }),
    qc.refetchQueries({ queryKey: ['workflows'] }),
  ])
}
