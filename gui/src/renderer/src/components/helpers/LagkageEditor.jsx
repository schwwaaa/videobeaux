import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

/**
 * Lagkage layout editor — a crude canvas for placing images / GIFs / videos on a stand-in for the
 * base video, then turning that into the layout JSON lagkage reads (positions are stored as
 * percentages of the video, so the layout works at any resolution).
 */

const ASPECTS = { '16:9': [16, 9], '9:16': [9, 16], '1:1': [1, 1], '4:3': [4, 3], '21:9': [21, 9] }
const REF_W = 1920                                  // only used to write readable pixel positions
const VIDEO_EXT = new Set(['mp4', 'mov', 'webm', 'mkv', 'avi', 'm4v', 'mpg', 'mpeg'])
const ANCHORS = [['top_left', '↖'], ['top', '↑'], ['top_right', '↗'],
                 ['left', '←'], ['center', '●'], ['right', '→'],
                 ['bottom_left', '↙'], ['bottom', '↓'], ['bottom_right', '↘']]
const round = (n, d = 2) => Math.round(n * 10 ** d) / 10 ** d
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n))
let uid = 0

function typeFor(path) {
  const ext = (path.split('.').pop() || '').toLowerCase()
  if (ext === 'gif') return 'gif'
  return VIDEO_EXT.has(ext) ? 'video' : 'img'
}
const baseName = (p) => (p || '').split(/[\\/]/).pop()

