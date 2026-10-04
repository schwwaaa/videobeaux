import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { lockModal } from '../../useModalLock'

/**
 * Lagkage layout editor — a crude canvas for placing images / GIFs / videos on a stand-in for the base video,
 * then turning that into the layout JSON lagkage reads. Positions and sizes are stored as percentages of the
 * video, so a layout works at any resolution.
 *
 * Layers can be moved, resized freely (corners keep the aspect ratio, Shift or the edge handles stretch),
 * rotated, blurred; files can be dropped on the canvas; arrow keys nudge the selected layer.
 */

const ASPECTS = { '16:9': [16, 9], '9:16': [9, 16], '1:1': [1, 1], '4:3': [4, 3], '21:9': [21, 9] }
const REF_W = 1920                                  // only used to write readable pixel positions
const VIDEO_EXT = new Set(['mp4', 'mov', 'webm', 'mkv', 'avi', 'm4v', 'mpg', 'mpeg'])
const MEDIA_EXT = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', ...VIDEO_EXT])
const ANCHORS = [['top_left', '↖'], ['top', '↑'], ['top_right', '↗'],
                 ['left', '←'], ['center', '●'], ['right', '→'],
                 ['bottom_left', '↙'], ['bottom', '↓'], ['bottom_right', '↘']]
// resize handles: [key, hx, hy, cursor] — hx/hy are -1/0/1 (which edge(s) the handle moves)
const HANDLES = [['nw', -1, -1, 'nwse-resize'], ['n', 0, -1, 'ns-resize'], ['ne', 1, -1, 'nesw-resize'],
                 ['w', -1, 0, 'ew-resize'], ['e', 1, 0, 'ew-resize'],
                 ['sw', -1, 1, 'nesw-resize'], ['s', 0, 1, 'ns-resize'], ['se', 1, 1, 'nwse-resize']]
const round = (n, d = 2) => Math.round(n * 10 ** d) / 10 ** d
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n))
const ext = (p) => (p.split('.').pop() || '').toLowerCase()
const baseName = (p) => (p || '').split(/[\\/]/).pop()
let uid = 0

function typeFor(path) {
  const e = ext(path)
  if (e === 'gif') return 'gif'
  return VIDEO_EXT.has(e) ? 'video' : 'img'
}

