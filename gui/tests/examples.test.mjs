import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync, existsSync } from 'node:fs'
import { CATEGORIES, EXCLUDED_FROM_GUI } from '../src/renderer/src/programs.js'

const EX = new URL('../../examples/', import.meta.url)
const index = JSON.parse(readFileSync(new URL('index.json', EX), 'utf8'))
const visible = new Set(CATEGORIES.flatMap(c => c.programs.map(p => p.id)).filter(id => !EXCLUDED_FROM_GUI.has(id)))

test('the sample clip the examples use is present', () => {
  assert.ok(existsSync(new URL(index.sample, EX)), `${index.sample} is missing from examples/`)
})

test('every example preset is listed, and every listed preset exists', () => {
  const files = readdirSync(new URL('presets/', EX)).filter(f => f.endsWith('.vbpreset.json'))
  assert.equal(files.length, index.examples.length)
  for (const e of index.examples) assert.ok(existsSync(new URL(e.file, EX)), `${e.file} is listed but missing`)
})

test('every example is a visible program mode with the sample in and a token-named output', () => {
  for (const e of index.examples) {
    const p = JSON.parse(readFileSync(new URL(e.file, EX), 'utf8'))
    assert.equal(p.presetFormatVersion, 1, e.id)
    const eff = p.nodes.filter(n => n.type === 'effectNode')
    assert.equal(eff.length, 1, `${e.id}: one program mode per example`)
    assert.ok(visible.has(eff[0].data.program), `${e.id}: ${eff[0].data.program} is not a visible program mode`)
    assert.equal(p.nodes.find(n => n.id === 'input-1').data.filePath, '{{sample}}', e.id)
    assert.equal(p.nodes.find(n => n.id === 'output-1').data.filePath, `{{outputs}}/${eff[0].data.program}.mp4`, e.id)
    assert.equal(p.edges.length, 2, e.id)
  }
})

test('no hidden program mode is in the example library', () => {
  for (const e of index.examples) assert.ok(!EXCLUDED_FROM_GUI.has(e.id), e.id)
})
