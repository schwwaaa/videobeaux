import React, { useState, useEffect } from 'react'
import {
  Handle, Position, useReactFlow,
  useNodeConnections, useNodesData, useUpdateNodeInternals
} from '@xyflow/react'
import { usePrograms } from '../../ProgramsContext'
import { videoArgsOf, upstreamIsBatch } from '../../pipeline'

// ── Model picker ─────────────────────────────────────────────────────────────
//
// Dropdown of whatever's actually in videobeaux-gui/models/ right now (fetched
// fresh on mount, not cached like program discovery) + a Browse… escape hatch
// for anything else. A custom-browsed path is used as-is for this run only —
// not copied into models/ — so it's stitched into the option list as a
// one-off entry whenever it isn't already one of the discovered models.

function ModelPickerField({ value, onChange }) {
  const [models, setModels] = useState([])

  useEffect(() => {
    let cancelled = false
    window.electronAPI.listModels().then(list => { if (!cancelled) setModels(list) })
    return () => { cancelled = true }
  }, [])

  const handleBrowse = async () => {
    const picked = await window.electronAPI.openDirectory()
    if (picked != null) onChange(picked)
  }

  const options = (value && !models.some(m => m.path === value))
    ? [{ name: value.split(/[\\/]/).pop(), path: value }, ...models]
    : models

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
        <select
          className="nodrag"
          style={{
            width: '100%', padding: '4px 7px', fontSize: 12,
            background: 'var(--paper)', border: '2px solid var(--ink)', borderRadius: 6,
            color: 'var(--ink)', flex: 1, minWidth: 0, cursor: 'pointer'
          }}
          value={value || ''}
          onChange={e => onChange(e.target.value)}
        >
          <option value="" disabled>Select a model…</option>
          {options.map(m => <option key={m.path} value={m.path}>{m.name}</option>)}
        </select>
        <button
          className="nodrag"
          onClick={handleBrowse}
          title="Browse for a model folder"
          style={{
            background: 'var(--yellow)', border: '2px solid var(--ink)', borderRadius: 5,
            color: 'var(--ink)', padding: '4px 8px', fontSize: 11, fontWeight: 700,
            cursor: 'pointer', flexShrink: 0
          }}
        >
          …
        </button>
      </div>
      {value && (
        <span
          title={value}
          style={{ fontSize: 9, color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
        >
          {value}
        </span>
      )}
    </div>
  )
}

// ── Ollama model picker ──────────────────────────────────────────────────────
//
// Optional-path picker for auto_narrate's --topic mode — lists whatever
// Ollama server happens to be running locally (fetched fresh on mount, same
// pattern as ModelPickerField). Unlike Vosk models, there's no folder to
// browse to (models are referenced by name, pulled via `ollama pull`
// elsewhere), and an empty list is a normal, expected state rather than
// something to route around — this field is never required.

function OllamaModelPickerField({ value, onChange }) {
  const [models, setModels] = useState([])

  useEffect(() => {
    let cancelled = false
    window.electronAPI.listOllamaModels().then(list => { if (!cancelled) setModels(list) })
    return () => { cancelled = true }
  }, [])

  const options = (value && !models.some(m => m.name === value))
    ? [{ name: value, size: null }, ...models]
    : models

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <select
        className="nodrag"
        style={{
          width: '100%', padding: '4px 7px', fontSize: 12,
          background: 'var(--paper)', border: '2px solid var(--ink)', borderRadius: 6,
          color: 'var(--ink)', cursor: 'pointer'
        }}
        value={value || ''}
        onChange={e => onChange(e.target.value)}
      >
        <option value="">— none (use Script instead) —</option>
        {options.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
      </select>
      {models.length === 0 && (
        <span style={{ fontSize: 9, color: 'var(--muted)' }}>
          No local Ollama models found — this field is optional.
        </span>
      )}
    </div>
  )
}

// ── kokoro-tts voice picker ──────────────────────────────────────────────────
//
// Lists whatever kokoro-tts itself reports via --help-voices (fetched fresh
// on mount, same pattern as the other pickers) — no hardcoded voice list to
// go stale across kokoro-tts versions.

function KokoroVoicePickerField({ value, onChange }) {
  const [voices, setVoices] = useState([])

  useEffect(() => {
    let cancelled = false
    window.electronAPI.listKokoroVoices().then(list => { if (!cancelled) setVoices(list) })
    return () => { cancelled = true }
  }, [])

  const options = (value && !voices.includes(value)) ? [value, ...voices] : voices

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <select
        className="nodrag"
        style={{
          width: '100%', padding: '4px 7px', fontSize: 12,
          background: 'var(--paper)', border: '2px solid var(--ink)', borderRadius: 6,
          color: 'var(--ink)', cursor: 'pointer'
        }}
        value={value || ''}
        onChange={e => onChange(e.target.value)}
      >
        {options.length === 0 && <option value="">— kokoro-tts not found —</option>}
        {options.map(v => <option key={v} value={v}>{v}</option>)}
      </select>
      {voices.length === 0 && (
        <span style={{ fontSize: 9, color: 'var(--muted)' }}>
          No voices found — is kokoro-tts installed and on PATH?
        </span>
      )}
    </div>
  )
}

