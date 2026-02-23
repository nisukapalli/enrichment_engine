import { useRef, useState } from 'react'
import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, Download, RefreshCw, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { Card, Button, PageHeader, Spinner } from '../components/ui'

function FileRow({ name, dir }: { name: string; dir: 'uploads' | 'outputs' }) {
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
    <Card className="flex items-center gap-3 px-5 py-3.5">
      <FileText size={16} className={dir === 'uploads' ? 'text-blue-500 shrink-0' : 'text-green-500 shrink-0'} />
      <span className="text-base text-gray-700 flex-1 font-mono truncate">{name}</span>
      {downloadUrl && (
        <a href={downloadUrl} download={name}>
          <Button variant="ghost" size="sm">
            <Download size={14} />
            Download
          </Button>
        </a>
      )}
      <button
        onClick={() => deleteMutation.mutate()}
        disabled={deleteMutation.isPending}
        className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
      >
        <Trash2 size={14} />
        Delete
      </button>
    </Card>
  )
}

export function FilesPage() {
  const qc = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)

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
            onClick={() => {
              qc.invalidateQueries({ queryKey: ['files'] })
            }}
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

      <div className="grid grid-cols-2 gap-6">
        {/* Uploads */}
        <div>
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
            <div className="flex flex-col gap-2">
              {uploads.map((name) => (
                <FileRow key={name} name={name} dir="uploads" />
              ))}
            </div>
          )}
        </div>

        {/* Outputs */}
        <div>
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
            <div className="flex flex-col gap-2">
              {outputs.map((name) => (
                <FileRow key={name} name={name} dir="outputs" />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
