import test from 'node:test'
import assert from 'node:assert/strict'
import { resolvePresetTokens } from '../src/main/presetTokens.js'

test('example tokens become real paths, and nothing else changes', () => {
  const nodes = [
    { id: 'input-1', type: 'inputNode', data: { filePath: '{{sample}}' } },
    { id: 'effect-1-1', type: 'effectNode', data: { program: 'halftone', args: { cell_size: 8 } } },
    { id: 'output-1', type: 'outputNode', data: { filePath: '{{outputs}}/halftone.mp4', format: 'mp4' } }
  ]
  const out = resolvePresetTokens(nodes, { sampleFile: '/app/examples/sample.mp4', outputsDir: '/Users/me/Documents/videobeaux/outputs' })
  assert.equal(out[0].data.filePath, '/app/examples/sample.mp4')
  assert.equal(out[2].data.filePath, '/Users/me/Documents/videobeaux/outputs/halftone.mp4')
  assert.equal(out[2].data.format, 'mp4')
  assert.deepEqual(out[1], nodes[1])
  assert.equal(nodes[0].data.filePath, '{{sample}}', 'the input array is not modified')
})

test('a preset with no tokens loads unchanged, including empty and missing paths', () => {
  const nodes = [{ id: 'input-1', type: 'inputNode', data: { filePath: '/x/clip.mp4' } }, { id: 'output-1', type: 'outputNode', data: {} }]
  assert.deepEqual(resolvePresetTokens(nodes, { sampleFile: 'S', outputsDir: 'O' }), nodes)
  assert.deepEqual(resolvePresetTokens(undefined, { sampleFile: 'S', outputsDir: 'O' }), [])
})
