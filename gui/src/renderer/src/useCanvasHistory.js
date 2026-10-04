import { createContext, useCallback, useContext, useRef, useState } from 'react'
import { useReactFlow } from '@xyflow/react'

/**
 * Undo/redo for the canvas (nodes + connections + their settings).
 *
 * Snapshot-based: record() saves the canvas as it is RIGHT NOW, so call it
 * just before a change. undo() restores the last snapshot (saving the current
 * state for redo); any new change clears the redo stack. Rapid edits with the
 * same key (e.g. dragging a number field) coalesce into a single undo step.
 */

const noop = { record: () => {} }
export const CanvasHistoryContext = createContext(noop)
export const useCanvasHistory = () => useContext(CanvasHistoryContext)

/** Like React Flow's updateNodeData, but undoable. Use inside node components. */
export function useUpdateNodeData() {
  const { record } = useCanvasHistory()
  const { updateNodeData } = useReactFlow()
  return useCallback((id, patch) => {
    record(`data:${id}`)
    updateNodeData(id, patch)
  }, [record, updateNodeData])
}

const LIMIT = 100
const COALESCE_MS = 1200

export function useHistory({ getSnapshot, restore }) {
  const past = useRef([])
  const future = useRef([])
  const last = useRef({ key: null, t: 0 })
  const [counts, setCounts] = useState({ undo: 0, redo: 0 })
  const sync = () => setCounts({ undo: past.current.length, redo: future.current.length })

  const record = useCallback((key) => {
    const now = Date.now()
    if (key && last.current.key === key && now - last.current.t < COALESCE_MS) {
      last.current.t = now   // same burst of edits — keep the snapshot taken at its start
      return
    }
    last.current = { key: key || null, t: now }
    past.current.push(getSnapshot())
    if (past.current.length > LIMIT) past.current.shift()
    future.current = []
    sync()
  }, [getSnapshot])

  const undo = useCallback(() => {
    const prev = past.current.pop()
    if (!prev) return
    future.current.push(getSnapshot())
    restore(prev)
    last.current = { key: null, t: 0 }
    sync()
  }, [getSnapshot, restore])

  const redo = useCallback(() => {
    const next = future.current.pop()
    if (!next) return
    past.current.push(getSnapshot())
    restore(next)
    last.current = { key: null, t: 0 }
    sync()
  }, [getSnapshot, restore])

  return { record, undo, redo, canUndo: counts.undo > 0, canRedo: counts.redo > 0 }
}
