import React, { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { lockModal } from '../../useModalLock'

/**
 * Key-colour picker: shows a frame of the video; click the screen colour (or the colour to remove) to sample it.
 * Writes `key_color` and turns off auto-detect. Works for any color field (the `onChange` is the field's own).
 */
export default function KeyColorPicker({ value, onChange, onClose, inputPath }) {
  const [path, setPath] = useState(inputPath || '')
  const [t, setT] = useState(0)
  const [frame, setFrame] = useState(null)
  const [busy, setBusy] = useState(false)
  const [picked, setPicked] = useState(/^#[0-9a-fA-F]{6}$/.test(value || '') ? value.toUpperCase() : null)
  const [hover, setHover] = useState(null)
  const canvasRef = useRef(null)

  useEffect(() => lockModal(), [])
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); onClose() }
      else if (!(e.target && ['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName))) e.stopPropagation()
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [onClose])

  useEffect(() => {
    if (!path) return
    let cancelled = false
    setBusy(true)
    window.electronAPI.grabFrame(path, t).then(url => { if (!cancelled) { setFrame(url); setBusy(false) } })
    return () => { cancelled = true }
  }, [path, t])

  useEffect(() => {
    if (!frame || !canvasRef.current) return
    const img = new Image()
    img.onload = () => {
      const c = canvasRef.current
      c.width = img.naturalWidth; c.height = img.naturalHeight
      c.getContext('2d', { willReadFrequently: true }).drawImage(img, 0, 0)
    }
    img.src = frame
  }, [frame])

  const sample = (e) => {
    const c = canvasRef.current
    const r = c.getBoundingClientRect()
    const x = Math.floor(((e.clientX - r.left) / r.width) * c.width)
    const y = Math.floor(((e.clientY - r.top) / r.height) * c.height)
    // average a 5×5 neighbourhood so a single noisy pixel doesn't set the key
    const d = c.getContext('2d').getImageData(Math.max(0, x - 2), Math.max(0, y - 2), 5, 5).data
    let R = 0, G = 0, B = 0, n = 0
    for (let i = 0; i < d.length; i += 4) { R += d[i]; G += d[i + 1]; B += d[i + 2]; n++ }
    const hex = '#' + [R, G, B].map(v => Math.round(v / n).toString(16).padStart(2, '0')).join('').toUpperCase()
    return hex
  }

  const browse = async () => {
    const p = await window.electronAPI.openFile([{ name: 'Videos / images', extensions: ['mp4', 'mov', 'm4v', 'mkv', 'webm', 'avi', 'png', 'jpg'] }, { name: 'All Files', extensions: ['*'] }])
    if (p) setPath(p)
  }
  const btn = { padding: '5px 12px', fontSize: 12, fontWeight: 700 }

  return createPortal(
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(8,8,8,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
         onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}>
      <div style={{ width: 'min(820px, 100%)', background: 'var(--paper)', color: 'var(--ink)', border: 'var(--border)', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 14px', background: 'var(--lime-bright)', color: '#080808', borderBottom: 'var(--border)' }}>
          <strong style={{ fontFamily: 'var(--font-display)', fontSize: 13 }}>Pick the color to remove</strong>
          <span style={{ fontSize: 11 }}>click the screen (green / blue / the color you want gone)</span>
          <span style={{ flex: 1 }} />
          <button onClick={onClose} style={{ padding: '2px 9px' }}>✕</button>
        </div>
        <div style={{ padding: 14 }}>
          {!path ? (
            <div style={{ textAlign: 'center', padding: 24 }}>
              <p style={{ fontSize: 13, marginBottom: 12 }}>Choose a video (or connect an Input node with a file to this program first).</p>
              <button onClick={browse} style={{ ...btn, background: 'var(--yellow)', color: '#080808' }}>Browse…</button>
            </div>
          ) : (
            <>
              <div style={{ background: '#000', border: '2px solid var(--ink)', borderRadius: 8, display: 'flex', justifyContent: 'center', minHeight: 120, position: 'relative' }}>
                <canvas ref={canvasRef} onClick={e => setPicked(sample(e))} onMouseMove={e => setHover(sample(e))} onMouseLeave={() => setHover(null)}
                        style={{ maxWidth: '100%', maxHeight: 420, cursor: 'crosshair', display: frame ? 'block' : 'none' }} />
                {busy && <span style={{ position: 'absolute', top: 8, left: 10, color: '#fff', fontSize: 11 }}>Loading frame…</span>}
              </div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 10 }}>
                <label style={{ fontSize: 11 }}>Frame at (s)
                  <input type="number" min={0} step={0.5} value={t} onChange={e => setT(Math.max(0, Number(e.target.value) || 0))} style={{ width: 80, marginLeft: 6, padding: '3px 6px' }} />
                </label>
                <button onClick={browse} style={btn}>Other video…</button>
                <span style={{ flex: 1 }} />
                <span style={{ fontSize: 11, color: 'var(--muted-dim)' }}>under cursor</span>
                <span style={{ width: 22, height: 22, border: '2px solid var(--ink)', borderRadius: 4, background: hover || 'transparent' }} />
                <b style={{ fontFamily: 'var(--font-mono)', fontSize: 12, width: 70 }}>{hover || '—'}</b>
                <span style={{ fontSize: 11, color: 'var(--muted-dim)' }}>picked</span>
                <span style={{ width: 28, height: 28, border: '2px solid var(--ink)', borderRadius: 4, background: picked || 'transparent' }} />
                <b style={{ fontFamily: 'var(--font-mono)', fontSize: 12, width: 70 }}>{picked || '—'}</b>
              </div>
            </>
          )}
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '0 14px 14px' }}>
          <button onClick={onClose} style={btn}>Cancel</button>
          <button disabled={!picked} onClick={() => { onChange(picked); onClose() }} style={{ ...btn, background: 'var(--yellow)', color: '#080808' }}>Use this color</button>
        </div>
      </div>
    </div>,
    document.body
  )
}
