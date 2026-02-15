import type { BlockType } from '../types'

interface BlockPaletteProps {
  blockTypes: { type: BlockType; label: string }[]
  onAdd: (type: BlockType) => void
}

const LABELS: Record<BlockType, string> = {
  read_csv: 'Read CSV',
  enrich_lead: 'Enrich Lead',
  find_email: 'Find Email',
  filter: 'Filter',
  save_csv: 'Save CSV',
}

export function BlockPalette({ blockTypes, onAdd }: BlockPaletteProps) {
  const list = blockTypes.length
    ? blockTypes
    : (Object.entries(LABELS) as [BlockType, string][]).map(([type, label]) => ({
        type,
        label,
      }))

  return (
    <div className="block-palette">
      <span className="palette-title">Add block</span>
      <div className="palette-buttons">
        {list.map(({ type, label }) => (
          <button
            key={type}
            type="button"
            className="palette-btn"
            onClick={() => onAdd(type)}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  )
}
