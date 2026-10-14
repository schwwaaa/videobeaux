import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { lockModal } from '../../useModalLock'

/**
 * Topobeaux band editor: a gradient strip (the signal, 0 → 1) with draggable dividers. Each divider is a cut point;
 * each band between dividers has a color swatch. Writes `bands`, `cuts` and `colors`.
 */
const PALETTE = ['#0b1d51', '#1f6fa8', '#3fb68b', '#d6d84a', '#f08a3c', '#c8372d']
const HEX = /^#[0-9a-fA-F]{6}$/

function parseList(text) {
  return String(text || '').split(',').map(s => s.trim()).filter(Boolean)
}
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n))

export default function BandEditor({ values, setArgs, onClose }) {
  const initialBands = clamp(Number(values.bands) || 5, 2, 6)
  const [bands, setBands] = useState(initialBands)
  const [cuts, setCuts] = useState(() => {
    const c = parseList(values.cuts).map(Number).filter(Number.isFinite)
    return c.length === initialBands - 1 ? [...c].sort((a, b) => a - b) : Array.from({ length: initialBands - 1 }, (_, k) => (k + 1) / initialBands)
  })
  const [colors, setColors] = useState(() => {
    const c = parseList(values.colors).filter(x => HEX.test(x))
    return Array.from({ length: 6 }, (_, k) => c[k] || PALETTE[k])
  })
  const [soft, setSoft] = useState(Number(values.softness) || 0)
  const stripRef = useRef(null)
  const drag = useRef(null)

  useEffect(() => lockModal(), [])
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); onClose() }
      else if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); apply() }
      else if (!(e.target && ['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName))) e.stopPropagation()
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  })

  const changeBands = (n) => {
    setBands(n)
    setCuts(Array.from({ length: n - 1 }, (_, k) => (k + 1) / n))
  }

  const edges = useMemo(() => [0, ...cuts, 1], [cuts])
  const stops = useMemo(() => {
    // hard (or softened) stops of the false-color strip
    const out = []
    for (let k = 0; k < bands; k++) {
      const a = edges[k], b = edges[k + 1]
      out.push(`${colors[k]} ${(a * 100).toFixed(2)}%`, `${colors[k]} ${(b * 100).toFixed(2)}%`)
    }
    return out.join(', ')
  }, [edges, colors, bands])

  const posFromEvent = (e) => {
    const r = stripRef.current.getBoundingClientRect()
    return clamp((e.clientX - r.left) / r.width, 0, 1)
  }
  const onDown = (e, idx) => {
    e.preventDefault()
    e.currentTarget.setPointerCapture?.(e.pointerId)
    drag.current = idx
  }
  const onMove = (e) => {
    const idx = drag.current
    if (idx == null) return
    const lo = idx === 0 ? 0 : cuts[idx - 1] + 0.005
    const hi = idx === cuts.length - 1 ? 1 : cuts[idx + 1] - 0.005
    const v = Math.round(clamp(posFromEvent(e), lo, hi) * 1000) / 1000
    setCuts(cs => cs.map((c, k) => (k === idx ? v : c)))
  }
  const onUp = () => { drag.current = null }

  const apply = () => {
    setArgs({
      bands,
      cuts: cuts.map(c => (Math.round(c * 1000) / 1000).toString()).join(','),
      colors: colors.slice(0, bands).join(','),
      softness: soft
    })
    onClose()
  }

  const btn = { padding: '5px 12px', fontSize: 12, fontWeight: 700 }
  return createPortal(
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(8,8,8,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
         onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}>
      <div style={{ width: 'min(720px, 100%)', background: 'var(--paper)', color: 'var(--ink)', border: 'var(--border)', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 14px', background: 'var(--purple)', color: '#080808', borderBottom: 'var(--border)' }}>
          <strong style={{ fontFamily: 'var(--font-display)', fontSize: 13 }}>Topobeaux bands</strong>
          <span style={{ fontSize: 11 }}>drag the dividers · click a swatch to recolor a band</span>
          <span style={{ flex: 1 }} />
          <button onClick={onClose} style={{ padding: '2px 9px' }}>✕</button>
        </div>
        <div style={{ padding: '18px 22px 8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <label style={{ fontSize: 12 }}>Bands</label>
            <input type="range" min={2} max={6} step={1} value={bands} onChange={e => changeBands(Number(e.target.value))} style={{ width: 160, accentColor: 'var(--slider)' }} />
            <b style={{ fontFamily: 'var(--font-mono)', fontSize: 12, width: 14 }}>{bands}</b>
            <span style={{ flex: 1 }} />
            <label style={{ fontSize: 12 }}>Edge softness</label>
            <input type="range" min={0} max={0.5} step={0.01} value={soft} onChange={e => setSoft(Number(e.target.value))} style={{ width: 140, accentColor: 'var(--slider)' }} />
            <b style={{ fontFamily: 'var(--font-mono)', fontSize: 12, width: 36 }}>{soft.toFixed(2)}</b>
          </div>

          <div style={{ fontSize: 10, color: 'var(--muted-dim)', fontFamily: 'var(--font-mono)', display: 'flex', justifyContent: 'space-between' }}>
            <span>signal 0 (dark / low)</span><span>1 (bright / high)</span>
          </div>
          {/* the source gradient */}
          <div style={{ height: 22, border: '2px solid var(--ink)', borderBottom: 'none', background: 'linear-gradient(90deg, #000, #fff)' }} />
          {/* the resulting bands + dividers */}
          <div ref={stripRef} onPointerMove={onMove} onPointerUp={onUp} onPointerCancel={onUp}
               style={{ position: 'relative', height: 64, border: '2px solid var(--ink)', background: `linear-gradient(90deg, ${stops})`, touchAction: 'none' }}>
            {cuts.map((c, k) => (
              <div key={k} onPointerDown={e => onDown(e, k)} title={`cut ${k + 1}: ${c.toFixed(3)}`}
                   style={{ position: 'absolute', left: `${c * 100}%`, top: -8, bottom: -8, width: 18, marginLeft: -9, cursor: 'ew-resize', display: 'flex', justifyContent: 'center' }}>
                <div style={{ width: 4, background: 'var(--select)', outline: '2px solid #080808' }} />
              </div>
            ))}
          </div>
          <div style={{ position: 'relative', height: 22, marginTop: 4 }}>
            {cuts.map((c, k) => (
              <span key={k} style={{ position: 'absolute', left: `${c * 100}%`, transform: 'translateX(-50%)', fontFamily: 'var(--font-mono)', fontSize: 10 }}>{c.toFixed(2)}</span>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 10, marginTop: 8, flexWrap: 'wrap' }}>
            {Array.from({ length: bands }, (_, k) => (
              <label key={k} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11 }}>
                <span style={{ fontFamily: 'var(--font-mono)' }}>{k + 1}</span>
                <input type="color" value={colors[k]} onChange={e => setColors(cs => cs.map((c, i) => (i === k ? e.target.value : c)))}
                       style={{ width: 34, height: 26, padding: 0, border: '2px solid var(--ink)', borderRadius: 6, background: 'none' }} />
              </label>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '10px 22px 16px' }}>
          <button onClick={onClose} style={btn}>Cancel</button>
          <button onClick={apply} style={{ ...btn, background: 'var(--yellow)', color: '#080808' }}>Use these bands</button>
        </div>
      </div>
    </div>,
    document.body
  )
}
