import React, { useState, useEffect } from 'react'
import { Handle, Position, useReactFlow } from '@xyflow/react'

const ACCENT = 'var(--cyan)'

const styles = {
  node: {
    background: 'var(--paper)',
    border: '3px solid var(--ink)',
    borderRadius: 12,
    minWidth: 220,
    boxShadow: 'var(--shadow)'
  },
  header: {
    background: ACCENT,
    borderBottom: '3px solid var(--ink)',
    borderRadius: '9px 9px 0 0',
    padding: '7px 12px',
    display: 'flex',
    alignItems: 'center',
    gap: 7
  },
  dot: {
    width: 9, height: 9,
    borderRadius: '50%',
    background: 'var(--paper)',
    border: '2px solid var(--ink)',
    flexShrink: 0
  },
  removeBtn: {
    marginLeft: 'auto',
    background: 'transparent',
    border: 'none',
    color: 'var(--ink)',
    fontSize: 14,
    lineHeight: 1,
    padding: '0 2px',
    cursor: 'pointer',
    borderRadius: 3,
    display: 'flex',
    alignItems: 'center',
    transition: 'color 0.1s'
  },
  title: {
    fontFamily: 'var(--font-mono, monospace)',
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: 'var(--ink)'
  },
  body: {
    padding: '10px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: 6
  },
  label: {
    fontSize: 11,
    color: 'var(--muted-dim)',
    marginBottom: 2
  },
  pathDisplay: {
    background: 'var(--paper)',
    border: '2px solid var(--ink)',
    borderRadius: 6,
    padding: '5px 8px',
    fontSize: 11,
    color: 'var(--ink)',
    wordBreak: 'break-all',
    minHeight: 28,
    lineHeight: 1.4
  },
  placeholderText: {
    color: 'var(--muted)',
    fontStyle: 'italic'
  },
  browseBtn: {
    background: 'var(--yellow)',
    border: '2px solid var(--ink)',
    borderRadius: 6,
    color: 'var(--ink)',
    padding: '5px 10px',
    fontSize: 12,
    fontWeight: 700,
    cursor: 'pointer',
    boxShadow: 'var(--shadow-sm)',
    transition: 'transform 0.08s, box-shadow 0.08s'
  },
  modeRow: {
    display: 'flex',
    gap: 4,
    marginBottom: 2
  },
  modeBtn: (active) => ({
    flex: 1,
    padding: '3px 6px',
    fontSize: 10,
    fontWeight: 700,
    letterSpacing: '0.03em',
    textTransform: 'uppercase',
    border: '2px solid var(--ink)',
    borderRadius: 6,
    cursor: 'pointer',
    background: active ? 'var(--yellow)' : 'var(--paper)',
    color: 'var(--ink)'
  }),
  fileCount: {
    fontSize: 10,
    color: 'var(--muted-dim)'
  }
}

/** Live count of video files in a folder-mode Input's chosen folder. */
function useVideoFileCount(folderPath) {
  const [count, setCount] = useState(null)

  useEffect(() => {
    if (!folderPath) { setCount(null); return }
    let cancelled = false
    window.electronAPI.listVideoFiles(folderPath).then(files => {
      if (!cancelled) setCount(files.length)
    })
    return () => { cancelled = true }
  }, [folderPath])

  return count
}

export default function InputNode({ id, data, deletable }) {
  const { updateNodeData, deleteElements } = useReactFlow()
  const mode = data.mode === 'folder' ? 'folder' : 'file'
  const fileCount = useVideoFileCount(mode === 'folder' ? data.folderPath : null)

  const handleBrowseFile = async () => {
    const path = await window.electronAPI.openFile()
    if (path) updateNodeData(id, { filePath: path })
  }

  const handleBrowseFolder = async () => {
    const path = await window.electronAPI.openDirectory()
    if (path) updateNodeData(id, { folderPath: path })
  }

  const filename = data.filePath
    ? data.filePath.split(/[\\/]/).pop()
    : null
  const foldername = data.folderPath
    ? data.folderPath.split(/[\\/]/).pop()
    : null

  return (
    <div style={styles.node}>
      <div style={styles.header}>
        <div style={styles.dot} />
        <span style={styles.title}>{data.label || 'Input Video'}</span>
        {/* The original Input node is created non-deletable; extra ones added
            from the sidebar can be removed here (or with Backspace/Delete). */}
        {deletable !== false && (
          <button
            className="nodrag"
            onClick={e => { e.stopPropagation(); deleteElements({ nodes: [{ id }] }) }}
            title="Remove this input"
            style={styles.removeBtn}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--coral)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--ink)'}
          >
            ✕
          </button>
        )}
      </div>
      <div style={styles.body}>
        <div style={styles.modeRow}>
          <button
            className="nodrag"
            style={styles.modeBtn(mode === 'file')}
            onClick={() => updateNodeData(id, { mode: 'file' })}
          >
            File
          </button>
          <button
            className="nodrag"
            style={styles.modeBtn(mode === 'folder')}
            onClick={() => updateNodeData(id, { mode: 'folder' })}
          >
            Folder (batch)
          </button>
        </div>

        {mode === 'file' ? (
          <>
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
              onClick={handleBrowseFile}
              onMouseDown={e => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translate(3px, 3px)' }}
              onMouseUp={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
            >
              Browse…
            </button>
          </>
        ) : (
          <>
            <div style={styles.label}>Source folder</div>
            <div style={styles.pathDisplay}>
              {foldername
                ? <span title={data.folderPath}>{foldername}</span>
                : <span style={styles.placeholderText}>No folder selected…</span>
              }
            </div>
            {foldername && (
              <div style={styles.fileCount}>
                {fileCount === null
                  ? 'Counting video files…'
                  : fileCount === 0
                    ? '⚠️ No video files found in this folder.'
                    : `${fileCount} video file${fileCount === 1 ? '' : 's'} — runs the downstream chain once per file.`
                }
              </div>
            )}
            <button
              className="nodrag"
              style={styles.browseBtn}
              onClick={handleBrowseFolder}
              onMouseDown={e => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translate(3px, 3px)' }}
              onMouseUp={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
            >
              Browse…
            </button>
          </>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        style={{ background: ACCENT, borderColor: 'var(--ink)', borderWidth: 2 }}
      />
    </div>
  )
}
