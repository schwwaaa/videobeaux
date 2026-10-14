import React, { useEffect, useRef } from 'react'
import { Handle, Position, useReactFlow, useStore } from '@xyflow/react'
import { useUpdateNodeData } from '../../useCanvasHistory'
import { usePrograms } from '../../ProgramsContext'

// Grouped for the dropdown. Keep in step with ALLOWED_OUTPUT_EXTS in videobeaux/cli.py.
const FORMAT_GROUPS = [
  ['Video', ['mp4', 'mov', 'avi', 'mkv', 'webm', 'gif']],
  ['Audio', ['mp3', 'wav', 'm4a', 'flac']],
  ['Data / image', ['json', 'png']]
]
const ACCENT = 'var(--coral)'

const styles = {
  node: {
    background: 'var(--paper)',
    border: '3px solid var(--line, var(--ink))',
    borderRadius: 12,
    minWidth: 220,
    boxShadow: 'var(--shadow)'
  },
  header: {
    background: ACCENT,
    borderBottom: '3px solid var(--line, var(--ink))',
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
  title: {
    fontFamily: 'var(--font-mono, monospace)',
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: 'var(--on-color)'
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
    lineHeight: 1.4,
    flex: 1
  },
  placeholderText: {
    color: 'var(--muted)',
    fontStyle: 'italic'
  },
  browseBtn: {
    background: 'var(--yellow)',
    border: '2px solid var(--ink)',
    borderRadius: 6,
    color: 'var(--on-color)',
    padding: '5px 10px',
    fontSize: 12,
    fontWeight: 700,
    cursor: 'pointer',
    boxShadow: 'var(--shadow-sm)',
    transition: 'transform 0.08s, box-shadow 0.08s',
    whiteSpace: 'nowrap'
  },
  select: {
    width: '100%',
    padding: '4px 8px',
    fontSize: 12,
    background: 'var(--paper)',
    border: '2px solid var(--ink)',
    borderRadius: 6,
    color: 'var(--ink)',
    cursor: 'pointer'
  }
}

/** What file kind each program output type is written as, and which formats are acceptable for it. */
const OUTPUT_KIND = {
  json:  { formats: ['json'], preferred: 'json', label: 'a JSON report' },
  image: { formats: ['png'], preferred: 'png', label: 'images' },
  audio: { formats: ['mp3', 'wav', 'm4a', 'flac'], preferred: 'wav', label: 'audio' }
}
const VIDEO_FORMATS = ['mp4', 'mov', 'avi', 'mkv', 'webm', 'gif']

/** Strip any existing extension from a path and append a new one. */
function replaceExt(filePath, ext) {
  const stem = filePath.replace(/\.[^./\\]+$/, '')
  return `${stem}.${ext}`
}

export default function OutputNode({ id, data }) {
  const updateNodeData = useUpdateNodeData()
  const { programMap } = usePrograms()

  // The program feeding this Output decides what kind of file it is: Media Info → JSON, Extract Sound → audio, …
  const upstreamProgram = useStore(s => {
    const e = s.edges.find(x => x.target === id)
    return e ? s.nodeLookup.get(e.source)?.data?.program : undefined
  })
  const upstreamType = upstreamProgram ? (programMap?.[upstreamProgram]?.outputType || 'video') : null
  const kind = OUTPUT_KIND[upstreamType] || null

  // Keep the format valid for what's connected — but only react when the upstream kind changes (or on first mount when
  // it is already wrong), so a user's own valid choice (e.g. MP3 vs WAV) is never overridden.
  const lastType = useRef(null)
  useEffect(() => {
    if (!upstreamType || lastType.current === upstreamType) return
    lastType.current = upstreamType
    const fmt = data.format || 'mp4'
    let want = null
    if (kind && !kind.formats.includes(fmt)) want = kind.preferred
    if (!kind && upstreamType === 'video' && !VIDEO_FORMATS.includes(fmt)) want = 'mp4'
    if (want && want !== fmt) {
      const update = { format: want }
      if (data.filePath) update.filePath = replaceExt(data.filePath, want)
      updateNodeData(id, update)
    }
  }, [upstreamType]) // eslint-disable-line react-hooks/exhaustive-deps

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
        style={{ background: ACCENT, borderColor: 'var(--ink)', borderWidth: 2 }}
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
            onMouseDown={e => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translate(3px, 3px)' }}
            onMouseUp={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
            onMouseLeave={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
          >
            Save As…
          </button>
        </div>

        {kind && (
          <div style={{ ...styles.label, color: 'var(--ink)' }}>
            The connected step produces {kind.label}.
          </div>
        )}
        <div style={styles.label}>Container format</div>
        <select
          className="nodrag"
          style={styles.select}
          value={data.format || 'mp4'}
          onChange={e => handleFormatChange(e.target.value)}
        >
          {FORMAT_GROUPS.map(([label, list]) => (
            <optgroup key={label} label={label}>
              {list.map(f => <option key={f} value={f}>{f.toUpperCase()}</option>)}
            </optgroup>
          ))}
        </select>
      </div>
    </div>
  )
}
