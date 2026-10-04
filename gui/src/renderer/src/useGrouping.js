import { useCallback } from 'react'

export const GROUP_COLORS = ['#8654aa', '#32b9df', '#2ec4b6', '#ff9f1c', '#d52c91', '#a8ad23']
const PAD = 26
const HEADER = 38
const COLLAPSED_W = 230

const sizeOf = (n) => ({ w: n.measured?.width ?? n.width ?? 260, h: n.measured?.height ?? n.height ?? 180 })

/**
 * Node grouping. A group is a container node (type 'groupNode') that owns its members through React Flow's
 * `parentId` (member positions are relative to the group, so dragging the group moves them all). Groups are
 * purely structural — they never change what the pipeline runs. Collapsing hides the members and shows the
 * group as one compact card; connections that cross the group's boundary are re-routed to it for display only.
 * Limits (v1): one level deep, effect programs only, no new connections into a collapsed group.
 */
export function useGrouping({ setNodes, getNodes, record, newId }) {
  const groupSelection = useCallback(() => {
    const all = getNodes()
    const picked = all.filter(n => n.selected && n.type === 'effectNode' && !n.parentId)
    if (picked.length < 2) return false
    const minX = Math.min(...picked.map(n => n.position.x)) - PAD
    const minY = Math.min(...picked.map(n => n.position.y)) - PAD - HEADER
    const maxX = Math.max(...picked.map(n => n.position.x + sizeOf(n).w)) + PAD
    const maxY = Math.max(...picked.map(n => n.position.y + sizeOf(n).h)) + PAD
    const id = newId('group')
    const group = {
      id, type: 'groupNode', position: { x: minX, y: minY }, selected: true,
      data: { label: 'Group', color: GROUP_COLORS[0], collapsed: false, locked: false },
      width: maxX - minX, height: maxY - minY, zIndex: -1
    }
    const ids = new Set(picked.map(n => n.id))
    const members = picked.map(n => ({
      ...n, parentId: id, expandParent: true, selected: false,
      position: { x: n.position.x - minX, y: n.position.y - minY }
    }))
    record()
    setNodes([...all.filter(n => !ids.has(n.id)).map(n => (n.selected ? { ...n, selected: false } : n)), group, ...members])
    return true
  }, [getNodes, setNodes, record, newId])

  const ungroup = useCallback((groupId) => {
    const all = getNodes()
    const g = all.find(n => n.id === groupId)
    if (!g) return
    record()
    setNodes(all.filter(n => n.id !== groupId).map(n => (n.parentId === groupId
      ? { ...n, parentId: undefined, expandParent: undefined, hidden: false, draggable: undefined,
          position: { x: n.position.x + g.position.x, y: n.position.y + g.position.y }, selected: true }
      : n)))
  }, [getNodes, setNodes, record])

  const ungroupSelection = useCallback(() => {
    const all = getNodes()
    const gids = new Set(all.filter(n => n.selected && n.type === 'groupNode').map(n => n.id))
    // a selected member also stands for its group
    for (const n of all) if (n.selected && n.parentId) gids.add(n.parentId)
    if (!gids.size) return false
    record()
    const groups = new Map(all.filter(n => gids.has(n.id)).map(n => [n.id, n]))
    setNodes(all.filter(n => !gids.has(n.id)).map(n => {
      const g = groups.get(n.parentId)
      return g ? { ...n, parentId: undefined, expandParent: undefined, hidden: false, draggable: undefined,
                   position: { x: n.position.x + g.position.x, y: n.position.y + g.position.y } } : n
    }))
    return true
  }, [getNodes, setNodes, record])

  const toggleCollapse = useCallback((groupId) => {
    record()
    setNodes(all => {
      const g = all.find(n => n.id === groupId)
      if (!g) return all
      const collapsing = !g.data.collapsed
      return all.map(n => {
        if (n.id === groupId) {
          return collapsing
            ? { ...n, width: undefined, height: undefined, style: { width: COLLAPSED_W },
                data: { ...n.data, collapsed: true, expanded: { w: n.width ?? n.measured?.width ?? 400, h: n.height ?? n.measured?.height ?? 300 } } }
            : { ...n, style: undefined, width: n.data.expanded?.w ?? 400, height: n.data.expanded?.h ?? 300,
                data: { ...n.data, collapsed: false } }
        }
        return n.parentId === groupId ? { ...n, hidden: collapsing, selected: false } : n
      })
    })
  }, [setNodes, record])

  const updateGroup = useCallback((groupId, patch) => {
    setNodes(all => all.map(n => (n.id === groupId ? { ...n, data: { ...n.data, ...patch } } : n)))
  }, [setNodes])

  const toggleLock = useCallback((groupId) => {
    record()
    setNodes(all => {
      const g = all.find(n => n.id === groupId)
      const locked = !g?.data?.locked
      return all.map(n => {
        if (n.id === groupId) return { ...n, data: { ...n.data, locked } }
        return n.parentId === groupId ? { ...n, draggable: locked ? false : undefined } : n
      })
    })
  }, [setNodes, record])

  return { groupSelection, ungroup, ungroupSelection, toggleCollapse, updateGroup, toggleLock }
}

/**
 * Derives what the canvas shows when groups are collapsed. Returns:
 *   displayEdges  — real edges, with boundary edges of collapsed groups re-routed to the group's handles
 *                   (id 'proxy:<realId>'), and edges fully inside a collapsed group hidden
 *   boundary      — groupId → { ins: [realEdgeId], outs: [realEdgeId] } (one handle per connection)
 *   members       — groupId → [{ label, color }] for the collapsed card's summary
 */
export function deriveGroupView(nodes, edges, programMap) {
  const byId = new Map(nodes.map(n => [n.id, n]))
  const collapsedOf = new Map()
  const members = {}
  const boundary = {}
  for (const n of nodes) {
    if (n.type === 'groupNode') { boundary[n.id] = { ins: [], outs: [] }; members[n.id] = [] }
  }
  for (const n of nodes) {
    if (!n.parentId || !members[n.parentId]) continue
    const prog = programMap[n.data?.program]
    members[n.parentId].push({ label: prog?.label || n.data?.program || 'Node', color: prog?.categoryColor || '#8a8a80' })
    if (byId.get(n.parentId)?.data?.collapsed) collapsedOf.set(n.id, n.parentId)
  }
  const displayEdges = []
  for (const e of edges) {
    const sg = collapsedOf.get(e.source), tg = collapsedOf.get(e.target)
    if (!sg && !tg) { displayEdges.push(e); continue }
    if (sg && sg === tg) { displayEdges.push({ ...e, hidden: true }); continue }
    if (sg) boundary[sg].outs.push(e.id)
    if (tg) boundary[tg].ins.push(e.id)
    displayEdges.push({
      ...e, id: `proxy:${e.id}`,
      source: sg || e.source, sourceHandle: sg ? `out:${e.id}` : e.sourceHandle,
      target: tg || e.target, targetHandle: tg ? `in:${e.id}` : e.targetHandle
    })
  }
  return { displayEdges, boundary, members }
}
