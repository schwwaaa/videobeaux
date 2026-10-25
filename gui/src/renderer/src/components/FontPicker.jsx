import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

// A font dropdown where every option is drawn in its own typeface.
//
// The list comes from the app's own font catalogue (python -m videobeaux.utils.fonts): the open-licensed set bundled with
// Videobeaux (identical on every computer) followed by the fonts installed on this one. Previews are loaded from the very font
// files the caption renderer will use (served through the vbmedia:// protocol), so what you see here is what gets burned in.
// Faces are loaded lazily, only for the rows that scroll into view.

let catalogPromise = null
function loadCatalog(refresh = false) {
  if (!catalogPromise || refresh) {
    const ask = window.electronAPI?.listFonts
    catalogPromise = (ask ? ask(refresh) : Promise.resolve([]))
      .then(list => (Array.isArray(list) ? list : []))
      .catch(() => [])
  }
  return catalogPromise
}

const faceIds = new Map()          // family → css family name (or null when it can't be previewed)
const listeners = new Set()
const faceId = family => 'vbf-' + family.replace(/[^a-z0-9]+/gi, '-')

function ensureFace(font) {
  if (faceIds.has(font.family)) return faceIds.get(font.family)
  const file = font.bold || font.regular
  if (!file || !/\.(ttf|otf)$/i.test(file) || typeof FontFace === 'undefined') { faceIds.set(font.family, null); return null }
  const id = faceId(font.family)
  faceIds.set(font.family, id)
  try {
    const face = new FontFace(id, `url("${window.electronAPI.mediaUrl(file)}")`)
    face.load().then(f => { document.fonts.add(f); listeners.forEach(l => l()) }).catch(() => { faceIds.set(font.family, null) })
  } catch { faceIds.set(font.family, null) }
  return id
}

function Row({ font, selected, onPick, root }) {
  const ref = useRef(null)
  const [, bump] = useState(0)
  useEffect(() => {
    const l = () => bump(n => n + 1)
    listeners.add(l)
    return () => listeners.delete(l)
  }, [])
  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    if (typeof IntersectionObserver === 'undefined') { ensureFace(font); return undefined }
    const io = new IntersectionObserver(entries => { if (entries[0].isIntersecting) { ensureFace(font); io.disconnect() } }, { root: root.current, rootMargin: '120px' })
    io.observe(el)
    return () => io.disconnect()
  }, [font, root])
  const id = faceIds.get(font.family)
  return (
    <button
      ref={ref}
      type="button"
      role="option"
      aria-selected={selected}
      data-opt="1"
      onClick={() => onPick(font.family)}
      title={font.family}
      style={{
        display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px', margin: 0,
        border: 'none', borderBottom: '1px solid rgba(8,8,8,.12)', borderRadius: 0,
        background: selected ? 'var(--yellow)' : 'transparent', color: 'var(--ink)', boxShadow: 'none',
        fontFamily: id ? `"${id}", var(--font)` : 'var(--font)', fontSize: 20, fontWeight: 400, lineHeight: 1.25,
        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', cursor: 'pointer'
      }}
    >
      {font.family}
    </button>
  )
}

