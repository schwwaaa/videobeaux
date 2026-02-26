import React from 'react'
import { Handle, Position, useReactFlow } from '@xyflow/react'

const FORMATS = ['mp4', 'mov', 'avi', 'mkv', 'webm']

const styles = {
  node: {
    background: '#1e1e1e',
    border: '1px solid #ef4444',
    borderRadius: 8,
    minWidth: 220,
    boxShadow: '0 0 0 1px rgba(239,68,68,0.15), 0 4px 16px rgba(0,0,0,0.4)'
  },
  header: {
    background: 'rgba(239,68,68,0.12)',
    borderBottom: '1px solid rgba(239,68,68,0.3)',
    borderRadius: '7px 7px 0 0',
    padding: '7px 12px',
    display: 'flex',
    alignItems: 'center',
    gap: 7
  },
  dot: {
    width: 8, height: 8,
    borderRadius: '50%',
    background: '#ef4444',
    flexShrink: 0
  },
  title: {
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: '#ef4444'
  },
  body: {
    padding: '10px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: 6
  },
  row: {
    display: 'flex',
    gap: 6,
    alignItems: 'center'
  },
  label: {
    fontSize: 11,
    color: '#888',
    marginBottom: 2
  },
  pathDisplay: {
    background: '#111',
    border: '1px solid #333',
    borderRadius: 5,
    padding: '5px 8px',
    fontSize: 11,
    color: '#e0e0e0',
    wordBreak: 'break-all',
    minHeight: 28,
    lineHeight: 1.4,
    flex: 1
  },
  placeholderText: {
    color: '#555',
    fontStyle: 'italic'
  },
  browseBtn: {
    background: 'rgba(239,68,68,0.12)',
    border: '1px solid rgba(239,68,68,0.4)',
    borderRadius: 5,
    color: '#ef4444',
    padding: '5px 10px',
    fontSize: 12,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'background 0.15s',
    whiteSpace: 'nowrap'
  },
  select: {
    width: '100%',
    padding: '4px 8px',
    fontSize: 12,
    background: '#1a1a1a',
    border: '1px solid #333',
    borderRadius: 5,
    color: '#e0e0e0',
    cursor: 'pointer'
  }
}

/** Strip any existing extension from a path and append a new one. */
function replaceExt(filePath, ext) {
  const stem = filePath.replace(/\.[^./\\]+$/, '')
  return `${stem}.${ext}`
}

export default function OutputNode({ id, data }) {
  const { updateNodeData } = useReactFlow()

  const handleSave = async () => {
    const ext = data.format || 'mp4'
    // Pre-fill the dialog with the current stem + new extension if we already
    // have a path, otherwise use a generic default.
    const defaultName = data.filePath
      ? replaceExt(data.filePath, ext)
      : `output.${ext}`
    const path = await window.electronAPI.saveFile({
      defaultName,
      filters: [
        { name: ext.toUpperCase(), extensions: [ext] },
        { name: 'All Files', extensions: ['*'] }
      ]
    })
    if (path) updateNodeData(id, { filePath: path })
  }

  const handleFormatChange = (newFmt) => {
    // When the format changes, update the extension in the stored path so
    // the two fields always stay in sync.
    const update = { format: newFmt }
    if (data.filePath) update.filePath = replaceExt(data.filePath, newFmt)
    updateNodeData(id, update)
  }

  const filename = data.filePath
    ? data.filePath.split(/[\\/]/).pop()
    : null

  return (
    <div style={styles.node}>
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: '#ef4444', borderColor: '#0f0f0f' }}
      />

      <div style={styles.header}>
        <div style={styles.dot} />
        <span style={styles.title}>Output</span>
      </div>

      <div style={styles.body}>
        <div style={styles.label}>Output file</div>
        <div style={styles.row}>
          <div style={styles.pathDisplay}>
            {filename
              ? <span title={data.filePath}>{filename}</span>
              : <span style={styles.placeholderText}>No path set…</span>
            }
          </div>
          <button
            className="nodrag"
            style={styles.browseBtn}
            onClick={handleSave}
            onMouseOver={e => e.currentTarget.style.background = 'rgba(239,68,68,0.22)'}
            onMouseOut={e => e.currentTarget.style.background = 'rgba(239,68,68,0.12)'}
          >
            Save As…
          </button>
        </div>

        <div style={styles.label}>Container format</div>
        <select
          className="nodrag"
          style={styles.select}
          value={data.format || 'mp4'}
          onChange={e => handleFormatChange(e.target.value)}
        >
          {FORMATS.map(f => (
            <option key={f} value={f}>{f.toUpperCase()}</option>
          ))}
        </select>
      </div>
    </div>
  )
}
