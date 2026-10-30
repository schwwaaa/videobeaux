import test from 'node:test'
import assert from 'node:assert/strict'
import { resolvePresetTokens } from '../src/main/presetTokens.js'

const TOKENS = { sample: '/app/examples/sample.mp4', sample2: '/app/examples/sample2.mp4', outputs: '/Users/me/Documents/videobeaux/outputs' }

test('example tokens become real paths, and nothing else changes', () => {
  const nodes = [
    { id: 'input-1', type: 'inputNode', data: { filePath: '{{sample}}' } },
    { id: 'effect-1-1', type: 'effectNode', data: { program: 'halftone', args: { cell_size: 8 } } },
    { id: 'output-1', type: 'outputNode', data: { filePath: '{{outputs}}/halftone.mp4', format: 'mp4' } }
  ]
  const out = resolvePresetTokens(nodes, { tokens: TOKENS })
  assert.equal(out[0].data.filePath, '/app/examples/sample.mp4')
  assert.equal(out[2].data.filePath, '/Users/me/Documents/videobeaux/outputs/halftone.mp4')
  assert.equal(out[2].data.format, 'mp4')
  assert.deepEqual(out[1], nodes[1])
  assert.equal(nodes[0].data.filePath, '{{sample}}', 'the input array is not modified')
})

test('the second clip token is filled, and a second clip in a folder path is too', () => {
  const nodes = [
    { id: 'input-2', type: 'inputNode', data: { filePath: '{{sample2}}' } },
    { id: 'input-3', type: 'inputNode', data: { folderPath: '{{outputs}}/batch' } }
  ]
  const out = resolvePresetTokens(nodes, { tokens: TOKENS })
  assert.equal(out[0].data.filePath, '/app/examples/sample2.mp4')
  assert.equal(out[1].data.folderPath, '/Users/me/Documents/videobeaux/outputs/batch')
})

test('a token in a string argument is filled, and other arguments are kept as they are', () => {
  const nodes = [{ id: 'effect-1-1', type: 'effectNode', data: { program: 'soundtrack', args: { audio: '{{sample}}', gain: 0.5, on: true } } }]
  const out = resolvePresetTokens(nodes, { tokens: TOKENS })
  assert.deepEqual(out[0].data.args, { audio: '/app/examples/sample.mp4', gain: 0.5, on: true })
})

test('a preset with no tokens loads unchanged, including empty and missing paths', () => {
  const nodes = [{ id: 'input-1', type: 'inputNode', data: { filePath: '/x/clip.mp4' } }, { id: 'output-1', type: 'outputNode', data: {} }]
  assert.deepEqual(resolvePresetTokens(nodes, { tokens: TOKENS }), nodes)
  assert.deepEqual(resolvePresetTokens(undefined, { tokens: TOKENS }), [])
})

test('a replacement value with a dollar sign is inserted as written', () => {
  const nodes = [{ id: 'input-1', type: 'inputNode', data: { filePath: '{{sample}}' } }]
  const out = resolvePresetTokens(nodes, { tokens: { sample: '/Users/me/$Movies/clip.mp4' } })
  assert.equal(out[0].data.filePath, '/Users/me/$Movies/clip.mp4')
})
