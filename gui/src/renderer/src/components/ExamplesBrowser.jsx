import React, { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { lockModal } from '../useModalLock'
import { usePrograms } from '../ProgramsContext'

// Colours for the examples' categories come from the program list, so a card matches its program mode's colour in the sidebar.
// Chains have no program category of their own.
const CHAIN_CATEGORY = 'Chains'
const CHAIN_COLOR = '#d52c91'
const FALLBACK_COLOR = '#8a8a80'

function metaLine(e) {
  const clips = `${e.clips} clip${e.clips === 1 ? '' : 's'}`
  return e.steps > 1 ? `${clips} · ${e.steps} steps` : clips
}

/**
 * The Examples library: ready-made canvases (single program modes and chains), each one a click away. Picking one loads it through
 * onOpen (which returns true when the canvas was replaced); the window closes after that.
 */
export default function ExamplesBrowser({ onClose, onOpen }) {
  const { categories } = usePrograms()
  const [index, setIndex] = useState(null)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [busy, setBusy] = useState(false)

  useEffect(() => lockModal(), [])
  useEffect(() => {
    let alive = true
    window.electronAPI.listExamples()
      .then(data => { if (alive) setIndex(data) })
      .catch(err => { if (alive) setError(err.message) })
    return () => { alive = false }
  }, [])
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); onClose() }
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [onClose])

  const examples = index?.examples ?? []
  const categoryNames = useMemo(() => [...new Set(examples.map(e => e.category))], [examples])
  const colorOf = label => {
    if (label === CHAIN_CATEGORY) return CHAIN_COLOR
    return categories.find(c => c.label === label)?.color || FALLBACK_COLOR
  }

  const q = query.trim().toLowerCase()
  const shown = examples.filter(e =>
    (category === 'All' || e.category === category) &&
    (!q || e.name.toLowerCase().includes(q) || e.description.toLowerCase().includes(q) || e.id.toLowerCase().includes(q))
  )

  const pick = async (example) => {
    setBusy(true)
    let loaded = false
    try {
      loaded = await onOpen(example)
    } catch (err) {
      setError(err.message)
    }
    setBusy(false)
    if (loaded) onClose()
  }

  const chip = (label, color, active, onClick) => (
    <button key={label} onClick={onClick} aria-pressed={active} style={{
      fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase',
      padding: '3px 8px', borderRadius: 4, border: '2px solid var(--ink)', cursor: 'pointer',
      background: active ? 'var(--ink)' : color, color: active ? 'var(--paper)' : 'var(--on-color)'
    }}>{label}</button>
  )

  return createPortal(
    <div style={{ position: 'fixed', inset: 0, zIndex: 1100, background: 'rgba(8,8,8,0.55)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', padding: 16 }}
         onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}>
      <div role="dialog" aria-label="Examples" style={{
        width: 'min(880px, 100%)', maxHeight: '86vh', display: 'flex', flexDirection: 'column',
        background: 'var(--paper)', color: 'var(--ink)', border: 'var(--border)', borderRadius: 'var(--radius)',
        boxShadow: 'var(--shadow)', overflow: 'hidden'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'var(--cyan)', color: 'var(--on-color)',
                      padding: '8px 14px', borderBottom: 'var(--border)', fontFamily: 'var(--font-display)', fontSize: 13 }}>
          <span>🧪 Examples</span>
          <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            {index ? `${examples.length} ready to load` : ''}
          </span>
          <button onClick={onClose} aria-label="Close examples" style={{ padding: '0 8px', fontSize: 16, lineHeight: '22px' }}>×</button>
        </div>

        <div style={{ padding: '12px 14px 0', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search examples"
                 aria-label="Search examples" style={{ width: '100%' }} />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {chip('All', 'var(--paper-dim)', category === 'All', () => setCategory('All'))}
            {categoryNames.map(name => chip(name, colorOf(name), category === name, () => setCategory(name)))}
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: 14 }}>
          {error && <div style={{ fontSize: 12, color: 'var(--coral)' }}>Examples could not be loaded: {error}</div>}
          {!error && !index && <div style={{ fontSize: 12, color: 'var(--muted)', fontStyle: 'italic' }}>Loading examples…</div>}
          {index && shown.length === 0 && <div style={{ fontSize: 12, color: 'var(--muted)', fontStyle: 'italic' }}>No examples match.</div>}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
            {shown.map(e => (
              <button key={e.id} disabled={busy} onClick={() => pick(e)} style={{
                textAlign: 'left', padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column',
                background: 'var(--paper)', color: 'var(--ink)', border: '2px solid var(--ink)', borderRadius: 'var(--radius-sm)',
                boxShadow: '3px 3px 0 var(--ink)', cursor: busy ? 'wait' : 'pointer'
              }}>
                <span style={{ height: 6, background: colorOf(e.category) }} />
                <span style={{ padding: '8px 10px 10px', display: 'flex', flexDirection: 'column', gap: 4, flex: 1 }}>
                  <span style={{ fontWeight: 700, fontSize: 13, lineHeight: 1.25 }}>{e.name}</span>
                  <span style={{ fontSize: 11.5, lineHeight: 1.4, color: 'var(--muted)' }}>{e.description}</span>
                  <span style={{ marginTop: 'auto', paddingTop: 4, fontFamily: 'var(--font-mono)', fontSize: 10,
                                 letterSpacing: '0.06em', textTransform: 'uppercase' }}>{metaLine(e)}</span>
                </span>
              </button>
            ))}
          </div>
        </div>

        <div style={{ padding: '8px 14px', borderTop: 'var(--border)', fontSize: 11, color: 'var(--muted)' }}>
          Examples use the sample clips that ship with videobeaux. Results are saved to Documents/videobeaux/outputs.
        </div>
      </div>
    </div>,
    document.body
  )
}