export default function LagkageEditor({ value, onChange, onClose, nodeId }) {
  const [layers, setLayers] = useState([])
  const [selId, setSelId] = useState(null)
  const [aspect, setAspect] = useState('16:9')
  const [direction, setDirection] = useState('forward')
  const [status, setStatus] = useState('')
  const [layoutPath, setLayoutPath] = useState(null)
  const [stage, setStage] = useState({ w: 640, h: 360 })
  const [dropping, setDropping] = useState(false)
  const areaRef = useRef(null)
  const stageRef = useRef(null)

  const [aw, ah] = ASPECTS[aspect]
  const stageRatio = aw / ah
  // height (in % of the video's height) of a box that is `w` % of its width and has aspect `ar` (w / h)
  const hFromW = useCallback((w, ar, ratio = stageRatio) => (w / ar) * ratio, [stageRatio])

  // The canvas underneath must not see the keyboard while this window is open.
  useEffect(() => lockModal(), [])

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

  // Aspect-locked layers keep their picture shape when the stage shape changes.
  const changeAspect = (next) => {
    const [a, b] = ASPECTS[next]
    setLayers(ls => ls.map(l => (l.lock ? { ...l, h: (l.w / l.ar) * (a / b) } : l)))
    setAspect(next)
  }

  // ── Loading ────────────────────────────────────────────────────────────────
  const makeLayer = useCallback(async (filename, extra = {}, jsonPath = null, ratio = stageRatio) => {
    const probe = await window.electronAPI.probeMedia(filename, jsonPath)
    const type = extra.type || typeFor(filename)
    const dataUrl = type === 'video' ? null : await window.electronAPI.readImageDataUrl(filename, jsonPath)
    const ar = probe && probe.width && probe.height ? probe.width / probe.height : 1
    const w = extra.w ?? 25
    return {
      id: ++uid, name: extra.name || baseName(filename).replace(/\.[^.]+$/, ''), filename, type, ar, dataUrl,
      x: 10, y: 10, w, h: extra.h ?? (w / ar) * ratio, lock: true, rotation: 0, blur: 0, opacity: 1, zoom: 1, raw: {}, ...extra
    }
  }, [stageRatio])

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
      const w = Number(L.size ?? 100)
      const layer = await makeLayer(L.filename, {
        name: L.name, type: (L.type || '').toLowerCase() || undefined, w,
        opacity: Number(L.opacity ?? 1), zoom: Number(L.zoom ?? 1), rotation: Number(L.rotate ?? 0), blur: Number(L.blur ?? 0), raw: L
      }, jsonPath, refRatio)
      if (L.height_pct != null) {
        layer.h = Number(L.height_pct)
        layer.lock = Math.abs(layer.h - (w / layer.ar) * refRatio) < 0.5      // stretched layouts open unlocked
      }
      const wPct = w, hPct = layer.h
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

  const addPaths = async (paths, at = null) => {
    const made = []
    for (const path of paths) {
      const n = layers.length + made.length
      const layer = await makeLayer(path, { x: 8 + (n * 6) % 40, y: 8 + (n * 6) % 40 })
      if (at) { layer.x = round(at.x - layer.w / 2 + made.length * 3, 1); layer.y = round(at.y - layer.h / 2 + made.length * 3, 1) }
      made.push(layer)
    }
    if (!made.length) return
    setLayers(ls => [...ls, ...made])
    setSelId(made[made.length - 1].id)
  }

  const addLayer = async () => {
    const picked = await window.electronAPI.openFile([
      { name: 'Images, GIFs and videos', extensions: [...MEDIA_EXT] }, { name: 'All Files', extensions: ['*'] }])
    if (picked) addPaths([picked])
  }

  const openJson = async () => {
    const picked = await window.electronAPI.openFile([{ name: 'Layout JSON', extensions: ['json'] }])
    if (picked) loadJson(picked)
  }

  // ── Drag-and-drop of files onto the canvas ──────────────────────────────────────
  const onDragOver = (e) => {
    if (!e.dataTransfer?.types?.includes('Files')) return
    e.preventDefault(); e.stopPropagation()
    e.dataTransfer.dropEffect = 'copy'
    setDropping(true)
  }
  const onDrop = (e) => {
    e.preventDefault(); e.stopPropagation()     // stopPropagation: React portals would otherwise bubble this to the canvas's own onDrop
    setDropping(false)
    const files = Array.from(e.dataTransfer?.files || [])
    const paths = files.map(f => window.electronAPI.pathForFile(f)).filter(p => p && MEDIA_EXT.has(ext(p)))
    if (!paths.length) { setStatus('Drop image, GIF or video files to add layers.'); return }
    const rect = stageRef.current.getBoundingClientRect()
    const inside = e.clientX >= rect.left && e.clientX <= rect.right && e.clientY >= rect.top && e.clientY <= rect.bottom
    addPaths(paths, inside ? { x: ((e.clientX - rect.left) / rect.width) * 100, y: ((e.clientY - rect.top) / rect.height) * 100 } : null)
  }

  // ── Output ───────────────────────────────────────────────────────────────────
  const buildJson = () => ({
    sequence_direction: direction,
    editor: { aspect, ref_w: REF_W, ref_h: Math.round(REF_W / stageRatio) },
    layers: layers.map((l, i) => {
      const { place, ...rest } = l.raw || {}
      const out = {
        ...rest, layer_number: i + 1, name: l.name, filename: l.filename, type: l.type, mode: 'free',
        pos_x_pct: round(l.x), pos_y_pct: round(l.y),
        pos_x: Math.round((l.x / 100) * REF_W), pos_y: Math.round((l.y / 100) * (REF_W / stageRatio)),
        size: round(l.w), height_pct: round(l.h), opacity: round(l.opacity)
      }
      for (const k of ['zoom', 'rotate', 'blur']) delete out[k]
      if (l.zoom > 1) out.zoom = round(l.zoom)
      if (Math.abs(l.rotation) > 0.01) out.rotate = round(l.rotation, 1)
      if (l.blur > 0.01) out.blur = round(l.blur, 2)
      return out
    })
  })

  const apply = async () => {
    if (!layers.length) { setStatus('Add at least one layer first.'); return }
    const file = await window.electronAPI.writeLayout(`lagkage-${nodeId || 'layout'}`, buildJson())
    onChange(file)
    onClose()
  }

  // ── Pointer interactions: move / resize / rotate ──────────────────────────────────
  const drag = useRef(null)
  const startDrag = (e, layer, mode, handle = null) => {
    e.preventDefault(); e.stopPropagation()
    setSelId(layer.id)
    e.currentTarget.setPointerCapture?.(e.pointerId)
    drag.current = { mode, handle, id: layer.id, sx: e.clientX, sy: e.clientY, layer: { ...layer }, W: stage.w, H: stage.h }
  }
  const onMove = (e) => {
    const d = drag.current
    if (!d) return
    const { layer: l0, W, H } = d
    const dx = e.clientX - d.sx, dy = e.clientY - d.sy
    if (d.mode === 'move') {
      update(d.id, { x: round(clamp(l0.x + (dx / W) * 100, -150, 150), 1), y: round(clamp(l0.y + (dy / H) * 100, -150, 150), 1) })
      return
    }
    const th = (l0.rotation * Math.PI) / 180, cos = Math.cos(th), sin = Math.sin(th)
    const w0 = (l0.w / 100) * W, h0 = (l0.h / 100) * H
    const c0 = { x: (l0.x / 100) * W + w0 / 2, y: (l0.y / 100) * H + h0 / 2 }
    if (d.mode === 'rotate') {
      const rect = stageRef.current.getBoundingClientRect()
      const px = e.clientX - rect.left - c0.x, py = e.clientY - rect.top - c0.y
      let deg = (Math.atan2(py, px) * 180) / Math.PI + 90
      deg = ((deg + 180) % 360 + 360) % 360 - 180
      if (e.shiftKey) deg = Math.round(deg / 15) * 15
      update(d.id, { rotation: round(deg, 1) })
      return
    }
    // resize: express the pointer movement in the layer's own (rotated) axes
    const [, hx, hy] = HANDLES.find(h => h[0] === d.handle)
    const dxl = dx * cos + dy * sin, dyl = -dx * sin + dy * cos
    const minPx = 8
    let nw = hx ? Math.max(minPx, w0 + hx * dxl) : w0
    let nh = hy ? Math.max(minPx, h0 + hy * dyl) : h0
    const corner = hx !== 0 && hy !== 0
    const keepRatio = corner && (l0.lock !== e.shiftKey)         // lock on: corners keep the shape, Shift stretches; lock off: the reverse
    if (keepRatio) { const s = Math.max(nw / w0, nh / h0); nw = w0 * s; nh = h0 * s }
    const sx = (hx * (nw - w0)) / 2, sy = (hy * (nh - h0)) / 2     // centre moves so the opposite edge stays put
    const c = { x: c0.x + sx * cos - sy * sin, y: c0.y + sx * sin + sy * cos }
    update(d.id, {
      w: round((nw / W) * 100, 2), h: round((nh / H) * 100, 2),
      x: round(((c.x - nw / 2) / W) * 100, 2), y: round(((c.y - nh / 2) / H) * 100, 2),
      ...(!corner ? { lock: false } : {})
    })
  }
  const endDrag = () => { drag.current = null }

  const removeLayer = useCallback((id) => {
    setLayers(ls => ls.filter(l => l.id !== id))
    setSelId(s => (s === id ? null : s))
  }, [])

  // ── Keyboard: the editor owns it while open ──────────────────────────────────────
  const selRef = useRef(null)
  selRef.current = selId
  useEffect(() => {
    const onKey = (e) => {
      const t = e.target
      const typing = t && (t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' ||
        (t.tagName === 'INPUT' && !['range', 'checkbox', 'radio', 'button'].includes(t.type)))
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); onClose(); return }
      if (typing) return                                  // let text/number fields work normally
      const arrows = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }
      if (e.key === 'Delete' || e.key === 'Backspace') {
        e.preventDefault(); e.stopPropagation()
        if (selRef.current != null) removeLayer(selRef.current)
      } else if (arrows[e.key]) {
        e.preventDefault(); e.stopPropagation()
        const step = e.shiftKey ? 5 : e.altKey ? 0.1 : 0.5
        const [dx, dy] = arrows[e.key]
        if (selRef.current != null) {
          setLayers(ls => ls.map(l => (l.id === selRef.current
            ? { ...l, x: round(l.x + dx * step, 2), y: round(l.y + dy * step, 2) } : l)))
        }
      } else if (e.metaKey || e.ctrlKey) {
        e.stopPropagation()                                // ⌘A / ⌘C / ⌘V / ⌘D / ⌘Z belong to the canvas, which is locked
      }
    }
    window.addEventListener('keydown', onKey, true)       // capture: runs before React Flow's document listener
    return () => window.removeEventListener('keydown', onKey, true)
  }, [onClose, removeLayer])

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
    const xs = { left: 0, center: (100 - l.w) / 2, right: 100 - l.w }, ys = { top: 0, center: (100 - l.h) / 2, bottom: 100 - l.h }
    const [v, hz] = key === 'center' ? ['center', 'center'] : key.includes('_') ? key.split('_') : (['top', 'bottom'].includes(key) ? [key, 'center'] : ['center', key])
    update(l.id, { x: round(xs[hz]), y: round(ys[v]) })
  }
  const setW = (l, w) => update(l.id, l.lock ? { w, h: round((w / l.ar) * stageRatio, 2) } : { w })
  const setH = (l, h) => update(l.id, l.lock ? { h, w: round((h * l.ar) / stageRatio, 2) } : { h })
  const resetShape = (l) => update(l.id, { h: round((l.w / l.ar) * stageRatio, 2), lock: true, rotation: 0 })

  const sel = layers.find(l => l.id === selId)

  // ── UI ─────────────────────────────────────────────────────────────────────────
  const btn = { padding: '5px 10px', fontSize: 11, fontWeight: 700, background: 'var(--paper)', color: 'var(--ink)',
                border: '2px solid var(--ink)', borderRadius: 6 }
  const field = { padding: '3px 6px', fontSize: 11, width: '100%', background: 'var(--paper)', color: 'var(--ink)',
                  border: '2px solid var(--ink)', borderRadius: 5 }
  const label = { fontSize: 10, color: 'var(--muted-dim)', fontFamily: 'var(--font-mono)' }
  const slider = { width: '100%', accentColor: 'var(--slider)' }
  const blurOnRelease = (e) => e.currentTarget.blur()       // so arrow keys keep nudging the layer, not the slider

  return createPortal(
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(8,8,8,0.55)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', padding: 24 }}
         onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}
         onDragOver={onDragOver} onDragLeave={() => setDropping(false)} onDrop={onDrop}>
      <div style={{ width: 'min(1100px, 100%)', height: 'min(720px, 100%)', display: 'flex', flexDirection: 'column',
                    background: 'var(--paper)', color: 'var(--ink)', border: 'var(--border)', borderRadius: 'var(--radius)',
                    boxShadow: 'var(--shadow)', overflow: 'hidden' }}>
        {/* header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: 'var(--cyan)',
                      borderBottom: 'var(--border)', color: '#080808' }}>
          <strong style={{ fontFamily: 'var(--font-display)', fontSize: 13, letterSpacing: '0.04em' }}>Lagkage layout</strong>
          <span style={{ fontSize: 11, opacity: 0.85 }}>drop files here · drag to move · handles resize (Shift stretches) · arrows nudge · Delete removes</span>
          <span style={{ flex: 1 }} />
          <select className="nodrag" value={aspect} onChange={e => changeAspect(e.target.value)} style={{ ...field, width: 78 }}
                  title="Shape of your video (only the preview — positions are saved as percentages)">
            {Object.keys(ASPECTS).map(a => <option key={a}>{a}</option>)}
          </select>
          <select className="nodrag" value={direction} onChange={e => setDirection(e.target.value)} style={{ ...field, width: 96 }}
                  title="Order the layers are stacked: forward = layer 1 at the bottom, backward = reversed, random = shuffled each run">
            <option>forward</option><option>backward</option><option>random</option>
          </select>
          <button style={btn} onClick={openJson}>Open JSON…</button>
          <button style={{ ...btn, background: 'var(--yellow)', color: '#080808' }} onClick={apply}>Use this layout</button>
          <button style={btn} onClick={onClose}>✕</button>
        </div>

        <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
          {/* stage */}
          <div ref={areaRef} style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                      background: 'var(--paper-dim)', outline: dropping ? '3px dashed var(--cyan)' : 'none', outlineOffset: -6 }}
               onPointerDown={() => setSelId(null)}>
            <div ref={stageRef} onPointerMove={onMove} onPointerUp={endDrag} onPointerCancel={endDrag}
                 style={{ position: 'relative', width: stage.w, height: stage.h, overflow: 'hidden', flexShrink: 0,
                          background: 'repeating-conic-gradient(#2b2b2b 0% 25%, #353535 0% 50%) 50% / 24px 24px',
                          border: '3px solid var(--ink)', boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ position: 'absolute', left: 6, top: 4, fontSize: 10, color: 'rgba(255,255,255,0.55)',
                            fontFamily: 'var(--font-mono)', pointerEvents: 'none' }}>your video · {aspect}</div>
              {layers.map((l, i) => {
                const selected = l.id === selId
                const handleSize = 10
                return (
                  <div key={l.id} onPointerDown={e => startDrag(e, l, 'move')} title={`${l.name} (layer ${i + 1})`}
                       style={{ position: 'absolute', left: (stage.w * l.x) / 100, top: (stage.h * l.y) / 100,
                                width: (stage.w * l.w) / 100, height: (stage.h * l.h) / 100,
                                transform: `rotate(${l.rotation}deg)`, transformOrigin: '50% 50%',
                                opacity: l.opacity, cursor: 'move', touchAction: 'none',
                                outline: selected ? '2px solid var(--yellow)' : '1px dashed rgba(255,255,255,0.45)', outlineOffset: 1 }}>
                    <div style={{ width: '100%', height: '100%', overflow: 'hidden', pointerEvents: 'none',
                                  filter: l.blur > 0 ? `blur(${(stage.w * l.blur) / 100}px)` : 'none' }}>
                      {l.dataUrl
                        ? <img src={l.dataUrl} alt="" draggable={false}
                               style={{ width: '100%', height: '100%', display: 'block', objectFit: 'fill', transform: `scale(${l.zoom})` }} />
                        : <div style={{ width: '100%', height: '100%', background: 'rgba(50,185,223,0.55)', color: '#080808', display: 'flex',
                                        alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, textAlign: 'center' }}>▶ {l.name}</div>}
                    </div>
                    {selected && HANDLES.map(([key, hx, hy, cursor]) => (
                      <div key={key} onPointerDown={e => startDrag(e, l, 'resize', key)}
                           title={hx && hy ? 'Resize (Shift = free stretch)' : 'Stretch'}
                           style={{ position: 'absolute', width: handleSize, height: handleSize, background: 'var(--yellow)',
                                    border: '2px solid #080808', borderRadius: 2, cursor, touchAction: 'none',
                                    left: `calc(${(hx + 1) * 50}% - ${handleSize / 2}px)`, top: `calc(${(hy + 1) * 50}% - ${handleSize / 2}px)` }} />
                    ))}
                    {selected && (
                      <>
                        <div style={{ position: 'absolute', left: '50%', top: -22, width: 2, height: 20, background: '#ffe500', marginLeft: -1, pointerEvents: 'none' }} />
                        <div onPointerDown={e => startDrag(e, l, 'rotate')} title="Rotate (Shift = 15° steps)"
                             style={{ position: 'absolute', left: '50%', top: -34, width: 14, height: 14, marginLeft: -7, borderRadius: '50%',
                                      background: 'var(--cyan)', border: '2px solid #080808', cursor: 'grab', touchAction: 'none' }} />
                      </>
                    )}
                  </div>
                )
              })}
              {!layers.length && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                              color: 'rgba(255,255,255,0.75)', fontSize: 12, textAlign: 'center', padding: 20, pointerEvents: 'none' }}>
                  Drop an image, GIF or video here — or click “＋ Add layer”.
                </div>
              )}
            </div>
          </div>

          {/* side panel */}
          <div style={{ width: 300, borderLeft: 'var(--border)', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
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
              <div style={{ borderTop: '2px solid var(--ink)', padding: 8, display: 'flex', flexDirection: 'column', gap: 6, overflow: 'auto', maxHeight: '62%' }}>
                <div><div style={label}>Name</div><input className="nodrag" style={field} value={sel.name} onChange={e => update(sel.id, { name: e.target.value })} /></div>
                <div style={{ display: 'flex', gap: 6, alignItems: 'flex-end' }}>
                  <div style={{ flex: 1 }}><div style={label}>Width %</div>
                    <input className="nodrag" type="number" step={0.5} style={field} value={round(sel.w, 1)} onChange={e => setW(sel, Math.max(1, Number(e.target.value)))} /></div>
                  <div style={{ flex: 1 }}><div style={label}>Height %</div>
                    <input className="nodrag" type="number" step={0.5} style={field} value={round(sel.h, 1)} onChange={e => setH(sel, Math.max(1, Number(e.target.value)))} /></div>
                  <label title="On: width and height change together (corner handles keep the shape). Off: free stretch." style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: 10, paddingBottom: 4 }}>
                    <input type="checkbox" checked={sel.lock} onChange={e => update(sel.id, { lock: e.target.checked, ...(e.target.checked ? { h: round((sel.w / sel.ar) * stageRatio, 2) } : {}) })} />
                    lock
                  </label>
                </div>
                <div><div style={label}>Rotate {round(sel.rotation, 1)}°</div>
                  <input className="nodrag" type="range" min={-180} max={180} step={1} value={sel.rotation} style={slider}
                         onChange={e => update(sel.id, { rotation: Number(e.target.value) })} onPointerUp={blurOnRelease} /></div>
                <div><div style={label}>Blur {round(sel.blur, 1)}% of width</div>
                  <input className="nodrag" type="range" min={0} max={20} step={0.1} value={sel.blur} style={slider}
                         onChange={e => update(sel.id, { blur: Number(e.target.value) })} onPointerUp={blurOnRelease} /></div>
                <div><div style={label}>Opacity {Math.round(sel.opacity * 100)}%</div>
                  <input className="nodrag" type="range" min={0} max={1} step={0.01} value={sel.opacity} style={slider}
                         onChange={e => update(sel.id, { opacity: Number(e.target.value) })} onPointerUp={blurOnRelease} /></div>
                <div><div style={label}>Zoom into it ×{round(sel.zoom, 2)}</div>
                  <input className="nodrag" type="range" min={1} max={4} step={0.05} value={sel.zoom} style={slider}
                         onChange={e => update(sel.id, { zoom: Number(e.target.value) })} onPointerUp={blurOnRelease} /></div>
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
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <button style={btn} onClick={() => resetShape(sel)} title="Back to the picture's own shape, unrotated">Reset shape</button>
                  <button style={btn} onClick={() => duplicate(sel)}>Duplicate</button>
                  <button style={{ ...btn, background: 'var(--coral)', color: '#080808' }} onClick={() => removeLayer(sel.id)}>Delete</button>
                </div>
                <div style={{ fontSize: 10, color: 'var(--muted)', wordBreak: 'break-all' }} title={sel.filename}>{sel.filename}</div>
              </div>
            )}
          </div>
        </div>

        <div style={{ padding: '4px 12px', fontSize: 10, color: 'var(--muted-dim)', fontFamily: 'var(--font-mono)', borderTop: '2px solid var(--ink)', minHeight: 22 }}>
          {status || (layoutPath ? `Editing ${baseName(layoutPath)}` : 'Positions and sizes are saved as percentages, so the layout works at any resolution. Videos show as blue tiles.')}
        </div>
      </div>
    </div>,
    document.body
  )
}
