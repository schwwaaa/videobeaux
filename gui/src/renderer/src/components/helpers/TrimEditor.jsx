import React, { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { lockModal } from '../../useModalLock'

/**
 * QuickTime-style trim: play the clip, drag the in / out handles on the timeline (or press I / O), step frames
 * with ← / →, then "Use this range". Writes `start` and `end` (seconds). Playback uses vbmedia:// (see main/index.js).
 */
const fmt = (t) => {
  if (!Number.isFinite(t)) return '0:00.000'
  const m = Math.floor(t / 60), s = t - m * 60
  return `${m}:${s.toFixed(3).padStart(6, '0')}`
}
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n))

export default function TrimEditor({ values, setArgs, onClose, inputPath }) {
  const [path, setPath] = useState(inputPath || '')
  const [dur, setDur] = useState(0)
  const [inT, setInT] = useState(Number(values.start) || 0)
  const [outT, setOutT] = useState(values.end !== undefined && values.end !== '' && Number.isFinite(Number(values.end)) ? Number(values.end) : null)
  const [now, setNow] = useState(0)
  const [playing, setPlaying] = useState(false)
  const videoRef = useRef(null)
  const trackRef = useRef(null)
  const drag = useRef(null)
  const out = outT ?? dur

  useEffect(() => lockModal(), [])

  const seek = (t) => {
    const v = videoRef.current
    if (!v) return
    v.currentTime = clamp(t, 0, dur || v.duration || 0)
    setNow(v.currentTime)
  }
  const togglePlay = () => {
    const v = videoRef.current
    if (!v) return
    if (v.paused) {
      if (v.currentTime < inT || v.currentTime >= out - 0.05) v.currentTime = inT
      v.play()
    } else v.pause()
  }
  const step = (frames) => seek((videoRef.current?.currentTime || 0) + frames / 30)

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); onClose(); return }
      if (e.target && ['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return
      e.stopPropagation()
      if (e.key === ' ') { e.preventDefault(); togglePlay() }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); step(e.shiftKey ? -10 : -1) }
      else if (e.key === 'ArrowRight') { e.preventDefault(); step(e.shiftKey ? 10 : 1) }
      else if (e.key.toLowerCase() === 'i') setInT(Math.min(videoRef.current?.currentTime || 0, out - 0.05))
      else if (e.key.toLowerCase() === 'o') setOutT(Math.max(videoRef.current?.currentTime || 0, inT + 0.05))
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  })

  const timeAt = (e) => {
    const r = trackRef.current.getBoundingClientRect()
    return clamp((e.clientX - r.left) / r.width, 0, 1) * dur
  }
  const startDrag = (e, which) => {
    e.preventDefault(); e.stopPropagation()
    e.currentTarget.setPointerCapture?.(e.pointerId)
    drag.current = which
  }
  const onMove = (e) => {
    const d = drag.current
    if (!d || !dur) return
    const t = timeAt(e)
    if (d === 'in') { const v = Math.min(t, out - 0.05); setInT(v); seek(v) }
    else if (d === 'out') { const v = Math.max(t, inT + 0.05); setOutT(v); seek(v) }
    else if (d === 'head') seek(t)
  }
  const endDrag = () => { drag.current = null }

  const apply = () => {
    setArgs({ start: inT > 0.0005 ? inT.toFixed(3) : '0', end: outT != null && outT < dur - 0.02 ? outT.toFixed(3) : '', duration: '' })
    onClose()
  }
  const browse = async () => {
    const p = await window.electronAPI.openFile([{ name: 'Videos', extensions: ['mp4', 'mov', 'm4v', 'mkv', 'webm', 'avi'] }, { name: 'All Files', extensions: ['*'] }])
    if (p) { setPath(p); setDur(0); setOutT(null) }
  }

  const pct = (t) => (dur ? `${(t / dur) * 100}%` : '0%')
  const btn = { padding: '5px 10px', fontSize: 12, fontWeight: 700 }
  const field = { width: 96, padding: '3px 6px', fontSize: 12, fontFamily: 'var(--font-mono)' }

  return createPortal(
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(8,8,8,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
         onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}>
      <div style={{ width: 'min(860px, 100%)', background: 'var(--paper)', color: 'var(--ink)', border: 'var(--border)', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 14px', background: 'var(--coral)', color: '#080808', borderBottom: 'var(--border)' }}>
          <strong style={{ fontFamily: 'var(--font-display)', fontSize: 13 }}>Trim</strong>
          <span style={{ fontSize: 11 }}>drag the yellow handles · Space plays · I / O set in / out · ← → step a frame</span>
          <span style={{ flex: 1 }} />
          <button onClick={onClose} style={{ padding: '2px 9px' }}>✕</button>
        </div>

        {!path ? (
          <div style={{ padding: 28, textAlign: 'center' }}>
            <p style={{ fontSize: 13, marginBottom: 12 }}>Choose the video to trim (or connect an Input node with a file to this program first).</p>
            <button onClick={browse} style={{ ...btn, background: 'var(--yellow)', color: '#080808' }}>Browse…</button>
          </div>
        ) : (
          <div style={{ padding: 14 }}>
            <div style={{ background: '#000', borderRadius: 8, display: 'flex', justifyContent: 'center', border: '2px solid var(--ink)' }}>
              <video
                ref={videoRef}
                src={window.electronAPI.mediaUrl(path)}
                style={{ maxWidth: '100%', maxHeight: 380, display: 'block' }}
                onLoadedMetadata={e => setDur(e.currentTarget.duration || 0)}
                onTimeUpdate={e => {
                  const t = e.currentTarget.currentTime
                  setNow(t)
                  if (!e.currentTarget.paused && outT != null && t >= outT) { e.currentTarget.pause(); e.currentTarget.currentTime = outT }
                }}
                onPlay={() => setPlaying(true)}
                onPause={() => setPlaying(false)}
                muted={false}
                preload="auto"
              />
            </div>

            {/* timeline */}
            <div ref={trackRef} onPointerMove={onMove} onPointerUp={endDrag} onPointerCancel={endDrag}
                 onPointerDown={e => { if (dur) { drag.current = 'head'; seek(timeAt(e)) } }}
                 style={{ position: 'relative', height: 46, margin: '16px 4px 6px', background: 'var(--paper-dim)', border: '2px solid var(--ink)', borderRadius: 6, touchAction: 'none', cursor: 'pointer' }}>
              {/* kept range */}
              <div style={{ position: 'absolute', top: 0, bottom: 0, left: pct(inT), width: dur ? `${((out - inT) / dur) * 100}%` : 0, background: 'var(--select)', opacity: 0.35 }} />
              {/* playhead */}
              <div style={{ position: 'absolute', top: -6, bottom: -6, left: pct(now), width: 2, background: 'var(--ink)', pointerEvents: 'none' }} />
              {/* handles */}
              {[['in', inT], ['out', out]].map(([k, t]) => (
                <div key={k} onPointerDown={e => startDrag(e, k)} title={k === 'in' ? 'In point' : 'Out point'}
                     style={{ position: 'absolute', top: -8, bottom: -8, left: pct(t), width: 14, marginLeft: -7, cursor: 'ew-resize',
                              background: 'var(--select)', border: '2px solid #080808', borderRadius: 4, touchAction: 'none' }} />
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted-dim)' }}>
              <span>0:00.000</span><span>now {fmt(now)}</span><span>{fmt(dur)}</span>
            </div>

            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 12, flexWrap: 'wrap' }}>
              <button onClick={togglePlay} style={btn}>{playing ? '❚❚ Pause' : '▶ Play selection'}</button>
              <button onClick={() => step(-1)} style={btn} title="Back one frame (←)">◀</button>
              <button onClick={() => step(1)} style={btn} title="Forward one frame (→)">▶</button>
              <span style={{ flex: 1 }} />
              <button onClick={() => setInT(Math.min(videoRef.current?.currentTime || 0, out - 0.05))} style={btn}>Set in (I)</button>
              <label style={{ fontSize: 11 }}>In <input style={field} value={inT.toFixed(3)} onChange={e => { const v = Number(e.target.value); if (Number.isFinite(v)) setInT(clamp(v, 0, out - 0.05)) }} /></label>
              <label style={{ fontSize: 11 }}>Out <input style={field} value={out.toFixed(3)} onChange={e => { const v = Number(e.target.value); if (Number.isFinite(v)) setOutT(clamp(v, inT + 0.05, dur || v)) }} /></label>
              <button onClick={() => setOutT(Math.max(videoRef.current?.currentTime || 0, inT + 0.05))} style={btn}>Set out (O)</button>
            </div>
            <div style={{ fontSize: 12, marginTop: 10 }}>Keeps <b>{fmt(Math.max(0, out - inT))}</b> of {fmt(dur)}.</div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '0 14px 14px' }}>
          {path && <button onClick={browse} style={btn}>Other video…</button>}
          <button onClick={onClose} style={btn}>Cancel</button>
          <button onClick={apply} disabled={!path || !dur} style={{ ...btn, background: 'var(--yellow)', color: '#080808' }}>Use this range</button>
        </div>
      </div>
    </div>,
    document.body
  )
}