// ── Arg field renderer ──────────────────────────────────────────────────────

function ArgField({ arg, value, onChange }) {
  const inputStyle = {
    width: '100%',
    padding: '4px 7px',
    fontSize: 12,
    background: 'var(--paper)',
    border: '2px solid var(--ink)',
    borderRadius: 6,
    color: 'var(--ink)'
  }

  if (arg.type === 'file' && arg.subtype === 'model') {
    return <ModelPickerField value={value} onChange={onChange} />
  }

  if (arg.type === 'file' && arg.subtype === 'ollama_model') {
    return <OllamaModelPickerField value={value} onChange={onChange} />
  }

  if (arg.type === 'file' && arg.subtype === 'kokoro_voice') {
    return <KokoroVoicePickerField value={value} onChange={onChange} />
  }

  if (arg.type === 'file') {
    // subtype:'dir' → open a folder picker, otherwise file picker
    const isDir = arg.subtype === 'dir'

    const handleBrowse = async () => {
      const picked = isDir
        ? await window.electronAPI.openDirectory()
        : await window.electronAPI.openFile([{ name: 'All Files', extensions: ['*'] }])
      if (picked != null) onChange(picked)
    }

    return (
      <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
        <input
          className="nodrag"
          type="text"
          style={{ ...inputStyle, flex: 1, minWidth: 0 }}
          value={value || ''}
          placeholder={isDir ? 'Directory path…' : 'File path…'}
          onChange={e => onChange(e.target.value)}
          title={value || ''}
        />
        <button
          className="nodrag"
          onClick={handleBrowse}
          title={isDir ? 'Choose directory' : 'Choose file'}
          style={{
            background: 'var(--yellow)',
            border: '2px solid var(--ink)',
            borderRadius: 5,
            color: 'var(--ink)',
            padding: '4px 8px',
            fontSize: 11,
            fontWeight: 700,
            cursor: 'pointer',
            flexShrink: 0
          }}
        >
          …
        </button>
      </div>
    )
  }

  if (arg.type === 'select') {
    return (
      <select
        className="nodrag"
        style={{ ...inputStyle, cursor: 'pointer' }}
        value={value !== undefined && value !== '' ? value : (arg.default || arg.choices[0])}
        onChange={e => onChange(e.target.value)}
      >
        {arg.choices.map(c => <option key={c} value={c}>{c}</option>)}
      </select>
    )
  }

  if (arg.type === 'number') {
    return (
      <input
        className="nodrag"
        type="number"
        style={inputStyle}
        value={value !== undefined && value !== '' ? value : (arg.default !== undefined ? arg.default : '')}
        min={arg.min}
        max={arg.max}
        step={arg.step || 'any'}
        placeholder={arg.default !== undefined ? String(arg.default) : ''}
        onChange={e => onChange(e.target.value)}
      />
    )
  }

  if (arg.type === 'color') {
    // A native OS color picker (macOS's has its own color-wheel tab) paired
    // with a plain hex text field, kept in sync both ways: pick on the
    // wheel and the hex updates, or type/paste a hex code directly. The
    // swatch itself needs a valid #RRGGBB at all times (native input
    // requirement), so it falls back to the arg's default while the text
    // field is mid-edit with something incomplete — the text field's own
    // value (what actually gets passed to the program) is never touched.
    const hexPattern = /^#[0-9a-fA-F]{6}$/
    const swatchValue = hexPattern.test(value) ? value : (hexPattern.test(arg.default) ? arg.default : '#000000')
    return (
      <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
        <input
          className="nodrag"
          type="color"
          value={swatchValue}
          onChange={e => onChange(e.target.value.toUpperCase())}
          title="Pick a color"
          style={{
            width: 32, height: 28, padding: 0, border: '2px solid var(--ink)',
            borderRadius: 6, cursor: 'pointer', background: 'none', flexShrink: 0
          }}
        />
        <input
          className="nodrag"
          type="text"
          style={{ ...inputStyle, flex: 1, minWidth: 0, fontFamily: 'monospace' }}
          value={value || ''}
          placeholder={arg.default !== undefined ? String(arg.default) : '#RRGGBB'}
          onChange={e => onChange(e.target.value)}
        />
      </div>
    )
  }

  if (arg.type === 'checkbox') {
    return (
      <label className="nodrag" style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
        <input
          type="checkbox"
          className="nodrag"
          checked={value !== undefined ? !!value : !!arg.default}
          onChange={e => onChange(e.target.checked)}
          style={{ accentColor: 'var(--purple)', cursor: 'pointer' }}
        />
        <span style={{ fontSize: 11, color: 'var(--muted-dim)' }}>Enabled</span>
      </label>
    )
  }

  // default: text
  return (
    <input
      className="nodrag"
      type="text"
      style={inputStyle}
      value={value || ''}
      placeholder={arg.default !== undefined ? String(arg.default) : ''}
      onChange={e => onChange(e.target.value)}
    />
  )
}

