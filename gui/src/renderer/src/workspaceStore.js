// Remembering the canvas, so a reload never costs the user their patch (laptop sleep/wake reloads the dev server page,
// a renderer can be reset by the OS, the app can be quit by accident…). Pure helpers + a thin localStorage wrapper.
//
// The stored shape matches Save Preset (without the file dialog): { version, savedAt, nodes, edges, viewport }.

export const WORKSPACE_KEY = 'vb.workspace.v1'
export const WORKSPACE_OFF_KEY = 'vb.workspace.off'     // '1' = the user turned "Remember my workspace" off
const VERSION = 1

/** Strip React Flow's transient fields (selected / dragging / measured …) the same way Save Preset does. */
export function cleanNodes(nodes) {
  return (nodes || []).map(({ id, type, position, data, deletable, parentId, width, height, style, hidden, draggable }) => ({
    id, type, position, data,
    ...(deletable === false ? { deletable } : {}),
    ...(parentId ? { parentId, expandParent: true } : {}),
    ...(type === 'groupNode' ? { width, height, style, zIndex: -1 } : {}),
    ...(hidden ? { hidden: true } : {}),
    ...(draggable === false ? { draggable: false } : {})
  }))
}

export function cleanEdges(edges) {
  return (edges || []).map(({ id, source, target, sourceHandle, targetHandle, type }) => ({
    id, source, target, sourceHandle: sourceHandle ?? null, targetHandle: targetHandle ?? null, type
  }))
}

export function serializeWorkspace({ nodes, edges, viewport }) {
  return JSON.stringify({
    version: VERSION,
    savedAt: new Date().toISOString(),
    nodes: cleanNodes(nodes),
    edges: cleanEdges(edges),
    viewport: viewport && Number.isFinite(viewport.x) && Number.isFinite(viewport.y) && Number.isFinite(viewport.zoom)
      ? { x: viewport.x, y: viewport.y, zoom: viewport.zoom } : null
  })
}

const isNode = n => n && typeof n.id === 'string' && typeof n.type === 'string' &&
  n.position && Number.isFinite(n.position.x) && Number.isFinite(n.position.y)
const isEdge = e => e && typeof e.id === 'string' && typeof e.source === 'string' && typeof e.target === 'string'

/** Parse stored text; null for anything missing, corrupt or from a different version (start-up must never break on it). */
export function parseWorkspace(text) {
  if (!text || typeof text !== 'string') return null
  let data
  try { data = JSON.parse(text) } catch { return null }
  if (!data || data.version !== VERSION || !Array.isArray(data.nodes) || !Array.isArray(data.edges)) return null
  if (!data.nodes.every(isNode) || !data.edges.every(isEdge)) return null
  const ids = new Set(data.nodes.map(n => n.id))
  if (!ids.has('input-1') || !ids.has('output-1')) return null                 // the fixed Input/Output pair must exist
  const edges = data.edges.filter(e => ids.has(e.source) && ids.has(e.target))  // drop edges pointing at missing nodes
  const v = data.viewport
  const viewport = v && Number.isFinite(v.x) && Number.isFinite(v.y) && Number.isFinite(v.zoom) && v.zoom > 0 ? v : null
  return { nodes: data.nodes, edges, viewport, savedAt: data.savedAt || null }
}

/** Is there anything worth bringing back (more than the empty starter canvas)? */
export function hasRealWork(ws) {
  if (!ws) return false
  if (ws.edges.length > 0 || ws.nodes.length > 2) return true
  return ws.nodes.some(n => n.data && (n.data.filePath || n.data.folderPath))
}

/** Largest numeric id suffix (effect-12-…), so freshly created nodes never collide with restored ones. */
export function maxNodeSuffix(nodes, current = 0) {
  return nodes.reduce((max, n) => {
    const m = /-(\d+)(?:-\d+)?$/.exec(n.id)
    return m ? Math.max(max, parseInt(m[1], 10)) : max
  }, current)
}

function store() {
  try { return window.localStorage } catch { return null }
}

export function workspaceRemembered() {
  const s = store()
  try { return !(s && s.getItem(WORKSPACE_OFF_KEY) === '1') } catch { return true }
}

export function setWorkspaceRemembered(on) {
  const s = store()
  try {
    if (!s) return
    if (on) s.removeItem(WORKSPACE_OFF_KEY)
    else { s.setItem(WORKSPACE_OFF_KEY, '1'); s.removeItem(WORKSPACE_KEY) }     // turning it off also forgets the saved copy
  } catch { /* storage unavailable — nothing to remember with */ }
}

/** The workspace to start with: the saved one if remembering is on and it has real content, else null. */
export function loadStartWorkspace() {
  if (!workspaceRemembered()) return null
  const s = store()
  let text = null
  try { text = s ? s.getItem(WORKSPACE_KEY) : null } catch { text = null }
  const ws = parseWorkspace(text)
  return hasRealWork(ws) ? ws : null
}

export function saveWorkspaceText(text) {
  const s = store()
  try { if (s && workspaceRemembered()) s.setItem(WORKSPACE_KEY, text) } catch { /* quota / private mode: skip silently */ }
}
