import React from 'react'
import { Handle, Position, useReactFlow } from '@xyflow/react'

const styles = {
  node: {
    background: '#1e1e1e',
    border: '1px solid #22c55e',
    borderRadius: 8,
    minWidth: 220,
    boxShadow: '0 0 0 1px rgba(34,197,94,0.15), 0 4px 16px rgba(0,0,0,0.4)'
  },
  header: {
    background: 'rgba(34,197,94,0.15)',
    borderBottom: '1px solid rgba(34,197,94,0.3)',
    borderRadius: '7px 7px 0 0',
    padding: '7px 12px',
    display: 'flex',
    alignItems: 'center',
    gap: 7
  },
  dot: {
    width: 8, height: 8,
    borderRadius: '50%',
    background: '#22c55e',
    flexShrink: 0
  },
  title: {
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: '#22c55e'
  },
  body: {
    padding: '10px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: 6
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
    lineHeight: 1.4
  },
  placeholderText: {
    color: '#555',
    fontStyle: 'italic'
  },
  browseBtn: {
    background: 'rgba(34,197,94,0.15)',
    border: '1px solid rgba(34,197,94,0.4)',
    borderRadius: 5,
    color: '#22c55e',
    padding: '5px 10px',
    fontSize: 12,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'background 0.15s'
  }
}

export default function InputNode({ id, data }) {
  const { updateNodeData } = useReactFlow()

  const handleBrowse = async () => {
    const path = await window.electronAPI.openFile()
    if (path) updateNodeData(id, { filePath: path })
  }

  const filename = data.filePath
    ? data.filePath.split(/[\\/]/).pop()
    : null

  return (
    <div style={styles.node}>
      <div style={styles.header}>
        <div style={styles.dot} />
        <span style={styles.title}>Input Video</span>
      </div>
      <div style={styles.body}>
        <div style={styles.label}>Source file</div>
        <div style={styles.pathDisplay}>
          {filename
            ? <span title={data.filePath}>{filename}</span>
            : <span style={styles.placeholderText}>No file selected…</span>
          }
        </div>
        <button
          className="nodrag"
          style={styles.browseBtn}
          onClick={handleBrowse}
          onMouseOver={e => e.currentTarget.style.background = 'rgba(34,197,94,0.25)'}
          onMouseOut={e => e.currentTarget.style.background = 'rgba(34,197,94,0.15)'}
        >
          Browse…
        </button>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        style={{ background: '#22c55e', borderColor: '#0f0f0f' }}
      />
    </div>
  )
}
