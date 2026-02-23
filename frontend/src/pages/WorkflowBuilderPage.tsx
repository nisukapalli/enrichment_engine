import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Plus, Trash2, Play, GripVertical, Save } from 'lucide-react'
import { api } from '../api/client'
import type { Block, BlockType } from '../api/types'
import { Card, Button, Input, Select, Spinner, Badge } from '../components/ui'

// ── Block type metadata ────────────────────────────────────────────────────

const BLOCK_META: Record<BlockType, { label: string; color: string; dot: string; description: string }> = {
  read_csv:    { label: 'Read CSV',     color: 'text-violet-600',  dot: 'bg-violet-500',  description: 'Load CSV from uploads/' },
  filter:      { label: 'Filter',       color: 'text-sky-600',     dot: 'bg-sky-500',     description: 'Filter rows by column value' },
  enrich_lead: { label: 'Enrich Lead',  color: 'text-fuchsia-600', dot: 'bg-fuchsia-500', description: 'Enrich leads via Sixtyfour API' },
  find_email:  { label: 'Find Email',   color: 'text-emerald-600', dot: 'bg-emerald-500', description: 'Find email via Sixtyfour API' },
  save_csv:    { label: 'Save CSV',     color: 'text-amber-600',   dot: 'bg-amber-500',   description: 'Write output to outputs/' },
}

const BLOCK_GRID = 'grid grid-cols-3 gap-2 items-center'

// ── Validation ─────────────────────────────────────────────────────────────

function validateBlocks(blocks: Block[]): Record<number, string> {
  const errors: Record<number, string> = {}
  blocks.forEach((block, i) => {
    if ((block.type === 'read_csv' || block.type === 'save_csv') && !block.params.path.trim()) {
      errors[i] = block.type === 'read_csv' ? 'File path is required' : 'Output file path is required'
    } else if (block.type === 'filter') {
      if (!block.params.column.trim()) errors[i] = 'Column name is required'
      else if (!block.params.value.trim()) errors[i] = 'Filter value is required'
    } else if (block.type === 'enrich_lead') {
      const entries = Object.entries(block.params.struct)
      if (entries.length === 0) errors[i] = 'At least one enrichment field is required'
      else if (entries.some(([k]) => !k.trim())) errors[i] = 'All field names must be non-empty'
    }
  })
  return errors
}

// ── Default params per block type ─────────────────────────────────────────

function defaultBlock(type: BlockType): Block {
  switch (type) {
    case 'read_csv':    return { type, params: { path: '' } }
    case 'filter':      return { type, params: { column: '', operator: 'contains', value: '' } }
    case 'enrich_lead': return { type, params: { struct: {} } }
    case 'find_email':  return { type, params: { mode: 'PROFESSIONAL' } }
    case 'save_csv':    return { type, params: { path: '' } }
  }
}

// ── Block editor ───────────────────────────────────────────────────────────

