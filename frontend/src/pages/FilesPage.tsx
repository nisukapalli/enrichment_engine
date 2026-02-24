import { useRef, useState } from 'react'
import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, Download, RefreshCw, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { refreshAllData } from '../lib/refresh'
import { Card, Button, PageHeader, Spinner } from '../components/ui'

function FileHeadPreview({ name, dir }: { name: string; dir: 'uploads' | 'outputs' }) {
  const fetcher = dir === 'uploads' ? () => api.files.getUploadHead(name) : () => api.files.getOutputHead(name)
  const { data: rows, isLoading, error } = useQuery({
    queryKey: ['files', dir, name, 'head'],
    queryFn: fetcher,
    enabled: true,
  })

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3">
        <Spinner size={18} />
      </div>
    )
  }
  if (error || !rows?.length) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-500">
        {error instanceof Error ? error.message : 'No rows to display'}
      </div>
    )
  }

  const columns = Object.keys(rows[0])
  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50 overflow-hidden">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 py-2 border-b border-gray-200">
        First 10 rows
      </p>
      <div className="overflow-x-auto max-h-64 overflow-y-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-white sticky top-0">
              {columns.map((col) => (
                <th key={col} className="text-left px-3 py-2 font-medium text-gray-600 whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-b border-gray-100 hover:bg-white/60">
                {columns.map((col) => (
                  <td key={col} className="px-3 py-2 text-gray-700 truncate max-w-[200px]" title={String(row[col] ?? '')}>
                    {String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function FileRow({
  name,
  dir,
  isExpanded,
  onToggle,
}: {
  name: string
  dir: 'uploads' | 'outputs'
  isExpanded: boolean
  onToggle: () => void
}) {
  const qc = useQueryClient()
  const downloadUrl = dir === 'outputs' ? api.files.downloadUrl(name) : undefined

  const deleteMutation = useMutation({
    mutationFn: () =>
      dir === 'uploads' ? api.files.deleteUpload(name) : api.files.deleteOutput(name),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['files', dir] })
    },
  })

  return (
    <Card
      className={`flex items-center gap-3 w-full min-w-0 px-5 py-3.5 min-h-[52px] cursor-pointer transition-colors ${
        isExpanded ? 'ring-2 ring-blue-400 border-blue-300' : 'hover:border-gray-300'
      }`}
      onClick={onToggle}
    >
      <FileText size={16} className={dir === 'uploads' ? 'text-blue-500 shrink-0' : 'text-green-500 shrink-0'} />
      <span className="text-base text-gray-700 flex-1 font-mono truncate">{name}</span>
      {downloadUrl ? (
        <a href={downloadUrl} download={name} onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="sm">
            <Download size={14} />
            Download
          </Button>
        </a>
      ) : (
        <span className="invisible inline-flex items-center gap-2 px-3 py-2 text-sm shrink-0" aria-hidden>
          <Download size={14} />
          Download
        </span>
      )}
      <button
        onClick={(e) => { e.stopPropagation(); deleteMutation.mutate() }}
        disabled={deleteMutation.isPending}
        className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
      >
        <Trash2 size={14} />
        Delete
      </button>
    </Card>
  )
}

function expandedKey(dir: 'uploads' | 'outputs', name: string) {
  return `${dir}:${name}`
}

export function FilesPage() {
  const qc = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(() => new Set())

  const toggleExpanded = (dir: 'uploads' | 'outputs', name: string) => {
    const key = expandedKey(dir, name)
    setExpandedKeys((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const { data: uploads = [], isLoading: uploadsLoading } = useQuery({
    queryKey: ['files', 'uploads'],
    queryFn: api.files.listUploads,
  })

  const { data: outputs = [], isLoading: outputsLoading } = useQuery({
    queryKey: ['files', 'outputs'],
    queryFn: api.files.listOutputs,
  })

  const handleUpload = async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      setError('Only CSV files are supported.')
      return
    }
    setUploading(true)
    setError(null)
    try {
      await api.files.upload(file)
      qc.invalidateQueries({ queryKey: ['files', 'uploads'] })
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }

  return (
    <div className="p-10">
      <PageHeader
        title="Files"
        subtitle="Upload input CSVs and download output files"
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

      {/* Upload zone */}
      <Card
        className={`flex flex-col items-center justify-center py-14 mb-8 border-dashed cursor-pointer transition-colors ${
          dragOver ? 'border-blue-400 bg-blue-50' : 'hover:border-gray-300 hover:bg-gray-50'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
        />
        <div className="w-14 h-14 rounded-xl bg-gray-100 flex items-center justify-center mb-3">
          {uploading ? <Spinner size={22} /> : <Upload size={22} className="text-gray-400" />}
        </div>
        <p className="text-base font-medium text-gray-700 mb-1">
          {uploading ? 'Uploading…' : 'Drop a CSV here or click to browse'}
        </p>
        <p className="text-sm text-gray-400">Only .csv files are accepted</p>
        {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
      </Card>

      <div className="grid gap-6" style={{ gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)' }}>
        {/* Uploads */}
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Uploads ({uploads.length})
          </h2>
          {uploadsLoading ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : uploads.length === 0 ? (
            <p className="text-sm text-gray-400 py-6 text-center border border-dashed border-gray-200 rounded-xl">
              No uploaded files yet
            </p>
          ) : (
            <div className="flex flex-col gap-2 w-full min-w-0">
              {uploads.map((name) => (
                <React.Fragment key={name}>
                  <FileRow
                    name={name}
                    dir="uploads"
                    isExpanded={expandedKeys.has(expandedKey('uploads', name))}
                    onToggle={() => toggleExpanded('uploads', name)}
                  />
                  {expandedKeys.has(expandedKey('uploads', name)) && (
                    <div className="mt-1">
                      <FileHeadPreview name={name} dir="uploads" />
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          )}
        </div>

        {/* Outputs */}
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Outputs ({outputs.length})
          </h2>
          {outputsLoading ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : outputs.length === 0 ? (
            <p className="text-sm text-gray-400 py-6 text-center border border-dashed border-gray-200 rounded-xl">
              No output files yet — run a workflow with a <code className="text-blue-500">save_csv</code> block
            </p>
          ) : (
            <div className="flex flex-col gap-2 w-full min-w-0">
              {outputs.map((name) => (
                <React.Fragment key={name}>
                  <FileRow
                    name={name}
                    dir="outputs"
                    isExpanded={expandedKeys.has(expandedKey('outputs', name))}
                    onToggle={() => toggleExpanded('outputs', name)}
                  />
                  {expandedKeys.has(expandedKey('outputs', name)) && (
                    <div className="mt-1">
                      <FileHeadPreview name={name} dir="outputs" />
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
