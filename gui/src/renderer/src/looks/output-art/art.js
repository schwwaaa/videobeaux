// Thumbnails cropped from what each module really produces (tools/make_module_art.py).
//   · bundled set: looks/output-art/art/*.webp (made from a generated clip)
//   · user set:    <userData>/module-art/ — rendered in-app from the user's own video; when present it replaces the bundled
//                  set entirely, so all previews come from the same footage
// A module with no image simply falls back to its glyph.
import { useSyncExternalStore } from 'react'

const files = import.meta.glob('./art/*.webp', { eager: true, query: '?url', import: 'default' })

const BUNDLED = {}
for (const [path, url] of Object.entries(files)) {
  BUNDLED[path.replace(/^.*\//, '').replace(/\.webp$/, '')] = url
}

let overrides = {}
let info = { source: '', generated: '', count: 0 }
let version = 0
const listeners = new Set()
const emit = () => { version += 1; listeners.forEach(l => l()) }

export function artFor(programId) {
  if (Object.keys(overrides).length) return overrides[programId] || null
  return BUNDLED[programId] || null
}

export const ART_COUNT = Object.keys(BUNDLED).length

/** Re-read the user's thumbnails (call at start-up and after generating / resetting). */
export async function refreshArtOverrides() {
  try {
    const st = await window.electronAPI?.artStatus?.()
    const next = {}
    for (const [id, m] of Object.entries(st?.programs || {})) {
      next[id] = `${window.electronAPI.mediaUrl(`${st.dir}/${m.file}`)}?v=${encodeURIComponent(st.generated || '')}`
    }
    overrides = next
    info = { source: st?.source || '', generated: st?.generated || '', count: Object.keys(next).length }
    emit()
    return info
  } catch {
    return info
  }
}

export function artInfo() { return info }

/** Subscribe a component so it re-renders when the thumbnails change. */
export function useArtVersion() {
  return useSyncExternalStore(
    (cb) => { listeners.add(cb); return () => listeners.delete(cb) },
    () => version
  )
}
