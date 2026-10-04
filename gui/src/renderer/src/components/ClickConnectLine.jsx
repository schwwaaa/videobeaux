import React, { useEffect, useRef, useState } from 'react'
import { useStore, useStoreApi } from '@xyflow/react'

/**
 * Two-click connections: click a dot → a line follows the cursor → click another dot.
 *
 * React Flow already implements the click logic (connectOnClick: the first handle click is
 * remembered in `connectionClickStartHandle`, the second completes the connection) but
 * draws nothing while it waits. This renders that missing line, and adds the ways out
 * React Flow doesn't: Esc or a click on empty canvas cancels.
 *
 * Must be rendered inside <ReactFlow>.
 */
export default function ClickConnectLine() {
  const store = useStoreApi()
  const armed = useStore(s => s.connectionClickStartHandle)
  const [geom, setGeom] = useState(null)
  const pointer = useRef(null)
  const rootRef = useRef(null)

  // Cancel on Esc.
  useEffect(() => {
    if (!armed) return
    const onKey = (e) => {
      if (e.key === 'Escape') store.setState({ connectionClickStartHandle: null })
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [armed, store])

  // Follow the cursor. Re-reading the start handle's position every frame keeps the line
  // glued to it through panning, zooming and node drags without subscribing to all of those.
  useEffect(() => {
    if (!armed) { setGeom(null); pointer.current = null; return }
    const onMove = (e) => { pointer.current = { x: e.clientX, y: e.clientY } }
    window.addEventListener('pointermove', onMove)
    let raf = 0
    const tick = () => {
      raf = requestAnimationFrame(tick)
      const root = rootRef.current
      const container = root?.parentElement
      const handle = container?.querySelector('.react-flow__handle.clickconnecting')
      if (!container || !handle || !pointer.current) return
      const c = container.getBoundingClientRect()
      const h = handle.getBoundingClientRect()
      const next = {
        x1: h.left + h.width / 2 - c.left,
        y1: h.top + h.height / 2 - c.top,
        x2: pointer.current.x - c.left,
        y2: pointer.current.y - c.top,
        dir: armed.type === 'source' ? 1 : -1
      }
      setGeom(prev => (prev && prev.x1 === next.x1 && prev.y1 === next.y1 &&
                       prev.x2 === next.x2 && prev.y2 === next.y2) ? prev : next)
    }
    raf = requestAnimationFrame(tick)
    return () => { cancelAnimationFrame(raf); window.removeEventListener('pointermove', onMove) }
  }, [armed])

  let d = null
  if (armed && geom) {
    const { x1, y1, x2, y2, dir } = geom
    const reach = Math.max(40, Math.min(160, Math.abs(x2 - x1) / 2 + 30))
    d = `M ${x1} ${y1} C ${x1 + dir * reach} ${y1}, ${x2 - dir * reach * 0.4} ${y2}, ${x2} ${y2}`
  }

  return (
    <svg
      ref={rootRef}
      style={{
        position: 'absolute', inset: 0, width: '100%', height: '100%',
        pointerEvents: 'none', zIndex: 20, overflow: 'visible'
      }}
    >
      {d && (
        <>
          <path d={d} fill="none" stroke="var(--select)" strokeWidth="9" strokeLinecap="round" opacity="0.55" />
          <path d={d} fill="none" stroke="var(--ink)" strokeWidth="3" strokeLinecap="round" strokeDasharray="8 6">
            <animate attributeName="stroke-dashoffset" from="28" to="0" dur="0.7s" repeatCount="indefinite" />
          </path>
          <circle cx={geom.x2} cy={geom.y2} r="6" fill="var(--select)" stroke="var(--select-outline)" strokeWidth="2.5" />
        </>
      )}
    </svg>
  )
}
