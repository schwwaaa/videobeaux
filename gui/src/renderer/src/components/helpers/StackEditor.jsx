import React, { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { lockModal } from '../../useModalLock'

/**
 * Stackadelic stack editor: three boxes on a stand-in frame. Drag a box to move it, drag its handles to resize,
 * toggle rectangle / rhombus, color and on/off per layer. Layer 1 is on top (and cuts out of the layers beneath).
 * Writes l{n}_left / right / top / bottom (percent of the frame), l{n}_shape, l{n}_color and l{n}_opacity
 * (0 = layer off). Size / ratio / rotation / tiles stay as the node's own fields.
 */
const LAYERS = [1, 2, 3]
const HANDLES = [['nw', -1, -1, 'nwse-resize'], ['n', 0, -1, 'ns-resize'], ['ne', 1, -1, 'nesw-resize'], ['w', -1, 0, 'ew-resize'],
                 ['e', 1, 0, 'ew-resize'], ['sw', -1, 1, 'nesw-resize'], ['s', 0, 1, 'ns-resize'], ['se', 1, 1, 'nwse-resize']]
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n))
const r1 = (n) => Math.round(n * 10) / 10

export default function StackEditor({ values, setArgs, onClose }) {
  const [layers, setLayers] = useState(() => LAYERS.map(n => {
    const g = (k, d) => (values[`l${n}_${k}`] ?? d)
    const l = Number(g('left', 30)), r = Number(g('right', 70)), t = Number(g('top', 30)), b = Number(g('bottom', 70))
    return {
      n, left: Math.min(l, r), right: Math.max(l, r), top: Math.min(t, b), bottom: Math.max(t, b),
      shape: g('shape', 'rectangle'), color: g('color', ['#FF3D7F', '#FFB000', '#2EC4B6'][n - 1]),
      on: Number(g('opacity', n === 1 ? 1 : 0)) > 0
    }
  }))
  const [sel, setSel] = useState(1)
  const [aspect, setAspect] = useState(16 / 9)
  const stageRef = useRef(null)
  const drag = useRef(null)

  useEffect(() => lockModal(), [])
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); onClose(); return }
      if (e.target && ['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return
      e.stopPropagation()                                     // the canvas underneath must not see the keyboard
      const step = e.shiftKey ? 5 : 1
      const d = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[e.key]
      if (d) { e.preventDefault(); nudge(d[0], d[1]) }
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  })

  const update = (n, patch) => setLayers(ls => ls.map(l => (l.n === n ? { ...l, ...patch } : l)))
  const nudge = (dx, dy) => setLayers(ls => ls.map(l => {
    if (l.n !== sel) return l
    const w = l.right - l.left, h = l.bottom - l.top
    const left = clamp(l.left + dx, 0, 100 - w), top = clamp(l.top + dy, 0, 100 - h)
    return { ...l, left: r1(left), right: r1(left + w), top: r1(top), bottom: r1(top + h) }
  }))

  const start = (e, l, mode, handle) => {
    e.preventDefault(); e.stopPropagation()
    setSel(l.n)
    e.currentTarget.setPointerCapture?.(e.pointerId)
    drag.current = { n: l.n, mode, handle, sx: e.clientX, sy: e.clientY, orig: { ...l } }
  }
  const move = (e) => {
    const d = drag.current
    if (!d) return
    const rect = stageRef.current.getBoundingClientRect()
    const dx = ((e.clientX - d.sx) / rect.width) * 100, dy = ((e.clientY - d.sy) / rect.height) * 100
    const o = d.orig
    if (d.mode === 'move') {
      const w = o.right - o.left, h = o.bottom - o.top
      const left = clamp(o.left + dx, 0, 100 - w), top = clamp(o.top + dy, 0, 100 - h)
      update(d.n, { left: r1(left), right: r1(left + w), top: r1(top), bottom: r1(top + h) })
      return
    }
    const [, hx, hy] = HANDLES.find(h => h[0] === d.handle)
    let { left, right, top, bottom } = o
    if (hx < 0) left = clamp(o.left + dx, 0, o.right - 1)
    if (hx > 0) right = clamp(o.right + dx, o.left + 1, 100)
    if (hy < 0) top = clamp(o.top + dy, 0, o.bottom - 1)
    if (hy > 0) bottom = clamp(o.bottom + dy, o.top + 1, 100)
    update(d.n, { left: r1(left), right: r1(right), top: r1(top), bottom: r1(bottom) })
  }
  const end = () => { drag.current = null }

  const apply = () => {
    const patch = {}
    for (const l of layers) {
      Object.assign(patch, {
        [`l${l.n}_left`]: l.left, [`l${l.n}_right`]: l.right, [`l${l.n}_top`]: l.top, [`l${l.n}_bottom`]: l.bottom,
        [`l${l.n}_shape`]: l.shape, [`l${l.n}_color`]: l.color,
        [`l${l.n}_opacity`]: l.on ? (Number(values[`l${l.n}_opacity`]) > 0 ? Number(values[`l${l.n}_opacity`]) : 1) : 0
      })
    }
    setArgs(patch)
    onClose()
  }

  const btn = { padding: '5px 12px', fontSize: 12, fontWeight: 700 }
  const cur = layers.find(l => l.n === sel)
  return createPortal(
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(8,8,8,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
         onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}>
      <div style={{ width: 'min(900px, 100%)', background: 'var(--paper)', color: 'var(--ink)', border: 'var(--border)', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 14px', background: 'var(--cyan)', color: '#080808', borderBottom: 'var(--border)' }}>
          <strong style={{ fontFamily: 'var(--font-display)', fontSize: 13 }}>Stackadelic layers</strong>
          <span style={{ fontSize: 11 }}>drag boxes · handles resize · arrows nudge · layer 1 is on top</span>
          <span style={{ flex: 1 }} />
          <select value={aspect} onChange={e => setAspect(Number(e.target.value))} style={{ padding: '2px 6px', fontSize: 11 }} title="Shape of the stand-in frame">
            <option value={16 / 9}>16:9</option><option value={9 / 16}>9:16</option><option value={1}>1:1</option><option value={4 / 3}>4:3</option>
          </select>
          <button onClick={onClose} style={{ padding: '2px 9px' }}>✕</button>
        </div>
        <div style={{ display: 'flex', gap: 16, padding: 16 }}>
          <div style={{ flex: 1, minWidth: 0, display: 'flex', justifyContent: 'center' }}
               onPointerDown={() => setSel(null)}>
            <div ref={stageRef} onPointerMove={move} onPointerUp={end} onPointerCancel={end}
                 style={{ position: 'relative', width: '100%', maxWidth: 560, aspectRatio: String(aspect), overflow: 'hidden',
                          background: 'repeating-conic-gradient(#2b2b2b 0% 25%, #353535 0% 50%) 50% / 24px 24px', border: '3px solid var(--ink)' }}>
              {[...layers].reverse().map(l => {                    // layer 3 first so layer 1 ends up on top
                const selected = l.n === sel
                return (
                  <div key={l.n} onPointerDown={e => start(e, l, 'move')}
                       style={{ position: 'absolute', left: `${l.left}%`, top: `${l.top}%`, width: `${l.right - l.left}%`, height: `${l.bottom - l.top}%`,
                                opacity: l.on ? 1 : 0.35, cursor: 'move', touchAction: 'none',
                                outline: selected ? '2px solid var(--select)' : '1px dashed rgba(255,255,255,0.5)', outlineOffset: 1 }}>
                    <div style={{ position: 'absolute', inset: 0, background: l.color, opacity: 0.8,
                                  clipPath: l.shape === 'rhombus' ? 'polygon(50% 0, 100% 50%, 50% 100%, 0 50%)' : 'none' }} />
                    <span style={{ position: 'absolute', left: 4, top: 2, fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#080808',
                                   background: 'rgba(255,255,255,0.75)', borderRadius: 3, padding: '0 4px' }}>{l.n}</span>
                    {selected && HANDLES.map(([key, hx, hy, cursor]) => (
                      <div key={key} onPointerDown={e => start(e, l, 'resize', key)}
                           style={{ position: 'absolute', width: 10, height: 10, background: 'var(--select)', border: '2px solid #080808', borderRadius: 2, cursor, touchAction: 'none',
                                    left: `calc(${(hx + 1) * 50}% - 5px)`, top: `calc(${(hy + 1) * 50}% - 5px)` }} />
                    ))}
                  </div>
                )
              })}
            </div>
          </div>
          <div style={{ width: 230, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {layers.map(l => (
              <div key={l.n} onClick={() => setSel(l.n)}
                   style={{ border: '2px solid var(--ink)', borderRadius: 8, padding: 8, background: l.n === sel ? 'var(--paper-dim)' : 'transparent',
                            outline: l.n === sel ? '2px solid var(--select)' : 'none' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <b style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>Layer {l.n}</b>
                  <span style={{ flex: 1 }} />
                  <label style={{ fontSize: 11, display: 'flex', gap: 4, alignItems: 'center' }}>
                    <input type="checkbox" checked={l.on} onChange={e => update(l.n, { on: e.target.checked })} /> on
                  </label>
                </div>
                <div style={{ display: 'flex', gap: 6, marginTop: 6, alignItems: 'center' }}>
                  <select value={l.shape} onChange={e => update(l.n, { shape: e.target.value })} style={{ flex: 1, padding: '2px 4px', fontSize: 11 }}>
                    <option value="rectangle">rectangle</option><option value="rhombus">rhombus</option>
                  </select>
                  <input type="color" value={l.color} onChange={e => update(l.n, { color: e.target.value })}
                         style={{ width: 30, height: 24, padding: 0, border: '2px solid var(--ink)', borderRadius: 6, background: 'none' }} />
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted-dim)', marginTop: 4 }}>
                  L {l.left}  R {l.right}  T {l.top}  B {l.bottom}
                </div>
              </div>
            ))}
            {cur == null && <div style={{ fontSize: 11, color: 'var(--muted)' }}>Click a box to select it.</div>}
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '0 16px 16px' }}>
          <button onClick={onClose} style={btn}>Cancel</button>
          <button onClick={apply} style={{ ...btn, background: 'var(--yellow)', color: '#080808' }}>Use this stack</button>
        </div>
      </div>
    </div>,
    document.body
  )
}
