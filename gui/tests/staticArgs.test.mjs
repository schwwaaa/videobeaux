// The GUI shows a program's own arg list when it has one, and ignores the Python side. So options added in Python
// must also be listed in programs.js, or they never appear in the app. These are the ones that were missed before.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { CATEGORIES } from '../src/renderer/src/programs.js'

const program = id => CATEGORIES.flatMap(c => c.programs || []).find(p => p.id === id)
const argNames = id => (program(id)?.args || []).map(a => a.name)

test('Auto Narrate shows the duck option and its ratio', () => {
  const names = argNames('auto_narrate')
  assert.ok(names.includes('duck'), 'duck checkbox is listed')
  assert.ok(names.includes('duck_ratio'), 'duck ratio is listed')
  const ratio = program('auto_narrate').args.find(a => a.name === 'duck_ratio')
  assert.equal(ratio.min, 1)
  assert.equal(ratio.max, 20)
  assert.equal(program('auto_narrate').args.find(a => a.name === 'duck').type, 'checkbox')
})

test('Text Overlay shows wobble and its period', () => {
  const names = argNames('text_overlay')
  assert.ok(names.includes('spin'))
  assert.ok(names.includes('wobble'))
  assert.ok(names.includes('wobble_period'))
})