// ── MediaInputRow ────────────────────────────────────────────────────────────
//
// One row per video-connectable arg. Always rendered (never inside the
// collapsible args section) so its Handle stays mounted and React Flow keeps
// a valid measured position for any edge routed into it. Shows either a
// "connected to <upstream node>" pill (edge wins) or falls back to the
// ordinary file-picker (today's behavior) when nothing is connected.

function MediaInputRow({ nodeId, arg, value, onChange, color }) {
  const { deleteElements } = useReactFlow()
  const { programMap } = usePrograms()
  const connections = useNodeConnections({ id: nodeId, handleType: 'target', handleId: arg.name })
  const conn = connections[0] ?? null
  const upstream = useNodesData(conn?.source ?? '')

  let upstreamLabel = 'Connected'
  if (upstream) {
    if (upstream.type === 'inputNode') {
      const fname = upstream.data?.filePath ? upstream.data.filePath.split(/[\\/]/).pop() : null
      upstreamLabel = upstream.data?.label || fname || 'Input'
    } else if (upstream.type === 'effectNode') {
      upstreamLabel = programMap[upstream.data?.program]?.label || upstream.data?.program || 'Effect'
    }
  }

  const handleBrowse = async () => {
    const picked = await window.electronAPI.openFile([{ name: 'All Files', extensions: ['*'] }])
    if (picked != null) onChange(picked)
  }

  const missing = arg.required && !conn && !value

  return (
    <div style={{ position: 'relative', padding: '5px 10px 5px 16px' }}>
      <Handle
        id={arg.name}
        type="target"
        position={Position.Left}
        style={{
          top: '50%',
          background: conn ? color : 'var(--paper)',
          borderColor: missing ? 'var(--coral)' : 'var(--ink)',
          borderWidth: 2
        }}
      />

      <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 3 }}>
        <span style={{ fontSize: 11, color: 'var(--muted-dim)' }}>{arg.label}</span>
        {missing && <span style={{ fontSize: 10, color: 'var(--coral)' }}>*</span>}
        {arg.help && (
          <span title={arg.help} style={{ fontSize: 9, color: 'var(--cyan)', cursor: 'help', opacity: 0.9, userSelect: 'none' }}>
            ⓘ
          </span>
        )}
      </div>

      {conn ? (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: `${color}33`, border: '2px solid var(--ink)', borderRadius: 6,
          padding: '4px 7px', fontSize: 11, color: 'var(--ink)'
        }}>
          <span
            title={upstreamLabel}
            style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
          >
            ▸ {upstreamLabel}
          </span>
          <button
            className="nodrag"
            onClick={() => deleteElements({ edges: [{ id: conn.edgeId }] })}
            title="Disconnect"
            style={{
              background: 'transparent', border: 'none', color: 'var(--ink)',
              cursor: 'pointer', fontSize: 12, lineHeight: 1, flexShrink: 0
            }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--coral)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--ink)'}
          >
            ✕
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
          <input
            className="nodrag"
            type="text"
            style={{
              flex: 1, minWidth: 0, padding: '4px 7px', fontSize: 12,
              background: 'var(--paper)', border: `2px solid ${missing ? 'var(--coral)' : 'var(--ink)'}`,
              borderRadius: 6, color: 'var(--ink)'
            }}
            value={value || ''}
            placeholder="File path… or connect a node"
            onChange={e => onChange(e.target.value)}
            title={value || ''}
          />
          <button
            className="nodrag"
            onClick={handleBrowse}
            title="Choose file"
            style={{
              background: 'var(--yellow)', border: '2px solid var(--ink)', borderRadius: 5,
              color: 'var(--ink)', padding: '4px 8px', fontSize: 11, fontWeight: 700,
              cursor: 'pointer', flexShrink: 0
            }}
          >
            …
          </button>
        </div>
      )}
    </div>
  )
}

