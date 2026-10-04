import { createContext, useContext } from 'react'

/** Everything a GroupNode needs from the canvas: boundary connections, member summaries, and actions. */
export const GroupContext = createContext({
  boundary: {}, members: {},
  toggleCollapse: () => {}, ungroup: () => {}, updateGroup: () => {}, toggleLock: () => {}
})
export const useGroupContext = () => useContext(GroupContext)

/** The real edges. React Flow is handed display edges (collapsed-group boundary edges are re-routed to the group). */
export const RealEdgesContext = createContext([])
export const useRealEdges = () => useContext(RealEdgesContext)
