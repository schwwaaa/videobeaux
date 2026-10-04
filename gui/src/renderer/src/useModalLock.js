import { useSyncExternalStore } from 'react'

/**
 * While a helper window (e.g. the Lagkage layout editor) is open the canvas underneath must ignore the keyboard:
 * Delete would remove the selected program node, arrow keys would nudge it, ⌘-shortcuts would copy/paste it.
 * Helper windows call lockModal() on mount (and the returned function on unmount); the canvas reads useModalLocked().
 */
let count = 0
const listeners = new Set()
const notify = () => listeners.forEach(l => l())

export function lockModal() {
  count += 1
  notify()
  let released = false
  return () => { if (!released) { released = true; count -= 1; notify() } }
}

export const isModalLocked = () => count > 0
export function useModalLocked() {
  return useSyncExternalStore(
    (cb) => { listeners.add(cb); return () => listeners.delete(cb) },
    () => count > 0
  )
}
