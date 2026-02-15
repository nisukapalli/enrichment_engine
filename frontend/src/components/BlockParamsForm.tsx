import type { BlockConfig, BlockType } from '../types'

interface BlockParamsFormProps {
  block: BlockConfig
  onUpdate: (updates: Partial<BlockConfig>) => void
}

export function BlockParamsForm({ block, onUpdate }: BlockParamsFormProps) {
  const params = block.params || {}
  const setParam = (key: string, value: unknown) => {
    onUpdate({
      params: { ...params, [key]: value },
    })
  }

  switch (block.type) {
    case 'read_csv':
      return (
        <div className="params-form">
          <label>
            File path
            <input
              type="text"
              value={(params.file_path as string) ?? ''}
              onChange={(e) => setParam('file_path', e.target.value)}
              placeholder="Upload CSV or enter path"
            />
          </label>
        </div>
      )
    case 'enrich_lead':
      return (
        <div className="params-form">
          <label>
            Struct (JSON) – fields to collect
            <textarea
              value={
                typeof params.struct === 'object'
                  ? JSON.stringify(params.struct, null, 2)
                  : (params.struct as string) ?? '{}'
              }
              onChange={(e) => {
                try {
                  setParam('struct', JSON.parse(e.target.value || '{}'))
                } catch {
                  // leave as-is on invalid JSON
                }
              }}
              rows={4}
              placeholder='{"name": "Full name", "email": "Email"}'
            />
          </label>
          <label>
            Research plan (optional)
            <input
              type="text"
              value={(params.research_plan as string) ?? ''}
              onChange={(e) => setParam('research_plan', e.target.value)}
            />
          </label>
        </div>
      )
    case 'find_email':
      return (
        <div className="params-form">
          <label>
            Mode
            <select
              value={(params.mode as string) ?? 'PROFESSIONAL'}
              onChange={(e) => setParam('mode', e.target.value)}
            >
              <option value="PROFESSIONAL">Professional (company)</option>
              <option value="PERSONAL">Personal</option>
            </select>
          </label>
        </div>
      )
    case 'filter':
      return (
        <div className="params-form params-form-inline">
          <label>
            Column
            <input
              type="text"
              value={(params.column as string) ?? ''}
              onChange={(e) => setParam('column', e.target.value)}
              placeholder="column_name"
            />
          </label>
          <label>
            Operator
            <select
              value={(params.operator as string) ?? 'contains'}
              onChange={(e) => setParam('operator', e.target.value)}
            >
              <option value="contains">contains</option>
              <option value="eq">equals</option>
              <option value="ne">not equals</option>
            </select>
          </label>
          <label>
            Value
            <input
              type="text"
              value={(params.value as string) ?? ''}
              onChange={(e) => setParam('value', e.target.value)}
              placeholder="value"
            />
          </label>
        </div>
      )
    case 'save_csv':
      return (
        <div className="params-form">
          <label>
            Output filename
            <input
              type="text"
              value={(params.output_filename as string) ?? 'output.csv'}
              onChange={(e) => setParam('output_filename', e.target.value)}
              placeholder="output.csv"
            />
          </label>
        </div>
      )
    default:
      return null
  }
}
