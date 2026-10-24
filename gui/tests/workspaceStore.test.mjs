import test from 'node:test'
import assert from 'node:assert/strict'
import { serializeWorkspace, parseWorkspace, hasRealWork, maxNodeSuffix, cleanNodes } from '../src/renderer/src/workspaceStore.js'

const input = { id: 'input-1', type: 'inputNode', position: { x: 0, y: 0 }, data: { filePath: '' }, deletable: false, selected: true, measured: { width: 9, height: 9 } }
const output = { id: 'output-1', type: 'outputNode', position: { x: 600, y: 0 }, data: { filePath: '', format: 'mp4' }, deletable: false }
const fx = { id: 'effect-7-1700000000000', type: 'effectNode', position: { x: 300, y: 40 }, data: { program: 'halftone', args: { size: 4 }, collapsed: true }, dragging: true }
const edge = { id: 'e1', source: 'input-1', target: 'effect-7-1700000000000', sourceHandle: undefined, targetHandle: null, type: 'smoothstep', selected: true, animated: true }

test('serialize → parse round-trips the patch, view and collapsed state, and drops transient fields', () => {
  const text = serializeWorkspace({ nodes: [input, fx, output], edges: [edge], viewport: { x: -40, y: 12, zoom: 0.8 } })
  const ws = parseWorkspace(text)
  assert.equal(ws.nodes.length, 3)
  assert.equal(ws.edges.length, 1)
  assert.deepEqual(ws.viewport, { x: -40, y: 12, zoom: 0.8 })
  assert.equal(ws.nodes.find(n => n.id === fx.id).data.collapsed, true)
  assert.equal(ws.nodes[0].deletable, false)
  assert.equal('selected' in ws.nodes[0], false)
  assert.equal('measured' in ws.nodes[0], false)
  assert.equal('dragging' in ws.nodes[1], false)
  assert.equal(ws.edges[0].sourceHandle, null)
  assert.equal('animated' in ws.edges[0], false)
})

test('anything corrupt, empty or from another version parses to null', () => {
  for (const bad of [null, undefined, '', 'not json', '{}', '[]', '{"version":2,"nodes":[],"edges":[]}',
                     JSON.stringify({ version: 1, nodes: 'x', edges: [] }),
                     JSON.stringify({ version: 1, nodes: [{ id: 5 }], edges: [] })]) {
    assert.equal(parseWorkspace(bad), null, String(bad))
  }
})

test('the fixed Input/Output pair must be present, and edges to missing nodes are dropped', () => {
  const noOutput = serializeWorkspace({ nodes: [input, fx], edges: [], viewport: null })
  assert.equal(parseWorkspace(noOutput), null)
  const dangling = serializeWorkspace({ nodes: [input, output], edges: [{ id: 'x', source: 'input-1', target: 'ghost' }], viewport: null })
  assert.equal(parseWorkspace(dangling).edges.length, 0)
})

test('bad viewport values become null instead of breaking the view', () => {
  const ws = parseWorkspace(serializeWorkspace({ nodes: [input, output], edges: [], viewport: { x: NaN, y: 0, zoom: 1 } }))
  assert.equal(ws.viewport, null)
})

test('hasRealWork: the empty starter canvas is not worth restoring; a chosen file or a program is', () => {
  const empty = parseWorkspace(serializeWorkspace({ nodes: [input, output], edges: [], viewport: null }))
  assert.equal(hasRealWork(empty), false)
  assert.equal(hasRealWork(null), false)
  const withFile = parseWorkspace(serializeWorkspace({ nodes: [{ ...input, data: { filePath: '/a/b.mp4' } }, output], edges: [], viewport: null }))
  assert.equal(hasRealWork(withFile), true)
  assert.equal(hasRealWork(parseWorkspace(serializeWorkspace({ nodes: [input, fx, output], edges: [], viewport: null }))), true)
})

test('maxNodeSuffix keeps new ids ahead of restored ones', () => {
  assert.equal(maxNodeSuffix([input, fx, output], 2), 7)
  assert.equal(maxNodeSuffix([{ id: 'effect-31-170' }, { id: 'input-4-1' }], 2), 31)
  assert.equal(maxNodeSuffix([], 5), 5)
})

test('cleanNodes keeps group geometry', () => {
  const g = { id: 'group-3-1', type: 'groupNode', position: { x: 0, y: 0 }, data: {}, width: 300, height: 200, style: { zIndex: -1 } }
  const [c] = cleanNodes([g])
  assert.equal(c.width, 300)
  assert.equal(c.zIndex, -1)
})
