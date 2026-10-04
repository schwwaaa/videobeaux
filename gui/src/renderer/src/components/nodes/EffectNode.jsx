import React, { useState, useEffect } from 'react'
import {
  Handle, Position, useReactFlow,
  useNodeConnections, useNodesData, useUpdateNodeInternals
} from '@xyflow/react'
import { usePrograms } from '../../ProgramsContext'
import { videoArgsOf, upstreamIsBatch } from '../../pipeline'
import { useUpdateNodeData } from '../../useCanvasHistory'
import { ARG_HELPERS } from '../helpers/registry'
import { useRealEdges } from '../../GroupContext'

/** Choices like "Pack · Name" are shown grouped under their pack; plain choices stay flat. */
function renderChoices(choices) {
  if (!choices.some(c => c.includes(' · '))) {
    return choices.map(c => <option key={c} value={c}>{c}</option>)
  }
  const groups = []
  for (const c of choices) {
    const [pack, ...rest] = c.split(' · ')
    const name = rest.join(' · ') || c
    let g = groups.find(x => x.pack === pack)
    if (!g) { g = { pack, items: [] }; groups.push(g) }
    g.items.push([c, name])
  }
  return groups.map(g => (
    <optgroup key={g.pack} label={g.pack}>
      {g.items.map(([value, name]) => <option key={value} value={value}>{name}</option>)}
    </optgroup>
  ))
}

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
            color: 'var(--on-color)', padding: '4px 8px', fontSize: 11, fontWeight: 700,
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

/** Slider range: the declared min/max, else a soft range derived from the default (typed values may exceed it). */
function sliderRange(arg) {
  const d = Number.isFinite(Number(arg.default)) && arg.default !== '' ? Number(arg.default) : 0
  let lo = arg.min != null ? arg.min : (d < 0 ? d * 4 : 0)
  let hi = arg.max != null ? arg.max : Math.max(arg.integer ? 10 : 1, Math.abs(d) * 4)
  if (hi <= lo) hi = lo + 1
  return [lo, hi]
}

/** Step for the arrow keys / slider: explicit, else 1 for integers, else fine enough for the range. */
function numberStep(arg, lo, hi) {
  if (arg.step) return arg.step
  if (arg.integer) return 1
  const r = hi - lo
  if (r <= 2) return 0.01
  if (r <= 20) return 0.1
  const d = String(arg.default ?? '').split('.')[1]
  if (d && r <= 200) return Math.max(0.01, Math.pow(10, -d.length))
  return 1
}

/**
 * A typeable number box with a slider next to it — always (a soft range from the default when the program declares
 * none; anything typed outside it is still accepted).
 *
 * Typing uses a local draft so the box can be emptied and retyped (it used to snap back to the default, so "0"
 * could never be deleted). Valid numbers are stored as numbers as you type; on blur an empty/invalid draft reverts
 * and a valid one is clamped to min/max with a brief red hint. A ↺ button appears when the value differs from the
 * default, and a tinted strip under the slider marks the recommended ("good") range and the default.
 */
