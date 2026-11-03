// Pipeline rules for a select that fills other fields (size presets) and for a source program (no input video).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { argPatch, buildPipeline } from '../src/renderer/src/pipeline.js'

test('a select with fills also sets the fields it names', () => {
  const arg = { name: 'preset', fills: { '720p': { width: 1280, height: 720 } } }
  assert.deepEqual(argPatch(arg, '720p'), { preset: '720p', width: 1280, height: 720 })
  assert.deepEqual(argPatch(arg, 'custom'), { preset: 'custom' })
})

test('a select without fills changes only itself', () => {
  assert.deepEqual(argPatch({ name: 'fit' }, 'stretch'), { fit: 'stretch' })
})

test('a source program needs no input video and runs with a null primary input', () => {
  const nodes = [
    { id: 'gen', type: 'effectNode', position: { x: 0, y: 0 }, data: { program: 'color_pattern', args: {} } },
    { id: 'out', type: 'outputNode', position: { x: 300, y: 0 }, data: { filePath: '/tmp/out.mp4' } },
  ]
  const edges = [{ id: 'e1', source: 'gen', target: 'out' }]
  const programMap = { color_pattern: { id: 'color_pattern', source: true, args: [] } }
  const p = buildPipeline(nodes, edges, programMap)
  assert.equal(p.tasks.length, 1)
  assert.equal(p.tasks[0].program, 'color_pattern')
  assert.equal(p.tasks[0].primaryInput, null)
})

test('an ordinary program still needs its input connected', () => {
  const nodes = [
    { id: 'fx', type: 'effectNode', position: { x: 0, y: 0 }, data: { program: 'speed', args: {} } },
    { id: 'out', type: 'outputNode', position: { x: 300, y: 0 }, data: { filePath: '/tmp/out.mp4' } },
  ]
  const edges = [{ id: 'e1', source: 'fx', target: 'out' }]
  const programMap = { speed: { id: 'speed', args: [] } }
  assert.throws(() => buildPipeline(nodes, edges, programMap), /main video input is not connected/)
})
