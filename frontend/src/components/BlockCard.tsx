import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { BlockParamsForm } from './BlockParamsForm'
import type { BlockConfig } from '../types'
import './BlockCard.css'

interface BlockCardProps {
  block: BlockConfig
  onUpdate: (updates: Partial<BlockConfig>) => void
  onRemove: () => void
}

const LABELS: Record<BlockConfig['type'], string> = {
  read_csv: 'Read CSV',
  enrich_lead: 'Enrich Lead',
  find_email: 'Find Email',
  filter: 'Filter',
  save_csv: 'Save CSV',
}

export function BlockCard({ block, onUpdate, onRemove }: BlockCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: block.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`block-card ${isDragging ? 'dragging' : ''}`}
    >
      <div className="block-card-header">
        <span
          className="block-drag-handle"
          {...attributes}
          {...listeners}
          aria-label="Drag to reorder"
        >
          ⋮⋮
        </span>
        <span className="block-title">{LABELS[block.type]}</span>
        <button
          type="button"
          className="block-remove"
          onClick={onRemove}
          aria-label="Remove block"
        >
          ×
        </button>
      </div>
      <div className="block-card-body">
        <BlockParamsForm block={block} onUpdate={onUpdate} />
      </div>
    </div>
  )
}
