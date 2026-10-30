import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync, existsSync } from 'node:fs'
import { CATEGORIES, EXCLUDED_FROM_GUI } from '../src/renderer/src/programs.js'

const EX = new URL('../../examples/', import.meta.url)
const index = JSON.parse(readFileSync(new URL('index.json', EX), 'utf8'))
const visible = new Set(CATEGORIES.flatMap(c => c.programs.map(p => p.id)).filter(id => !EXCLUDED_FROM_GUI.has(id)))
const presetOf = e => JSON.parse(readFileSync(new URL(e.file, EX), 'utf8'))

test('the sample clips the examples use are present', () => {
  assert.ok(existsSync(new URL(index.sample, EX)), `${index.sample} is missing from examples/`)
  for (const clip of index.clips) assert.ok(existsSync(new URL(clip, EX)), `${clip} is missing from examples/`)
})

test('every example preset is listed, and every listed preset exists', () => {
  const files = readdirSync(new URL('presets/', EX)).filter(f => f.endsWith('.vbpreset.json'))
  assert.equal(files.length, index.examples.length)
  for (const e of index.examples) assert.ok(existsSync(new URL(e.file, EX)), `${e.file} is listed but missing`)
})

test('every index entry has the fields the Examples window shows', () => {
  for (const e of index.examples) {
    for (const key of ['id', 'name', 'description', 'category', 'file']) {
      assert.equal(typeof e[key], 'string', `${e.id}: ${key}`)
      assert.ok(e[key].length > 0, `${e.id}: ${key} is empty`)
    }
    assert.ok(Number.isInteger(e.clips) && e.clips >= 1, `${e.id}: clips`)
    assert.ok(Number.isInteger(e.steps) && e.steps >= 1, `${e.id}: steps`)
  }
})

test('every example is a path from the main clip through its program modes to the output, with extra clips wired in', () => {
  for (const e of index.examples) {
    const p = presetOf(e)
    assert.equal(p.presetFormatVersion, 1, e.id)
    const byId = new Map(p.nodes.map(n => [n.id, n]))
    assert.equal(byId.size, p.nodes.length, `${e.id}: node ids are not unique`)

    const effects = p.nodes.filter(n => n.type === 'effectNode')
    assert.equal(effects.length, e.steps, `${e.id}: steps in the index match the canvas`)
    for (const n of effects) assert.ok(visible.has(n.data.program), `${e.id}: ${n.data.program} is not a visible program mode`)

    // The main path: input-1 → each program in order → output-1, using the main (unnamed) handles.
    const main = p.edges.filter(ed => ed.targetHandle == null)
    let at = 'input-1'
    for (let i = 0; i < effects.length; i++) {
      const next = main.find(ed => ed.source === at)
      assert.ok(next, `${e.id}: nothing leaves ${at}`)
      assert.equal(byId.get(next.target).type, 'effectNode', `${e.id}: the main path goes to a program`)
      at = next.target
    }
    assert.equal(main.find(ed => ed.source === at)?.target, 'output-1', `${e.id}: the last program feeds the output`)

    // Extra clips: every extra input node is a clip token and feeds a named video handle of a program.
    const inputs = p.nodes.filter(n => n.type === 'inputNode')
    assert.equal(inputs.length, e.clips, `${e.id}: clip count in the index matches the canvas`)
    for (const n of inputs) assert.match(n.data.filePath, /^\{\{sample\d?\}\}$/, `${e.id}: ${n.id} uses a clip token`)
    for (const ed of p.edges.filter(ed => ed.targetHandle != null)) {
      assert.equal(byId.get(ed.source).type, 'inputNode', `${e.id}: a named handle is fed by a clip`)
      assert.equal(byId.get(ed.target).type, 'effectNode', `${e.id}: a clip feeds a program`)
    }

    const out = byId.get('output-1')
    assert.match(out.data.filePath, /^\{\{outputs\}\}\/[\w.-]+\.mp4$/, `${e.id}: output goes to the outputs folder`)
  }
})

test('the Chains category holds only chains, and every chain has at least two program modes', () => {
  const chains = index.examples.filter(e => e.category === 'Chains')
  assert.ok(chains.length >= 2, 'there is at least one chain example')
  for (const e of chains) assert.ok(e.steps >= 2, `${e.id}: a chain has more than one program mode`)
  for (const e of index.examples.filter(x => x.category !== 'Chains')) assert.equal(e.steps, 1, `${e.id}: single program mode`)
})

test('no hidden program mode is in the example library', () => {
  for (const e of index.examples) {
    for (const n of presetOf(e).nodes.filter(n => n.type === 'effectNode')) {
      assert.ok(!EXCLUDED_FROM_GUI.has(n.data.program), `${e.id}: ${n.data.program} is hidden`)
    }
  }
})
