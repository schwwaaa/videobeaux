// "Tidy": arrange the programs as a layered graph, using their real sizes so nothing overlaps.
//
//   columns  = longest path out of the Inputs (Outputs always last)
//   rows     = ordered by the average row of their inputs (two sweeps → fewer crossing lines)
//   groups   = laid out as one block; their members keep their positions relative to the group
//   loose    = nodes with no connections are parked in a tidy grid underneath
//
//   direction  'horizontal' = the flow runs left → right (the default)
//              'vertical'   = the flow runs top → bottom: the same layout, turned on its side
//              'auto'       = whichever of the two comes out closest to the shape of the canvas
//
// Pure and deterministic (same input → same output), so a second Tidy changes nothing.

const GAP_X = 90
const GAP_Y = 36
const LOOSE_GAP = 110
// Each direction's gaps: "rank" is the space between columns (left → right) or rows (top → bottom), "within" the space
// between the programs stacked in one column or spread along one row.
const GAPS = {
  horizontal: { rank: GAP_X, within: GAP_Y },
  vertical: { rank: GAP_Y * 2, within: GAP_X },
}

export function nodeSize(n) {
  const w = n.measured?.width ?? n.width ?? (n.type === 'outputNode' ? 230 : n.type === 'inputNode' ? 240 : 250)
  const h = n.measured?.height ?? n.height ?? (n.type === 'effectNode' ? (n.data?.collapsed ? 70 : 230) : 150)
  return { w, h }
}

/**
 * @param {{nodes: object[], edges: object[], only?: string[]|null, direction?: 'horizontal'|'vertical'|'auto',
 *          aspect?: number}} p
 *   `only` = lay out just these (plus their groups). `aspect` = the canvas width ÷ height, used by 'auto'.
 * @returns {{positions: Record<string,{x:number,y:number}>}} new positions for top-level nodes that were laid out.
 */
export function autoLayout({ nodes, edges, only = null, direction = 'horizontal', aspect = 16 / 9 }) {
  const byId = new Map(nodes.map(n => [n.id, n]))
  const rep = (id) => { const n = byId.get(id); return n && n.parentId && byId.has(n.parentId) ? n.parentId : id }
  let items = nodes.filter(n => !n.parentId && !n.hidden)
  if (only && only.length) {
    const want = new Set(only.map(rep))
    items = items.filter(n => want.has(n.id))
  }
  if (items.length === 0) return { positions: {} }
  const size = new Map(items.map(n => [n.id, nodeSize(n)]))
  const pos = new Map(items.map(n => [n.id, n.position]))

  const horizontal = layoutColumns({ items, edges, rep, size, pos, gaps: GAPS.horizontal })
  if (direction === 'horizontal') return { positions: horizontal }

  // Vertical: the same layout with x and y swapped. Sizes and positions go in turned, and the result comes back turned.
  const turnedSize = new Map([...size].map(([id, { w, h }]) => [id, { w: h, h: w }]))
  const turnedPos = new Map([...pos].map(([id, p]) => [id, { x: p.y, y: p.x }]))
  const turned = layoutColumns({ items, edges, rep, size: turnedSize, pos: turnedPos, gaps: GAPS.vertical })
  const vertical = Object.fromEntries(Object.entries(turned).map(([id, p]) => [id, { x: p.y, y: p.x }]))
  if (direction === 'vertical') return { positions: vertical }

  // auto: keep whichever arrangement's overall shape is closer to the canvas (ties go to horizontal)
  const offHorizontal = shapeOff(horizontal, size, aspect)
  const offVertical = shapeOff(vertical, size, aspect)
  return { positions: offVertical < offHorizontal ? vertical : horizontal }
}

// How far an arrangement's overall shape is from the target aspect ratio, on a log scale (0 = exactly that shape).
function shapeOff(positions, size, aspect) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity
  for (const [id, p] of Object.entries(positions)) {
    const { w, h } = size.get(id)
    x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y)
    x1 = Math.max(x1, p.x + w); y1 = Math.max(y1, p.y + h)
  }
  const target = aspect > 0 && Number.isFinite(aspect) ? aspect : 16 / 9
  return Math.abs(Math.log(Math.max(1, x1 - x0) / Math.max(1, y1 - y0)) - Math.log(target))
}

// Lays out the graph with the flow running along x. The vertical arrangement calls this on the turned graph.
function layoutColumns({ items, edges, rep, size, pos, gaps }) {
  const ids = new Set(items.map(n => n.id))

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
  // the order the user already has on the canvas (top to bottom, then left to right) keeps the result close to it
  const byPosition = (a, b) => pos.get(a.id).y - pos.get(b.id).y || pos.get(a.id).x - pos.get(b.id).x || (a.id < b.id ? -1 : 1)

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
  for (const n of [...main].sort(byPosition)) cols[layer.get(n.id)].push(n.id)

  // ── rows: barycentre sweeps ──
  const order = () => { const m = new Map(); cols.forEach(c => c.forEach((id, i) => m.set(id, i))); return m }
  const sweep = (from, to, step, nbrs) => {
    for (let c = from; c !== to; c += step) {
      const p = order()
      const bary = new Map(cols[c].map((id, i) => {
        const ns = [...nbrs(id)].filter(x => layer.get(x) === c - step)
        return [id, ns.length ? ns.reduce((s, x) => s + p.get(x), 0) / ns.length : i]
      }))
      cols[c] = [...cols[c]].sort((a, b) => bary.get(a) - bary.get(b) || (a < b ? -1 : 1))
    }
  }
  for (let k = 0; k < 2; k++) { sweep(1, cols.length, 1, id => inn.get(id)); sweep(cols.length - 2, -1, -1, id => out.get(id)) }

  // ── coordinates ──
  const colW = cols.map(c => Math.max(0, ...c.map(id => size.get(id).w)))
  const colH = cols.map(c => c.reduce((s, id) => s + size.get(id).h, 0) + Math.max(0, c.length - 1) * gaps.within)
  const tallest = Math.max(0, ...colH)
  const x0 = Math.min(...items.map(n => pos.get(n.id).x))
  const y0 = Math.min(...items.map(n => pos.get(n.id).y))
  const positions = {}
  let x = x0
  cols.forEach((c, ci) => {
    let y = y0 + (tallest - colH[ci]) / 2          // columns are centred on a common middle line
    for (const id of c) {
      const { w, h } = size.get(id)
      positions[id] = { x: Math.round(x + (colW[ci] - w) / 2), y: Math.round(y) }
      y += h + gaps.within
    }
    x += colW[ci] + gaps.rank
  })
  const mainRight = Math.max(x0 + 1, x - gaps.rank)
  const mainBottom = y0 + tallest

  // ── loose nodes: a tidy grid below ──
  if (loose.length) {
    const avgW = loose.reduce((s, n) => s + size.get(n.id).w, 0) / loose.length
    const perRow = Math.max(1, Math.floor((mainRight - x0 + gaps.rank) / (avgW + gaps.rank)))
    const sorted = [...loose].sort(byPosition)
    let y = mainBottom + (main.length ? LOOSE_GAP : 0)
    for (let r = 0; r * perRow < sorted.length; r++) {
      const row = sorted.slice(r * perRow, (r + 1) * perRow)
      let xx = x0
      for (const n of row) { positions[n.id] = { x: Math.round(xx), y: Math.round(y) }; xx += size.get(n.id).w + gaps.rank }
      y += Math.max(...row.map(n => size.get(n.id).h)) + gaps.within
    }
  }
  return positions
}
