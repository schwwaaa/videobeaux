// Run:  node --test gui/tests/        (from the repo root, or `node --test tests/` inside gui/)
import test from 'node:test'
import assert from 'node:assert/strict'
import { buildPipeline } from '../src/renderer/src/pipeline.js'
import { deriveGroupView } from '../src/renderer/src/useGrouping.js'

const programMap = {
  negative: { args: [], label: 'Negative', categoryColor: '#8654aa' },
  pixelate: { args: [], label: 'Pixelate', categoryColor: '#8654aa' }
}
const effect = (id, program, extra = {}) => ({ id, type: 'effectNode', position: { x: 0, y: 0 }, data: { program, args: {} }, ...extra })
const base = () => [
  { id: 'input-1', type: 'inputNode', position: { x: 0, y: 0 }, data: { filePath: '/tmp/in.mp4' } },
  { id: 'output-1', type: 'outputNode', position: { x: 0, y: 0 }, data: { filePath: '/tmp/out.mp4', format: 'mp4' } }
]
const edges = [
  { id: 'e1', source: 'input-1', target: 'a' },
  { id: 'e2', source: 'a', target: 'b' },
  { id: 'e3', source: 'b', target: 'output-1' }
]

test('grouping does not change the pipeline that runs', () => {
  const flat = [...base(), effect('a', 'negative'), effect('b', 'pixelate')]
  const grouped = [
    ...base(),
    { id: 'g', type: 'groupNode', position: { x: 0, y: 0 }, data: { label: 'G', collapsed: true } },
    effect('a', 'negative', { parentId: 'g', hidden: true }), effect('b', 'pixelate', { parentId: 'g', hidden: true })
  ]
  const p1 = buildPipeline(flat, edges, programMap)
  const p2 = buildPipeline(grouped, edges, programMap)
  assert.deepEqual(p2, p1)
})

test('collapsed group: boundary edges are re-routed, internal edges hidden, real edges untouched', () => {
  const nodes = [
    ...base(),
    { id: 'g', type: 'groupNode', position: { x: 0, y: 0 }, data: { label: 'G', collapsed: true } },
    effect('a', 'negative', { parentId: 'g', hidden: true }), effect('b', 'pixelate', { parentId: 'g', hidden: true })
  ]
  const { displayEdges, boundary, members } = deriveGroupView(nodes, edges, programMap)
  const byId = Object.fromEntries(displayEdges.map(e => [e.id, e]))
  assert.equal(byId['proxy:e1'].target, 'g')
  assert.equal(byId['proxy:e1'].targetHandle, 'in:e1')
  assert.equal(byId['proxy:e3'].source, 'g')
  assert.equal(byId['proxy:e3'].sourceHandle, 'out:e3')
  assert.equal(byId.e2.hidden, true)
  assert.deepEqual(boundary.g, { ins: ['e1'], outs: ['e3'] })
  assert.deepEqual(members.g.map(m => m.label), ['Negative', 'Pixelate'])
  assert.equal(edges[0].target, 'a')                              // the real edge objects were not mutated
})

test('expanded group leaves edges alone', () => {
  const nodes = [
    ...base(),
    { id: 'g', type: 'groupNode', position: { x: 0, y: 0 }, data: { label: 'G', collapsed: false } },
    effect('a', 'negative', { parentId: 'g' }), effect('b', 'pixelate', { parentId: 'g' })
  ]
  const { displayEdges } = deriveGroupView(nodes, edges, programMap)
  assert.deepEqual(displayEdges.map(e => e.id), ['e1', 'e2', 'e3'])
})