function BlockEditor({
  block,
  onChange,
  uploads,
}: {
  block: Block
  onChange: (b: Block) => void
  uploads: string[]
}) {
  if (block.type === 'read_csv') {
    if (uploads.length === 0) {
      return (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span>No uploaded files.</span>
          <Link to="/files" className="text-blue-600 hover:underline font-medium">
            Upload a file →
          </Link>
        </div>
      )
    }
    return (
      <div className={BLOCK_GRID}>
        <Select
          value={block.params.path}
          onChange={(e) => onChange({ ...block, params: { path: e.target.value } })}
        >
          <option value="">Select a file…</option>
          {uploads.map((f) => (
            <option key={f} value={f}>{f}</option>
          ))}
        </Select>
        <Link to="/files">
          <Button variant="ghost" size="sm">Upload new file</Button>
        </Link>
      </div>
    )
  }

  if (block.type === 'save_csv') {
    return (
      <div className={BLOCK_GRID}>
        <Input
          placeholder="output.csv"
          value={block.params.path}
          onChange={(e) => onChange({ ...block, params: { path: e.target.value } })}
        />
      </div>
    )
  }

  if (block.type === 'filter') {
    return (
      <div className={BLOCK_GRID}>
        <Input
          placeholder="Column"
          value={block.params.column}
          onChange={(e) => onChange({ ...block, params: { ...block.params, column: e.target.value } })}
        />
        <Select
          value={block.params.operator}
          onChange={(e) => onChange({ ...block, params: { ...block.params, operator: e.target.value as Block['params'] extends { operator: infer O } ? O : never } })}
        >
          {([
            ['contains',   'Contains'],
            ['equals',     'Equals'],
            ['not_equals', 'Does not equal'],
            ['gt',         'Greater than'],
            ['lt',         'Less than'],
            ['gte',        'Greater than or equal'],
            ['lte',        'Less than or equal'],
          ] as [string, string][]).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </Select>
        <Input
          placeholder="Value"
          value={block.params.value}
          onChange={(e) => onChange({ ...block, params: { ...block.params, value: e.target.value } })}
        />
      </div>
    )
  }

  if (block.type === 'enrich_lead') {
    const struct = block.params.struct
    const entries = Object.entries(struct)
    return (
      <div className="flex flex-col gap-2">
        {entries.map(([k, v], i) => (
          <div key={i} className="flex gap-2 items-center">
            <Input
              placeholder="Field name"
              value={k}
              onChange={(e) => {
                const newStruct = Object.fromEntries(entries.map(([ek, ev], ei) => [ei === i ? e.target.value : ek, ev]))
                onChange({ ...block, params: { ...block.params, struct: newStruct } })
              }}
            />
            <span className="text-gray-400 text-sm shrink-0">→</span>
            <Input
              placeholder="Description"
              value={v}
              onChange={(e) => {
                const newStruct = { ...struct, [k]: e.target.value }
                onChange({ ...block, params: { ...block.params, struct: newStruct } })
              }}
            />
            <Button
              variant="danger"
              size="sm"
              onClick={() => {
                const newStruct = Object.fromEntries(entries.filter((_, ei) => ei !== i))
                onChange({ ...block, params: { ...block.params, struct: newStruct } })
              }}
            >
              <Trash2 size={13} />
            </Button>
          </div>
        ))}
        <Button
          variant="ghost"
          size="sm"
          className="self-start"
          onClick={() => onChange({ ...block, params: { ...block.params, struct: { ...struct, '': '' } } })}
        >
          <Plus size={13} />
          Add field
        </Button>
        <Input
          placeholder="Research plan (optional)"
          value={block.params.research_plan ?? ''}
          onChange={(e) => onChange({ ...block, params: { ...block.params, research_plan: e.target.value || undefined } })}
        />
      </div>
    )
  }

  if (block.type === 'find_email') {
    return (
      <div className={BLOCK_GRID}>
        <Select
          value={block.params.mode}
          onChange={(e) => onChange({ ...block, params: { mode: e.target.value as 'PROFESSIONAL' | 'PERSONAL' } })}
        >
          <option value="PROFESSIONAL">Professional</option>
          <option value="PERSONAL">Personal</option>
        </Select>
      </div>
    )
  }

  return null
}

// ── Main page ──────────────────────────────────────────────────────────────

export function WorkflowBuilderPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: workflow, isLoading } = useQuery({
    queryKey: ['workflows', id],
    queryFn: () => api.workflows.get(id!),
    enabled: !!id,
  })

  const { data: allWorkflows = [] } = useQuery({
    queryKey: ['workflows'],
    queryFn: api.workflows.list,
  })

  const { data: uploads = [] } = useQuery({
    queryKey: ['files', 'uploads'],
    queryFn: api.files.listUploads,
  })

  const { data: outputs = [] } = useQuery({
    queryKey: ['files', 'outputs'],
    queryFn: api.files.listOutputs,
  })

  const [blocks, setBlocks] = useState<Block[] | null>(null)
  const [name, setName] = useState<string | null>(null)
  const [nameError, setNameError] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<Record<number, string>>({})
  const [overwriteFilename, setOverwriteFilename] = useState<string | null>(null)

  const currentBlocks = blocks ?? workflow?.blocks ?? []
  const currentName = name ?? workflow?.name ?? ''

  const validateName = (value: string): string | null => {
    const trimmed = value.trim()
    if (!trimmed) return 'Workflow name cannot be empty.'
    const duplicate = allWorkflows.find((w) => w.name === trimmed && w.id !== id)
    if (duplicate) return `A workflow named "${trimmed}" already exists.`
    return null
  }

  const saveMutation = useMutation({
    mutationFn: () => api.workflows.update(id!, { name: currentName.trim(), blocks: currentBlocks }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflows', id] })
      qc.invalidateQueries({ queryKey: ['workflows'] })
    },
  })

  const runMutation = useMutation({
    mutationFn: async () => {
      await saveMutation.mutateAsync()
      return api.jobs.create({ workflow_id: id! })
    },
    onSuccess: () => { setValidationErrors({}); navigate('/jobs') },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : 'Failed to start job.'
      setValidationErrors({ [-1]: msg })
    },
  })

  const handleNameBlur = () => {
    const error = validateName(currentName)
    if (error) {
      setNameError(error)
      return
    }
    setNameError(null)
    if (currentName.trim() !== workflow?.name) {
      saveMutation.mutate()
    }
  }

  const handleSave = () => {
    const error = validateName(currentName)
    if (error) {
      setNameError(error)
      return
    }
    setNameError(null)
    saveMutation.mutate()
  }

  const handleRun = () => {
    const nameErr = validateName(currentName)
    if (nameErr) {
      setNameError(nameErr)
      return
    }
    setNameError(null)

    const errors = validateBlocks(currentBlocks)
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors)
      return
    }
    setValidationErrors({})

    // Check if save_csv output file already exists
    const saveCsvBlock = currentBlocks.find((b) => b.type === 'save_csv')
    if (saveCsvBlock && saveCsvBlock.type === 'save_csv') {
      const filename = saveCsvBlock.params.path.trim()
      if (filename && outputs.includes(filename)) {
        setOverwriteFilename(filename)
        return
      }
    }

    runMutation.mutate()
  }

  const updateBlock = (i: number, b: Block) => {
    setBlocks(currentBlocks.map((c, ci) => (ci === i ? b : c)))
    if (validationErrors[i]) {
      const next = { ...validationErrors }
      delete next[i]
      setValidationErrors(next)
    }
  }

  const removeBlock = (i: number) =>
    setBlocks(currentBlocks.filter((_, ci) => ci !== i))

  const addBlock = (type: BlockType) =>
    setBlocks([...currentBlocks, defaultBlock(type)])

  if (isLoading) {
    return <div className="flex justify-center py-20"><Spinner size={24} /></div>
  }

  const apiError = validationErrors[-1]

  return (
    <div className="p-10">
      <div className="flex items-center gap-3 mb-1">
        <Button variant="ghost" size="sm" onClick={() => navigate('/workflows')}>
          <ArrowLeft size={16} />
        </Button>
        <div className="w-80">
          <Input
            value={currentName}
            onChange={(e) => { setName(e.target.value); setNameError(null) }}
            onBlur={handleNameBlur}
            onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur() }}
            className={`text-lg font-semibold ${nameError ? 'border-red-400 focus:border-red-500' : ''}`}
          />
          {nameError && (
            <p className="text-xs text-red-500 mt-1 px-1">{nameError}</p>
          )}
        </div>
        <div className="ml-auto flex gap-2">
          <Button variant="ghost" onClick={handleSave} disabled={saveMutation.isPending}>
            {saveMutation.isPending ? <Spinner size={14} /> : <Save size={15} />}
            Save
          </Button>
          <Button onClick={handleRun} disabled={runMutation.isPending || currentBlocks.length === 0}>
            {runMutation.isPending ? <Spinner size={14} /> : <Play size={15} />}
            Run
          </Button>
        </div>
      </div>

      <div className="mb-6" />

      {apiError && (
        <div className="mb-4 flex items-start gap-3 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm">
          <span className="shrink-0 mt-0.5">⚠</span>
          <span>{apiError}</span>
          <button className="ml-auto shrink-0 hover:text-red-800 transition-colors" onClick={() => setValidationErrors({})}>✕</button>
        </div>
      )}

      {Object.keys(validationErrors).filter(k => k !== '-1').length > 0 && (
        <div className="mb-4 flex items-start gap-3 px-4 py-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-700 text-sm">
          <span className="shrink-0 mt-0.5">⚠</span>
          <span>Please fill in all required fields before running. Errors are highlighted below.</span>
          <button className="ml-auto shrink-0 hover:text-amber-900 transition-colors" onClick={() => setValidationErrors({})}>✕</button>
        </div>
      )}

      {overwriteFilename && (
        <div className="mb-4 flex items-start gap-3 px-4 py-3 rounded-lg bg-yellow-50 border border-yellow-300 text-yellow-800 text-sm">
          <span className="shrink-0 mt-0.5">⚠</span>
          <span>
            <strong>{overwriteFilename}</strong> already exists in your outputs. Running this workflow will overwrite it. Continue?
          </span>
          <div className="ml-auto flex gap-2 shrink-0">
            <button
              className="font-medium text-yellow-900 hover:text-yellow-700 transition-colors"
              onClick={() => { setOverwriteFilename(null); runMutation.mutate() }}
            >
              Yes, overwrite
            </button>
            <button
              className="text-yellow-600 hover:text-yellow-800 transition-colors"
              onClick={() => setOverwriteFilename(null)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-[1fr_280px] gap-6">
        {/* Block chain */}
        <div className="flex flex-col gap-2">
          {currentBlocks.length === 0 && (
            <div className="flex flex-col items-center justify-center py-14 border border-dashed border-gray-200 rounded-xl text-center">
              <p className="text-sm text-gray-400">No blocks yet. Add one from the right panel.</p>
            </div>
          )}

          {currentBlocks.map((block, i) => {
            const meta = BLOCK_META[block.type]
            const error = validationErrors[i]
            return (
              <div key={i} className="relative">
                {i > 0 && (
                  <div className="absolute -top-2 left-6 w-px h-2 bg-gray-200" />
                )}
                <Card className={`p-4 ${error ? 'border-red-300' : ''}`}>
                  <div className="flex items-start gap-2">
                    <GripVertical size={16} className="text-gray-300 mt-1 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2.5">
                        <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${meta.dot}`} />
                        <span className={`text-sm font-semibold ${meta.color}`}>{meta.label}</span>
                        <Badge status={`step ${i + 1}`} />
                        {error && <span className="text-xs text-red-500 ml-1">— {error}</span>}
                      </div>
                      <BlockEditor block={block} onChange={(b) => updateBlock(i, b)} uploads={uploads} />
                    </div>
                    <button
                      onClick={() => removeBlock(i)}
                      className="text-gray-300 hover:text-red-500 transition-colors p-1 mt-0.5 shrink-0"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </Card>
              </div>
            )
          })}
        </div>

        {/* Block palette */}
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Add Block
          </p>
          <div className="flex flex-col gap-2">
            {(Object.keys(BLOCK_META) as BlockType[]).map((type) => {
              const meta = BLOCK_META[type]
              return (
                <button
                  key={type}
                  onClick={() => addBlock(type)}
                  className="flex items-start gap-3 px-4 py-3.5 rounded-lg bg-white border border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-left transition-colors cursor-pointer"
                >
                  <span className={`w-2.5 h-2.5 rounded-full shrink-0 mt-1 ${meta.dot}`} />
                  <div>
                    <p className={`text-sm font-semibold ${meta.color}`}>{meta.label}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{meta.description}</p>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
