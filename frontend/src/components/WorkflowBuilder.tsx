import { useState, useCallback } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { BlockCard } from './BlockCard'
import { BlockPalette } from './BlockPalette'
import type { BlockConfig, BlockType } from '../types'
import './WorkflowBuilder.css'
import { uploadCsv, getBlockTypes } from '../api'
import { useEffect, useId } from 'react'

interface WorkflowBuilderProps {
  blocks: BlockConfig[]
  onBlocksChange: (blocks: BlockConfig[]) => void
  onRun: (inputFilePath: string | null) => void
  uploadedFilePath: string | null
  onUploadedFileChange: (path: string | null) => void
}

export function WorkflowBuilder({
  blocks,
  onBlocksChange,
  onRun,
  uploadedFilePath,
  onUploadedFileChange,
}: WorkflowBuilderProps) {
  const [blockTypes, setBlockTypes] = useState<{ type: BlockType; label: string }[]>([])
  const [running, setRunning] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileInputId = useId()

  useEffect(() => {
    getBlockTypes().then((list) =>
      setBlockTypes(list.map((b) => ({ type: b.type, label: b.label })))
    )
  }, [])

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event
      if (!over || active.id === over.id) return
      const oldIndex = blocks.findIndex((b) => b.id === active.id)
      const newIndex = blocks.findIndex((b) => b.id === over.id)
      if (oldIndex === -1 || newIndex === -1) return
      onBlocksChange(arrayMove(blocks, oldIndex, newIndex))
    },
    [blocks, onBlocksChange]
  )

  const addBlock = useCallback(
    (type: BlockType) => {
      const id = `block-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
      const params: Record<string, unknown> =
        type === 'read_csv'
          ? { file_path: uploadedFilePath ?? '' }
          : type === 'save_csv'
            ? { output_filename: 'output.csv' }
            : type === 'filter'
              ? { column: '', operator: 'contains', value: '' }
              : type === 'find_email'
                ? { mode: 'PROFESSIONAL' }
                : {}
      onBlocksChange([...blocks, { id, type, params }])
    },
    [blocks, onBlocksChange, uploadedFilePath]
  )

  const updateBlock = useCallback(
    (id: string, updates: Partial<BlockConfig>) => {
      onBlocksChange(
        blocks.map((b) => (b.id === id ? { ...b, ...updates } : b))
      )
    },
    [blocks, onBlocksChange]
  )

  const removeBlock = useCallback(
    (id: string) => {
      onBlocksChange(blocks.filter((b) => b.id !== id))
    },
    [blocks, onBlocksChange]
  )

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      setUploadError(null)
      const file = e.target.files?.[0]
      if (!file) return
      try {
        const { file_path } = await uploadCsv(file)
        onUploadedFileChange(file_path)
        const firstReadCsv = blocks.find((b) => b.type === 'read_csv')
        if (firstReadCsv) {
          updateBlock(firstReadCsv.id, {
            params: { ...firstReadCsv.params, file_path },
          })
        }
      } catch (err) {
        setUploadError(err instanceof Error ? err.message : 'Upload failed')
      }
      e.target.value = ''
    },
    [blocks, onUploadedFileChange, updateBlock]
  )

  const handleRunClick = useCallback(async () => {
    setRunning(true)
    try {
      await onRun(uploadedFilePath)
    } finally {
      setRunning(false)
    }
  }, [onRun, uploadedFilePath])

  const canRun =
    blocks.length > 0 &&
    (blocks[0].type !== 'read_csv' || (blocks[0].params?.file_path as string) || uploadedFilePath)

  return (
    <div className="workflow-builder">
      <div className="builder-toolbar">
        <div className="upload-row">
          <label htmlFor={fileInputId} className="upload-label">
            CSV file
          </label>
          <input
            id={fileInputId}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="file-input"
          />
          {uploadedFilePath && (
            <span className="uploaded-name">{uploadedFilePath}</span>
          )}
          {uploadError && <span className="upload-error">{uploadError}</span>}
        </div>
        <BlockPalette blockTypes={blockTypes} onAdd={addBlock} />
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={blocks.map((b) => b.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="blocks-list">
            {blocks.length === 0 ? (
              <p className="empty-hint">Add blocks from the palette above. Drag to reorder.</p>
            ) : (
              blocks.map((block) => (
                <BlockCard
                  key={block.id}
                  block={block}
                  onUpdate={(updates) => updateBlock(block.id, updates)}
                  onRemove={() => removeBlock(block.id)}
                />
              ))
            )}
          </div>
        </SortableContext>
      </DndContext>

      <div className="run-row">
        <button
          type="button"
          className="run-button"
          onClick={handleRunClick}
          disabled={!canRun || running}
        >
          {running ? 'Running…' : 'Run workflow'}
        </button>
      </div>
    </div>
  )
}