export default function LagkageEditor({ value, onChange, onClose, nodeId }) {
  const [layers, setLayers] = useState([])
  const [selId, setSelId] = useState(null)
  const [aspect, setAspect] = useState('16:9')
  const [direction, setDirection] = useState('forward')
  const [status, setStatus] = useState('')
  const [layoutPath, setLayoutPath] = useState(null)
  const [stage, setStage] = useState({ w: 640, h: 360 })
  const areaRef = useRef(null)
  const stageRef = useRef(null)

  const [aw, ah] = ASPECTS[aspect]
  const stageRatio = aw / ah

  // Fit the stage into the available area, preserving the chosen aspect.
  useLayoutEffect(() => {
    const el = areaRef.current
    if (!el) return
    const fit = () => {
      const maxW = el.clientWidth - 16, maxH = el.clientHeight - 16
      let w = maxW, h = w / stageRatio
      if (h > maxH) { h = maxH; w = h * stageRatio }
      setStage({ w: Math.max(80, Math.floor(w)), h: Math.max(60, Math.floor(h)) })
    }
    fit()
    const ro = new ResizeObserver(fit)
    ro.observe(el)
    return () => ro.disconnect()
  }, [stageRatio])

  const update = useCallback((id, patch) => {
    setLayers(ls => ls.map(l => (l.id === id ? { ...l, ...patch } : l)))
  }, [])

  // ── Loading ────────────────────────────────────────────────────────────────
  const makeLayer = useCallback(async (filename, extra = {}, jsonPath = null) => {
    const probe = await window.electronAPI.probeMedia(filename, jsonPath)
    const type = extra.type || typeFor(filename)
    const dataUrl = type === 'video' ? null : await window.electronAPI.readImageDataUrl(filename, jsonPath)
    const ar = probe && probe.width && probe.height ? probe.width / probe.height : 1
    return {
      id: ++uid, name: extra.name || baseName(filename).replace(/\.[^.]+$/, ''), filename, type,
      ar, dataUrl, x: 10, y: 10, size: 25, opacity: 1, zoom: 1, raw: {}, ...extra
    }
  }, [])

  const loadJson = useCallback(async (jsonPath) => {
    const text = await window.electronAPI.readLayout(jsonPath)
    if (!text) { setStatus('Could not read that layout file.'); return }
    let data
    try { data = JSON.parse(text) } catch { setStatus('That file is not valid JSON.'); return }
    const asp = data.editor?.aspect && ASPECTS[data.editor.aspect] ? data.editor.aspect : '16:9'
    const [a, b] = ASPECTS[asp]
    const refRatio = a / b
    const out = []
    for (const L of [...(data.layers || [])].sort((p, q) => (p.layer_number || 0) - (q.layer_number || 0))) {
      if (!L.filename) continue
      const size = Number(L.size ?? 100)
      const layer = await makeLayer(L.filename, { name: L.name, type: (L.type || '').toLowerCase() || undefined, size,
        opacity: Number(L.opacity ?? 1), zoom: Number(L.zoom ?? 1), raw: L }, jsonPath)
      const wPct = size, hPct = (size / layer.ar) * refRatio          // box size in % of the video's width / height
      if ('pos_x_pct' in L || 'pos_y_pct' in L) { layer.x = Number(L.pos_x_pct ?? 0); layer.y = Number(L.pos_y_pct ?? 0) }
      else if ((L.mode || 'place') === 'free') {
        const refW = data.editor?.ref_w || REF_W, refH = data.editor?.ref_h || REF_W / refRatio
        layer.x = (Number(L.pos_x || 0) / refW) * 100; layer.y = (Number(L.pos_y || 0) / refH) * 100
      } else {
        const place = (L.place || 'center').toLowerCase()
        const right = 100 - wPct, bottom = 100 - hPct
        const pos = { top_left: [0, 0], top_right: [right, 0], bottom_left: [0, bottom], bottom_right: [right, bottom] }[place]
        ;[layer.x, layer.y] = pos || [right / 2, bottom / 2]
      }
      out.push(layer)
    }
    setAspect(asp)
    setDirection(['forward', 'backward', 'random'].includes(data.sequence_direction) ? data.sequence_direction : 'forward')
    setLayers(out)
    setSelId(out.length ? out[out.length - 1].id : null)
    setLayoutPath(jsonPath)
    setStatus(`Loaded ${out.length} layer${out.length === 1 ? '' : 's'} from ${baseName(jsonPath)}.`)
  }, [makeLayer])

  useEffect(() => {
    if (value && /\.json$/i.test(value)) loadJson(value)
  }, [])   // eslint-disable-line react-hooks/exhaustive-deps

  const addLayer = async () => {
    const picked = await window.electronAPI.openFile([
      { name: 'Images, GIFs and videos', extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'mp4', 'mov', 'webm', 'mkv', 'avi', 'm4v'] },
      { name: 'All Files', extensions: ['*'] }])
    if (!picked) return
    const n = layers.length
    const layer = await makeLayer(picked, { x: 8 + (n * 6) % 40, y: 8 + (n * 6) % 40 })
    setLayers(ls => [...ls, layer])
    setSelId(layer.id)
  }

  const openJson = async () => {
    const picked = await window.electronAPI.openFile([{ name: 'Layout JSON', extensions: ['json'] }])
    if (picked) loadJson(picked)
  }

  // ── Output ───────────────────────────────────────────────────────────────────
  const buildJson = () => ({
    sequence_direction: direction,
    editor: { aspect, ref_w: REF_W, ref_h: Math.round(REF_W / stageRatio) },
    layers: layers.map((l, i) => {
      const { place, ...rest } = l.raw || {}
      return {
        ...rest, layer_number: i + 1, name: l.name, filename: l.filename, type: l.type, mode: 'free',
        pos_x_pct: round(l.x), pos_y_pct: round(l.y),
        pos_x: Math.round((l.x / 100) * REF_W), pos_y: Math.round((l.y / 100) * (REF_W / stageRatio)),
        size: round(l.size), opacity: round(l.opacity), ...(l.zoom > 1 ? { zoom: round(l.zoom) } : {})
      }
    })
  })

  const apply = async () => {
    if (!layers.length) { setStatus('Add at least one layer first.'); return }
    const file = await window.electronAPI.writeLayout(`lagkage-${nodeId || 'layout'}`, buildJson())
    onChange(file)
    onClose()
  }

  // ── Dragging ─────────────────────────────────────────────────────────────────
  const drag = useRef(null)
  const startDrag = (e, layer, mode) => {
    e.preventDefault(); e.stopPropagation()
    setSelId(layer.id)
    e.currentTarget.setPointerCapture?.(e.pointerId)
    drag.current = { mode, id: layer.id, sx: e.clientX, sy: e.clientY, x: layer.x, y: layer.y, size: layer.size }
  }
  const onMove = (e) => {
    const d = drag.current
    if (!d) return
    const dx = ((e.clientX - d.sx) / stage.w) * 100
    const dy = ((e.clientY - d.sy) / stage.h) * 100
    if (d.mode === 'move') update(d.id, { x: round(clamp(d.x + dx, -100, 100), 1), y: round(clamp(d.y + dy, -100, 100), 1) })
    else update(d.id, { size: round(clamp(d.size + dx, 1, 200), 1) })
  }
  const endDrag = () => { drag.current = null }

  useEffect(() => {
    const onKey = (e) => {
      const t = e.target
      const typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT')
      if (e.key === 'Escape') onClose()
      else if ((e.key === 'Delete' || e.key === 'Backspace') && !typing && selId != null) removeLayer(selId)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  const removeLayer = (id) => {
    setLayers(ls => ls.filter(l => l.id !== id))
    setSelId(s => (s === id ? null : s))
  }
  const move = (id, dir) => setLayers(ls => {
    const i = ls.findIndex(l => l.id === id), j = i + dir
    if (i < 0 || j < 0 || j >= ls.length) return ls
    const copy = [...ls]; [copy[i], copy[j]] = [copy[j], copy[i]]
    return copy
  })
  const duplicate = (l) => {
    const copy = { ...l, id: ++uid, name: `${l.name} copy`, x: l.x + 4, y: l.y + 4 }
    setLayers(ls => [...ls, copy]); setSelId(copy.id)
  }
  const anchor = (l, key) => {
    const w = l.size, h = (l.size / l.ar) * stageRatio
    const xs = { left: 0, center: (100 - w) / 2, right: 100 - w }, ys = { top: 0, center: (100 - h) / 2, bottom: 100 - h }
    const [v, hz] = key === 'center' ? ['center', 'center'] : key.includes('_') ? key.split('_') : (['top', 'bottom'].includes(key) ? [key, 'center'] : ['center', key])
    update(l.id, { x: round(xs[hz]), y: round(ys[v]) })
  }

  const sel = layers.find(l => l.id === selId)

  // ── UI ─────────────────────────────────────────────────────────────────────────
  const btn = { padding: '5px 10px', fontSize: 11, fontWeight: 700, background: 'var(--paper)', color: 'var(--ink)',
                border: '2px solid var(--ink)', borderRadius: 6 }
  const field = { padding: '3px 6px', fontSize: 11, width: '100%', background: 'var(--paper)', color: 'var(--ink)',
                  border: '2px solid var(--ink)', borderRadius: 5 }
  const label = { fontSize: 10, color: 'var(--muted-dim)', fontFamily: 'var(--font-mono)' }

  return createPortal(
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(8,8,8,0.55)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', padding: 24 }}
         onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}>
      <div style={{ width: 'min(1100px, 100%)', height: 'min(720px, 100%)', display: 'flex', flexDirection: 'column',
                    background: 'var(--paper)', color: 'var(--ink)', border: 'var(--border)', borderRadius: 'var(--radius)',
                    boxShadow: 'var(--shadow)', overflow: 'hidden' }}>
        {/* header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: 'var(--cyan)',
                      borderBottom: 'var(--border)', color: '#080808' }}>
          <strong style={{ fontFamily: 'var(--font-display)', fontSize: 13, letterSpacing: '0.04em' }}>Lagkage layout</strong>
          <span style={{ fontSize: 11, opacity: 0.8 }}>drag layers onto the video · corner handle resizes</span>
          <span style={{ flex: 1 }} />
          <select className="nodrag" value={aspect} onChange={e => setAspect(e.target.value)} style={{ ...field, width: 78 }}
                  title="Shape of your video (only the preview — positions are saved as percentages)">
            {Object.keys(ASPECTS).map(a => <option key={a}>{a}</option>)}
          </select>
          <select className="nodrag" value={direction} onChange={e => setDirection(e.target.value)} style={{ ...field, width: 96 }}
                  title="Order the layers are stacked: forward = layer 1 at the bottom, backward = reversed, random = shuffled each run">
            <option>forward</option><option>backward</option><option>random</option>
          </select>
          <button style={btn} onClick={openJson}>Open JSON…</button>
          <button style={{ ...btn, background: 'var(--yellow)' }} onClick={apply}>Use this layout</button>
          <button style={btn} onClick={onClose}>✕</button>
        </div>

        <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
          {/* stage */}
          <div ref={areaRef} style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                      background: 'var(--paper-dim)' }}
               onPointerDown={() => setSelId(null)}>
            <div ref={stageRef} onPointerMove={onMove} onPointerUp={endDrag} onPointerCancel={endDrag}
                 style={{ position: 'relative', width: stage.w, height: stage.h, overflow: 'hidden', flexShrink: 0,
                          background: 'repeating-conic-gradient(#2b2b2b 0% 25%, #353535 0% 50%) 50% / 24px 24px',
                          border: '3px solid var(--ink)', boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ position: 'absolute', left: 6, top: 4, fontSize: 10, color: 'rgba(255,255,255,0.55)',
                            fontFamily: 'var(--font-mono)', pointerEvents: 'none' }}>your video · {aspect}</div>
              {layers.map((l, i) => {
                const w = (stage.w * l.size) / 100, h = w / l.ar
                const selected = l.id === selId
                return (
                  <div key={l.id} onPointerDown={e => startDrag(e, l, 'move')}
                       title={`${l.name} (layer ${i + 1})`}
                       style={{ position: 'absolute', left: (stage.w * l.x) / 100, top: (stage.h * l.y) / 100, width: w, height: h,
                                opacity: l.opacity, cursor: 'move', touchAction: 'none',
                                outline: selected ? '2px solid var(--yellow)' : '1px dashed rgba(255,255,255,0.45)', outlineOffset: 1 }}>
                    {l.dataUrl
                      ? <img src={l.dataUrl} alt="" draggable={false}
                             style={{ width: '100%', height: '100%', display: 'block', pointerEvents: 'none',
                                      objectFit: 'cover', transform: `scale(${l.zoom})` }} />
                      : <div style={{ width: '100%', height: '100%', background: 'rgba(50,185,223,0.55)', color: '#080808', display: 'flex',
                                      alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, pointerEvents: 'none',
                                      overflow: 'hidden', textAlign: 'center' }}>▶ {l.name}</div>}
                    {selected && (
                      <div onPointerDown={e => startDrag(e, l, 'resize')} title="Drag to resize"
                           style={{ position: 'absolute', right: -7, bottom: -7, width: 14, height: 14, background: 'var(--yellow)',
                                    border: '2px solid #080808', borderRadius: 3, cursor: 'nwse-resize', touchAction: 'none' }} />
                    )}
                  </div>
                )
              })}
              {!layers.length && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                              color: 'rgba(255,255,255,0.7)', fontSize: 12, textAlign: 'center', padding: 20, pointerEvents: 'none' }}>
                  Click “＋ Add layer” to place an image, GIF or video on top of your video.
                </div>
              )}
            </div>
          </div>

          {/* side panel */}
          <div style={{ width: 290, borderLeft: 'var(--border)', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div style={{ padding: 8, borderBottom: '2px solid var(--ink)' }}>
              <button style={{ ...btn, width: '100%', background: 'var(--lime-bright)', color: '#080808' }} onClick={addLayer}>＋ Add layer (image / GIF / video)</button>
            </div>
            <div style={{ flex: 1, overflow: 'auto', minHeight: 80 }}>
              {[...layers].reverse().map(l => {
                const idx = layers.findIndex(x => x.id === l.id)
                return (
                  <div key={l.id} onClick={() => setSelId(l.id)}
                       style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '5px 8px', fontSize: 11,
                                background: l.id === selId ? 'var(--yellow)' : 'transparent', color: l.id === selId ? '#080808' : 'var(--ink)',
                                borderBottom: '1px solid var(--gray)' }}>
                    <span style={{ opacity: 0.6, width: 14 }}>{idx + 1}</span>
                    <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {l.type === 'video' ? '🎞 ' : l.type === 'gif' ? '✨ ' : '🖼 '}{l.name}
                    </span>
                    <button style={{ ...btn, padding: '0 5px', fontSize: 10 }} title="Bring forward" onClick={e => { e.stopPropagation(); move(l.id, 1) }}>▲</button>
                    <button style={{ ...btn, padding: '0 5px', fontSize: 10 }} title="Send back" onClick={e => { e.stopPropagation(); move(l.id, -1) }}>▼</button>
                  </div>
                )
              })}
              {!layers.length && <div style={{ padding: 12, fontSize: 11, color: 'var(--muted)' }}>No layers yet. Layers higher in this list sit on top.</div>}
            </div>

            {sel && (
              <div style={{ borderTop: '2px solid var(--ink)', padding: 8, display: 'flex', flexDirection: 'column', gap: 6, overflow: 'auto', maxHeight: '55%' }}>
                <div><div style={label}>Name</div><input className="nodrag" style={field} value={sel.name} onChange={e => update(sel.id, { name: e.target.value })} /></div>
                <div><div style={label}>Opacity {Math.round(sel.opacity * 100)}%</div>
                  <input className="nodrag" type="range" min={0} max={1} step={0.01} value={sel.opacity} style={{ width: '100%', accentColor: 'var(--purple)' }}
                         onChange={e => update(sel.id, { opacity: Number(e.target.value) })} /></div>
                <div><div style={label}>Size {round(sel.size, 1)}% of video width</div>
                  <input className="nodrag" type="range" min={1} max={150} step={0.5} value={Math.min(150, sel.size)} style={{ width: '100%', accentColor: 'var(--purple)' }}
                         onChange={e => update(sel.id, { size: Number(e.target.value) })} /></div>
                <div><div style={label}>Zoom into it ×{round(sel.zoom, 2)}</div>
                  <input className="nodrag" type="range" min={1} max={4} step={0.05} value={sel.zoom} style={{ width: '100%', accentColor: 'var(--purple)' }}
                         onChange={e => update(sel.id, { zoom: Number(e.target.value) })} /></div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <div style={{ flex: 1 }}><div style={label}>X %</div>
                    <input className="nodrag" type="number" step={0.5} style={field} value={round(sel.x, 1)} onChange={e => update(sel.id, { x: Number(e.target.value) })} /></div>
                  <div style={{ flex: 1 }}><div style={label}>Y %</div>
                    <input className="nodrag" type="number" step={0.5} style={field} value={round(sel.y, 1)} onChange={e => update(sel.id, { y: Number(e.target.value) })} /></div>
                </div>
                <div>
                  <div style={label}>Snap to</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 30px)', gap: 3 }}>
                    {ANCHORS.map(([k, ch]) => <button key={k} style={{ ...btn, padding: 0, height: 24 }} title={k.replace('_', ' ')} onClick={() => anchor(sel, k)}>{ch}</button>)}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button style={btn} onClick={() => duplicate(sel)}>Duplicate</button>
                  <button style={{ ...btn, background: 'var(--coral)', color: '#080808' }} onClick={() => removeLayer(sel.id)}>Delete</button>
                </div>
                <div style={{ fontSize: 10, color: 'var(--muted)', wordBreak: 'break-all' }} title={sel.filename}>{sel.filename}</div>
              </div>
            )}
          </div>
        </div>

        <div style={{ padding: '4px 12px', fontSize: 10, color: 'var(--muted-dim)', fontFamily: 'var(--font-mono)', borderTop: '2px solid var(--ink)', minHeight: 22 }}>
          {status || (layoutPath ? `Editing ${baseName(layoutPath)}` : 'Positions are saved as percentages, so the layout works at any resolution. Videos show as blue tiles.')}
        </div>
      </div>
    </div>,
    document.body
  )
}
