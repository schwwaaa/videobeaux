import test from 'node:test'
import assert from 'node:assert/strict'
import { autoLayout, nodeSize } from '../src/renderer/src/autoLayout.js'

const N = (id, type, x, y, extra = {}) => ({ id, type, position: { x, y }, data: {}, ...extra })
const E = (a, b) => ({ id: `${a}>${b}`, source: a, target: b })

function world() {
  const nodes = [
    N('output-1', 'outputNode', 900, 40, { deletable: false }),
    N('input-1', 'inputNode', 700, 500, { deletable: false }),
    N('fx-b', 'effectNode', 10, 10),
    N('fx-a', 'effectNode', 400, 400),
    N('fx-c', 'effectNode', 123, 777),
    N('fx-d', 'effectNode', 50, 60, { measured: { width: 260, height: 90 } }),
    N('loose-1', 'effectNode', 5, 5),
    N('loose-2', 'effectNode', 9, 9),
  ]
  const edges = [E('input-1', 'fx-a'), E('fx-a', 'fx-b'), E('input-1', 'fx-c'), E('fx-c', 'fx-b'), E('fx-b', 'fx-d'), E('fx-d', 'output-1')]
  return { nodes, edges }
}
const place = (nodes, pos) => nodes.map(n => ({ ...n, position: pos[n.id] || n.position }))
const box = n => { const s = nodeSize(n); return { x: n.position.x, y: n.position.y, w: s.w, h: s.h } }
const overlap = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h

test('nothing overlaps after tidying', () => {
  const { nodes, edges } = world()
  const laid = place(nodes, autoLayout({ nodes, edges }).positions)
  for (let i = 0; i < laid.length; i++) for (let j = i + 1; j < laid.length; j++) {
    assert.equal(overlap(box(laid[i]), box(laid[j])), false, `${laid[i].id} overlaps ${laid[j].id}`)
  }
})

test('every connection runs left → right and Output is the last column', () => {
  const { nodes, edges } = world()
  const laid = new Map(place(nodes, autoLayout({ nodes, edges }).positions).map(n => [n.id, n]))
  for (const e of edges) {
    const a = laid.get(e.source), b = laid.get(e.target)
    assert.ok(a.position.x + nodeSize(a).w <= b.position.x, `${e.source} → ${e.target} does not run left to right`)
  }
  const out = laid.get('output-1')
  for (const n of laid.values()) if (n.id !== 'output-1' && !n.id.startsWith('loose')) assert.ok(n.position.x < out.position.x)
  assert.ok(laid.get('input-1').position.x <= Math.min(...[...laid.values()].map(n => n.position.x)))
})

test('unconnected nodes are parked in a grid below the graph', () => {
  const { nodes, edges } = world()
  const laid = new Map(place(nodes, autoLayout({ nodes, edges }).positions).map(n => [n.id, n]))
  const mainBottom = Math.max(...['input-1', 'fx-a', 'fx-b', 'fx-c', 'fx-d', 'output-1'].map(id => laid.get(id).position.y + nodeSize(laid.get(id)).h))
  for (const id of ['loose-1', 'loose-2']) assert.ok(laid.get(id).position.y >= mainBottom, `${id} should be below the graph`)
})

test('tidying twice changes nothing (stable, deterministic)', () => {
  const { nodes, edges } = world()
  const once = place(nodes, autoLayout({ nodes, edges }).positions)
  const twice = autoLayout({ nodes: once, edges }).positions
  for (const n of once) assert.deepEqual(twice[n.id], n.position, n.id)
})

test('group members keep their relative position; edges to members count as the group', () => {
  const nodes = [
    N('input-1', 'inputNode', 0, 0, { deletable: false }),
    N('output-1', 'outputNode', 100, 0, { deletable: false }),
    N('grp', 'groupNode', 300, 300, { width: 600, height: 260 }),
    N('m1', 'effectNode', 20, 40, { parentId: 'grp' }),
    N('m2', 'effectNode', 320, 40, { parentId: 'grp' }),
  ]
  const edges = [E('input-1', 'm1'), E('m1', 'm2'), E('m2', 'output-1')]
  const { positions } = autoLayout({ nodes, edges })
  assert.ok(positions.grp)
  assert.equal(positions.m1, undefined)
  assert.equal(positions.m2, undefined)
  assert.ok(positions['input-1'].x < positions.grp.x && positions.grp.x < positions['output-1'].x)
})

test('"only" lays out just the chosen programs and leaves the rest alone', () => {
  const { nodes, edges } = world()
  const { positions } = autoLayout({ nodes, edges, only: ['fx-a', 'fx-b'] })
  assert.deepEqual(Object.keys(positions).sort(), ['fx-a', 'fx-b'])
})

test('an empty or single-node canvas is handled', () => {
  assert.deepEqual(autoLayout({ nodes: [], edges: [] }).positions, {})
  const one = autoLayout({ nodes: [N('input-1', 'inputNode', 50, 50, { deletable: false })], edges: [] }).positions
  assert.deepEqual(one['input-1'], { x: 50, y: 50 })
})

test('a cycle does not hang the layout', () => {
  const nodes = [N('a', 'effectNode', 0, 0), N('b', 'effectNode', 0, 0)]
  const { positions } = autoLayout({ nodes, edges: [E('a', 'b'), E('b', 'a')] })
  assert.equal(Object.keys(positions).length, 2)
})