function NumberField({ arg, value, onChange, inputStyle }) {
  const [lo, hi] = sliderRange(arg)
  const step = numberStep(arg, lo, hi)
  const showSlider = !arg.free
  const [draft, setDraft] = useState(null)         // text while the box is being edited, else null
  const [hint, setHint] = useState('')
  const current = value !== undefined && value !== '' ? value : (arg.default !== undefined ? arg.default : '')
  const clamp = (v) => {
    let n = Number(v)
    if (!Number.isFinite(n)) return v
    if (arg.min != null) n = Math.max(arg.min, n)
    if (arg.max != null) n = Math.min(arg.max, n)
    return arg.integer ? Math.round(n) : n
  }
  const decimals = (String(step).split('.')[1] || '').length
  const numeric = Number.isFinite(Number(current)) && current !== '' ? Number(current) : lo
  const pct = (v) => `${Math.max(0, Math.min(100, ((v - lo) / (hi - lo)) * 100))}%`
  const hasGood = arg.good_min != null && arg.good_max != null
  const hasDefault = Number.isFinite(Number(arg.default)) && arg.default !== ''
  const differs = hasDefault && Number(current) !== Number(arg.default)

  const commit = (text) => {
    const t = String(text).trim()
    setDraft(null)
    if (t === '' || !Number.isFinite(Number(t))) return                // nothing usable typed: keep the last good value
    const n = Number(t)
    const c = clamp(n)
    if (c !== n) {
      setHint(n > c ? `max ${c}` : `min ${c}`)
      setTimeout(() => setHint(''), 1600)
    }
    onChange(c)
  }

  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
      {showSlider && (
        <div style={{ flex: 1, minWidth: 0, position: 'relative', paddingBottom: hasGood || hasDefault ? 6 : 0 }}>
          <input
            className="nodrag"
            type="range"
            min={lo}
            max={hi}
            step={step}
            value={Math.min(hi, Math.max(lo, numeric))}
            onChange={e => { setDraft(null); onChange(arg.integer ? Number(e.target.value) : Number(Number(e.target.value).toFixed(decimals + 1))) }}
            style={{ width: '100%', display: 'block', accentColor: 'var(--slider)', cursor: 'pointer' }}
          />
          {hasGood && (
            <div title={`Good starting range: ${arg.good_min}–${arg.good_max}`} style={{
              position: 'absolute', bottom: 0, height: 4, borderRadius: 2, pointerEvents: 'none',
              left: pct(arg.good_min), width: `calc(${pct(arg.good_max)} - ${pct(arg.good_min)})`,
              background: 'var(--slider)', opacity: 0.45
            }} />
          )}
          {hasDefault && (
            <div title={`Default: ${arg.default}`} style={{
              position: 'absolute', bottom: 0, height: 6, width: 2, left: pct(Number(arg.default)),
              background: 'var(--ink)', opacity: 0.7, pointerEvents: 'none'
            }} />
          )}
        </div>
      )}
      <input
        className="nodrag"
        type="number"
        style={{ ...inputStyle, width: showSlider ? 68 : '100%', flexShrink: 0, ...(hint ? { borderColor: 'var(--coral)' } : {}) }}
        value={draft !== null ? draft : current}
        min={arg.min}
        max={arg.max}
        step={step}
        placeholder={arg.default !== undefined ? String(arg.default) : ''}
        title={hint || (hasGood ? `Good starting range: ${arg.good_min}–${arg.good_max}` : undefined)}
        onFocus={e => e.currentTarget.select()}
        onChange={e => {
          const t = e.target.value
          setDraft(t)
          if (t !== '' && Number.isFinite(Number(t))) onChange(clamp(Number(t)))
        }}
        onBlur={e => commit(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') e.currentTarget.blur() }}
      />
      {differs && (
        <button className="nodrag" title={`Reset to default (${arg.default})`} onClick={() => { setDraft(null); onChange(arg.default) }}
                style={{ padding: '0 5px', height: 22, fontSize: 12, lineHeight: 1, flexShrink: 0 }}>↺</button>
      )}
      {hint && <span style={{ fontSize: 10, color: 'var(--coral)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>{hint}</span>}
    </div>
  )
}

function ArgField({ arg, value, onChange, programId, nodeId }) {
  const [helperOpen, setHelperOpen] = useState(false)
  const helper = ARG_HELPERS[programId]?.[arg.name]
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
            color: 'var(--on-color)',
            padding: '4px 8px',
            fontSize: 11,
            fontWeight: 700,
            cursor: 'pointer',
            flexShrink: 0
          }}
        >
          …
        </button>
        {helper && (
          <>
            <button
              className="nodrag"
              onClick={() => setHelperOpen(true)}
              title={helper.title}
              style={{
                background: 'var(--cyan)', border: '2px solid var(--ink)', borderRadius: 5, color: '#080808',
                padding: '4px 7px', fontSize: 12, fontWeight: 700, flexShrink: 0, lineHeight: 1
              }}
            >
              ✎
            </button>
            {helperOpen && (
              <helper.Component
                value={value}
                onChange={onChange}
                onClose={() => setHelperOpen(false)}
                nodeId={nodeId}
                programId={programId}
              />
            )}
          </>
        )}
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
        {renderChoices(arg.choices)}
      </select>
    )
  }

  if (arg.type === 'number') {
    return <NumberField arg={arg} value={value} onChange={onChange} inputStyle={inputStyle} />
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
          style={{ accentColor: 'var(--slider)', cursor: 'pointer' }}
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
              color: 'var(--on-color)', padding: '4px 8px', fontSize: 11, fontWeight: 700,
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
  const { deleteElements, getNodes } = useReactFlow()
  const realEdges = useRealEdges()
  const updateNodeData = useUpdateNodeData()
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
    ? upstreamIsBatch(id, getNodes(), realEdges, programMap)
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

  // The selected look (ring above the shadow) lives in index.css (.react-flow__node.selected)
  // so every node type shares it.
  const boxShadow = 'var(--shadow)'

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
          cursor: 'default',
          userSelect: 'none'
        }}
      >
        {/* Colour dot */}
        <div style={{ width: 9, height: 9, borderRadius: '50%', background: 'var(--paper)', border: '2px solid var(--ink)', flexShrink: 0 }} />

        {/* Program label */}
        <span style={{
          fontFamily: 'var(--font-mono, monospace)',
          fontSize: 11, fontWeight: 700,
          letterSpacing: '0.07em',
          textTransform: 'uppercase',
          color: 'var(--on-color)',
          flex: 1
        }}>
          {prog.label}
        </span>

        {/* Collapse / expand — only this button toggles, so clicking the header or name just selects the node */}
        {hasCollapsible && (
          <button
            className="nodrag node-caret"
            onClick={e => { e.stopPropagation(); setExpanded(x => !x) }}
            title={expanded ? 'Collapse' : 'Expand'}
            aria-label={expanded ? 'Collapse program' : 'Expand program'}
          >
            {expanded ? '▾' : '▸'}
          </button>
        )}

        {/* Delete button */}
        <button
          className="nodrag"
          onClick={handleDelete}
          title="Remove node"
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--on-color)',
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
          onMouseLeave={e => e.currentTarget.style.color = 'var(--on-color)'}
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
          {prog.presets && Object.keys(prog.presets).length > 0 && (
            <div style={{ gridColumn: '1 / -1', display: 'flex', flexWrap: 'wrap', gap: 5, alignItems: 'center' }}>
              <span style={{ fontSize: 10, color: 'var(--muted-dim)', fontFamily: 'var(--font-mono)' }}>Presets</span>
              {Object.entries(prog.presets).map(([name, vals]) => {
                const active = Object.entries(vals).every(([k, v]) => Number((data.args || {})[k] ?? NaN) === Number(v) || (data.args || {})[k] === v)
                return (
                  <button key={name} className="nodrag" onClick={() => updateNodeData(id, { args: { ...(data.args || {}), ...vals } })}
                          style={{ padding: '1px 8px', fontSize: 10, fontFamily: 'var(--font-mono)', borderRadius: 999,
                                   background: active ? color : 'var(--paper)', color: active ? 'var(--on-color)' : 'var(--ink)' }}>
                    {name}
                  </button>
                )
              })}
            </div>
          )}
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
                programId={data.program}
                nodeId={id}
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