// ── EffectNode ──────────────────────────────────────────────────────────────

export default function EffectNode({ id, data, selected }) {
  const { updateNodeData, deleteElements, getNodes, getEdges } = useReactFlow()
  const { programMap }     = usePrograms()
  const [expanded, setExpanded] = useState(true)

  const prog      = programMap[data.program]
  const videoArgs = videoArgsOf(prog)

  // The set of media-input handles can change after mount — programMap
  // starts as the static registry and is later replaced once async program
  // discovery resolves, which can change a node's video-arg count (or take
  // it from undefined to defined). React Flow needs to re-measure handle
  // positions whenever that set changes, or newly-added handles won't route
  // edges correctly. This hook (and the videoArgs it depends on) MUST stay
  // above the "unknown program" early return below — moving it after would
  // change the hook order between the unknown/known-program renders.
  const updateNodeInternals = useUpdateNodeInternals()
  const handleKey = videoArgs.map(a => a.name).join('|')
  useEffect(() => { updateNodeInternals(id) }, [id, handleKey, updateNodeInternals])

  // Primary-handle connection, tracked for the batch badge below — hooks
  // must stay above the early return too, for the same reason as above.
  const primaryConnections = useNodeConnections({ id, handleType: 'target', handleId: null })
  const primaryConn = primaryConnections[0] ?? null
  const primaryUpstream = useNodesData(primaryConn?.source ?? '')

  if (!prog) return <div style={{ color: 'var(--coral)', padding: 8 }}>Unknown: {data.program}</div>

  const color = prog.categoryColor || 'var(--muted)'
  const videoNames = new Set(videoArgs.map(a => a.name))
  const plainArgs  = (prog.args || []).filter(a => !videoNames.has(a.name) && !a.hidden)

  // Batch badge: only meaningful when the primary input traces back to a
  // batch source (a folder-mode Input, or a program that natively fans out
  // like qwikchop) — walks the whole upstream chain, not just one hop, since
  // batch-ness propagates through ordinary effects too.
  const isBatchUpstream = primaryConn
    ? upstreamIsBatch(id, getNodes(), getEdges(), programMap)
    : false
  let batchLabel = 'Batch'
  if (primaryUpstream?.type === 'inputNode') {
    const foldername = primaryUpstream.data?.folderPath
      ? primaryUpstream.data.folderPath.split(/[\\/]/).pop()
      : null
    batchLabel = primaryUpstream.data?.label || foldername || 'Input folder'
  } else if (primaryUpstream?.type === 'effectNode') {
    batchLabel = programMap[primaryUpstream.data?.program]?.label || primaryUpstream.data?.program || 'Effect'
  }

  const setArg = (name, value) => {
    updateNodeData(id, { args: { ...(data.args || {}), [name]: value } })
  }

  const handleDelete = (e) => {
    e.stopPropagation()
    deleteElements({ nodes: [{ id }] })
  }

  // Selected: colored ring added around the usual comic-black border/shadow
  const boxShadow = selected
    ? `var(--shadow), 0 0 0 3px ${color}`
    : `var(--shadow)`

  const hasCollapsible = plainArgs.length > 0
  const hasAnyBody      = hasCollapsible || videoArgs.length > 0
  // Arg-heavy nodes (e.g. Convert, with 17 options) run off the bottom of the
  // canvas as a single tall column — past this threshold, lay them out as a
  // 2-column grid instead and widen the node to fit. Small nodes are
  // unaffected (this only ever kicks in well above what any other current
  // program has).
  const useGrid = plainArgs.length > 6

  return (
    <div style={{
      background: 'var(--paper)',
      border: '3px solid var(--ink)',
      borderRadius: 12,
      minWidth: useGrid ? 420 : 230,
      maxWidth: useGrid ? 480 : 280,
      boxShadow,
      transition: 'box-shadow 0.1s'
    }}>
      {/* Primary (main) video input — the default/unlabeled handle */}
      <Handle
        type="target"
        position={Position.Left}
        style={{ top: 21, background: color, borderColor: 'var(--ink)', borderWidth: 2 }}
      />

      {/* Header */}
      <div
        style={{
          background: color,
          borderBottom: '3px solid var(--ink)',
          borderRadius: hasAnyBody ? '9px 9px 0 0' : 9,
          padding: '7px 8px 7px 10px',
          display: 'flex',
          alignItems: 'center',
          gap: 7,
          cursor: hasCollapsible ? 'pointer' : 'default',
          userSelect: 'none'
        }}
        onClick={() => hasCollapsible && setExpanded(x => !x)}
      >
        {/* Colour dot */}
        <div style={{ width: 9, height: 9, borderRadius: '50%', background: 'var(--paper)', border: '2px solid var(--ink)', flexShrink: 0 }} />

        {/* Program label */}
        <span style={{
          fontFamily: 'var(--font-mono, monospace)',
          fontSize: 11, fontWeight: 700,
          letterSpacing: '0.07em',
          textTransform: 'uppercase',
          color: 'var(--ink)',
          flex: 1
        }}>
          {prog.label}
        </span>

        {/* Collapse chevron */}
        {hasCollapsible && (
          <span style={{
            fontSize: 10, color: 'var(--ink)',
            transform: expanded ? 'rotate(0deg)' : 'rotate(-90deg)',
            transition: 'transform 0.15s',
            marginRight: 4
          }}>▼</span>
        )}

        {/* Delete button */}
        <button
          className="nodrag"
          onClick={handleDelete}
          title="Remove node"
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--ink)',
            fontSize: 14,
            lineHeight: 1,
            padding: '0 2px',
            cursor: 'pointer',
            borderRadius: 3,
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            transition: 'color 0.1s'
          }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--coral)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--ink)'}
        >
          ✕
        </button>
      </div>

      {/* Batch badge — shown only when this node's primary input traces back
          to a batch source, so the runner will run this node once per file. */}
      {isBatchUpstream && (
        <div style={{
          margin: '6px 10px 0',
          background: `${color}33`, border: '2px solid var(--ink)', borderRadius: 6,
          padding: '4px 7px', fontSize: 11, color: 'var(--ink)',
          display: 'flex', alignItems: 'center', gap: 5
        }}>
          <span title={batchLabel} style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            ▸ {batchLabel} • runs once per file
          </span>
        </div>
      )}

      {/* Media inputs — always rendered, regardless of collapsed state */}
      {videoArgs.length > 0 && (
        <div style={{
          padding: '6px 0',
          borderBottom: hasCollapsible ? '2px dashed var(--gray)' : 'none',
          display: 'flex', flexDirection: 'column'
        }}>
          {videoArgs.map(arg => (
            <MediaInputRow
              key={arg.name}
              nodeId={id}
              arg={arg}
              value={(data.args || {})[arg.name]}
              onChange={v => setArg(arg.name, v)}
              color={color}
            />
          ))}
        </div>
      )}

      {/* Arg fields (collapsible, video args excluded — they're above) */}
      {hasCollapsible && expanded && (
        <div style={useGrid
          ? { padding: '8px 10px', display: 'grid', gridTemplateColumns: '1fr 1fr', columnGap: 14, rowGap: 7 }
          : { padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 7 }
        }>
          {plainArgs.map(arg => (
            <div key={arg.name}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 3 }}>
                <span style={{ fontSize: 11, color: 'var(--muted-dim)' }}>{arg.label}</span>
                {arg.required && <span style={{ fontSize: 10, color: 'var(--coral)' }}>*</span>}
                {arg.help && (
                  <span
                    title={arg.help}
                    style={{
                      fontSize: 9,
                      color: 'var(--cyan)',
                      cursor: 'help',
                      lineHeight: 1,
                      opacity: 0.9,
                      userSelect: 'none'
                    }}
                  >
                    ⓘ
                  </span>
                )}
              </div>
              <ArgField
                arg={arg}
                value={(data.args || {})[arg.name]}
                onChange={v => setArg(arg.name, v)}
              />
            </div>
          ))}
        </div>
      )}

      {/* No-args description */}
      {!hasAnyBody && (
        <div style={{ padding: '6px 10px 8px', fontSize: 11, color: 'var(--muted)', fontStyle: 'italic' }}>
          {prog.description}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        style={{ background: color, borderColor: 'var(--ink)', borderWidth: 2 }}
      />
    </div>
  )
}