export default function FontPicker({ value, onChange, inputStyle }) {
  const [fonts, setFonts] = useState([])
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [pos, setPos] = useState({ left: 0, top: 0, width: 280, maxHeight: 360 })
  const btnRef = useRef(null)
  const popRef = useRef(null)
  const listRef = useRef(null)

  useEffect(() => { let on = true; loadCatalog().then(l => { if (on) setFonts(l) }); return () => { on = false } }, [])

  const current = value || 'Arial'
  const currentFont = useMemo(() => fonts.find(f => f.family.toLowerCase() === String(current).toLowerCase()), [fonts, current])
  const isPath = /[\\/]/.test(String(current)) && /\.(ttf|otf|ttc)$/i.test(String(current))
  const label = isPath ? String(current).split(/[\\/]/).pop() : current

  // draw the closed button in the chosen font too
  const [, bump] = useState(0)
  useEffect(() => {
    const l = () => bump(n => n + 1)
    listeners.add(l)
    return () => listeners.delete(l)
  }, [])
  useEffect(() => { if (currentFont) ensureFace(currentFont) }, [currentFont])
  const currentId = currentFont ? faceIds.get(currentFont.family) : null

  const place = useCallback(() => {
    const r = btnRef.current?.getBoundingClientRect()
    if (!r) return
    const width = Math.max(r.width, 300)
    const below = window.innerHeight - r.bottom - 12
    const above = r.top - 12
    const flip = below < 220 && above > below
    const maxHeight = Math.max(160, Math.min(380, flip ? above : below))
    setPos({
      left: Math.max(8, Math.min(r.left, window.innerWidth - width - 8)),
      top: flip ? Math.max(8, r.top - maxHeight - 4) : r.bottom + 4,
      width, maxHeight
    })
  }, [])

  useLayoutEffect(() => { if (open) place() }, [open, place])
  useEffect(() => {
    if (!open) return undefined
    const down = e => { if (!popRef.current?.contains(e.target) && !btnRef.current?.contains(e.target)) setOpen(false) }
    const key = e => { if (e.key === 'Escape') { setOpen(false); btnRef.current?.focus() } }
    document.addEventListener('mousedown', down, true)
    document.addEventListener('keydown', key, true)
    window.addEventListener('resize', place)
    return () => {
      document.removeEventListener('mousedown', down, true)
      document.removeEventListener('keydown', key, true)
      window.removeEventListener('resize', place)
    }
  }, [open, place])

  const q = query.trim().toLowerCase()
  const shown = q ? fonts.filter(f => f.family.toLowerCase().includes(q)) : fonts
  const bundled = shown.filter(f => f.bundled)
  const system = shown.filter(f => !f.bundled)

  const pick = family => { onChange(family); setOpen(false); setQuery('') }
  const browse = async () => {
    setOpen(false)
    const p = await window.electronAPI.openFile([{ name: 'Fonts', extensions: ['ttf', 'otf'] }])
    if (p) onChange(p)
  }
  const onListKey = e => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return
    e.preventDefault()
    const opts = [...(popRef.current?.querySelectorAll('[data-opt]') || [])]
    const at = opts.indexOf(document.activeElement)
    const next = opts[Math.max(0, Math.min(opts.length - 1, at + (e.key === 'ArrowDown' ? 1 : -1)))]
    next?.focus()
  }

  const heading = text => (
    <div style={{ padding: '6px 10px 3px', fontSize: 10, fontWeight: 700, letterSpacing: '.06em', textTransform: 'uppercase',
      background: 'var(--ink)', color: 'var(--paper)', position: 'sticky', top: 0, zIndex: 1 }}>{text}</div>
  )

  return (
    <>
      <button
        ref={btnRef}
        type="button"
        className="nodrag"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen(o => !o)}
        title="Choose a font"
        style={{
          ...inputStyle, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6, textAlign: 'left',
          cursor: 'pointer', fontFamily: currentId ? `"${currentId}", var(--font)` : 'var(--font)', fontSize: 16, fontWeight: 400,
          padding: '4px 8px'
        }}
      >
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{label}</span>
        <span aria-hidden="true" style={{ fontFamily: 'var(--font)', fontSize: 11 }}>▾</span>
      </button>

      {open && createPortal(
        <div
          ref={popRef}
          className="nodrag nowheel"
          onMouseDown={e => e.stopPropagation()}
          onWheel={e => e.stopPropagation()}
          onKeyDown={e => { e.stopPropagation(); onListKey(e) }}
          style={{
            position: 'fixed', left: pos.left, top: pos.top, width: pos.width, maxHeight: pos.maxHeight, zIndex: 100000,
            display: 'flex', flexDirection: 'column', background: 'var(--paper)', border: '3px solid var(--ink)',
            borderRadius: 8, boxShadow: '5px 5px 0 var(--ink)', overflow: 'hidden'
          }}
        >
          <input
            autoFocus
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder={`Search ${fonts.length} fonts…`}
            style={{ ...inputStyle, borderRadius: 0, border: 'none', borderBottom: '2px solid var(--ink)', padding: '7px 10px', fontSize: 13 }}
          />
          <div ref={listRef} role="listbox" style={{ overflowY: 'auto', flex: 1 }}>
            {bundled.length > 0 && heading('Included with Videobeaux')}
            {bundled.map(f => <Row key={'b' + f.family} font={f} root={listRef} selected={f.family.toLowerCase() === String(current).toLowerCase()} onPick={pick} />)}
            {system.length > 0 && heading('Installed on this computer')}
            {system.map(f => <Row key={'s' + f.family} font={f} root={listRef} selected={f.family.toLowerCase() === String(current).toLowerCase()} onPick={pick} />)}
            {shown.length === 0 && (
              <div style={{ padding: 12, fontSize: 12, color: 'var(--muted)' }}>
                {fonts.length === 0 ? 'No fonts found. Use “Choose a font file…” below.' : 'No font matches that search.'}
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={browse}
            style={{ borderRadius: 0, border: 'none', borderTop: '2px solid var(--ink)', background: 'var(--yellow)', padding: '8px 10px', fontSize: 12, boxShadow: 'none' }}
          >
            Choose a font file…
          </button>
        </div>,
        document.body
      )}
    </>
  )
}
