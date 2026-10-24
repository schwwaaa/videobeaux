// "Tidy": arrange the programs left → right as a layered graph, using their real sizes so nothing overlaps.
//
//   columns  = longest path out of the Inputs (Outputs always last)
//   rows     = ordered by the average row of their inputs (two sweeps → fewer crossing lines)
//   groups   = laid out as one block; their members keep their positions relative to the group
//   loose    = nodes with no connections are parked in a tidy grid underneath
//
// Pure and deterministic (same input → same output), so a second Tidy changes nothing.

const GAP_X = 90
const GAP_Y = 36
const LOOSE_GAP = 110

export function nodeSize(n) {
  const w = n.measured?.width ?? n.width ?? (n.type === 'outputNode' ? 230 : n.type === 'inputNode' ? 240 : 250)
  const h = n.measured?.height ?? n.height ?? (n.type === 'effectNode' ? (n.data?.collapsed ? 70 : 230) : 150)
  return { w, h }
}

/**
 * @param {{nodes: object[], edges: object[], only?: string[]|null}} p  `only` = lay out just these (plus their groups).
 * @returns {{positions: Record<string,{x:number,y:number}>}} new positions for top-level nodes that were laid out.
 */
export function autoLayout({ nodes, edges, only = null }) {
  const byId = new Map(nodes.map(n => [n.id, n]))
  const rep = (id) => { const n = byId.get(id); return n && n.parentId && byId.has(n.parentId) ? n.parentId : id }
  let items = nodes.filter(n => !n.parentId && !n.hidden)
  if (only && only.length) {
    const want = new Set(only.map(rep))
    items = items.filter(n => want.has(n.id))
  }
  if (items.length === 0) return { positions: {} }
  const ids = new Set(items.map(n => n.id))
  const size = new Map(items.map(n => [n.id, nodeSize(n)]))

  // edges between laid-out items (members count as their group)
  const out = new Map(items.map(n => [n.id, new Set()]))
  const inn = new Map(items.map(n => [n.id, new Set()]))
  for (const e of edges) {
    const a = rep(e.source), b = rep(e.target)
    if (a === b || !ids.has(a) || !ids.has(b)) continue
    out.get(a).add(b); inn.get(b).add(a)
  }
  const isEnd = n => n.type === 'inputNode' || n.type === 'outputNode'
  const connected = new Set()
  for (const n of items) if (out.get(n.id).size || inn.get(n.id).size) connected.add(n.id)
  // the fixed Input / Output pair always belongs to the main graph, even when nothing is wired yet
  for (const n of items) if (isEnd(n) && n.deletable === false) connected.add(n.id)
  const main = items.filter(n => connected.has(n.id))
  const loose = items.filter(n => !connected.has(n.id))

  // ── columns: longest path from the sources (cycles are cut at the back edge) ──
  const layer = new Map()
  const state = new Map()                        // 0 visiting, 1 done
  const depth = (id) => {
    if (layer.has(id) && state.get(id) === 1) return layer.get(id)
    if (state.get(id) === 0) return 0            // cycle: ignore this back edge
    state.set(id, 0)
    let d = 0
    for (const p of inn.get(id)) if (connected.has(p)) d = Math.max(d, depth(p) + 1)
    layer.set(id, d); state.set(id, 1)
    return d
  }
  for (const n of main) depth(n.id)
  let maxLayer = Math.max(0, ...main.map(n => layer.get(n.id)))
  for (const n of main) {
    if (n.type === 'inputNode' && !inn.get(n.id).size) layer.set(n.id, 0)
  }
  const outputs = main.filter(n => n.type === 'outputNode')
  if (outputs.length) {
    // outputs sit one column to the right of everything that isn't an output
    const lastNonOutput = Math.max(-1, ...main.filter(n => n.type !== 'outputNode').map(n => layer.get(n.id)))
    for (const o of outputs) layer.set(o.id, lastNonOutput + 1)
    maxLayer = Math.max(maxLayer, lastNonOutput + 1)
  }
  const cols = Array.from({ length: maxLayer + 1 }, () => [])
  // start from the current vertical order so the result stays close to what the user had
  for (const n of [...main].sort((a, b) => a.position.y - b.position.y || a.position.x - b.position.x || (a.id < b.id ? -1 : 1))) cols[layer.get(n.id)].push(n.id)

  // ── rows: barycentre sweeps ──
  const order = () => { const m = new Map(); cols.forEach(c => c.forEach((id, i) => m.set(id, i))); return m }
  const sweep = (from, to, step, nbrs) => {
    for (let c = from; c !== to; c += step) {
      const pos = order()
      const bary = new Map(cols[c].map((id, i) => {
        const ns = [...nbrs(id)].filter(x => layer.get(x) === c - step)
        return [id, ns.length ? ns.reduce((s, x) => s + pos.get(x), 0) / ns.length : i]
      }))
      cols[c] = [...cols[c]].sort((a, b) => bary.get(a) - bary.get(b) || (a < b ? -1 : 1))
    }
  }
  for (let k = 0; k < 2; k++) { sweep(1, cols.length, 1, id => inn.get(id)); sweep(cols.length - 2, -1, -1, id => out.get(id)) }

  // ── coordinates ──
  const colW = cols.map(c => Math.max(0, ...c.map(id => size.get(id).w)))
  const colH = cols.map(c => c.reduce((s, id) => s + size.get(id).h, 0) + Math.max(0, c.length - 1) * GAP_Y)
  const tallest = Math.max(0, ...colH)
  const x0 = Math.min(...items.map(n => n.position.x))
  const y0 = Math.min(...items.map(n => n.position.y))
  const positions = {}
  let x = x0
  cols.forEach((c, ci) => {
    let y = y0 + (tallest - colH[ci]) / 2          // columns are centred on a common middle line
    for (const id of c) {
      const { w, h } = size.get(id)
      positions[id] = { x: Math.round(x + (colW[ci] - w) / 2), y: Math.round(y) }
      y += h + GAP_Y
    }
    x += colW[ci] + GAP_X
  })
  const mainRight = Math.max(x0 + 1, x - GAP_X)
  const mainBottom = y0 + tallest

  // ── loose nodes: a tidy grid below ──
  if (loose.length) {
    const avgW = loose.reduce((s, n) => s + size.get(n.id).w, 0) / loose.length
    const perRow = Math.max(1, Math.floor((mainRight - x0 + GAP_X) / (avgW + GAP_X)))
    const sorted = [...loose].sort((a, b) => a.position.y - b.position.y || a.position.x - b.position.x || (a.id < b.id ? -1 : 1))
    let y = mainBottom + (main.length ? LOOSE_GAP : 0)
    for (let r = 0; r * perRow < sorted.length; r++) {
      const row = sorted.slice(r * perRow, (r + 1) * perRow)
      let xx = x0
      for (const n of row) { positions[n.id] = { x: Math.round(xx), y: Math.round(y) }; xx += size.get(n.id).w + GAP_X }
      y += Math.max(...row.map(n => size.get(n.id).h)) + GAP_Y
    }
  }
  return { positions }
}
